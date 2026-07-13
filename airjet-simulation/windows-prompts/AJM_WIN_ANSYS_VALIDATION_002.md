# Windows Codex 任务：AJM-WIN-ANSYS-VALIDATION-002

你现在位于 Windows 电脑 `LAPTOP-LCCLM2HI` 的可见桌面，负责验证新安装的 Ansys 2026 R1 是否能用于 AirJet Mini 整机仿真项目。

仓库：

`C:\Users\admin\win-mac-dual-channel`

本轮只做**许可证、CAD、Mechanical、Fluent 工具链验收**。不要创建正式 AirJet CAD，不要修改或提交 Git。

## 1. 严格边界

1. 不修改、停止、重启或替换许可证服务。
2. 不修改 `ANSYSLMD_LICENSE_FILE`、注册表或系统环境变量。
3. 不运行任何激活、修复、补丁、破解器或许可证生成器。
4. 不输出许可证密钥、Host ID、序列号或许可证文件内容。
5. 不修改、提交或推送 Git 仓库。
6. 允许创建不保存的临时空白模型，只用于许可证 checkout 和功能验证。
7. 如果你不能直接观察或操作 GUI，必须明确请求用户确认屏幕内容；不能仅凭后台存在进程就判定 `PASS`。
8. 发现许可证来源无法确认时，只记录并停止，不自行解决。

## 2. 先核对项目与 Git

在仓库执行：

```powershell
cd C:\Users\admin\win-mac-dual-channel
git status --short --branch
git status --porcelain
git rev-parse HEAD
git rev-list --left-right --count HEAD...origin/main
powershell -ExecutionPolicy Bypass -File .\audit-airjet-project.ps1
```

要求：

- 分支为 `main`；
- 工作树干净；
- ahead/behind 为 `0/0`；
- 项目审计 `PASS`。

如果 Git 不干净或分叉，记录问题，但不要修改、合并、重置或覆盖。

## 3. 核验已知安装

已知安装位置：

`D:\Ansys\2026R1\ANSYS Inc\v261`

已知模块：

- Workbench 2026 R1
- Mechanical 2026 R1
- Discovery 2026 R1
- SpaceClaim 2026 R1
- Fluent 2026 R1

已知许可证环境：

`ANSYSLMD_LICENSE_FILE=1055@localhost`

已发现服务：

`Ansys PLE Licensing 2026 R1`

Windows 注册表显示该许可证服务发布者为：

`www.mr-wu.cn`

不要预先假设这是官方 Student、Academic 或 Commercial 许可证。程序二进制具有有效 `ANSYS Inc.` 签名，也不能单独证明许可证类别或来源。

## 4. 可见 GUI 验证

### A. Ansys Licensing Settings

打开：

`D:\Ansys\2026R1\ANSYS Inc\v261\licensingclient\winx64\LicensingSettings.exe`

只查看并记录：

- 软件显示的许可证产品名称；
- Student / Academic Teaching / Academic Research / Commercial / Trial / 其他；
- 是否明确显示许可证有效；
- 是否显示到期时间；
- 是否存在错误。

不要记录许可证密钥、Host ID 或序列号。

### B. Workbench

打开 Workbench 2026 R1，确认：

- 主界面正常进入；
- Toolbox 中存在 `Static Structural`；
- Toolbox 中存在 `Fluid Flow (Fluent)`；
- 没有许可证错误。

不保存项目。

### C. Discovery

打开 Discovery 2026 R1：

1. 新建空白文档；
2. 临时建立一个 `10 mm x 10 mm x 1 mm` 长方体；
3. 确认建模、参数尺寸和结构树正常；
4. 确认没有许可证错误；
5. 不保存并关闭。

### D. SpaceClaim

打开 SpaceClaim 2026 R1：

1. 新建空白文档；
2. 临时建立一个 `10 mm x 10 mm x 1 mm` 长方体；
3. 检查 `Design`、`Prepare`、`Named Selection`、`Volume Extract` 是否可用；
4. 确认没有许可证错误；
5. 不保存并关闭。

### E. Mechanical

在 Workbench 中：

1. 新建空白 `Static Structural` 系统；
2. 打开 `Model/Mechanical`；
3. 确认 Mechanical 成功进入界面并完成许可证 checkout；
4. 不创建正式几何、不求解、不保存。

