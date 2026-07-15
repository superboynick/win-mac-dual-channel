# AirJet Mini 整机数字复原：当前状态

更新时间：2026-07-15
状态口径：**P0 公开证据冻结 v1 已通过；P1–P6 CAD/物理仿真阶段尚未通过。**

## 1. 已完成

- 唯一建模目标锁定为 AirJet Mini Gen1；G2 只保留为产品选择比较证据，不进入几何、参数、校准、九变体或 P1–P6，也不安排本冲刺迁移阶段。
- 第一代 Mini 的外形、功耗、总热、净热、压力能力、系统噪声和重量已进入参数注册表。
- 官方性能图右轴已纠正为 50 cm 系统噪声，不是流量；曲线点有 PDF 哈希、像素坐标、转换公式和自动复算脚本。
- 专利尺寸已按 `P` 类候选范围记录；膜片长度、孔间隔 `s`、最低喷速和中央锚定均未伪装成 Mini 产品实测值。
- 已建立 Layout-L/M/S 的整机候选搜索框架与可执行 notebook；候选能放入外形只表示几何可行，不表示内部结构已确认。
- 已完成 P1–P6 操作规划、仿真注释规则、阶段 Gate、运行日志/Git 规则和 Windows 交接手册。
- Mac/Windows skills 有版本锁、规范化 SHA256、必需文件清单和跨平台安装脚本。
- 项目 Python 审计、Windows PowerShell 审计、skill 安装和曲线复算都有自动化入口。
- Windows 硬件、软件、研究 ZIP 和 Python 已实测，结果写入 `WINDOWS_ENVIRONMENT_REPORT.md`。
- Windows 已完成第三方 PLE 清理并保留纯净官方 Ansys Student 2026 R1；核心程序签名、旧 1055/环境变量清理经 Mac SSH 复核。Workbench/Fluent 基础 Student checkout 已由 Windows 可见会话报告；005 alternate-route v2 已在签名 commit `9a88b7ad...` 端到端通过，但 P2–P5 物理能力仍未评价；详见 `reports/AJM_WIN_ANSYS_STUDENT_CLEANUP_2026-07-14.md` 与本节后续 005 记录。
- 为避免通用 GUI 代理只输出摘要而不执行软件，已建立 `airjet-ansys-automation` skill、
  hash-pinned 本地 MCP 和 SpaceClaim/Workbench/PyMechanical/PyFluent 四路 T0 脚本。
  Windows 已完成安装、签名/依赖/并发等负向检查；commit
  `6265043003dfb44b2b694ef3e91cfd84d7cc832b` 的确定性重试四路均为
  `PROCESS_EXITED_0 / PASS_CONTROL`，suite 为 `PASS_CONTROL_SET`，结束后相关进程数为 0。
  这只证明官方控制接口可控；005 T1 partial CAD 的 SpaceClaim 子集已在第四次签名运行通过，
  但 SpaceClaim→Workbench transfer set 仍失败，其他工程小模型仍为 `NOT_RUN`。
