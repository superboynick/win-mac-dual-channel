# AirJet manual Git watcher

This toolkit keeps the Mac and Windows AirJet worktrees synchronized through the
trusted GitHub `main` branch. It is deliberately manual: it does not install a
LaunchAgent, cron job, login item, Windows service, scheduled task, or startup
entry. An unchanged remote branch does not invoke Codex and consumes no model
tokens.

The Windows implementation remains local at `C:\Users\admin\AirJetGitWatcher`.
The reviewed macOS adapter is versioned under `mac/`; machine state is stored
outside Git in `~/Library/Application Support/AirJetGitWatcher/`.

## macOS commands

Run from a visible, locally logged-in Terminal session:

```sh
cd /Users/zhangjianxiao/win-mac-dual-channel
sh tools/airjet-git-watcher/mac/manage-airjet-watcher.sh start
sh tools/airjet-git-watcher/mac/manage-airjet-watcher.sh status
sh tools/airjet-git-watcher/mac/manage-airjet-watcher.sh stop
```

Optional maintenance commands:

```sh
# Perform one safe check. A strictly-behind clean repository may be fast-forwarded,
# but Codex is not opened; a durable pending event is retained.
sh tools/airjet-git-watcher/mac/manage-airjet-watcher.sh once

# Resume a retained event and open the visible Codex task.
sh tools/airjet-git-watcher/mac/manage-airjet-watcher.sh retry

# Archive an event only after its visible Codex task/report has been reviewed.
sh tools/airjet-git-watcher/mac/manage-airjet-watcher.sh acknowledge
```

The default poll interval is 180 seconds. Override it only for a manual run:

```sh
sh tools/airjet-git-watcher/mac/manage-airjet-watcher.sh start --poll-seconds 300
```

## Safety behavior

Each poll verifies the exact repository root, `main`, `origin/main`, trusted
remote URL, clean worktree, and commit relationship. It stops instead of
merging when the worktree is dirty, local history is ahead/diverged, identity
checks fail, authentication is unavailable, or the fast-forward cannot be
verified. A pending event is written before the pull, so an interruption cannot
silently lose the update.

When an update is verified, the watcher opens a new visible Terminal/Codex task
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
stored in this repository.
