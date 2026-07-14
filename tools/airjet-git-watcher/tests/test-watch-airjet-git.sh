#!/bin/sh
set -eu

# Local-only functional tests for the macOS watcher.  The suite never contacts
# GitHub and never invokes the visible wake path.

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
WATCHER=$(CDPATH= cd -- "$SCRIPT_DIR/../mac" && pwd -P)/watch-airjet-git.sh
MANAGER=$(CDPATH= cd -- "$SCRIPT_DIR/../mac" && pwd -P)/manage-airjet-watcher.sh
RUNNER=$(CDPATH= cd -- "$SCRIPT_DIR/../mac" && pwd -P)/run-awakened-codex.sh
TMP_BASE=${TMPDIR:-/private/tmp}
TMP_BASE=$(CDPATH= cd -- "$TMP_BASE" && pwd -P)
TEST_ROOT=$(mktemp -d "$TMP_BASE/airjet-watcher-test.XXXXXX")
ORIGIN=$TEST_ROOT/origin.git
SEED=$TEST_ROOT/seed
WRITER=$TEST_ROOT/writer
PASS_COUNT=0

cleanup() {
  if [ "${AIRJET_WATCHER_KEEP_TEST_ROOT:-0}" = 1 ]; then
    printf 'TEST_ROOT_RETAINED=%s\n' "$TEST_ROOT"
    return
  fi
  case "$TEST_ROOT" in
    "$TMP_BASE"/airjet-watcher-test.*) rm -rf -- "$TEST_ROOT" ;;
    *) printf 'refusing to remove unexpected test root: %s\n' "$TEST_ROOT" >&2 ;;
  esac
}
trap cleanup 0 1 2 15

fail() {
  printf 'TEST_RESULT=FAIL detail=%s\n' "$1" >&2
  exit 1
}

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf 'CASE_PASS=%s\n' "$1"
}

assert_contains() {
  label=$1
  value=$2
  expected=$3
  case "$value" in
    *"$expected"*) pass "$label" ;;
    *) fail "$label missing $expected; output=$value" ;;
  esac
}

assert_equal() {
  label=$1
  actual=$2
  expected=$3
  [ "$actual" = "$expected" ] || fail "$label expected=$expected actual=$actual"
  pass "$label"
}

configure_identity() {
  repo=$1
  git -C "$repo" config user.name AirJetWatcherTest
  git -C "$repo" config user.email airjet-watcher-test@example.invalid
}

clone_case() {
  name=$1
  path=$TEST_ROOT/$name
  git clone -q "$ORIGIN" "$path"
  configure_identity "$path"
  printf '%s\n' "$path"
}

run_watcher() {
  repo=$1
  state=$2
  set +e
  WATCH_OUTPUT=$(env \
    AIRJET_REPO_ROOT="$repo" \
    AIRJET_EXPECTED_REMOTE="$ORIGIN" \
    AIRJET_WATCHER_STATE_ROOT="$state" \
    /bin/sh "$WATCHER" --poll-seconds 30 --once --no-wake 2>&1)
  WATCH_CODE=$?
  set -e
}

run_watcher_retry() {
  repo=$1
  state=$2
  set +e
  WATCH_OUTPUT=$(env \
    AIRJET_REPO_ROOT="$repo" \
    AIRJET_EXPECTED_REMOTE="$ORIGIN" \
    AIRJET_WATCHER_STATE_ROOT="$state" \
    /bin/sh "$WATCHER" --poll-seconds 30 --once --no-wake --retry-pending 2>&1)
  WATCH_CODE=$?
  set -e
}

commit_writer_file() {
  relative=$1
  content=$2
  message=$3
  mkdir -p "$(dirname -- "$WRITER/$relative")"
  printf '%s\n' "$content" > "$WRITER/$relative"
  git -C "$WRITER" add -- "$relative"
  git -C "$WRITER" commit -q -m "$message"
  git -C "$WRITER" push -q origin main
}