- 005 T1 的第一条 SpaceClaim→Workbench 小模型已完成脚本、固定 profile、冻结 predecessor
  manifest 和确定性 runner。commit `96f0799e...` 首轮已实跑：5/6 mm 脚本参数重建通过，但
  普通 Python list 不能传给 `CreateByGroups(System.String[])`。commit `aa914a6...` 第二轮越过
  类型边界并保存/重开产物，但解析指纹发现入口未进入最终 fluid（`200` 而非
  `203.1415927 mm³`，`zmin=1` 而非 `0`，`INLET=0`）；STEP 文本含
  `MANIFOLD_SOLID_BREP` 记录，但有效可导入实体及层级尚未证实，根层 body query 为 0。
  同机官方例子随后纠正了圆柱三点语义。commit `74e8557...` 第三轮确认 raw inlet、解析 union、
  `INLET/OUTLET/WALLS=1/1/11` 以及原生保存重开全部通过；STEP `GetAllBodies()` 进入唯一候选，
  但其 runtime shape 为通用 `TrimmedSpace`，旧指纹错误访问不存在的 `PieceCount`。commit
  `9652054...` 的第四轮用 occurrence geometry 与 master topology 分层检查关闭了这一问题：
  STEP 为全层唯一 body、单片、闭合、manifold，体积/bbox/13 个 faces 与原生模型一致，SpaceClaim
  首次报告 `PASS_PARTIAL_CAD_CAPABILITY`。Workbench 随后验证精确 predecessor 身份，但当前
  `.scdocx → Geometry.SetFile → Model.Refresh` 路线无法附加 geometry structure；因此
  Named Selection inspection、粗网格和 project save 都未到达，完整 CAD transfer set 仍 FAIL。
  commit `f3a1769...` 的第五轮只把更新语义换成
  `Model.Update(AllDependencies=True)`，到达标记证明 SetFile 返回、Update 被调用但同样无法附加；
  由此排除旧 update/refresh 顺序这一窄假设。commit `d10fa51...` 第六轮建立独立 Geometry source，
  但普通 Geometry component→Static Geometry 的 `TransferData` 组合被 v261 明确拒绝；下一实验
  转向同机官方 standard Geometry journal 的 `ComponentsToShare` 架构。commit `a4aa2be...` 第七轮
  已越过 share 与 `GetGeometryFileAndSaveData()`，但保持不变的 Model Component Update 仍 attach
  失败。commit `1d1c9ee...` 第八轮改用官方 Model container Refresh 仍出现同一 attach 失败，
  已排除 share topology 中的 update API 选择；下一轮显式 SpaceClaim Edit/Exit。八轮证据和哈希
  均已保留。commit `c965c73...` 第九轮的显式 Edit/Exit 均返回，但 downstream Refresh 仍 attach
  失败。commit `6f828fe...` 第十轮用同轮生产者已回读并冻结 SHA 的 STEP 诊断，成功到达
  Workbench share/save-data/Model Refresh、Mechanical inspection、粗网格和 project save：1 个
  body、1063 nodes、513 elements、50588-byte `.wbpj` 均有机器证据；但
  `INLET/OUTLET/WALLS` 对象和实体全为 0。脚本按设计把 native canonical assertions 保持 false，
  suite 仍为 FAIL。这证明通用 WB→Mechanical→mesh→project 管线可用，并把当前故障收窄到 native
  `.scdocx` attach/semantic bridge；不能把 STEP 几何可达伪报为 native Named Selection transfer。
  commit `4f80fc6...` 随后把 semantic reconstruction 拆为独立 profile/runner 并首次实跑：
  SpaceClaim producer、STEP/sidecar/report/manifest 身份链全部通过；Workbench source/share/save-data
  通过，但 `Model.Refresh()` 保存/附加临时 `SYS.mechdb` 失败，Mechanical 面枚举、负向 controls、
  1/1/11 重建、mesh 和 project 全部未到达。当前只能写 host attach 前置失败，不能写重建算法失败。
  commit `0fe714f...` 的单变量短 case ID 复测把 WB job root 从 176 降到 154 字符，随后
  `Model.Refresh`、Mechanical inspection 与 project save 全部返回，对 legacy path-budget sensitivity
  提供强支持。真实分类首次得到 `INLET=0/OUTLET=1/WALLS=12` 并被硬检查拒绝；未创建 Named
  Selections、未 mesh。下一轮只让失败分支保存 13-face map 与 negative-control 中间观测，不放宽
  匹配容差。commit `d107c40...` 已完成该观测：body=1、faces=13、四项 negative controls 全 PASS；
  位于精确入口中心的 face 44 面积为 `2.0 mm²`，而 producer sidecar 为 `π mm²`，因此面积条件单独
  导致入口 0 匹配。commit `63d8440...` 的 topology 观测显示 face 44 为 plane、2 edges、
  `[0,0,-1]` normal，13 个面三类 API 均无 error。commit `7a7f8e0...` 只把入口 hard anchor
  替换为 centroid+topology 后，第十五次签名实跑得到
  `PASS_STEP_SEMANTIC_RECONSTRUCTION_DIAGNOSTIC`：1 body/13 faces 唯一重建
  `INLET/OUTLET/WALLS=1/1/11`，创建前同名对象为 0，创建后对象/实体为 1/1/1 与 1/1/11，四项
  negative controls 全通过，并生成 1063 nodes/513 elements 粗网格及 50593-byte project。
  该 PASS 只属于 hash-bound STEP+sidecar 的 solver-side reconstruction；canonical native claims
  仍全 false。审查同时确认脚本两次重建只能证明等效参数驱动，不能证明 `.scdocx` 原生 driving
  parameter；native attach、native Named Selection transfer 与 native parameterization 仍需独立
  关闭，`P1_CAD_TOOLCHAIN_READINESS` 继续 BLOCKED。
  commit `41fa4a6...` 随后把同一短路径单变量用于 native route：case ID 16 characters、WB job root
  102 characters、frozen `.scdocx` input path 145 characters，但 SetFile、Edit/Exit、share/save-data
  返回后，`Model.Refresh()` 仍以同一“无法附加几何结构”失败；280.347 秒后 Mechanical inspection
  仍未到达。由此关闭“只缩短 native path 即可修复”的假设，下一轮只测试 hash-equal writable
  working copy，不解除 frozen predecessor 的只读保护。
  commit `3336c75...` 的 writable-staging 有意干预复测随后验证：本轮 frozen predecessor 前后均
  为只读且 32143-byte/SHA 不变；同路径长度、初始 hash-equal 的 working copy 在 Edit 前明确可写，
  运行结束仍存在且 size/SHA 未变。Edit/Exit、share/save-data 返回后，异常点仍是
  `Model.Refresh()`；整个 WB job 为 282.115 秒。结果关闭“本轮可写 staging 足以修复 attach”这一
  窄假设，但不能全局排除权限与其他因素联合作用。下一轮改查 Workbench-managed SpaceClaim
  Geometry editor 内部文档创建/导入的 materialization route，不再叠加路径或权限 workaround。
  commit `f15aae3...` 已把该路线拆成独立 connected-document diagnostic 并首轮实跑：空 Geometry
  cell、Edit、RunScript 和 Exit 都返回，但内层 `connected_spaceclaim_build.json` 未生成；因此在
  share/save-data/Refresh/Mechanical 之前 fail closed。当前只能定位为内层脚本执行或输出证据缺失，
  不能称为 connected transfer 已失败。`AIRJET_JOB_DIR` 在 SpaceClaim host 中缺失、陈旧或指向其他
  job 是优先假设而非确认根因。下一轮只嵌入绝对路径并增加 import 前 sentinel/stage/traceback，保持
  fixture、API 顺序、前驱范围和 Gate 合同不变。
  commit `0b32f5d...` 的 literal-path early-sentinel 复测随后确认：RunScript 返回后、Exit 后和 failure
  catch 三个同-run 检查点均没有 sentinel/build report，且无 probe error；Exit 前后约 2 ms。
  因此 child 中 `AIRJET_JOB_DIR` 指错报告位置已不是充分解释，入口仍未被观测，transfer 仍未到达。
  v261 官方资料明确 `.py`/`.scscript` 均受支持，但没有证明两者合法文件可逐字节等价，因此不把简单
  改后缀当严格 A/B。下一次在同一 editor 先用官方 inline `SendCommand` 写独立 sentinel，再保留现有
  `.py` RunScript，直接区分 scripting channel 与 file loader；API claims 不变。
  commit `abb1d9a...` 的 inline/file 对照随后在 producer PASS 后得到更早的直接异常：empty cell 与
  `Edit(Interactive=False)` RETURNED，但 `SendCommand` 仅到 CALLED 就抛 Workbench 空引用；
  post-SendCommand probe 与 `.py` RunScript 都未到达，failure freeze 中两个 sentinel/build report
  全 absent，cleanup Exit 返回。分类必须是 `CHECKPOINT_NOT_REACHED`，不能写成两通道都失败。
  下一轮只把受审 outer journal 的 Edit 改为 `Interactive=True`，检验 batch connected session 这一
  共同未决变量；其余 payload、API 顺序、path-generation/binding、timeout、fixture 逻辑和 Gate 合同
  不变；per-run absolute path 与注入后的 bytes 仍会重生成。
  commit `fe84454...` 的受审 outer journal 单参数复测随后得到同一外部失败签名：literal True 的 Edit RETURNED，
  recorded journal 也把它 canonicalize 为默认 interactive 写法，但 SendCommand 仍在 line 553 空引用；
  post-call probe 与 RunScript 未到达，cleanup Exit 返回。由此只关闭“改一个 Interactive 参数就足以
  修复”这一窄命题，不能声称真实 GUI/session 已被用户观察或所有 session 因素已排除。下一轮保持
  True，移除前置 SendCommand，让 `.py` RunScript 成为唯一 scripting action。
  run #22 随后在 commit `1a9696c...` 实跑：producer 的八项断言全真，状态为
  `PASS_PARTIAL_CAD_CAPABILITY`；connected Workbench 的 Edit、direct `.py RunScript` 和 Exit 均返回，
  但 post-RunScript、post-Exit、failure-pre 与 failure-post 四个检查点都没有观察到 34-byte entry
  sentinel 或 build report，且 probe-error 列表为空。connected build contract 到 `CALLED` 后以
  `FAIL_RUNSCRIPT_RETURNED_ENTRY_AND_BUILD_ABSENT` fail closed，精确分类
  `RUNSCRIPT_RETURNED_ENTRY_ABSENT`；share/save-data/Refresh/Mechanical/mesh/project 全部
  `NOT_REACHED`。最强结论仅为“调用返回但 child entry/build 未被观测”，不能写成 build 已执行后失败、
  `.py` 不受支持或 connected transfer 已失败。该 connected route 已冻结为
  `DEFERRED_CURRENT_HOST_ROUTE`，本冲刺不再追加 connected 探针。
