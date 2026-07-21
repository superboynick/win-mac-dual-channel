#!/bin/sh
set -eu

# Local-only functional tests for the macOS watcher.  The suite never contacts
# GitHub and never invokes the visible wake path.

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
WATCHER=$(CDPATH= cd -- "$SCRIPT_DIR/../mac" && pwd -P)/watch-airjet-git.sh
MANAGER=$(CDPATH= cd -- "$SCRIPT_DIR/../mac" && pwd -P)/manage-airjet-watcher.sh
RUNNER=$(CDPATH= cd -- "$SCRIPT_DIR/../mac" && pwd -P)/run-awakened-codex.sh
INSTALLER=$(CDPATH= cd -- "$SCRIPT_DIR/../mac" && pwd -P)/install-mac-watcher.sh
TMP_BASE=${TMPDIR:-/private/tmp}
TMP_BASE=$(CDPATH= cd -- "$TMP_BASE" && pwd -P)
TEST_ROOT=$(mktemp -d "$TMP_BASE/airjet-watcher-test.XXXXXX")
ORIGIN=$TEST_ROOT/origin.git
SEED=$TEST_ROOT/seed
WRITER=$TEST_ROOT/writer
PASS_COUNT=0
MAC_TEST_KEY=$TEST_ROOT/mac-signing
WINDOWS_TEST_KEY=$TEST_ROOT/windows-signing
TEST_TRUST=$TEST_ROOT/trust-template

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
  role=${2:-windows}
  case "$role" in
    mac) name=AirJetMacTest; email=airjet-mac@airjet.local; key=$MAC_TEST_KEY ;;
    windows) name=AirJetWindowsTest; email=airjet-windows@airjet.local; key=$WINDOWS_TEST_KEY ;;
    *) fail "unknown test signing role: $role" ;;
  esac
  git -C "$repo" config user.name "$name"
  git -C "$repo" config user.email "$email"
  git -C "$repo" config gpg.format ssh
  git -C "$repo" config user.signingkey "$key"
  git -C "$repo" config commit.gpgsign true
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
  trust_mode=${3:-install}
  expected_remote=${4:-$ORIGIN}
  [ "$trust_mode" = skip ] || install_test_trust "$state"
  set +e
  WATCH_OUTPUT=$(env \
    AIRJET_WATCHER_TEST_MODE=1 \
    AIRJET_REPO_ROOT="$repo" \
    AIRJET_EXPECTED_REMOTE="$expected_remote" \
    AIRJET_WATCHER_STATE_ROOT="$state" \
    /bin/sh "$WATCHER" --poll-seconds 10 --once --no-wake 2>&1)
  WATCH_CODE=$?
  set -e
}

write_mac_task() {
  repo=$1
  task_id=$2
  workflow_id=$3
  instruction_name=$4
  instruction_path=airjet-simulation/collaboration/instructions/$instruction_name
  mkdir -p "$repo/airjet-simulation/collaboration/instructions"
  printf '# isolated instruction for %s\n' "$task_id" > "$repo/$instruction_path"
  {
    printf '%s\n' 'schema_version=2'
    printf '%s\n' 'type=task'
    printf '%s\n' 'source=windows'
    printf '%s\n' 'target=mac'
    printf '%s\n' 'action=wake_codex'
    printf 'task_id=%s\n' "$task_id"
    printf 'workflow_id=%s\n' "$workflow_id"
    printf '%s\n' 'parent_task_id=NONE'
    printf '%s\n' 'hop=0'
    printf '%s\n' 'max_hops=0'
    printf 'instruction_path=%s\n' "$instruction_path"
  } > "$repo/airjet-simulation/collaboration/MAC_TASK.env"
}

run_watcher_retry() {
  repo=$1
  state=$2
  install_test_trust "$state"
  set +e
  WATCH_OUTPUT=$(env \
    AIRJET_WATCHER_TEST_MODE=1 \
    AIRJET_REPO_ROOT="$repo" \
    AIRJET_EXPECTED_REMOTE="$ORIGIN" \
    AIRJET_WATCHER_STATE_ROOT="$state" \
    /bin/sh "$WATCHER" --poll-seconds 10 --once --no-wake --retry-pending 2>&1)
  WATCH_CODE=$?
  set -e
}