[ -f "$WATCHER" ] || fail "watcher missing: $WATCHER"
[ -f "$MANAGER" ] || fail "manager missing: $MANAGER"
[ -f "$RUNNER" ] || fail "runner missing: $RUNNER"
/bin/sh -n "$WATCHER"
/bin/sh -n "$MANAGER"
/bin/sh -n "$RUNNER"
pass shell_syntax

git init -q --bare "$ORIGIN"
git --git-dir="$ORIGIN" symbolic-ref HEAD refs/heads/main
git init -q "$SEED"
configure_identity "$SEED"
git -C "$SEED" checkout -q -b main
mkdir -p "$SEED/tools/airjet-git-watcher"
printf '%s\n' baseline > "$SEED/README.fixture"
printf '%s\n' baseline > "$SEED/tools/airjet-git-watcher/fixture.txt"
git -C "$SEED" add README.fixture tools/airjet-git-watcher/fixture.txt
git -C "$SEED" commit -q -m baseline
git -C "$SEED" remote add origin "$ORIGIN"
git -C "$SEED" push -q -u origin main
git clone -q "$ORIGIN" "$WRITER"
configure_identity "$WRITER"

# 1. An unchanged clean repository must not create a pending event.
UNCHANGED=$(clone_case case-unchanged)
UNCHANGED_HEAD=$(git -C "$UNCHANGED" rev-parse HEAD)
run_watcher "$UNCHANGED" "$TEST_ROOT/state-unchanged"
assert_equal unchanged_exit "$WATCH_CODE" 0
assert_equal unchanged_head "$(git -C "$UNCHANGED" rev-parse HEAD)" "$UNCHANGED_HEAD"
[ ! -f "$TEST_ROOT/state-unchanged/pending-event.state" ] || fail unchanged_created_pending
pass unchanged_no_pending

# 2. A clean strictly-behind repository may fast-forward, but an ordinary
# update without a changed target=mac envelope must not create a wake event.
FAST_FORWARD=$(clone_case case-fast-forward)
FF_OLD=$(git -C "$FAST_FORWARD" rev-parse HEAD)
commit_writer_file normal-update.txt normal normal_update
FF_TARGET=$(git -C "$WRITER" rev-parse HEAD)
run_watcher "$FAST_FORWARD" "$TEST_ROOT/state-fast-forward"
assert_equal fast_forward_exit "$WATCH_CODE" 0
assert_equal fast_forward_head "$(git -C "$FAST_FORWARD" rev-parse HEAD)" "$FF_TARGET"
[ ! -f "$TEST_ROOT/state-fast-forward/pending-event.state" ] || fail ordinary_update_created_pending
pass ordinary_update_no_pending
assert_contains ordinary_update_status "$(cat "$TEST_ROOT/state-fast-forward/status.state")" state=SYNCED_NO_MAC_TASK
assert_equal fast_forward_clean "$(git -C "$FAST_FORWARD" status --porcelain)" ""
[ "$FF_OLD" != "$FF_TARGET" ] || fail fast_forward_fixture_did_not_advance
pass fast_forward_target_changed

