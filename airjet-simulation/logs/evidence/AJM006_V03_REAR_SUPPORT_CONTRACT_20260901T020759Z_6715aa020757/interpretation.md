# AJM006 V03 rear-support contract retry

## Suite result

- Suite: `AJM006_V03_TWO_STAGE_CONTINUOUS_MESH_SUITE`
- Signed Git head: `fc7256c23d4e9d0727d46a2c3b1ace8bde0c0946`
- Terminal result: `FAIL_PRELIMINARY_V03_TWO_STAGE_MESH_SUITE`
- Visibility: `NOT_USER_OBSERVED`
- Gate effect: no C7 mesh evidence was created; formal 006 and P1--P6 remain `NOT_RUN`/`NOT_PASSED`.

## Producer job

SpaceClaim job `AJM006-V03-CONTINUOUS-22885f73ae65` reached `PROCESS_EXITED_0` and its declared
report returned `PASS_PARTIAL_CAD_CAPABILITY`. The hash-bound rear-support geometry retained one
closed/manifold continuous fluid body, 972 finite throats, native and STEP reopen closure, the
`3.250 mm` rear extension to `Y=-17.750 mm`, and volume `469.43964384263649 mm3`. The native body
has 1076 faces. This is preliminary geometry-runtime evidence only, not formal 006 or P1 PASS.

## Consumer job

PyFluent-profile job `AJM006-V03-CONTINUOUS-6715aa020757` reached `FAILED_PROCESS` with exit code 2
after 2.64 seconds. The declared report records `PREDECESSOR_NATIVE_EVIDENCE_INVALID`. The approved
consumer at this signed commit still required the pre-extension 1078-face fingerprint, while the
accepted rear-support producer emitted the measured 1076-face body. The consumer stopped inside
`validate_predecessor()` before Fluent launch; every mesh assertion remained false, no mesh was
written, and `solver_mode=NOT_ENTERED`.

## Disposition

The accepted correction changes the exact source contract to 1076 faces, including 74 remaining
unclassified continuous walls instead of 76, while retaining 4 inlets, 1 outlet, 1 heat wall,
12 membrane-top faces, 12 membrane-bottom faces and 972 throat walls. The consumer, runner,
profile SHA lock, tests, task card and MCP policy audit are updated together. A clean hash-pinned
retry is required; this failed run cannot be promoted to mesh capability or any P1--P6 Gate.

Raw native CAD, STEP, reopen inventories and process logs remain under the two external job
directories recorded by `producer-job.json`, `consumer-job.json` and their artifact manifests.
The canonical repository `logs/external-files.csv` intentionally remains header-only until the
formal 006 manifest workflow, as required by the current project audit.
