#!/bin/sh
set -eu

ACTION=${1:-status}
[ "$#" -eq 0 ] || shift
POLL_SECONDS=180
FORCE=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --poll-seconds)
      [ "$#" -ge 2 ] || { printf '%s\n' 'missing value for --poll-seconds' >&2; exit 2; }
      POLL_SECONDS=$2
      shift 2
      ;;
    --force) FORCE=1; shift ;;
    *) printf 'unknown argument: %s\n' "$1" >&2; exit 2 ;;
  esac
done

case "$POLL_SECONDS" in ''|*[!0-9]*) printf '%s\n' 'poll seconds must be an integer' >&2; exit 2 ;; esac
if [ "$POLL_SECONDS" -lt 30 ] || [ "$POLL_SECONDS" -gt 3600 ]; then
  printf '%s\n' 'poll seconds must be between 30 and 3600' >&2
  exit 2
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
WATCHER=$SCRIPT_DIR/watch-airjet-git.sh
STATE_ROOT=${AIRJET_WATCHER_STATE_ROOT:-$HOME/Library/Application Support/AirJetGitWatcher}
EVENT_ROOT=$STATE_ROOT/events
STATUS_PATH=$STATE_ROOT/status.state
PID_PATH=$STATE_ROOT/watcher.pid
LOCK_DIR=$STATE_ROOT/watcher.lock
STOP_PATH=$STATE_ROOT/stop.request
PENDING_PATH=$STATE_ROOT/pending-event.state
umask 077
mkdir -p "$STATE_ROOT" "$EVENT_ROOT"
chmod 700 "$STATE_ROOT" "$EVENT_ROOT" 2>/dev/null || true

state_field() {
  key=$1
  file=$2
  [ -f "$file" ] || return 0
  sed -n "s/^$key=//p" "$file" | sed -n '1p'
}

validated_pid() {
  VALIDATED_PID=
  [ -f "$PID_PATH" ] || return 1
  pid=$(sed -n '1p' "$PID_PATH")
  case "$pid" in ''|*[!0-9]*) return 1 ;; esac
  kill -0 "$pid" 2>/dev/null || return 1
  command_line=$(ps -p "$pid" -o command= 2>/dev/null || true)
  case "$command_line" in *"$WATCHER"*) VALIDATED_PID=$pid; return 0 ;; esac
  printf 'PID %s exists but is not the AirJet watcher; refusing to control it.\n' "$pid" >&2
  exit 1
}

show_status() {
  running=false
  pid=NONE
  if validated_pid; then running=true; pid=$VALIDATED_PID; fi
  state=$(state_field state "$STATUS_PATH"); [ -n "$state" ] || state=UNKNOWN
  detail=$(state_field detail "$STATUS_PATH"); [ -n "$detail" ] || detail=NONE
  commit=$(state_field commit "$STATUS_PATH"); [ -n "$commit" ] || commit=UNKNOWN
  phase=$(state_field phase "$PENDING_PATH"); [ -n "$phase" ] || phase=NONE
  pending_commit=$(state_field new_commit "$PENDING_PATH"); [ -n "$pending_commit" ] || pending_commit=NONE
  [ -f "$PENDING_PATH" ] && pending=true || pending=false
  printf 'WATCHER_RUNNING=%s\nWATCHER_PID=%s\nWATCHER_STATE=%s\nWATCHER_DETAIL=%s\nWATCHER_COMMIT=%s\n' "$running" "$pid" "$state" "$detail" "$commit"
  printf 'PENDING_EVENT=%s\nPENDING_PHASE=%s\nPENDING_COMMIT=%s\nAUTO_START=DISABLED\n' "$pending" "$phase" "$pending_commit"
}

clean_stale_lock() {
  [ -d "$LOCK_DIR" ] || return 0
  lock_pid=
  [ ! -f "$LOCK_DIR/pid" ] || lock_pid=$(sed -n '1p' "$LOCK_DIR/pid")
  case "$lock_pid" in
    ''|*[!0-9]*) ;;
    *) if kill -0 "$lock_pid" 2>/dev/null; then printf 'watcher lock is held by PID %s\n' "$lock_pid" >&2; exit 1; fi ;;
  esac
  rm -f "$LOCK_DIR/pid"
  rmdir "$LOCK_DIR" || { printf '%s\n' 'stale lock directory is not empty; refusing recursive removal' >&2; exit 1; }
}

assert_local_gui() {
  [ "$(uname -s)" = Darwin ] || { printf '%s\n' 'this action requires macOS' >&2; exit 1; }
  [ -z "${SSH_CONNECTION:-}${SSH_CLIENT:-}${SSH_TTY:-}" ] || { printf '%s\n' 'start/retry is refused from SSH' >&2; exit 1; }
  console_user=$(stat -f '%Su' /dev/console 2>/dev/null || true)
  [ -n "$console_user" ] && [ "$console_user" = "$(id -un)" ] || { printf '%s\n' 'current user does not own the visible console' >&2; exit 1; }
  launchctl print "gui/$(id -u)" >/dev/null 2>&1 || { printf '%s\n' 'no GUI launchd session is available' >&2; exit 1; }
}

