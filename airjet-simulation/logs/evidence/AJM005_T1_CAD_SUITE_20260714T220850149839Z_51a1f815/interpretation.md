# AJM-005 T1 native CAD transfer：短路径单变量复测

本轮唯一有意的 runner 行为变量是把 native suite case ID 从长 `ajm005-cad-xfer-...` 改为
16-character `a5n-<12 hex>`。SpaceClaim producer profile/几何构造、native 格式、Workbench journal、
五项 assertions 和 Gate 口径未改变。producer 在本轮重新生成 32148-byte `.scdocx`，因此不主张它与
历史 native control 在字节层相同。

短路径确实把 Workbench job directory 降到 102 characters，冻结 native input 的完整路径为 145
characters。SpaceClaim 八项 partial CAD assertions 继续通过；Workbench 的 predecessor identity、
SetFile、显式 SpaceClaim Edit/Exit、ComponentsToShare、save-data 和 Model container 都返回，但
`Model.Refresh()` 仍报告无法附加同一 `.scdocx` geometry structure。Mechanical inspection、native
Named Selection cardinality、mesh 和 project save 没有到达。

这关闭了“只要缩短 native job path 就能修复 attach”的假设。它也说明 semantic route 的路径敏感性
不能自动外推到 native route：两条路线消费不同格式，并经过不同的底层 translator/materialization。
下一项最小区分实验应检查 MCP 冻结副本的只读属性是否与 SpaceClaim/Workbench 需要写回 native
working document 冲突，同时保持原冻结文件不变。

suite 保持 `FAIL_CAD_TRANSFER_SET`，P1 readiness BLOCKED，P1--P6 `NOT_RUN`，可见性为
`NOT_USER_OBSERVED`。本轮不能写 native geometry transfer、native Named Selection transfer 或 P1
PASS。
