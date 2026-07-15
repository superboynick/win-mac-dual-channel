# AJM-006 V03 high-resolution mesh attempt interpretation

Commit `ca62c01bd0727f2a4ab1ab6357c9904d8fcc6715` completed the frozen V03 preliminary geometry producer and then reached real PyFluent meshing work. Stage 1 remained a preliminary geometry pass: the candidate exported and reopened as one CAD body with the frozen 972 finite-throat inventory. That is not formal 006 or P1 completion.

Stage 2 imported the exact predecessor STEP, reconstructed four inlet zones, one outlet zone and 972 throat query hits, applied 0.05 mm local throat sizing, created the surface mesh, and verified that zones 4/9/18/24 became `velocity-inlet` while zone 32 became `pressure-outlet`. These are durable report/trace observations.

Fluent's internal transcript then reported completion of a poly-hexcore volume-mesh operation with 1,580,277 cells, 12 cell zones, and minimum orthogonal quality 0.23064141. This is internal telemetry, not an accepted mesh artifact. The cell count exceeded the Student 1,000,000 limit by 580,277 cells, or 58.0277%. The 12-zone observation also did not satisfy the one-common-fluid-zone contract.

The license error was raised from the volume-mesh API call before the script could query its postconditions. Therefore `volume_mesh`, `one_fluid_cell_zone`, throat occupancy, integrity, Student-limit and file-hash assertions remained false. No `.msh.h5`, mesh inventory, verification file or source-chain file was written. This run is `FAIL_PRELIMINARY_MESH_CAPABILITY`, while P1-P6 remain `NOT_RUN`.

The next run uses a separately committed Student-coarse topology candidate. It may establish a saveable diagnostic mesh, but it must not hide multiple fluid zones or promote a coarse topology diagnostic into a resolution-converged result.

The text copies in this directory use LF line endings. `evidence-summary.json` preserves both the Windows raw SHA/size and the LF-normalized repository-copy SHA/size where relevant.
