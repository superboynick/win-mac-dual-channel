# AJM-005 T1 native CAD transfer：writable-staging 有意干预复测

本轮保持 16-character short case ID、同一个 SpaceClaim producer、`.scdocx` 格式、显式
SpaceClaim Edit/Exit、`ComponentsToShare`、五项 native assertions 和 Gate 口径不变。唯一有意的
route intervention 是：MCP 冻结的 predecessor 继续只读，Workbench job 内另建一个初始 size/SHA
相同、完整路径长度也相同的可写 working copy，`SetFile` 只消费该 working copy。本轮 producer
重新生成了 32143-byte native 文件，与前轮 32148-byte 文件并非逐字节配对控制，因此这里只把
“有意改动”与其他自然运行差异区分开，不声称是严格 permission-only paired trial。

证据链证明 staging 合同实际生效：frozen source 在前后均为 read-only，size 32143 bytes、SHA-256
`7e1d3729...` 前后不变；working copy 在 Edit 前可写，运行结束仍存在，size/SHA 与初值相同。显式
Edit/Exit、`ComponentsToShare` 和 save-data 都返回，但 working copy 没有被 editor 改写；整个 WB
job 为 282.115 秒，异常点仍是 `Model.Refresh()` 无法附加 staged `.scdocx`。journal 没有单独记录
Refresh 调用耗时，因此不能把整个 job 时长写成 Refresh 独占耗时。Mechanical inspection、native Named
Selection transfer、mesh 与 project save 没有到达。

因此可以关闭“本轮 job-local hash-equal writable staging 足以修复当前 native attach route”以及
“read-only 是唯一充分解释”这两个窄假设。不能全局排除权限是多因素之一，不能把结果扩大成
“SpaceClaim 从不需要可写文件”，也不能单凭 `working_copy_mutated_by_editor=false` 断言编辑器完全
没有内部活动；本轮只观测了该路径下文件的 size/SHA。

suite 保持 `FAIL_CAD_TRANSFER_SET`，P1 readiness BLOCKED，P1--P6 `NOT_RUN`，可见性为
`NOT_USER_OBSERVED`。本轮不能写 native geometry transfer、native Named Selection transfer、native
parameterization 或 P1 PASS。下一步应改变 native materialization route，而不再叠加路径或权限
workaround：让 Workbench 管理 SpaceClaim Geometry editor 的内部文档创建/导入，再用同一五项合同判定。

suite 顶层 `pass_005_capability=PARTIAL_CAD_TRANSFER_ONLY` 只指 SpaceClaim disposable producer 的
partial CAD capability，不表示 Workbench native transfer 部分通过。顶层
`p1_cad_blocker=NATIVE_PARAMETERIZATION_NOT_RUN` 是仍未完成的后续 hard blocker；本轮最直接的当前
阻断点仍是 Refresh native attach failure。两者不能互相替代。
