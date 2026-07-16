# AJM006 V03 C5 Stage 1 0.15 mm diagnostic

- Task: `ajm-stage1-only`
- Git commit used: `e4261c4228f287cd186e86b04d627573486755d9`
- Job: `AJM006-V03-CONTINUOUS-d837d7bb7f0c`
- Runtime phase: `PROCESS_EXITED_0`
- Producer status: `FAIL_PRELIMINARY_GEOMETRY`
- P1-P6: `NOT_RUN`
- STEP SHA256: `a5921b8291bc756f92d2b2e70b7c9f5343d87efd652ab35cc978697f32b6d5b2`
- STEP bytes: `1815624`
- Producer-report SHA256: `1a09331725193470df3ca44d76721e66b8a7b02997a0681da9de9c6f4d7c6f01`

The 0.15 mm perimeter Boolean-overlap candidate was built and exported as a
single closed, manifold STEP body. All 972 explicit finite throats and the
frozen boundary counts survived native and STEP reopening. This is a failed
diagnostic artifact, not a formal geometry pass: the larger overlap changed
the final body volume by about 0.1016 mm3 and expanded the X/Y bounds by about
0.025 mm relative to the frozen analytic route. Therefore
`single_continuous_fluid_boolean`, `native_reopen_single_body`, and
`round_trip_shape_fidelity` remained false. No mesh, solver, physics, or Gate
was run.
