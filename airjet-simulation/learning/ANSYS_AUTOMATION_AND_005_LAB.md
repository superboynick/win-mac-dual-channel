# ANSYS 自动化与 005 工具链实验手册

## 1. 为什么不再依赖通用 GUI 代理

三次通用 Windows Codex 尝试都只检查 Git/审计并输出摘要，没有启动 ANSYS，也没有生成
005 报告。问题不是 ANSYS 没有自动化能力，而是通用提示缺少确定的应用接口、完成断言和
产物协议。坐标点击还会受窗口状态、分辨率和焦点影响。

当前路线使用产品官方接口：

| 路线 | 固定入口 | 主要用途 |
|---|---|---|
| SpaceClaim | `SpaceClaim.exe /RunScript /ScriptAPI=V261` | 参数化几何、流体负体积、Named Selections、原生/STEP |
| Workbench | `RunWB2.exe -B -R` | 系统模板、几何/命名传递、项目集成 |
| PyMechanical | `launch_mechanical(exec_file=AnsysWBU.exe)` | 结构、模态、谐响应、网格、求解和结果导出 |
| PyFluent | `launch_fluent(product_version=v261)` | Fluent Meshing、CFD、瞬态、Dynamic Mesh、CHT |

官方接口说明集中在 skill 的 `references/official-automation-routes.md`。

## 2. Windows 固定基线

当前只允许：

```text
Repository  C:\Users\admin\win-mac-dual-channel
ANSYS root  D:\ansys\ANSYS Inc\ANSYS Student\v261
Python      C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe
Venv        C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv
MCP name    airjet-ansys
```

Windows 实测 Python 为 3.12.10，`venv` 和 `ensurepip` 存在；基础 Python 没有 pip、MCP、
PyFluent 或 PyMechanical，因此依赖必须装在隔离 venv，不能污染基础环境。

## 3. 安装和注册

在 clean `main`、fetch 成功、HEAD 与 `origin/main` 相同并验签后运行：

```powershell
cd C:\Users\admin\win-mac-dual-channel
powershell -NoProfile -ExecutionPolicy Bypass -File `
  .\codex-skills\airjet-ansys-automation\scripts\bootstrap_windows.ps1
