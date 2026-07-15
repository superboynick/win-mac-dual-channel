# AJM-006 V03 two-stage runtime interpretation

Commit `9352bd14de81ae048a7c68f2e0a4af456a24b7dc` produced a valid preliminary geometry Stage 1 and a Stage 2 launch-boundary failure.

The SpaceClaim producer exited 0 and its report records `PASS_PARTIAL_CAD_CAPABILITY`. The frozen candidate remained one continuous, closed, manifold fluid body and preserved 972 finite throats through build, native reopen, and STEP reopen. This is preliminary candidate-geometry evidence only; it is not formal 006 or P1 completion, and 972 throats, 0.25 mm diameter, and 0.10 mm effective throat length remain candidate inputs rather than measured Mini product facts.

The PyFluent consumer verified the predecessor identity, copied the exact 16,619,010-byte STEP with matching SHA-256, and constructed 4 inlet, 1 outlet, and 972 throat query points. Its final durable checkpoint was `fluent_launch_started`; `fluent_launch_completed` was never observed. The process was externally terminated after the synchronous launch call did not return. No consumer report, watertight import, surface mesh, volume mesh, `.msh.h5`, solver physics, or Gate result was reached.

This preserved attempt does not identify the lower-level launch cause. Later diagnostic commits are separate experiments and must not be retroactively attributed to this run. The correct gate state is `P1-P6=NOT_RUN`.

The preserved text copies in this Git directory use LF line endings. `evidence-summary.json` therefore records both the source Windows byte SHA/size and the LF-normalized repository-copy SHA/size; the two identities must not be substituted for one another.
