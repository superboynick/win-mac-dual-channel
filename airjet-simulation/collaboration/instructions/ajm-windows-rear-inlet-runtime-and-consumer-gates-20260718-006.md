# Windows A/B rear-inlet correction acceptance task

TASK_ID=`ajm-windows-rear-inlet-runtime-and-consumer-gates-20260718-006`

Pull the exact signed `main` task commit with `git pull --ff-only`, verify clean `main`,
`0/0` divergence and the trusted Mac signature before acting. Do not use or merge commit
`4fbec7b3d899b7962244bf2330fb64d67b178887`; its clipping proposal is rejected.

Frozen facts: four inlets total; V01/V02 extend backward, not downward. The cell-footprint
rear plane is `Y=-14.500 mm`, the two rear inlet minima are `Y=-17.750 mm`, and the missing
support length is `3.250 mm` each. The reviewed fix preserves all four vent boxes and
extends the C-class shared plenum backward to `Y=-17.750 mm`. P1--P6 remain fail-closed.

## Windows A — official ANSYS runtime owner

Publish the required task card first. Own only official-MCP inventory, profile/hash
preflight, producer execution, native/STEP reopen validation, small evidence condensation,
run index/external artifact index and runtime failure logging. Do not edit OpenFOAM files.

Acceptance requires literal runtime evidence for: exact 4 inlet / 1 outlet; V01/V02 raw
boxes preserved and supported to `Y=-17.750 mm`; one closed/manifold piece; bbox
`[-10.875,-17.750,1.2675]--[10.875,20.750,2.800] mm`; expected analytic volume
`469.4396438426395 mm3` within frozen tolerances; native reopen and STEP reopen; expected
connectivity and no new body/piece defect. Use only the reviewed hash-pinned profile.
Stop at the first failed assertion and report exact error/job/artifact path; do not start
Fluent. First checkpoint: inventory/profile/hash report within 15 minutes. Runtime report
target: 45 minutes, revised ETA mandatory if late.

FILES_OWNED: `logs/run-index.csv`, `logs/external-files.csv`, a new bounded
`logs/evidence/<job>/` condensation, and runtime-only additions to
`logs/REALITY_AND_FAILURE_LOG.md` / `MODEL_ANNOTATIONS.md` after pulling the task commit.

## Windows B — OpenFOAM consumer rejection owner

Publish a separate required task card first. Do not run or edit ANSYS producer/contracts,
native CAD or STEP. Add a source-only preflight schema and negative tests that reject:
missing/duplicate inlet identities; inlet count not 4; outlet count not 1; missing
`cell_footprint_y_min_mm=-14.5`; missing `supported_plenum_y_min_mm=-17.75`; rear support
extension not `3.25`; rear IDs not exactly V01/V02; producer/profile/artifact hash mismatch;
or A acceptance state other than explicit PASS. Do not consume fabricated geometry or run
OpenFOAM. First checkpoint: file lease and test matrix within 15 minutes. Signed source/test
commit target: 45 minutes, revised ETA mandatory if late.

FILES_OWNED: new files only below `airjet-simulation/automation/openfoam/` plus one bounded
Track-B report. A's owned files and all ANSYS sources are read-only.

## Delivery and watcher

A and B must use separate signed branches and must not push `main`. Each report includes
expected vs actual time, delivered evidence, blocker, next action and revised ETA. Start the
watcher from the already-visible Windows desktop using the reviewed manager command; report
manager status, PID, state/detail and whether this task was automatically consumed. An SSH
process is not watcher recovery. Mac accepts and linearly integrates only reviewed commits;
overlap, dirty integration checkout, divergence or merge commits stop acceptance.
