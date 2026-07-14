# AJM-005 T1 STEP semantic reconstruction：第十一次真实运行

第十一次运行使用签名 commit `4f80fc6aa461163635fb7c4d9e0fece008ac0e66`，首次执行与 native
transfer 完全分离的 semantic reconstruction profile/runner。SpaceClaim producer 正常退出：原有
七项 partial CAD assertions 与新增 `semantic_sidecar` assertion 全为 true，STEP、sidecar、producer
report 和 MCP predecessor manifest 的身份链通过。

Workbench 的 predecessor identity、semantic sidecar identity、STEP `SetFile`、component share 和
save-data 全部通过；`Model.Refresh()` 被调用，但在保存临时 `SYS.mechdb` 并附加 geometry structure
时抛出异常。因此 Mechanical inspection、面枚举、四项 partition negative controls、1/1/11 Named
Selection 重建、mesh 和 project save 全部 **NOT_REACHED**。

这不是“semantic reconstruction 算法已经运行但分类失败”。当前可以确认的是算法的输入身份检查
通过，而 host 在进入 Mechanical 前失败。与第十次相同 STEP route 成功到达 Mechanical 的记录相比，
本轮 case/job/temp 路径更长，存在 Workbench 临时数据库路径敏感的可检验假设；仅凭一次失败不能
认定它是根因。下一最小实验只缩短 semantic runner 的 case prefix，其余 profile、journal、STEP
route、sidecar 合同和判定全部保持不变。

本轮 suite 必须记为 `FAIL_STEP_SEMANTIC_RECONSTRUCTION_DIAGNOSTIC`。native attach、native Named
Selection transfer、native parameterization 和 P1 readiness 继续 false/BLOCKED，P1–P6 继续
`NOT_RUN`。