```

bootstrap 会安装项目 skills、建立 venv、安装精确版本：

```text
mcp==1.28.1
ansys-fluent-core==0.40.2
ansys-mechanical-core==0.12.11
```

然后注册 stdio MCP `airjet-ansys`。新 skill 需要新 Codex 会话加载。

## 4. MCP 为什么设计得很窄

调用者只能提交 `profile_id` 和不含路径的 `case_id`。profile 固定：

- ANSYS engine；
- Git 路径与脚本 SHA-256；
- 超时；
- 输出根 ID；
- 允许内联读取的 JSON 报告。

MCP 不提供 shell、PowerShell、CMD、任意脚本、任意文件读取、可执行路径、argv、cwd、
环境变量或授权参数。执行字节来自已验签的具体 Git commit blob，而不是可变化的工作树。
Python profile 以 `python -I -B` 运行；子进程只收到固定的最小环境，不继承 token、
`PYTHONPATH` 或许可变量。Windows 进程在恢复执行前被放进 Job Object，后台 watchdog 独立
执行超时；一次只允许运行一个 profile。

这些限制防的是误操作和 prompt injection。当前 Windows 用户是本机管理员，因此它们不能
抵抗管理员主动篡改；正式长时间无人值守求解前，仍建议增加非管理员 runner 账户。

## 5. 一次标准运行

1. `inventory()`：确认 Git、签名、官方 exe、精确依赖和批准 profile。
2. `submit_job(profile_id, case_id)`：服务器生成 job ID 和固定输出目录。
3. `poll_job(job_id)`：只观察服务器创建的 job；终态前不能取最终 manifest。
4. `artifact_manifest(job_id)`：分块计算文件哈希，只解析 profile 声明的小型 JSON。
5. 立即把 `job.json`、manifest 和 declared report 的脱敏副本放进
   `logs/evidence/<run_id>/`，并关闭 `logs/run-index.csv` 对应行。

终态词只描述执行层：`PROCESS_EXITED_0`、`FAILED_PROCESS`、`TIMED_OUT`、`CANCELLED`、
`FAILED_TERMINATION`。工程判定必须来自 declared report 的断言。

## 6. T0 与 T1/005 的区别

- T0 / `PASS_CONTROL`：官方接口启动、完成一个确定的小断言并正常退出。
- T1 / `PASS_005_CAPABILITY`：真正完成 005 要求的几何、传递、求解、保存/重开、守恒或
  并行测试，且原生产物齐全。

例子：PyFluent health 为 `SERVING` 只证明控制通道；只有建立网格、完成迭代、质量流量有限、
质量不平衡满足记录阈值并保存/重开 case/data，才能写 `MINIMAL_FLOW_SOLVE=PASS`。

## 7. 四个 T0 实验

### SpaceClaim

用 V261 API 建立 `20 x 10 x 4 mm` 方块、命名、保存 `.scdocx` 和 `.scdoc`，记录 body 数。
本机安装同时存在两种扩展名，但文件关联不同；因此只相信 `DocumentSave.Execute` 的返回、
实际文件和后续重开，不靠扩展名猜测。

### Workbench

查询 Static Structural、Modal、Harmonic Response、Fluid Flow (Fluent) 模板，建立最小
Static Structural system 并保存 `.wbpj`。这不能代替几何/Named Selection 传递验证。

### PyMechanical

启动固定 v261 `AnsysWBU.exe`，断言版本 `261`、远程算术 `2+3=5`、连接存活并正常退出。
这不能代替最小静力模型、网格、求解和 CSV 导出。

### PyFluent

启动 v261、3D、Double Precision、1 core、无 GUI，要求 health `SERVING` 和版本匹配。
这不能代替实际网格、模型设置、流动求解和 1/4/8 core 测试。

## 8. 005 工程能力实验

完整字段和判定以
[`AJM_WIN_ANSYS_STUDENT_CAPABILITY_SMOKE_005.md`](../windows-prompts/AJM_WIN_ANSYS_STUDENT_CAPABILITY_SMOKE_005.md)
为准。关键是：

- CAD 必须有参数更新、INLET/OUTLET/WALLS、单一连通流体体、原生保存、STEP 回读、
  Workbench 和 Named Selection 传递；
- Mechanical 必须有最小静力求解和结果导出，并分别记录 modal/harmonic/piezo 路线；
- Fluent 必须有实际流道、网格、至少 20 次迭代、质量平衡、case/data 重开和 1/4/8 核尝试；
- `P1_STAGE_GATE` 始终为 `NOT_RUN`。

用户本轮不要求看到 GUI，所以记录 `VISIBILITY=NOT_USER_OBSERVED`。无头 API 产物可支持技术
字段，但不能代填 `GUI_VISIBLE=PASS`。

## 9. 现实故障排查顺序

```text
inventory 不 ready
  -> Git/签名 -> 固定路径/签名 -> venv/包版本 -> profile/hash
submit 失败
  -> 输出根 junction -> 执行副本 hash -> Job Object/挂起恢复 -> 最小环境
进程非零
  -> declared report -> stderr hash/原始日志 -> 对照官方 API 版本
进程为零但能力失败
  -> 不提升 PASS；检查原生文件、重开、Named Selection、求解/守恒断言
上游失败
  -> 下游写 BLOCKED_UPSTREAM，不把它算作下游 FAIL_DIRECT
```

所有新问题先进入 [`REALITY_AND_FAILURE_LOG.md`](../logs/REALITY_AND_FAILURE_LOG.md)，再做最小
区分实验。禁止用降低整机 cell/孔数、修改授权、无限重试或手工改报告来“通过”。