- 已新增学习入口、ANSYS/005 实验手册、现实失败日志、run index 和论文方法—证据映射；
  后续每次运行会同步保留小型脱敏机器证据和 Git 外大产物哈希。
- Gen1 两张官方产品透视图已分别做 homography、10,000 次像素误差 Monte Carlo 和跨视图差比较；四个画出 vent 只作为 `I` 类顶盖候选，不用于推断 cell 数。
- 官方剖面已标注：只锁总厚度和定性流路，不缩放内部层厚或数绿色波形。
- 核心专利已建立产品部件映射表，定位改为本地 PDF 页码 + FIG. + printed column/line；中央锚定仍是候选，不是量产事实。
- Layout 候选已由 34 个 family 组合去重为 32 个唯一几何；A0 下 23 个可装入，工作主/备选为 `M-3x4-7.0` 与 `M+S-3x5-6.0`，当前评分覆盖率仅 20%。
- P0 Gate 证据与限制已冻结在 `evidence/P0_EVIDENCE_FREEZE_RECORD.md`。
- P1 的四个工作布局已生成求解器无关配置表；`TB0-PLACEHOLDER` 厚度表严格闭合 2.8 mm，并显式保留 0.735 mm 未识别残差，未把占位层伪装成产品事实。
- P1 可执行 CAD 合同已生成：6 个交付/残差变体 + 3 个单因素派生变体、342 条参数映射、3 类喷孔解释、两套四开口 vent、每配置两套单侧排气分支、10 条内部几何 R0 构造规则，以及 feature/成对 interface/Named Selection/open-question 表；新增的 vent riser 仅为四个 vent 投影内的 C 类局部连通闭合；252 条 Gate 行仍全部 `NOT_RUN`。
- Windows 006 完整产品 CAD 任务已写好；Gen1-only production schema/validator、九个 trusted variant blueprint、campaign 与 006/007 reviewer bridge 的静态合同已通过 CPython/IronPython、负向测试、MCP policy 和双项目审计。两个 006 production profile 仍未注册，`execution_state=STATIC_CONTRACT_ONLY_NOT_REGISTERED`，所以当前必须 fail closed，不得启动正式 CAD。
- V02 preliminary producer 已在 Windows 完成三次签名实跑并于 commit `64b57303...` PASS：主候选 `M-3x4-7.0__R50_BALANCED` 的 3×4/12-cell、972-hole、upstream/downstream 两个流体区均真实建立；两个 body 为 single-piece/closed/manifold，4/1 inlet/outlet、12/12 membrane、972/972 orifice faces 与 1 heat wall 全部闭合。十项断言和六个外部产物 size/SHA 与 MCP manifest 一致，runner 为 `PASS_PRELIMINARY_PRODUCER`。实际代理孔隙率为 `8.114445310611391%`；10% 仍是未锁定 proxy。STEP shape round-trip 最大 bbox/volume delta 为 `0.014975 mm` / `0.003996774 mm^3`，在记录的 STEP-only 容差内。
- V02 topology observer 已在 commit `9699df565d5b93bfe8bf8354834af7fc5f79624c` 完成修正版实跑：同一 MCP 会话的 producer `...-13950bddaec8` 与 observer `...-2fb76257a827` 均 exit 0，suite 为 `PASS_PRELIMINARY_TOPOLOGY_OBSERVER`。Mechanical 中 upstream 为 body 4288/100 faces，downstream 为 body 7231/978 faces；downstream 接口保留 972 个与预期 XY 完整对应的孔印记和大面 7158，upstream 对应孔口候选为 0、972 个预期位置全缺失，shared ID/coincident pair/cross-body duplicate 均为 0。精确分类为 `MIXED_OR_OTHER / UPSTREAM_ORIFICE_GEOMETRY_LOST_DOWNSTREAM_972_IMPRINTS_RETAINED`。这说明观测流程 PASS，却否决当前 STEP→Workbench/Mechanical 两区连通路线；没有 mesh、shared-node 或 conformality 证据，不能宣称 semantic、正式 006 或 P1 PASS。
- 005 alternate-route v2 于 `2026-07-15T10:04:43Z--10:06:02Z` 在 commit
  `9a88b7ad26d5d5c9f35d8a5f956df7038cfca0fd` 首次同轮端到端 PASS：SpaceClaim producer 与
  Workbench consumer 均 exit 0，参数化构造、原生保存/重开、STEP 导出/重导、hash-bound semantic
  sidecar、solver-side 1/1/11 语义重建、负向 controls、1063-node/513-element 粗网格和 50555-byte
  `.wbpj` 均有哈希证据。closeout 为 `PASS_START_P1 / START_006_ALTERNATE_ROUTE_ONLY`；这只解除 006
  alternate-route 的工具链前置阻塞，P1 Stage 仍 `NOT_RUN`，native 三项仍 `NOT_PROVEN`。证据见
  `logs/evidence/AJM005_T1_ALTERNATE_ROUTE_SUITE_20260715T100443733301Z_d1743e81/`。