install_test_trust() {
  state=$1
  mkdir -p "$state/trust"
  cp "$TEST_TRUST/allowed_signers" "$state/trust/allowed_signers"
  cp "$TEST_TRUST/windows_task_signers" "$state/trust/windows_task_signers"
  cp "$TEST_TRUST/revoked_keys.krl" "$state/trust/revoked_keys.krl"
  chmod 700 "$state/trust"
  chmod 600 "$state/trust/allowed_signers" "$state/trust/windows_task_signers" "$state/trust/revoked_keys.krl"
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
[ -f "$INSTALLER" ] || fail "installer missing: $INSTALLER"
/bin/sh -n "$WATCHER"
/bin/sh -n "$MANAGER"
/bin/sh -n "$RUNNER"
/bin/sh -n "$INSTALLER"
pass shell_syntax
[ "$(grep -c '^RUNTIME_STATUS=ENABLED_AFTER_REVIEW$' "$WATCHER")" -eq 1 ] || fail watcher_runtime_status_missing
[ "$(grep -c '^RUNTIME_STATUS=ENABLED_AFTER_REVIEW$' "$MANAGER")" -eq 1 ] || fail manager_runtime_status_missing
[ "$(grep -c '^RUNTIME_STATUS=ENABLED_AFTER_REVIEW$' "$RUNNER")" -eq 1 ] || fail runner_runtime_status_missing
grep -q 'INSTALL_RESULT=REFUSED_DISABLED_PENDING_END_TO_END' "$INSTALLER" || fail installer_runtime_guard_missing
grep -q '<key>KeepAlive</key><dict><key>SuccessfulExit</key><false/></dict>' "$INSTALLER" || fail installer_failure_restart_missing
grep -q '<key>ThrottleInterval</key><integer>60</integer>' "$INSTALLER" || fail installer_restart_throttle_missing
pass runtime_guard_source

ssh-keygen -q -t ed25519 -N '' -C airjet-mac-test -f "$MAC_TEST_KEY"
ssh-keygen -q -t ed25519 -N '' -C airjet-windows-test -f "$WINDOWS_TEST_KEY"
mkdir -p "$TEST_TRUST"
{
  printf 'airjet-mac@airjet.local namespaces="git" '
  cat "$MAC_TEST_KEY.pub"
  printf 'airjet-windows@airjet.local namespaces="git" '
  cat "$WINDOWS_TEST_KEY.pub"
} > "$TEST_TRUST/allowed_signers"
{
  printf 'airjet-windows@airjet.local namespaces="git" '
  cat "$WINDOWS_TEST_KEY.pub"
} > "$TEST_TRUST/windows_task_signers"
ssh-keygen -q -k -f "$TEST_TRUST/revoked_keys.krl"
chmod 600 "$TEST_TRUST/allowed_signers" "$TEST_TRUST/windows_task_signers" "$TEST_TRUST/revoked_keys.krl"
pass signing_fixture

git init -q --bare "$ORIGIN"
git --git-dir="$ORIGIN" symbolic-ref HEAD refs/heads/main
git init -q "$SEED"
configure_identity "$SEED" mac
git -C "$SEED" checkout -q -b main
mkdir -p "$SEED/tools/airjet-git-watcher"
printf '%s\n' baseline > "$SEED/README.fixture"
printf '%s\n' baseline > "$SEED/tools/airjet-git-watcher/fixture.txt"
git -C "$SEED" add README.fixture tools/airjet-git-watcher/fixture.txt
git -C "$SEED" commit -q -m baseline
git -C "$SEED" remote add origin "$ORIGIN"
git -C "$SEED" push -q -u origin main
git clone -q "$ORIGIN" "$WRITER"
configure_identity "$WRITER" windows

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
TASK_OLD=$(git -C "$TASK_WAKE" rev-parse HEAD)
mkdir -p "$WRITER/airjet-simulation/collaboration/instructions"
printf '%s\n' '# isolated test instruction' > "$WRITER/airjet-simulation/collaboration/instructions/test-mac-task.md"
{
  printf '%s\n' 'schema_version=2'
  printf '%s\n' 'type=task'
  printf '%s\n' 'source=windows'
  printf '%s\n' 'target=mac'
  printf '%s\n' 'action=wake_codex'
  printf '%s\n' 'task_id=isolated-watcher-test'
  printf '%s\n' 'workflow_id=isolated-workflow'
  printf '%s\n' 'parent_task_id=NONE'
  printf '%s\n' 'hop=0'
  printf '%s\n' 'max_hops=0'
  printf '%s\n' 'instruction_path=airjet-simulation/collaboration/instructions/test-mac-task.md'
} > "$WRITER/airjet-simulation/collaboration/MAC_TASK.env"
git -C "$WRITER" add airjet-simulation/collaboration/MAC_TASK.env airjet-simulation/collaboration/instructions/test-mac-task.md
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
  printf '%s\n' 'schema_version=2'
  printf '%s\n' 'type=task'
  printf '%s\n' 'source=windows'
  printf '%s\n' 'target=mac'
  printf '%s\n' 'action=wake_codex'
  printf '%s\n' 'task_id=tampered-local-state'
  printf '%s\n' 'workflow_id=tampered-workflow'
  printf '%s\n' 'parent_task_id=NONE'
  printf '%s\n' 'hop=0'
  printf '%s\n' 'max_hops=0'
  printf '%s\n' 'instruction_path=airjet-simulation/collaboration/instructions/test-mac-task.md'
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
  printf '%s\n' 'schema_version=2'
  printf '%s\n' 'type=task'
  printf '%s\n' 'source=windows'
  printf '%s\n' 'target=windows'
  printf '%s\n' 'action=wake_codex'
  printf '%s\n' 'task_id=wrong-target'
  printf '%s\n' 'workflow_id=wrong-target-workflow'
  printf '%s\n' 'parent_task_id=NONE'
  printf '%s\n' 'hop=0'
  printf '%s\n' 'max_hops=0'
  printf '%s\n' 'instruction_path=airjet-simulation/collaboration/instructions/test-mac-task.md'
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

# Automatic reciprocal relay is deliberately disabled in the first release.
RELAY=$(clone_case case-relay-disabled)
{
  printf '%s\n' 'schema_version=2'
  printf '%s\n' 'type=task'
  printf '%s\n' 'source=windows'
  printf '%s\n' 'target=mac'
  printf '%s\n' 'action=wake_codex'
  printf '%s\n' 'task_id=relay-disabled-test'
  printf '%s\n' 'workflow_id=relay-disabled-workflow'
  printf '%s\n' 'parent_task_id=previous-task'
  printf '%s\n' 'hop=1'
  printf '%s\n' 'max_hops=2'
  printf '%s\n' 'instruction_path=airjet-simulation/collaboration/instructions/test-mac-task.md'
} > "$WRITER/airjet-simulation/collaboration/MAC_TASK.env"
git -C "$WRITER" add airjet-simulation/collaboration/MAC_TASK.env
git -C "$WRITER" commit -q -m relay_disabled_envelope
git -C "$WRITER" push -q origin main
RELAY_COMMIT=$(git -C "$WRITER" rev-parse HEAD)
run_watcher "$RELAY" "$TEST_ROOT/state-relay"
[ "$WATCH_CODE" -ne 0 ] || fail automatic_relay_did_not_block
assert_contains automatic_relay_block "$WATCH_OUTPUT" 'BLOCKED_INVALID_MAC_TASK_ENVELOPE detail=automatic_relay_not_enabled'
assert_equal automatic_relay_data_synced "$(git -C "$RELAY" rev-parse HEAD)" "$RELAY_COMMIT"
[ ! -f "$TEST_ROOT/state-relay/pending-event.state" ] || fail automatic_relay_left_pending
pass automatic_relay_no_pending

# 12. Lexical traversal in instruction_path is rejected.
TRAVERSAL=$(clone_case case-traversal)
{
  printf '%s\n' 'schema_version=2'
  printf '%s\n' 'type=task'
  printf '%s\n' 'source=windows'
  printf '%s\n' 'target=mac'
  printf '%s\n' 'action=wake_codex'
  printf '%s\n' 'task_id=traversal-test'
  printf '%s\n' 'workflow_id=traversal-workflow'
  printf '%s\n' 'parent_task_id=NONE'
  printf '%s\n' 'hop=0'
  printf '%s\n' 'max_hops=0'
  printf '%s\n' 'instruction_path=airjet-simulation/collaboration/instructions/../instructions/test-mac-task.md'
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
ln -s ../../../../outside-instruction.md "$WRITER/airjet-simulation/collaboration/instructions/symlink-task.md"
{
  printf '%s\n' 'schema_version=2'
  printf '%s\n' 'type=task'
  printf '%s\n' 'source=windows'
  printf '%s\n' 'target=mac'
  printf '%s\n' 'action=wake_codex'
  printf '%s\n' 'task_id=symlink-test'
  printf '%s\n' 'workflow_id=symlink-workflow'
  printf '%s\n' 'parent_task_id=NONE'
  printf '%s\n' 'hop=0'
  printf '%s\n' 'max_hops=0'
  printf '%s\n' 'instruction_path=airjet-simulation/collaboration/instructions/symlink-task.md'
} > "$WRITER/airjet-simulation/collaboration/MAC_TASK.env"
git -C "$WRITER" add airjet-simulation/collaboration/MAC_TASK.env airjet-simulation/collaboration/instructions/symlink-task.md
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
  printf '%s\n' 'schema_version=2'
  printf '%s\n' 'type=task'
  printf '%s\n' 'source=windows'
  printf '%s\n' 'target=mac'
  printf '%s\n' 'target=mac'
  printf '%s\n' 'action=wake_codex'
  printf '%s\n' 'task_id=duplicate-test'
  printf '%s\n' 'workflow_id=duplicate-workflow'
  printf '%s\n' 'parent_task_id=NONE'
  printf '%s\n' 'hop=0'
  printf '%s\n' 'max_hops=0'
  printf '%s\n' 'instruction_path=airjet-simulation/collaboration/instructions/test-mac-task.md'
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
  printf '%s\n' 'schema_version=2'
  printf '%s\n' 'type=task'
  printf '%s\n' 'source=windows'
  printf '%s\n' 'target=mac'
  printf '%s\n' 'action=wake_codex'
  printf '%s\n' 'task_id=unknown-field-test'
  printf '%s\n' 'workflow_id=unknown-workflow'
  printf '%s\n' 'parent_task_id=NONE'
  printf '%s\n' 'hop=0'
  printf '%s\n' 'max_hops=0'
  printf '%s\n' 'instruction_path=airjet-simulation/collaboration/instructions/test-mac-task.md'
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
mkdir -p "$WRITER/airjet-simulation/collaboration/instructions/nested"
printf '%s\n' nested > "$WRITER/airjet-simulation/collaboration/instructions/nested/file.md"
{
  printf '%s\n' 'schema_version=2'
  printf '%s\n' 'type=task'
  printf '%s\n' 'source=windows'
  printf '%s\n' 'target=mac'
  printf '%s\n' 'action=wake_codex'
  printf '%s\n' 'task_id=tree-test'
  printf '%s\n' 'workflow_id=tree-workflow'
  printf '%s\n' 'parent_task_id=NONE'
  printf '%s\n' 'hop=0'
  printf '%s\n' 'max_hops=0'
  printf '%s\n' 'instruction_path=airjet-simulation/collaboration/instructions/nested'
} > "$WRITER/airjet-simulation/collaboration/MAC_TASK.env"
git -C "$WRITER" add airjet-simulation/collaboration/MAC_TASK.env airjet-simulation/collaboration/instructions/nested/file.md
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
run_watcher "$STATE_INSIDE" "$STATE_INSIDE/.watcher-state" skip
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

# 17. The runner's dedicated report directory cannot be replaced by a symlink.
# Use a pinned local origin at the signed task commit so runner revalidation is
# real and cannot be bypassed by mutable state.
RUNNER_HOME=$TEST_ROOT/runner-home
RUNNER_STATE=$TEST_ROOT/runner-state
RUNNER_TARGET=$TEST_ROOT/runner-report-target
RUNNER_ORIGIN=$TEST_ROOT/runner-origin.git
git clone -q --bare "$TASK_WAKE" "$RUNNER_ORIGIN"
git -C "$TASK_WAKE" remote set-url origin "$RUNNER_ORIGIN"
git -C "$TASK_WAKE" fetch -q origin
mkdir -p "$RUNNER_HOME/Downloads" "$RUNNER_STATE/events" "$RUNNER_STATE/processed" "$RUNNER_TARGET"
install_test_trust "$RUNNER_STATE"
printf '%s\n' prompt-handle > "$RUNNER_STATE/events/wake-$TASK_TARGET.txt"
{
  printf '%s\n' 'schema_version=1'
  printf '%s\n' 'phase=WAKE_REQUESTED'
  printf 'repo=%s\n' "$TASK_WAKE"
  printf 'old_commit=%s\n' "$TASK_OLD"
  printf 'new_commit=%s\n' "$TASK_TARGET"
  printf '%s\n' 'task_id=isolated-watcher-test'
  printf '%s\n' 'workflow_id=isolated-workflow'
  printf '%s\n' 'parent_task_id=NONE'
  printf '%s\n' 'hop=0'
  printf '%s\n' 'max_hops=0'
  printf '%s\n' 'instruction_path=airjet-simulation/collaboration/instructions/test-mac-task.md'
} > "$RUNNER_STATE/pending-event.state"
ln -s "$RUNNER_TARGET" "$RUNNER_HOME/Downloads/AirJetGitWatcherReports"
set +e
RUNNER_OUTPUT=$(env HOME="$RUNNER_HOME" AIRJET_WATCHER_TEST_MODE=1 AIRJET_REPO_ROOT="$TASK_WAKE" \
  AIRJET_TEST_RUNNER_MODE=path-check \
  AIRJET_EXPECTED_REMOTE="$RUNNER_ORIGIN" AIRJET_WATCHER_STATE_ROOT="$RUNNER_STATE" \
  /bin/sh "$RUNNER" "$RUNNER_STATE/events/wake-$TASK_TARGET.txt" "$TASK_OLD" "$TASK_TARGET" 2>&1)
RUNNER_CODE=$?
set -e
[ "$RUNNER_CODE" -ne 0 ] || fail report_root_symlink_did_not_block
assert_contains report_root_symlink_block "$RUNNER_OUTPUT" BLOCKED_REPORT_ROOT_SYMLINK

# The runner validator must reject a mutable pending task ID before any test-mode
# path handling. This proves the validator call itself is exercised.
RUNNER_VALIDATE_HOME=$TEST_ROOT/runner-validate-home
mkdir -p "$RUNNER_VALIDATE_HOME/Downloads"
sed 's/^task_id=isolated-watcher-test$/task_id=tampered-runner-task/' \
  "$RUNNER_STATE/pending-event.state" > "$RUNNER_STATE/pending-event.state.tmp"
mv "$RUNNER_STATE/pending-event.state.tmp" "$RUNNER_STATE/pending-event.state"
set +e
RUNNER_VALIDATE_OUTPUT=$(env HOME="$RUNNER_VALIDATE_HOME" AIRJET_WATCHER_TEST_MODE=1 AIRJET_REPO_ROOT="$TASK_WAKE" \
  AIRJET_TEST_RUNNER_MODE=validate-only \
  AIRJET_EXPECTED_REMOTE="$RUNNER_ORIGIN" AIRJET_WATCHER_STATE_ROOT="$RUNNER_STATE" \
  /bin/sh "$RUNNER" "$RUNNER_STATE/events/wake-$TASK_TARGET.txt" "$TASK_OLD" "$TASK_TARGET" 2>&1)
RUNNER_VALIDATE_CODE=$?
set -e
[ "$RUNNER_VALIDATE_CODE" -ne 0 ] || fail tampered_runner_task_id_did_not_block
assert_contains tampered_runner_task_id_block "$RUNNER_VALIDATE_OUTPUT" 'BLOCKED_PENDING_TASK_REVALIDATION detail=task_id_mismatch'

# 18. An unsigned incoming commit must be rejected before fast-forward.
UNSIGNED_ORIGIN=$TEST_ROOT/unsigned-origin.git
UNSIGNED_WRITER=$TEST_ROOT/unsigned-writer
UNSIGNED_CASE=$TEST_ROOT/case-unsigned
git clone -q --bare "$ORIGIN" "$UNSIGNED_ORIGIN"
git clone -q "$UNSIGNED_ORIGIN" "$UNSIGNED_CASE"
git clone -q "$UNSIGNED_ORIGIN" "$UNSIGNED_WRITER"
configure_identity "$UNSIGNED_WRITER" windows
git -C "$UNSIGNED_CASE" config gpg.ssh.program /usr/bin/true
git -C "$UNSIGNED_WRITER" config commit.gpgsign false
UNSIGNED_OLD=$(git -C "$UNSIGNED_CASE" rev-parse HEAD)
printf '%s\n' unsigned > "$UNSIGNED_WRITER/unsigned.txt"
git -C "$UNSIGNED_WRITER" add unsigned.txt
git -C "$UNSIGNED_WRITER" commit -q -m unsigned_incoming
git -C "$UNSIGNED_WRITER" push -q origin main
run_watcher "$UNSIGNED_CASE" "$TEST_ROOT/state-unsigned" install "$UNSIGNED_ORIGIN"
[ "$WATCH_CODE" -ne 0 ] || fail unsigned_commit_did_not_block
assert_contains unsigned_commit_block "$WATCH_OUTPUT" BLOCKED_UNTRUSTED_COMMIT
assert_equal unsigned_head_unchanged "$(git -C "$UNSIGNED_CASE" rev-parse HEAD)" "$UNSIGNED_OLD"
[ ! -f "$TEST_ROOT/state-unsigned/pending-event.state" ] || fail unsigned_commit_left_pending
pass unsigned_commit_no_pending

# 19. A task signed by the target Mac key is allowed as repository history but
# cannot authorize a Windows-to-Mac wake.
SELF_ORIGIN=$TEST_ROOT/self-signed-origin.git
SELF_WRITER=$TEST_ROOT/self-signed-writer
SELF_CASE=$TEST_ROOT/case-self-signed
git clone -q --bare "$ORIGIN" "$SELF_ORIGIN"
git clone -q "$SELF_ORIGIN" "$SELF_CASE"
git clone -q "$SELF_ORIGIN" "$SELF_WRITER"
configure_identity "$SELF_WRITER" mac
write_mac_task "$SELF_WRITER" self-signed-task self-signed-workflow self-signed.md
git -C "$SELF_WRITER" add airjet-simulation/collaboration/MAC_TASK.env airjet-simulation/collaboration/instructions/self-signed.md
git -C "$SELF_WRITER" commit -q -m self_signed_mac_task
git -C "$SELF_WRITER" push -q origin main
SELF_TARGET=$(git -C "$SELF_WRITER" rev-parse HEAD)
run_watcher "$SELF_CASE" "$TEST_ROOT/state-self-signed" install "$SELF_ORIGIN"
[ "$WATCH_CODE" -ne 0 ] || fail self_signed_task_did_not_block
assert_contains self_signed_task_block "$WATCH_OUTPUT" 'BLOCKED_INVALID_MAC_TASK_ENVELOPE detail=task_tip_not_signed_by_windows_peer'
assert_equal self_signed_task_data_synced "$(git -C "$SELF_CASE" rev-parse HEAD)" "$SELF_TARGET"
[ ! -f "$TEST_ROOT/state-self-signed/pending-event.state" ] || fail self_signed_task_left_pending
pass self_signed_task_no_pending

# 20. A valid task commit followed by another signed commit is ambiguous and
# must not authorize execution because the task is no longer the target tip.
NONTIP_ORIGIN=$TEST_ROOT/nontip-origin.git
NONTIP_WRITER=$TEST_ROOT/nontip-writer
NONTIP_CASE=$TEST_ROOT/case-nontip
git clone -q --bare "$ORIGIN" "$NONTIP_ORIGIN"
git clone -q "$NONTIP_ORIGIN" "$NONTIP_CASE"
git clone -q "$NONTIP_ORIGIN" "$NONTIP_WRITER"
configure_identity "$NONTIP_WRITER" windows
write_mac_task "$NONTIP_WRITER" nontip-task nontip-workflow nontip.md
git -C "$NONTIP_WRITER" add airjet-simulation/collaboration/MAC_TASK.env airjet-simulation/collaboration/instructions/nontip.md
git -C "$NONTIP_WRITER" commit -q -m nontip_task
printf '%s\n' after-task > "$NONTIP_WRITER/after-task.txt"
git -C "$NONTIP_WRITER" add after-task.txt
git -C "$NONTIP_WRITER" commit -q -m after_task
git -C "$NONTIP_WRITER" push -q origin main
NONTIP_TARGET=$(git -C "$NONTIP_WRITER" rev-parse HEAD)
run_watcher "$NONTIP_CASE" "$TEST_ROOT/state-nontip" install "$NONTIP_ORIGIN"
[ "$WATCH_CODE" -ne 0 ] || fail nontip_task_did_not_block
assert_contains nontip_task_block "$WATCH_OUTPUT" 'BLOCKED_INVALID_MAC_TASK_ENVELOPE detail=task_commit_not_target_tip'
assert_equal nontip_task_data_synced "$(git -C "$NONTIP_CASE" rev-parse HEAD)" "$NONTIP_TARGET"
[ ! -f "$TEST_ROOT/state-nontip/pending-event.state" ] || fail nontip_task_left_pending
pass nontip_task_no_pending

# 21. Automatic mode rejects merge commits even when every commit is signed.
MERGE_ORIGIN=$TEST_ROOT/merge-origin.git
MERGE_WRITER=$TEST_ROOT/merge-writer
MERGE_CASE=$TEST_ROOT/case-merge
git clone -q --bare "$ORIGIN" "$MERGE_ORIGIN"
git clone -q "$MERGE_ORIGIN" "$MERGE_CASE"
git clone -q "$MERGE_ORIGIN" "$MERGE_WRITER"
configure_identity "$MERGE_WRITER" windows
MERGE_OLD=$(git -C "$MERGE_CASE" rev-parse HEAD)
git -C "$MERGE_WRITER" checkout -q -b signed-side
printf '%s\n' signed-side > "$MERGE_WRITER/signed-side.txt"
git -C "$MERGE_WRITER" add signed-side.txt
git -C "$MERGE_WRITER" commit -q -m signed_side
git -C "$MERGE_WRITER" checkout -q main
printf '%s\n' signed-main > "$MERGE_WRITER/signed-main.txt"
git -C "$MERGE_WRITER" add signed-main.txt
git -C "$MERGE_WRITER" commit -q -m signed_main
git -C "$MERGE_WRITER" merge -q --no-ff signed-side -m signed_merge
git -C "$MERGE_WRITER" push -q origin main
run_watcher "$MERGE_CASE" "$TEST_ROOT/state-merge" install "$MERGE_ORIGIN"
[ "$WATCH_CODE" -ne 0 ] || fail merge_commit_did_not_block
assert_contains merge_commit_block "$WATCH_OUTPUT" 'BLOCKED_SIGNATURE_RANGE_INVALID detail=merge_commit_present'
assert_equal merge_head_unchanged "$(git -C "$MERGE_CASE" rev-parse HEAD)" "$MERGE_OLD"

# 22. One commit cannot request both endpoint wakeups.
DUAL_ORIGIN=$TEST_ROOT/dual-origin.git
DUAL_WRITER=$TEST_ROOT/dual-writer
DUAL_CASE=$TEST_ROOT/case-dual
git clone -q --bare "$ORIGIN" "$DUAL_ORIGIN"
git clone -q "$DUAL_ORIGIN" "$DUAL_CASE"
git clone -q "$DUAL_ORIGIN" "$DUAL_WRITER"
configure_identity "$DUAL_WRITER" windows
write_mac_task "$DUAL_WRITER" dual-task dual-workflow dual.md
{
  printf '%s\n' 'schema_version=2'
  printf '%s\n' 'type=task'
  printf '%s\n' 'source=mac'
  printf '%s\n' 'target=windows'
  printf '%s\n' 'action=wake_codex'
  printf '%s\n' 'task_id=dual-windows-task'
  printf '%s\n' 'workflow_id=dual-workflow'
  printf '%s\n' 'parent_task_id=NONE'
  printf '%s\n' 'hop=0'
  printf '%s\n' 'max_hops=0'
  printf '%s\n' 'instruction_path=airjet-simulation/collaboration/instructions/dual.md'
} > "$DUAL_WRITER/airjet-simulation/collaboration/WINDOWS_TASK.env"
git -C "$DUAL_WRITER" add airjet-simulation/collaboration/MAC_TASK.env airjet-simulation/collaboration/WINDOWS_TASK.env airjet-simulation/collaboration/instructions/dual.md
git -C "$DUAL_WRITER" commit -q -m dual_endpoint_task
git -C "$DUAL_WRITER" push -q origin main
DUAL_TARGET=$(git -C "$DUAL_WRITER" rev-parse HEAD)
run_watcher "$DUAL_CASE" "$TEST_ROOT/state-dual" install "$DUAL_ORIGIN"
[ "$WATCH_CODE" -ne 0 ] || fail dual_endpoint_task_did_not_block
assert_contains dual_endpoint_task_block "$WATCH_OUTPUT" 'BLOCKED_INVALID_MAC_TASK_ENVELOPE detail=dual_endpoint_envelope_change'
assert_equal dual_endpoint_data_synced "$(git -C "$DUAL_CASE" rev-parse HEAD)" "$DUAL_TARGET"
[ ! -f "$TEST_ROOT/state-dual/pending-event.state" ] || fail dual_endpoint_task_left_pending
pass dual_endpoint_task_no_pending

# 23. Group/other-writable trust files fail closed before any Git operation.
TRUST_CASE=$(clone_case case-trust-permissions)
TRUST_STATE=$TEST_ROOT/state-trust-permissions
install_test_trust "$TRUST_STATE"
chmod 666 "$TRUST_STATE/trust/allowed_signers"
TRUST_HEAD=$(git -C "$TRUST_CASE" rev-parse HEAD)
run_watcher "$TRUST_CASE" "$TRUST_STATE" skip
[ "$WATCH_CODE" -ne 0 ] || fail writable_trust_file_did_not_block
assert_contains writable_trust_file_block "$WATCH_OUTPUT" 'BLOCKED_TRUST_STORE_INVALID detail=all_signers_writable_by_group_or_other'
assert_equal writable_trust_head_unchanged "$(git -C "$TRUST_CASE" rev-parse HEAD)" "$TRUST_HEAD"

# 24. A key present in allowed_signers is still rejected when the local KRL
# revokes it.
REVOKED_ORIGIN=$TEST_ROOT/revoked-origin.git
REVOKED_WRITER=$TEST_ROOT/revoked-writer
REVOKED_CASE=$TEST_ROOT/case-revoked
REVOKED_STATE=$TEST_ROOT/state-revoked
git clone -q --bare "$ORIGIN" "$REVOKED_ORIGIN"
git clone -q "$REVOKED_ORIGIN" "$REVOKED_CASE"
git clone -q "$REVOKED_ORIGIN" "$REVOKED_WRITER"
configure_identity "$REVOKED_WRITER" windows
REVOKED_OLD=$(git -C "$REVOKED_CASE" rev-parse HEAD)
printf '%s\n' revoked-signer > "$REVOKED_WRITER/revoked-signer.txt"
git -C "$REVOKED_WRITER" add revoked-signer.txt
git -C "$REVOKED_WRITER" commit -q -m revoked_signer
git -C "$REVOKED_WRITER" push -q origin main
install_test_trust "$REVOKED_STATE"
ssh-keygen -q -k -f "$REVOKED_STATE/trust/revoked_keys.krl" "$WINDOWS_TEST_KEY.pub"
chmod 600 "$REVOKED_STATE/trust/revoked_keys.krl"
run_watcher "$REVOKED_CASE" "$REVOKED_STATE" skip "$REVOKED_ORIGIN"
[ "$WATCH_CODE" -ne 0 ] || fail revoked_signer_did_not_block
assert_contains revoked_signer_block "$WATCH_OUTPUT" BLOCKED_UNTRUSTED_COMMIT
assert_equal revoked_signer_head_unchanged "$(git -C "$REVOKED_CASE" rev-parse HEAD)" "$REVOKED_OLD"

# 25. Exercise the manager guard itself; a marker string alone is insufficient.
MANAGER_STATE=$TEST_ROOT/manager-state
set +e
MANAGER_START_OUTPUT=$(env AIRJET_WATCHER_TEST_MODE=1 AIRJET_WATCHER_STATE_ROOT="$MANAGER_STATE" /bin/sh "$MANAGER" start 2>&1)
MANAGER_START_CODE=$?
MANAGER_RETRY_OUTPUT=$(env AIRJET_WATCHER_TEST_MODE=1 AIRJET_WATCHER_STATE_ROOT="$MANAGER_STATE" /bin/sh "$MANAGER" retry 2>&1)
MANAGER_RETRY_CODE=$?
set -e
[ "$MANAGER_START_CODE" -ne 0 ] || fail manager_start_test_mode_was_not_blocked
assert_contains manager_start_test_mode_guard "$MANAGER_START_OUTPUT" START_RESULT=REFUSED_TEST_MODE
[ "$MANAGER_RETRY_CODE" -ne 0 ] || fail manager_retry_test_mode_was_not_blocked
assert_contains manager_retry_test_mode_guard "$MANAGER_RETRY_OUTPUT" RETRY_RESULT=REFUSED_TEST_MODE

TARGET_ENVELOPE_GATE=BEHAVIOR_TESTED
RUNTIME_TEST_MODE_GUARD=BEHAVIOR_TESTED
STATE_ROOT_REPO_BOUNDARY=BEHAVIOR_TESTED
REPORT_ROOT_BOUNDARY=BEHAVIOR_TESTED
EXPECTED_PASS_COUNT=80
[ "$PASS_COUNT" -eq "$EXPECTED_PASS_COUNT" ] || fail "pass_count_expected_$EXPECTED_PASS_COUNT actual_$PASS_COUNT"

printf 'CORE_CASES_PASS=%s\n' "$PASS_COUNT"
printf 'EXPECTED_PASS_COUNT=%s\n' "$EXPECTED_PASS_COUNT"
printf 'TARGET_ENVELOPE_GATE=%s\n' "$TARGET_ENVELOPE_GATE"
printf 'RUNTIME_TEST_MODE_GUARD=%s\n' "$RUNTIME_TEST_MODE_GUARD"
printf 'STATE_ROOT_REPO_BOUNDARY=%s\n' "$STATE_ROOT_REPO_BOUNDARY"
printf 'REPORT_ROOT_BOUNDARY=%s\n' "$REPORT_ROOT_BOUNDARY"
printf '%s\n' 'VISIBLE_WAKE_TEST=SKIPPED_BY_DESIGN'
printf '%s\n' 'OVERALL=PASS_CORE_RUNTIME_ENABLED_MANUAL'
