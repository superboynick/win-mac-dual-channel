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
