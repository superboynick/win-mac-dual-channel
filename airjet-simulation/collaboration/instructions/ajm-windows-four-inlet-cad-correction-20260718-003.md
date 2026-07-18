# User-confirmed rear overhang in two of four inlet structures

This task supersedes `ajm-windows-cad-false-positive-close-20260718-002`. The Mac
coordinator retracts the false-positive conclusion. The user personally inspected the
3D geometry and confirmed a real local CAD defect:

- the product has exactly four inlet ports;
- at the tail, on the side opposite the outlet, two inlet 3D structures extend
  backward beyond the intended rear product/housing boundary;
- the defect is backward overhang, not downward penetration;
- the questioned solids are inlet structures, not an outlet-manifold extension.

Overall bbox agreement is insufficient and must not be used to dismiss this local
solid-construction error.

## Ownership and immediate stop

A alone owns the ANSYS CAD correction. B remains OpenFOAM-only and must not consume
this invalid geometry. Do not run CFD, CHT or claim any Gate until corrected CAD reopen
evidence passes. Do not edit the integration checkout or manually patch a generated
`.scdocx` as the canonical fix.

## Required pre-edit evidence

In A's isolated worktree, preserve and hash the current native/STEP artifacts. Through
reviewed SpaceClaim/Discovery automation, identify all four inlet structures and the
actual outlet. For each inlet record stable body/face semantics where available,
centroid, bounding box, normal and area. Identify the intended rear boundary plane from
the frozen housing/product construction—not from the erroneous final global bbox—and
measure the signed backward overhang of the two defective inlet structures.

Capture compact screenshots or neutral observations outside Git and record path, size
and SHA256 in the incident report. Determine the exact producer operation that created
the overhang: placement transform, extrusion direction/length, mirror/array operation,
boolean union, or missing intersection/trim. Do not guess from a rendered view alone.

## Reviewed correction

Prepare the smallest source change in the approved A CAD producer or its frozen
contract. Preserve four distinct inlet openings and one outlet while constraining the
two rear inlet structures to the intended rear boundary. Do not delete, merge, relabel,
or symmetrically crop all four inlet structures merely to make the bbox look plausible.

Add fail-closed tests that reject:

- either rear inlet structure crossing the intended rear boundary beyond tolerance;
- four-to-one inlet collapse;
- inlet/outlet role reversal;
- bbox-only acceptance without per-inlet containment;
- loss of four inlet openings after native reopen or STEP reopen.

Run producer guards, relevant geometry-contract tests, ANSYS MCP policy and project
audit. Then push the reviewed source proposal on the incident branch for Mac review.
A formal ANSYS rerun requires a clean signed synchronized commit and official MCP. Stop
before Fluent if CAD reopen evidence is not exact four-inlet/one-outlet and rear-contained.

## Report and timing

Update `airjet-simulation/reports/AJM_WINDOWS_INCIDENT_RECOVERY_2026-07-18.md` on
`incident/windows-recovery-20260718-001` with:

- `INCIDENT_STATE=OPEN_CONFIRMED_REAR_INLET_OVERHANG`;
- `USER_CONFIRMED_FOUR_INLETS=YES`;
- `DEFECT_DIRECTION=BACKWARD_NOT_DOWNWARD`;
- measured rear boundary and both signed overhangs;
- evidence hashes, root cause, exact proposed files, tests, owner and revised ETA;
- destructive actions and solver actions, which must remain `NONE` during diagnosis.

Commit with the trusted Windows key and push the incident branch. Deliver measured
diagnosis within 20 minutes and a reviewed source/test proposal within 60 minutes. If
measurement or API access blocks progress, report the exact blocker immediately and
switch A to source/static diagnosis rather than retrying solvers.

P1-P6 remain NOT_RUN/NOT_PASSED.
