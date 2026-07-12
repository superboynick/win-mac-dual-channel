# AirJet 仿真论文项目

本目录是 AirJet 仿真项目的跨机器工作台。**先阅读 `AIRJET_MINI_FULL_PRODUCT_MASTER_PLAN.md`**；它是当前主线：在没有实物拆解的条件下，用公开证据复原一颗完整 AirJet Mini 产品，而非只建立单个 cooling cell。

## 这一阶段的目标

先做一个**公开证据约束的 AirJet Mini 整机数字复原模型**。最终 CAD 和至少一个气动/CHT 算例必须覆盖完整外壳、全部内部单元、完整进排气流道和热结构。单 cell 高保真模型只用于校准膜片与流量边界。先校准至公开产品的封装与性能量级；优化设计是后续阶段，不是当前任务。

## 文件

- `AIRJET_MINI_FULL_PRODUCT_MASTER_PLAN.md`：当前主项目文件；整机目标选择、多尺度模型、阶段、算法、算力和手册规划。
- `DECISION_AND_REASONING_ARCHIVE.md`：产品选择、参数来源、算法、替代方案、否决理由和未解决问题的可学习工程推理档案。
- `WINDOWS_HANDOFF.md`：Windows Codex 的读取顺序、当前阶段和下一步。
- `AIRJET_RECONSTRUCTION_PLAN.md`：内部单元复原依据；现在是整机规划的子文档，不再是最终目标。
- `OPERATION_MANUAL_00_EVIDENCE_TO_CAD.md`：早期单元证据到 CAD 草案；将扩写为完整产品 CAD 手册。
- `MODEL_ANNOTATIONS.md`：仿真注释总表；每一个简化、设置和结果都必须在这里解释。
- `evidence/airjet_reconstruction_ledger.csv`：可追溯参数账本，区分证实、范围、推断和未知。
- `evidence/airjet_mini_performance_curve_digitized.csv`：Mini 官方功耗—净散热/流量曲线的近似数字化校准点。
- `evidence/layout_candidate_constraints.md`：整机内部 Layout-L/M/S 的硬约束、搜索范围和淘汰顺序。
- `evidence/SOURCE_PROVENANCE.md`：每份产品卡、专利和论文能支持哪些参数，以及不能支持什么。
- `parameters/full_product_parameter_registry.csv`：完整产品尺寸、性能、结构、流体、控制和热参数注册表。
- `manuals/01_FULL_PRODUCT_CAD.md`：完整产品 CAD 装配、流道和候选阵列操作规划。
- `manuals/02_ACTUATOR_STRUCTURAL.md`：执行片结构、压电谐响应、位移场和整机功耗约束。
- `manuals/03_CELL_TRANSIENT_CFD.md`：单 cell 可压缩动态网格校准与整机降阶接口。
- `manuals/04_FULL_PRODUCT_AIRFLOW.md`：全部单元、相位、进排气歧管和整机气动验收。
- `manuals/05_FULL_PRODUCT_CHT.md`：完整热结构、自热/芯片热账户和官方热工况校准。
- `manuals/06_CALIBRATION_AND_UNCERTAINTY.md`：多指标参数识别、验证集与不可辨识性处理。
- `manuals/07_RUN_LOG_AND_GIT.md`：每次算例注释、大文件索引和 Windows/Mac 交接。
- `checklists/full_product_stage_gates.md`：P0–P6 的整机验收门槛。
- `AIRJET_SIMULATION_PROJECT.md`：旧的“参数优化”蓝图，保留作未来阶段参考，不可作为当前建模任务。

## 本地资料位置（不纳入 Git）

`/Users/zhangjianxiao/Downloads/AirJet_research/` 保存公开专利、Frore 官方资料和基础论文。Windows 上请解压之前交付的 `AirJet_simulation_bundle_2026-07-12_v2.zip`；复原阶段优先使用专利 `US12137540B2`、`US11978690B2`、Hot Chips 2024 教程和 AirJet Mini 数据表。

## 协作规则

在 Windows 或 Mac 继续之前，先执行 `git pull`；完成一小段可检查工作后，提交并 `git push`。不要把求解结果、网格、case/data、临时文件或许可证信息直接提交；应只提交脚本、参数表、图表源文件、日志摘要和小型后处理数据。
