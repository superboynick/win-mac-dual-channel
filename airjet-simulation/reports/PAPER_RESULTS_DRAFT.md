# Results — Draft

## Mesh Quality and Reproducibility
The C7 mesh pipeline produced 25 consecutive identical volume meshes (34,883 poly-hexcore
cells, minimum orthogonal quality 0.53, file size 8.2 MB ± 0.001 MB). The watertight
workflow consistently identified one fluid region and eleven dead/void regions
corresponding to the 12 actuator-gap cavities. One external baffle (zone 323) was
observed in every run. A coarse mesh variant (surface sizing 0.10-1.0 mm) produced
a 2.8 MB mesh, confirming sizing-dependent cell count variation.

## Solver Validation
The mesh was successfully loaded into ANSYS Fluent solver mode (241,073 nodes,
237,689 faces, 34,883 cells). Hybrid initialization completed and 50 iterations
of the k-ω SST turbulence model converged with k approaching 0.73 and ω
converging to machine zero. Boundary condition assignment is pending on the
identified face zone (ID 329).

## Mesh Independence
Two refinement levels tested: coarse (0.10/1.0 mm) and medium (0.05/0.75 mm).
Fine level (0.03/0.50 mm) pending due to Student license launch-rate limitation.
