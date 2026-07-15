# AirJet 仿真注释

此文件由我随项目进展维护。它不写论文内容；它记录你每次建模和运行时“为什么这样做、证据来自哪里、结果能说明什么、不能说明什么”。

## 标签规则

- `D`：具体产品官方资料直接支持，可锁定为该型号目标。
- `P`：专利实施例或范围，只能约束候选，不能写成量产 Mini 事实。
- `I`：由官方图或多个事实导出的几何/物理推断，必须带推导与误差。
- `C`：为匹配多个独立指标而待标定的参数。
- `U`：未知或不可辨识，必须保留替代方案。

## AJM-P0-001：完整产品目标定义

日期：2026-07-12  
状态：P0 v1 已冻结；P1–P6 待执行

**整机目标**：第一代 AirJet Mini，官方包络 27.5 × 41.5 × 2.8 mm。最终模型覆盖外壳、全部候选 cell、完整进气/排气流道、孔板、冲击通道、热扩散面、TIM 和芯片。

**性能目标**：最大电功耗 1 W；官方工况下总热耗散 5.25 W、净热移除 4.25 W；最大背压 1750 Pa；系统内 50 cm 最大噪声 21 dBA；重量 11 g。功耗—净热/噪声曲线已初步数字化。

**多尺度说明**：单 cell 高保真模型不是最终产品；它向整机模型提供位移场、净流量和压差传递函数。最终至少完成一个无对称简化的整机气动/CHT 算例。

**型号选择**：Mini Gen1 的尺寸、横截面、功耗和性能曲线公开链最完整，因此优先于 G2；G2 是迁移验证目标，PAK 是系统级背压/阵列参考。

## AJM-P0-002：内部布局尚未锁定

日期：2026-07-12  
状态：P0 v1 候选搜索完成；P1–P5 物理筛选待执行

不能通过宣传图中的绿色波形数量直接认定执行单元数。先建立 Layout-L/M/S 三种满足产品外形和专利广义 4–10 mm 范围的候选；6–8 mm 优选实施例给予更高先验权重，再用活动面积、总功耗、压力/流量、质量和热均匀性共同淘汰。

## R0A-001：单元子模型定义

日期：2026-07-12  
状态：待建 CAD

**目标**：复原一个以中央锚定压电执行片驱动、上进气、上下双腔、孔板微喷和近壁冲击/侧向排气为核心的 AirJet 类单 cell。此模型现在明确为 AJM 整机模型的结构/流体校准子模型，不是最终交付物。

**P 类专利约束**：执行片广义 4–10 mm、优选 6–8 mm；8 mm 实施例频率 20–25 kHz；位移优选 10–60 μm；顶腔、孔宽、孔间隔 `s`、开孔率和冲击间隙均为专利候选范围，详见 ledger E02–E15。它们不是 Mini 的直接产品数据。

**关键推断**：采用 8 mm × 8 mm 的单 cell 平面尺寸，顶板进气口居中，中央锚点宽 2.25 mm，孔板初始开孔率 10%。这些是可追溯的初始几何，不宣称对应某一代 Mini 的精确生产图。

**尚不能做的事**：不设稳态入口速度代替膜片；不做热优化；不假定真实 PZT 层厚或驱动电压；不宣称“这是 AirJet 内部结构”。

**当前证据结果**：Mini 数据表已锁定外包络/系统指标；官方透视图、剖面、像素坐标、homography、像素误差和跨视图差已保存。现阶段只确定 P1 工作顺序，仍需用整机质量、功耗、压力能力与热目标淘汰候选。不得把专利 cell 参数升级为产品锁定值。

## AJM-P0-003：官方图坐标化

日期：2026-07-13
状态：P0 v1 已冻结

**方法**：对 Gen1 数据表中 636 x 387 和 547 x 257 两张嵌入产品图分别选择四个顶面角点，映射到 27.5 x 41.5 mm 矩形。角点 `+/-3 px`、vent PCA 端点 `+/-2 px` 通过每视图 10,000 次 Monte Carlo 传播。

**结果能说明**：两张官方渲染都画出四个 elongated top vent objects；可用于第一版顶盖候选和投影比较。剖面直接支持多个膜片、脉冲射流、底部热扩散面和单侧 integrated spout 的定性拓扑。

