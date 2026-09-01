# AJM-006 V03 C7 update-regions checkpoint

## Scope

This package preserves the audited two-stage C7 retry launched from signed Git head
`010cbe627cc94c52fa6650020f77dd1a6884beb6`. It is preliminary capability evidence only.
It does not establish C7, P1-P6, a formal mesh, solver entry, or product performance.

## Observed result

- Producer job `AJM006-V03-CONTINUOUS-a712e60cefcf` exited 0.
- Consumer job `AJM006-V03-CONTINUOUS-02af10398b21` exited 2 with
  `MIXED_REGION_STATE_NOT_EXACT_13`.
- The previously added `retain_dead_region_name = True` route crossed the former
  `dead0 already exists` failure. The trace records one flow volume and retention enabled,
  and Fluent reports region identification completed in 0.04 minutes.
- The surface mesh again completed successfully: Fluent reports one fluid/solid region,
  12 voids, 0.92 minutes, and maximum skewness 0.57.
- Immediately after successful Create Regions, the generated Update Regions fields
  `RegionCurrentList`, `RegionCurrentTypeList`, and `NumberOfListedRegions` were all null.
  The strict 1-main-plus-12-void guard therefore stopped execution before Update Regions,
  volume meshing, Student cell-count guards, mesh hashing, or solver entry.

## Evidence-led interpretation

The official local Fluent 2026 R1 generated task definition gives Update Regions an explicit
`MeshObject` argument whose default is empty. The failed consumer did not bind that argument.
The minimal reviewed follow-up binds the already validated unique product mesh object before
reading the generated region lists. It does not relax the exact 13-region contract.

## Claim boundary

This run proves that the name-retention change resolved the prior Create Regions collision.
It does not yet prove that binding `MeshObject` will populate the region menu, that a volume
mesh can be generated within Student limits, or that any CFD physics can run.

