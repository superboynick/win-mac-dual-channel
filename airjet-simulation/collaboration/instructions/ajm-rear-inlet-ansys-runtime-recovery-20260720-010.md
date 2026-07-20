# Rear-inlet official ANSYS runtime recovery

TASK_ID=`ajm-rear-inlet-ansys-runtime-recovery-20260720-010`

Windows A owns this recovery task exclusively. Track B is read-only. The previous task
failed before submission because the awakened watcher identity could not use Git signing,
Python, or the official MCP approval path. Do not repeat those identity-dependent Git
operations and do not copy, expose, or weaken permissions on any private key.

## First 15-minute checkpoint

1. Report the executing Windows user, session ID, checkout path, official MCP inventory
   result, and exact blocker (if any) to the Git-external watcher report root. A Git commit
   is not required from this sandbox.
2. Make at most two official `airjet-ansys` MCP inventory attempts. If both fail with the
   same error, stop restarting MCP servers, record their timestamps and the exact error,
   and continue only with safe read-only diagnosis.
3. Confirm Student 2026 R1, the approved profile
   `ajm006-spaceclaim-v03-continuous-throat-pilot-v1`, clean source tip, and producer/profile
   SHA `8f23d7d7dd66efcf06909341a45a76caccd6732cbf11fa1f54157699d55228b0`.
4. Reject if the producer contains `vent_rear_containment_clip` or
   `box[1] = footprint_y_min`. Do not modify the producer or profile.

## Runtime contract

If and only if official inventory passes, submit the reviewed profile exactly once, poll
the job to a terminal state, and keep all native, STEP, dependency, log and manifest
artifacts under the registered Git-external evidence root. Do not write generated artifacts
inside any repository checkout. Do not start Fluent, meshing or later P2--P6 work.

Acceptance requires literal evidence for 4 inlets and 1 outlet; preserved V01/V02 vent
boxes; footprint Y-min `-14.500 mm`; supported plenum Y-min `-17.750 mm`; backward
extension `3.250 mm`; one closed/manifold body and piece; bbox
`[-10.875,-17.750,1.2675]--[10.875,20.750,2.800] mm`; analytic/native/STEP volume
`469.4396438426395 mm3` within route tolerances; native reopen, STEP reopen and expected
connectivity. Stop at the first failed assertion.

## Handoff and deadlines

- By 15 minutes: Git-external task card and inventory result.
- By 45 minutes: submitted/terminal job state or exact fail-closed blocker.
- By 90 minutes: complete external artifact manifest with SHA-256 hashes and paths.
- Write small reports to `C:\Users\admin\Downloads\AirJetGitWatcherReports`; large ANSYS
  artifacts remain in the registered external evidence root.
- Mac will retrieve, independently review, condense and sign the evidence. The awakened
  Windows sandbox must not create a branch, fetch, sign, push, or request a private key.
- Report actual versus expected time, revised ETA, safe A-only backlog and all job/process
  IDs. P1--P6 remain `NOT_RUN/NOT_PASSED` unless Mac later accepts the evidence.
