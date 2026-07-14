# AJM P1 CAD 运行记录模板

## 运行身份

- task_id:
- run_id:
- UTC started/finished:
- operator/Codex:
- computer:
- Git commit:
- Ansys/SpaceClaim version:
- 005 report path and SHA256:
- external run directory:

## 输入复核

- `build_p1_cad_inputs.py --check`:
- `build_p1_cad_contracts.py --check`:
- configuration_id:
- variant_id:
- selected_vent_candidate_set_id:
- selected_orifice_pattern_id:
- selected_exhaust_branch_id:
- selected_cell_geometry_rule_id:
- selected_central_anchor_rule_id:
- selected_bottom_chamber_rule_id:
- selected_cell_partition_rule_id:
- selected_top_chamber_branch_id:
- selected_perimeter_gap_branch_id:
- selected_side_frame_closure_branch_id:
- selected_residual_closure_branch_id:
- selected_orifice_grid_rule_id:
- comparison_parent_variant_id / changed_factor:
- unresolved branch decisions and reason:

## 几何结果

- envelope measured (mm):
- cell count / connected cell count:
- solid body count:
- required fluid body count / connected count:
- isolated fluid count:
- interference count:
- zero-thickness/sliver count:
- blind/lost orifice count:
- actual orifice count:
- actual active plate area (mm2):
- actual open area (mm2 / %):
- minimum displacement clearance (mm):
- thickness closure error (mm):

## 传递与文件

- native save/reopen:
- STEP export/reimport:
- Workbench geometry transfer:
- Named Selection transfer:
- expected/actual Named Selection cardinalities:
- native/STEP/fluid/screenshot/log paths and SHA256:

## 证据边界与异常

- retained open questions:
- geometry-only body guard result:
- known-volume mass estimate:
- unresolved mass to 11 g:
- Student/software limitation:
- failed operation and exact error:
- workaround attempted:
- impact on later P2--P5:

## Gate 建议

- P1 candidate status: `INCOMPLETE` / `PENDING_PEER_REVIEW`
- hard failures:
- items requiring independent peer review:
- statement: 本记录不允许将 `P1_STAGE_GATE` 写为 `PASS`。
