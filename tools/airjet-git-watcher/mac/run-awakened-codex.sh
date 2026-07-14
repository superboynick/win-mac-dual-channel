#!/bin/sh
set -eu

[ "$#" -eq 3 ] || { printf '%s\n' 'usage: run-awakened-codex.sh PROMPT OLD_COMMIT NEW_COMMIT' >&2; exit 2; }
PROMPT_PATH=$1
OLD_COMMIT=$2
NEW_COMMIT=$3
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
REPO_ROOT=${AIRJET_REPO_ROOT:-$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd -P)}
REPO_ROOT=$(CDPATH= cd -- "$REPO_ROOT" && pwd -P)
STATE_ROOT=${AIRJET_WATCHER_STATE_ROOT:-$HOME/Library/Application Support/AirJetGitWatcher}
case "$STATE_ROOT" in
  "$REPO_ROOT"|"$REPO_ROOT"/*) printf '%s\n' 'BLOCKED_STATE_ROOT_INSIDE_REPOSITORY' >&2; exit 1 ;;
esac
STATE_ROOT=$(CDPATH= cd -- "$STATE_ROOT" && pwd -P)
case "$STATE_ROOT" in
  "$REPO_ROOT"|"$REPO_ROOT"/*) printf '%s\n' 'BLOCKED_STATE_ROOT_INSIDE_REPOSITORY' >&2; exit 1 ;;
esac
EVENT_ROOT=$STATE_ROOT/events
PENDING_PATH=$STATE_ROOT/pending-event.state
EVENT_ROOT_REAL=$(CDPATH= cd -- "$EVENT_ROOT" && pwd -P)
[ "$EVENT_ROOT_REAL" = "$EVENT_ROOT" ] || { printf '%s\n' 'BLOCKED_EVENT_ROOT_NOT_DIRECT_STATE_CHILD' >&2; exit 1; }
REPORT_PARENT=$HOME/Downloads
[ -d "$REPORT_PARENT" ] || { printf '%s\n' 'BLOCKED_DOWNLOADS_MISSING' >&2; exit 1; }
REPORT_PARENT=$(CDPATH= cd -- "$REPORT_PARENT" && pwd -P)
REPORT_ROOT=$REPORT_PARENT/AirJetGitWatcherReports
case "$REPORT_ROOT" in
  "$REPO_ROOT"|"$REPO_ROOT"/*) printf '%s\n' 'BLOCKED_REPORT_ROOT_INSIDE_REPOSITORY' >&2; exit 1 ;;
esac
[ ! -L "$REPORT_ROOT" ] || { printf '%s\n' 'BLOCKED_REPORT_ROOT_SYMLINK' >&2; exit 1; }
umask 077
mkdir -p "$REPORT_ROOT"
REPORT_ROOT_REAL=$(CDPATH= cd -- "$REPORT_ROOT" && pwd -P)
[ "$REPORT_ROOT_REAL" = "$REPORT_ROOT" ] || { printf '%s\n' 'BLOCKED_REPORT_ROOT_REDIRECTED' >&2; exit 1; }
chmod 700 "$REPORT_ROOT" 2>/dev/null || true

valid_commit() {
  printf '%s\n' "$1" | grep -Eq '^[0-9a-f]{40}([0-9a-f]{24})?$'
}

pending_field() {
  key=$1
  sed -n "s/^$key=//p" "$PENDING_PATH" | sed -n '1p'
}

write_pending_phase() {
  phase=$1
  tmp=$PENDING_PATH.runner-$$.tmp
  {
    printf 'schema_version=1\n'
    printf 'phase=%s\n' "$phase"
    printf 'created_at=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    printf 'repo=%s\n' "$REPO_ROOT"
    printf 'old_commit=%s\n' "$OLD_COMMIT"
    printf 'new_commit=%s\n' "$NEW_COMMIT"
  } > "$tmp"
  mv -f "$tmp" "$PENDING_PATH"
}

[ "$(uname -s)" = Darwin ] || { printf '%s\n' 'BLOCKED_NOT_MACOS' >&2; exit 1; }
[ -z "${SSH_CONNECTION:-}${SSH_CLIENT:-}${SSH_TTY:-}" ] || { printf '%s\n' 'BLOCKED_SSH_SESSION' >&2; exit 1; }
console_user=$(stat -f '%Su' /dev/console 2>/dev/null || true)
[ -n "$console_user" ] && [ "$console_user" = "$(id -un)" ] || { printf '%s\n' 'BLOCKED_NOT_CONSOLE_USER' >&2; exit 1; }
valid_commit "$OLD_COMMIT" || { printf '%s\n' 'BLOCKED_OLD_COMMIT_INVALID' >&2; exit 1; }
valid_commit "$NEW_COMMIT" || { printf '%s\n' 'BLOCKED_NEW_COMMIT_INVALID' >&2; exit 1; }
[ -f "$PROMPT_PATH" ] && [ ! -L "$PROMPT_PATH" ] || { printf '%s\n' 'BLOCKED_PROMPT_MISSING_OR_SYMLINKED' >&2; exit 1; }
PROMPT_DIR=$(CDPATH= cd -- "$(dirname -- "$PROMPT_PATH")" && pwd -P)
EVENT_ROOT_REAL=$(CDPATH= cd -- "$EVENT_ROOT" && pwd -P)
[ "$PROMPT_DIR" = "$EVENT_ROOT_REAL" ] || { printf '%s\n' 'BLOCKED_PROMPT_OUTSIDE_EVENT_ROOT' >&2; exit 1; }
[ -f "$PENDING_PATH" ] || { printf '%s\n' 'BLOCKED_PENDING_MISSING' >&2; exit 1; }
[ "$(pending_field phase)" = WAKE_REQUESTED ] || { printf '%s\n' 'BLOCKED_PENDING_PHASE' >&2; exit 1; }
[ "$(pending_field old_commit)" = "$OLD_COMMIT" ] || { printf '%s\n' 'BLOCKED_PENDING_OLD_COMMIT' >&2; exit 1; }
[ "$(pending_field new_commit)" = "$NEW_COMMIT" ] || { printf '%s\n' 'BLOCKED_PENDING_NEW_COMMIT' >&2; exit 1; }
[ "$(pending_field repo)" = "$REPO_ROOT" ] || { printf '%s\n' 'BLOCKED_PENDING_REPO' >&2; exit 1; }

case "$PROMPT_PATH" in
  "$EVENT_ROOT"/*) ;;
  *) printf '%s\n' 'BLOCKED_PROMPT_OUTSIDE_EVENT_ROOT' >&2; exit 1 ;;
esac

CODEX=$(command -v codex || true)
[ -n "$CODEX" ] || { printf '%s\n' 'BLOCKED_CODEX_MISSING' >&2; exit 1; }
case "$CODEX" in /*) ;; *) printf '%s\n' 'BLOCKED_CODEX_PATH_NOT_ABSOLUTE' >&2; exit 1 ;; esac
[ -x "$CODEX" ] || { printf '%s\n' 'BLOCKED_CODEX_NOT_EXECUTABLE' >&2; exit 1; }
PROMPT=$(cat "$PROMPT_PATH")
cd "$REPO_ROOT"

write_pending_phase CODEX_STARTED
printf '%s\n' 'AirJet Git update detected and safely fast-forwarded.'
printf 'OLD_COMMIT=%s\nNEW_COMMIT=%s\n' "$OLD_COMMIT" "$NEW_COMMIT"
printf '%s\n' 'Starting a visible interactive Codex session with workspace-write and on-request approvals.'
set +e
"$CODEX" -C "$REPO_ROOT" -s workspace-write -a on-request --add-dir "$REPORT_ROOT" "$PROMPT"
code=$?
set -e
if [ "$code" -eq 0 ]; then
  write_pending_phase CODEX_EXITED_0
else
  write_pending_phase CODEX_FAILED
fi
printf 'CODEX_EXIT=%s\n' "$code"
printf '%s' 'Press Return to close this Terminal window: '
read answer || true
exit "$code"
