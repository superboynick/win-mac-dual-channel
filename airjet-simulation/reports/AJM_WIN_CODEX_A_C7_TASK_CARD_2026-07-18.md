# Windows Codex A C7 task card

```text
TASK_ID=ajm-win-a-c7-formal-20260718-010
OWNER=A
SCOPE=Close the AJM-006 C7 full-product mesh boundary contract through the reviewed hash-pinned two-stage ANSYS runner; stop before solver mode on any failed assertion.
INPUT_COMMIT=bda8341bc9b9a188d2a39dcf5ae4cbd850e13f73
ESTIMATED_EFFORT=3 hours after the blocking main-worktree conflict is cleared
STARTED_AT_UTC=2026-07-18T09:23:00Z
ETA_UTC=2026-07-18T13:15:00Z revised after the 09:30Z checkpoint slipped because the overlapping CLI started a third ad-hoc Fluent experiment
CHECKPOINTS=2026-07-18T09:30:00Z=missed: integration main synchronized then re-dirtied by overlapping CLI;2026-07-18T10:15:00Z=conflict cleanup plus watcher/inventory preflight;2026-07-18T12:15:00Z=formal two-stage terminal evidence;2026-07-18T13:15:00Z=validated report and peer-review handoff
DELIVERABLES=External producer and consumer manifests, native CAD/mesh hashes, C7 semantic-gate report, compact Git evidence report, and signed source-only commit if a reviewed fix is required
ACCEPTANCE=4 inlet zones;1 outlet;972 throat faces;1 heat wall;12 membrane-top;12 membrane-bottom;complete 1078-face coverage;10 canonical boundary zones;one connected main fluid zone;correct full-product bbox;Student guards;mesh integrity and quality;real mesh hash;solver mode NOT_ENTERED on failure
BLOCKERS=Primary main is behind origin/main and is dirty because the separate Windows Codex CLI is running an overlapping ad-hoc Fluent diagnostic against A-owned ANSYS files; watcher and official airjet-ansys inventory are therefore fail-closed
SAFE_BACKLOG_NEXT=Run source-only C7 gate/runner/consumer guard tests;review approved profile and hash closure;condense the overlapping diagnostic failure evidence;prepare peer-review handoff without solver execution
FILES_OWNED=airjet-simulation/reports/AJM_WIN_CODEX_A_C7_TASK_CARD_2026-07-18.md;airjet-simulation/automation/ansys/run_v03_continuous_mesh_006.py;airjet-simulation/automation/ansys/approved/006/v03_pyfluent_watertight_mesh_consumer.py;airjet-simulation/automation/ansys/profiles.json;airjet-simulation/automation/ansys/contracts/c7_hdf5_boundary_semantic_gate.py;corresponding A-side tests
EXTERNAL_ARTIFACT_ROOT=D:\AirJet_P1\AJM-P1-CAD-006\AJM006-A-C7-FORMAL-20260718
```

Initial safe-backlog verification at `2026-07-18T09:22:00Z`:

- C7 HDF5 semantic gate direct test: PASS (`positive=1`, `collapsed=1`, `negative=9`, `parser=2`).
- Formal two-stage runner guards: PASS_ALL (17 tests).
- V03 PyFluent consumer guards: PASS_ALL (31 tests).
- No ANSYS process was launched by Codex A.

Current escalation: the overlapping CLI is assigned by the user to Windows track B but is repeatedly modifying and executing A-owned ANSYS/Fluent files in the dirty integration checkout. Its outputs are diagnostic only and cannot satisfy this task's signed-input or official-MCP acceptance requirements.

Checkpoint update at `2026-07-18T09:36:00Z`:

- Integration `main` was fast-forwarded to signed Mac commit `bda8341bc9b9a188d2a39dcf5ae4cbd850e13f73`, but the overlapping CLI immediately re-dirtied the A-owned consumer and recreated root-level ad-hoc scripts.
- Its first two observed terminal attempts both stopped before volume mesh. Attempt 2 tested deletion of `dead*` regions, observed none to delete, and still failed at `Topology region with name dead0 already exists`.
- Attempt 3 is active and tests saving the labeled surface mesh before the region failure, followed by a standalone surface-to-volume mesher. It is diagnostic only; no A Gate claim is permitted.
- Revised ETA is `2026-07-18T13:15:00Z`. The exact blocker remains concurrent A-file ownership overlap, dirty integration checkout, watcher off and official MCP inventory fail-closed.

Formal A execution checkpoint at `2026-07-18T10:08:00Z`:

- Production watcher was clean and `WATCHING`; official ANSYS inventory returned `ready=true` at signed head `bda8341bc9b9a188d2a39dcf5ae4cbd850e13f73`.
- Reviewed two-stage runner submitted producer job `AJM006-V03-CONTINUOUS-cd12932a990d` and consumer job `AJM006-V03-CONTINUOUS-b5dcd946e346` through the official MCP only.
- Producer reached `PROCESS_EXITED_0`; consumer reached `FAILED_PROCESS` with exit code `2` at `workflow.create_regions()` and literal error `Topology region with name dead0 already exists`.
- Consumer report preserved boundary evidence (4 inlet zones, 1 outlet, 972 throat hits, 1078 imported face zones, throat local sizing) but `volume_mesh=false`, `solver_mode=NOT_ENTERED`, `p1_p6_gates=NOT_RUN`, and `formal_006_completion=false`.
- Full producer/consumer job trees and MCP stderr are indexed in the external recovery increment `D:\AirJet_P1\external-evidence\workspace-recovery-20260718T075804Z\increment-20260718T101000Z`.
- Repeated overlapping CLI experiments were archived as diagnostics only; they do not alter A acceptance or the signed canonical consumer. Main checkout was restored clean and watcher returned to `WATCHING` after evidence capture.

Current decision: escalate the unchanged `dead0` topology blocker to Mac for root-cause/design decision; do not repeat the same consumer route or enter solver mode without a reviewed source change.

Mac remediation handoff:

- Root cause is isolated to the pre-region inlet split: `sep_face_zone_by_region` creates implicit topology-region state before the Watertight `Create Regions` task, whose first generated void name then collides at `dead0`.
- The reviewed consumer now uses an 89-degree face-angle split for the four disconnected planar inlet patches. Exact four-zone cardinality, face-count conservation, and four representative-point bindings remain mandatory fail-closed checks.
- A must pull the reviewed signed commit, verify the policy hash, and run exactly one official-MCP two-stage retry. Do not retain or rerun the prior diagnostics. ETA: source sync/preflight 15 minutes; formal retry evidence 2 hours; blocker report immediately on the first failed assertion.