**结果不能说明**：四个画出 vent 不是已证实的真实进气组，更不等于四个 cell。两视图 vent 中心横向差约 1.57--2.67 mm，说明渲染系统误差大于纯像素误差。剖面绿色波形、黄色/蓝色/红色箭头和 Schlieren 图不能数 cell/孔、测喷速或求流量；内部层厚不能从 2.8 mm 示意剖面按比例锁定。

**追溯**：`evidence/OFFICIAL_IMAGE_COORDINATE_METHOD.md`、`official_image_measurements.csv`、`annotated_figures/gen1_vent_homography_results.csv` 和生成脚本。

## AJM-P0-004：专利到产品部件映射

日期：2026-07-13
状态：P0 v1 已冻结

**决定**：中央锚定 + 上下腔 + 周边转移路径 + 孔板 + 冲击通道作为 R0 专利相容主候选；多 cell、共享板和相位驱动作为整机模型必须检查的候选机制。

**限制**：专利证明的是 Frore 专利族实施方式，不证明 Mini/G2 量产结构。edge/adhesive/rotational anchor、分隔/共享腔和不同 outlet/duct 仍是替代方案。定位统一使用本地 PDF 页码 + FIG. + printed column/line；旧的网页行号 `paragraph 864/866` 已移除。

**追溯**：`evidence/patent_product_component_map.csv`、`SOURCE_PROVENANCE.md`、registry P001--P014。

## AJM-P0-005：布局工作主/备选

日期：2026-07-13
状态：P0 工作顺序已冻结，真实布局未识别

**去重**：34 个 L/M/S family 组合对应 32 个唯一几何；A0 下 23 个可装入、9 个仅在 A0 下不装入。

**工作顺序**：`M-3x4-7.0` 为 P1 工作主候选；唯一几何 `M+S-3x5-6.0` 为备选；`L-2x4-8.0` 与 `S-3x5-5.5` 保留为 model-form sentinels。

**评分解释**：目前只打 geometry 与 cell-count complexity 代理，覆盖率 20%；image/modal/power/flow/thermal 为空，不重归一化。1750 Pa 只作压力能力扫描，另在较低背压检查非零净流和热输运；不得虚构 1750 Pa 对应流量。

**追溯**：`evidence/build_layout_candidate_scores.py`、`layout_candidate_scores.csv`、`layout_candidate_constraints.md`。

## AJM-P1-TOOL-001：Ansys 激活前工具链基线

日期：2026-07-13
状态：历史激活前基线；已被 2026-07-14 纯净 Student 基线取代

**观察**：Windows 上的 Ansys 2026 R1 Workbench 与 Static Structural、Modal、Harmonic Response、Fluid Flow (Fluent) 模板可见；SpaceClaim/Discovery 未进入可用建模界面，Mechanical 最小结构求解未完成，Fluent 单核 checkout 后退出。

**决定**：不因软件图标、安装目录或 Workbench 模板存在而宣布 P1 就绪。该测试发生在第三方 PLE 清理前，只保留作失败对照。

**模型影响**：目前没有生成 CAD、网格或结果，因此 P0 几何候选和参数证据没有变化。若 004 只有 Mechanical/Fluent 通过而 CAD 仍不可用，可改用中性 STEP 主几何，但必须重新验证 Named Selections、流体负体积和往返拓扑。

**追溯**：`reports/AJM_WIN_ANSYS_CAPABILITY_SMOKE_003_SUMMARY.md`、Windows 原始报告 `C:\Users\admin\Downloads\AIRJET_ANSYS_CAPABILITY_SMOKE_003.txt`。

## AJM-P1-TOOL-002：纯净官方 Student 基线

日期：2026-07-14
状态：清理/签名基线 PASS；P1--P5 能力待 005

**观察**：第三方 PLE 卸载后，Windows 可见会话报告 Workbench 基础启动和 Fluent Student 本地许可池 checkout 成功。Mac SSH 再验证 PLE 卸载项/服务、1055 监听和 `ANSYSLMD_LICENSE_FILE` 均为空；官方 Student 根目录和 Workbench、Fluent、Mechanical APDL、SpaceClaim 核心程序均为 `Authenticode=Valid / ANSYS Inc.`。