# 3. A changed, valid target=mac task envelope creates a retained no-wake event.
TASK_WAKE=$(clone_case case-task-wake)
mkdir -p "$WRITER/airjet-simulation/collaboration" "$WRITER/airjet-simulation/tasks"
printf '%s\n' '# isolated test instruction' > "$WRITER/airjet-simulation/tasks/test-mac-task.md"
{
  printf '%s\n' 'schema_version=1'
  printf '%s\n' 'target=mac'
  printf '%s\n' 'action=wake_codex'
  printf '%s\n' 'task_id=isolated-watcher-test'
  printf '%s\n' 'instruction_path=airjet-simulation/tasks/test-mac-task.md'
} > "$WRITER/airjet-simulation/collaboration/MAC_TASK.env"
git -C "$WRITER" add airjet-simulation/collaboration/MAC_TASK.env airjet-simulation/tasks/test-mac-task.md
git -C "$WRITER" commit -q -m mac_task_envelope
git -C "$WRITER" push -q origin main
TASK_TARGET=$(git -C "$WRITER" rev-parse HEAD)
run_watcher "$TASK_WAKE" "$TEST_ROOT/state-task-wake"
assert_equal task_wake_exit "$WATCH_CODE" 0
assert_equal task_wake_head "$(git -C "$TASK_WAKE" rev-parse HEAD)" "$TASK_TARGET"
assert_contains task_wake_pending "$(cat "$TEST_ROOT/state-task-wake/pending-event.state")" phase=PENDING_NO_WAKE
assert_contains task_wake_record "$(cat "$TEST_ROOT/state-task-wake/events/mac-task-$TASK_TARGET.env")" task_id=isolated-watcher-test

# 4. The retained task event must block a second ordinary poll.
run_watcher "$TASK_WAKE" "$TEST_ROOT/state-task-wake"
[ "$WATCH_CODE" -ne 0 ] || fail pending_event_did_not_block
assert_contains pending_event_block "$WATCH_OUTPUT" BLOCKED_PENDING_EVENT

# Retry must revalidate live Git state and rebuild the task record from the
# committed envelope instead of trusting mutable state-root contents.
printf '%s\n' dirty >> "$TASK_WAKE/README.fixture"
run_watcher_retry "$TASK_WAKE" "$TEST_ROOT/state-task-wake"
[ "$WATCH_CODE" -ne 0 ] || fail dirty_pending_retry_did_not_block
assert_contains dirty_pending_retry_block "$WATCH_OUTPUT" BLOCKED_DIRTY_WORKTREE
git -C "$TASK_WAKE" restore README.fixture
TASK_EVENT=$TEST_ROOT/state-task-wake/events/mac-task-$TASK_TARGET.env
{
  printf '%s\n' 'schema_version=1'
  printf '%s\n' 'target=mac'
  printf '%s\n' 'action=wake_codex'
  printf '%s\n' 'task_id=tampered-local-state'
  printf '%s\n' 'instruction_path=airjet-simulation/tasks/test-mac-task.md'
} > "$TASK_EVENT"
run_watcher_retry "$TASK_WAKE" "$TEST_ROOT/state-task-wake"
assert_equal tampered_state_retry_exit "$WATCH_CODE" 0
assert_contains task_state_rebuilt_from_commit "$(cat "$TASK_EVENT")" task_id=isolated-watcher-test
assert_contains task_retry_pending "$(cat "$TEST_ROOT/state-task-wake/pending-event.state")" phase=PENDING_NO_WAKE

# 5. A dirty worktree must block before synchronization.
DIRTY=$(clone_case case-dirty)
printf '%s\n' dirty >> "$DIRTY/README.fixture"
DIRTY_HEAD=$(git -C "$DIRTY" rev-parse HEAD)
run_watcher "$DIRTY" "$TEST_ROOT/state-dirty"
[ "$WATCH_CODE" -ne 0 ] || fail dirty_worktree_did_not_block
assert_contains dirty_block "$WATCH_OUTPUT" BLOCKED_DIRTY_WORKTREE
assert_equal dirty_head_unchanged "$(git -C "$DIRTY" rev-parse HEAD)" "$DIRTY_HEAD"

# 6. A local-ahead repository must block and retain its commit.
AHEAD=$(clone_case case-ahead)
printf '%s\n' local-ahead > "$AHEAD/local-ahead.txt"
git -C "$AHEAD" add local-ahead.txt
git -C "$AHEAD" commit -q -m local_ahead
AHEAD_HEAD=$(git -C "$AHEAD" rev-parse HEAD)
run_watcher "$AHEAD" "$TEST_ROOT/state-ahead"
[ "$WATCH_CODE" -ne 0 ] || fail local_ahead_did_not_block
assert_contains ahead_block "$WATCH_OUTPUT" BLOCKED_LOCAL_AHEAD_OR_DIVERGED
assert_equal ahead_head_unchanged "$(git -C "$AHEAD" rev-parse HEAD)" "$AHEAD_HEAD"

