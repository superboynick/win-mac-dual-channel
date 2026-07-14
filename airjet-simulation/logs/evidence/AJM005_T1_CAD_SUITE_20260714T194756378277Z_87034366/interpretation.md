# AJM-005 T1 CAD transfer suite：第五次运行

第五次真实运行使用签名 commit `f3a1769eca78b146967e27193f54c1bf8cc729af`。SpaceClaim 再次
取得七项 `PASS_PARTIAL_CAD_CAPABILITY`，说明上轮 partial PASS 可复现；不同 run 的原生文件
哈希略有变化，但每个 Workbench job 都只消费本轮冻结并复核过的 predecessor，不能跨 run 混用
产物 SHA。

本轮的唯一功能变量是 Workbench 更新语义：把旧的
`Model.UpdateUpstreamComponents(); Model.Refresh()` 替换为
`Model.Update(AllDependencies=True)`。其余 `.scdocx`、Static Structural 模板、Geometry
container `SetFile`、Named Selection import 属性、Mechanical 检查与 Gate 均不变。新增的
`execution_reach` 证明 `SetFile=RETURNED`、`Update(AllDependencies=True)=CALLED` 但没有返回；
错误仍是无法附加 `.scdocx` geometry structure。Mechanical container/inspection、粗网格和 project
save 均未到达。

因此可以排除“只有旧的 upstream-update + refresh 顺序导致 attach 失败”这一窄假设，但不能把
结果扩大为“.scdocx 格式绝对不支持”或“Mechanical 不可用”。下一步必须改变数据流架构而不同时
改变格式：按同机 v261 sample 建立独立 Geometry source，再显式 TransferData 到 Static Geometry。
suite 总状态仍为 `FAIL_CAD_TRANSFER_SET`；原生 driving parameter 仍 `NOT_RUN`，P1 readiness
保持 BLOCKED，P1–P6 仍 NOT_RUN。
