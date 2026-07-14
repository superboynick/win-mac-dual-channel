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
- T1 partial / `PASS_PARTIAL_CAD_CAPABILITY`：只完成声明的脚本重建、几何、回读或传递子集；
  未关闭的原生参数化等硬门槛必须同时写明。
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

## 10. 2026-07-14 实战复盘：第一次 suite 为什么失败

第一次确定性 suite 在 commit `1777d25c...` 上串行运行四个 T0 profile：

| engine | 终态 | 当时观察 | 真正问题 |
|---|---|---|---|
| SpaceClaim | `PROCESS_EXITED_0 / PASS_CONTROL` | 建成一个命名方块，`.scdocx` 落盘 | `.scdoc` 调用成功但文件不存在，说明返回值不等于落盘 |
| Workbench | `FAILED_PROCESS / FAIL_CONTROL` | 项目与 `SYS` 保存了，模板查询失败 | UI 显示名不是完整内部模板键；结构模板还需 `Solver=ANSYS` |
| PyMechanical | `PROCESS_EXITED_0 / PASS_CONTROL` | v261 连接、算术和退出正常 | 只是控制面，还没有 FEA |
| PyFluent | `TIMED_OUT / FAIL_CONTROL` | health=`SERVING`、settings/TUI 存在 | 把显示文本当版本协议；`exit()` 默认异步，子进程树仍活着 |

这里最重要的不是“API 名字写错了”，而是四类证据不能混用：

- **显示层**：界面名称、日志中的产品名称，适合给人读；
- **协议层**：内部 template key、Enum、schema 字段，适合稳定判断；
- **进程层**：根进程退出码，只描述某个 process；
- **任务层**：整个 Job Object 中所有子进程退出后才是完整终态。

如果脚本只检查“窗口打开”或根 Python 返回 0，Workbench 内部查询错误和 Fluent 长尾进程都
可能被错误写成 PASS。

## 11. 怎样做一次不篡改历史的修复

这次采取的顺序是：

1. 不修改首轮 job、report 或 suite JSON；先记录 SHA-256。
2. 查本机 v261 API 类型和官方示例，分别识别 display name/internal key、display string/Enum。
3. Workbench 结构模板加入 `Solver="ANSYS"`，Fluent 模板改用内部键 `Fluid Flow`。
4. PyFluent 版本改为与 `FluentVersion.v261` 比较，同时记录 `.value=26.1.0`。
5. PyFluent 退出改为有界等待；Job Object/watchdog 仍作为外层兜底。
6. 重新计算脚本 SHA，签名提交并让 Windows fast-forward 到精确 commit。
7. 用新 case/job ID 重跑，而不是覆盖旧目录。
8. suite 4/4 通过后，再检查相关进程数为 0。

成功轮 commit 为 `6265043003dfb44b2b694ef3e91cfd84d7cc832b`。完整结果 JSON SHA-256
为 `4e3973828e3b99c88dd65d6429901f2b5656c704fb702eca2bc2a674c241ba38`。失败轮与成功轮都在
`logs/evidence/` 留有凝练摘要；每个 job 在 `logs/run-index.csv` 独立登记。

## 12. 为什么 4/4 PASS 仍不能开始声称仿真完成

T0 只回答“我们能否用确定方式控制软件”。005 T1 才回答“这套安装能否完成计划所需的
最小工程动作”。当前没有做：

- 带腔体、入口、出口的参数化流体几何；
- `INLET/OUTLET/WALLS` 及其跨 Workbench/Meshing 传递；
- Mechanical 网格、静力、模态、谐响应、压电求解；
- Fluent 网格、至少 20 次实际迭代、质量守恒、case/data 重开；
- transient/dynamic mesh/CHT 的实际小模型；
- 4/8 solver process 的实际限制测试。

所以此刻正确状态是：

```text
PASS_CONTROL_SET
engineering_capability=NOT_RUN
P1_STAGE_GATE=NOT_RUN
```

## 13. T1 能力探针为什么要拆开

一个巨型“全功能脚本”一旦失败，很难区分是几何、传递、求解、Student 限制还是退出清理。
因此按最小因果链拆分：

| probe | 最小工程动作 | 通过后可以说 | 仍不能说 |
|---|---|---|---|
| `SC-CAD-T1` | 脚本参数重建、腔体/孔/出口、命名面、单连通流体体、原生重开、STEP 回读 | 本轮声明的 partial CAD 构建/回读能力通过 | 原生参数化或已建立 AirJet 整机 CAD |
| `WB-XFER-T1` | 只接收上一步冻结 SHA 的产物，核对 body/名称并生成粗网格 | partial 几何与 Named Selections 可传入 Workbench/Mechanical | P1 readiness 或 P1 Gate 通过 |
| `MECH-STATIC-T1` | 10×10×1 mm 块实际网格/求解/导出/重开 | 最小静力路线可运行 | AirJet 执行片模型成立 |
| `MECH-MH-T1` | 至少三阶模态和一次谐响应扫频 | modal/harmonic API 实际求解可用 | 找到产品 20–25 kHz 模态 |
| `MECH-PZ-T1` | 最小压电耦合模型及电压反号检查 | 至少一条压电路线实际可用 | 压电材料栈或 1 W 功耗闭合 |
| `FL-WT-FLOW-T1` | 三维流道网格、20+ iterations、质量平衡、case/data 重开 | 小型稳态 CFD 路线可运行 | AirJet 动态喷流成立 |
| `FL-ET-T1` | Energy/ideal gas/transient 实际推进时间步 | 对应模型组合在小模型可运行 | 高频瞬态已收敛 |
| `FL-DM-T1` | 运动边界、smoothing/remeshing、多时间步 | dynamic mesh 在小模型实际执行 | 膜片真实位移场已经耦合 |
| `FL-CHT-T1` | 流固区、热界面、能量方程、热流闭合 | 小型 CHT 路线可运行 | 5.25/4.25 W 整机热账户闭合 |
| `FL-P4/P8-T1` | 分别用 4/8 solver processes 实际读 case 并迭代 | 记录本机 Student 实际并行能力 | 获得任何额外授权或整机性能 |

