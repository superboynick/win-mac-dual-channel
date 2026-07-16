# C7 main-flow mesh boundary-collapse blocker

C7 geometry and main-flow region selection passed in signed result commit
`d0d6d32be81c4af0cba0903e787bcce8b2c57ea7`, but the minimal
`save_mesh4.py` path is not solver-ready.

Independent HDF5 topology inspection found:

- one cell zone: ID 482, name `ajm006_v03_fluid_continuous`, 34,883 cells;
- two face-zone IDs only: 481 and 329;
- zone types: 2 (interior) and 3 (generic boundary/wall);
- the encoded names are
  `interior--ajm006_v03_fluid_continuous` and
  `ajm006_v03_fluid_continuous:329`;
- interior face IDs 1..223217;
- generic boundary face IDs 223218..237689 (14,472 faces).

Therefore the mesh retained the correct full-product volume but collapsed the
four inlets, outlet, heat wall, membrane faces, and throat-wall semantics into
one generic boundary zone. It cannot receive correct solver boundary
conditions and must not be called solver-ready, P1 complete, or P3-ready.

Mac actions:

1. Update status/guide text to record `MAIN_VOLUME_PASS_BOUNDARY_SEMANTICS_FAIL`.
2. Audit the approved
   `v03_pyfluent_watertight_mesh_consumer.py` semantic reconstruction path
   against the new C7 predecessor. Prefer that fail-closed consumer over the
   ad-hoc `save_mesh4.py` route.
3. Dispatch one Windows task that reconstructs and freezes separate inlet,
   outlet, heat-wall, membrane, throat-wall, and remaining-wall zones before
   volume meshing, then verifies the final HDF5 zone inventory.
4. No solver physics until the boundary inventory passes. P1-P6 remain
   `NOT_RUN`.

Do not weaken group counts or accept a single generic boundary as a
limitation.