# 7. Diverged histories must block.
DIVERGED=$(clone_case case-diverged)
printf '%s\n' local-diverged > "$DIVERGED/local-diverged.txt"
git -C "$DIVERGED" add local-diverged.txt
git -C "$DIVERGED" commit -q -m local_diverged
DIVERGED_HEAD=$(git -C "$DIVERGED" rev-parse HEAD)
commit_writer_file remote-diverged.txt remote remote_diverged
run_watcher "$DIVERGED" "$TEST_ROOT/state-diverged"
[ "$WATCH_CODE" -ne 0 ] || fail divergence_did_not_block
assert_contains divergence_block "$WATCH_OUTPUT" BLOCKED_LOCAL_AHEAD_OR_DIVERGED
assert_equal divergence_head_unchanged "$(git -C "$DIVERGED" rev-parse HEAD)" "$DIVERGED_HEAD"

# A clean pending task must also stop if remote main has advanced beyond the
# exact task commit; retry never wakes a stale task.
run_watcher_retry "$TASK_WAKE" "$TEST_ROOT/state-task-wake"
[ "$WATCH_CODE" -ne 0 ] || fail remote_moved_pending_retry_did_not_block
assert_contains remote_moved_pending_retry_block "$WATCH_OUTPUT" BLOCKED_PENDING_REMOTE_MOVED

# 8. An incoming watcher change must block before the worktree is updated and
# must not leave a retry-only pending event.
CRITICAL=$(clone_case case-critical)
CRITICAL_HEAD=$(git -C "$CRITICAL" rev-parse HEAD)
commit_writer_file tools/airjet-git-watcher/fixture.txt changed critical_watcher_update
CRITICAL_TARGET=$(git -C "$WRITER" rev-parse HEAD)
run_watcher "$CRITICAL" "$TEST_ROOT/state-critical"
[ "$WATCH_CODE" -ne 0 ] || fail critical_update_did_not_block
assert_contains critical_update_block "$WATCH_OUTPUT" BLOCKED_CRITICAL_WATCHER_UPDATE
assert_equal critical_head_unchanged "$(git -C "$CRITICAL" rev-parse HEAD)" "$CRITICAL_HEAD"
[ ! -f "$TEST_ROOT/state-critical/pending-event.state" ] || fail critical_update_left_pending
pass critical_update_no_pending

# 9. A legacy matching PULL_PENDING must not trap critical-update retry in a
# permanent loop.  This models state left by an earlier watcher version.
{
  printf '%s\n' 'schema_version=1'
  printf '%s\n' 'phase=PULL_PENDING'
  printf 'repo=%s\n' "$CRITICAL"
  printf 'old_commit=%s\n' "$CRITICAL_HEAD"
  printf 'new_commit=%s\n' "$CRITICAL_TARGET"
} > "$TEST_ROOT/state-critical/pending-event.state"
run_watcher_retry "$CRITICAL" "$TEST_ROOT/state-critical"
[ "$WATCH_CODE" -ne 0 ] || fail legacy_pending_critical_retry_did_not_block
assert_contains legacy_pending_critical_block "$WATCH_OUTPUT" BLOCKED_CRITICAL_WATCHER_UPDATE
[ ! -f "$TEST_ROOT/state-critical/pending-event.state" ] || fail legacy_critical_retry_left_pending
pass legacy_critical_retry_no_pending

# 10. A mismatched remote URL must block before network synchronization.
WRONG_REMOTE=$(clone_case case-wrong-remote)
git -C "$WRONG_REMOTE" remote set-url origin "$TEST_ROOT/not-the-origin.git"
run_watcher "$WRONG_REMOTE" "$TEST_ROOT/state-wrong-remote"
[ "$WATCH_CODE" -ne 0 ] || fail wrong_remote_did_not_block
assert_contains wrong_remote_block "$WATCH_OUTPUT" BLOCKED_WRONG_REMOTE