有前后依赖的探针不能读取“最近生成的文件”。上一步产物必须通过固定 job ID 或服务器端
artifact linkage 传递，并校验 SHA；否则调用期间文件可能被替换，运行证据就失去身份。

## 14. 每次运行后你应学会问的九个问题

1. 输入对应哪个 commit、profile 和 script SHA？
2. 这是产品证据、专利候选、文献方法、推导值还是未知假设？
3. process terminal state 与工程断言是否分开？
4. 原生产物是否真正落盘、能否关闭后重开？
5. 报告中的数量、单位、面/体 identity 能否由机器复算？
6. 失败是直接失败、上游阻塞还是根本没有运行？
7. workaround 是否改变了物理问题、产品完整性或许可边界？
8. 这项结果最多能支持论文中的哪一句话？
9. 它明确不能支持什么？

只要第 8、9 题没有写清，运行就还没有形成可安全用于论文的方法证据。

## 15. T1 CAD→Workbench 为什么先保留为 partial

第一条 T1 链的详细几何、解析值、同版本 API 来源和学习题见
[`T1_CAD_TRANSFER_WORKBOOK.md`](T1_CAD_TRANSFER_WORKBOOK.md)。它故意把三件事分开：

| 能力 | 本轮路线 | 发布前口径 |
|---|---|---|
| 参数改变几何 | 同一脚本用 5/6 mm cavity width 构建两个临时 block 并复算体积 | `script_parameterization_equivalent` |
| 原生参数化 | 保存文件中存在 driving parameter、修改有效且重开后保留 | `NOT_RUN` |
| 流体体积 | 直接建立三个负体积后 Boolean union | `volume_extract_api=NOT_RUN`，只通过 equivalent route |

005 合同允许用等价参数做烟雾动作，但正式开始 P1 的硬门槛仍明确要求原生参数化。因此本轮
即使 SpaceClaim 与 Workbench 两个 profile 都通过，suite 可以写
`PASS_CAD_TRANSFER_SET`，但必须同时保留：

```text
pass_005_capability=PARTIAL_CAD_TRANSFER_ONLY
p1_cad_toolchain_readiness=BLOCKED
p1_cad_blocker=NATIVE_PARAMETERIZATION_NOT_RUN
P1_STAGE_GATE=NOT_RUN
```

这不是降低实验价值。它让我们先消除 Boolean、原生保存、重开、STEP、Named Selection、
Workbench import 和 Mechanical mesh 的不确定性，同时不偷换仍未关闭的参数化问题。

## 16. 一个上游文件为什么需要两次哈希还不够

旧设计在 Workbench 提交时对 SpaceClaim 文件算一次 SHA，复制后再算一次。若两者相等，只能
证明复制过程没有改变字节。它不能回答：这个字节是否仍是上一个 suite 已经审查过的字节。

修订后的身份链是：

```text
terminal SC job
  -> first artifact_manifest freezes size/SHA in MCP memory
  -> WB submit names exact predecessor job ID
  -> server checks same case/profile/commit/output root
  -> server rehashes current source against frozen snapshot
  -> server copies only policy-listed files
  -> destination rehash equals frozen/source hash
  -> read-only predecessor-manifest records the linkage
```

冻结 manifest 不写回上游 job，避免为了记录 snapshot 又改变 `job.json` 的哈希。MCP 重启会
丢失内存身份，因此依赖任务必须在同一 server session 中完成；重启后以明确错误阻止，而不是
从 Downloads 猜“最近一次”产物。

这仍不是 OS sandbox。签名脚本在 Windows 当前用户权限下运行；安全性来自调用者不能注入路径/
命令/环境、脚本字节绑定签名 commit，以及 predecessor 供应和证据哈希受限。文档不能把它夸大
为“进程只能读取这些文件”。

## 17. 发布前审查修掉了哪些会制造假阳性的点

1. 圆柱入口的三点顺序按 v261 `centerPoint/startPoint/endPoint` 语义修正；
2. `parametric_geometry` 改为诚实的 `script_parameterization_equivalent`；
3. P1 readiness 不再因 partial pair 通过而改为 PASS；
4. runner 的 job commit 必须与初次 inventory commit 精确相等，堵住中途 fast-forward；
5. job 目录创建后立即写 `PREPARING`，后续任一准备错误落 `FAILED_START`，不留无状态目录；
6. `.scdocx/.step/.wbpj/inspection.json` 都要求 manifest size/SHA 与 profile 报告自报值一致；
7. predecessor 还要核对 probe、required assertions、P1 Gate 和许可参数标记。

静态 policy/audit PASS 只证明这些规则在代码和配置中存在。它们还要经过 Windows 负向测试与
第一轮真实 ANSYS 运行，才能把状态从 `PENDING_SIGNED_RUN` 改成实测结果。
