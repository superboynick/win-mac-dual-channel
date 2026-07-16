# Run C6 Stage 1 (Inward Clamped Overlap)

**Task ID:** ajm-run-c6-stage1-20260716
**Source:** Mac
**Target:** Windows SpaceClaim producer
**Priority:** P3_BLOCKING — C6 code is in place, needs execution

## Status

C6 code change (`perimeter_boolean_overlap_mm = 0.05`, inward clamped) is committed.
Now RUN it to produce a new STEP geometry and verify the contract.

## Run Command

```powershell
cd C:\Users\admin\win-mac-dual-channel
python airjet-simulation\automation\ansys\run_v03_continuous_fluid_006.py
```

## After Run

1. Push the producer JSON + STEP file
2. If PASS: also run Stage 2 mesh (save_mesh4.py)
3. If FAIL: push the diagnostic evidence and describe the failure

## Acceptance

- 1 closed manifold body
- 972 throats
- X bounds = ±10.875 mm (±0.001)
- Volume within native tolerance (0.08 mm³)
- STEP volume within 0.03 mm³
