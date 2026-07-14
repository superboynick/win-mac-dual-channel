# AJM-WIN-ANSYS-CAPABILITY-SMOKE-003 摘要

日期：2026-07-13
主机：`LAPTOP-LCCLM2HI`
基线 commit：`13b6919deb92124882df61fc9be1d0d525aa06b7`
原始报告：`C:\Users\admin\Downloads\AIRJET_ANSYS_CAPABILITY_SMOKE_003.txt`（不纳入 Git）

## 结论

`SMOKE_STATUS=BLOCKED_TECHNICAL_FAILURE`

Ansys 2026 R1 的 Workbench 主界面和 Static Structural、Modal、Harmonic Response、Fluid Flow (Fluent) 模板可见，但本轮没有形成任何可用的 CAD、结构或 CFD 求解会话。因此 P1--P5 仍为 `BLOCKED`，不得把“软件已安装”写成“工具链已就绪”。

## 实测结果

| 能力 | 结果 | 观察证据 |
|---|---|---|
| Workbench 主界面 | PASS | 可见窗口正常进入，关键系统模板可见 |
| SpaceClaim/Discovery | FAIL | 未进入可用建模界面，未完成参数化、Named Selections、Volume Extract 或 STEP 往返 |
| Mechanical 最小求解 | FAIL | 未形成可见可用 Mechanical 会话，未完成静力求解和位移表导出 |
| Modal/Harmonic 模板 | PASS（仅可见） | 只证明 Workbench 模板存在，不证明求解许可可用 |
| 压电/耦合场路线 | 未确认 | GUI 入口不可见，Mechanical APDL 路线未验证 |
| Fluent 单核 | FAIL | GUI 短暂出现后因 checkout 问题退出 |
| Fluent 八核 | 未尝试 | 按烟雾测试规则，单核失败后不盲目重试 |
| P1 整机 CAD | BLOCKED | 没有可用参数化 CAD 会话和流体体积提取 |
| P2 执行片结构 | BLOCKED | 没有最小求解、压电路线和位移导出证据 |
| P3--P5 CFD/CHT | BLOCKED | 没有可用 Fluent 会话、最小流动求解或质量守恒结果 |

## 边界

- 本轮没有创建正式 AirJet CAD 或仿真模型。
- 本轮没有读取或修改许可证文件、服务、注册表或授权环境变量。
- 本轮没有运行激活、修复、补丁或许可证生成工具。
- 原始截图、日志和临时文件保留在 `C:\Users\admin\Downloads\AIRJET_ANSYS_SMOKE_003\`。
- 该结果只描述当时观察到的技术能力，不判定许可证名称、来源或合法性。

## 后续决定

用户已于 2026-07-13 提交 Ansys 30 天官方试用申请。当前报告作为官方试用激活前的对照基线。只有在官方 entitlement/临时账号实际开通并按官方说明完成配置后，才执行 `windows-prompts/AJM_WIN_ANSYS_OFFICIAL_TRIAL_INSTALL_AND_SMOKE_004.md`。004 通过后才允许进入 P1 整机 CAD；若官方试用仍不提供可用 CAD，而 Mechanical/Fluent 可用，则再单独选择中性 STEP CAD 路线。
