# AirJet Git update wake policy

The Git watcher may open a new visible Codex task only after it has safely
fast-forwarded the trusted repository and verified a clean `0 ahead / 0 behind`
state.

The awakened task-owning peer agent must:

1. Verify the reported commit, clean worktree, `main`, `origin/main`, trusted
   remote, and `0 ahead / 0 behind` before acting.
2. Read `AGENTS.md`, the `airjet-product-reconstruction` skill, and every changed
   instruction/task file completely.
3. Obey stage gates and stop conditions. Never convert `NOT_RUN`, `NOT_VISIBLE`,
   or unobserved GUI work into `PASS`.
4. Not modify, commit, or push Git unless the new committed task explicitly
   authorizes that exact action.
5. Never expose credentials, tokens, license contents, activation data, Keychain
   data, or verification codes; never run unofficial license tools.
6. Require actual visible-desktop observation for GUI claims.
7. Report `NO_ENDPOINT_TASK` and take no project action when the update contains
   no instruction for the current execution endpoint.
8. Stop and report a blocker when authority is missing or scope materially
   expands.
9. For genuinely long or multi-part work, use 1-2 bounded subagents only for
   independent research, audit, or testing. The task-owning agent must read skills,
   retain task ownership, integrate and verify results, and stop all subagents before
   handoff. Do not use subagents merely for idle persistence.
10. Never create or modify `MAC_TASK.env` or `WINDOWS_TASK.env` as a completion
    side effect. Automatic reciprocal relay is disabled; a new signed root task
    must be created by the coordinating session.
11. Never alter watcher state or install an automatic startup mechanism unless
    the user explicitly requests that separate action.

The runner saves the final response to the endpoint's dedicated
`Downloads/AirJetGitWatcherReports/AIRJET_GIT_WATCHER_LAST_REPORT.txt` file.
