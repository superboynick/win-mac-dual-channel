# Stage routing and gates

## P0 Evidence freeze

Input: official sheets, patent families, tutorial, numerical literature.
Output: source index, parameter registry, uncertainty list, product selection.
Gate: every active input has source class and no unresolved unit ambiguity.

## P1 Full-product CAD

Input: frozen envelope, layout constraints, flow-path evidence.
Output: whole assembly, Layout L/M/S configurations, complete fluid volumes.
Gate: 27.5 x 41.5 x 2.8 mm envelope; inlet-to-outlet connectivity; all cells represented; no collisions or blind orifices.

## P2 Actuator structure

Input: one cell extracted from the selected full layout.
Output: modes, harmonic response, displacement field, stress, cell power.
Gate: frequency, mode shape, displacement, clearance, stress, and total 1 W budget are jointly feasible.

## P3 Cell transient CFD

Input: P2 displacement field and P1 chambers/orifices.
Output: pressure-flow-displacement map, backflow ratio, jet velocity, reduced interface.
Gate: dynamic mesh, time step, grid, periodic stability, and mass balance pass.

## P4 Full-product airflow

Input: full fluid volume and P3 interfaces.
Output: all-cell flow distribution, pressure, phase response, 1750 Pa behavior.
Gate: complete no-symmetry case, mass balance, cell starvation analysis, pressure/acoustic proxy rationale.

## P5 Full-product CHT

Input: P4 flow, chip/TIM/spreader, separate self-heat.
Output: complete temperature/heat-flow field and 85 C/25 C comparison.
Gate: <1% energy error, 4.25 W net and 5.25 W total definitions consistent, fixed-temperature and fixed-power checks agree.

## P6 Calibration and uncertainty

Input: all observables and adjustable `C` parameters.
Output: primary/alternate parameter sets, validation residuals, confidence/feasible envelope.
Gate: multi-layer training metrics, held-out validation, no hidden hard-constraint violation.

## Fallback rule

If a gate fails, return to the nearest upstream source of the failure. Do not compensate a structural failure with a thermal parameter or an airflow failure with an arbitrary heat-transfer coefficient.
