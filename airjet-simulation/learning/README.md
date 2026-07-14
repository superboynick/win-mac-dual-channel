# AirJet 整机复原学习入口

这套学习材料服务于两个目标：你能理解并复现项目中的建模/仿真工作；你能基于真实证据
自己写论文。它不是论文代写，也不会把不确定内部结构包装成产品实测真相。

## 1. 项目现在能声称什么

- P0 公开证据冻结 v1 已通过；这表示产品公开数据、专利候选和推断边界已整理并审计。
- P1--P6 尚未通过；当前没有正式整机 CAD、结构求解、整机 CFD 或 CHT 结果。
- 005 只验证 ANSYS 工具链是否能完成后续工作。即使 005 全过，也只能允许开始 P1，
  不能写成“AirJet 产品已经复原”或“仿真已经验证产品性能”。

实时状态以 [`PROJECT_STATUS.md`](../PROJECT_STATUS.md) 为准。

## 2. 先理解证据和 Gate

项目把数值分为 D/P/I/C/U：

- D：直接产品资料；
- P：专利候选，不等于量产产品事实；
- I：由公开图像或多源资料得到的推断；
- C：为闭合模型而设的候选或假设；
- U：仍未知。

参数的权威入口是 [`full_product_parameter_registry.csv`](../parameters/full_product_parameter_registry.csv)，
证据语言规则见 [`MODEL_ANNOTATIONS.md`](../MODEL_ANNOTATIONS.md)。阶段 Gate 见
[`full_product_stage_gates.md`](../checklists/full_product_stage_gates.md)。任何软件启动、脚本退出码 0、
文件存在或项目审计 PASS 都不能自动变成物理 Gate PASS。

## 3. 推荐阅读顺序

1. [`AIRJET_MINI_FULL_PRODUCT_MASTER_PLAN.md`](../AIRJET_MINI_FULL_PRODUCT_MASTER_PLAN.md)：整机目标。
2. [`DECISION_AND_REASONING_ARCHIVE.md`](../DECISION_AND_REASONING_ARCHIVE.md)：可审计的工程判断。
3. [`SOURCE_PROVENANCE.md`](../evidence/SOURCE_PROVENANCE.md)：资料从哪里来、能支持什么。
4. [`ANSYS_AUTOMATION_AND_005_LAB.md`](ANSYS_AUTOMATION_AND_005_LAB.md)：当前 Windows 实验。
5. `manuals/01` 到 `manuals/06`：P1 CAD、P2 结构、P3 单 cell 标定、P4 整机气动、
   P5 CHT、P6 不确定性。
6. [`PAPER_METHOD_EVIDENCE_MAP.md`](PAPER_METHOD_EVIDENCE_MAP.md)：把运行证据映射到你自己的论文。

## 4. 每个阶段都用同一学习循环

1. 理论：这个阶段求解什么物理问题，控制方程和主要尺度是什么。
2. 输入：逐行查参数表、几何合同和证据等级。
3. 动作：由固定、可版本控制的 ANSYS 脚本完成模型动作。
4. 证据：检查原生文件、报告、求解日志、守恒/收敛指标和 SHA-256。
5. 边界：写清哪些结论通过、哪些只是假设、哪些仍不能声称。

## 5. 当前可以自己复核的练习

阅读 005 的四个 T0 脚本，回答：

1. 为什么 `PASS_CONTROL` 不等于 `PASS_005_CAPABILITY`？
2. 为什么 SpaceClaim 同时测试 `.scdocx` 和 `.scdoc`，但不凭文件关联判断格式可用性？
3. 为什么 MCP 从已验签 commit blob 取脚本，而不直接执行工作树文件？
4. 为什么 Fluent health check 通过仍不能说明质量守恒、Dynamic Mesh 或 CHT 已通过？

答案可从 005 实验手册、[`REALITY_AND_FAILURE_LOG.md`](../logs/REALITY_AND_FAILURE_LOG.md)
和 skill 的 `references/gate-evidence.md` 中核对。

## 6. 记录分工

- 机器事实：`logs/run-index.csv` 和 `logs/evidence/<run_id>/`；
- 现实故障：`logs/REALITY_AND_FAILURE_LOG.md`；
- 长期工程决策：`DECISION_AND_REASONING_ARCHIVE.md`；
- 模型解释：`MODEL_ANNOTATIONS.md`；
- 论文方法映射：`learning/PAPER_METHOD_EVIDENCE_MAP.md`。

同一个事实只在一个权威位置维护，其他文件链接过去，避免以后相互矛盾。
