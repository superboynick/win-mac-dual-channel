# AJM-005 T1 CAD transfer suite：首次失败

首次真实 SC-CAD-T1 在签名 commit `96f0799e98b264cc4efb8c914b4df734c5814158` 上运行。
5/6 mm 两次脚本重建与 160/192 mm³ 解析体积断言通过；随后 v261
`Selection.CreateByGroups(System.String[])` 拒绝普通 Python list，declared report 写
`FAIL_DIRECT`。SpaceClaim wrapper 虽退出 0，suite 没有把进程状态冒充工程能力；Workbench
被正确标为 `BLOCKED_UPSTREAM`，没有启动。

修复路线是显式构造 .NET `Array[String]`，并以新脚本 SHA、签名 commit 和 job ID 重试。
首次 suite、report、job state 与日志哈希保留，不覆盖。P1 readiness 仍 BLOCKED，P1–P6
仍 NOT_RUN。
