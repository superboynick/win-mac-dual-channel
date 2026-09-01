# AJM-006 V03 C7 local-sizing checkpoint

This package preserves the audited retry from Git head
`f90019ab87fb1a160438ea420d3cf79bf5ae32f6`. Producer
`AJM006-V03-CONTINUOUS-8734ce0a510d` exited 0; consumer
`AJM006-V03-CONTINUOUS-412cf4f0633b` exited 2 with
`LOCAL_SIZING_LAST_CHILD_NOT_CREATED`.

The run passed predecessor identity, Fluent launch, 1076-face import, four inlet queries, one
outlet query, 972 throat hits, and normal reversal. It stopped while creating the already-approved
0.075 mm local sizing child, before surface mesh and before the newly corrected Update Regions
callable-argument route. Therefore this run neither validates nor invalidates that route.

This failure is not evidence of a Student cell/node limit, insufficient RAM, volume-mesh quality,
solver entry, or product performance. C7, formal 006, and P1-P6 remain unaccepted. No automatic
repeat was launched because the first failed assertion is preserved for reproducibility review.