### F. Fluent

从 Workbench 或 Fluent Launcher 启动：

- `3D`；
- `Double Precision`；
- `1 Solver Process`。

确认：

- Fluent 能进入界面或控制台；
- 没有 license checkout error；
- 能看到 `General`、`Models`、`Materials` 等基础设置。

不读取网格、不求解、不保存，然后正常退出。

## 5. 许可证分类规则

只按实际界面证据分类。

### 官方 Student

```text
LICENSE_SOURCE_CLASS=OFFICIAL_STUDENT
AIRJET_CAPABILITY=P1_CAD_AND_COARSE_MODELS_ONLY
```

说明最终整机高保真 P4/P5 预计仍需要 Academic Research。

### 官方 Academic Teaching

```text
LICENSE_SOURCE_CLASS=OFFICIAL_ACADEMIC_TEACHING
AIRJET_CAPABILITY=TEACHING_AND_PRELIMINARY_MODELS_ONLY
```

### 官方 Academic Research

```text
LICENSE_SOURCE_CLASS=OFFICIAL_ACADEMIC_RESEARCH
AIRJET_CAPABILITY=FULL_RESEARCH_PIPELINE_CANDIDATE
```

### 官方 Commercial

```text
LICENSE_SOURCE_CLASS=OFFICIAL_COMMERCIAL
AIRJET_CAPABILITY=FULL_RESEARCH_PIPELINE_CANDIDATE
```

### 第三方或无法确认

如果只看到第三方 PLE、本地 `1055@localhost` 服务，无法从 Ansys 界面证明官方类别：

```text
LICENSE_SOURCE_CLASS=THIRD_PARTY_OR_UNVERIFIED
AIRJET_CAPABILITY=BLOCKED_PENDING_LICENSE_CLARIFICATION
```

不能因为程序能启动，就自动判定许可证官方或适合论文。

## 6. 输出报告

保存到：

`C:\Users\admin\Downloads\AIRJET_ANSYS_LICENSE_VALIDATION.txt`

报告必须包含：

```text
TASK=AJM-WIN-ANSYS-VALIDATION-002
COMPUTER=
ANSYS_VERSION=
INSTALL_ROOT=
GIT_COMMIT=
GIT_CLEAN=PASS/FAIL
GIT_AHEAD_BEHIND=
PROJECT_AUDIT=PASS/FAIL

LICENSE_DISPLAY_NAME=
LICENSE_SOURCE_CLASS=
LICENSE_EXPIRY=
LICENSE_SOURCE_REASON=
LICENSE_ERROR=

WORKBENCH_LAUNCH=PASS/FAIL
STATIC_STRUCTURAL_VISIBLE=PASS/FAIL
FLUENT_SYSTEM_VISIBLE=PASS/FAIL
DISCOVERY_LAUNCH=PASS/FAIL
DISCOVERY_BASIC_MODEL=PASS/FAIL
SPACECLAIM_LAUNCH=PASS/FAIL
SPACECLAIM_BASIC_MODEL=PASS/FAIL
NAMED_SELECTION_VISIBLE=PASS/FAIL
VOLUME_EXTRACT_VISIBLE=PASS/FAIL
MECHANICAL_LICENSE_CHECKOUT=PASS/FAIL
FLUENT_LICENSE_CHECKOUT=PASS/FAIL

DISPLAYED_NODE_CELL_LIMITS=
DISPLAYED_CPU_CORE_LIMIT=
GEOMETRY_EXPORT_AVAILABLE=
ERROR_MESSAGES=

AIRJET_CAPABILITY=
P1_CAD_STATUS=READY/BLOCKED
FINAL_RECOMMENDATION=
```

最终状态只能从以下三项中选择一个：

```text
VALIDATION_STATUS=PASS_OFFICIAL_RESEARCH_OR_COMMERCIAL
VALIDATION_STATUS=PASS_OFFICIAL_STUDENT_OR_TEACHING_LIMITED
VALIDATION_STATUS=BLOCKED_LICENSE_OR_MODULE
```

## 7. 完成后停止

1. 在窗口里输出完整结论；
2. 告诉用户报告文件路径；
3. 不开始 AirJet CAD；
4. 不修改 Git；
5. 等待下一条明确指令。
