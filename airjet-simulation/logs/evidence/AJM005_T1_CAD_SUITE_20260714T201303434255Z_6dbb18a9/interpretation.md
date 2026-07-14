# AJM-005 T1 CAD transfer suite：第八次运行

第八次真实运行使用签名 commit `1d1c9eeba85249d8f848bfb08f49ad3937aece17`。SpaceClaim 七项
partial CAD 能力继续通过。Workbench 保持第七轮已经越过的 source、SetFile、ComponentsToShare
与 save-data 路线，仅把下游 Component Update 替换为同机官方 Model container `Refresh()`。

Model container 成功取得，但 `Refresh()` 被调用后没有返回，错误仍为无法附加 `.scdocx`
geometry structure；Mechanical inspection、mesh 和 project save 未到达。因此 share topology 中
两种更新 API 都不能关闭当前 attach 失败，不能再把根因归为 update API 选择。

下一最小实验保持 share/refresh 不变，只在 source 上显式调用官方
`Edit(Interactive=False, IsSpaceClaimGeometry=True)` 后 `Exit()`，检验 Workbench 管理的 SpaceClaim
editor 能否真实打开并关闭该 predecessor。完整 suite 仍 FAIL，P1 readiness BLOCKED，P1–P6
NOT_RUN。