# 11. A changed envelope targeting another machine is invalid and cannot leave
# a pending wake event, although the safe data-only fast-forward is retained.
BAD_TARGET=$(clone_case case-bad-target)
{
  printf '%s\n' 'schema_version=1'
  printf '%s\n' 'target=windows'
  printf '%s\n' 'action=wake_codex'
  printf '%s\n' 'task_id=wrong-target'
  printf '%s\n' 'instruction_path=airjet-simulation/tasks/test-mac-task.md'
} > "$WRITER/airjet-simulation/collaboration/MAC_TASK.env"
git -C "$WRITER" add airjet-simulation/collaboration/MAC_TASK.env
git -C "$WRITER" commit -q -m invalid_target_envelope
git -C "$WRITER" push -q origin main
BAD_TARGET_COMMIT=$(git -C "$WRITER" rev-parse HEAD)
run_watcher "$BAD_TARGET" "$TEST_ROOT/state-bad-target"
[ "$WATCH_CODE" -ne 0 ] || fail bad_target_envelope_did_not_block
assert_contains bad_target_block "$WATCH_OUTPUT" 'BLOCKED_INVALID_MAC_TASK_ENVELOPE detail=bad_target'
assert_equal bad_target_synced_head "$(git -C "$BAD_TARGET" rev-parse HEAD)" "$BAD_TARGET_COMMIT"
[ ! -f "$TEST_ROOT/state-bad-target/pending-event.state" ] || fail bad_target_left_pending
pass bad_target_no_pending

# 12. Lexical traversal in instruction_path is rejected.
TRAVERSAL=$(clone_case case-traversal)
{
  printf '%s\n' 'schema_version=1'
  printf '%s\n' 'target=mac'
  printf '%s\n' 'action=wake_codex'
  printf '%s\n' 'task_id=traversal-test'
  printf '%s\n' 'instruction_path=airjet-simulation/../README.fixture'
} > "$WRITER/airjet-simulation/collaboration/MAC_TASK.env"
git -C "$WRITER" add airjet-simulation/collaboration/MAC_TASK.env
git -C "$WRITER" commit -q -m traversal_envelope
git -C "$WRITER" push -q origin main
run_watcher "$TRAVERSAL" "$TEST_ROOT/state-traversal"
[ "$WATCH_CODE" -ne 0 ] || fail traversal_envelope_did_not_block
assert_contains traversal_block "$WATCH_OUTPUT" 'BLOCKED_INVALID_MAC_TASK_ENVELOPE detail=unsafe_instruction_path'
[ ! -f "$TEST_ROOT/state-traversal/pending-event.state" ] || fail traversal_left_pending
pass traversal_no_pending

# 13. A Git symlink is not accepted as the committed instruction file.
SYMLINK_TASK=$(clone_case case-symlink-task)
ln -s ../../../outside-instruction.md "$WRITER/airjet-simulation/tasks/symlink-task.md"
{
  printf '%s\n' 'schema_version=1'
  printf '%s\n' 'target=mac'
  printf '%s\n' 'action=wake_codex'
  printf '%s\n' 'task_id=symlink-test'
  printf '%s\n' 'instruction_path=airjet-simulation/tasks/symlink-task.md'
} > "$WRITER/airjet-simulation/collaboration/MAC_TASK.env"
git -C "$WRITER" add airjet-simulation/collaboration/MAC_TASK.env airjet-simulation/tasks/symlink-task.md
git -C "$WRITER" commit -q -m symlink_instruction
git -C "$WRITER" push -q origin main
run_watcher "$SYMLINK_TASK" "$TEST_ROOT/state-symlink-task"
[ "$WATCH_CODE" -ne 0 ] || fail symlink_instruction_did_not_block
assert_contains symlink_instruction_block "$WATCH_OUTPUT" 'BLOCKED_INVALID_MAC_TASK_ENVELOPE detail=unsafe_instruction_object_type'
[ ! -f "$TEST_ROOT/state-symlink-task/pending-event.state" ] || fail symlink_instruction_left_pending
pass symlink_instruction_no_pending

