# AirJet 仿真教学文档

## 课程目录

| 编号 | 主题 | 内容 |
|------|------|------|
| 01 | CFD 基础与 AirJet | CFD 是什么、三大守恒方程、AirJet 仿真流程 |
| 02 | Fluent Watertight 工作流 | 7 步网格流程、PyFluent API、踩坑记录 |
| 03 | 网格质量与独立性 | 正交质量、网格类型、独立性验证方法 |
| 04a | SpaceClaim 参数化几何 | 如何在 SpaceClaim 中用 Python 构建 AirJet 几何 |
| 04b | 求解器设置与边界条件 | 压力基/密度基、湍流模型、边界条件设置 |
| 05a | PyFluent 自动化网格 | Python 驱动 Fluent 自动网格化 |
| 05b | 几何参数来源与推导 | 参数证据分级、来源、推导方法 |
| 06 | 自动化流程与项目结构 | MCP 架构、两阶段流程、合同层 |
| 07 | CHT 与 FSI 概念 | 共轭传热、流固耦合、许可证需求 |

## 学习路径

```
01 → 02 → 03 → 04a → 05a → 06 → 04b → 05b → 07
(基础)  (实操)  (理论)  (CAD)  (网格)  (架构)  (求解)  (参数)  (进阶)
```

## 配套资源

- 复现指南：`AIRJET_SIMULATION_REPRODUCTION_GUIDE.md`
- 项目主计划：`AIRJET_MINI_FULL_PRODUCT_MASTER_PLAN.md`
- 决策存档：`DECISION_AND_REASONING_ARCHIVE.md`
- 操作手册：`OPERATION_MANUAL_00_EVIDENCE_TO_CAD.md`

## 贡献

Mac Codex + Windows Codex 协作生成
