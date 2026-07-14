# AJM-005 T1 CAD transfer suite：第四次运行

第四次真实运行使用签名 commit `9652054cf6d84467dce877342eb032df12c375a6`。SpaceClaim 的七项
断言首次全部通过：脚本等效参数重建、三段流体 union、单片闭合 manifold、
`INLET/OUTLET/WALLS=1/1/11`、原生保存重开，以及 STEP 导出后按 occurrence/master 两层接口
回读。STEP 中根层 body 数为 0，但组件内全层 body 数为 1；occurrence `TrimmedSpace` 提供
放置后的体积和 bbox，`Master.Shape` 的 `Body` 提供 `PieceCount/IsClosed/IsManifold`。这是
SpaceClaim 小模型的 `PASS_PARTIAL_CAD_CAPABILITY`，不代表 STEP 保存 Named Selections，报告也
明确把该预期写为 false。

MCP 随后冻结同一 job 的 report、`.scdocx` 与 STEP，并在 Workbench job 中复核 commit、profile、
job ID 和 SHA-256，`predecessor_identity` 为 PASS。`Geometry.SetFile` 和
`UpdateUpstreamComponents()` 没有抛异常；执行到 `model_component.Refresh()` 时，Workbench 报告
无法附加 `.scdocx` geometry structure。因此真正的直接失败只有 geometry attach，Mechanical
inspection 尚未开始，Named Selection transfer、粗网格和 project save 都是 `NOT_REACHED`，
不能把三个 false 布尔值误写成三个已执行的独立失败。

本轮证明了四件事不能互相替代：文件身份正确、生产者能够原生重开、消费者能够附加、下游语义及
网格通过。前三个中的前两个已经通过，第三个直接失败，第四个未到达。suite 所需条件是合取，所以
总状态仍为 `FAIL_CAD_TRANSFER_SET`；原生 driving parameter 仍 `NOT_RUN`，
`P1_CAD_TOOLCHAIN_READINESS` 保持 BLOCKED，P1–P6 仍 NOT_RUN。原始文件留在 Windows，仓库只
保存带哈希的凝练证据。