**决定**：不等待 30 天官方试用审批。先用 005 判断 Student 是否足以开始 P1；只有原生参数化、Named Selections、Volume Extract、连通、原生保存、Workbench 几何传递和 Named Selections 传递全部通过，才可开始 P1，并把 STEP、P2/P3/P4/P5 限制分别记录。005 只判定工具链就绪度，`P1_STAGE_GATE=NOT_RUN`；Student 安装存在不等于任何物理 Gate PASS。

**警告**：`python_site_syscplg` 与 `cuDSS` 解压失败使 System Coupling/GPU 稀疏求解保持未验证。需要前必须用官方安装器修复；不能用当前基础 Fluent 启动结果替代这些功能测试。

**追溯**：`reports/AJM_WIN_ANSYS_STUDENT_CLEANUP_2026-07-14.md`、`windows-prompts/AJM_WIN_ANSYS_STUDENT_CAPABILITY_SMOKE_005.md`。

## AJM-P1-GEO-001：TB0 占位厚度预算与布局输入

日期：2026-07-13
状态：P1 输入已生成；内部层厚仍未识别

**直接约束**：总厚度 `D003=2.8 mm`。

**候选/推导**：顶腔、执行片和冲击间隙取专利候选 `P005/P002/P010`；底腔 `C018=P004/1000+P006=0.04 mm`；顶盖、孔板、spreader 和内部支撑为 `C009/C015/C016/C017` 占位候选。未分配部分严格由 `C019=D003-sum(allocated layers)=0.735 mm` 计算，初始用 `C020=0.5` 上下对称分配。`C018/C019` 是公式输出，必须由父参数重算，不允许独立调整。

**边界**：厚度算术闭合只通过几何总厚度检查，不通过“内部结构已识别”检查。`C019` 的物理部件、材料和位置都是 `U`；`C017/C019_TOP/C019_BOTTOM` 只能作几何记账，禁止分配材料、质量或进入结构/CHT。`P002=0.275 mm` 是 8 mm 专利执行片占位值，跨尺寸用于四个 P1 配置不表示 5.5/6/7 mm 布局得到相同专利厚度支持；P2 前必须按尺寸分支。P1 还必须比较残差位置，并结合质量、图像、碰撞和流体连通筛选。

**孔数代理**：配置表按 0.25 mm 圆孔、10% 候选开孔率和膜片面积代理估算约 924--1198 个孔，只用于 Boolean/网格规模规划。真实活动孔板面积和 `separation s` 图义未锁定，代理数不能写成真实孔数。

**追溯**：`parameters/full_product_parameter_registry.csv`、`parameters/build_p1_cad_inputs.py`、`parameters/p1_layout_configuration_matrix.csv`、`parameters/p1_thickness_budget.csv`。

## AJM-P1-GEO-002：整机 CAD 可执行合同与模型形式分支

日期：2026-07-14
状态：合同/输入已生成；CAD 与 P1 Gate 均未运行

**问题**：P0 已经知道整机必须有顶盖开口、孔板、冲击通道和单侧 spout，但 `C005` 排气三维尺寸、vent 真实投影和专利 `P008 separation s` 的几何含义仍未知。若只给 Windows 一份文字手册，它会在 CAD 中临场补尺寸，导致模型不可复现。

**决定**：新增生成式 P1 合同。它把“存在、拓扑、精确几何、所选分支”四类证据分开，并把每个 CAD 变量绑定到 D/P/I/C/U 来源。主布局保留 `C020=0.25/0.50/0.75`；vent 保留图像包围框槽和第二视图中心线+P013 槽宽两套完整候选；单侧排气对每个配置保留全宽矩形与半宽线性收缩两支。为了不让 CAD 端临场补尺寸，另锁 10 条 C 类 R0 构造规则：cell 中心/膜片、每 cell 方形底腔、中央锚 datum、分区 datum、共享顶腔、四个 vent 投影内的局部候选 riser、外围转移间隙、side-wall 流体边界、残差数值封闭和每 cell 中心落孔。vent riser 只解决候选模型连通，不表示 C019 整层为空气；中央锚和分区仅为无 Boolean/无材料的 construction datum，避免把未知实体偷偷写进产品。三条单因素比较拥有独立 variant ID、父项 diff 和完整 Gate 行；总计 9 个变体、252 条初始 `NOT_RUN` Gate。

