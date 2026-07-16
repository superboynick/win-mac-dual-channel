# C7: Bridge Solids at Bottom-Chamber Interface

**Task ID:** ajm-c7-bridge-solids-20260716
**Source:** Mac (analysis of C6 failure)
**Target:** Windows SpaceClaim producer

## C6 Failure Analysis

C6 moved ring inner edges inward by 0.05mm for the FULL ring height.
Result: +4.587mm³ volume, membrane faces 12→0. Too aggressive.

## C7 Approach

1. **Keep original full-height rings unchanged** — revert `perimeter_boolean_overlap_mm` to original behavior
2. **Add redundant bridge solids** ONLY at the bottom-chamber interface (Z: bottom_z_min to bottom_z_max)
3. Each bridge is a small rectangular prism:
   - X: overlaps the ring inner edge and the bottom block by 0.05mm
   - Y: spans the full ring section
   - Z: bottom_z_min to bottom_z_max
4. Bridge solids must be **fully contained** in the frozen final union
5. After Merge, bridges disappear into the union without changing outer geometry

## Implementation Notes

In the producer, after creating the bottom blocks and ring blocks, add:
```python
# Bridge solids at each ring-bottom interface
# RING_L bridge: X from cx-half_membrane-0.05 to cx-half_membrane+0.05
# Same for RING_R, RING_B, RING_T
# Z: bottom_z_min to bottom_z_max
```

## Acceptance Criteria

| Gate | Criterion |
|---|---|
| G1 | 1 closed manifold body |
| G2 | 972 throats |
| G3 | X bounds = ±10.875 mm |
| G4 | Volume within 0.08mm³ tolerance |
| G5 | Membrane faces 12/12 preserved |

## Run Command

```powershell
cd C:\Users\admin\win-mac-dual-channel
python airjet-simulation\automation\ansys\run_v03_continuous_fluid_006.py
```
