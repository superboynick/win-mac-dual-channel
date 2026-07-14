#!/bin/sh
set -eu

[ "$#" -eq 3 ] || { printf '%s\n' 'usage: run-awakened-codex.sh PROMPT_HANDLE OLD_COMMIT NEW_COMMIT' >&2; exit 2; }
PROMPT_HANDLE=$1
OLD_COMMIT=$2
NEW_COMMIT=$3
RUNTIME_STATUS=DISABLED_PENDING_END_TO_END
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd -P)
STATE_ROOT="$HOME/Library/Application Support/AirJetGitWatcher"
TEST_MODE=${AIRJET_WATCHER_TEST_MODE:-0}
if [ "$TEST_MODE" = 1 ]; then
  TEST_RUNNER_MODE=${AIRJET_TEST_RUNNER_MODE:-}
  case "$TEST_RUNNER_MODE" in validate-only|path-check) ;; *) printf '%s\n' 'BLOCKED_TEST_RUNNER_MODE' >&2; exit 1 ;; esac
  REPO_ROOT=$(CDPATH= cd -- "${AIRJET_REPO_ROOT:?}" && pwd -P)
  STATE_ROOT=$(CDPATH= cd -- "${AIRJET_WATCHER_STATE_ROOT:?}" && pwd -P)
  case "$REPO_ROOT:$STATE_ROOT" in
    /private/tmp/*:/private/tmp/*|/private/var/folders/*:/private/var/folders/*) ;;
    *) printf '%s\n' 'BLOCKED_TEST_PATH_OUTSIDE_TEMP' >&2; exit 1 ;;
  esac
elif [ "$TEST_MODE" != 0 ]; then
  printf '%s\n' 'invalid AIRJET_WATCHER_TEST_MODE' >&2
  exit 2
fi
if [ "$TEST_MODE" = 0 ] && [ "$RUNTIME_STATUS" != ENABLED_AFTER_REVIEW ]; then
  printf 'RUNNER_RESULT=REFUSED_%s\n' "$RUNTIME_STATUS" >&2
  exit 1
fi
EVENT_ROOT=$STATE_ROOT/events
PROCESSED_ROOT=$STATE_ROOT/processed
PENDING_PATH=$STATE_ROOT/pending-event.state
WATCHER=$SCRIPT_DIR/watch-airjet-git.sh
POLICY=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)/wake-policy.md
TASK_ENVELOPE_REL=airjet-simulation/collaboration/MAC_TASK.env
CLAIM_HELD=0
RUNNER_TERMINAL_WRITTEN=0

for variable in $(env | sed -n 's/^\(GIT_CONFIG_[A-Za-z0-9_]*\)=.*/\1/p'); do unset "$variable"; done
unset GIT_EXEC_PATH GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_REPLACE_REF_BASE || true
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE GIT_SHALLOW_FILE GIT_NAMESPACE GIT_CEILING_DIRECTORIES || true
export GIT_CONFIG_NOSYSTEM=1
export GIT_CONFIG_SYSTEM=/dev/null
export GIT_CONFIG_GLOBAL=/dev/null
export GIT_TERMINAL_PROMPT=0
export GIT_ASKPASS=/usr/bin/false
export GIT_SSH_COMMAND='/usr/bin/ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=15 -p 443'

valid_commit() {
  printf '%s\n' "$1" | grep -Eq '^[0-9a-f]{40}([0-9a-f]{24})?$'
}

pending_field() {
  key=$1
  sed -n "s/^$key=//p" "$PENDING_PATH" | sed -n '1p'
}

committed_field() {
  key=$1
  /usr/bin/git --no-replace-objects -C "$REPO_ROOT" show "$NEW_COMMIT:$TASK_ENVELOPE_REL" | sed -n "s/^$key=//p" | sed -n '1p'
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
    printf 'task_id=%s\n' "$TASK_ID"
    printf 'workflow_id=%s\n' "$WORKFLOW_ID"
    printf 'parent_task_id=%s\n' "$PARENT_TASK_ID"
    printf 'hop=%s\n' "$HOP"
    printf 'max_hops=%s\n' "$MAX_HOPS"
    printf 'instruction_path=%s\n' "$INSTRUCTION_PATH"
  } > "$tmp"
  mv -f "$tmp" "$PENDING_PATH"
}

