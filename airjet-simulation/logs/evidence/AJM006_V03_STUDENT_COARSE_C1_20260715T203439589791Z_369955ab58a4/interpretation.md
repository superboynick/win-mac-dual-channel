# AJM-006 V03 Student-coarse C1 interpretation

C1 achieved its first purpose: the same complete 12-cell/972-throat candidate completed the PyFluent volume-mesh API with 413,405 cells and minimum orthogonal quality 0.24604596. The cell count was below the one-million threshold and no license error was observed; the node-count and complete Student guard were not reached.

It then failed the unchanged single-common-fluid-zone contract. Fluent reported 12 cell zones with roughly 34,000 cells each. More importantly, the surface stage explicitly described one fluid/solid region and eleven voids. The existing workflow subsequently treated all 12 as fluid. This proves a region-classification problem, but it does not yet prove that the main flow geometry is disconnected: the eleven actuator exclusion pockets may need to remain dead/void. The 12 zones must not be merged or renamed to manufacture a pass.

The script stopped before the Student node-count, 972 throat-axis common-zone occupancy, full integrity checks and durable mesh write. No `.msh.h5` was created. Therefore C1 is a useful topology diagnosis, not a mesh deliverable or P1 result.

The next diagnostic must capture the complete `update_regions` name/type state before execution without mutating it. If the eleven pockets are confirmed as dead/void, the workflow must retain only the one live flow region for transfer. CAD overlap may be changed only if that state capture and a fail-closed rerun still demonstrate real flow disconnection.

Text files in this directory use LF line endings. The summary preserves Windows raw and normalized repository identities separately.
