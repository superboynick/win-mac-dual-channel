# AirJet 仿真论文项目

本目录是 AirJet 仿真项目的跨机器工作台。**先阅读 `AIRJET_MINI_FULL_PRODUCT_MASTER_PLAN.md`**；它是当前主线：在没有实物拆解的条件下，用公开证据复原一颗完整 AirJet Mini 产品，而非只建立单个 cooling cell。

## 这一阶段的目标

先做一个**公开证据约束的 AirJet Mini 整机数字复原模型**。最终 CAD 和至少一个气动/CHT 算例必须覆盖完整外壳、全部内部单元、完整进排气流道和热结构。单 cell 高保真模型只用于校准膜片与流量边界。先校准至公开产品的封装与性能量级；优化设计是后续阶段，不是当前任务。

## 文件

- `AIRJET_MINI_FULL_PRODUCT_MASTER_PLAN.md`：当前主项目文件；整机目标选择、多尺度模型、阶段、算法、算力和手册规划。
- `PROJECT_STATUS.md`：已完成/未完成的真实边界、P0–P6 状态和下一步执行顺序。
- `DECISION_AND_REASONING_ARCHIVE.md`：产品选择、参数来源、算法、替代方案、否决理由和未解决问题的可学习工程推理档案。
- `WINDOWS_HANDOFF.md`：Windows Codex 的读取顺序、当前阶段和下一步。
- `WINDOWS_ENVIRONMENT_REPORT.md`：Windows 实测硬件/软件、分阶段适用性和升级门槛。
- `reports/AIRJET_MINI_PROJECT_REPORT_FOR_ADVISOR_2026-07-13.md`：可直接交导师审阅的完整项目描述与阶段汇报；PDF 构建方法见 `reports/README.md`。
- `SKILLS_AND_GIT_WORKFLOW.md`：Git 作为 skill 源版本、一键安装和两机哈希验证方法。
- `PEER_COLLABORATION_PROTOCOL.md`：Mac/Windows Codex 平级权限、统一任务入口、任务领取、双向 push 和分叉处理规则。
- `AIRJET_RECONSTRUCTION_PLAN.md`：已明确降级为 P2/P3 单元子模型历史参考；不得先于整机 P1 执行。
- `OPERATION_MANUAL_00_EVIDENCE_TO_CAD.md`：早期单元 CAD 参考，同样只能在 P1 后使用；当前整机手册是 `manuals/01_FULL_PRODUCT_CAD.md`。
- `MODEL_ANNOTATIONS.md`：仿真注释总表；每一个简化、设置和结果都必须在这里解释。
- `evidence/airjet_reconstruction_ledger.csv`：可追溯参数账本，区分证实、范围、推断和未知。
- `evidence/airjet_mini_performance_curve_digitized.csv`：Mini 官方功耗—净散热/50 cm 系统噪声曲线的数字化校准点；它不是流量曲线。
- `evidence/CURVE_DIGITIZATION_METHOD.md`、`airjet_mini_curve_pixels.csv`、`digitize_airjet_mini_curve.py`：原 PDF 哈希、渲染条件、点坐标、换算公式和自动复核。
- `evidence/layout_candidate_constraints.md`：整机内部 Layout-L/M/S 的硬约束、搜索范围和淘汰顺序。
- `evidence/P0_EVIDENCE_FREEZE_RECORD.md`：已通过的 `AJM-P0-v001` Gate、证据边界、仍未知参数和 P1 入口。
- `evidence/OFFICIAL_IMAGE_COORDINATE_METHOD.md`：双透视图 homography、像素误差、Monte Carlo、跨视图差和剖面禁用规则。
- `evidence/patent_product_component_map.csv`：专利 FIG./页/printed column-line 到整机部件的候选映射。
- `evidence/layout_candidate_scores.csv`：去重后的唯一布局、硬门槛、pending 分数、P0 工作主/备选和评分覆盖率。
- `windows-prompts/AJM_WIN_P1_READINESS_001.md`：已完成的历史只读 P1 就绪核验提示，不再是下一轮入口。
- `windows-prompts/AJM_WIN_ANSYS_OFFICIAL_TRIAL_INSTALL_AND_SMOKE_004.md`：收到官方 entitlement 后执行的正版安装、签名核验与 P1–P5 能力复测；只有申请回执时必须停止。
- `windows-prompts/AJM_WIN_ANSYS_STUDENT_CAPABILITY_SMOKE_005.md`：已完成的 Student 能力历史入口；005 alternate-route v2 已通过，不能代替 P1 Gate。
- `reports/AJM_WIN_ANSYS_STUDENT_CLEANUP_2026-07-14.md`：第三方 PLE 清理、官方 Student 签名、Fluent Student checkout 报告及 Mac SSH 复核边界。
- `evidence/SOURCE_PROVENANCE.md`：每份产品卡、专利和论文能支持哪些参数，以及不能支持什么。
- `parameters/full_product_parameter_registry.csv`：完整产品尺寸、性能、结构、流体、控制和热参数注册表。
- `parameters/build_p1_cad_inputs.py`、`p1_layout_configuration_matrix.csv`、`p1_thickness_budget.csv`：从冻结账本生成的 P1 主/备/sentinel 布局输入、孔数代理和严格 2.8 mm 占位厚度预算；占位闭合不等于内部层厚已识别。
- `parameters/build_p1_cad_contracts.py`、`P1_CAD_CONTRACT_METHOD.md`：生成并解释 P1 的 6 个交付/残差变体、3 个单因素派生变体、内部 R0 构造规则、参数映射和全部 `NOT_RUN` Gate 行。
- `geometry/contracts/`：整机 feature、参数绑定、接口、Named Selections 和开放问题的证据分离合同。
- `logs/p1_cad_run_template.md`、`logs/external-files.csv`：P1 运行记录与 Git 外大文件哈希索引模板。
- `checklists/P1_CAD_INDEPENDENT_REVIEW_METHOD.md`、`prepare_p1_cad_review.py`：006 后的跨系统证据包校验、252 行 Gate worksheet 和 finalize/六项原生抽查校验；准备或推荐 PASS 都不直接改写 P1 阶段状态。
- `manuals/01_FULL_PRODUCT_CAD.md`：完整产品 CAD 装配、流道和候选阵列操作规划。
- `manuals/02_ACTUATOR_STRUCTURAL.md`：执行片结构、压电谐响应、位移场和整机功耗约束。
- `manuals/03_CELL_TRANSIENT_CFD.md`：单 cell 可压缩动态网格校准与整机降阶接口。
- `manuals/04_FULL_PRODUCT_AIRFLOW.md`：全部单元、相位、进排气歧管和整机气动验收。
- `manuals/05_FULL_PRODUCT_CHT.md`：完整热结构、自热/芯片热账户和官方热工况校准。
- `manuals/06_CALIBRATION_AND_UNCERTAINTY.md`：多指标参数识别、验证集与不可辨识性处理。
- `manuals/07_RUN_LOG_AND_GIT.md`：每次算例注释、大文件索引和 Windows/Mac 交接。
- `windows-prompts/AJM_WIN_P1_FULL_PRODUCT_CAD_BUILD_006.md`：只有 005 P1 CAD 工具链通过后才可执行的完整产品 CAD 建模任务；006 本身不能宣布 P1 Gate PASS。
- `windows-prompts/AJM_WIN_V02_PRELIMINARY_006.md`：已完成的 V02 两区整机 producer 历史入口；12-cell/972-hole preliminary CAD 已 PASS，不重复无差别 producer。
- `windows-prompts/AJM_WIN_V02_TOPOLOGY_OBSERVER_006.md`：已完成的 V02 Workbench/Mechanical topology observer 历史入口；修正版确认当前 STEP handoff 只保留 downstream 972 个孔印记而丢失 upstream 对应界面，不重复运行。
- `windows-prompts/AJM_WIN_V02_PARASOLID_TOPOLOGY_OBSERVER_006.md`：已完成的失败诊断入口；官方 v261 export options 下仍未生成 x_t，未启动 observer，不代表整机几何失败。
- `automation/ansys/run_v02_native_topology_observer_006.py`：一轮实跑确认 972 shared single-face membership，另一轮在 Workbench Refresh attach 失败；当前进入 repeatability/mesh conformality 诊断，P1 未通过。
- `automation/ansys/run_v02_native_mesh_conformality_006.py`：已冻结的 0.5 mm、无物理 Mechanical 共节点诊断；静态审计完成，Windows 实跑结果尚未写入。
- `automation/ansys/run_v02_split_step_converter_006.py`：已静态冻结的 fallback；仅在 native 重复性路线继续失败时运行独立 upstream/downstream STEP 转换与回读。
- `logs/evidence/AJM006_V02_PRELIMINARY_20260715T113939945030Z_1082d551ee85/`：V02 PASS 凝练证据；三轮 113-file 原始副本另存 Mac/Windows Downloads ZIP，六产物与 ZIP 的大小/SHA 见该目录 `evidence-summary.json`。正式 P1 的 `logs/external-files.csv` 在 P1 前保持 canonical empty。
- `logs/evidence/AJM006_V02_TOPOLOGY_OBSERVER_20260715T122149298547Z_2bdb5b95702a/` 与 `...T122907417508Z_2fb76257a827/`：首次及修正版 topology observer 凝练证据；首次 inventory 保留但角色分类被修正版取代。修正版 PASS 表示观测闭合，不是 mesh、formal 006 或 P1 PASS。
- `notebooks/airjet-mini-layout-baseline.ipynb`：可执行的产品指标核对与 Layout-L/M/S 几何候选枚举；几何可装入不等于真实内部布局。
- `notebooks/build_layout_baseline.py`：可重复生成上述 notebook 的标准库脚本。
- `checklists/full_product_stage_gates.md`：P0–P6 的整机验收门槛。
- `AIRJET_SIMULATION_PROJECT.md`：旧的“参数优化”蓝图，保留作未来阶段参考，不可作为当前建模任务。

