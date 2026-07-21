# Plan A: formal 006 registration preflight

TASK_ID=`ajm-p1-formal006-registration-preflight-20260721-015`

## Ownership and result boundary

Windows Plan A owns this task. Plan B remains read-only for every ANSYS path and continues
only the OpenFOAM line. This task is a no-solver inventory and contract preflight. It must
not run SpaceClaim, Workbench, Mechanical, Fluent, PyMechanical, PyFluent, or any MCP job.
It cannot change `P1_STAGE_GATE`, register a profile, or modify the Git worktree.

Create or refresh the external task card at
`C:\Users\admin\Downloads\AirJetGitWatcherReports\TASK_A_LIVE_PROGRESS.env` within five
minutes. Include OWNER=A, INPUT_COMMIT, STARTED_AT_UTC, ETA_UTC, checkpoints at 15/45/90
minutes, deliverables, blockers, and safe backlog. Refresh it after every checkpoint.

## Frozen accepted input

- Handoff: `airjet-simulation/automation/openfoam/rear_inlet_handoff_accepted_20260720.json`
- Producer source SHA256: `8f23d7d7dd66efcf06909341a45a76caccd6732cbf11fa1f54157699d55228b0`
- Native SHA256: `50223b0fd0d70b80ce7d4abd4e267e44fb2c66c1a4ae77f117629953b08cae9e`
- STEP SHA256: `b1ce3b9016f74663a7fdb686b122f491f9df391a668d86b43c33a5132e477fa4`
- Runtime report SHA256: `6bd4604baa6b9c7631e99ff8a517ce782d3c006de13301c31f9955a12def0c4b`
- Geometry: exactly four inlets and one outlet; V01/V02 extend rearward to `Y=-17.750 mm`
  and are supported by the C-class shared plenum. Do not move them downward.

## Required work

1. Verify clean signed `main`, `0/0` divergence, project audit PASS, and the exact handoff
   contents above. Stop without reset, clean, merge, rebase, or force push on any mismatch.
2. Re-hash only the three declared external files under the paths recorded in the handoff.
   Record existence, size and SHA256. Do not regenerate or copy them.
3. Run the static full-product contract, trusted-variant, P1 review-bridge, ANSYS policy and
   P2 readiness tests below. Record literal commands, exit codes and final markers.

```powershell
python airjet-simulation\automation\ansys\contracts\test_full_product_semantic_contract_v1.py
python airjet-simulation\automation\ansys\contracts\test_full_product_trusted_variants.py
python airjet-simulation\checklists\test_prepare_p1_cad_review_static.py
python codex-skills\airjet-ansys-automation\scripts\test_airjet_ansys_mcp_policy.py
python airjet-simulation\automation\ansys\contracts\test_p2_production_readiness_v1.py
```
4. Inspect `profiles.json` at INPUT_COMMIT. The expected current result is
   `STATIC_CONTRACT_ONLY_NOT_REGISTERED` with both formal profile IDs absent. This is a
   runtime blocker, not an engineering failure and not permission to edit the policy.
5. Read-only inventory every existing external `AJM006*` run directory. Classify each as
   accepted rear-inlet geometry, reusable partial evidence, superseded diagnostic, or
   unusable. Hash manifests/reports only; do not recursively hash large CAD/mesh files.
6. Produce a nine-row delta table from the trusted campaign. For each variant list the exact
   producer, observer, native/STEP, semantic sidecar/binding/observation, job-record,
   artifact-manifest and Gate-evidence roles still missing. Never mark a role present unless
   its actual external file and hash were observed.
7. Write the external report
   `C:\Users\admin\Downloads\AirJetGitWatcherReports\AJM_PLAN_A_015_FORMAL006_PREFLIGHT.md`.
   It must end with exactly these truthful ceilings:

```text
FORMAL_006_RUNTIME_AUTHORIZATION=BLOCKED_UNREGISTERED_PROFILES
ACCEPTED_REAR_INLET_PRODUCER_RERUN=PROHIBITED
P1_STAGE_GATE=NOT_PASSED
P2_STAGE_GATE=NOT_RUN
```

## Acceptance and escalation

Acceptance requires a fresh task card, exact external artifact hashes, all static test
markers, a complete nine-row delta table, and zero Git changes. At 15 minutes report Git,
handoff and profile-state evidence; at 45 minutes report the external-run inventory and test
matrix; at 90 minutes deliver the final report or an exact blocker with a revised ETA.

If the same check fails twice unchanged, stop retrying and report root cause. If an artifact
is missing or hash-mismatched, preserve it and report the literal path/hash; do not repair it.
When the report is complete, remain on Plan A's safe backlog: review the formal producer and
observer dependency map read-only and refresh the task card. Do not wait for Mac or Plan B.
