# Plan A runtime evidence closeout — no idle process

TASK_ID=`ajm-plan-a-runtime-evidence-closeout-20260720-012`

Windows A owns this task exclusively. Task 011 was terminated after its report stopped
changing while the Codex process remained alive. Do not treat process existence as progress.
Track B is read-only and must not duplicate this work.

## Five-minute liveness contract

Within 5 minutes write `TASK_012_PROGRESS.env` under
`C:\Users\admin\Downloads\AirJetGitWatcherReports` with UTC time, current action, completed
artifact count, blocker and next checkpoint. Refresh it after every material check and at
least every 5 minutes. If no meaningful work remains, finish and exit; never idle in a
long-lived shell, MCP server or Codex process.

## Objective

Independently close the external evidence package for job
`ajm-rear-inlet-009-mcp-fbff57daa893` at
`D:\AirJet_P1\AJM-P1-CAD-006\ajm-rear-inlet-009-mcp\ajm-rear-inlet-009-mcp-fbff57daa893`.

1. Verify `job.json` says `PROCESS_EXITED_0`, `exit_code=0`, reviewed profile, Git head
   `a8ece4383e0c65c7a33f026203d86807feac6c0c`, and script SHA
   `8f23d7d7dd66efcf06909341a45a76caccd6732cbf11fa1f54157699d55228b0`.
2. Verify and hash native SCDOCX, STEP, producer JSON, source-chain JSON, native reopen JSON,
   STEP reimport JSON, throat inventory, stdout/stderr and dependency manifest. Reject
   missing, zero-length required artifacts, time-order inconsistency or hash mismatch.
3. Emit a compact machine-readable external acceptance manifest containing literal values:
   4 inlets, 1 outlet; preserved V01/V02 boxes; footprint Y-min `-14.500 mm`; plenum Y-min
   `-17.750 mm`; backward extension `3.250 mm`; one closed/manifold body and piece; bbox
   `[-10.875,-17.750,1.2675]--[10.875,20.750,2.800] mm`; analytic/native/STEP volumes;
   972 one-to-one throat matches; native and STEP reopen status.
4. Run a second independent parser/checker over that compact manifest and report literal
   PASS/FAIL for every assertion. A generating session may claim only
   `PENDING_MAC_PEER_REVIEW`, never formal P1 acceptance.
5. Write the final report and SHA-256 manifest under the external report root. Do not modify
   Git, producer/profile, native artifacts or private keys; do not start Fluent or Track B.

Checkpoints: progress file in 5 minutes; verified artifact/hash table in 15 minutes; compact
manifest and independent checker in 30 minutes. On failure report the exact file/assertion,
actual versus expected time, revised ETA and safe A-only next action. P1--P6 remain formally
`NOT_RUN/NOT_PASSED` until Mac peer review.
