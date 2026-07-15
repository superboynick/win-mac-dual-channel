# AJM-006 V03 Student-coarse C3 interpretation

C3 在同一完整 12-cell/972-throat 候选上启用了 `wall_to_internal=true`，并允许用 1 到 12 个流体 cell zones 的连通图证明流路，而不再把“必须恰好一个 cell zone”当成物理真相。Fluent 完成了体网格 API：共 413,855 cells、12 个 fluid cell zones，最低正交质量为 0.22220636。这个 cell 数低于当前脚本中的 Student 一百万 cell 上限；但 node count 和完整 Student 双上限守卫尚未执行，所以不能宣称 Student 规格门已通过。

表面阶段同时报告 `1 fluid/solid regions and 11 voids`，并明确识别出一个 external baffle（zone 323）。这说明“12 个体区都被命名为 fluid”本身不足以证明真实流动连通；仍必须证明这些区通过合法 interior 接口连接，而且没有用本应封闭的执行器空腔或壁面制造捷径。

972 个喉道轴点查询全部返回原始 `None`。C3 没有对明显位于入口/出口流体内部的点执行正控制，因此这个结果既可能表示查询 API/单位不适用，也可能表示喉道轴上确实没有体网格，不能单独作物理结论。脚本随后在 `get_baffles_for_face_zones` 返回 `None` 时失败；在此之前没有把 interior face graph 写入 trace，也没有执行完整 mesh integrity、node count 或持久化网格。

因此 C3 是一次失败闭合但有价值的诊断：它证明粗网格可以生成 12 个体区及可接受数量级的 cells，也发现 external baffle；它没有证明整机流路连通，没有生成 `.msh.h5`，也没有通过 P1 或任何 P1-P6 Gate。下一轮必须先保留 API 的 `None` 语义，加入入口/出口正控制，持久化 cell-zone graph 与逐面邻接，并在所有工程判定之前明确 external baffle 的真实角色。
