# Windows Codex 任务：AJM-WIN-ANSYS-CAPABILITY-SMOKE-003

你现在位于 Windows 电脑 `LAPTOP-LCCLM2HI` 的可见桌面。把现有 Ansys 2026 R1 当作已经安装好的工程软件，只验证它的**实际技术能力**是否覆盖 AirJet Mini 项目的建模与仿真需求。

仓库：

`C:\Users\admin\win-mac-dual-channel`

本轮不判断许可证来源，不讨论正版/盗版，不修改任何许可证相关设置。不要创建正式 AirJet CAD；只做可删除的最小烟雾测试。

## 1. 严格边界

1. 不打开、读取、修改、停止或替换许可证文件、许可证服务、注册表或授权环境变量。
2. 不运行激活、修复、补丁、破解器或许可证生成器。
3. 正常启动和使用已经安装的 Discovery、SpaceClaim、Workbench、Mechanical、Mechanical APDL 和 Fluent。
4. 所有临时测试文件只放在：
   `C:\Users\admin\Downloads\AIRJET_ANSYS_SMOKE_003\`
5. 不修改、提交或推送 Git 仓库。
6. 如果不能直接观察或操作 GUI，必须让用户确认屏幕内容；不能仅凭后台进程存在就判定 GUI 功能 `PASS`。
7. 测试失败时记录原始错误，不修许可证，不反复盲试。

## 2. Git 与项目基线

先执行：

```powershell
cd C:\Users\admin\win-mac-dual-channel
git status --short --branch
git status --porcelain
git rev-parse HEAD
git rev-list --left-right --count HEAD...origin/main
powershell -ExecutionPolicy Bypass -File .\audit-airjet-project.ps1
```

要求：

- branch=`main`；
- 工作树干净；
- ahead/behind=`0/0`；
- 项目审计 `PASS`。

任一不符时只写报告并停止，不合并、不重置、不覆盖。

## 3. 建立临时测试目录

```powershell
$Smoke = 'C:\Users\admin\Downloads\AIRJET_ANSYS_SMOKE_003'
New-Item -ItemType Directory -Force $Smoke | Out-Null
```

测试结束后暂时保留该目录，供 Mac 端复核；不要放入 Git。

## 4. CAD 技术能力测试

### 4.1 SpaceClaim/Discovery 基础参数化几何

在可见 GUI 中完成一个最小流道测试件：

1. 建立 `20 mm x 10 mm x 4 mm` 外部块体；
2. 在内部建立 `16 mm x 6 mm x 2 mm` 腔体；
3. 建立一个直径 `2 mm` 的圆柱入口和一个 `4 mm x 1 mm` 的矩形出口；
4. 确认入口—腔体—出口几何连通；
5. 对关键尺寸建立 driving dimensions 或等价参数；
6. 建立命名选择：`INLET`、`OUTLET`、`WALLS`；
7. 使用 `Volume Extract` 或等价功能提取内部流体体积；
8. 检查内部流体只有一个连续体，没有孤立体或盲孔。

保存原生测试模型到：

`C:\Users\admin\Downloads\AIRJET_ANSYS_SMOKE_003\cad_smoke_native.scdoc`

如果实际原生扩展名不同，记录真实扩展名。

### 4.2 STEP 导出能力

尝试把同一测试几何导出为：

`C:\Users\admin\Downloads\AIRJET_ANSYS_SMOKE_003\cad_smoke.step`

只记录：

- 导出菜单是否可用；
- 文件是否实际生成；
- 文件大小是否大于 0；
- 重新导入后实体数是否合理。

不得通过第三方转换器绕过软件自身限制。

## 5. Workbench 与 Mechanical 技术能力测试

### 5.1 Workbench

确认 Toolbox 至少存在：

- `Static Structural`；
- `Modal`；
- `Harmonic Response`；
- `Fluid Flow (Fluent)`；
- `Coupled Field Static`、`Coupled Field Harmonic` 或可完成压电耦合的等价系统；若没有，记录为 `NOT_VISIBLE`，不要猜测。

### 5.2 最小结构求解

使用一个 `10 mm x 10 mm x 1 mm` 固体完成最小 Static Structural 测试：

1. 赋予常用线弹性材料；
2. 一端固定；
3. 另一端施加一个小载荷；
4. 生成小网格；
5. 求解位移；
6. 确认 Solution 为正常完成。

保存到临时目录，不放入 Git。

### 5.3 AirJet P2 所需功能检查

只检查功能是否存在，不建立正式膜片：

- Modal analysis；
- Harmonic response；
- 薄层/层合或等效材料设置；
- 压电/电—结构耦合入口或 Mechanical APDL coupled-field 路线；
- 结果导出为 CSV/table；
- 可供 Fluent 使用的位移—时间表导出路线。

若 GUI 没有直接压电入口，但 Mechanical APDL 具有 coupled-field 元素/分析路线，分别记录，不把两者混为一项。

## 6. Fluent 技术能力测试

### 6.1 单核正常启动

启动：

- 3D；
- Double Precision；
- 1 Solver Process。

确认能够进入 Fluent 并看到：

- General；
- Models；
- Materials；
- Cell Zone Conditions；
- Boundary Conditions；
- Solution Methods；
- Run Calculation。

### 6.2 AirJet P3–P5 必需模型检查

只检查功能入口是否存在并可选择，不建立正式算例：

- Energy equation；
- ideal-gas/compressible air；
- transient solver；
- dynamic mesh；
- smoothing/remeshing 或等价动态网格方法；
- User-Defined Functions 或 profile/table 边界入口；
- conjugate heat transfer 所需的 fluid + solid cell zones；
- periodic/time-history monitor 与数据导出；
- Fluent Meshing 或 Watertight Geometry workflow。

### 6.3 最小流动求解

使用 CAD 烟雾测试流体域或 Fluent 自建的等价简单流道：

1. 生成小网格；
2. 空气，常温；
3. 入口设置低速或小压差；
4. 出口 pressure outlet；
5. 先用稳态层流运行至少 20 iterations；
6. 确认质量不平衡可收敛到合理量级；
7. 保存 case/data 到临时目录。

这只验证工具链，不代表 AirJet 物理模型。

### 6.4 8 核启动能力

在关闭前一个 Fluent 会话后，从正常 Fluent Launcher 或官方命令行尝试：

- 3D；
- Double Precision；
- 8 Solver Processes。

只判断是否能正常进入 Fluent 并完成计算进程初始化。成功后立即正常退出，不运行大算例。

不得修改许可证设置来强行开启 8 核。

记录：

```text
FLUENT_8_CORE_START=PASS/FAIL
FLUENT_REPORTED_PROCESS_COUNT=
FLUENT_8_CORE_ERROR=
```

## 7. 能力分类

这里只分类实际观察到的功能，不分类许可证合法性或名称。

### `STUDENT_LIKE_LIMITS_OBSERVED`

满足以下主要特征：

- 软件自身 STEP 导出不可用；并且
- Fluent 8 核启动被限制到 4 核或失败；或 GUI 明确显示 Student 规模限制。

### `ABOVE_STUDENT_CAPABILITY_OBSERVED`

至少同时满足：

- STEP 导出成功并可重新导入；
- Fluent 以 8 solver processes 正常初始化；
- Mechanical、Fluent 关键模块均可正常启动。

这只表示观察到的技术能力高于官方 Student 的典型限制，不代表最终算例一定适合本机运行。

### `CAPABILITY_INDETERMINATE`

证据混合、GUI 无法验证、测试流程本身失败或只能确认部分模块时使用。

## 8. 对 AirJet 各阶段的实际判定

分别输出：

- `P1_FULL_PRODUCT_CAD`：需要参数化几何、Named Selections、Volume Extract、流体连通和原生保存；STEP 导出不是唯一硬门槛，但成功更利于交接。
- `P2_ACTUATOR_STRUCTURAL`：需要 Modal、Harmonic、压电或 coupled-field 路线、位移表导出。
- `P3_CELL_TRANSIENT_CFD`：需要 transient、compressible/ideal-gas、dynamic mesh、profile/UDF、周期监视。
- `P4_FULL_PRODUCT_AIRFLOW_LOCAL_DEBUG`：需要完整 Fluent 功能和并行；本机 32 GiB 只评估粗网格/流程调试，不承诺 5–80M 网格生产算例。
- `P5_CHT_LOCAL_DEBUG`：需要 Energy 与 fluid-solid CHT；本机只评估粗网格/流程调试，不承诺 10–40M 网格生产算例。

对每项写 `PASS`、`LIMITED` 或 `BLOCKED`，并给出一句技术原因。

## 9. 输出报告

保存到：

`C:\Users\admin\Downloads\AIRJET_ANSYS_CAPABILITY_SMOKE_003.txt`

报告必须包含：

```text
TASK=AJM-WIN-ANSYS-CAPABILITY-SMOKE-003
COMPUTER=
ANSYS_VERSION=
INSTALL_ROOT=
GIT_COMMIT=
GIT_CLEAN=PASS/FAIL
GIT_AHEAD_BEHIND=
PROJECT_AUDIT=PASS/FAIL

