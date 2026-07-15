# Windows Codex 任务：AJM-WIN-ANSYS-STUDENT-CAPABILITY-SMOKE-005

目标：在已经清理第三方授权、只保留官方 Ansys Student 2026 R1 的 Windows 上，通过可复核的 GUI 操作或官方批处理/API 验证 AirJet Mini P1--P5 所需实际技术能力。只做可删除的小模型；不建立正式 AirJet CAD。

## 0. 2026-07-14 执行修订：官方 API 路线

用户已明确表示本轮不要求亲眼观察 GUI。允许使用仓库审计后的 `airjet-ansys-automation`
skill、固定 `profile_id` MCP 和 ANSYS 官方接口执行：SpaceClaim `/RunScript`、Workbench
`RunWB2 -B -R`、PyMechanical 和 PyFluent。无头结果记录
`VISIBILITY=NOT_USER_OBSERVED`，不能写成 `GUI_VISIBLE=PASS`。

`PASS_CONTROL` 只表示官方接口可控；只有实际完成本任务要求的小几何、传递、求解、
保存/重开和守恒断言，并产生规定的原生文件与报告，才允许相应技术字段写 `PASS`。
任何纯菜单/API 节点存在性检查均不能冒充实际工程能力通过。

仓库：`C:\Users\admin\win-mac-dual-channel`

## 1. 严格边界

