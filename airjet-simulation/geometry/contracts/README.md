# P1 CAD 合同表

这些 CSV 是 `parameters/build_p1_cad_contracts.py` 的生成物，不手工编辑。

- `p1_cad_features.csv`：完整产品部件/流体体的存在、拓扑、几何和选择证据分开记录；
- `p1_cad_feature_parameter_bindings.csv`：参数 ID 到 CAD 特征属性的绑定；
- `p1_cad_interfaces.csv`：未来流体、结构、CHT 接口的两侧实体和守恒要求；
- `p1_cad_named_selections.csv`：跨重建稳定的命名规则、数量和方向检查；
- `p1_cad_open_questions.csv`：不能由 P1 候选 CAD 自动解决的未知量。

使用顺序：先读取 feature 与 `parameters/p1_internal_geometry_rules.csv`，再应用 parameter binding；之后按 interface 表分别建立归属 A/B feature 的成对 named selections，最后逐项对照 open questions 和 `checklists/p1_cad_gate_matrix.csv`。`{NNN}` 必须展开为 `001..N_CELL`；无 `{NNN}` 的 ID 按字面创建。

禁止事项：不得把 `CAND`、`REF`、`U` 体改名成 `REAL`/`PRODUCTION`；不得给 `C017/C019` 参考体赋材料或求解器物理；不得用 Boolean 后的临时 face index 代替稳定 Named Selection；不得因 CAD 成功生成而关闭开放问题。
