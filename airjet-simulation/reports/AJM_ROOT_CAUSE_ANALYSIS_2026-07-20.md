# WINDOWS A — ROOT CAUSE ANALYSIS & CORRECTION
**UTC**: 2026-07-20T08:34:22Z
**Incident Branch**: incident/windows-recovery-20260718-001
**Correction Commit**: d42630d

## ROOT CAUSE

The error originated from TWO independent failures:

### 1. Information Processing Error
- **Source**: I read cell_footprint_y_min_mm from CSV = -14.375 mm
- **Corrected by Mac**: The frozen contract value is -14.500 mm (0.125 mm difference)
- **Why**: I trusted a single CSV field without cross-referencing the Mac coordination report
- **Fix**: Now using frozen contract value supported_plenum_y_min_mm = -17.750

### 2. Technical Approach Error  
- **Wrong approach**: Clipped V01/V02 vent boxes to cell footprint (shrinking inlets by 3.250 mm)
- **Why wrong**: This would have changed the 4 inlet geometries that Plan B (OpenFOAM) must consume
- **Correct approach**: Extend the shared plenum backward to Y=-17.750 mm, preserving all four vent boxes
- **Impact on Plan B**: Plan B would have received incorrect inlet dimensions, breaking CFD/CHT validation

### 3. Branch Protocol Error
- Committed to main instead of incident/windows-recovery-20260718-001
- Mac rejected commit 4fbec7b (clipping approach)

## CORRECTION APPLIED (d42630d)

- Producer: supported_plenum_y_min_mm = -17.750 replaces ootprint_y_min in upstream create_block
- All vent boxes preserved at full extent
- 8/8 negative tests PASS (including explicit clipping-approach rejection test)
- E2E collaboration report: COLLAB_E2E=PASS
- Plenum extends to support V01/V02 at Y=-17.750 mm
- Expected bbox: [-10.875, -17.750, 1.2675]--[10.875, 20.750, 2.800] mm

## CFD STATUS
- CFD Run completed successfully: v03_cfd_result_retry.dat.h5 (86.5 MB), v03_cfd_setup_retry.cas.h5 (84.1 MB)
- Run used OLD mesh (pre-correction); new mesh required after Mac reviews correction

## NEXT FOR PLAN B / MAC
- Review incident branch d42630d
- If approved: Plan B can consume corrected plenum Y-min = -17.750
- Windows A awaits Mac authorization to run official MCP SpaceClaim producer