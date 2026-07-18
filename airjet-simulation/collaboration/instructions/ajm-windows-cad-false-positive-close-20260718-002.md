# Close false-positive CAD overhang incident without changing geometry

The Mac review rejects the proposed CAD trim. Do not modify or rerun SpaceClaim,
Workbench, Fluent, Mechanical, or OpenFOAM for this task.

The reported `Y=[-17.75, 20.75] mm` asymmetry is an explicit frozen product-flow
contract, not evidence of an accidental housing overhang. Repository evidence includes:

- `EVIDENCE_CHAIN_COMPLETE.md`: exact contract bounds and explanation of asymmetric
  inlet/outlet offset;
- `AIRJET_SIMULATION_REPRODUCTION_GUIDE.md`: cell footprint ends at `+17.75 mm`, while
  the outlet manifold intentionally reaches `+20.75 mm`;
- `parameters/p1_planform_exhaust_candidates.csv`: outlet collection/manifold ends at
  `+20.75 mm` and is explicitly described as a single-side outlet candidate;
- `automation/ansys/run_v03_continuous_fluid_006.py` and its tests: the same min/max
  values are pinned;
- `automation/ansys/contracts/c7_hdf5_boundary_semantic_gate.py`: the same bounds are
  an acceptance condition.

Therefore trimming the positive-Y outlet rectangles to a symmetric cell footprint
would delete the intended outlet flow path and invalidate the frozen candidate.

Read those sources directly. Update
`airjet-simulation/reports/AJM_WINDOWS_INCIDENT_RECOVERY_2026-07-18.md` on branch
`incident/windows-recovery-20260718-001` with:

- `INCIDENT_STATE=RESOLVED_FALSE_POSITIVE`
- `CAD_TRIM_EXECUTED=NO`
- the distinction between cell/housing footprint and complete fluid-domain/outlet
  manifold envelope;
- exact current UTC time rather than the stale `11:10Z` timestamp;
- confirmation that destructive actions, solver actions, and Gate changes are NONE;
- A's actual remaining blocker: official-MCP C7 retry after synchronization, not CAD
  trimming.

Before committing, inspect the relevant source lines and run the V03 producer guards,
C7 semantic gate tests, ANSYS MCP policy test and project audit. Commit with the trusted
Windows key and push the same incident branch. Do not push `main`.

If there is a different visible geometric anomaly beyond the intentional manifold,
do not infer from bbox. Preserve a screenshot or neutral-format observation outside
Git, record its SHA256 and exact body/face coordinates, and keep the incident OPEN with
that discriminating evidence. Otherwise close the false positive within 20 minutes.

After the corrected report is pushed, A owns the reviewed C7 retry; B remains isolated
on OpenFOAM. P1-P6 remain NOT_RUN/NOT_PASSED.
