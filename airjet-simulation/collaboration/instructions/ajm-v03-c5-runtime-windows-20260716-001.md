# C5 Runtime: one authorized two-stage mesh execution

Windows, this is a schema-v2 root task: `parent_task_id=NONE`, `hop=0`, `max_hops=0`.
You are authorized to execute exactly ONE run of the C5 two-stage mesh suite.

## Start gate

Require clean `main`, `HEAD == origin/main`, `0/0`, GOOD Mac signature on this task tip.
Require the task tip's sole parent to equal the static freeze commit.
Do not amend, reset, rebase, merge, or force push.

## Pre-run checks (MUST all PASS before submit_job)

1. Four focused tests:
   - `python airjet-simulation/automation/ansys/contracts/test_v03_finite_throat_contract_v1.py`
   - `python airjet-simulation/automation/ansys/test_run_v03_continuous_mesh_006.py`
2. MCP policy: `profiles=20 tools=0` (from `airjet-simulation/automation/ansys/profiles.json`)
3. Python audit: all `.py` files in `airjet-simulation/automation/ansys/` parse without SyntaxError
4. PowerShell audit: no ANSYS processes running (`Get-Process ansys* -ErrorAction SilentlyContinue | measure | % Count` must be 0)
5. Git: `git diff --check` PASS, no `.pyc`/`__pycache__` in working tree
6. Student inventory: `D:\ansys\ANSYS Inc\ANSYS Student\v261` exists, Workbench/Fluent/SpaceClaim exe present
7. Exact Student 2026 R1 — no third-party licensing, no 1055@localhost, ANSYSLMD_LICENSE_FILE not set to 1055

## Authorized execution (EXACTLY ONE)

```powershell
C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe `
  .\airjet-simulation\automation\ansys\run_v03_continuous_mesh_006.py
```

## Prohibitions

- No manual stages, retries, or threshold/geometry/profile changes
- No Workbench, Mechanical, physics, solve, or formal 006 nine-variant
- No P1 PASS claim
- No ANSYS process left running after completion or failure

## Success criteria

Literal `PASS_PRELIMINARY_V03_TWO_STAGE_MESH_SUITE` with:
- Terminal producer AND consumer
- 972/972 throat occupancy
- One accepted flow cell zone
- 12 excluded actuator-gap probes
- Connected fluid cell zone graph
- <1M cells, <1M nodes
- Mesh integrity (OQ > 0, free_face=0, multi_face=0)
- Real hash-bound `.msh.h5`
- P1-P6 and physics remain NOT_RUN

## Failure

Stop without retry. Preserve partial evidence. Report `FAIL_PRELIMINARY_V03_TWO_STAGE_MESH_SUITE`.

## Required report

```
C5_RUNTIME=PASS|FAIL
RUN_COMMIT=<40hex>
CELL_COUNT=<int>
MIN_OQ=<float>
THROAT_972=PASS|FAIL
ACTUATOR_12_EXCLUDED=PASS|FAIL
GRAPH_CONNECTED=PASS|FAIL
MSH_H5_SHA256=<64hex>
ERROR=<message|NONE>
ANSYS_POST_RUN_PROCESSES=<int>
```