start_watcher() {
  assert_local_gui
  if validated_pid; then printf 'watcher already running: PID %s\n' "$VALIDATED_PID" >&2; exit 1; fi
  [ ! -f "$PENDING_PATH" ] || { printf '%s\n' 'pending event exists; use retry or acknowledge' >&2; exit 1; }
  [ -f "$WATCHER" ] || { printf 'watcher missing: %s\n' "$WATCHER" >&2; exit 1; }
  clean_stale_lock
  rm -f "$PID_PATH" "$STOP_PATH"
  nohup /bin/sh "$WATCHER" --poll-seconds "$POLL_SECONDS" >/dev/null 2>&1 &
  spawned=$!
  waited=0
  while [ "$waited" -lt 60 ]; do
    sleep 0.25
    if validated_pid; then
      printf 'STARTED_PID=%s\n' "$VALIDATED_PID"
      show_status
      return 0
    fi
    if ! kill -0 "$spawned" 2>/dev/null; then
      printf '%s\n' 'watcher exited during startup' >&2
      show_status
      exit 1
    fi
    waited=$((waited + 1))
  done
  printf 'watcher startup not confirmed; spawned PID %s\n' "$spawned" >&2
  exit 1
}

stop_watcher() {
  if ! validated_pid; then
    printf '%s\n' 'STOP_RESULT=NOT_RUNNING'
    show_status
    return 0
  fi
  pid=$VALIDATED_PID
  run_id=$(state_field run_id "$STATUS_PATH")
  [ -n "$run_id" ] || { printf '%s\n' 'watcher run_id is unavailable; refusing stop' >&2; exit 1; }
  tmp=$STOP_PATH.$$.tmp
  printf 'run_id=%s\nrequested_at=%s\n' "$run_id" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" > "$tmp"
  mv -f "$tmp" "$STOP_PATH"
  waited=0
  while [ "$waited" -lt 135 ]; do
    sleep 1
    if ! kill -0 "$pid" 2>/dev/null; then
      printf '%s\n' 'STOP_RESULT=STOPPED'
      show_status
      return 0
    fi
    waited=$((waited + 1))
  done
  if [ "$FORCE" -ne 1 ]; then
    printf 'STOP_RESULT=STOP_PENDING PID=%s; Git may still be completing. Retry status, then stop --force only after review.\n' "$pid" >&2
    exit 1
  fi
  validated_pid || { printf '%s\n' 'STOP_RESULT=STOPPED_DURING_RECHECK'; return 0; }
  kill -KILL "$VALIDATED_PID"
  printf 'STOP_RESULT=FORCED_PID_%s\n' "$VALIDATED_PID"
  show_status
}

acknowledge() {
  if validated_pid; then printf '%s\n' 'stop the watcher before acknowledging' >&2; exit 1; fi
  [ -f "$PENDING_PATH" ] || { printf '%s\n' 'ACKNOWLEDGE_RESULT=NO_PENDING_EVENT'; return 0; }
  new=$(state_field new_commit "$PENDING_PATH")
  phase=$(state_field phase "$PENDING_PATH")
  case "$phase" in CODEX_EXITED_0|CODEX_FAILED) ;; *) printf 'pending phase %s is not terminal; refusing acknowledgement\n' "$phase" >&2; exit 1 ;; esac
  printf '%s\n' "$new" | grep -Eq '^[0-9a-f]{40}([0-9a-f]{24})?$' || { printf '%s\n' 'pending commit is invalid' >&2; exit 1; }
  destination=$EVENT_ROOT/acknowledged-$new-$(date -u '+%Y%m%dT%H%M%SZ').state
  mv "$PENDING_PATH" "$destination"
  printf 'ACKNOWLEDGE_RESULT=ARCHIVED\nACKNOWLEDGED_PATH=%s\n' "$destination"
}

case "$ACTION" in
  start) start_watcher ;;
  stop) stop_watcher ;;
  status) show_status ;;
  once)
    validated_pid && { printf '%s\n' 'watcher is already running' >&2; exit 1; }
    /bin/sh "$WATCHER" --poll-seconds "$POLL_SECONDS" --once --no-wake
    show_status
    ;;
  retry)
    assert_local_gui
    validated_pid && { printf '%s\n' 'watcher is already running' >&2; exit 1; }
    [ -f "$PENDING_PATH" ] || { printf '%s\n' 'no pending event to retry' >&2; exit 1; }
    /bin/sh "$WATCHER" --poll-seconds "$POLL_SECONDS" --once --retry-pending
    show_status
    ;;
  acknowledge) acknowledge ;;
  *) printf 'unknown action: %s\n' "$ACTION" >&2; exit 2 ;;
esac
