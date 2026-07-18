# AJM rear inlet overhang coordination — 2026-07-18

## Confirmed defect

The selected `M-3x4-7.0__R50_BALANCED` producer uses
`VENT_FLOW_BBOX_R0`. Its upstream/plenum footprint rear boundary is
`Y=-14.375 mm`, while inlet risers V01 and V02 are constructed down to
`Y=-17.750 mm`. Each therefore extends `3.375 mm` backward beyond the supporting
rear boundary. V03 and V04 remain inside the forward footprint. The producer directly
unions all four raw vent boxes and has no per-inlet containment Gate.

This is a local solid-construction defect. It is not downward penetration, an outlet
extension, a label-only error, or something that can be accepted from the final global
bbox. P1-P6 remain `NOT_RUN/NOT_PASSED`.

## Non-overlapping owners

### Windows A — runtime CAD owner

- Preserve/hash the current native and STEP artifacts.
- Measure V01/V02 against the intended rear plane using reviewed SpaceClaim automation.
- Identify whether the minimum correct source fix is clipping/intersection, corrected
  slot placement/length, or a different frozen vent candidate; do not manually patch
  generated native CAD.
- Implement the approved producer/contract change only after Mac review.
- Prove exact 4 inlet / 1 outlet, rear containment, single closed/manifold body, native
  reopen and STEP reopen before Fluent.
- First measured report ETA: 20 minutes. Source/test proposal ETA: 60 minutes.

### Windows B — OpenFOAM owner

- Do not edit ANSYS producer/contracts or consume the invalid CAD.
- Add an OpenFOAM-side input preflight specification/test fixture that rejects missing
  per-inlet identities, inlet count other than four, outlet count other than one, and a
  declared rear-containment failure.
- Continue T0/source-only backlog; do not install tooling or run AirJet cases without
  separate authorization and corrected hash-bound input.
- Source-only rejection contract ETA: 60 minutes.

### Mac — coordinator and integration owner

- Own the static root-cause diff, rear-containment contract design, negative acceptance
  tests, peer review, profile/hash closure and linear Git integration.
- Reject bbox-only fixes, deletion/merge of inlet ports, manual `.scdocx` edits and any
  CFD run using the invalid geometry.
- Check Git every 10 minutes; escalate a missed checkpoint immediately with blocker and
  revised ETA.

## Acceptance sequence

1. Preserve current evidence and measure V01/V02 overhang independently.
2. Freeze the intended rear plane and correction rule with evidence class and model-form
   uncertainty; do not silently promote image-derived candidates to product fact.
3. Add producer and pure-contract negative tests before editing CAD generation.
4. Generate CAD through the hash-pinned official ANSYS route.
5. Require native and STEP reopen: four separate inlets, one outlet, no rear overhang,
   expected connectivity and no new body/piece defect.
6. Only then resume C7 surface/volume meshing. B consumes only the accepted manifest.

## Current root-cause location

`airjet-simulation/automation/ansys/approved/006/v03_continuous_fluid_producer.py`
builds `vent_boxes` from the raw candidate center/axis/length/width and immediately calls
`create_block(...)` followed by `merge_into(upstream, risers, "VENT_RISERS")`. The
missing control is a per-vent rear-boundary containment or an explicitly reviewed
construction rule before that union.