- 006 后的 007 独立复核已定义：先核验真实 005 副本、精确 006 commit 合同 bundle、9 个 variant 的 producer/observer 身份、独立 artifact-manifest、STEP/sidecar/binding/observation、solver actual IDs、机器检查/252 行 evidence 和完整目录 SHA256，再实际调用 production validator；computed missing/unexpected/dangling/orphan/coverage/assignment 结果必须逐字段闭合。finalize 复用同一硬校验并要求 252/252 hard Gate PASS。transfer limitation 不可接受。当前没有 006 产物，所以 007 也未运行。

## 2. 尚未完成，不能声称完成

| 阶段 | 当前状态 | 缺失的实际产物 |
|---|---|---|
| P0 证据冻结 | **PASS v1** | 若得到新 D 类资料、实物/CT 或发现证据冲突，需建立 v2；当前内部未知量不会被伪装成已解决 |
| P1 整机 CAD | 005 alternate-route v2 工具链前置已 PASS；V02 两区 preliminary producer 与 topology observer 均已实跑 PASS；observer 确认 STEP handoff 只保留 downstream 972 个印记而丢失 upstream 972-interface，当前两区路线被拒绝；输入合同和 Gen1 production 静态语义合同完成，正式九变体 CAD 未开始，两个正式 006 production profile 尚未注册，P1 BLOCKED | 改变接口传递表示并重新 observer，证明两侧 972-interface 在 solver 中可审计且可进入后续网格；随后才注册正式 producer/observer profiles 并运行九变体 006。P1 Stage 仍 `NOT_RUN`，P1–P6 均未通过 |
| P2 执行片结构 | 未开始 | 材料栈候选、模态、谐响应、位移场、功耗闭合 |
| P3 单 cell 动态 CFD | 未开始 | 网格/时间步独立性、周期稳定、质量守恒、降阶传递关系 |
| P4 整机气动 | 未开始 | 全部 cell/孔板/歧管/出口模型、压力能力扫描、相位对比 |
| P5 整机 CHT | 未开始 | 扩散板/TIM/热源/自热、温度场和 5.25/4.25 W 热账户 |
| P6 标定与不确定性 | 未开始 | 训练/验证分离、灵敏度、候选布局后验、失败回退记录 |

