# Plan A continuous handoff: P1 peer package and P2 preflight

TASK_ID=`ajm-plan-a-p1-peer-package-p2-preflight-20260720-013`

Windows A continues immediately from task 012. Track B is read-only. Do not wait for Mac
peer review and do not rerun the accepted SpaceClaim producer.

## Five-minute liveness

Create and refresh `TASK_013_PROGRESS.env` in the Git-external watcher report root within
5 minutes and after each material checkpoint. Record UTC, current action, completed checks,
blocker and next action. Exit promptly when deliverables are complete; never remain as an
idle Codex, shell or MCP process.

## Work package

1. Re-hash task 012 compact manifest and independent checker, cross-bind them to job
   `ajm-rear-inlet-009-mcp-fbff57daa893`, the native/STEP hashes and all source-chain hashes.
   Treat zero-byte `stderr.log` as valid only because `exit_code=0`, stdout is non-empty and
   no required assertion depends on stderr content.
2. Correct/report any time inconsistency: use filesystem and `job.json` timestamps as
   evidence; do not invent future timestamps.
3. Produce a concise P1 peer-review package that Mac can independently retrieve and verify.
   Status is only `PENDING_MAC_PEER_REVIEW`; do not self-award P1.
4. In parallel, perform P2 Mechanical source-only preflight for the complete product:
   inventory the approved structural profile/contracts, input artifact requirements,
   material/plate/membrane/piezo boundary contracts, Student limits, expected output manifest,
   terminal polling and external artifact routing. Do not submit Mechanical until Mac accepts
   P1 and issues a signed runtime task.
5. Run relevant static policy/unit/audit checks using available executables. If a Python
   launcher is unavailable, use the exact registered automation-venv Python path; do not
   change PATH globally or weaken policy.

Deliver within 15 minutes: cross-bound hash manifest and progress report. Within 30 minutes:
P1 peer package plus P2 preflight matrix with literal PASS/FAIL/NOT_READY. Keep all outputs
Git-external; no Git writes, Fluent, OpenFOAM, CAD changes, private-key access or repeated MCP
inventory calls. Formal P1--P6 remain fail-closed pending Mac acceptance.
