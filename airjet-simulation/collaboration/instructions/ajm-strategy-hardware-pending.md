# Strategy: continue simulation, hardware supplement later

ZOTAC ZBOX PI430AJ purchased (open-box, 10% off). Will ship to Pomona, CA.
Estimated arrival: 1-2 weeks.

## Strategy Decision
- **BEFORE hardware arrives:** continue current simulation plan unchanged
  - Mesh pipeline (save_mesh6.py) → keep producing
  - CFD solve (solve_cfd6.py) → iterate on BCs, get meaningful results
  - Paper writing → use CURRENT parameters (B/C evidence class)
- **AFTER hardware arrives:** supplement paper with:
  - Teardown photos + measurements → upgrade parameters to A-class
  - Thermal imaging → simulation vs experiment comparison
  - Paper upgrade from "pure sim" to "sim+experiment"

## Current priorities
1. Keep mesh pipeline running continuously
2. Get CFD solve with proper boundary conditions (mass-flow-inlet on zone 329)
3. Continue Stage 1 (SpaceClaim) to produce new STEPs
4. All results committed and pushed

## Paper status
- V2 structure with hardware section ready: airjet-simulation/reports/PAPER_STRUCTURE_V2_WITH_HARDWARE.md
- Method section drafted
- Will expand with experimental results after teardown

P1-P6 unchanged. Continue.
