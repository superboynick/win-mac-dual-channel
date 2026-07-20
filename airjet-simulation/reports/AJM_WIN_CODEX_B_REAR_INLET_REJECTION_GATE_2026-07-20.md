# AJM Windows Codex B rear-inlet acceptance harness — 2026-07-20

## Required task card

- `TASK_ID=AJM-B-REAR-INLET-REJECTION-20260720-001`
- `UPSTREAM_TASK_ID=ajm-dual-windows-harness-execute-20260720-008`
- `POLICY_CONTRACT_TASK_ID=ajm-dual-windows-harness-recovery-20260720-007`
- `GEOMETRY_CONTRACT_TASK_ID=ajm-windows-rear-inlet-runtime-and-consumer-gates-20260718-006`
- `OWNER=Windows Codex B / OpenFOAM consumer rejection`
- `INPUT_COMMIT=bf605260c53ecd1412e3e3292c0da3f4db044729`
- `INITIAL_INPUT_COMMIT=5c715780621de9f02969f9d57972dd5ba51861b4`
- `INPUT_BRANCH=origin/main`
- `WORK_BRANCH=codex-b-rear-inlet-gate-20260720`
- `STARTED_AT_UTC=2026-07-20T08:39:41Z`
- `ESTIMATED_EFFORT_MIN=90`
- `FIRST_CHECKPOINT_TARGET_MIN=15`
- `SIGNED_SOURCE_TEST_TARGET_MIN=45`
- `SCOPE=source-only handoff schema, fail-closed validator, clip-marker policy, pinned producer hash, and negative tests`
- `FILES_OWNED=only new rear-inlet gate files below airjet-simulation/automation/openfoam/ and this report`
- `A_FILES=READ_ONLY`
- `ANSYS_EXECUTION=PROHIBITED`
- `OPENFOAM_EXECUTION=PROHIBITED_UNTIL_EXPLICIT_A_PASS`

## Lease and test matrix checkpoint

`FILE_LEASE=ACTIVE_NO_OVERLAP`

Planned new files:

- `automation/openfoam/rear_inlet_handoff_schema_v1.json`
- `automation/openfoam/validate_rear_inlet_handoff.py`
- `automation/openfoam/test_validate_rear_inlet_handoff.py`

The validator must reject each of the following independently:

1. missing inlet identity;
2. duplicate inlet identity;
3. inlet count other than four;
4. outlet count other than one;
5. missing or non-frozen `cell_footprint_y_min_mm=-14.5`;
6. missing or non-frozen `supported_plenum_y_min_mm=-17.75`;
7. missing or non-frozen rear support extension `3.25 mm`;
8. rear IDs other than exactly `V01` and `V02`;
9. producer script, profile, or artifact declared/observed hash mismatch;
10. A acceptance state other than explicit `PASS`.
11. either rejected producer clip marker, an incomplete marker scan, or producer hash other
    than the reviewed pin `8f23d7d7dd66efcf06909341a45a76caccd6732cbf11fa1f54157699d55228b0`.
12. missing Mac review, Mac state other than literal `ACCEPTED_PASS`, or a Mac receipt whose
    producer commit/runtime-report hash does not match the supplied handoff.

Additional fail-closed checks cover one closed/manifold piece, the frozen bounding box,
the analytic volume, native/STEP reopen, connectivity, artifact role completeness, SHA-256
syntax, and rejection of unknown fields. The implementation reads a supplied manifest only;
it does not open CAD/STEP files, fabricate geometry, run ANSYS, or run OpenFOAM.

## Delivery status

- Expected time: 90 minutes total; first checkpoint within 15 minutes; signed source/test
  target within 45 minutes.
- Actual time: task card and lease at about 2 minutes; initial Task 006 implementation and
  21-test matrix at about 12 minutes. Before push, signed Tasks 007 and 008 advanced
  `origin/main`;
  the unpushed B commit was linearly rebased with a fresh signature and the harness was
  extended for the new pinned-producer/clip-marker requirements.
- Delivered evidence: JSON Schema Draft 2020-12 declaration, standard-library fail-closed
  validator/CLI, positive/negative tests including CLI paths and Mac receipt binding, and
  stable reason codes.
- Independent review: a tool-free DeepSeek review supplied extra negative-test ideas. ID
  syntax, hash syntax, unknown fields, role completeness, and cross-boundary duplicates were
  incorporated. A second implementation review exceeded its response window and made no
  changes.
- Baseline transition: both repository audits correctly failed at initial input `5c71578`
  because untouched A producer/profile hashes differed. Mac-signed `35d48f5` restored the
  reviewed producer and retained its correct profile pin; the repository audit now passes.
  B did not modify either A-owned file and did not cherry-pick the rejected incident fix.
- Blocker: A runtime native/STEP acceptance evidence is still absent. A source/hash repair is
  not a runtime geometry pass; missing proof must cause consumer rejection, not a gate bypass.
- Next action: publish the signed B source/test commit for Mac review; then wait for a new,
  hash-consistent explicit A `PASS` manifest before any consumer use.
- Revised ETA: not required; source/test work completed ahead of the 45-minute target.
- `TRACK_B_SOURCE_GATE=PASS`
- `REPOSITORY_AUDIT=PASS_AT_bf60526`
- `A_HANDOFF_ACCEPTANCE=REJECT`
- `P1_STAGE_GATE=NOT_RUN`
- `P2_STAGE_GATE=NOT_RUN`
- `P3_STAGE_GATE=NOT_RUN`
- `OPENFOAM_PRODUCTION_SOLVE=NOT_RUN`
