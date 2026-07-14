# AJM-005 T1 CAD transfer suite：第七次运行

第七次真实运行使用签名 commit `a4aa2befd0aa1b15aacaf8771d5b806f4e569b6e`。SpaceClaim 七项
partial CAD 能力继续通过。Workbench 的独立 Geometry source、`.scdocx SetFile`、
`ComponentsToShare` Static system 和 `GetGeometryFileAndSaveData()` 全部返回，说明第六轮的
component 兼容性问题已经由官方 share 架构越过。

失败发生在仍保持不变的 `Model.Update(AllDependencies=True)`，错误再次是无法附加 `.scdocx`
geometry structure；Mechanical inspection、mesh 和 project save 未到达。这证明 share 数据流本身
能建立，但尚不能证明 downstream model 已能消费 geometry。

同机官方 `StaticStructuralANSYS.wbjn` 在 share/save-data 后调用的是 Model container
`Refresh()`，不是 Component `Update(AllDependencies=True)`。下一轮只替换这一个下游更新语义，
保持已越过的 share route 与所有验收断言不变。完整 suite 仍 FAIL，P1 readiness BLOCKED，
P1–P6 NOT_RUN。
