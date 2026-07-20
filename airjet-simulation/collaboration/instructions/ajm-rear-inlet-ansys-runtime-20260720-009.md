# Rear-inlet official ANSYS runtime acceptance

TASK_ID=`ajm-rear-inlet-ansys-runtime-20260720-009`

Windows A owns this task exclusively. Track B is integrated and read-only. Start from clean,
synchronized `main` at this signed tip, create a separate signed A branch, publish the
required task card and file lease, and do not push `main`.

1. Use the installed `airjet-ansys-automation` skill and the official `airjet-ansys` MCP.
   Inventory must confirm the exact Student 2026 R1 root, approved profile, clean Git state
   and producer/profile SHA
   `8f23d7d7dd66efcf06909341a45a76caccd6732cbf11fa1f54157699d55228b0`.
2. Reject immediately if producer source contains `vent_rear_containment_clip` or
   `box[1] = footprint_y_min`. Do not use incident `d42630d` and do not update the profile.
3. Submit exactly the reviewed profile
   `ajm006-spaceclaim-v03-continuous-throat-pilot-v1`. Poll to terminal and collect the
   declared report and artifact manifest. Dependency manifests and native/STEP artifacts
   must remain job-local or under the registered Git-external evidence root; nothing may be
   generated below the repository source tree.
4. Accept only literal runtime evidence for: 4 inlets, 1 outlet; preserved V01/V02 boxes;
   cell-footprint Y-min `-14.500 mm`; supported plenum Y-min `-17.750 mm`; extension
   `3.250 mm`; one closed/manifold body and piece; bbox
   `[-10.875,-17.750,1.2675]--[10.875,20.750,2.800] mm`; analytic/native/STEP volume
   `469.4396438426395 mm3` within route tolerances; native reopen, STEP reopen and expected
   connectivity.
5. Stop on the first failed assertion and report its exact code, job ID and artifact path.
   Do not start Fluent, mesh, physics or reuse the old mesh.
6. Condense only small audited evidence, update run/external indexes and reality log on the A
   branch, then push the signed branch for Mac review.

Checkpoints: task card and inventory within 15 minutes; submitted/terminal job state within
45 minutes; evidence branch within 90 minutes. Every slip requires actual versus expected
time, blocker, revised ETA and safe A-only backlog. P1--P6 remain `NOT_RUN/NOT_PASSED`.
