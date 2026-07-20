# Dual Windows harness status — 2026-07-20

## Current control state

- Reviewed rear-inlet source: four vent boxes preserved; C-class shared plenum extends from
  cell footprint `Y=-14.500 mm` to `Y=-17.750 mm`.
- Reviewed producer SHA: `8f23d7d7dd66efcf06909341a45a76caccd6732cbf11fa1f54157699d55228b0`.
- Windows incident `d42630d` is a superseded candidate and must not be cherry-picked.
- The old Fluent result used pre-correction geometry/mesh and is diagnostic only.
- Native/STEP runtime acceptance, OpenFOAM input acceptance and P1--P6 are not passed.

## Governance findings

- The Windows custom heartbeat loop created 182 signed heartbeat-only commits on `main`.
  Existing history is preserved, but new Git heartbeat commits are prohibited.
- A rejected clip implementation entered `main`; this harness recovery removes it and
  restores the independently tested producer/profile SHA pair.
- `MAC_TASK.env` was overwritten with a non-schema task-completion record. It is restored to
  the exact schema-v2 task form; results belong in immutable receipt files, not task endpoints.
- Official Windows watcher recovery remains unproven until the reviewed manager reports a
  live PID/state from the visible desktop. Generic background jobs do not count.

## Ownership and acceptance

| Owner | Exclusive work | First evidence | Acceptance owner |
|---|---|---|---|
| Windows A | Official ANSYS producer and native/STEP reopen | MCP inventory/profile/job | Mac independent review |
| Windows B | OpenFOAM input rejection harness only | test matrix and signed branch | Mac independent review |
| Mac | Git linear integration, contract audit, deadlines and Gate language | signed task tip and audit | user retains final scope decisions |

All lines use the 15/45/90-minute checkpoints in task 007. No owner may stay idle while a
solver/input is pending: use only its assigned source tests, evidence condensation or static
review backlog.
