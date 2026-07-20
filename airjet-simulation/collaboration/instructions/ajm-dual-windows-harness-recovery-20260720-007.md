# Dual Windows harness recovery and rear-inlet acceptance

TASK_ID=`ajm-dual-windows-harness-recovery-20260720-007`

Start only from clean synchronized `main` at the signed target commit. Publish two
separate task cards with owner, scope, files, start UTC, ETA UTC, checkpoints, acceptance,
blockers and safe backlog. A and B may overlap in review but must not edit the same files.

## Watcher and repository hygiene

- Stop the custom loop that creates `windows-heartbeat-*.txt`, commits and pushes `main`.
  Git history is not a process heartbeat channel. Do not delete or rewrite existing history.
- Runtime PID/state/heartbeat belongs only below the Git-external watcher state root.
- From the visible Windows desktop, start the reviewed manager with `-Action start
  -PollSeconds 10`. Report manager PID, state/detail, commit and pending phase. Do not claim
  watcher recovery from SSH, a generic background job, trigger-file rewriting or heartbeat
  commits. Do not register startup persistence.
- Keep the integration checkout clean. Both owners work on separate signed branches and
  push those branches only; neither pushes `main`.

## Windows A — ANSYS owner

Use the `airjet-ansys-automation` skill and official hash-pinned MCP only. Confirm producer
SHA `8f23d7d7dd66efcf06909341a45a76caccd6732cbf11fa1f54157699d55228b0` and reject any
source containing `vent_rear_containment_clip` or `box[1] = footprint_y_min`. Run the
producer once, then validate native and STEP reopen: 4 inlets, 1 outlet, preserved V01/V02
boxes, shared plenum Y-min `-17.750 mm`, support extension `3.250 mm`, one closed/manifold
piece, frozen bbox, analytic volume `469.4396438426395 mm3` within contract tolerances and
expected connectivity. Stop on first failed assertion; do not start Fluent or reuse the old
mesh. Condense only audited small evidence and index large artifacts externally.

## Windows B — OpenFOAM owner

Do not edit ANSYS files or run cases. Implement the source-only input acceptance harness on
a separate branch. It must reject wrong/missing/duplicate inlet identities, counts other
than 4/1, rear-support values other than `-14.500/-17.750/3.250`, wrong rear IDs, any clip
marker, producer/profile/artifact hash drift, or A state other than explicit accepted PASS.
Add positive and negative tests. Correct input remains blocked until A runtime evidence is
accepted by Mac.

## Checkpoints and escalation

- 15 minutes: watcher status plus both task cards and file leases.
- 45 minutes: A preflight/job state and B committed test matrix.
- 90 minutes: A terminal runtime evidence or exact blocker; B signed branch ready for review.
- A missed checkpoint requires expected vs actual time, blocker, revised ETA and safe backlog.
- Two unchanged failures stop retries and require root-cause analysis.

P1--P6 remain `NOT_RUN/NOT_PASSED`. Exit code zero, process existence, heartbeat, CFD on the
old mesh and branch-local self-tests are not acceptance.
