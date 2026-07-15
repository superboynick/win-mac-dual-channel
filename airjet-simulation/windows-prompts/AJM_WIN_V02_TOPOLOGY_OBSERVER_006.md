# Windows execution task: AJM-WIN-V02-TOPOLOGY-OBSERVER-006

## Outcome

Run one audited, hash-bound `producer -> Workbench topology observer` suite for the AirJet Mini Gen1 V02 complete-product preliminary CAD. The observer must enumerate the actual Mechanical body/face graph and classify the 972-hole interface as one of:

- `972_SHARED_SINGLE_FACE`
- `972_COINCIDENT_FACE_PAIRS`
- `DOWNSTREAM_HEALED_SINGLE_FACE`
- `MIXED_OR_OTHER`

This is topology discovery only. It does not mesh, solve, complete formal 006, or pass P1-P6.

## Safety and ownership

- Windows executes; Mac and Windows remain peers.
- Do not edit, commit, push, reset, clean, rebase, or force-push.
- Do not invoke ANSYS directly; use the signed runner and MCP only.
- Do not inspect or alter licensing, services, registry, activation, or checkout state.
- A healed or mixed topology is valid evidence. Do not weaken assertions or relabel it as semantic/P1 PASS.

## Execute

In PowerShell:

```powershell
cd C:\Users\admin\win-mac-dual-channel
git fetch origin
git pull --ff-only
git status --porcelain
git rev-list --left-right --count HEAD...origin/main
git verify-commit HEAD
powershell -NoProfile -ExecutionPolicy Bypass -File .\audit-airjet-project.ps1

$Python = 'C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe'
$Runner = '.\airjet-simulation\automation\ansys\run_v02_topology_observer_006.py'
$RunnerTest = '.\airjet-simulation\automation\ansys\test_run_v02_topology_observer_006.py'

& $Python -I -B $RunnerTest
if ($LASTEXITCODE -ne 0) { throw 'V02_TOPOLOGY_OBSERVER_GUARDS_FAILED' }

& $Python -I -B $Runner
$RunnerExit = $LASTEXITCODE
$Summary = 'D:\AirJet_P1\AJM-P1-CAD-006\V02_TOPOLOGY_OBSERVER_RUN_SUMMARY.json'
Write-Host "RUNNER_EXIT=$RunnerExit"
Write-Host "SUMMARY=$Summary"
if (Test-Path $Summary) { Get-Content -Raw $Summary }
```

Proceed only with signed clean `main`, `0/0` divergence, and project audit PASS. The runner intentionally reruns the deterministic producer because MCP predecessor jobs exist only in the current server process. It must freeze the producer artifact manifest before submitting the observer with the exact predecessor job ID.

## Required result boundary

Success means only:

```text
RUNNER_FINAL_STATUS=PASS_PRELIMINARY_TOPOLOGY_OBSERVER
TOPOLOGY_RESULT=<one of the four classifications>
TOPOLOGY_DETAIL=<exact diagnostic subtype, including one-sided interface loss when observed>
FORMAL_006_COMPLETION=false
P1_STAGE_GATE=NOT_RUN
P2_P6_GATES=NOT_RUN
MESH_CONFORMALITY=NOT_EVALUATED_NO_MESH
```

Preserve both job directories, the fixed suite summary, MCP stderr log, observer report, raw `v02_solver_topology_inventory.json`, and Workbench project. Stop after reporting; do not start formal nine-variant 006 or any solver run.
