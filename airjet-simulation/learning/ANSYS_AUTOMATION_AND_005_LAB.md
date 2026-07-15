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

1. 圆柱入口三点曾按 v261 XML 的短参数名做过一次静态修正，但第二次签名实跑用
   `200 mm³ / zmin=1 / INLET=0` 推翻该解释；同机官方 example 最终确认 `p1→p2` 是轴线、
   `p2→p3` 是半径，第三版还在 Boolean 前检查 raw cylinder 指纹；
2. `parametric_geometry` 改为诚实的 `script_parameterization_equivalent`；
3. P1 readiness 不再因 partial pair 通过而改为 PASS；
4. runner 的 job commit 必须与初次 inventory commit 精确相等，堵住中途 fast-forward；
5. job 目录创建后立即写 `PREPARING`，后续任一准备错误落 `FAILED_START`，不留无状态目录；
6. `.scdocx/.step/.wbpj/inspection.json` 都要求 manifest size/SHA 与 profile 报告自报值一致；
7. predecessor 还要核对 probe、required assertions、P1 Gate 和许可参数标记。

静态 policy/audit PASS 只证明这些规则在代码和配置中存在。Windows 负向测试已通过，真实 CAD
探针前三轮 FAIL 均已保留；第四次签名运行已用 occurrence/master 分层指纹通过 STEP 几何回读，
SpaceClaim profile 首次得到 `PASS_PARTIAL_CAD_CAPABILITY`。但 Workbench 在
`model_component.Refresh()` 直接失败，完整 transfer set 仍 FAIL；局部修复通过不能倒写前三轮，
也不能提前写 aggregate 能力 PASS。

## 18. 第四次实跑怎样区分 direct fail 与 not reached

Workbench 的固定 report schema 会为后续断言预置 false。第四次运行中：

```text
predecessor identity   = PASS
geometry attach        = FAIL_DIRECT at Model.Refresh
named-selection inspect= NOT_REACHED
mesh generation        = NOT_REACHED
project save           = NOT_REACHED
```

这里不能把四个 false 当成四个并列失败。判断规则是：先沿 traceback 找第一个异常，再结合脚本控制流
判断异常后的操作是否曾被调用。固定 schema 方便机器校验，但机器字段必须配合 phase、traceback 和
到达标记解释。下一版脚本会显式记录 `SetFile`、`UpdateUpstreamComponents` 和 `Refresh` 三个边界，
让“在哪一步失败”不再只依赖 traceback。

这轮还揭示了 CAD 链常见的四层证据边界：

```text
SHA 身份正确 -> 生产软件可重开 -> 下游软件可附加 -> 语义/网格实际通过
```

每一箭头都需要新的运行证据。前一步 PASS 只是排除一类原因，不能替代后一步。

第五次签名运行进一步把旧更新顺序替换为 `Model.Update(AllDependencies=True)`，但 attach 错误不变。
到达标记显示 `SetFile` 返回、Update 被调用但未返回，其后全部未到达。由此只排除旧更新顺序这一
窄假设；下一步才允许单独改变为 Geometry source→`TransferData` 数据流架构。

第六次签名运行证实普通 Geometry source 和 Static Geometry 的 `TransferData` 组合在调用阶段即被
v261 拒绝。`TransferData` 方法真实存在，不代表任意 component 类型兼容。下一轮按同机官方
post-import journal 改用 `ComponentsToShare`；这种“由运行建立兼容矩阵”的记录必须保留在方法日志。

第七次运行中 `ComponentsToShare` 和 `GetGeometryFileAndSaveData()` 已返回，说明官方 share 架构
越过兼容性拒绝；但保持不变的 Component Update 仍 attach 失败。下一轮只改为同机官方 Model
container `Refresh()`，不提前把 share 建立写成完整 geometry transfer PASS。

第八次用官方 Model container Refresh 仍得到同一 attach 失败，关闭了 share topology 中“只因
Update API 选错”的假设。下一轮只增加显式 SpaceClaim `Edit/Exit`，继续用到达标记把 CAD editor
attach 与 downstream model attach 分开。

第九次 `Edit/Exit` 均返回而 downstream Refresh 仍失败，证明“Workbench editor 可打开”与“Model
可附加”不同。下一轮 STEP 只作为管线诊断；Named Selection 语义不被交换格式保证，因此不会用
STEP body/mesh PASS 代替完整 transfer PASS。

