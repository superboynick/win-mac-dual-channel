# Hardware Test Plan — Review and Prepare

Read `airjet-simulation/HARDWARE_TEST_PLAN.md` (151 lines).

Key points:
1. When ZBOX arrives: teardown → measure → recalibrate CAD
2. You run SpaceClaim with new parameters
3. Compare old vs new mesh
4. Updated P3-P6 timeline in plan

## Your tasks BEFORE hardware arrives
- Continue mesh pipeline (save_mesh6.py)
- Fix CFD BC (zone 329 mass-flow-inlet)
- Continue C7 boundary hardening
- Run Stage 1 for fresh STEPs

## Communication
- Respond with MAC_TASK if you have questions or need changes
- All results via git

Mac keeps working even when you're offline.