**孔距逻辑**：`d=0.25 mm, phi=10%` 导出方阵节距约 0.700624 mm。若把 `P008=0.5 mm` 直接当中心节距，R0 方阵开孔率约 19.635%，与当前开孔率范围冲突，因此保留为哨兵而不建成交付 CAD；若解释为边缘间距，节距为 0.75 mm、开孔率约 8.727%，保留为替代候选。这是对解释分支的筛选，不是对专利本身的否定。

**真实性边界**：公开数据只把外包络锁为 D 类。vent 候选仍是 I/C，排气平面闭合是 C，`C017/C019` 仍是 U/C 几何记账。模型生成成功不会把这些项升级为量产事实，也不会关闭开放问题。

**执行边界**：005 必须先证明 Student 的参数化、Named Selections、Volume Extract、连通、原生保存和 Workbench/Named Selection 传递能力；随后 006 才能建立完整产品。006 只能输出 `INCOMPLETE/PENDING_PEER_REVIEW`，不能宣布 P1 PASS。独立复核角色不绑定 Mac 或 Windows。

**残差数值处理**：`C017/C019` 不参与物理 Boolean，也不当空气。P1 只直接构造合同声明的流体体并 union；`FLUID_DOMAIN_CLOSURE_DATUM_C` 仅在厚度预算 Z 边界提供数值封闭。严禁用“外包络减所有候选固体”抽流体域，否则未识别残差会被错误解释为空气。

**接口处理**：每个接口使用 A/B feature 各自拥有的一对 Named Selections；允许 matched 或 nonconformal，但不能用同一 owner 的 selection 冒充两侧。外部入口/出口域在 P1 可选、P4 必需；内部 vent opening 到 product outlet 连通在 P1 必需。

**独立复核**：006 完成后由 007 校验报告唯一键、Git 祖先、run-root 和全部外部文件 SHA256，再生成 252 行 review worksheet。准备 PASS、仓库审计 PASS 和 006 完成状态都不等于 P1 PASS。

**追溯**：`parameters/P1_CAD_CONTRACT_METHOD.md`、`parameters/build_p1_cad_contracts.py`、`geometry/contracts/`、`checklists/p1_cad_gate_matrix.csv`、`windows-prompts/AJM_WIN_P1_FULL_PRODUCT_CAD_BUILD_006.md`。

## AJM-P1-TOOL-003：Phase B 冻结交接路径与 252/252 硬门禁

日期：2026-07-15
状态：Gate/复核合同迁移完成；alternate-route v2 组合确认与正式 006 尚未运行

**取代范围**：本条取代 `AJM-P1-TOOL-002` 与 `AJM-P1-GEO-002` 中把 external native attach、native parameterization 或 native Named Selection transfer 视为 P1 启动必要条件的旧执行边界；历史观测保留，不改写为成功。

**冻结路径**：签名 SpaceClaim 脚本参数化建模 → native save/reopen → STEP export/reimport → hash-bound semantic sidecar/binding → Workbench/Mechanical STEP import → solver-side semantic reconstruction。重建必须逐实体校验唯一 semantic key、cardinality、adjacency 与完整 hash chain。`EXTERNAL_NATIVE_ATTACH`、`NATIVE_PARAMETERIZATION`、`NATIVE_NAMED_SELECTION_TRANSFER` 保持 `NOT_PROVEN`，不得从替代路径 PASS 推导为原生路径 PASS。

**Gate 影响**：P1 Gate matrix 的 252/252 行全部为 hard Gate；9 个 `G4_STEP_TRANSFER` 和 9 个 `G4_WB_TRANSFER` 都不能接受 transfer limitation。005 仍只判定是否允许开始 P1，必须保持 `P1_STAGE_GATE=NOT_RUN`；006 即使生成全部证据也只能到 `PENDING_PEER_REVIEW`，不能自评 P1 PASS。

**追溯**：`parameters/P1_CAD_CONTRACT_METHOD.md`、`checklists/p1_cad_gate_matrix.csv`、`checklists/P1_CAD_INDEPENDENT_REVIEW_METHOD.md`、`windows-prompts/AJM_WIN_P1_FULL_PRODUCT_CAD_BUILD_006.md`。

