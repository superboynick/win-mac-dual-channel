# Windows Codex 接手说明

交接日期：2026-07-12  
目标机器：`LAPTOP-LCCLM2HI`，用户 `admin`  
仓库：`C:\Users\admin\win-mac-dual-channel`

## 当前目标

完整复原第一代 AirJet Mini 产品，不是单喷嘴、单 cell 或参数优化。单 cell 仅作为结构和动态 CFD 校准子模型。设计改进等整机复原完成后再开始。

## Windows Codex 启动后先读

1. `AGENTS.md`
2. `airjet-simulation/README.md`
3. `airjet-simulation/AIRJET_MINI_FULL_PRODUCT_MASTER_PLAN.md`
4. `airjet-simulation/DECISION_AND_REASONING_ARCHIVE.md`
5. `airjet-simulation/evidence/SOURCE_PROVENANCE.md`
6. `airjet-simulation/parameters/full_product_parameter_registry.csv`
7. `airjet-simulation/checklists/full_product_stage_gates.md`
8. `airjet-simulation/manuals/01_FULL_PRODUCT_CAD.md`

## 研究资料

Windows Downloads 应有：

`C:\Users\admin\Downloads\AirJet_simulation_bundle_2026-07-12_v2.zip`

Expected SHA256:

`96f65ca6e5c8b8d4bc2b4acdeeb78d9917cf3c5ec2c159055daf88fa3ea261a4`

解压后将得到 `AirJet_research`，包含产品数据表、Hot Chips 教程、专利和基础 CFD 论文。PDF 不提交 Git。

## 当前工作阶段

P0 产品证据冻结与完整布局候选。尚未进入 CAD 定版。Windows Codex 应先：

1. 核实 Windows CPU、RAM、GPU、磁盘和 ANSYS/Fluent/Mechanical 版本与许可证；
2. 解压研究 ZIP；
3. 确认 Mini 性能曲线送风量轴单位；
4. 从官方 Mini 顶视图/横截面提取活动区、进气和出口比例；
5. 完善 Layout-L/M/S 候选约束；
6. 在用户确认 CAD 软件后再开始完整产品 CAD。

## 安全规则

- 不把旧 `AIRJET_SIMULATION_PROJECT.md` 当主线；它已归档。
- 不从宣传图直接断言 cell 数。
- 不把专利范围写成产品实际精确值。
- 不自动进行参数优化或论文写作。
- 不提交许可证、密钥、大型 case/data/mesh。
- 修改前 `git status`；发现未知修改或分支分叉立即停止。
