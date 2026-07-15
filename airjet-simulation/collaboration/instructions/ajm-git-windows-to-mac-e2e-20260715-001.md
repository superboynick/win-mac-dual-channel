# Windows-to-Mac signed watcher E2E 001

## Task identity

- `task_id=ajm-git-windows-to-mac-e2e-20260715-001`
- `workflow_id=ajm-git-windows-to-mac-e2e-20260715`
- `nonce=AJM-BIDI-20260715-W2M-6F1C9A42`
- Executor: Mac Codex
- Scope: establish or verify the bounded Windows-to-Mac signed-Git wake channel and leave the Mac watcher running manually at a 10-second poll interval

## Hard boundaries

- Do not start CAD, ANSYS, CFD, optimization, paper writing, or any engineering stage work.
- Do not modify either endpoint task envelope, watcher source, trust roots, project parameters, or stage-gate conclusions.
- Do not create a reciprocal task. This is an independent schema-v2 root task with `parent_task_id=NONE`, `hop=0`, and `max_hops=0`.
- Do not register a LaunchAgent, cron job, login item, or any other automatic startup mechanism.
- Do not reset, clean, stash, merge, rebase, force-push, or overwrite peer work.
- Do not report a GUI window as user-observed unless the user actually confirms seeing it.

## Required Mac procedure

1. In the visible Mac Terminal, enter `/Users/zhangjianxiao/win-mac-dual-channel`. Require `main`, a clean worktree, and no ahead/divergence. Fetch and fast-forward only when safe. Save this task tip as `TASK_COMMIT`.
2. Verify that `TASK_COMMIT` has a good SSH signature from the Windows signing fingerprint `SHA256:oI3/MIlKz1mgLV3+5n1coQxynaqQOzxqi0GHxreGEdc`.
3. Verify that exactly this instruction and `airjet-simulation/collaboration/MAC_TASK.env` are regular `100644` blobs changed by `TASK_COMMIT`, that the envelope has the strict 11-field schema-v2 root-task form, and that `TASK_COMMIT` is the remote target tip received by the Mac endpoint.
4. Record the actual invocation evidence before changing runtime state. If a watcher event, processed claim, and runner log prove this Codex process was launched for this task, set `WAKE_CHANNEL=SIGNED_GIT_WATCHER` and continue the real E2E assessment. If the task was opened manually, set `WAKE_CHANNEL=MANUAL_GIT_HANDOFF`; never upgrade that to an automatic wake PASS.
5. Fully read the repository collaboration protocol and watcher README/wake policy. Run `sh ./install-skills.sh`, the repository audit, and `sh tools/airjet-git-watcher/tests/test-watch-airjet-git.sh`. The isolated watcher matrix must literally report `CORE_CASES_PASS=80`, `EXPECTED_PASS_COUNT=80`, and `OVERALL=PASS_CORE_RUNTIME_ENABLED_MANUAL`.
6. From the visible local session, inspect Git-external watcher trust hashes, manager status, processed state, and pending events. Do not delete or rewrite pending/processed state. If there is a pending event, review it and use only the documented manager `retry`/acknowledge path when appropriate; otherwise report the blocker.
7. Confirm no watcher autostart registration exists. Do not install one. If the watcher is not already running and all trust/preflight checks pass, leave Git reporting until steps 8-10 are safely pushed, then manually run:

   ```sh
   sh tools/airjet-git-watcher/mac/manage-airjet-watcher.sh start --poll-seconds 10
   ```

   If this task was itself watcher-launched, do not start a duplicate process; require the existing watcher to return to `WATCHING` after the child exits.
8. Create only this result summary: `airjet-simulation/reports/AJM_GIT_WINDOWS_TO_MAC_E2E_2026-07-15_MAC.md`. It must contain the literal fields below and supporting raw evidence:

   ```text
   TASK_ID=ajm-git-windows-to-mac-e2e-20260715-001
   NONCE=AJM-BIDI-20260715-W2M-6F1C9A42
   TASK_COMMIT=<full hash>
   WINDOWS_TASK_SIGNATURE=PASS|FAIL
   GIT_PRECHECK=PASS|FAIL
   SKILL_INSTALL=PASS|FAIL
   PROJECT_AUDIT=PASS|FAIL
   MAC_WATCHER_TESTS=80_OF_80_PASS|FAIL
   WAKE_CHANNEL=SIGNED_GIT_WATCHER|MANUAL_GIT_HANDOFF|NOT_PROVEN
   REAL_WINDOWS_TO_MAC_WAKE=PASS|FAIL|NOT_RUN
   MAC_WATCHER_RUNTIME=WATCHING_10S|NOT_RUNNING|BLOCKED|NOT_PROVEN
   MAC_AUTOSTART=ABSENT|PRESENT|NOT_PROVEN
   GUI_VISIBILITY=USER_OBSERVED|NOT_USER_OBSERVED|NOT_VISIBLE
   CAD=NOT_RUN
   ANSYS=NOT_RUN
   CFD=NOT_RUN
   OPTIMIZATION=NOT_RUN
   PAPER=NOT_RUN
   ROUNDTRIP_STATUS=PASS|PARTIAL|FAIL
   BLOCKERS=NONE|<literal blockers>
   ```

   `REAL_WINDOWS_TO_MAC_WAKE=PASS` and `ROUNDTRIP_STATUS=PASS` are allowed only when the actual signed watcher event launched this task and all required verification passed. A manual handoff may prepare the runtime but must remain `REAL_WINDOWS_TO_MAC_WAKE=NOT_RUN` and `ROUNDTRIP_STATUS=PARTIAL`.
9. Recheck fetch/ahead-behind. If clean and non-divergent, make a normal Mac-signed result commit containing only the result summary and push it. Save the full hash as `RESULT_COMMIT`.
10. Create exactly one immutable receipt at `airjet-simulation/collaboration/receipts/ajm-git-windows-to-mac-e2e-20260715-001.env`, using the repository receipt schema with `executor=mac`, an accurate `status`, saved `TASK_COMMIT` and `RESULT_COMMIT`, the summary path above, and `next_task_id=NONE`. Make a separate Mac-signed receipt commit whose direct parent is `RESULT_COMMIT`, then push normally.
11. If this was a manual handoff and all readiness checks passed, start the Mac watcher manually at 10 seconds only after the result and receipt are pushed and the repository is clean/0-ahead/0-behind. Show manager status in the final response and leave the process running. Do not make another Git commit after starting it.
12. Final output must display the report fields, `RESULT_COMMIT`, receipt commit, manager status, and `GIT_READY=<full receipt commit>`. Stop; do not begin another task.

If any signature, ownership, Git state, audit, trust, or runtime check fails, fail closed and report the exact blocker. Do not fabricate PASS and do not create unrelated files.
