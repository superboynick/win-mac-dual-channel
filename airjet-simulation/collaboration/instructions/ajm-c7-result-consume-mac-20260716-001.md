# Consume C7 Stage 1 and WTM diagnostic result

Windows completed C7 and pushed signed result commit
`d0d6d32be81c4af0cba0903e787bcce8b2c57ea7`.

Verified result:

- SpaceClaim job `AJM006-V03-CONTINUOUS-86b658998972`;
- producer `PASS_PARTIAL_CAD_CAPABILITY` with all 17 assertions true;
- one closed/manifold body, 972 throats, membrane top/bottom 12/12;
- native volume `451.77881884263655 mm3`, analytic delta about `3e-12`;
- STEP volume `451.77324837529756 mm3`, analytic delta
  `0.0055704673419540995`;
- native X bound deviation at most `0.000025 mm`;
- WTM: one retained `ajm006_v03_fluid_continuous` cell zone,
  34,883 cells, minimum orthogonal quality `0.52909493`;
- mesh SHA256
  `9ecc0b2883e91a3fc1cd850edd825fdad3de19f880214e4493c61559891e7ce0`;
- independent HDF5 bounds `X=[-10.875,10.875]`,
  `Y=[-17.75,20.75]`, `Z=[1.26750004,2.79999995] mm`.

Authoritative interpretation:
`airjet-simulation/logs/evidence/AJM006_V03_C7_BRIDGE_STAGE1_20260716_86b658998972/interpretation.md`.

Mac actions:

1. Verify the signed evidence and correct status/guide/paper text to identify C7
   as the successful contained-bridge geometry and preliminary main-flow mesh.
2. Preserve the claim ceiling: formal 006, solver, physics, calibration, and
   P1-P6 remain NOT_RUN until their own gates execute.
3. Dispatch the smallest audited Windows next task for solver-mode mesh read,
   mesh check, cell-zone/boundary inventory, and process cleanup. Do not add
   flow/thermal physics until that check passes.
4. Keep AirJet Mini Gen1 as the sole target.