## 19. 第十次实跑：STEP 诊断关闭了哪些问题，又没有关闭哪些问题

签名 commit `6f828fe...` 把同轮 SpaceClaim 已验证的 STEP 作为 frozen predecessor。Workbench 的
source/share/save-data/Model Refresh 全部返回；Mechanical 实际得到 1 个 body，生成 1063 nodes / 513
elements，并保存 50588-byte `.wbpj`。因此“Workbench、Mechanical 或 mesher 在本机整体不可用”这一
宽泛假设已被真实运行推翻。

与此同时，`INLET/OUTLET/WALLS` 的对象数和实体数全为 0。脚本按设计保留 native assertions 为
false，并以 exit 2 fail closed。因此这次结果应记为：

```text
generic body/mesh/project pipeline = PASS_DIAGNOSTIC
upstream semantic labels           = ABSENT
native named-selection transfer    = NOT_PROVEN / false
suite                              = FAIL_CAD_TRANSFER_SET
```

现实工程中，“有可计算几何”与“边界条件语义仍在”是两件不同的事。求解器若只有 body 而不知道哪个
面是 inlet/outlet，后续 CFD 仍可能把边界条件施加错。所以下一步不会手工凭 face ID 点选，而会建立
STEP + semantic sidecar 的确定性重建：绑定 source SHA，按面几何与邻接唯一匹配，检查三组互斥和全
覆盖，再 mesh、保存、重开复核。该路线的报告名、字段名和论文措辞都必须使用 reconstruction，不能
把 solver-side 重建写成 native CAD transfer。

## 20. 第十一次实验的操作边界与 Windows 入口

为了避免混淆，native transfer 和 STEP semantic reconstruction 现在是两个 profile/runner。Windows
只在工作树干净、签名 commit 精确同步、skills 重新安装且静态 policy PASS 后运行：

```powershell
$Python = 'C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe'
$Runner = "$HOME\.codex\skills\airjet-ansys-automation\scripts\run_t1_semantic_reconstruction_suite.py"
& $Python -I -B $Runner
```

允许的成功输出只有 `PASS_STEP_SEMANTIC_RECONSTRUCTION_DIAGNOSTIC`。它要求 producer sidecar 与
STEP/report/MCP manifest 哈希链一致、Mechanical 面唯一分类为 1/1/11、负向 partition controls 全部
拒绝、Named Selection 创建后实体数仍为 1/1/11、mesh 和 project 有非空 SHA 产物。

无论诊断是否 PASS，native runner 的历史/当前状态不被改写，P1 readiness 保持 BLOCKED。操作人员
不能把新 runner 的 exit 0 转录成 `PASS_CAD_TRANSFER_SET`；这是两个不同的问题。

### 20.1 第一次实跑：怎样读懂“false 但没有执行”

第十一次真实运行的 suite 是
`AJM005_T1_SEMANTIC_RECON_SUITE_20260714T210952085661Z_4c81dce0`。producer 和 sidecar identity 通过，
Workbench 也到达 `Model.Refresh()`，但在进入 Mechanical script 前无法保存/附加 `SYS.mechdb`。

因此要分三层读报告：

1. `assertion=false`：最终成功合同没有满足；
2. `execution_reach=NOT_REACHED`：这一算法步骤没有机会接受测试；
3. `error phase=Model.Refresh`：当前优先排查 host/project materialization，而不是修改面分类容差。

本轮若直接放宽 centroid/area tolerance，既不会越过 `Model.Refresh()`，又会同时改变算法，导致实验
无法归因。正确的下一轮只缩短 case prefix；如果短路径进入 Mechanical，才逐个处理 v261 API 与
单位风险。该例展示了自动化仿真里“先恢复可达性，再调算法”的基本顺序。

### 20.2 第十二次实跑：失败分支也必须保存中间观测

短 case ID 让 Workbench job root 降到 154 字符，`Model.Refresh()` 和 Mechanical script 都返回。
因此第十一次的 attach 异常不是永久软件不可用；它对 ANSYS 某个 legacy 子组件的路径预算敏感提供
强支持。

接着 fail-closed classifier 正确拒绝 `INLET=0, OUTLET=1, WALLS=12`。由于 Named Selection 创建位于
partition validation 之后，本轮没有把错误边界写进模型，这是安全行为。问题在于旧脚本也没有把
失败前已经算出的 face map 写进 inspection，导致我们知道“入口没匹配”，却不知道最近的实际面差
多少。