# 14. Duplicate required fields are rejected.
DUPLICATE=$(clone_case case-duplicate-field)
{
  printf '%s\n' 'schema_version=1'
  printf '%s\n' 'target=mac'
  printf '%s\n' 'target=mac'
  printf '%s\n' 'action=wake_codex'
  printf '%s\n' 'task_id=duplicate-test'
  printf '%s\n' 'instruction_path=airjet-simulation/tasks/test-mac-task.md'
} > "$WRITER/airjet-simulation/collaboration/MAC_TASK.env"
git -C "$WRITER" add airjet-simulation/collaboration/MAC_TASK.env
git -C "$WRITER" commit -q -m duplicate_envelope_field
git -C "$WRITER" push -q origin main
run_watcher "$DUPLICATE" "$TEST_ROOT/state-duplicate"
[ "$WATCH_CODE" -ne 0 ] || fail duplicate_field_did_not_block
assert_contains duplicate_field_block "$WATCH_OUTPUT" 'BLOCKED_INVALID_MAC_TASK_ENVELOPE detail=field_target_count_2'
[ ! -f "$TEST_ROOT/state-duplicate/pending-event.state" ] || fail duplicate_field_left_pending
pass duplicate_field_no_pending

# 15. Unknown fields and directory objects are rejected independently.
UNKNOWN=$(clone_case case-unknown-field)
{
  printf '%s\n' 'schema_version=1'
  printf '%s\n' 'target=mac'
  printf '%s\n' 'action=wake_codex'
  printf '%s\n' 'task_id=unknown-field-test'
  printf '%s\n' 'instruction_path=airjet-simulation/tasks/test-mac-task.md'
  printf '%s\n' 'unexpected=value'
} > "$WRITER/airjet-simulation/collaboration/MAC_TASK.env"
git -C "$WRITER" add airjet-simulation/collaboration/MAC_TASK.env
git -C "$WRITER" commit -q -m unknown_envelope_field
git -C "$WRITER" push -q origin main
run_watcher "$UNKNOWN" "$TEST_ROOT/state-unknown"
[ "$WATCH_CODE" -ne 0 ] || fail unknown_field_did_not_block
assert_contains unknown_field_block "$WATCH_OUTPUT" 'BLOCKED_INVALID_MAC_TASK_ENVELOPE detail=unknown_or_malformed_field'
[ ! -f "$TEST_ROOT/state-unknown/pending-event.state" ] || fail unknown_field_left_pending
pass unknown_field_no_pending

TREE_TASK=$(clone_case case-tree-task)
{
  printf '%s\n' 'schema_version=1'
  printf '%s\n' 'target=mac'
  printf '%s\n' 'action=wake_codex'
  printf '%s\n' 'task_id=tree-test'
  printf '%s\n' 'instruction_path=airjet-simulation/tasks'
} > "$WRITER/airjet-simulation/collaboration/MAC_TASK.env"
git -C "$WRITER" add airjet-simulation/collaboration/MAC_TASK.env
git -C "$WRITER" commit -q -m tree_instruction
git -C "$WRITER" push -q origin main
run_watcher "$TREE_TASK" "$TEST_ROOT/state-tree-task"
[ "$WATCH_CODE" -ne 0 ] || fail tree_instruction_did_not_block
assert_contains tree_instruction_block "$WATCH_OUTPUT" 'BLOCKED_INVALID_MAC_TASK_ENVELOPE detail=unsafe_instruction_object_type'
[ ! -f "$TEST_ROOT/state-tree-task/pending-event.state" ] || fail tree_instruction_left_pending
pass tree_instruction_no_pending

