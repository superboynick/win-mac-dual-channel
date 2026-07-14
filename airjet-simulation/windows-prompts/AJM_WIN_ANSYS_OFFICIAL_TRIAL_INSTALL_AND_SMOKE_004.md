# Windows Codex 任务：AJM-WIN-ANSYS-OFFICIAL-TRIAL-INSTALL-AND-SMOKE-004

仅在用户明确确认已经收到 Ansys 官方 Welcome/entitlement/试用开通邮件，并且可以从 Ansys Customer Center 下载官方安装包后执行。**提交申请或收到自动回执不等于试用已开通。**

目标机器：`LAPTOP-LCCLM2HI`
仓库：`C:\Users\admin\win-mac-dual-channel`

本任务目标是按 Ansys 官方邮件和安装器安装官方 30 天试用，并验证 AirJet Mini P1--P5 所需功能。不得猜测服务器、PIN、Host ID、产品代码或 entitlement；不得把授权信息写入 Git 或报告。

## 0. 停止条件

遇到以下任一情况，写报告并停止：

- 用户只有申请回执，没有官方下载/entitlement 权限；
- 安装包不是从 Ansys 官方 Customer Center 获得；
- 实际执行的 `setup.exe` 或 `AnsysInstaller.exe` Authenticode 签名不是有效的 Ansys/Synopsys 官方签名；
- Git 工作树不干净或与 `origin/main` 分叉；
- 官方邮件要求销售或支持人员完成尚未完成的配置；
- 需要卸载现有软件但用户尚未在当前窗口明确同意；
- 需要输入许可证文件、服务器、PIN、账号验证码时用户不在场。

不要绕过任何停止条件，不运行补丁、破解器、许可证生成器或第三方激活程序。

## 1. Git 与项目基线

```powershell
cd C:\Users\admin\win-mac-dual-channel
git status --short --branch
git status --porcelain
git fetch origin
git rev-list --left-right --count HEAD...origin/main
powershell -ExecutionPolicy Bypass -File .\audit-airjet-project.ps1
```

要求 `main`、工作树干净、ahead/behind=`0/0`、项目审计 `PASS`。本任务不修改、提交或推送 Git。

阅读：

1. `airjet-simulation/reports/AJM_WIN_ANSYS_CAPABILITY_SMOKE_003_SUMMARY.md`
2. `airjet-simulation/WINDOWS_ENVIRONMENT_REPORT.md`
3. `airjet-simulation/manuals/01_FULL_PRODUCT_CAD.md`
4. `airjet-simulation/manuals/02_ACTUATOR_STRUCTURAL.md`
5. `airjet-simulation/manuals/03_CELL_TRANSIENT_CFD.md`
6. `airjet-simulation/manuals/04_FULL_PRODUCT_AIRFLOW.md`
7. `airjet-simulation/manuals/05_FULL_PRODUCT_CHT.md`

## 2. 官方开通证据：只看状态，不复制敏感值

由用户在可见浏览器中登录官方 Ansys Account/Customer Center。确认并只记录：

- 官方试用是否显示 active；
- 产品名称；
- 开始/到期日期；
- 是否有 Windows x64 官方下载权限；
- 是否覆盖 Fluent、Mechanical、3D Design/Geometry 中的哪些项目；
- 是否提供 Cloud Burst/Elastic 权限。

不得在终端、Codex 输出、截图文件名或 Git 中显示账号密码、验证码、license server PIN、license 文件正文、Host ID 或 entitlement ID。禁止截取含这些信息的页面内容；若必须保存功能证据，先裁剪或遮挡所有账号、entitlement、Host ID、服务器和 PIN。

## 3. 官方安装包验证

用户从官方 Customer Center 下载后，将原始下载包保留在 Downloads。官方路线可能是 ZIP/ISO/多分卷中的 `setup.exe`，也可能是官方自动安装器 `AnsysInstaller.exe`。容器本身可能没有 Authenticode；先记录每个原始文件的来源、大小和 SHA256，再对实际运行的官方 EXE 检查签名：

```powershell
Get-Item '<用户实际下载的官方安装包路径>' | Select-Object FullName,Length,LastWriteTime
Get-FileHash '<用户实际下载的官方安装包路径>' -Algorithm SHA256
Get-AuthenticodeSignature '<实际 setup.exe 或 AnsysInstaller.exe 路径>' |
  Select-Object Status,StatusMessage,@{Name='Signer';Expression={$_.SignerCertificate.Subject}}
Get-FileHash '<实际 setup.exe 或 AnsysInstaller.exe 路径>' -Algorithm SHA256
```

