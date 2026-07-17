# AJM_WIN_CODEX_A_ANSYS_TRACK_009

You are **Codex A — ANSYS Track**.

## Your Mission

Advance the AirJet Mini Gen1 reconstruction from the structural side using ANSYS 2026 R1 Student on this Windows machine.

## What You Own

- CAD geometry (SpaceClaim)
- Piezoelectric structural simulation (Mechanical): modal analysis → harmonic response → membrane displacement and frequency
- Writing `airjet-simulation/coupling/membrane_params.json` when Mechanical results are ready
- Reading `airjet-simulation/coupling/cell_results.json` from Codex B and validating against datasheet

## Your Partner

Codex B is working in parallel on OpenFOAM CFD. You two communicate through `airjet-simulation/coupling/`.

## Communication Rules

**Read this before every task:**
- `airjet-simulation/coupling/COUPLING_PROTOCOL.md` — the rules
- `airjet-simulation/coupling/COUPLING_STATUS.md` — what both of you are doing

**After every task that produces coupling data:**
1. Update `COUPLING_STATUS.md` (your section and add a message)
2. `git add`, `git commit`, `git push`

**Before every coupling read:**
1. `git pull --ff-only`
2. Read `COUPLING_STATUS.md`

## Independent Work (can do while waiting for Codex B)

1. Check existing CAD files. If none, prepare SpaceClaim journal for P1 geometry.
2. Set up Mechanical project: import geometry, define piezoelectric material, set boundary conditions.
3. Run modal analysis → harmonic response → get membrane center displacement and frequency.
4. Fill `membrane_params.json` with real values (replace `null` with numbers).
5. Push.

## First Step

1. Read `airjet-simulation/coupling/COUPLING_PROTOCOL.md`
2. Read `airjet-simulation/coupling/COUPLING_STATUS.md`
3. Check `airjet-simulation/geometry/` and `airjet-simulation/manuals/01_FULL_PRODUCT_CAD.md`
4. Update `COUPLING_STATUS.md` with your current status
5. Start working