# The same legacy phase must be cleared even when remote main advanced beyond
# the originally recorded target before retry.
{
  printf '%s\n' 'schema_version=1'
  printf '%s\n' 'phase=PULL_PENDING'
  printf 'repo=%s\n' "$CRITICAL"
  printf 'old_commit=%s\n' "$CRITICAL_HEAD"
  printf 'new_commit=%s\n' "$CRITICAL_TARGET"
} > "$TEST_ROOT/state-critical/pending-event.state"
run_watcher_retry "$CRITICAL" "$TEST_ROOT/state-critical"
[ "$WATCH_CODE" -ne 0 ] || fail advanced_legacy_pending_critical_retry_did_not_block
assert_contains advanced_legacy_pending_critical_block "$WATCH_OUTPUT" BLOCKED_CRITICAL_WATCHER_UPDATE
[ ! -f "$TEST_ROOT/state-critical/pending-event.state" ] || fail advanced_legacy_critical_retry_left_pending
pass advanced_legacy_critical_retry_no_pending

# 16. The state root itself and its writable child directories must not resolve
# inside the repository.
STATE_INSIDE=$(clone_case case-state-inside)
run_watcher "$STATE_INSIDE" "$STATE_INSIDE/.watcher-state"
[ "$WATCH_CODE" -ne 0 ] || fail state_root_inside_repo_did_not_block
assert_contains state_root_boundary_output "$WATCH_OUTPUT" BLOCKED_STATE_ROOT_INSIDE_REPOSITORY
[ ! -d "$STATE_INSIDE/.watcher-state" ] || fail state_root_inside_repo_was_created
pass state_root_not_created

STATE_CHILD=$(clone_case case-state-child-symlink)
mkdir -p "$TEST_ROOT/state-child-symlink"
ln -s "$STATE_CHILD/airjet-simulation/collaboration" "$TEST_ROOT/state-child-symlink/events"
run_watcher "$STATE_CHILD" "$TEST_ROOT/state-child-symlink"
[ "$WATCH_CODE" -ne 0 ] || fail state_child_symlink_did_not_block
assert_contains state_child_symlink_block "$WATCH_OUTPUT" BLOCKED_EVENT_ROOT_NOT_DIRECT_STATE_CHILD
assert_equal state_child_repo_clean "$(git -C "$STATE_CHILD" status --porcelain)" ''

STATE_LOG=$(clone_case case-state-log-symlink)
mkdir -p "$TEST_ROOT/state-log-symlink/events"
ln -s "$STATE_LOG/airjet-simulation/collaboration" "$TEST_ROOT/state-log-symlink/logs"
run_watcher "$STATE_LOG" "$TEST_ROOT/state-log-symlink"
[ "$WATCH_CODE" -ne 0 ] || fail state_log_symlink_did_not_block
assert_contains state_log_symlink_block "$WATCH_OUTPUT" BLOCKED_LOG_ROOT_NOT_DIRECT_STATE_CHILD
assert_equal state_log_repo_clean "$(git -C "$STATE_LOG" status --porcelain)" ''

# 17. The runner's dedicated report directory cannot be replaced by a symlink
# or redirected inside the repository.
RUNNER_HOME=$TEST_ROOT/runner-home
RUNNER_STATE=$TEST_ROOT/runner-state
RUNNER_TARGET=$TEST_ROOT/runner-report-target
mkdir -p "$RUNNER_HOME/Downloads" "$RUNNER_STATE/events" "$RUNNER_TARGET"
ln -s "$RUNNER_TARGET" "$RUNNER_HOME/Downloads/AirJetGitWatcherReports"
set +e
RUNNER_OUTPUT=$(env HOME="$RUNNER_HOME" AIRJET_REPO_ROOT="$STATE_CHILD" AIRJET_WATCHER_STATE_ROOT="$RUNNER_STATE" \
  /bin/sh "$RUNNER" missing-prompt 0000000000000000000000000000000000000000 1111111111111111111111111111111111111111 2>&1)