修正方式是在 real validation 之前更新 inspection 的纯观测字段：CAD unit、body/face count、每个
face 的 ID/centroid/area、candidate labels 和 negative controls。`semantic_reconstruction` 仍为 false，
不提前创建任何树对象，不放宽容差。静态测试还要断言这个 prevalidation marker 位于真实
`validate_partition(...)` 之前，避免以后重构时又丢失失败证据。

### 20.3 第十三次实跑：不要用“调大容差”掩盖指标不兼容

完整 face map 显示，入口候选的 centroid 与 sidecar 完全一致，但 `face.Area` 从 `π` 变成 `2.0`。
若把面积容差从 0.02 直接扩大到 1.2，确实可能让当前 fixture 变绿，但会让 predicate 接受范围扩大
60 倍，而且没有说明为什么这个范围对未来几何安全。

更好的顺序是：

1. 保存跨 kernel 后的实际 face map；
2. 找出哪个 descriptor 稳定、哪个不稳定；
3. 用 surface type、edge topology、normal 和唯一性补强稳定 descriptor；
4. 再做单变量 predicate 修改，并保留 0/multiple/overlap/coverage 负向测试；
5. 最后才允许创建边界对象和 mesh。

本轮 body 和 negative controls 明确 PASS，但 suite 仍 FAIL，说明局部 assertion 进展与最终能力 PASS
可以同时存在。写论文方法时应呈现这种分层，而不是只保留最后一次绿色运行。

### 20.4 第十四次实跑：从“不稳定 descriptor”迁移到校准后的复合锚点

Topology APIs 实测全部可用。face 44 的 `center + plane + 2 edges + abs(z-normal)` 在 13 面中唯一，
而 area 是已知不稳定项。下一轮不是单纯“忽略面积”，而是用三个独立局部拓扑 descriptor 替换它，
并继续让唯一性、1/1/11、互斥、全覆盖和 negative controls fail closed。

复合锚点也有适用范围。这里的 edge count=2 是 STEP→Mechanical 对这个圆形 cap 的实际表达，不是
圆的一般数学性质，更不是 AirJet 产品事实。所以 report 必须同时记录：

- `scope=DISPOSABLE_CAPABILITY_FIXTURE_ONLY`；
- area role 为 `DIAGNOSTIC_ONLY`；
- solver topology calibration 来源为 REAL-034/035；
- native transfer/parameterization claims 继续 false。

这样即使下一轮变绿，读者也知道通过的是“可删除小模型的重建能力”，不是产品 CAD Gate。

### 20.5 第十五次实跑：绿色终态也要逐层验收

本轮 exit 0 不是因为 runner 只看进程返回码。它依次要求七个 diagnostic assertions 全 true：

```text
predecessor identity
-> semantic sidecar identity
-> body/13-face geometry available
-> unique 1/1/11 semantic reconstruction
-> four negative controls reject bad partitions
-> mesh 1063 nodes / 513 elements
-> project save with non-empty SHA
```

Mechanical 创建前确认 INLET/OUTLET/WALLS 同名对象都是 0；创建后对象数为 1/1/1，实体数为
1/1/11。这一步防止旧树对象制造假阳性。inspection 还保存了 candidate IDs 与 reconstructed IDs
完全一致，所以“分类成功”和“实际树对象绑定成功”是两次独立检查。

suite 的正确成功字符串是 `PASS_STEP_SEMANTIC_RECONSTRUCTION_DIAGNOSTIC`。report 的 error 字段仍写
`DIAGNOSTIC_PASS_CANNOT_CLOSE_NATIVE_TRANSFER_GATE`；它是机器可读的 claim boundary，不表示运行
失败。canonical native claims 全部保持 false，P1 readiness 继续 BLOCKED。

下一实验重新回到独立的 native 路线：先用同一 producer 和最短安全 case ID 复测 `.scdocx` attach
与原生 Named Selection transfer；原生 driving parameter 另设独立合同。随后还要做 Mechanical 与
Fluent 可删除 T1 求解。任何一项诊断 PASS 都不能替代另一项，也不能提前启动 006。

### 20.6 两个审计器为什么会给出不同结果

第十五次证据提交在 Mac 的 Python project audit 中 PASS，但 Windows 根 PowerShell audit 在精确拉取
后 FAIL。不是 Windows 文件损坏，而是两个审计器的覆盖面不同：Python 审计保护项目骨架与证据语言；
PowerShell 还硬锁 skill required files 和 profile ID 集。semantic runner/profile 已加入真实策略，
PowerShell 的期望清单却仍停在旧版本。

