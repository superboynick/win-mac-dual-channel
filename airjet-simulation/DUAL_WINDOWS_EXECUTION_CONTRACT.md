# Dual Windows execution, scheduling and escalation contract

## Required task card

Before work, each Codex publishes:

```text
TASK_ID=
OWNER=A|B
SCOPE=
INPUT_COMMIT=
ESTIMATED_EFFORT=
STARTED_AT_UTC=
ETA_UTC=
CHECKPOINTS=<UTC=deliverable;...>
DELIVERABLES=
ACCEPTANCE=
BLOCKERS=NONE|...
SAFE_BACKLOG_NEXT=
FILES_OWNED=
EXTERNAL_ARTIFACT_ROOT=
```

Time estimates are planning commitments, not evidence. Engineering acceptance remains Gate-based.

## Coordinator duties

Mac Codex owns scheduling, reminders, acceptance and escalation:

- Check Git/watch­er status at every checkpoint.
- Ask for delivery when a checkpoint is due; require evidence and a revised ETA when late.
- Treat no commit/report/valid active job across the agreed interval as idle.
- Stop repeated identical failures after two unchanged attempts; require root-cause analysis before another run.
- Escalate immediately when the same blocker survives two discriminating experiments, a deadline slips twice, a license/resource decision is needed, or A/B ownership overlaps.
- Report to the user: owner, expected vs actual time, delivered evidence, blocker, next decision and revised ETA.

## No-idle backlog

When a solver, dependency or peer input is pending, switch to a safe independent task:

- A: approved-script tests, profile/hash review, CAD contract checks, evidence condensation, post-processing and downstream static preparation.
- B: tooling/source tests, schema validation, case generators, conservation/post-processing scripts, official tutorial smoke preparation and downstream static templates.
- Neither line may fabricate inputs, repeat a failed case unchanged, or cross a Gate merely to stay busy.

## Acceptance

A delivery is accepted only when the declared files exist, hashes and schema validate, relevant tests/audit pass, large artifacts are externally indexed, reality failures are recorded, and the declared Gate effect matches the evidence. `RUNNING`, `DONE`, exit code 0 and solver iteration count are not acceptance states.

## Shared-file lease

Every task names `FILES_OWNED`. Shared files receive one temporary writer; the other line is read-only until that task commits. Conflicts stop both writers and go to the coordinator.