RUNNER_CODE=$?
set -e
[ "$RUNNER_CODE" -ne 0 ] || fail report_root_symlink_did_not_block
assert_contains report_root_symlink_block "$RUNNER_OUTPUT" BLOCKED_REPORT_ROOT_SYMLINK

REPORT_INSIDE=$(clone_case case-report-inside-repo)
REPORT_INSIDE_HOME=$REPORT_INSIDE/fake-home
REPORT_INSIDE_STATE=$TEST_ROOT/report-inside-state
mkdir -p "$REPORT_INSIDE_HOME/Downloads" "$REPORT_INSIDE_STATE/events"
set +e
REPORT_INSIDE_OUTPUT=$(env HOME="$REPORT_INSIDE_HOME" AIRJET_REPO_ROOT="$REPORT_INSIDE" AIRJET_WATCHER_STATE_ROOT="$REPORT_INSIDE_STATE" \
  /bin/sh "$RUNNER" missing-prompt 0000000000000000000000000000000000000000 1111111111111111111111111111111111111111 2>&1)
REPORT_INSIDE_CODE=$?
set -e
[ "$REPORT_INSIDE_CODE" -ne 0 ] || fail report_root_inside_repo_did_not_block
assert_contains report_root_inside_repo_block "$REPORT_INSIDE_OUTPUT" BLOCKED_REPORT_ROOT_INSIDE_REPOSITORY
[ ! -e "$REPORT_INSIDE_HOME/Downloads/AirJetGitWatcherReports" ] || fail report_root_inside_repo_was_created
pass report_root_inside_repo_not_created

# 18. Exercise the manager guard itself; a marker string alone is insufficient.
MANAGER_STATE=$TEST_ROOT/manager-state
set +e
MANAGER_START_OUTPUT=$(env AIRJET_WATCHER_STATE_ROOT="$MANAGER_STATE" /bin/sh "$MANAGER" start 2>&1)
MANAGER_START_CODE=$?
MANAGER_RETRY_OUTPUT=$(env AIRJET_WATCHER_STATE_ROOT="$MANAGER_STATE" /bin/sh "$MANAGER" retry 2>&1)
MANAGER_RETRY_CODE=$?
set -e
[ "$MANAGER_START_CODE" -ne 0 ] || fail manager_start_was_not_disabled
assert_contains manager_start_disabled "$MANAGER_START_OUTPUT" START_RESULT=REFUSED_DISABLED_PENDING_HARDENING
[ "$MANAGER_RETRY_CODE" -ne 0 ] || fail manager_retry_was_not_disabled
assert_contains manager_retry_disabled "$MANAGER_RETRY_OUTPUT" RETRY_RESULT=REFUSED_DISABLED_PENDING_HARDENING

TARGET_ENVELOPE_GATE=BEHAVIOR_TESTED
RUNTIME_DISABLE_GUARD=BEHAVIOR_TESTED
STATE_ROOT_REPO_BOUNDARY=BEHAVIOR_TESTED
REPORT_ROOT_BOUNDARY=BEHAVIOR_TESTED

printf 'CORE_CASES_PASS=%s\n' "$PASS_COUNT"
printf 'TARGET_ENVELOPE_GATE=%s\n' "$TARGET_ENVELOPE_GATE"
printf 'RUNTIME_DISABLE_GUARD=%s\n' "$RUNTIME_DISABLE_GUARD"
printf 'STATE_ROOT_REPO_BOUNDARY=%s\n' "$STATE_ROOT_REPO_BOUNDARY"
printf 'REPORT_ROOT_BOUNDARY=%s\n' "$REPORT_ROOT_BOUNDARY"
printf '%s\n' 'VISIBLE_WAKE_TEST=SKIPPED_BY_DESIGN'
printf '%s\n' 'OVERALL=PASS_CORE_RUNTIME_DISABLED'