## AJM-P1-GEO-003：V02 两区 preliminary 整机 CAD

日期：2026-07-15
状态：Windows preliminary producer 已实跑 PASS；observer 结果见 AJM-P1-GEO-004；正式 006 与 P1 Gate 均未运行

**目标**：在不缩成单 cell 的前提下，用主候选 `M-3x4-7.0__R50_BALANCED` 提前实测完整 12-cell/972-hole Boolean、两区接口、native reopen 和 STEP reimport。该 pilot 用来发现实际 ANSYS 拓扑，不替代正式九变体 006。

**两区表示**：`FLUID_UPSTREAM` 含 vent/riser、top plenum、perimeter gap、bottom chambers 和 orifice throats；`FLUID_DOWNSTREAM` 含 impingement channel、manifold 和 outlet。孔口面可能导入为 shared ID 或 coincident pair；当前正式合同不得在运行前伪定其中一种。

**孔隙率**：972 个直径 0.25 mm 圆孔对应膜片面积代理孔隙率约 8.114445%。表中 10% 是早期 proxy；差值必须记录，不能改孔数或改写测量来制造相等。

**硬检查**：4 inlet、1 outlet、12 membrane top、12 membrane bottom、972 upstream orifice、972 downstream orifice、1 heat wall、2 个 closed/manifold/single-piece bodies；native/STEP 几何指纹与 6 个产物 hash/size 必须闭合。输入来自同签名 commit 的 15 文件 dependency manifest，不读取可变工作树。

**实测结果**：签名 commit `64b57303b324aa1c98890d4241462814678af41f` 的 job `AJM006-V02-PRELIMINARY-1082d551ee85` 得到 `PASS_PRELIMINARY_PRODUCER`；上述计数全部闭合，实际代理孔隙率为 `8.114445310611391%`。native 与 STEP 重导均为两个 closed/manifold body。STEP 最大 bbox/volume drift 分别为 `0.014975 mm` 与 `0.003996774 mm^3`，在明确记录的 STEP-only `0.02 mm` / `0.005 mm^3` 阈值内；native 仍保持 `0.005 mm` bbox 门槛。

**producer 阶段未决拓扑**：STEP 中 downstream face decomposition 从 native 978 faces 合并为 6 faces；本 pilot 只检查 STEP shape equivalence，不要求面数或名字持久化。该未决项后来由 AJM-P1-GEO-004 的 Workbench observer 实测关闭，并得到“当前 STEP 两区路线单侧接口丢失”的否决结果，而不是 shared/coincident schema。

**声明边界**：成功只能写 `PASS_PRELIMINARY_PRODUCER`。`formal_006_completion=false`，P1--P6 均 `NOT_RUN`；没有 mesh、solver、semantic reconstruction 或产品真实性升级。

**追溯**：`automation/ansys/approved/006/v02_preliminary_producer.py`、`automation/ansys/run_v02_preliminary_006.py`、`windows-prompts/AJM_WIN_V02_PRELIMINARY_006.md`、`logs/evidence/AJM006_V02_PRELIMINARY_20260715T113939945030Z_1082d551ee85/`。

## AJM-P1-GEO-004：V02 Workbench topology observer 与单侧接口丢失

日期：2026-07-15
状态：preliminary observer PASS；当前 STEP 两区 handoff 被拒绝；正式 006 与 P1 Gate 未运行

**观测对象**：commit `9699df565d5b93bfe8bf8354834af7fc5f79624c` 在一个 MCP 会话内先生成 producer job `AJM006-V02-PRELIMINARY-13950bddaec8`，冻结 manifest，再运行 observer job `AJM006-V02-PRELIMINARY-2fb76257a827`。两者均 exit 0，predecessor 前后哈希不变，Workbench import、Mechanical inventory、分类和 project save 全部返回。

**三个几何内核的实际分解**：SpaceClaim native 中 upstream/downstream 为 2044/978 faces；SpaceClaim STEP reopen 为 2044/6 faces；Workbench/Mechanical 中为 100/978 faces。Mechanical 保留名称，故 upstream 绑定为 body 4288、downstream 为 body 7231；z 范围只作 fallback。face count 只用于诊断，不能跨内核承担角色身份。

