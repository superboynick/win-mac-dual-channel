# Mac peer acceptance — rear-inlet runtime geometry correction

## Decision

`REAR_INLET_GEOMETRY_RUNTIME=ACCEPTED_PASS`

This acceptance is limited to the reviewed full-product V03 CAD route and its native/STEP
reopen evidence. It does **not** promote the formal P1 Gate, mesh, physics, P2, P3, P4, P5
or P6. Those remain `NOT_PASSED`.

## Bound identity

- Job: `ajm-rear-inlet-009-mcp-fbff57daa893`
- Job phase / exit: `PROCESS_EXITED_0` / `0`
- Job start / end: `2026-07-20T09:16:31.922396+00:00` /
  `2026-07-20T09:18:05.142933+00:00`
- Producer source commit: `a8ece4383e0c65c7a33f026203d86807feac6c0c`
- Profile: `ajm006-spaceclaim-v03-continuous-throat-pilot-v1`
- Producer SHA-256:
  `8f23d7d7dd66efcf06909341a45a76caccd6732cbf11fa1f54157699d55228b0`
- Profile contract SHA-256:
  `c525f5d53e8a72100232b4e30a88020ab54305769b5cd6c71629e09b5acf15e0`

## Independent evidence checks

Mac copied and independently parsed the compact JSON artifacts from the registered external
job directory. The job manifest, producer report, source-chain report, native reopen, STEP
reimport and throat inventory hashes were recomputed locally.

| Evidence | Size (bytes) | SHA-256 | Result |
|---|---:|---|---|
| `job.json` | 5,738 | `3661f8c93caeff5a7b591125a7ec7cc5e3b6e154f3b651035e7fff16b910556b` | PASS |
| `v03_continuous_fluid_producer.json` | 16,056 | `6bd4604baa6b9c7631e99ff8a517ce782d3c006de13301c31f9955a12def0c4b` | PASS |
| `v03_source_chain.json` | 1,619 | `1234ec097198a534b90cea5cb159a005bcc0864a2fff2826dfdd4fb4eeed32dc` | PASS |
| `v03_native_reopen.json` | 533,071 | `1335db49566bd3fe124986a6a9013667396ea5fba2dd3434eba2ca39b2f054c1` | PASS |
| `v03_step_reimport.json` | 500,939 | `e8799fe4fe82f56161aa88136c24c15ec87175ad7b21ae41ed7d773f0d51f70c` | PASS |
| `v03_throat_inventory.json` | 1,071,139 | `2f49d27f20e784affb51dd3f26c7fe4058c9e06bac7e1099993302c78c47e9c2` | PASS |
| `product_continuous_fluid.scdocx` | 6,957,892 | `50223b0fd0d70b80ce7d4abd4e267e44fb2c66c1a4ae77f117629953b08cae9e` | PASS by Windows hash plus native reopen |
| `product_continuous_fluid.step` | 1,806,621 | `b1ce3b9016f74663a7fdb686b122f491f9df391a668d86b43c33a5132e477fa4` | PASS by Windows hash plus STEP reimport |

The invalid task-012 embedded future timestamp was rejected. Only `job.json` and filesystem
times above are authoritative.

## Geometry assertions

- Four inlet identities: `V01`, `V02`, `V03`, `V04`; one outlet identity.
- Rear inlet identities: exactly `V01`, `V02`.
- Cell footprint Y-min: `-14.500 mm`.
- Supported shared-plenum Y-min: `-17.750 mm`.
- Rearward support extension: `3.250 mm`; no downward projection or inlet clipping.
- One body, one piece, closed and manifold.
- Native and STEP bbox:
  `[-10.875,-17.750,1.2675]--[10.875,20.750,2.800] mm` within route tolerances.
- Analytic volume: `469.4396438426395 mm3`.
- Native reopen volume: `469.43964384263637 mm3`.
- STEP reimport volume: `469.43964384264342 mm3`.
- All 972 finite throats matched one-to-one in native and STEP evidence.
- Producer source contains neither `vent_rear_containment_clip` nor
  `box[1] = footprint_y_min`.

## Gate boundary

The geometry defect raised by user visual review is closed for this hash-bound CAD route.
Consumer use still requires the machine-readable handoff to pass the OpenFOAM rejection
gate. Formal P1 remains `NOT_PASSED` until the complete P1 stage contract is reviewed;
P2--P6 remain `NOT_PASSED`.
