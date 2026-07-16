# C5 runtime: one V03 two-stage mesh suite execution

Windows, you are authorized to execute exactly one V03 C5 two-stage mesh run.
Static freeze parent commit: `2d9fb72868ba8ed34e5dc672b922d7c8c8dfa98f`.
Do not amend, reset, rebase, merge, force push, install skills, or rewrite evidence.

## Preflight (hard block — do NOT run if any fails)

```powershell
# 1. Clean signed Git
git status --short --branch   # must be clean, main, 0/0 vs origin/main
git rev-parse HEAD            # must == 2d9fb72868ba8ed34e5dc672b922d7c8c8dfa98f

# 2. All four focused static tests
python -B .\airjet-simulation\automation\ansys\test_run_v03_continuous_mesh_006.py
python -B .\airjet-simulation\automation\ansys\test_v03_pyfluent_watertight_mesh_consumer.py
python -B .\airjet-simulation\automation\ansys\contracts\test_v03_finite_throat_contract_v1.py
python -B .\airjet-simulation\automation\ansys\test_run_v03_continuous_fluid_006.py

# 3. MCP policy + both project audits
python -B .\codex-skills\airjet-ansys-automation\scripts\test_airjet_ansys_mcp_policy.py
python -B .\codex-skills\airjet-product-reconstruction\scripts\audit_project.py --repo .

# 4. Student ANSYS inventory
#    Must confirm: Workbench, Fluent, Mechanical APDL, SpaceClaim present
#    Authenticode: all Valid / ANSYS Inc.

# 5. ANSYS process count = 0 (no leftover Fluent/Workbench/SpaceClaim processes)
```

## Authorized single execution

```powershell
C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe `
  .\airjet-simulation\automation\ansys\run_v03_continuous_mesh_006.py
```

## Prohibitions

- No manual stages, retries, or partial re-runs
- No threshold/geometry/profile/sizing changes
- No Workbench, Mechanical, physics, solve, or modal/harmonic
- No formal nine-variant 006
- No P1 PASS claim
- No rewriting of freeze-commit evidence

## PASS criteria (all must be true)

```text
consumer_status=PASS_PRELIMINARY_MESH_CAPABILITY
mesh_result=PASS_V03_CONNECTED_ZONE_GRAPH_972_THROAT_VOLUME_MESH
occupancy_mode=FULL_972
executed_queries=972
hit_count=972
miss_count=0
raw_none_count=0
anchor_occupancy_ok=true
unique_owner_per_query=true
all_hits_in_accepted_flow_zone=true
actuator_gap_zones_excluded=true
main_flow_region_count=1
non_flow_region_count=11
cell_zone_count=1
target_flow_volume_matches_predecessor=true
cell_count < 1_000_000
node_count < 1_000_000
mesh_file.sha256 is real hex
mesh_file.size > 0
boundary_adjacency_ok=true
external_baffle_count=0
free_face_count=0
multi_face_count=0
min_orthogonal_quality in (0, 1]
```

## Failure rules

- Any failure stops without retry
- Preserve partial evidence (producer report, prelaunch trace, transcript)
- Consumer not submitted → state NOT_SUBMITTED
- Consumer submitted but failed → preserve producer facts
- Malformed evidence → FAIL, never NOT_RUN
- `P1-P6` and physics remain `NOT_RUN`

## Required terminal report

```text
C5_STATIC_FREEZE=PASS
BASE_COMMIT=2d9fb72868ba8ed34e5dc672b922d7c8c8dfa98f
CONTRACT=PASS
OCCUPANCY_972_GATE=PASS
ACTUATOR_EXCLUSION_GATE=PASS
POST_SUBMIT_CANCEL_GUARDS=PASS
MCP_POLICY=PASS profiles=20 tools=5
PYTHON_AUDIT=PASS required_files=163
POWERSHELL_AUDIT=NOT_RUN|PASS
RUNTIME_STATUS=<ACTUAL>
FORMAL_006=NOT_RUN
P1-P6=NOT_RUN
PREFLIGHT=<PASS|FAIL>
ANSYS_PROCESSES=<0|N>
RUNTIME_COMMIT=<40hex>
```
