# AJM Task 006 — Inventory & Profile/Hash Preflight Report
**UTC**: 2026-07-20T08:40:00Z
**Task**: ajm-windows-rear-inlet-runtime-and-consumer-gates-20260718-006
**Branch**: main (5c71578)

## INVENTORY_STATUS=HASH_MISMATCH_BLOCKING

### Profile Check
| Field | Value |
|-------|-------|
| profile_id | ajm006-spaceclaim-v03-continuous-throat-pilot-v1 |
| engine | spaceclaim |
| script | 006/v03_continuous_fluid_producer.py |
| PROFILE SHA256 | 8f23d7d7dd66efcf06909341a45a76caccd6732cbf11fa1f54157699d55228b0 |
| ACTUAL SHA256 | a6a1e91024030a14cc90a13eeaff31c4312311d0c8246fc8af60d7da61943b9f |
| MATCH | **NO** — v2 plenum-extension fix not yet reflected in profile |

### Root Cause
The v2 correction (extend plenum to Y=-17.750, remove clipping) was pushed to
incident/windows-recovery-20260718-001 (commit d42630d) but profiles.json on main
still pins the old hash. Mac has not yet reviewed and merged the correction.

### Corrected v2 Producer (incident branch d42630d)
- supported_plenum_y_min_mm = -17.750 replaces footprint_y_min in upstream create_block
- All 4 inlet vent boxes preserved (no clipping)
- 8/8 negative tests PASS
- Expected bbox: [-10.875, -17.750, 1.2675]--[10.875, 20.750, 2.800] mm
- Analytic volume: 469.4396438426395 mm3

### ANSYS Toolchain Status
| Tool | Status |
|------|--------|
| SpaceClaim.exe | INSTALLED (V261 API) |
| PyFluent | 0.40.2 (venv OK) |
| MCP airjet-ansys | NOT_CONNECTED |
| Fluent student license | UNSTABLE (PyFluent mode intermittent) |

### CFD Status
- Previous CFD run SUCCESS: v03_cfd_result_retry.dat.h5 (86.5 MB) on old mesh
- New mesh requires corrected CAD (blocked by hash mismatch)

### Blocker
- profiles.json sha256 must be updated from 8f23d7... to a6a1e9... after Mac review
- Or Mac merges incident branch into main with hash update

### Next Action
- Await Mac review of incident branch d42630d
- After merge: update profiles.json hash, run SpaceClaim producer
- Then: validate native/STEP reopen (4 inlet/1 outlet, bbox check)

### P1-P6 Gate Status
- P1-P6: NOT_RUN (task 006 blocked by hash mismatch)