# AJM-005 T1 CAD transfer suite：第九次运行

第九次真实运行使用签名 commit `c965c73ef1eba0148ff5b9ebfef7a65ae75c4e9c`。SpaceClaim 七项
partial CAD 能力继续通过。Workbench source Geometry 的 `SetFile`、显式
`Edit(Interactive=False, IsSpaceClaimGeometry=True)`、`Exit()`、ComponentsToShare 与 save-data
全部返回；这证明 Workbench 管理的 SpaceClaim editor 能打开并关闭本轮精确 `.scdocx` predecessor。

随后 Model container `Refresh()` 仍无法附加同一 geometry structure，Mechanical inspection、mesh
和 project save 未到达。因此“编辑器能打开”和“下游 Model 能附加”是不同能力，显式 materialize
不能关闭当前 native attach 问题。

下一步以同一生产者已经验证过的 STEP 为诊断输入，测试 Workbench→Mechanical→mesh 管线本身。
STEP 不预期保留 SpaceClaim groups，故即使 body 和 mesh 通过，Named Selection transfer 仍应 FAIL，
完整 suite 不能写 PASS。P1 readiness 继续 BLOCKED，P1–P6 NOT_RUN。
