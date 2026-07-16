# Stage 1 Geometry Fix: Inward Boolean Overlap

**Task ID:** ajm-stage1-geometry-fix-inward-overlap
**Source:** Mac (diagnostic review of 0.15mm overlap)
**Target:** Windows SpaceClaim producer
**Priority:** P3-blocking — no Stage 2 without clean Stage 1

## Problem

C5 0.15mm perimeter overlap diagnostic:
- ✅ Fixed region selection (main flow body, not actuator gap)
- ❌ Changed frozen geometry: X bounds +0.025mm, volume +0.102mm³

## Root Cause

`perimeter_boolean_overlap_mm` extends ring block inner edges toward membrane center.
`Combine.Merge` at the domain boundary produces slight numerical expansion.
At 0.15mm the expansion (0.025mm) exceeds STEP tolerance (0.03mm).
At 0.02mm the expansion was within tolerance but region selection failed.

## Fix Strategy

**内收式（Inward）Boolean overlap:**
1. Reduce `perimeter_boolean_overlap_mm` from 0.15 to 0.05
2. Add explicit clamping: ring block outer edges at footprint bounds
3. Verify the overlap region is entirely inside frozen domain

### Implementation

In `v03_continuous_fluid_producer.py`:

```python
# Change line 755
perimeter_boolean_overlap_mm = 0.05  # was 0.15

# In the ring block creation (lines 911-928), clamp outer edges:
# RING_L: x0 = max(cx - half_tile, footprint_x_min)
# RING_R: x1 = min(cx + half_tile, footprint_x_max)
# RING_B: y0 = max(cy - half_tile, footprint_y_min)
# RING_T: y1 = min(cy + half_tile, footprint_y_max)
```

### Acceptance Criteria

| Gate | Criterion |
|---|---|
| G1 | 1 closed manifold body |
| G2 | 972 throats preserved |
| G3 | X bounds = ±10.875 mm (within 0.001) |
| G4 | Y bounds unchanged |
| G5 | Volume within native 0.08mm³ tolerance |
| G6 | STEP volume within 0.03mm³ tolerance |
| G7 | 1 fluid + 11 voids in WTM (or equivalent region selection) |

## Run Command

```powershell
cd C:\Users\admin\win-mac-dual-channel
python airjet-simulation\automation\ansys\run_v03_continuous_fluid_006.py
```

## Output

Push result commit with producer JSON + STEP file.
