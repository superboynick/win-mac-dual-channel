# AJM006 V03 C7 contained-bridge Stage 1 and WTM diagnostic

- Git commit used: `2b76d50f76fc166eb0a9420644f02578b4c5f854`
- SpaceClaim job: `AJM006-V03-CONTINUOUS-86b658998972`
- Producer status: `PASS_PARTIAL_CAD_CAPABILITY`
- Producer pilot: `PASS_PRELIMINARY_V03_FINITE_THROAT_GEOMETRY`
- Stage 1 process: `PROCESS_EXITED_0`
- Raw STEP SHA256: `e66c14ab908ab031996da9dc54a5d2b6c0b783f9697814c7de089a4190f1e206`
- Raw STEP bytes: `1809448`
- Raw producer-report SHA256: `4ac8c4a7679c1b18d563c3a44b660f22a8bae392eea6005d02bc722906d35d62`

Stage 1 preserved one closed/manifold body, all 972 finite throats, and native
and STEP membrane top/bottom counts of 12/12. Native volume was
451.77881884263655 mm3 (analytic delta about 3e-12 mm3); STEP volume was
451.77324837529756 mm3 (analytic delta 0.0055704673419540995 mm3). Native X
bounds differed from +/-10.875 mm by at most 0.000025 mm.

One authorized WTM diagnostic used this exact STEP. Fluent reported one
region plus eleven voids, retained one cell zone named
`ajm006_v03_fluid_continuous`, and generated 34,883 cells with minimum
orthogonal quality 0.52909493. The mesh has SHA256
`9ecc0b2883e91a3fc1cd850edd825fdad3de19f880214e4493c61559891e7ce0` and
8,209,258 bytes. The first bbox check incorrectly included unused CAD and
curvature node zones. A corrected HDF5 gate followed final face connectivity
to the nodes actually used by the cell zone and found 202,480 used-node
references with bounds `X=[-10.75,-3.75]`, `Y=[-14.375,-7.375]`,
`Z=[1.6575,1.9325] mm`. Those bounds identify one actuator-gap tile, not the
frozen full-product main-flow domain. The final HDF5 also contains only one
interior and one generic wall face zone. Therefore the WTM result is
`REGION_SELECTION_FAIL_ACTUATOR_GAP` and `BOUNDARY_SEMANTICS_COLLAPSED`.

Only the preliminary Stage 1 geometry passed. The WTM route failed. No solver,
physics, calibration, formal 006 completion, or P1-P6 Gate was run or passed.