SPACECLAIM_OR_DISCOVERY_LAUNCH=PASS/FAIL
PARAMETRIC_GEOMETRY=PASS/FAIL
NAMED_SELECTIONS=PASS/FAIL
VOLUME_EXTRACT=PASS/FAIL
FLUID_CONNECTIVITY_CHECK=PASS/FAIL
NATIVE_CAD_SAVE=PASS/FAIL
STEP_EXPORT=PASS/FAIL
STEP_REIMPORT=PASS/FAIL

WORKBENCH_LAUNCH=PASS/FAIL
STATIC_STRUCTURAL_SOLVE=PASS/FAIL
MODAL_VISIBLE=PASS/FAIL
HARMONIC_VISIBLE=PASS/FAIL
PIEZOELECTRIC_GUI_ROUTE=PASS/FAIL/NOT_VISIBLE
MECHANICAL_APDL_COUPLED_FIELD_ROUTE=PASS/FAIL/NOT_CHECKED
DISPLACEMENT_TABLE_EXPORT_ROUTE=PASS/FAIL

FLUENT_1_CORE_START=PASS/FAIL
FLUENT_8_CORE_START=PASS/FAIL
FLUENT_REPORTED_PROCESS_COUNT=
FLUENT_8_CORE_ERROR=
ENERGY_MODEL=PASS/FAIL
IDEAL_GAS_COMPRESSIBLE=PASS/FAIL
TRANSIENT_SOLVER=PASS/FAIL
DYNAMIC_MESH=PASS/FAIL
SMOOTHING_REMESHING=PASS/FAIL
UDF_OR_PROFILE_ROUTE=PASS/FAIL
CHT_FLUID_SOLID_ROUTE=PASS/FAIL
WATERTIGHT_MESHING_ROUTE=PASS/FAIL
MINIMAL_FLOW_SOLVE=PASS/FAIL
MINIMAL_FLOW_MASS_BALANCE=