这类问题的处理顺序是：先核对工作树、commit、签名和真实 manifest/profile，确认不是分叉或篡改；
再比较审计器期望与 canonical 配置；最后只同步审计期望，不为了让审计变绿而删除合法 profile。
审计器修复也必须重新在其原生平台运行。一个审计器 PASS 只能证明它覆盖的规则，没有“全项目绝对
正确”的含义。

## 21. 第十六次实验：负结果怎样关闭一个看似合理的修复

native runner 的短 case ID 让输入路径从长路径降到 145 characters，但 `Model.Refresh()` 仍在同一点
失败。执行 reach 很重要：SetFile、SpaceClaim Edit/Exit、ComponentsToShare 和 save-data 都返回，
Mechanical script 却没有被调用。因此这轮只关闭“路径长度是 native attach 的充分解释”，不把后续
false assertions误写成 Named Selection、mesh 和 project 各自失败。

下一个变量是 working-copy writability。MCP 的 frozen predecessor 继续保持只读；journal 在 job root
另建 hash-equal staged `.scdocx`，然后验证它可写。若 Edit/Exit 修改了 staged file，报告应保存修改前
和修改后 SHA，但不能把修改后文件倒写成 predecessor。若 staging 仍无法 attach，就用真实运行关闭
这个假设，而不是继续叠加更多 workaround。

## 22. 第十七次实验：先证明干预发生，再解释失败

本轮的测试顺序是实验设计的关键：

1. 冻结 source report/manifest/native 的身份和 SHA；
2. 记录 source 的 read-only 属性；
3. 复制到 job-local `stagingcopy`，显式设为 writable；
4. 硬检查 working/source 路径不同但长度相同，size/SHA 相同；
5. 只把 working path 传给 `SetFile`；
6. 无论主路线成功或异常，都在写 report 前复核 working 终态和 frozen source 的字节/只读位；
7. runner 再用 manifest 的完整 nested relative path、size 和 SHA 复核 report，不能只比 basename。

两个独立静态审查先发现并关闭了三类潜在假阳性：只比 filename 可能把 predecessor 误认成 working
copy；working file 被删除时若不写 `exists=false` 会丢失败证据；只复核 source SHA 而不复核 read-only
位会遗漏属性变化。修好并审计后才允许 Windows 实跑。

实跑中 staging 合同全部通过，Edit/Exit、share/save-data 也返回；但 WB job 最终在 Refresh attach
失败。source 保持 `ReadOnly, Archive`，working copy 保持 `Archive`，两者前后都是 32143 bytes 和
SHA `7e1d3729...`。因此 writable-staging 有意干预已经实施，但对当前 route 不充分。

下一项 connected-editor diagnostic 必须使用独立 profile，不能覆盖既有 external native transfer
历史。成功合同仍要检查 1 body、Named Selection objects `1/1/1`、entities `1/1/11`、mesh 非零和
project save；同时明确 `external_scdocx_attach=NOT_RUN`、`native_parameterization=NOT_RUN`、
`p1_stage_gate=NOT_RUN`。diagnostic PASS 也不能提前启动 006。

### 22.1 一个很现实的跨平台操作错误

Windows handoff 时若从 Git Bash 误跑 `install-skills.sh`，会因为系统没有 `rsync` 在第一步失败。
正确入口是 `install-skills.ps1`，使用 Windows 自带 `robocopy`。这次随后四个 skill 哈希/必需文件、
根审计和 MCP policy 全部 PASS。教学点不是“安装脚本坏了”，而是同一仓库存在平台专用入口，运行前
应先按 handoff 手册选择；入口错误不能拿来解释后续 ANSYS 几何 attach 失败。

## 23. 第十八次实验：connected SpaceClaim 首轮及早期证据探针

### 23.1 为什么要单独建 profile

external `.scdocx` attach 已有连续失败历史，STEP+sidecar 也已有独立 diagnostic PASS。connected
editor 是第三条 materialization route；若复用原 profile，最后的状态和产物会混淆三种不同主张。
所以本轮新建 `ajm005-workbench-connected-spaceclaim-t1-v1`，成功状态也只能是
`PASS_CONNECTED_SPACECLAIM_TRANSFER_DIAGNOSTIC`。