仓库审计 PASS 只表示文件、表结构和证据不变量没有被破坏。P0 的独立 Gate 记录已经 PASS，但这**不等于 P1–P6 任何 CAD/物理 Gate PASS**。ZIP、Git 和 skills 能让另一台 Codex 读懂项目，但不能替代 CAD、网格、求解结果和人工工程判断。

## 3. 下一步执行顺序

1. 归档 run #22 后冻结当前 connected route：`RunScript` 已返回，但四个检查点都未观察到 child
   entry/build；该事实不足以判定 build 或 transfer 成败。48 小时冲刺内不再追加 marker-only 或新的
   connected 探针。主路线迁移为签名 SpaceClaim 脚本建模 → native save/reopen 检查 → STEP export →
   hash-bound semantic sidecar → Mechanical/Fluent 侧语义重建。逐实体 unique key、owner、cell/local
   coordinates、cardinality、adjacency、actual solver IDs、direction/bbox 与无环全链 hashes 已形成 Gen1
   production 静态合同。alternate semantic confirmation 已在 commit `9a88b7ad...` 通过，但 V02
   topology observer 随后实测当前 STEP 两区 handoff 丢失 upstream 972-interface；在接口传递表示被
   修复并由新 observer 关闭前，不注册正式 006 profiles，也不启动完整产品 006。外部 native attach、native
   parameterization 与 native Named Selection transfer 均保持 `NOT_PROVEN`，005 closeout 也不能写成
   P1 Stage PASS。
   旧行动项的处置也已显式冻结：简单 `.py`→`.scscript` suffix 实验因没有合法序列化逐字节等价证据而
   不再执行；native 短路径/writable-staging/connected 历史证据继续保留，但不在 native profile 中用
   solver-side reconstruction 补名；Mechanical/Fluent 可删除 T1 能力检查并入 alternate-route
   confirmation 与后续 pilot 的受审 profiles。run #19--#22 的完整因果链仍见
   `learning/T1_CAD_TRANSFER_WORKBOOK.md` 与 `logs/REALITY_AND_FAILURE_LOG.md`，没有被 run #22 覆盖。
