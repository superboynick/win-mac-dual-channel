# Dual Codex Coupling Protocol

Two Codex instances run in parallel on Windows:

| Slot | Codex | Track | Owns |
|---|---|---|---|
| A | ANSYS Codex | Structural | CAD geometry, Mechanical (piezo modal, harmonic, displacement, frequency) |
| B | OpenFOAM Codex | Fluid + Thermal | Single-cell CFD, full-device CFD, CHT |

## Communication Channel

**Primary:** Git repository (`win-mac-dual-channel`). Every exchange goes through `airjet-simulation/coupling/`.

**Secondary:** `COUPLING_STATUS.md` — shared message board. Both instances read it before acting and write to it after acting.

## Handoff Flow

```
[Codex A]                        [Codex B]
    │                                │
    ├─ Mechanical solves             │
    ├─ Writes membrane_params.json   │
    ├─ Updates COUPLING_STATUS.md    │
    ├─ git add, commit, push         │
    │                                │
    │                                ├─ git pull --ff-only
    │                                ├─ Reads COUPLING_STATUS.md
    │                                ├─ Sees "ANSYS_DONE = YES"
    │                                ├─ Reads membrane_params.json
    │                                ├─ Runs single-cell CFD
    │                                ├─ Writes cell_results.json
    │                                ├─ Updates COUPLING_STATUS.md
    │                                ├─ git add, commit, push
    │                                │
    ├─ git pull --ff-only            │
    ├─ Reads cell_results.json       │
    ├─ Compares with datasheet       │
    ├─ Accepts or requests re-run    │
    │                                │
```

## Rules

1. **Never force-push.** Never rewrite history.
2. **One owns the write.** Only Codex A writes `membrane_params.json`. Only Codex B writes `cell_results.json`. `COUPLING_STATUS.md` can be written by either, but never at the same time.
3. **Pull before write.** Always `git pull --ff-only` before editing any coupling file.
4. **Commit atomically.** Group related coupling outputs in one commit.
5. **Status before action.** Read `COUPLING_STATUS.md` before starting any coupled task.
6. **Do not block.** If the other Codex is not ready, continue independent work. Do not wait.

## What to do while waiting

| Codex A (ANSYS) | Codex B (OpenFOAM) |
|---|---|
| Refine CAD geometry | Set up solver dictionaries |
| Run mesh independence study | Test single-cell with placeholder params |
| Prepare Workbench journal | Validate turbulence model choice |
| Read patent evidence | Write post-processing scripts |