**孔口识别**：以接口 z、`GeoSurfacePlane`、单边界环、0.25 mm bbox x/y spans、期望 XY 和 `0.02 mm` XY/Z/bbox 容差为锚。Mechanical 报告的同一候选 face area 与 SpaceClaim 理论圆面积不稳定，因此 area 只作诊断，不能靠放宽面积阈值改变接口是否存在。

**结果**：总 face references/unique IDs 为 1078/1078，cross-body duplicate 为 0。downstream 接口 973 faces 中有 972 个孔印记与期望 XY 完整一致，另有大面 ID 7158；upstream 孔口候选为 0，972 个预期位置全缺失。shared interface candidate、same-ID pair 和 opposite-normal pair 均为 0。精确分类为 `MIXED_OR_OTHER / UPSTREAM_ORIFICE_GEOMETRY_LOST_DOWNSTREAM_972_IMPRINTS_RETAINED`。

**为什么 PASS 仍不能求解**：`PASS_PRELIMINARY_TOPOLOGY_OBSERVER` 只表示 hash-bound 观测链完整执行并给出可审计结果。本轮没有 mesh，`shared_node_or_conformal_mesh=NOT_EVALUATED_NO_MESH`；当前合同下不能把这两个导入 body 当作已连接的两区拓扑，也不能把它写成“网格已失败”。

**决定**：否决当前 STEP 两区 handoff。下一步改变 native/connected/re-authoring 或受审 solver-side interface reconstruction 表示，并重新 observer；修复前不注册正式九变体 profiles。`formal_006_completion=false`，P1--P6 均 `NOT_RUN`。

**追溯**：`automation/ansys/approved/006/v02_preliminary_topology_observer.wbjn`、`automation/ansys/run_v02_topology_observer_006.py`、`windows-prompts/AJM_WIN_V02_TOPOLOGY_OBSERVER_006.md`、`logs/evidence/AJM006_V02_TOPOLOGY_OBSERVER_20260715T122907417508Z_2fb76257a827/`。

## AJM-P1-GEO-005：V02 Parasolid x_t solver-handoff 诊断候选

日期：2026-07-15
状态：Windows converter 实跑失败并关闭；未产生 x_t，observer 未运行；正式 006 与 P1 Gate 未运行

**单一改变**：保持完整 V02、12-cell/972-hole、两流体区、参数和 Mechanical 分类目标不变，
只把 solver handoff 候选从 STEP 改为 Parasolid x_t。STEP 继续输出/保留作归档，不把 x_t 冒充
通用 STEP transfer。

**转换边界**：converter 只从冻结 native 的 job-local staging 副本导出 x_t 并回读，要求两体
single-piece/closed/manifold、逐体 face count、bbox/volume envelope 在记录容差内；它明确是
representation conversion，不声称 interface topology 已证明，也不修改 predecessor native。

**observer 硬门**：Workbench/Mechanical 按 name/z 绑定角色，逐角色比较 solver 与 x_t 回读的
face count、bbox、volume；孔口 shared/coincident 判定还要求 972 点 XY、`AdjacentBodies` 和逐对
centroid/plane/bbox/area/normal。观察链 PASS 与 `PASS_CANDIDATE_ROUTE_TO_MESH` 分离；后者也不等于
mesh/shared nodes/P1 PASS。

**当前结果**：converter 已通过 predecessor、staging 和 native reopen，但显式 v261
`ExportOptions.Create()` / `ParasolidVersion.V23` 后仍未生成 `product.x_t`；observer 按设计未启动。
这关闭当前环境的 x_t 诊断路线，不是整机几何失败，也不提供 mesh 或 P1 证据。

**追溯**：`automation/ansys/approved/006/v02_parasolid_converter.py`、
`automation/ansys/approved/006/v02_parasolid_topology_observer.wbjn`、
`automation/ansys/run_v02_parasolid_topology_006.py`、
`windows-prompts/AJM_WIN_V02_PARASOLID_TOPOLOGY_OBSERVER_006.md`。

## AJM-P1-GEO-006：V02 native staging Workbench observer

日期：2026-07-15
状态：一轮 PASS、一轮 attach FAIL；972 shared membership 已观测但重复性未闭合；mesh/P1 未运行