write_claim_phase() {
  phase=$1
  final=$CLAIM_ROOT/state
  tmp=$final.runner-$$.tmp
  {
    printf 'schema_version=1\n'
    printf 'task_id=%s\n' "$TASK_ID"
    printf 'workflow_id=%s\n' "$WORKFLOW_ID"
    printf 'task_commit=%s\n' "$NEW_COMMIT"
    printf 'phase=%s\n' "$phase"
    printf 'updated_at=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  } > "$tmp"
  mv -f "$tmp" "$final"
}

transition_phase() {
  phase=$1
  write_claim_phase "$phase"
  write_pending_phase "$phase"
}

runner_cleanup() {
  code=$?
  if [ "$CLAIM_HELD" -eq 1 ] && [ "$RUNNER_TERMINAL_WRITTEN" -eq 0 ]; then
    set +e
    write_claim_phase CODEX_FAILED
    write_pending_phase CODEX_FAILED
    set -e
  fi
  return "$code"
}

trap runner_cleanup 0
trap 'exit 130' 1 2 15

[ "$(uname -s)" = Darwin ] || { printf '%s\n' 'BLOCKED_NOT_MACOS' >&2; exit 1; }
[ -z "${SSH_CONNECTION:-}${SSH_CLIENT:-}${SSH_TTY:-}" ] || { printf '%s\n' 'BLOCKED_SSH_SESSION' >&2; exit 1; }
console_user=$(stat -f '%Su' /dev/console 2>/dev/null || true)
[ -n "$console_user" ] && [ "$console_user" = "$(id -un)" ] || { printf '%s\n' 'BLOCKED_NOT_CONSOLE_USER' >&2; exit 1; }
valid_commit "$OLD_COMMIT" || { printf '%s\n' 'BLOCKED_OLD_COMMIT_INVALID' >&2; exit 1; }
valid_commit "$NEW_COMMIT" || { printf '%s\n' 'BLOCKED_NEW_COMMIT_INVALID' >&2; exit 1; }
[ -d "$STATE_ROOT" ] && [ ! -L "$STATE_ROOT" ] || { printf '%s\n' 'BLOCKED_STATE_ROOT_INVALID' >&2; exit 1; }
STATE_ROOT=$(CDPATH= cd -- "$STATE_ROOT" && pwd -P)
case "$STATE_ROOT" in "$REPO_ROOT"|"$REPO_ROOT"/*) printf '%s\n' 'BLOCKED_STATE_ROOT_INSIDE_REPOSITORY' >&2; exit 1 ;; esac
EVENT_ROOT_REAL=$(CDPATH= cd -- "$EVENT_ROOT" && pwd -P)
PROCESSED_ROOT_REAL=$(CDPATH= cd -- "$PROCESSED_ROOT" && pwd -P)
[ "$EVENT_ROOT_REAL" = "$EVENT_ROOT" ] || { printf '%s\n' 'BLOCKED_EVENT_ROOT_NOT_DIRECT_STATE_CHILD' >&2; exit 1; }
[ "$PROCESSED_ROOT_REAL" = "$PROCESSED_ROOT" ] || { printf '%s\n' 'BLOCKED_PROCESSED_ROOT_NOT_DIRECT_STATE_CHILD' >&2; exit 1; }
[ -f "$PROMPT_HANDLE" ] && [ ! -L "$PROMPT_HANDLE" ] || { printf '%s\n' 'BLOCKED_PROMPT_HANDLE_MISSING_OR_SYMLINKED' >&2; exit 1; }
PROMPT_DIR=$(CDPATH= cd -- "$(dirname -- "$PROMPT_HANDLE")" && pwd -P)
[ "$PROMPT_DIR" = "$EVENT_ROOT_REAL" ] || { printf '%s\n' 'BLOCKED_PROMPT_HANDLE_OUTSIDE_EVENT_ROOT' >&2; exit 1; }
[ -f "$PENDING_PATH" ] && [ ! -L "$PENDING_PATH" ] || { printf '%s\n' 'BLOCKED_PENDING_MISSING_OR_SYMLINKED' >&2; exit 1; }
[ "$(pending_field phase)" = WAKE_REQUESTED ] || { printf '%s\n' 'BLOCKED_PENDING_PHASE' >&2; exit 1; }
[ "$(pending_field old_commit)" = "$OLD_COMMIT" ] || { printf '%s\n' 'BLOCKED_PENDING_OLD_COMMIT' >&2; exit 1; }
[ "$(pending_field new_commit)" = "$NEW_COMMIT" ] || { printf '%s\n' 'BLOCKED_PENDING_NEW_COMMIT' >&2; exit 1; }
[ "$(pending_field repo)" = "$REPO_ROOT" ] || { printf '%s\n' 'BLOCKED_PENDING_REPO' >&2; exit 1; }

TASK_ID=$(pending_field task_id)
printf '%s\n' "$TASK_ID" | grep -Eq '^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$' || { printf '%s\n' 'BLOCKED_PENDING_TASK_ID' >&2; exit 1; }
[ ! -e "$PROCESSED_ROOT/$TASK_ID.state" ] || { printf '%s\n' 'BLOCKED_TASK_ALREADY_PROCESSED' >&2; exit 1; }
[ ! -e "$PROCESSED_ROOT/$TASK_ID.claim" ] || { printf '%s\n' 'BLOCKED_TASK_ALREADY_CLAIMED' >&2; exit 1; }
[ -f "$WATCHER" ] && [ ! -L "$WATCHER" ] || { printf '%s\n' 'BLOCKED_WATCHER_VALIDATOR_MISSING' >&2; exit 1; }
/bin/sh "$WATCHER" --validate-task "$OLD_COMMIT" "$NEW_COMMIT" "$TASK_ID" >/dev/null

if [ "$TEST_MODE" = 1 ] && [ "$TEST_RUNNER_MODE" = validate-only ]; then
  printf 'TEST_VALIDATE_ONLY=PASS task_id=%s\n' "$TASK_ID"
  exit 0
fi

WORKFLOW_ID=$(committed_field workflow_id)
PARENT_TASK_ID=$(committed_field parent_task_id)
HOP=$(committed_field hop)
MAX_HOPS=$(committed_field max_hops)
INSTRUCTION_PATH=$(committed_field instruction_path)
[ "$(committed_field task_id)" = "$TASK_ID" ] || { printf '%s\n' 'BLOCKED_COMMITTED_TASK_ID_CHANGED' >&2; exit 1; }
INSTRUCTION=$(/usr/bin/git --no-replace-objects -C "$REPO_ROOT" show "$NEW_COMMIT:$INSTRUCTION_PATH")

REPORT_PARENT=$HOME/Downloads
[ -d "$REPORT_PARENT" ] || { printf '%s\n' 'BLOCKED_DOWNLOADS_MISSING' >&2; exit 1; }
REPORT_PARENT=$(CDPATH= cd -- "$REPORT_PARENT" && pwd -P)
REPORT_ROOT=$REPORT_PARENT/AirJetGitWatcherReports
case "$REPORT_ROOT" in "$REPO_ROOT"|"$REPO_ROOT"/*) printf '%s\n' 'BLOCKED_REPORT_ROOT_INSIDE_REPOSITORY' >&2; exit 1 ;; esac
[ ! -L "$REPORT_ROOT" ] || { printf '%s\n' 'BLOCKED_REPORT_ROOT_SYMLINK' >&2; exit 1; }
umask 077
mkdir -p "$REPORT_ROOT"
REPORT_ROOT_REAL=$(CDPATH= cd -- "$REPORT_ROOT" && pwd -P)
[ "$REPORT_ROOT_REAL" = "$REPORT_ROOT" ] || { printf '%s\n' 'BLOCKED_REPORT_ROOT_REDIRECTED' >&2; exit 1; }
chmod 700 "$REPORT_ROOT" 2>/dev/null || true

if [ "$TEST_MODE" = 1 ]; then
  printf '%s\n' 'BLOCKED_TEST_MODE_CODEX_START' >&2
  exit 1
fi

CODEX=$(command -v codex || true)
[ -n "$CODEX" ] && [ -x "$CODEX" ] || { printf '%s\n' 'BLOCKED_CODEX_MISSING' >&2; exit 1; }
case "$CODEX" in /*) ;; *) printf '%s\n' 'BLOCKED_CODEX_PATH_NOT_ABSOLUTE' >&2; exit 1 ;; esac
[ -f "$POLICY" ] && [ ! -L "$POLICY" ] || { printf '%s\n' 'BLOCKED_WAKE_POLICY_MISSING' >&2; exit 1; }

# Revalidate immediately before the atomic at-most-once claim. Two concurrent
# runners may both reach this point, but only one can create the claim directory.
/bin/sh "$WATCHER" --validate-task "$OLD_COMMIT" "$NEW_COMMIT" "$TASK_ID" >/dev/null
CLAIM_ROOT=$PROCESSED_ROOT/$TASK_ID.claim
if ! mkdir "$CLAIM_ROOT" 2>/dev/null; then
  printf '%s\n' 'BLOCKED_TASK_CLAIM_RACE' >&2
  exit 1
fi
CLAIM_HELD=1
chmod 700 "$CLAIM_ROOT" 2>/dev/null || true
write_claim_phase CLAIMED

# A final narrow check closes the validator-to-launch window for cooperative
# Git actors. The immutable task signature was checked immediately above.
[ "$(/usr/bin/git --no-replace-objects -C "$REPO_ROOT" rev-parse HEAD)" = "$NEW_COMMIT" ] || { write_claim_phase BLOCKED_FINAL_HEAD_CHANGED; printf '%s\n' 'BLOCKED_FINAL_HEAD_CHANGED' >&2; exit 1; }
[ -z "$(/usr/bin/git --no-replace-objects -C "$REPO_ROOT" status --porcelain=v1)" ] || { write_claim_phase BLOCKED_FINAL_DIRTY_WORKTREE; printf '%s\n' 'BLOCKED_FINAL_DIRTY_WORKTREE' >&2; exit 1; }
REMOTE_LINE=$(/usr/bin/git --no-replace-objects -C "$REPO_ROOT" ls-remote --exit-code origin refs/heads/main)
set -- $REMOTE_LINE
[ "$#" -eq 2 ] && [ "$1" = "$NEW_COMMIT" ] || { write_claim_phase BLOCKED_FINAL_REMOTE_MOVED; printf '%s\n' 'BLOCKED_FINAL_REMOTE_MOVED' >&2; exit 1; }

PROMPT=$(printf '%s\n\n' 'A signed AirJet peer task was revalidated immediately before this Codex launch.'
  printf 'OLD_COMMIT=%s\nNEW_COMMIT=%s\nTASK_ID=%s\nWORKFLOW_ID=%s\nHOP=%s/%s\nINSTRUCTION_PATH=%s\n\n' \
    "$OLD_COMMIT" "$NEW_COMMIT" "$TASK_ID" "$WORKFLOW_ID" "$HOP" "$MAX_HOPS" "$INSTRUCTION_PATH"
  printf 'Read and strictly follow the repository policy at: %s\n\n' "$POLICY"
  printf '%s\n\n' 'The signed committed instruction follows:'
  printf '%s\n' "$INSTRUCTION")

cd "$REPO_ROOT"
transition_phase CODEX_STARTED
printf '%s\n' 'Signed AirJet Git task validated; starting visible non-interactive Codex execution.'
printf 'TASK_ID=%s\nOLD_COMMIT=%s\nNEW_COMMIT=%s\n' "$TASK_ID" "$OLD_COMMIT" "$NEW_COMMIT"
REPORT_FILE=$REPORT_ROOT/AIRJET_GIT_WATCHER_LAST_REPORT.txt
set +e
"$CODEX" exec -C "$REPO_ROOT" -s workspace-write -c 'approval_policy="never"' -c 'model_reasoning_effort="high"' --add-dir "$REPORT_ROOT" -o "$REPORT_FILE" "$PROMPT"
code=$?
set -e
if [ "$code" -eq 0 ]; then
  transition_phase CODEX_EXITED_0
else
  transition_phase CODEX_FAILED
fi
RUNNER_TERMINAL_WRITTEN=1
printf 'CODEX_EXIT=%s\n' "$code"
exit "$code"
