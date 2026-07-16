# Review the C5 0.15 mm Stage 1 diagnostic

Windows completed the signed `ajm-stage1-only` task and pushed result commit
`e8a98e0b00097988b7268cb8f83a3094cde6de22`. A separate Windows-signed commit
`b1caada` subsequently ran WTM outside the Stage-1-only envelope. Treat that
mesh as diagnostic evidence, not as a passing formal predecessor.

Authoritative evidence:

- job: `AJM006-V03-CONTINUOUS-d837d7bb7f0c`
- runtime phase: `PROCESS_EXITED_0`
- producer status: `FAIL_PRELIMINARY_GEOMETRY`
- evidence path:
  `airjet-simulation/logs/evidence/AJM006_V03_C5_STAGE1_015MM_20260716T114130Z_d837d7bb7f0c`
- raw runtime STEP SHA256:
  `a5921b8291bc756f92d2b2e70b7c9f5343d87efd652ab35cc978697f32b6d5b2`

The candidate remained one closed/manifold body and retained all 972 throats
and boundary counts. It did not preserve the frozen geometry:

- native volume: `451.88041884263652 mm3`
- frozen route analytic volume: `451.77881884263951 mm3`
- native delta: `0.10159999999700631 mm3` (tolerance `0.08`)
- STEP volume: `451.87486218775109 mm3`
- STEP delta: `0.096043345111581857 mm3` (tolerance `0.03`)
- frozen X bounds: `[-10.875, 10.875] mm`
- observed X bounds: `[-10.9, 10.9] mm`
- frozen Y minimum: `-17.75 mm`
- observed Y minimum: `-17.750025 mm`

The later WTM diagnostic created one cell zone with 39,062 cells and minimum
orthogonal quality 0.49 after reporting one region plus eleven voids. An
independent read of the committed HDF5 node-coordinate dataset found 45,465
nodes with mesh bounds `X=[-10.8999996,10.8999996]`,
`Y=[-17.75,20.75]`, `Z=[1.26750004,2.79999995] mm`. These bounds prove that
the retained zone is the full-product main-flow body rather than one of the
13.475 mm3 actuator-gap cavities. Thus the 0.15 mm candidate fixed WTM region
selection, but did so while changing the frozen geometric set.

Required Mac work:

1. Correct `AIRJET_SIMULATION_REPRODUCTION_GUIDE.md` and downstream paper
   material so the 39,062-cell mesh is labelled a diagnostic main-flow mesh,
   not a formal geometry, P1, or solver result. Preserve the directly observed
   one-region/eleven-void transcript and HDF5 bbox evidence.
2. Treat the existing 0.15 mm route-contract statement that the overlap is
   fully contained and has zero union-volume effect as disproven evidence.
3. Design the next geometry correction so the Boolean robustness feature is
   contained inside the frozen final fluid set, or explicitly propose and
   justify a new analytic/bbox contract. Do not merely widen tolerances.
4. Do not issue a formal Stage 2 authorization until a new Stage 1 predecessor
   passes the one-body, closed/manifold, volume, bbox, 972-throat, and boundary
   gates. The already committed WTM run remains diagnostic-only.

P1-P6 remain `NOT_RUN`. No solver or physics was run.
