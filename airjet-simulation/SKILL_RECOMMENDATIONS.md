# AirJet 项目的 Codex 技能建议

检索日期：2026-07-12。

## 结论

官方可安装技能库当前没有专门的 CFD、ANSYS Fluent、OpenFOAM 或 FSI 技能。不要安装泛用设计、部署或网页技能来替代领域工作流。

## 适合安装的两个技能

1. `jupyter-notebook`
   - 用来创建可复现的 DOE、读取每个 Fluent 工况导出的 CSV、画网格独立性图、响应面和 Pareto 图。
   - 安装时机：进入 P3（参数扫描）前。

2. `pdf`
   - 用来将项目说明、图表、方法附录汇编为 PDF。
   - 安装时机：开始形成周报或论文初稿前。

## 暂缓的技能

- `define-goal`：目前项目文件已经定义阶段和门槛；若要以 Codex 的正式长期目标追踪，才安装。
- 自定义 `airjet-cfd`：等 P1 和 P2 跑通以后再做。届时技能应只记录已经验证过的：命名面、Fluent 求解设置、网格门槛、报告字段、失败处理和 Git 规则。

## 不是 Codex skill，但应采用的技术

- **PyFluent**：ANSYS 官方 Python 接口，适合把 Fluent 的启动、设置、运行和导出接入 Python/批处理。需要本机安装并授权 Fluent。
- **Fluent journal/UDF**：把可复现的求解设置保存进本仓库；先从 journal 开始，动态膜片阶段才考虑 UDF。
- **Python 数据管线**：`pandas + numpy + matplotlib + scipy`；所有图应能从 CSV 再生。

## 安装前提

先在 Windows 确认 Fluent 是否安装、版本、许可证和 RAM/CPU。技能不能替代求解器、许可证或模型验证。
