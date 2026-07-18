# AJM Windows Incident Recovery Report
**UTC**: 2026-07-18T11:10:00Z
**Branch**: incident/windows-recovery-20260718-001

## INCIDENT_STATE=OPEN

## Observed Failure
CAD geometry defect: outlet upper rectangular zones extend beyond housing boundary.
- Source: product_continuous_fluid.scdocx (V03 pilot)
- BBox Y=[-17.75, 20.75] (asymmetric, outlet side extended)
- Producer: exact_product_geometry=NOT_CLAIMED, formal_006_completion=false
- Impact: mesh includes invalid flow domain -> CFD results unreliable

## Worktree Inventory
| Worktree | Branch | HEAD | Status |
|----------|--------|------|--------|
| integration | main | 60916ea | 1 untracked (status file) |
| A (ANSYS) | codex-a-ansys-20260718 | c4195a6 | clean |
| B (OpenFOAM) | codex-b-openfoam-20260718 | be92c30 | clean |

## A State
- Dead0 fix: pulled (90b645a -> 60916ea)
- C7 retry: pending MCP availability
- ANSYS processes: 0
- PyFluent: operational but license unstable
- SpaceClaim: installed, no PySpaceClaim

## B State
- Scope: OpenFOAM CFD/CHT only
- Not accessed by A

## Actions Taken
- Read-only inventory: COMPLETE
- Destructive actions: NONE
- ANSYS execution: NONE
- OpenFOAM execution: NONE

## Next Action
- Mac: review CAD defect, provide SpaceClaim fix script or approve manual fix
- Windows: execute fix when ready
- C7 retry: requires Mac MCP; Windows Python direct run blocked by license instability

## P1-P6 Gate Effect
- P1-P6: unchanged, remain NOT_RUN
- C7 volume_mesh: remains false pending fix

## Checkpoint
Next update within 30 min or on state change.
