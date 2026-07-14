# Mac/Windows signed Git peer handshake 001

## Task identity

- `task_id=ajm-git-peer-handshake-20260714-001`
- `workflow_id=ajm-git-peer-handshake-20260714`
- Task owner for this bounded handshake: Mac Codex
- Scope: Git synchronization, signature verification, project audit, signed result, and signed receipt only

## Prohibited work

- Do not start the Mac watcher runtime; it remains `DISABLED_PENDING_END_TO_END`.
- Do not start ANSYS, CAD, CFD, optimization, or paper writing.
- Do not modify engineering parameters, stage-gate status, or project conclusions.
- Do not force-push, reset, rebase, merge, or overwrite peer work.

## Required Mac procedure

1. From `/Users/zhangjianxiao/win-mac-dual-channel`, require a clean worktree and run the peer Git preflight from `AGENTS.md`.
2. Fast-forward to this task tip and save its full commit as `TASK_COMMIT`.
3. Verify that `TASK_COMMIT` has a good SSH signature from the Windows signing fingerprint:
   `SHA256:oI3/MIlKz1mgLV3+5n1coQxynaqQOzxqi0GHxreGEdc`.
4. Verify that this instruction and `collaboration/MAC_TASK.env` are regular blobs in exactly `TASK_COMMIT`, and that the envelope is the strict schema-v2 root task for this task ID.
5. Run `sh ./install-skills.sh` and the repository project audit. Record literal PASS/FAIL without upgrading an unobserved result.
6. Create only this result summary:
   `airjet-simulation/reports/AJM_GIT_PEER_HANDSHAKE_2026-07-14_MAC.md`.
   It must record `TASK_COMMIT`, Mac signer fingerprint, skill result, audit result, clean/sync state, and any blocker. It must not claim watcher or GUI visibility testing.
7. Recheck fetch/ahead-behind. If clean and non-divergent, make a normal Mac-signed result commit and push it. Save its full hash as `RESULT_COMMIT`.
8. Create exactly one immutable receipt:
   `airjet-simulation/collaboration/receipts/ajm-git-peer-handshake-20260714-001.env`
   using the receipt schema in `collaboration/README.md`, with:
   `executor=mac`, `status=complete`, the saved `TASK_COMMIT` and `RESULT_COMMIT`, the summary path above, and `next_task_id=NONE`.
9. Recheck fetch/ahead-behind, make a separate Mac-signed receipt commit whose direct parent is `RESULT_COMMIT`, and push normally.
10. Report the final receipt commit as `GIT_READY=<full_commit>`.

If any signature, ownership, Git state, installation, or audit check fails, do not fabricate completion. Write no result commit unless the failure can be accurately and safely recorded; report the blocker to the user.
