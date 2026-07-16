# Correct the C7 WTM interpretation: retained zone is an actuator gap

This supersedes the earlier Windows interpretation that used all HDF5 node
zones to infer a full-product bbox. The mesh SHA remains
`9ecc0b2883e91a3fc1cd850edd825fdad3de19f880214e4493c61559891e7ce0`.

A new read-only HDF5 gate followed final face connectivity to the nodes
actually used by the 34,883-cell zone. It observed:

- used-node bbox `X=[-10.75,-3.75]`, `Y=[-14.375,-7.375]`,
  `Z=[1.6575,1.9325] mm`;
- one cell zone and 34,883 connected cells;
- only one interior and one generic wall face zone;
- full-product bounds came from unused CAD/curvature node zones.

The retained WTM zone is therefore one actuator-gap tile, not the main-flow
volume. Correct status is:

`STAGE1_GEOMETRY_PASS_WTM_REGION_SELECTION_FAIL_ACTUATOR_GAP`

and `BOUNDARY_SEMANTICS_COLLAPSED`.

Mac actions:

1. Correct every status, guide, report, and paper statement that calls the C7
   34,883-cell mesh a full-product main-flow mesh.
2. Preserve the valid C7 Stage 1 geometry PASS separately.
3. Review the new full-1078-face semantic consumer and HDF5 gate after the
   Windows integration commit; do not run the old `save_mesh4.py` route again.
4. Dispatch a new runtime task only after the static consumer requires unique
   4/1/1/12/12/972/76 roles, rejects generic collapse, and validates used-node
   bbox plus single-fluid adjacency.

P1-P6 remain `NOT_RUN`; no solver or physics is authorized.