2. V02 固定 producer 与修正版 observer 已完成。真实 solver import 没有给出 shared-face 或 paired-interface：downstream 972 个 imprint 全在，upstream 972-interface 全失，因此当前 STEP 两区表示被拒绝。下一轮必须改变 native/connected/re-authoring 或受审 solver-side interface reconstruction 路线，再用同类 observer 证明两侧 actual IDs/owner/adjacency 和后续 mesh 入口；不得靠放宽 area/位置阈值“找回”不存在的面。只有新路线关闭且 `profiles.json` 中两个正式 006 production profile 已注册并由静态 policy/双审计锁定后，才执行
   `windows-prompts/AJM_WIN_P1_FULL_PRODUCT_CAD_BUILD_006.md`：同一母版生成 4 个整机配置、
   6 个交付/残差变体和主配置 3 个有独立 ID/Gate 的单因素派生变体。006 最多写
   `PENDING_PEER_REVIEW`，不能由生成模型的同一会话自评 P1 PASS。
3. 已提交的 Ansys 30 天官方试用申请继续等待；只有 entitlement 实际激活后才执行 004，不让等待阻塞 Student 可完成的 P1 工作。
4. 先闭合 2.8 mm 厚度预算、四个候选顶盖 vent、单侧 spout 和全流路连通，再允许给 `S_image`/`S_geometry` 正式评分。
5. P1 Gate 通过后，才按 P2 → P3 → P4 → P5 → P6 顺序推进；不以高保真单 cell 替代整机主线。

## 4. 用户需要理解的边界

- “尽可能像产品”在无实物条件下意味着：外部直接数据锁定，内部未知保留候选，用多个公开系统指标筛选；不是把专利图直接宣称为量产 Mini 内部。
- `1750 Pa` 是公开压力能力，公开资料没有给出该压力对应流量；必须另做低背压流量/热输运算例和压力能力扫描。
- `21 dBA` 是产品装入系统后、50 cm、A 计权条件；没有安装声学和传播模型时，只能做趋势代理，不能把局部 CFD 压力脉动直接数值拟合为 21 dBA。
- 第一篇论文由用户撰写；仓库提供可复核的模型、方法、参数来源、运行记录和图表源数据，不代写结论。
