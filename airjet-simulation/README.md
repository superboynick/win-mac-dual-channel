# AirJet 仿真论文项目

本目录是 AirJet 仿真论文的跨机器工作台。先阅读 `AIRJET_SIMULATION_PROJECT.md`；它是研究问题、模型、算法、参数、验证、计算资源和论文交付的统一依据。

## 这一阶段的目标

先做一个**可验证的等效微射流共轭传热（CHT）基线模型**，而不是直接反向复刻商业 AirJet 的完整 MEMS 结构或建立全阵列双向 FSI。

## 文件

- `AIRJET_SIMULATION_PROJECT.md`：主项目文件，Windows 上也应优先阅读。
- `parameters/baseline_parameters.csv`：首轮 Fluent/CFX/OpenFOAM 参数录入表；带有参数状态和来源。
- `checklists/stage-gates.md`：每个阶段的完成判据，防止模型还未验证就进入优化。

## 本地资料位置（不纳入 Git）

`/Users/zhangjianxiao/Downloads/AirJet_research/` 保存公开专利、Frore 官方资料和基础论文；其 `SIMULATION_READING_GUIDE.md` 是资料阅读顺序。Windows 上请解压之前交付的 `AirJet_simulation_bundle_2026-07-12_v2.zip`，再把解压目录路径填进主项目文件第 2 节的“本地证据库”。

## 协作规则

在 Windows 或 Mac 继续之前，先执行 `git pull`；完成一小段可检查工作后，提交并 `git push`。不要把求解结果、网格、case/data、临时文件或许可证信息直接提交；应只提交脚本、参数表、图表源文件、日志摘要和小型后处理数据。
