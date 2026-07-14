# AJM-005 T1 predecessor negative test

Commit `96f0799e98b264cc4efb8c914b4df734c5814158` 上三种无效提交均在创建 ANSYS
进程前被 MCP 拒绝：缺少必需 predecessor、无依赖 profile 却提供 predecessor，以及未知
predecessor。三个 job 都留下 `FAILED_START` 状态，`pid=null`；测试后五类 ANSYS 相关进程
计数为 0。

这支持“依赖输入边界 fail-closed 且启动失败可审计”。它不支持 SpaceClaim、Workbench 或
任何工程能力 PASS，也不改变 P1–P6 Gate。
