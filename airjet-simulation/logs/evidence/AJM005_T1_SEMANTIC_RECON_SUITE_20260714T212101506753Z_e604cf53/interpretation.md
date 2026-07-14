# AJM-005 T1 STEP semantic reconstruction：第十二次短路径单变量复测

第十二次运行只把 semantic runner 的 case prefix 从 `ajm005-semantic-recon-` 缩为
`ajm005-sem-`。Workbench job directory 由 176 降至 154 字符。相同 profile、journal、STEP
share/save-data/Refresh route 和判定下，`Model.Refresh()` 从上轮的 attach exception 变为
`RETURNED`；Mechanical inspection、semantic reconstruction command 和 project save 也全部返回。
这对 legacy Workbench/Mechanical 路径预算敏感提供强支持，但不证明所有 Windows 路径问题都由
传统 `MAX_PATH=260` 单独造成。

进入算法后首次看到真实分类结果：`INLET=0, OUTLET=1, WALLS=12`，而合同要求 1/1/11。因此
fail-closed partition validation 正确拒绝，本轮没有创建三组 Named Selections，也没有 mesh。
Workbench 仍保存了 50593-byte 诊断 project；project save PASS 不能替代 semantic reconstruction
或 mesh PASS。

当前 inspection 的失败分支只保存 exception/traceback，没有保存已在内存生成的 13-face
`face_details`、candidate IDs 和 negative-control 明细。控制流显示程序已越过 body count、face count
和四项 pure partition controls 才在真实 1/1/11 validation 失败，但这些结果仍不能提升为报告 PASS。
下一轮只增强失败观测：在真实 partition validation 前把 CAD unit、body/face count、13-face map、
candidate IDs 与 negative controls 写入 inspection 对象；不放宽 centroid/area tolerance，不改变分类
规则。拿到真实候选面数值后，才允许提出下一个单变量算法修正。

suite 继续为 `FAIL_STEP_SEMANTIC_RECONSTRUCTION_DIAGNOSTIC`；canonical native claims 全为 false，
P1 readiness 继续 BLOCKED，P1–P6 继续 `NOT_RUN`。
