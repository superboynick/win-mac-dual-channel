# Plan B: recover and submit the isolated OpenFOAM consumer work

TASK_ID=`ajm-plan-b-consumer-recovery-20260721-016`

Windows Plan B exclusively owns this recovery. Do not read, write, run or kill ANSYS, MCP,
SpaceClaim, Workbench, Mechanical, Fluent or Plan A processes. The only repository files in
scope are:

- `airjet-simulation/automation/openfoam/consume_rear_inlet_artifacts.py`
- `airjet-simulation/automation/openfoam/test_consume_rear_inlet_artifacts.py`

## Safe branch recovery

1. Record a task card and 15/45/90 minute ETA in the external report root.
2. Verify the current branch is `main`, HEAD is `767c542`, ahead/behind is `0/<positive>`,
   and `git status --short` contains exactly the two untracked files above. Stop and report
   any other state. Do not pull, reset, clean, stash, merge, rebase or overwrite.
3. Create and switch to `codex-b-openfoam-consumer-20260721` from the current HEAD. Refuse if
   that branch already exists locally or remotely.
4. Inspect both files fully. Their role is artifact ingestion and fail-closed validation only;
   they cannot authorize an OpenFOAM solve while formal interface requirements remain unmet.
   Require bounded JSON depth/size, duplicate-key rejection, normalized-path uniqueness,
   exact accepted-handoff identity and hashes, and caught parser/type/resource failures.
5. Run the new test plus the existing handoff validator tests and project audit. Add only the
   two owned files. Review `git diff --cached` and `git diff --check`.
6. Commit with the configured trusted Windows signing identity, verify the signature, and
   push only the new branch. Never push `main` from this recovery.

## Delivery

Write `AJM_PLAN_B_016_RECOVERY_REPORT.md` outside Git with branch, commit, signature result,
tests, file hashes, runtime, blockers and revised ETA. End with:

```text
TRACK_B_SOLVER_AUTHORIZATION=REJECT
P1_STAGE_GATE=NOT_PASSED
P2_STAGE_GATE=NOT_RUN
MAC_INTEGRATION=REQUIRED
```

After the branch push, stop. Do not switch back, cherry-pick, or wait for Plan A. Mac owns
independent review and linear integration.
