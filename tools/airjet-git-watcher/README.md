# AirJet manual Git watcher

> Runtime status: `DISABLED_PENDING_HARDENING` (2026-07-14). Isolated local-Git tests now pass the core synchronization and fail-closed matrix, including a structured `target=mac` envelope, state-root confinement, visible block diagnostics, and critical-update cleanup. Continuous start/retry remain code-locked until commit-authentication policy and a user-observed visible-wake test are reviewed. Source synchronization and core test PASS do not authorize runtime use.

This toolkit keeps the Mac and Windows AirJet worktrees synchronized through the
trusted GitHub `main` branch. It is deliberately manual: it does not install a
LaunchAgent, cron job, login item, Windows service, scheduled task, or startup
entry. An unchanged remote branch does not invoke Codex and consumes no model
tokens.

The Windows implementation remains local at `C:\Users\admin\AirJetGitWatcher`.
The reviewed macOS adapter is versioned under `mac/`; machine state is stored
outside Git in `~/Library/Application Support/AirJetGitWatcher/`.

## macOS commands

Safe status and isolated test commands:

```sh
cd /Users/zhangjianxiao/win-mac-dual-channel
sh tools/airjet-git-watcher/mac/manage-airjet-watcher.sh status
sh tools/airjet-git-watcher/tests/test-watch-airjet-git.sh
```

The following one-shot command is no-wake but may fast-forward a clean,
strictly-behind real worktree. Use it only after inspecting local status:

```sh
# An ordinary update is synchronized without a pending wake event. A changed,
# valid target=mac envelope is retained as PENDING_NO_WAKE.
sh tools/airjet-git-watcher/mac/manage-airjet-watcher.sh once
```

`start` and `retry` currently return
`REFUSED_DISABLED_PENDING_HARDENING`. Do not bypass that lock. After the
remaining review closes, the intended manual start command will be:

```sh
sh tools/airjet-git-watcher/mac/manage-airjet-watcher.sh start --poll-seconds 300
```

## Mac task envelope

An update may request a visible Mac Codex wake only when the update itself
changes `airjet-simulation/collaboration/MAC_TASK.env` and the target commit
contains exactly these fields:

```text
schema_version=1
target=mac
action=wake_codex
task_id=short-auditable-id
instruction_path=airjet-simulation/path/to/committed-task.md
```

The task ID is restricted to 1--80 letters, digits, dots, underscores, or
hyphens. The instruction must be an existing file below `airjet-simulation/` in
the exact target commit. Missing, unchanged, malformed, duplicate, unknown, or
path-traversing fields cannot wake Codex. An ordinary commit without a changed
envelope may be synchronized, but records `SYNCED_NO_MAC_TASK` and creates no
pending event.

## Safety behavior

Each poll verifies the exact repository root, `main`, `origin/main`, trusted
remote URL, clean worktree, and commit relationship. It stops instead of
merging when the worktree is dirty, local history is ahead/diverged, identity
checks fail, authentication is unavailable, or the fast-forward cannot be
verified. A pending event is written before the pull, so an interruption cannot
silently lose the update.

When an update and task envelope are verified, the watcher may open a new visible Terminal/Codex task
using `workspace-write` and `on-request` approvals. It cannot inject work into an
already-open Codex chat. It refuses wake-up from SSH or without the same user at
the macOS console. Read `wake-policy.md` for the instructions given to the new
task.

The update is applied to the exact commit fetched from `origin/main` with hooks,
submodule recursion, and LFS smudge disabled. If an incoming update changes this
watcher, `.gitattributes`, or `.gitmodules`, automatic synchronization stops for
manual review; it never executes a newly pulled watcher implementation. Durable
wake phases distinguish a Terminal request from actual Codex start and exit.

No credentials, Codex state, logs, PIDs, prompts, reports, or pending events are
stored in this repository. State roots that resolve inside the repository are
rejected. The awakened Codex receives write access only to the repository and
`~/Downloads/AirJetGitWatcherReports/`, not all of Downloads.

## Current test result

`tests/test-watch-airjet-git.sh` creates only local temporary bare repositories
and never contacts GitHub or invokes Codex. The current matrix covers unchanged,
clean-behind fast-forward, ordinary no-task sync, valid task retention, pending
deduplication and revalidation, dirty/ahead/diverged histories, critical watcher
updates including legacy pending recovery, wrong remotes, malformed and
path-traversing envelopes, symlink/tree instructions, state/event/log directory
confinement, report-directory confinement, and real manager start/retry refusal.
Current result: `CORE_CASES_PASS=58` and
`OVERALL=PASS_CORE_RUNTIME_DISABLED`.
