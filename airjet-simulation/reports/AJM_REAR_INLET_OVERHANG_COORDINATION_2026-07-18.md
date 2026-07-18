# AJM rear inlet overhang coordination — 2026-07-18

## Confirmed defect

The selected `M-3x4-7.0__R50_BALANCED` producer uses
`VENT_FLOW_BBOX_R0`. The frozen cell-footprint rear boundary from
`p1_planform_exhaust_candidates.csv` is `Y=-14.500 mm`; `Y=-14.375 mm` is only
the array boundary and must not be substituted for it. Inlet risers V01 and V02
reach `Y=-17.750 mm`, so each lacks `3.250 mm` of supporting shared plenum in the
original producer. V03 and V04 remain inside the cell footprint. The original
producer directly united all four raw vent boxes without a per-inlet support Gate.

This is a local solid-construction defect. It is not downward penetration, an outlet
extension, a label-only error, or something that can be accepted from the final global
bbox. P1-P6 remain `NOT_RUN/NOT_PASSED`.

## Non-overlapping owners

### Windows A — runtime CAD owner

- Preserve/hash the current native and STEP artifacts.
- Measure V01/V02 against the intended rear plane using reviewed SpaceClaim automation.
- Validate the reviewed correction: preserve all four frozen vent boxes and extend the
  C-class shared plenum rear plane from `Y=-14.500 mm` to `Y=-17.750 mm`; do not
  clip/shorten V01/V02 or manually patch generated native CAD.
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

- Own the static root-cause diff, rear-support contract design, negative acceptance
  tests, peer review, profile/hash closure and linear Git integration.
- Reject bbox-only fixes, deletion/merge of inlet ports, manual `.scdocx` edits and any
  CFD run using the invalid geometry.
- Check Git every 10 minutes; escalate a missed checkpoint immediately with blocker and
  revised ETA.

## Acceptance sequence

1. Preserve current evidence and measure V01/V02 overhang independently.
2. Freeze the cell-footprint plane at `Y=-14.500 mm` and the C-class support extension
   at `3.250 mm`; do not silently promote image-derived vent candidates to product fact.
3. Add producer and pure-contract negative tests before editing CAD generation.
4. Generate CAD through the hash-pinned official ANSYS route.
5. Require native and STEP reopen: four separate inlets, one outlet, V01/V02 fully
   supported by the extended plenum, expected connectivity and no new body/piece defect.
6. Only then resume C7 surface/volume meshing. B consumes only the accepted manifest.

## Current root-cause location

`airjet-simulation/automation/ansys/approved/006/v03_continuous_fluid_producer.py`
builds `vent_boxes` from the raw candidate center/axis/length/width and immediately calls
`create_block(...)` followed by `merge_into(upstream, risers, "VENT_RISERS")`. The
missing control was an explicit per-vent support rule before that union. The reviewed
rule preserves the image-derived vent geometry and extends only the C-class shared
plenum; clipping is rejected because it silently changes the visible inlet candidates.