## 本地资料位置（不纳入 Git）

`/Users/zhangjianxiao/Downloads/AirJet_research/` 保存公开专利、Frore 官方资料和基础论文。Windows 上请解压之前交付的 `AirJet_simulation_bundle_2026-07-12_v2.zip`；复原阶段优先使用专利 `US12137540B2`、`US11978690B2`、Hot Chips 2024 教程和 AirJet Mini 数据表。

## 协作规则

Mac Codex 与 Windows Codex 是平级协作者，两端都可以建立任务、修改文件、commit 和 push；执行端/复核端只是具体任务中的临时角色。完整规则见 `PEER_COLLABORATION_PROTOCOL.md`。

在 Windows 或 Mac 继续之前，先执行 `git status`、`git fetch origin` 并检查 ahead/behind；只在工作树干净且未分叉时执行 `git pull --ff-only`。完成一小段可检查工作后再提交并 `git push`。两端都不得 force-push、破坏性 reset 或静默覆盖对方成果。不要把求解结果、网格、case/data、临时文件或许可证信息直接提交；应只提交脚本、参数表、图表源文件、日志摘要和小型后处理数据。

交接前在 Mac 运行项目 skill 的 Python 审计器，在 Windows 运行仓库根目录的 `audit-airjet-project.ps1`。两者都通过只证明项目骨架和证据不变量一致。P0 证据 Gate 另有 `P0_EVIDENCE_FREEZE_RECORD.md`，已于 2026-07-13 通过；这仍不代表 P1–P6 的 CAD/物理仿真已经通过。实时进度以 `PROJECT_STATUS.md` 和 `checklists/full_product_stage_gates.md` 为准。
