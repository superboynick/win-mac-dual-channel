# Mac to Windows collaboration E2E test

This is a coordination-channel test only. Do not run or modify CAD, ANSYS, Fluent,
OpenFOAM, WSL, Docker, native artifacts, profiles or engineering contracts.

From the synchronized integration checkout, verify and report:

1. task commit equals the signed commit containing this instruction;
2. branch is `main`, upstream is `origin/main`, worktree is clean and divergence is 0/0;
3. this task commit has a valid trusted Mac signature;
4. the frozen defect facts read from the committed coordination report are:
   actual plenum rear plane `Y=-14.500 mm`, V01/V02 minimum `Y=-17.750 mm`, unsupported
   rear length `3.250 mm` each, exactly four inlets and one outlet;
5. A owns ANSYS runtime CAD correction, B owns OpenFOAM input rejection, Mac owns
   integration and acceptance;
6. Windows watcher manager status, PID, state/detail and whether this task was consumed
   automatically by watcher or manually by an already-visible Codex session.

Create or update branch `incident/windows-recovery-20260718-001`. Write
`airjet-simulation/reports/AJM_MAC_WINDOWS_COLLAB_E2E_2026-07-18.md` containing these
literal fields:

```text
COLLAB_E2E=PASS|FAIL
TASK_ID=ajm-mac-windows-collaboration-e2e-20260718-005
TASK_COMMIT=<full hash>
CONSUMPTION=WATCHER_AUTOMATIC|VISIBLE_CODEX_MANUAL
INTEGRATION_CLEAN=true|false
DIVERGENCE=<ahead>/<behind>
MAC_SIGNATURE=PASS|FAIL
DEFECT_FACTS=PASS|FAIL
OWNERSHIP_SPLIT=PASS|FAIL
DESTRUCTIVE_ACTIONS=NONE
SOLVER_ACTIONS=NONE
UTC_RECEIVED=<ISO-8601 UTC>
UTC_PUSHED=<ISO-8601 UTC>
LATENCY_SECONDS=<integer>
```

Commit with the trusted Windows signing key and push only that incident branch. Do not
push main. Target delivery is 10 minutes. If any check fails, set `COLLAB_E2E=FAIL`,
preserve exact error text and still push the signed report. Exit code 0 alone is not a
PASS.
