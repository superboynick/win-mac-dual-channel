# Discussion — Draft

## Parameter Uncertainty and Hardware Calibration
The current simulation uses predominantly B-class parameters derived from
patent drawings and product literature. The orifice plate thickness (C016,
0.10 mm) and impingement channel height (0.04 mm) exhibit the highest
uncertainty. Physical teardown of the ZOTAC ZBOX PI430AJ will directly
measure these values, upgrading evidence class from B/C to A. This
represents the key calibration path for publication-quality results.

## Student License Limitations
The ANSYS Student 2026 R1 1,048,576 cell/node limit constrains mesh
refinement to ~35K cells at the current sizing. While sufficient for
flow-path topology validation and preliminary solver convergence testing,
boundary-layer-resolved meshes for heat transfer prediction will require an
Academic Research license. The observed boundary-type collapse (all semantic
zones merging into a single generic boundary face zone after volume meshing)
is a known v261 watertight workflow behavior; solver-time type assignment
via face zone adjacency provides a practical workaround.

## Experimental Validation Path
Hardware acquisition of the ZBOX PI430AJ enables model calibration through:
(1) direct dimensional measurement replacing estimated parameters, (2)
thermal imaging comparing simulated vs. measured junction temperatures, and
(3) acoustic measurement validating the synthetic jet frequency against
simulated membrane actuation. These data transform the study from a
simulation-only exercise to a validated methodology.