1. 不打开、读取或修改任何许可文件/本地许可池；不修改、停止或替换许可服务、注册表许可设置或授权环境变量。只允许只读检查已知污染标记 `ANSYSLMD_LICENSE_FILE=1055@localhost` 是否重新出现，不枚举或输出其他授权值。
2. 不运行激活、补丁、破解器、许可证生成器或第三方许可程序。
3. 不执行官方修复安装；`python_site_syscplg/cuDSS` 只记录警告。
4. 所有临时文件只放在 `C:\Users\admin\Downloads\AIRJET_ANSYS_STUDENT_SMOKE_005\`。
5. 不修改、提交或推送 Git。
6. GUI 可见性字段的 PASS 必须由可见桌面实际观察支持；但官方批处理/API 产生的确定性
   原生产物、重开结果、求解结果和数值断言可独立支持技术能力字段 PASS。后台进程仅存在、
   进程退出码为 0 或菜单/API 节点仅存在均不算技术能力 PASS。
7. 失败后记录原始错误，不反复盲试，不修改许可绕过限制。

## 2. Git 与纯净 Student 基线

```powershell
cd C:\Users\admin\win-mac-dual-channel
git fetch origin
git status --short --branch
git status --porcelain
git rev-parse HEAD
git rev-list --left-right --count HEAD...origin/main
powershell -ExecutionPolicy Bypass -File .\audit-airjet-project.ps1
```

要求 `git fetch origin` 成功、当前分支为 `main`、工作树干净、ahead/behind=`0/0`、项目审计 PASS。上述任一命令失败或条件不满足时，先把 `GIT_FETCH/PROJECT_AUDIT/ERROR_MESSAGES` 写入报告，最终写 `STUDENT_TOOLCHAIN_STATUS=BLOCKED_TECHNICAL_FAILURE`，停止，不进入 GUI 烟雾测试。阅读：

- `airjet-simulation/reports/AJM_WIN_ANSYS_STUDENT_CLEANUP_2026-07-14.md`；
- `airjet-simulation/reports/AJM_WIN_ANSYS_CAPABILITY_SMOKE_003_SUMMARY.md`；
- `airjet-simulation/manuals/01_FULL_PRODUCT_CAD.md`；
- `airjet-simulation/manuals/02_ACTUATOR_STRUCTURAL.md`；
- `airjet-simulation/manuals/03_CELL_TRANSIENT_CFD.md`。

只读确认安装根目录为 `D:\ansys\ANSYS Inc\ANSYS Student\v261`，并确认系统中没有 PLE 卸载项/服务、1055 监听或 `ANSYSLMD_LICENSE_FILE=1055@localhost`。若旧授权痕迹重新出现，输出 `STUDENT_TOOLCHAIN_STATUS=BLOCKED_CONTAMINATED_BASELINE` 并停止。

## 3. SpaceClaim / P1 CAD 烟雾测试

在 SpaceClaim GUI 或审计后的 `/RunScript` 中建立：

1. `20 x 10 x 4 mm` 外块；
2. 内部 `16 x 6 x 2 mm` 腔体；
3. 直径 `2 mm` 入口和 `4 x 1 mm` 出口；
4. 建立 driving dimensions 或等价参数；
5. Named Selections：`INLET`、`OUTLET`、`WALLS`；
6. Volume Extract 或等价方法提取单一连通流体体积；
7. 检查无孤立体、盲孔、零厚度面；
8. 保存官方原生格式；
9. 尝试 STEP 导出/重导入并记录结果；
10. 通过冻结的 STEP + semantic sidecar/binding 在 Workbench/Mechanical 完成 solver-side semantic reconstruction；不要求或暗示原生 Named Selections 传递。

本节只判定 alternate route 的 P1 CAD 工具链就绪度，不判定 P1 整机阶段 Gate。硬门槛是签名 SpaceClaim 脚本参数化、命名面、流体体积、连通、原生保存、STEP 导出/重导入、detached binding、Workbench STEP import、solver-side semantic key/cardinality/direction/owner/adjacency reconstruction 全部通过。任一项失败即 `P1_CAD_TOOLCHAIN_READINESS=BLOCKED`，不存在 transfer limitation 接受分支。正式 AirJet 整机尚未建立，所以 `P1_STAGE_GATE` 始终为 `NOT_RUN`。

### 3.1 Phase B alternate-route 语义确认

签名 runner `run_t1_alternate_route_confirmation_suite.py` 只运行
`ajm005-spaceclaim-cad-t1-v2` 与
`ajm005-workbench-semantic-reconstruction-t1-v2`。producer、consumer、fixture validator/schema、
judgment 与 route contract 必须从同一已验证 Git commit 冻结到作业依赖目录；consumer 必须对实际
STEP/native/sidecar/binding 字节、predecessor manifest、逐实体几何/方向、BODY owner、双向邻接、
唯一 cardinality 和 judgment 全部负向码进行 fail-closed 判定。

每个 runner 记录必须同时保存 `submitted`、`reached_terminal`、`capability_pass` 与
`capability_status`。只有从未提交的工作允许 `capability_status=NOT_RUN`；任何已提交或已到达终态但
identity/report/status/assertion/validation 缺失、畸形或失败的工作必须为 `FAIL`。`PASS` 仅在完整报告、
全部断言与产物身份都验证通过时成立。producer 未通过时 consumer 不得提交；consumer 失败不得抹去
producer 已证明的字段。

`PASS_ALTERNATE_ROUTE_SEMANTIC_CONFIRMATION` 只证明可删除 005 fixture 上 alternate route 工具链可用，
允许 `P1_CAD_TOOLCHAIN_READINESS=PASS` 且 scope 必须为 `ALTERNATE_ROUTE_ONLY`。它不证明 006
full-product artifacts 已建立，也不证明 formal P1 Gate；`EXTERNAL_NATIVE_ATTACH`、
`NATIVE_PARAMETERIZATION`、`NATIVE_NAMED_SELECTION_TRANSFER` 始终为 `NOT_PROVEN`，P1--P6 仍
`NOT_RUN`。connected route 保持 `DEFERRED_CURRENT_HOST_ROUTE`，不得重跑或升级其结论。

## 4. Workbench / Mechanical 烟雾测试

> Phase-B closeout override：第 4、5 节仅保留为历史 005 范围说明。冻结后的 alternate-route
> confirmation 不得执行这些 Mechanical 或 Fluent 物理测试。其技术字段必须为 `NOT_RUN`，GUI
> 字段必须为 `NOT_VISIBLE`，能力结果与 P2--P5 readiness 必须为 `NOT_EVALUATED`，P1--P6
> 必须保持 `NOT_RUN`。这些测试只能在未来独立任务与证据合同下执行。

1. 通过 GUI 或官方脚本接口确认 Static Structural、Modal、Harmonic Response、Fluid Flow (Fluent) 模板；
2. 用 `10 x 10 x 1 mm` 线弹性块完成固定端 + 小载荷的最小静力求解；
3. 确认结果表/CSV 导出；
4. 检查 Modal 与 Harmonic 入口；
5. 分开检查压电 GUI、Mechanical API、Coupled Field 或 Mechanical APDL coupled-field 路线；未观察 GUI 就写 `NOT_VISIBLE`，但若官方 API 路线经确定性小模型验证，可另写相应 API 字段 `PASS`；
6. 不测试 System Coupling，不测试 cuDSS/GPU 稀疏求解，把安装警告保留为 `UNVERIFIED_WARNING`。

## 5. Fluent 烟雾测试

按顺序、每次关闭前一会话：

1. 3D、Double Precision、1 Solver Process 启动；
2. 检查 Energy、ideal-gas/compressible、transient、dynamic mesh、smoothing/remeshing、UDF/profile、fluid-solid CHT、Watertight Geometry/Fluent Meshing；
3. 用第 3 节流体域或等价简单流道生成小网格，空气、低速/小压差入口、pressure outlet，稳态层流至少 20 iterations；
4. 记录质量不平衡、case/data 保存与正常退出；
5. 再尝试 4 Solver Processes；若成功再尝试 8，准确记录 Student 实际允许的进程数和错误；不修改授权强开；
6. 记录 GUI/日志明确显示的网格/节点/并行限制，不凭记忆填写 Student 限额。

## 6. 输出报告

保存到：

`C:\Users\admin\Downloads\AIRJET_ANSYS_STUDENT_CAPABILITY_SMOKE_005.txt`

canonical closeout 使用 `AJM005_ALTERNATE_ROUTE_CLOSEOUT_V2`，必须是 ASCII，字段集合和顺序与
`codex-skills/airjet-ansys-automation/scripts/ajm005_closeout_v2.py` 中的
`CLOSEOUT_FIELDS` 完全一致。不得省略既有 Mechanical/Fluent 字段，也不得增加笼统的
`RETAINED_SIGNED_PRIOR_EVIDENCE` 字段。技术检查统一只用 `PASS/FAIL/NOT_RUN`；GUI 可见性检查只用
`PASS/FAIL/NOT_VISIBLE`；P1--P5 readiness 只用 `PASS/LIMITED/BLOCKED/NOT_EVALUATED`。

完整字段如下：

```text
TASK=AJM-WIN-ANSYS-STUDENT-CAPABILITY-SMOKE-005
REPORT_CONTRACT=AJM005_ALTERNATE_ROUTE_CLOSEOUT_V2
COMPUTER=
ANSYS_VERSION=
INSTALL_ROOT=
GIT_COMMIT=
GIT_FETCH=PASS/FAIL/UNKNOWN
GIT_CLEAN=TRUE/FALSE/UNKNOWN
GIT_AHEAD_BEHIND=<N>_AHEAD_<N>_BEHIND/UNKNOWN
PROJECT_AUDIT=PASS/FAIL/NOT_RUN
OFFICIAL_EXE_SIGNATURES=PASS/NOT_VERIFIED
T0_CONTROLS_SOURCE_COMMIT=
T0_CONTROLS_SOURCE_PATH=
T0_CONTROLS_SOURCE_BLOB_SHA256=
T0_CONTROLS_SOURCE_VALIDATION=PASS/FAIL
T0_ENGINEERING_CAPABILITY=NOT_RUN/NOT_VERIFIED
T0_PASS_005_CAPABILITY=NOT_EVALUATED_T0_ONLY/NOT_VERIFIED
T0_P1_P6_GATES=NOT_RUN/NOT_VERIFIED
CLEANUP_SOURCE_COMMIT=
CLEANUP_SOURCE_PATH=
CLEANUP_SOURCE_BLOB_SHA256=
CLEANUP_SOURCE_VALIDATION=PASS/FAIL
OLD_PLE_BASELINE=CLEAN/NOT_VERIFIED
P0_SOURCE_COMMIT=
P0_SOURCE_PATH=
P0_SOURCE_BLOB_SHA256=
P0_SOURCE_VALIDATION=PASS/FAIL
EXECUTION_ROUTE=OFFICIAL_API
VISIBILITY=NOT_USER_OBSERVED
SPACECLAIM_AUTOMATION_CONTROL=PASS/FAIL/NOT_RUN
WORKBENCH_AUTOMATION_CONTROL=PASS/FAIL/NOT_RUN
PYMECHANICAL_CONTROL=PASS/FAIL/NOT_RUN
PYFLUENT_CONTROL=PASS/FAIL/NOT_RUN
SPACECLAIM_LAUNCH=PASS/FAIL/NOT_RUN
PARAMETRIC_GEOMETRY=PASS/FAIL/NOT_RUN
NAMED_SELECTIONS=PASS/FAIL/NOT_RUN
VOLUME_EXTRACT=PASS/FAIL/NOT_RUN
FLUID_CONNECTIVITY=PASS/FAIL/NOT_RUN
NATIVE_SAVE=PASS/FAIL/NOT_RUN
STEP_EXPORT_REIMPORT=PASS/FAIL/NOT_RUN
WORKBENCH_STEP_IMPORT=PASS/FAIL/NOT_RUN
SOLVER_SEMANTIC_RECONSTRUCTION=PASS/FAIL/NOT_RUN
SEMANTIC_KEY_CARDINALITY_CHECK=PASS/FAIL/NOT_RUN
CAD_AUTHORING_ROUTE=SPACECLAIM_SIGNED_SCRIPT_PARAMETRIC
SOLVER_HANDOFF_ROUTE=HASH_BOUND_STEP_SEMANTIC_SIDECAR
CONNECTED_ROUTE=DEFERRED_CURRENT_HOST_ROUTE
EXTERNAL_NATIVE_ATTACH=NOT_PROVEN
NATIVE_PARAMETERIZATION=NOT_PROVEN
NATIVE_NAMED_SELECTION_TRANSFER=NOT_PROVEN
STATIC_STRUCTURAL_SOLVE=PASS/FAIL/NOT_RUN
MODAL_VISIBLE=PASS/FAIL/NOT_VISIBLE
HARMONIC_VISIBLE=PASS/FAIL/NOT_VISIBLE
PIEZOELECTRIC_GUI_ROUTE=PASS/FAIL/NOT_VISIBLE
MODAL_API_ROUTE=PASS/FAIL/NOT_RUN
HARMONIC_API_ROUTE=PASS/FAIL/NOT_RUN
PIEZOELECTRIC_API_ROUTE=PASS/FAIL/NOT_RUN
APDL_COUPLED_FIELD_ROUTE=PASS/FAIL/NOT_RUN
RESULT_TABLE_EXPORT=PASS/FAIL/NOT_RUN
SYSTEM_COUPLING_STATUS=UNVERIFIED_WARNING
CUDSS_STATUS=UNVERIFIED_WARNING
MECHANICAL_CAPABILITY_RESULT=NOT_EVALUATED
FLUENT_1_CORE=PASS/FAIL/NOT_RUN
FLUENT_4_CORE=PASS/FAIL/NOT_RUN
FLUENT_8_CORE=PASS/FAIL/NOT_RUN
FLUENT_REPORTED_PROCESS_COUNT=NOT_EVALUATED
ENERGY=PASS/FAIL/NOT_RUN
IDEAL_GAS_COMPRESSIBLE=PASS/FAIL/NOT_RUN
TRANSIENT=PASS/FAIL/NOT_RUN
DYNAMIC_MESH=PASS/FAIL/NOT_RUN
SMOOTHING_REMESHING=PASS/FAIL/NOT_RUN
UDF_OR_PROFILE=PASS/FAIL/NOT_RUN
CHT_FLUID_SOLID=PASS/FAIL/NOT_RUN
WATERTIGHT_MESHING=PASS/FAIL/NOT_RUN
MINIMAL_FLOW_SOLVE=PASS/FAIL/NOT_RUN
MINIMAL_FLOW_MASS_BALANCE=NOT_EVALUATED
OBSERVED_STUDENT_LIMITS=NOT_EVALUATED
FLUENT_CAPABILITY_RESULT=NOT_EVALUATED
P0_STAGE_GATE=PASS/NOT_VERIFIED
P1_STAGE_GATE=NOT_RUN
P2_STAGE_GATE=NOT_RUN
P3_STAGE_GATE=NOT_RUN
P4_STAGE_GATE=NOT_RUN
P5_STAGE_GATE=NOT_RUN
P6_STAGE_GATE=NOT_RUN
P1_CAD_TOOLCHAIN_SCOPE=ALTERNATE_ROUTE_ONLY
P1_CAD_TOOLCHAIN_READINESS=PASS/BLOCKED
P2_STRUCTURAL_TOOLCHAIN_READINESS=PASS/LIMITED/BLOCKED/NOT_EVALUATED
P3_TRANSIENT_CFD_TOOLCHAIN_READINESS=PASS/LIMITED/BLOCKED/NOT_EVALUATED
P4_AIRFLOW_LOCAL_DEBUG_READINESS=PASS/LIMITED/BLOCKED/NOT_EVALUATED
P5_CHT_LOCAL_DEBUG_READINESS=PASS/LIMITED/BLOCKED/NOT_EVALUATED
SUITE_STATUS=
SUITE_RESULT_PATH=
SUITE_RESULT_SHA256=
PRODUCER_REPORT_SHA256=
CONSUMER_REPORT_SHA256=
STEP_SHA256=
ERROR_MESSAGES=
FINAL_TECHNICAL_RECOMMENDATION=
STUDENT_TOOLCHAIN_STATUS=PASS_START_P1/BLOCKED_TECHNICAL_FAILURE
```

T0、cleanup 和 P0 的 `PASS` 只能分别继承自以下祖先 commit 的严格 UTF-8 Git blob；runner
必须先验证 ancestor、精确路径、原始 blob SHA256 和精确状态 marker，并把 source commit/path/blob
SHA 写入报告：

```text
T0_CONTROLS_SOURCE_COMMIT=92712c7d63f44e1ccafb7a58e8386708b591b287
T0_CONTROLS_SOURCE_BLOB_SHA256=9ee6a41ca50561e6427950e84e38d9bf039d0b37f090fc0c76c93253cea6891d
CLEANUP_SOURCE_COMMIT=7a93eaa9c8b6c13b5a4f5f03ae2b401945c6b1f8
CLEANUP_SOURCE_BLOB_SHA256=1d1087664d3fecc43164dcce2084f8ba3c678da73005fa73def69375900d1f13
P0_SOURCE_COMMIT=59e0a296b47f2984606720ec16cf315a0852e625
P0_SOURCE_BLOB_SHA256=a1a93e1c5e8728e949110c05994b3b1f712a17f7b8889afd10c81e6de9d66456
```

判定规则：

- `PASS_START_P1`：仅表示上述 alternate-route P1 CAD 工具链合同全部通过，允许开始 006；不表示 006/007、P1 Gate 或 P2--P5 已通过。GUI 或官方 API 均可提供技术证据，但 `VISIBILITY` 不得由无头结果代填。
- `BLOCKED_TECHNICAL_FAILURE`：preflight、signed source 或任一 P1 工具链必要项失败。失败报告不得硬编码 clean、0/0 或 PASS；不可用事实写 `UNKNOWN`/`NOT_VERIFIED`，P1 readiness 必须为 `BLOCKED`。

无论最终状态如何，本任务都必须写 `P1_STAGE_GATE=NOT_RUN`；只有后续正式整机 CAD 通过完整 P1 Gate 后才能改变。

完成后停止，保留临时文件，不创建正式 AirJet CAD，等待独立 peer 复核；复核角色不绑定 Mac 或 Windows。
