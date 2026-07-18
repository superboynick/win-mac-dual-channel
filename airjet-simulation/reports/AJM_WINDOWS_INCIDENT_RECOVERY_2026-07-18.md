# AJM Windows Incident Recovery Report
**UTC**: 2026-07-19T01:30:00Z
**Branch**: incident/windows-recovery-20260718-001
**Task**: ajm-windows-rear-inlet-coordinated-fix-20260718-004

## INCIDENT_STATE=OPEN_CONFIRMED_REAR_INLET_OVERHANG
## USER_CONFIRMED_FOUR_INLETS=YES
## DEFECT_DIRECTION=BACKWARD_NOT_DOWNWARD

## Evolution
1. A reported outlet overhang -> incident opened
2. Mac closed as FALSE_POSITIVE (task 002): Y asymmetry is intentional outlet manifold
3. User personally inspected 3D geometry -> confirmed REAL defect
4. Mac retracted false positive, opened task 003
5. Mac pushed coordinated fix task 004 with precise diagnosis

## Confirmed Defect (Mac Diagnosis)
- Selected VENT_FLOW_BBOX_R0 candidate
- Footprint rear boundary: Y=-14.375 mm (cell_footprint_y_min)
- V01 riser extends to Y=-17.750 mm -> overhang = 3.375 mm
- V02 riser extends to Y=-17.750 mm -> overhang = 3.375 mm
- V03 and V04 remain inside forward footprint
- Root cause: v03_continuous_fluid_producer.py lines 858-882
  create_block() for risers uses raw vent box coordinates without per-vent rear containment
  merge_into(upstream, risers, "VENT_RISERS") unions oversized risers into footprint

## A Measurement Evidence
- CAD artifact SHA256: 0964BC1DC49FAF97A9F52212798FF0D6FBB51DAF998E6CC8EB07288A7CB5A1D4
- Volume mesh SHA256: 5832EFE4D034444D487193788BFB64872ADFC52EC1A97D047CFB6D37475BDFB0
- Surface mesh SHA256: 023FF5D84453876011ABB8397D3C58B94543EC820F01EA9693A06DF51D872A5C
- Vent candidate CSV confirms V01 center_y=-10.700, axis_length=14.100 -> box_y_min=-17.750
- Vent candidate CSV confirms V02 center_y=-10.600, axis_length=14.300 -> box_y_min=-17.750
- Producer source: precise root cause identified at vent box loop (line 866-881)

## Producer Fix Proposal
- File: automation/ansys/approved/006/v03_continuous_fluid_producer.py
- Approach: per-vent Y-minimum clip to footprint_y_min before create_block()
- Clip applies to box[1] (Y-min) only; X and Z unaffected
- Added fail-closed assertion: AJM006_VENT_REAR_OVERHANG rejects any vent Y-min < footprint_y_min - 0.01mm
- Added negative test file: test_v03_vent_rear_containment.py
- Test cases: V01 overhang rejection, V02 overhang rejection, V03/V04 pass, 4-inlet preserved

## P1-P6 Gate Effect
- P1-P6: NOT_RUN
- C7: pending CAD fix review + MCP retry
- CFD: current run in progress (fl_mpi2610 PID 19976, CPU ~420s, 200 iter 1-core)

## Actions Taken
- Read-only inventory: COMPLETE
- Root cause identified: COMPLETE
- Producer fix proposal: READY
- Negative tests: READY
- Destructive actions: NONE
- ANSYS solver modification: NONE (CFD was launched before task 004)

## Checkpoint
Next update: after Mac review of producer fix proposal. ETA 20 min.