这个 route 的固定边界是：

- 从 `GeometryFilePath=""` 的 Workbench Geometry cell 开始；
- `Edit(Interactive=False, IsSpaceClaimGeometry=True)`；
- `RunScript(ScriptFile=<reviewed absolute path>)`；
- `Exit()` 后才允许 share；
- 禁止 `SetFile`、external `DocumentOpen` 和 `DocumentSave`；
- 前驱只消费 producer report；
- external native attach、native parameterization、full-product CAD、P1--P6 始终不随 diagnostic PASS。

### 23.2 本轮实际停点

签名 commit `f15aae34...` 的 Windows preflight 为：4 个 skill hash/必需文件 PASS，项目审计
`106/7/28`，MCP static policy `8 profiles/5 tools`。随后 producer PASS。connected job 记录 empty
cell、Edit、RunScript、Exit 全 RETURNED，但没有 `connected_spaceclaim_build.json`，因此在 share
前 fail closed。Mechanical 没有启动，mesh/project 也没有结果。

报告缺失与报告 FAIL 必须分开：

- FAIL JSON 说明内层脚本至少进入了自己的保护区；
- missing JSON 只说明期望证据没出现在期望路径；
- 外层 API RETURNED 不能替代内层 JSON；
- 后续 assertions 为 false 是 `NOT_REACHED` 的结果，不能写成各项独立工程失败。

### 23.3 下一版 early sentinel 的操作合同

下一版嵌入脚本按以下顺序执行：

```text
1 absolute-path builtin open -> entry sentinel
2 import json/os/traceback and record os.environ.get("AIRJET_JOB_DIR")
3 establish result/report path and current stage
4 import .NET/SpaceClaim dependencies
5 build fixture and groups
6 write PASS/FAIL build JSON in outermost finally
```

外层 journal 在调用 `RunScript` 前记录 embedded script size/SHA；调用后依次检查 sentinel 和 build
report。sentinel/build report 都要进入主 report 和 artifact manifest；不能只靠 Workbench UI 或
CoreEvents 猜测。所有绝对路径由 job-local 外层生成，不把 Windows 用户名、Downloads root 或旧 job
硬编码进仓库。

### 23.4 三类现实噪声怎样处理

本轮 preflight 还暴露了验证基础设施本身的三个坑：临时检查器使用错误 profile 字段；临时 AST
检查器猜错 embedded 变量名；外层 PowerShell 把内部 native command 留下的 `$LASTEXITCODE` 当成
整个 installer 的退出码。正确做法是从 canonical JSON/AST 读取真实字段，并让 `.ps1` 作为独立
进程返回真实 exit code。

Workbench CoreEvents 还记录 RSM 未安装和 ProgramData 绝对路径 warning。由于本轮没有请求远程
队列，且 warning 后 project/Edit/RunScript/Exit 继续进行，它被保存为非因果旁路观测，不触发重装、
许可切换或 RSM 安装。工程排障要把“同一日志里出现”与“形成调用链因果关系”分开。

## 24. 第十九次实验：用三个时点而不是一个布尔值审查 child entry

### 24.1 literal path 为什么是诊断变量

首轮 child 在 report 初始化前读取环境变量，所以“没有 report”混合了两类情况：脚本没执行，或脚本
执行了但输出路径不可用。第二轮把绝对 job/report/sentinel 路径写进 child 源码，环境只作为诊断值。
sentinel 又先于 imports，因此它是比 JSON report 更低层的 entry 证据。

outer journal 的时序是：

```text
Edit RETURNED
RunScript RETURNED
probe sentinel/report
Exit RETURNED
probe sentinel/report
build contract
failure catch probe + GetMessages snapshot
```

每个 probe 必须 best-effort。若读取一个正在写入/被锁定的文件抛异常，探针只记录 `probe_error`，不能
提前跳入 cleanup 并改变被测时序。最终 PASS 仍独立要求 build JSON、几何指纹、groups、transfer、
Mechanical、mesh、project 和 manifest，probe 本身不能制造 PASS。

### 24.2 真实结果与正确写法

三个时点的 sentinel/report 都 absent，且无 probe error；RunScript 与 Exit 仍 RETURNED，Workbench
messages 为空。正确写法是：

> literal-path early-sentinel 在同一 run 的 post-RunScript、post-Exit 和 failure 三个检查点均未被
> 观测，connected transfer 未到达。