CAPABILITY_CLASS=STUDENT_LIKE_LIMITS_OBSERVED/ABOVE_STUDENT_CAPABILITY_OBSERVED/CAPABILITY_INDETERMINATE
P1_FULL_PRODUCT_CAD=PASS/LIMITED/BLOCKED
P1_REASON=
P2_ACTUATOR_STRUCTURAL=PASS/LIMITED/BLOCKED
P2_REASON=
P3_CELL_TRANSIENT_CFD=PASS/LIMITED/BLOCKED
P3_REASON=
P4_FULL_PRODUCT_AIRFLOW_LOCAL_DEBUG=PASS/LIMITED/BLOCKED
P4_REASON=
P5_CHT_LOCAL_DEBUG=PASS/LIMITED/BLOCKED
P5_REASON=

ERROR_MESSAGES=
FINAL_TECHNICAL_RECOMMENDATION=
```

最终状态只能选一项：

```text
SMOKE_STATUS=PASS_START_P1
SMOKE_STATUS=LIMITED_START_P1_WITH_RESTRICTIONS
SMOKE_STATUS=BLOCKED_TECHNICAL_FAILURE
```

## 10. 完成后停止

1. 在可见 Codex 窗口输出报告摘要；
2. 告诉用户报告路径；
3. 保留临时烟雾测试文件供复核；
4. 不开始正式 AirJet CAD；
5. 不修改 Git；
6. 等待下一条明确指令。
