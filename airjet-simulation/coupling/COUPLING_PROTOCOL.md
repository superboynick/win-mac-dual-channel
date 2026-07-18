# Dual Windows Codex coupling protocol

| Slot | Runtime | Full track | Exclusive ownership |
|---|---|---|---|
| A | Windows Codex A | Complete ANSYS P1-P6 | `automation/ansys/`, ANSYS run evidence, `membrane_params.json` |
| B | Windows Codex B | Complete OpenFOAM P3-P6 reproduction | `automation/openfoam/`, OpenFOAM cases/evidence, `cell_results.json` |
| Coordinator | Mac Codex | Scheduling, audit, acceptance, Git integration | task contracts, peer-review reports, deadline/escalation board |

## Worktree isolation

- Keep one clean integration checkout for watcher/Git handoff.
- A and B use separate Windows worktrees and separate external artifact roots.
- A and B never edit the same file concurrently. Shared status has a temporary named owner in the active task contract.
- Generated meshes, case/data, fields, transcripts, containers and native projects stay outside Git; Git stores small manifests, hashes and interpretations only.

## Data handoff

1. Producer writes a versioned schema-valid JSON plus units, evidence class, source commit and artifact hashes.
2. Producer commits and pushes from a clean, linear branch/worktree.
3. Consumer fast-forwards, validates schema/hash/units, and records acceptance or a precise rejection.
4. A rejected handoff returns to its owner. The consumer must not silently repair or overwrite it.

Coupling order:

`A/P1 geometry → A/P2 displacement → A/P3 and B/P3 independent cell maps → A/P4 and B/P4 full-product airflow → A/P5 and B/P5 CHT → P6 comparison`

## No duplicate work

- Every run has one task ID, owner, case ID, hypothesis and acceptance condition.
- A second implementation is allowed only when explicitly labeled independent cross-validation.
- Do not run placeholder AirJet physics while waiting. Work from the safe backlog in `DUAL_WINDOWS_EXECUTION_CONTRACT.md`.
- Never force-push, reset, clean, stash, rebase or overwrite peer work. Stop on dirty/diverged state.

## Completion boundary

Only formal Gate evidence changes P1-P6 status. Process exit, repeated identical meshes, solver iterations, or a zero-flow residual history do not establish engineering completion.
