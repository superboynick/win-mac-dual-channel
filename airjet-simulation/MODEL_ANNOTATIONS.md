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
