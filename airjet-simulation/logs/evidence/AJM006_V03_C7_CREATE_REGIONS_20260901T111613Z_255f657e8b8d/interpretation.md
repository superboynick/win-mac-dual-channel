# AJM006 V03 C7 Create Regions retry

## Suite result

- Suite: `AJM006_V03_TWO_STAGE_CONTINUOUS_MESH_SUITE`
- Signed Git head: `8ffed0360ac383b1d7e8a8abb2f6d17a0f3a3416`
- Terminal result: `FAIL_PRELIMINARY_V03_TWO_STAGE_MESH_SUITE`
- Visibility: `NOT_USER_OBSERVED`
- Gate effect: no volume mesh was created; formal 006 and P1--P6 remain `NOT_RUN`/`NOT_PASSED`.

## Producer job

SpaceClaim job `AJM006-V03-CONTINUOUS-70ec3b99d924` reached `PROCESS_EXITED_0` and its declared
report returned `PASS_PARTIAL_CAD_CAPABILITY`. It reconfirmed the hash-bound, rear-supported,
single closed/manifold continuous fluid body, 972 finite throats, native and STEP reopen closure,
1076 faces and volume `469.43964384263649 mm3`. This is preliminary geometry evidence only.

## Consumer job

PyFluent job `AJM006-V03-CONTINUOUS-255f657e8b8d` accepted the signed 1076-face predecessor and
launched Fluent 2026 R1. It imported all 1076 face zones, reconstructed four inlets, one outlet and
all 972 throat hits, applied the `0.075 mm` throat sizing contract, and completed the surface mesh
in about 1.26 minutes with maximum skewness `0.56680436`. The surface workflow reported one target
fluid/solid region and twelve non-flow voids.

The consumer then failed inside `workflow.create_regions()` with
`Topology region with name dead0 already exists`. Volume meshing, Student cell/node guards, mesh
integrity, mesh write/hash and all physics were not reached. `solver_mode=NOT_ENTERED` and zero
solver iterations were preserved.

## Root cause and reviewed fix

The prior face-angle split removed the older region-split side effect, but the v261 Create Regions
task still used its default `retain_dead_region_name=false`. With twelve distinct actuator-gap
voids, Fluent attempted a colliding `dead0` topology name. The approved consumer now pins
`workflow.create_regions.retain_dead_region_name = True` and fail-closes if the pre-execution
argument state does not confirm that value. The official v261 generated API documents this option
as retaining an original-region suffix on dead-region names.

The revised consumer SHA-256 is
`f7e530ddf59642d1a70bcbdb002d70921a6ac54bc760eb9b9fb8014f9a5fa021`. Its runner/profile locks,
51 workflow tests, 19 semantic-contract tests, MCP static policy (`profiles=20 tools=5`) and the
project audit pass together. A new clean, hash-pinned run is required; this failed run cannot be
promoted to C7, formal 006 or any P1--P6 Gate.

Raw native CAD, STEP, reopen inventories and full process trees remain under the external producer
and consumer directories recorded by the job files and artifact manifests. The compact repository
copy preserves the declared reports, exact console streams, diagnostic trace, suite summary and
manifest hashes without claiming a mesh artifact that does not exist.
