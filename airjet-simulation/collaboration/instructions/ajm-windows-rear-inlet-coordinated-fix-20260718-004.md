# Execute coordinated rear-inlet correction now

Read `airjet-simulation/reports/AJM_REAR_INLET_OVERHANG_COORDINATION_2026-07-18.md`
completely and execute its non-overlapping A/B assignments.

The Mac static diagnosis is now concrete: selected V01/V02 raw vent boxes reach
`Y=-17.750 mm`; the supporting upstream footprint rear plane is `Y=-14.375 mm`; each
rear inlet riser overhangs backward by `3.375 mm`. V03/V04 are not the same defect.
The producer directly creates and unions those raw boxes without per-inlet containment.

Windows A must deliver measured SpaceClaim/native/STEP evidence and a minimal
producer/contract/test proposal. Windows B must only deliver its OpenFOAM input-rejection
contract and must not edit or run ANSYS. Use their existing isolated worktrees and
branches. The integration checkout stays read-only except for fast-forward synchronization.

Publish A results on `incident/windows-recovery-20260718-001` and B results on
`codex-b-openfoam-20260718`, each as trusted signed commits. Do not push main. Initial A
measurement checkpoint is due in 20 minutes; both source proposals are due in 60 minutes.
On any blocker, report exact command/error, owner and revised ETA immediately. Do not let
either Codex cross into the other's files merely to stay busy.

No manual native-CAD patch, bbox-only acceptance, inlet deletion/merge, CFD/CHT run,
package installation, reset, clean, rebase, force push or Gate claim is authorized.