错误写法包括：“child 三次失败”“几何构造失败”“`.py` 不支持”“SpaceClaim 许可有问题”以及
“connected transfer 失败”。这些结论都超出 reach。

### 24.3 后续 A/B 顺序

1. 在同一 opened editor 先用官方
   `SendCommand(Language="Python", Command=<builtin open marker>)` 写独立 marker，然后保留 `.py`
   RunScript。两种调用共享同一 editor 与 absolute job root，但 marker 名不同。
2. inline marker 有、file marker 无：查 file loader/path；两者都无：查 editor scripting channel、
   session 或 batch integration；SendCommand 抛错：保存直接异常。
3. 官方同时支持 `.py`/`.scscript`，却没有证明合法文件可 byte-identical；不把简单改 suffix 当严格
   A/B。只有取得合法 `.scscript` 格式或等价性证据后才测 extension dispatch。
4. 在 entry 可观测前，不改 fixture 几何、不启动 Mechanical/Fluent、不动许可或安装。

## 25. 第二十次实验：先为 A/B 定义“还没进入 A/B”

### 25.1 为什么四态还不够

四态矩阵默认两个 action 都至少拥有可判定 checkpoint。如果第一个调用本身抛异常，第二个 action
尚未执行，就必须有第五个状态 `CHECKPOINT_NOT_REACHED`。否则数据表会把 control-flow failure
误写为两个 channel 的 engineering failure。

本轮通过三层合同避免误判：

1. reach 同时区分 `CALLED`、`RETURNED`、`NOT_REACHED`；
2. marker 只认 exact bytes/size/SHA，无 probe error；
3. suite 单独输出 `script_channel_classification`，不让总体 FAIL 覆盖细分类。

### 25.2 真实错误怎样定位

`Edit(Interactive=False)` 返回后，`SendCommand(Command=..., Language="Python")` 在 journal line 553
抛 Workbench NullReference。post-Send probe 没到，RunScript 没调用，正常 Exit 没到；failure catch
执行 cleanup Exit 并成功。failure artifact probe 三个文件均 absent，GetMessages/stdio 空。

这时不能靠“marker 没有”说 inline Python 写文件失败，因为命令可能尚未交给 interpreter。能写的
只有：Workbench—connected editor 的该 SendCommand 调用路径在 post-call checkpoint 前失败。

### 25.3 这轮遇到的两类自动化现实问题

- Windows text mode 可能把 `\n` 写成 `\r\n`。如果 outer 锁 LF-only SHA，child 用文本模式，即使
  真实执行也会假判。marker 因而统一使用 binary fixed bytes。
- `git verify-commit` 会把成功说明写到 stderr，PowerShell `Stop` 会把它包装成异常；格式化异常还会
  按宽度换行 fingerprint。最终改用 `%G?` 和 `%GF` 的 machine-readable 字段。

这两个问题都说明：验证器本身也要有数据合同，红字不自动等于被测软件坏了。

### 25.4 下一轮判读

只改受审 outer journal 的 `Edit(Interactive=True)`；case-specific absolute path 和注入后的 bytes 会按
同一合同重建，并非整组输入 byte-identical：

| observation | next inference/action |
|---|---|
| SendCommand RETURNED + inline exact | 支持 `Interactive` mode/session 相关假设；继续本轮 file marker |
| same NullReference | 只证明改该参数不足；下一轮 interactive RunScript-only |
| Edit/SendCommand hang or new launch error | 记录 SSH/MCP 下 interactive route 不可用；不推导许可坏 |

无论哪一项，都不能直接推进到 AirJet 完整 CAD。connected fixture 通过后还需回到 external native
attach、native Named Selection transfer、native parameter object/update/reopen，再满足 005 hard Gate。

## 26. 第二十一次实验：参数被接受，不等于所需 session 已建立

literal `Interactive=True` 在 recorded journal 中被规范成省略默认参数的
`Edit(IsSpaceClaimGeometry=True)`。这是一条有用证据：Workbench 接受并记录了 True；但 visibility
仍是 `NOT_USER_OBSERVED`，所以不能进一步说 GUI 已显示、用户 session 已建立或 interactive/batch
完全等价。

本轮与 False 轮的可观测签名相同，能关闭的是：

> 单独把 Interactive 参数改成 True，不足以让当前 SendCommand checkpoint/marker 通过。