只有实际执行 EXE 的 `Status=Valid` 且签名主体明确属于 Ansys/Synopsys 官方时继续。记录哈希和签名主体，不上传安装包、ISO 或分卷文件。

## 4. 安装前空间与冲突检查

```powershell
Get-Volume | Where-Object DriveLetter | Select-Object DriveLetter,Size,SizeRemaining
Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize,FreePhysicalMemory
```

当前机器已经完成第三方 PLE 清理，并保留纯净官方 Ansys Student 2026 R1。先在可见窗口列出官方 Student 和安装器可识别的组件，确认 30 天 trial 是新增 Web/Named User/Evaluation entitlement、复用现有程序，还是需要官方安装器替换产品组件。不得默认卸载 Student。若官方流程确实要求卸载/替换，把拟卸载项、拟保留项和预计释放空间展示给用户；**得到用户当前窗口明确同意后**才执行，不删除项目仓库、Downloads 研究资料或烟雾测试证据。

如果官方支持人员明确要求保留现有产品组件并只增加 Web/Elastic/Evaluation licensing，以官方书面步骤为准。若无法用官方 Licensing Settings、Customer Center 状态或应用 checkout 日志确认旧第三方授权已隔离且当前 checkout 来自官方 Student 或已开通 trial，直接写 `OFFICIAL_TRIAL_STATUS=INSTALL_BLOCKED`；不猜测、不修改许可优先级。报告只记录非敏感的许可模式、产品功能名和 checkout 成败，不记录服务器、PIN、Host ID 或 entitlement ID。

## 5. 官方可见安装

1. 关闭其他大型程序；
2. 右键官方 `setup.exe` 或 `AnsysInstaller.exe`，选择“以管理员身份运行”；
3. 使用一个统一安装根目录，不把同一 release 的产品拆到多个根目录；
4. 根据实际 entitlement 选择：
   - Fluid Dynamics / Fluent / Fluent Meshing；
   - Structures / Mechanical / Mechanical APDL；
   - 3D Design、Geometry Interfaces、SpaceClaim Direct Modeler 或 entitlement 提供的等价 CAD；
   - Workbench；
5. License Manager/Web Licensing/Elastic Licensing 只按官方邮件或安装器提示配置；
6. 任何服务器地址、PIN、license 文件必须由用户亲自在可见窗口输入；
7. 安装完成后若要求重启，先保存报告再由用户确认重启。

不要默认全选所有无关产品。AirJet 项目不需要电磁、光学、自动驾驶等模块。

## 6. 安装后技术烟雾测试

在可见桌面按 `AJM_WIN_ANSYS_CAPABILITY_SMOKE_003.md` 的 CAD、Workbench/Mechanical 和 Fluent 测试逐项重做，但输出改为：

```text
C:\Users\admin\Downloads\AIRJET_ANSYS_OFFICIAL_TRIAL_SMOKE_004.txt
C:\Users\admin\Downloads\AIRJET_ANSYS_OFFICIAL_TRIAL_SMOKE_004\
```

至少要求：

- SpaceClaim/Discovery 参数化几何、Named Selections、Volume Extract、原生保存和 STEP 往返；
- Mechanical 最小静力求解；Modal、Harmonic、压电 GUI 或 APDL coupled-field 路线；位移表导出；
- Fluent 1 核和 8 核启动；Energy、ideal gas/compressible、transient、dynamic mesh、UDF/profile、fluid-solid CHT、Watertight Meshing；
- 最小流道求解和质量不平衡记录。

## 7. 最终状态

报告必须给出且只能给出一个：

```text
OFFICIAL_TRIAL_STATUS=NOT_YET_ENTITLED
OFFICIAL_TRIAL_STATUS=INSTALL_BLOCKED
OFFICIAL_TRIAL_STATUS=INSTALLED_SMOKE_FAILED
OFFICIAL_TRIAL_STATUS=PASS_START_P1
OFFICIAL_TRIAL_STATUS=PASS_START_P1_WITH_LIMITATIONS
```

只有 CAD 参数化/流体体积、Mechanical 最小求解和 Fluent 单核最小流动求解都通过时，才允许 `PASS_START_P1`。如果 P1 所需原生参数化、Named Selections、Volume Extract、连通和 Workbench 几何传递已经通过，但 STEP、Mechanical、压电、Fluent 或八核中的能力仍缺失，可写 `PASS_START_P1_WITH_LIMITATIONS`：允许只做 P1，并明确阻塞的 P2/P3/P4/P5 阶段。STEP 不是 P1 唯一硬门槛。如果 CAD 本身失败，则不得写任何 `PASS_START_P1*`。

完成后停止，不创建正式 AirJet CAD。Mac 端复核报告后另发 P1 建模任务。