**目的**：直接观察 producer 的 `product_two_zone.scdocx` 在 Workbench/Mechanical 的实际 body/face
拓扑，区分 STEP translator 的单侧损失与 native attach 本身的能力边界。

**安全序列**：同一 MCP 会话重新运行 producer；observer 只接收 report、two-zone native、face
inventory、native reopen 四件前驱产物。native 先复制为 job-local staging 并校验 SHA；Workbench
仅 SetFile、Refresh、Mechanical GeoData inventory 与 Save。native 分支不 Edit、不 mesh、不求解。

**PASS 实测**：签名 tip `0fa89686820c737f7dc98ce94dea27252e4d8b86` 的 producer
`AJM006-V02-PRELIMINARY-a768ecd0008e` 与 observer `AJM006-V02-PRELIMINARY-0600a08e2a83`
均 exit 0。Mechanical downstream/upstream 为 body 316/1950、978/2044 faces；两侧各 972 个
XY 候选完整配对，same actual face ID 与双 body membership 均为 972，分类为
`972_SHARED_SINGLE_FACE / SHARED_ID_MEMBERSHIP_CONFIRMED`。source/copy/final SHA 一致。

**FAIL 实测**：同一签名 tip 的 producer `...-939d21f59c47` 生成另一 native 字节哈希；observer
`...-c1ff3339dcb9` 的 predecessor/staging SHA 仍闭合，但 `Model.Refresh()` 无法附加几何结构，
Mechanical 未到达。两轮 native 字节不同，故当前结论是 route candidate 已观察到、重复性未闭合。

**决定**：先做固定无物理 mesh/repeatability 诊断；在实际证明 shared nodes/conformality 与可重复 attach
前，不写 mesh-ready、正式 006 或 P1 PASS。split STEP 保留为 attach 再失败时的受审 fallback。

## AJM-P1-GEO-007：V02 split STEP 转换候选

日期：2026-07-15
状态：16-profile 静态包 PASS；Windows `NOT_RUN`；native repeatability 诊断期间暂缓

**单一改变**：从同一冻结 two-zone native 分别删除另一流体 body，导出独立
`upstream.step`/`downstream.step`，避免同一 STEP 文件内的跨体 healer 改写接口。

**第一道 Gate**：每个 STEP 单独回读时必须只有一个 closed/manifold body，逐角色 face count、bbox、
volume 与 native 指纹保持；这只证明两个独立表示，尚不证明同一 solver 模型内 adjacency、连接或网格。

**后续路线**：仅在 native attach 重复性/mesh 诊断继续失败时运行；通过后仍需双 system observer。
formal 006、P1--P6、mesh、physics 继续 `NOT_RUN`。

## AJM-P1-MESH-001：V02 native preliminary 共节点诊断合同

日期：2026-07-15
状态：17-profile 静态包与 fail-closed validator 已完成；Windows `NOT_RUN`

**对象**：只对 hash-bound V02 two-zone native 的 job-local 副本生成一次 `0.5 mm` Mechanical
粗网格；两个 observer 必须复用同一个 producer job/native SHA。完整 12-cell/972-hole 几何
不减项；不增加材料、载荷、边界条件或物理求解。

**硬判据**：先要求 `972_SHARED_SINGLE_FACE / SHARED_ID_MEMBERSHIP_CONFIRMED`；随后 global 与
两个 body 的 node/element count 均须为正，972 个共享 face region 均须非空，全部界面节点 ID
必须同时属于两个 body node set，并要求两个 body 的节点交集精确等于目标界面节点 union；
同时要求没有 contact/connection object。两个独立 observer 的关键拓扑/网格签名必须一致。

**声明边界**：未来单次 PASS 也只表示该次 preliminary Mechanical 网格的共享节点 ID 证据；
不等于 Fluent/CFD 接口、网格质量/独立性、物理结果、正式 006 或 P1。既有 native attach
一 PASS/一 FAIL 的重复性仍单独保持 `UNRESOLVED`。失败不得静默改变 0.5 mm、删孔、删 cell
或自动切换 split fallback。

**入口**：`automation/ansys/run_v02_native_mesh_conformality_006.py`、
`windows-prompts/AJM_WIN_V02_NATIVE_MESH_CONFORMALITY_006.md`。