不能关闭的是所有 desktop/session/broker 因素，也不能评价从未调用的 RunScript。自动化实验中，
“参数改了而结果没变”只否定该单独干预的充分性，不自动证明该因素完全无关。

### 26.1 下一 file-only 状态机

SendCommand 必须标记为 `SKIPPED_BY_EXPERIMENT`，不能让旧 inline checkpoint 的 None 把 file 结果误压
成 `CHECKPOINT_NOT_REACHED`。RunScript-only 至少记录：

```text
RUNSCRIPT_CALL_EXCEPTION
RUNSCRIPT_RETURNED_ENTRY_EXACT
RUNSCRIPT_RETURNED_ENTRY_ABSENT
ENTRY_DELAYED_OR_EXIT_TRIGGERED
ENTRY_EXACT_BUILD_REPORT_ABSENT
BUILD_CONTRACT_PASS_OR_FAIL
```

immediate entry exact 只证明 child 已进入；build JSON、1 body/13 faces、1/1/11 groups、share、Refresh、
Mechanical、mesh 和 project 仍各有硬断言。三个时点都 absent 也只能说本轮未观测 entry，不能写
`.py` 不支持、权限根因或 child 确定完全没运行。

### 26.2 新增的 PowerShell 现实坑

handoff wrapper 中 `$Head:` 会被解析为 drive-qualified variable；应写 `${Head}:`。parser error 在 Git
命令前发生，不能拿来解释签名或 ANSYS 失败。这个小坑和前一轮 stderr/console wrapping 一样，说明
外层验证器必须先通过自己的语法与 machine-readable 合同。

## 27. 第二十二次实验的实现合同：RunScript-only（尚未实跑）

### 27.1 为什么移除 source-editor SendCommand

run #20/#21 已经证明：在当前 connected Geometry route 中，`SendCommand` 会在 post-call checkpoint
前阻断后面的目标 action。run #22 移除它，是为了让 `.py RunScript` 第一次成为 Edit 后可到达的直接
scripting action，不是宣称 `SendCommand` 普遍不可用。代码因此写
`SKIPPED_BY_EXPERIMENT`，而不是 `NOT_REACHED` 或 FAIL。该轮也不是与 run #19 的 byte-identical A/B：
instrumentation、分类 schema 和每轮注入的 absolute path 都不同。

这里的 RunScript-only 只限定 source Geometry editor。若前半段合同通过，journal 后半段仍精确允许
一个 `model_container.SendCommand` 执行 Mechanical inspection；所以不能写“整个 journal 没有
SendCommand”。

### 27.2 file-only 状态机怎样避免把未执行写成失败

状态机分别保存 `runscript_call_outcome`、entry timing、build-report state 和最终 classification。当前
受审分类集合是：

```text
RUNSCRIPT_NOT_REACHED
RUNSCRIPT_CALL_EXCEPTION_ENTRY_ABSENT
RUNSCRIPT_CALL_EXCEPTION_ENTRY_EXACT
RUNSCRIPT_CALL_EXCEPTION_ENTRY_DELAYED_OR_CLEANUP_OBSERVED
RUNSCRIPT_RETURNED_ENTRY_ABSENT
RUNSCRIPT_RETURNED_ENTRY_EXACT
ENTRY_DELAYED_OR_POST_EXIT_OBSERVED
ENTRY_LOST_AFTER_CHECKPOINT
ENTRY_SENTINEL_INVALID_OR_PARTIAL
ENTRY_EXACT_BUILD_REPORT_ABSENT
PROBE_INDETERMINATE
BUILD_REPORT_INVALID
BUILD_CONTRACT_FAIL
BUILD_CONTRACT_PASS
```

总体 suite FAIL 不能覆盖这个细分类。例如 direct call 抛异常、call 返回但 entry 缺失、entry 到 cleanup
后才出现、entry 曾出现后丢失、build JSON 不可解析，是不同的可观测事实，下一轮实验也不同。

### 27.3 exact entry sentinel 只证明到达第一条写入

child 的第一条可观测输出是固定二进制：

```text
payload = AJM005_CONNECTED_CHILD_ENTERED_V2\n
size = 34 bytes
sha256 = 3ee230fb69349453cf2f7f5275879c40423a3462e6d78baadb97237f415cecd7
```

