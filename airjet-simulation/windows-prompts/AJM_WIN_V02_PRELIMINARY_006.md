# Windows Codex task: AJM-WIN-V02-PRELIMINARY-PRODUCER-006

## Outcome

Run the hash-pinned `ajm006-spaceclaim-v02-preliminary-v1` profile once through the audited AirJet MCP. This creates the complete V02 3x4 / 12-cell / 972-orifice two-fluid-zone preliminary CAD and records its actual SpaceClaim result. It is a P1 candidate activity only: formal P1 and P2-P6 remain `NOT_RUN`.

Do not run the Workbench observer yet. It is not registered in `profiles.json` and its draft is not part of this producer task.

## Ownership and safety

- Windows is the temporary executor for this one ANSYS job; Mac and Windows remain peer collaborators.
- Do not modify, commit, or push Git during this task.
- Do not read or alter license files, services, registry values, checkout configuration, or activation state.
- Do not invoke ANSYS directly. Use the fixed runner and audited MCP only.
- Do not mesh or solve physics.
- Do not turn `PASS_PRELIMINARY_PRODUCER` into P1 PASS, formal 006 completion, semantic PASS, or exact-product proof.
- A failed assertion is evidence. Preserve it and stop; do not weaken counts or replace measured values.

## 1. Synchronize and verify

In PowerShell:

```powershell
cd C:\Users\admin\win-mac-dual-channel
git fetch origin
git status --short --branch
git status --porcelain
git rev-parse --abbrev-ref HEAD
git rev-parse --abbrev-ref --symbolic-full-name '@{u}'
git rev-list --left-right --count HEAD...origin/main
git pull --ff-only
git rev-parse HEAD
git verify-commit HEAD
powershell -NoProfile -ExecutionPolicy Bypass -File .\audit-airjet-project.ps1
```

Proceed only when branch is `main`, upstream is `origin/main`, the worktree is clean, ahead/behind is `0/0`, the tip signature verifies, and the project audit passes. On any mismatch, stop and report the exact output without reset, clean, rebase, force push, or file copying.

Read:

- `AGENTS.md`
- `airjet-simulation/PROJECT_STATUS.md`
- `airjet-simulation/DECISION_AND_REASONING_ARCHIVE.md`
- `airjet-simulation/manuals/01_FULL_PRODUCT_CAD.md`
- this task file

## 2. Static producer checks

```powershell
$Repo = 'C:\Users\admin\win-mac-dual-channel'
$Producer = Join-Path $Repo 'airjet-simulation\automation\ansys\approved\006\v02_preliminary_producer.py'
$Runner = Join-Path $Repo 'airjet-simulation\automation\ansys\run_v02_preliminary_006.py'
$RunnerTest = Join-Path $Repo 'airjet-simulation\automation\ansys\test_run_v02_preliminary_006.py'
$Python = 'C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe'

Get-FileHash -Algorithm SHA256 $Producer
& $Python -I -B $RunnerTest
if ($LASTEXITCODE -ne 0) { throw 'V02_RUNNER_GUARDS_FAILED' }
```

The producer hash must equal the value pinned for `ajm006-spaceclaim-v02-preliminary-v1` in `airjet-simulation/automation/ansys/profiles.json`. The test must end with `AJM006_V02_PRELIMINARY_RUNNER_GUARDS=PASS_ALL`.

## 3. Run exactly once

```powershell
& $Python -I -B $Runner
$RunnerExit = $LASTEXITCODE
$Summary = 'D:\AirJet_P1\AJM-P1-CAD-006\V02_PRELIMINARY_RUN_SUMMARY.json'
Write-Host "RUNNER_EXIT=$RunnerExit"
Write-Host "SUMMARY=$Summary"
if (Test-Path $Summary) { Get-Content -Raw $Summary }
```

The runner performs signed-clean-main preflight and then MCP `inventory -> submit_job -> poll_job -> artifact_manifest`. It accepts success only if:

- MCP terminal phase is `PROCESS_EXITED_0`;
- the inlined report is valid JSON with `status=engineering_capability=PASS_PARTIAL_CAD_CAPABILITY`;
- all ten producer assertions are true;
- Git/profile/script/case identity matches the submitted job;
- the six declared CAD/inventory artifacts match the MCP manifest by filename, size, and SHA256;
- `formal_006_completion=false`, `p1_stage_gate=NOT_RUN`, and `p1_p6_gates=NOT_RUN`.

The producer itself must measure, not merely declare, the V02 topology: two connected closed/manifold fluid bodies; 4 inlet faces; 1 outlet face; 12 membrane-top and 12 membrane-bottom faces; 972 upstream and 972 downstream circular interface candidates; 1 heat wall; native reopen and STEP reimport equivalence. The 972-hole candidate has approximately 8.114445% membrane-area porosity; the 10% table value remains an unlocked proxy, not an equality target.

## 4. Report without changing Git

Return these fields to the coordinating session:

```text
TASK=AJM-WIN-V02-PRELIMINARY-PRODUCER-006
GIT_COMMIT=<40 hex>
GIT_CLEAN=true
GIT_AHEAD_BEHIND=0/0
PROJECT_AUDIT=PASS
RUNNER_EXIT=<integer>
RUNNER_FINAL_STATUS=<PASS_PRELIMINARY_PRODUCER or FAIL_PRELIMINARY>
JOB_ID=<actual or NONE>
JOB_PHASE=<actual or NONE>
PRODUCER_REPORT_STATUS=<actual or NONE>
ASSERTIONS=<actual object or NONE>
ARTIFACT_MANIFEST_FILE_COUNT=<actual or NONE>
SUMMARY_PATH=D:\AirJet_P1\AJM-P1-CAD-006\V02_PRELIMINARY_RUN_SUMMARY.json
P1_STAGE_GATE=NOT_RUN
P2_P6_GATES=NOT_RUN
FORMAL_006_COMPLETION=false
ERROR=<exact message or NONE>
```

If the producer fails, also report the job directory, `v02_preliminary_producer.json`, `stdout.log`, and `stderr.log` paths when present. Stop after reporting. Do not run the draft observer or start formal 006.
