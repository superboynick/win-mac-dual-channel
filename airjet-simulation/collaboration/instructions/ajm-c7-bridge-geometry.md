# C7 Geometry Fix: Bridge Solids at Bottom Interface

**Task ID:** ajm-c7-bridge-geometry
**Source:** Mac (from C6 failure analysis)
**Target:** Windows SpaceClaim producer
**Priority:** P3_BLOCKING — C6 inward 0.05mm added 4.6mm³ extra volume

## C6 Failure Summary

C6 moved ring inner edges inward → added volume through entire ring height → +4.587mm³.
Also lost 12/12 membrane top/bottom faces.

## C7 Strategy: Redundant Bridge Solids

**Do NOT modify existing ring blocks.** Instead:

1. For each of the 4 perimeter ring blocks, create a small "bridge" solid at the bottom interface
2. Bridge = thin rectangular block that overlaps BOTH the ring bottom face AND the base plate
3. Bridge dimensions: 0.05mm thick (Z), ring width (XY) at the bottom interface location
4. Bridge is FULLY contained within the frozen geometry union → no volume or bounds change
5. After bridge creation, Combine.Merge produces the necessary physical overlap

### SpaceClaim Implementation

```python
# For each ring at the bottom ring-base interface:
# bridge_z_center = ring.z_bottom
# bridge_z_height = 0.05  # small overlap thickness
# bridge = Block.Create(Frame.Create(origin, x_dir, y_dir))
# bridge.SetExtent(ring_length, ring_width, 0.05)
# bridge.Translate(Vector.Create(0, 0, ring.z_bottom - 0.025))
# Add bridge to merge list
```

### Key Constraint

The bridge must NOT:
- Extend beyond the frozen geometry bounds
- Add volume outside the union
- Change any face counts for non-interface faces

### Acceptance Criteria

Same as C6:
- 1 closed manifold body
- 972 throats preserved
- X bounds = ±10.875 mm
- Membrane top/bottom = 12/12
- Volume within native 0.08mm³ tolerance
- STEP volume within 0.03mm³ tolerance

## If This Also Fails

Fall back to the split-face approach:
- Use ring bottom faces to split the base plate top face
- Delete the ring-projected areas from base
- This creates physical opening without Boolean Merge

## Run Command

```powershell
cd C:\Users\admin\win-mac-dual-channel
python airjet-simulation\automation\ansys\run_v03_continuous_fluid_006.py
```
