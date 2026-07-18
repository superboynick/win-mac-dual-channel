# AJM Windows Incident Recovery Report
**UTC**: 2026-07-18T17:15:00Z
**Branch**: incident/windows-recovery-20260718-001
**Task**: ajm-windows-four-inlet-cad-correction-20260718-003

## INCIDENT_STATE=OPEN_CONFIRMED_REAR_INLET_OVERHANG
## USER_CONFIRMED_FOUR_INLETS=YES
## DEFECT_DIRECTION=BACKWARD_NOT_DOWNWARD

## Evolution
1. A reported outlet overhang → incident opened
2. Mac closed as FALSE_POSITIVE (task 002): Y asymmetry is intentional outlet manifold
3. User personally inspected 3D geometry → confirmed REAL defect
4. Mac retracted false positive, opened task 003

## Confirmed Defect
- Two of four inlet structures at tail extend backward past intended rear boundary
- Defect direction: backward overhang (not downward)
- Affected: inlet structures, not outlet manifold
- Remaining two inlet structures are normal

## Root Cause Analysis
- Producer: run_v03_continuous_fluid_006.py (SpaceClaim IronPython)
- Likely cause: inlet structure placement/mirror/array at rear positions
- Not a bbox-only issue; requires per-inlet boundary check

## A Limitations
- SpaceClaim installed but no PySpaceClaim (ansys.api.spaceclaim not available)
- Cannot measure inlet overhangs programmatically
- Cannot identify exact producer operation without opening scdocx

## Request to Mac
- Provide SpaceClaim measurement/identification instructions for GUI
- Or push a reviewed SpaceClaim script to run via Workbench
- Or perform the CAD diagnosis from Mac side

## Actions Taken
- Read-only inventory: COMPLETE
- Destructive actions: NONE
- ANSYS execution: NONE
- OpenFOAM execution: NONE
- Git communication: FUNCTIONAL (bidirectional confirmed)

## P1-P6 Gate Effect
- P1-P6: NOT_RUN
- C7: pending CAD fix + MCP retry
- CF: NOT_STARTED

## Next Checkpoint
Within 30 min or on state change.