只有 size 和 SHA 同时 exact 且无 probe error 才算 entry exact。文件存在但 bytes 不符属于
`ENTRY_SENTINEL_INVALID_OR_PARTIAL`；读取异常属于 `PROBE_INDETERMINATE`。即使 entry exact，也只证明
child 到达最前面的 builtin write，不证明 import、几何构造、1 body/13 faces、1/1/11 groups、transfer、
Mechanical、mesh、project 或 P1。

### 27.4 freeze 与 capture 为什么必须正交

`freeze` 固定分类所依据时点：正常路径用 `POST_EXIT`；仅对仍需 connected-build 失败诊断且 build
contract 尚未返回的异常路径，才先做 cleanup 前后 entry probe，再在 `FAILURE_POST_CLEANUP` freeze。
若 build state 已是 terminal 或 build contract 已返回，异常处理不会重复这组诊断。`capture` 是该类
failure freeze 后对 build JSON 的 best-effort 追取与解析。两者
分开不是消灭 TOCTOU，而是让 TOCTOU 可见：文件可能在两次读取之间出现、消失、写到一半或变得可读。

审查第一版协议时就出现了一个典型验证器 bug：它会拒绝“freeze 时 absent、capture 时出现 valid/FAIL/
invalid JSON”，也会拒绝“freeze 已见文件、capture 前文件消失”。修复原则不是把后读结果倒写成
immediate 证据，而是让 freeze classification 与 capture state 正交。另一个 bug 来自历史累计错误：
`build_report_probe_errors_at` 可以同时含旧 `POST_EXIT` 错误，而 existence 字段只属于最终 freeze；当前
是否出错必须检查 `freeze_probe` 是否也在错误列表中。

因此现有报告最多支持“某 checkpoint 观察到什么，稍后 capture 又观察到什么”。它不支持“两个字段
来自同一原子文件快照”，论文局限中必须保留这句话。

### 27.5 reachable-state validator 做了什么、没做什么

runner 不是只检查枚举拼写。它交叉约束：

- outcome 与 `execution_reach`；
- 四个 entry checkpoint、first-observed、delayed/lost；
- 当前与历史 probe error；
- normal/failure freeze、capture attempt、build existence/state；
- classification 与顶层 captured object/status 的基本一致性。

policy test 从 runner AST 抽取同一个 pure validator，重放 writer 可达的 late arrival/disappearance/error
状态，并用 contradiction mutation 确认 fail closed。这比只检查 JSON schema 强，但不是形式化证明。
当前 capability PASS 还必须同时满足：

```text
diagnostic_contract_ok = true
classification = BUILD_CONTRACT_PASS
build_report_state = CONTRACT_PASS
全部工程 assertions = true
全部声明 artifacts 通过 size/SHA/manifest 校验
```

已知限制是 capture error 字典内部字段和 normal contract 的部分顶层副本仍可进一步做双向约束；精确
profile SHA 与工程 assertions 防止它们制造当前 PASS，但这仍应作为验证器改进项记录。

### 27.6 为什么 AST 审查不能只搜索字符串

字符串搜索能看到 `.RunScript`，却挡不住先把对象或方法赋给 alias，再通过 `getattr`、subscript、
`operator.attrgetter`、`__builtins__` 或 IronPython/.NET reflection 调用。当前 policy 因而锁定：

- `source_system.GetContainer(ComponentName="Geometry")` 恰好一次并直接赋给 `source_geometry`；
- source editor 恰好 1 次 direct Edit、1 次 direct RunScript、2 次 direct/no-args Exit、0 次
  `source_geometry.SendCommand`；
- literal keywords 与 `Edit → RunScript → normal Exit → Mechanical SendCommand` 顺序；
- cleanup Exit 的 guard/ancestor；
- 禁止 source alias、method rebinding、computed dispatch、`__getattribute__`、`__builtins__` 和
  `GetType→GetMethod→Invoke` 等反射表面。

这只是对已签名 source 的静态形状约束，不是 Windows host 的 runtime sandbox，也不是运行证据。

### 27.7 实跑前结果栏必须保持空

```text
run_id = NONE
job_id = NONE
runscript_call_outcome = NOT_RUN
entry classification = NOT_RUN
build state = NOT_RUN
artifact manifest = NONE
visibility = NOT_USER_OBSERVED
P1 stage gate = NOT_RUN
```

只有签名提交、Windows clean sync、installed-skill hash 和 static policy 全部通过后，才允许启动新
case/job。实跑后按 report 填唯一分类；不能把实现完成、静态 PASS 或 reviewer PASS 写成 ANSYS 结果。
