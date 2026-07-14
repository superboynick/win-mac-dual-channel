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
10. 尝试把原生几何传入 Workbench Geometry/Meshing，记录 Named Selections 是否保留。

本节只判定 P1 CAD 工具链就绪度，不判定 P1 整机阶段 Gate。开始正式 P1 的工具链硬门槛是原生参数化、命名面、流体体积、连通、原生保存、Workbench/网格传递以及 Named Selections 传递全部通过。STEP 是重要交接能力，但不是唯一硬门槛；STEP 失败而上述必要项全部通过时写 `P1_CAD_TOOLCHAIN_READINESS=PASS_WITH_TRANSFER_LIMITATION`。正式 AirJet 整机尚未建立，所以 `P1_STAGE_GATE` 始终为 `NOT_RUN`。

## 4. Workbench / Mechanical 烟雾测试

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

至少包含：

```text
TASK=AJM-WIN-ANSYS-STUDENT-CAPABILITY-SMOKE-005
COMPUTER=
ANSYS_VERSION=
INSTALL_ROOT=
GIT_COMMIT=
GIT_FETCH=PASS/FAIL
GIT_CLEAN=
GIT_AHEAD_BEHIND=
PROJECT_AUDIT=
OFFICIAL_EXE_SIGNATURES=
OLD_PLE_BASELINE=CLEAN/CONTAMINATED
EXECUTION_ROUTE=GUI/OFFICIAL_API/MIXED
VISIBILITY=USER_OBSERVED/NOT_USER_OBSERVED
SPACECLAIM_AUTOMATION_CONTROL=PASS/FAIL/NOT_RUN
WORKBENCH_AUTOMATION_CONTROL=PASS/FAIL/NOT_RUN
PYMECHANICAL_CONTROL=PASS/FAIL/NOT_RUN
PYFLUENT_CONTROL=PASS/FAIL/NOT_RUN

SPACECLAIM_LAUNCH=PASS/FAIL
PARAMETRIC_GEOMETRY=PASS/FAIL
NAMED_SELECTIONS=PASS/FAIL
VOLUME_EXTRACT=PASS/FAIL
FLUID_CONNECTIVITY=PASS/FAIL
NATIVE_SAVE=PASS/FAIL
STEP_EXPORT_REIMPORT=PASS/FAIL
WORKBENCH_GEOMETRY_TRANSFER=PASS/FAIL
NAMED_SELECTION_TRANSFER=PASS/FAIL

STATIC_STRUCTURAL_SOLVE=PASS/FAIL
MODAL_VISIBLE=PASS/FAIL/NOT_VISIBLE
HARMONIC_VISIBLE=PASS/FAIL/NOT_VISIBLE
PIEZOELECTRIC_GUI_ROUTE=PASS/FAIL/NOT_VISIBLE
MODAL_API_ROUTE=PASS/FAIL/NOT_RUN
HARMONIC_API_ROUTE=PASS/FAIL/NOT_RUN
PIEZOELECTRIC_API_ROUTE=PASS/FAIL/NOT_RUN
APDL_COUPLED_FIELD_ROUTE=PASS/FAIL/NOT_CHECKED
RESULT_TABLE_EXPORT=PASS/FAIL
SYSTEM_COUPLING_STATUS=UNVERIFIED_WARNING
CUDSS_STATUS=UNVERIFIED_WARNING

FLUENT_1_CORE=PASS/FAIL
FLUENT_4_CORE=PASS/FAIL
FLUENT_8_CORE=PASS/FAIL/NOT_ATTEMPTED
FLUENT_REPORTED_PROCESS_COUNT=
ENERGY=PASS/FAIL
IDEAL_GAS_COMPRESSIBLE=PASS/FAIL
TRANSIENT=PASS/FAIL
DYNAMIC_MESH=PASS/FAIL
SMOOTHING_REMESHING=PASS/FAIL
UDF_OR_PROFILE=PASS/FAIL
CHT_FLUID_SOLID=PASS/FAIL
WATERTIGHT_MESHING=PASS/FAIL
MINIMAL_FLOW_SOLVE=PASS/FAIL
MINIMAL_FLOW_MASS_BALANCE=
OBSERVED_STUDENT_LIMITS=

P0_STAGE_GATE=PASS
P1_STAGE_GATE=NOT_RUN
P2_STAGE_GATE=NOT_RUN
P3_STAGE_GATE=NOT_RUN
P4_STAGE_GATE=NOT_RUN
P5_STAGE_GATE=NOT_RUN
P6_STAGE_GATE=NOT_RUN
P1_CAD_TOOLCHAIN_READINESS=PASS/PASS_WITH_TRANSFER_LIMITATION/BLOCKED
P2_STRUCTURAL_TOOLCHAIN_READINESS=PASS/LIMITED/BLOCKED
P3_TRANSIENT_CFD_TOOLCHAIN_READINESS=PASS/LIMITED/BLOCKED
P4_AIRFLOW_LOCAL_DEBUG_READINESS=PASS/LIMITED/BLOCKED
P5_CHT_LOCAL_DEBUG_READINESS=PASS/LIMITED/BLOCKED
ERROR_MESSAGES=
FINAL_TECHNICAL_RECOMMENDATION=
```

最终状态只能选一个：

```text
STUDENT_TOOLCHAIN_STATUS=PASS_START_P1
STUDENT_TOOLCHAIN_STATUS=PASS_START_P1_WITH_LIMITATIONS
STUDENT_TOOLCHAIN_STATUS=BLOCKED_TECHNICAL_FAILURE
STUDENT_TOOLCHAIN_STATUS=BLOCKED_CONTAMINATED_BASELINE
```

判定规则：

- `PASS_START_P1`：P1 工具链全部必要项（原生参数化、Named Selections、Volume Extract、连通、原生保存、Workbench 几何传递、Named Selections 传递）以及 STEP、Mechanical 最小求解/导出、至少一条经实际小模型验证的压电路线、Fluent 全部模型检查、最小流动求解和 1/4/8 核测试均通过，且没有观察到阻塞计划路线的 Student 限制。GUI 或官方 API 均可提供技术证据，但 `VISIBLE` 字段不得由无头结果代填。
- `PASS_START_P1_WITH_LIMITATIONS`：P1 工具链全部必要项通过，但 STEP 或 P2--P5/并行中的至少一项失败、受限或未验证；必须把限制映射到相应后续阶段。
- `BLOCKED_TECHNICAL_FAILURE`：Git/fetch/audit 失败，或任一 P1 工具链必要项失败。此时不得开始正式 P1。
- `BLOCKED_CONTAMINATED_BASELINE`：旧 PLE/1055/已知污染环境变量重新出现。

无论最终状态如何，本任务都必须写 `P1_STAGE_GATE=NOT_RUN`；只有后续正式整机 CAD 通过完整 P1 Gate 后才能改变。

完成后停止，保留临时文件，不创建正式 AirJet CAD，等待独立 peer 复核；复核角色不绑定 Mac 或 Windows。
