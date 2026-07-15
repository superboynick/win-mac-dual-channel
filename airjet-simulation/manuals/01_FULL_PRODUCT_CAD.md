# 操作手册 01：AirJet Mini 完整产品参数化 CAD

状态：可执行合同版；等待 Windows 005 工具链门槛通过后由 006 建模并补充实际截图。
目标：建立完整 AirJet Mini 装配体和可用于 CFD 的完整流体体积；单 cell 只是装配体中的参数化子组件。

## 1. 建模坐标和尺寸基准

- `X`：产品宽度方向，目标外包络 27.5 mm；
- `Y`：产品长度/主排气方向，目标外包络 41.5 mm；
- `Z`：厚度方向，目标外包络 2.8 mm；
- 原点：产品底部热扩散面几何中心；
- `Z=0`：AirJet 与热扩散面接触的参考平面；
- 所有零件使用同一装配坐标，禁止每个 cell 自建互不一致的局部原点。

## 2. 装配体树

```text
AJM_GEN1_PRODUCT
├── 00_REFERENCE
│   ├── ENVELOPE_27P5_41P5_2P8
│   ├── OFFICIAL_TOP_VIEW
│   └── OFFICIAL_CROSS_SECTION
├── 10_PACKAGE_SOLIDS
│   ├── TOP_COVER
│   ├── SIDE_FRAME
│   ├── ORIFICE_PLATE_CAND
│   ├── SPOUT_BOUNDARY_CONSTRUCTION_CAND
│   ├── HEAT_SPREADER
│   └── FLEX_PLACEHOLDER
├── 20_ACTIVE_ARRAY
│   ├── CELL_001 ... CELL_N
│   ├── CENTRAL_ANCHOR_DATUM_C
│   ├── MEMBRANES
│   └── CELL_PARTITION_DATUM_C
├── 30_FLOW_PATH
│   ├── EXTERNAL_INLET_PLENUM
│   ├── TOP_CHAMBERS
│   ├── PERIMETER_TRANSFER_GAPS
│   ├── BOTTOM_CHAMBERS
│   ├── ORIFICES
│   ├── IMPINGEMENT_CHANNEL
│   ├── EXHAUST_MANIFOLD
│   └── PRODUCT_OUTLET
└── 40_THERMAL_STACK
    ├── TIM_EQUIVALENT
    └── CHIP_HEAT_SOURCE
```

实体、流体体和命名面使用上述前缀，方便 Mechanical、Fluent 和 PyFluent 自动识别。

## 3. 第一步：外形证据锁定

1. 导入官方数据表的顶视图和剖面图作为 reference canvas。
2. 用已知 41.5 mm 长度缩放顶视图；用 2.8 mm 总厚度缩放剖面图。
3. 从图中测量进气开口、活动区、排气出口和 flex 的相对位置；记录“像素测量误差”。
4. 所有从图片比例得到的尺寸使用 `I-IMG-xxx` 编号，不升级为直接证据。
5. 建立 `ENVELOPE_27P5_41P5_2P8`，后续装配任何点都不得越界，flex 除外时必须单独说明。

### 3.1 P1 输入表与 2.8 mm 厚度预算

建模前运行：

```powershell
python .\airjet-simulation\parameters\build_p1_cad_inputs.py
python .\airjet-simulation\parameters\build_p1_cad_contracts.py
```

要求同时生成：

- `parameters/p1_layout_configuration_matrix.csv`：主候选、备选和两个 model-form sentinel 的阵列输入；
- `parameters/p1_thickness_budget.csv`：从底部热扩散面到顶盖的 `TB0-PLACEHOLDER` 坐标表。
- `parameters/p1_model_form_variants.csv` 与 `p1_cad_parameter_map.csv`：6 个交付/残差变体、3 个单因素派生变体及其逐参数 CAD 映射；
- `parameters/p1_orifice_pattern_candidates.csv`、`p1_vent_geometry_candidates.csv`、`p1_planform_exhaust_candidates.csv`：三类不能静默猜测的几何分支；
- `parameters/p1_internal_geometry_rules.csv`：膜片/每 cell 底腔、中央锚与分区 datum、共享顶腔、外围间隙、side-wall、残差数值封闭和喷孔落点等 9 条可重复 R0 规则；
- `geometry/contracts/*.csv`：整机 component/interface/Named Selection/open-question 合同；
- `checklists/p1_cad_gate_matrix.csv`：初始全部 `NOT_RUN` 的逐变体验收矩阵。

`TB0-PLACEHOLDER` 严格加和为 2.8 mm，但其中 `C019` 是未识别层厚残差，初始由 `C020=0.5` 对称分配到主动层上下。这个占位体只让第一版 CAD 能闭合、切片和检查拓扑，不证明真实产品存在两个等厚残差层。`C017`、`C019_TOP`、`C019_BOTTOM` 禁止赋予材料，禁止计入质量，禁止进入结构或 CHT 求解；只有分解成有独立证据的真实候选部件后才能升级用途。P1 必须至少比较 top-heavy、balanced、bottom-heavy 三种 `C020` 分配，并用双视图、质量预算、结构碰撞和流体连通淘汰；不得通过缩放官方示意剖面直接定层厚。

`P002=0.275 mm` 来自 8 mm 专利执行片实施例。TB0 暂把它跨尺寸借给 5.5/6/7/8 mm 四个具体配置，只用于 P1 CAD 占位；进入 P2 前必须按膜片尺寸建立独立厚度/材料分支，不能声称四个布局都得到相同专利厚度支持。

`porosity_hole_count_proxy` 只按 `phi_open * active_membrane_area_proxy / circular_hole_area` 估算建模规模。因为真实活动孔板面积未知、`separation s` 图义未解决，它不能直接成为最终喷孔数。初次 Boolean 可用代理孔阵列验证软件稳定性，正式 P1 Gate 仍须使实际孔数、孔径、活动面积和开孔率闭合。

生成后必须同时运行 `build_p1_cad_inputs.py --check` 和 `build_p1_cad_contracts.py --check`。第二个生成器还锁定两套 vent 坐标、两套排气平面闭合和 0.25/0.50/0.75 残差位置分支；完整公式、证据边界和禁止用途见 `parameters/P1_CAD_CONTRACT_METHOD.md`。两条命令无写入返回 PASS 只说明 CSV 与上游输入一致，仍不表示 CAD 已建立。

## 4. 第二步：建立产品层级流道

先画空气经过产品的整条路线，再放膜片：

```text
外部入口域
  → 顶盖进气开口
  → 顶部配气空间/各 cell 顶腔
  → 膜片外围转移间隙
  → 各 cell 底腔
  → 完整孔板喷孔
  → 全产品冲击通道
  → 排气汇流区
  → 集成 spout/产品出口
```

任何一段缺失都意味着模型不是完整产品。每完成一段，用“种子点 + volume extraction”检查空气域是否连通。

## 5. 第三步：候选内部布局

### Layout-L

- 采用接近专利上限的大执行片；
- 单元数较少；
- 优点：结构模态和驱动容易解释；
- 风险：覆盖率、总流量或官方图比例可能不符。

### Layout-M（当前主候选）

- 当前工作主配置执行片有效长度为 7 mm（`M-3x4-7.0`）；
- 中等数量单元，排气歧管和 flex 留出明确空间；
- 作为第一版完整装配体。

`P002=0.275 mm` 是 8 mm 专利执行片的跨尺寸厚度占位，它不是 Layout-M 的平面长度；8 mm 平面执行片只在 `L-2x4-8.0` sentinel 中出现。

### Layout-S

- 执行片较小、单元数较多；
- 用于测试官方横截面中的“多个膜片”是否更容易解释；
- 风险：总功耗和制造复杂度升高。

三个布局共用相同外壳、出口和热扩散面。不要分别手动画三份文件；使用参数表/configuration 驱动阵列数量、行列数、间距和活动区尺寸。

## 6. 第四步：cell 子组件

每个 `CELL_nnn` 包含：

- 非物理中央锚 construction datum；
- 零厚度 cell-partition ownership/naming datum；
- 复合执行片占位实体；
- 顶腔；
- 膜片外围连通间隙；
- 底腔；
- 该 cell 对应的孔板区域和喷孔集合。

cell 子组件必须能被完整产品阵列调用，但其外壁不能重复生成导致 cell 之间重叠。共享顶板、共享孔板和共享排气结构放在产品层级，不放在 cell 内重复复制。

## 7. 第五步：孔板和喷孔

1. 先定义活动孔板面积 `A_plate_active`。
2. 目标开孔面积 `A_open = porosity × A_plate_active`。
3. 根据孔宽和孔数计算实际开孔率；单独记录 CAD 中采用的中心节距/边缘间隔定义，不能把专利 `separation s` 未经图义确认就当作中心节距。
4. 喷孔可能为圆柱、锥形或带集成 spout；R0 先建圆柱孔，另建 `ORIFICE_CONICAL` 备选配置。
5. 所有孔必须通到底腔和冲击通道，Boolean 后检查丢失孔和盲孔。

## 8. 第六步：冲击与排气通道

- 孔板至热面初始间隙 0.25 mm；
- 冲击通道覆盖全部喷孔活动区；
- 通道不能在外壳四周全部设出口，除非官方流向支持；
- 用产品图确定主要出口方向，建立汇流歧管和集成 spout；
- 为比较建立 `EXHAUST_OPEN_ALL_SIDES` 诊断配置，但不得作为最终 Mini 模型。

正式 P1 R0 不再临场画歧管。默认从 `p1_planform_exhaust_candidates.csv` 选择 `<configuration_id>__EXH_FULL_WIDTH_RECT_R0`；主配置 balanced 另建 `EXH_CENTER_HALF_TAPER_R0`，一次只改变排气模型形式。二者都为 `C` 类工程闭合，不是产品截面。顶盖同样一次完整选择 `VENT_FLOW_BBOX_R0` 或 `VENT_UPPER_CENTERLINE_P013_R0` 的全部四行，禁止混拼两套视图。

## 9. 第七步：流体体积提取

分别提取并命名：

- `FLUID_INLET_EXTERNAL`；
- `FLUID_INTERNAL_PRODUCT`；
- `FLUID_JET_CHANNEL`；
- `FLUID_OUTLET_EXTERNAL`。

初期可保留为非共形接口以便调试；最终 P4 模型合并为连续流体域或使用严格守恒接口。执行切片检查，确认没有固体碎片、重复面、零厚度缝隙和孤立体积。

## 10. CAD 验收清单

- [ ] 外包络为 27.5 × 41.5 × 2.8 mm；
- [ ] 完整产品而非 cell 截取；
- [ ] 顶部入口至最终出口连续；
- [ ] 所有 cell 均有顶腔—外围间隙—底腔—喷孔；
- [ ] 孔宽、孔间隔/节距定义、孔数和开孔率自洽；
- [ ] 膜片最大位移时不碰撞顶/底板；
- [ ] 热扩散面覆盖冲击活动区；
- [ ] 每个未知尺寸拥有 `I/C/U` 标签；
- [ ] 三个概念族对应的四个具体配置可切换且外壳不变；
- [ ] STEP、原生 CAD、剖面图和参数表均已导出。
- [ ] `C017/C019` 参考体及中央锚/partition datum 没有材料、质量、Boolean、结构、CHT、fluid union 或求解器导出；
- [ ] 每个变体的 STEP 已成功导出/重导入并记录全链 SHA256；producer/observer job identity 与独立 artifact-manifest 已闭合；Workbench/Mechanical 已导入同字节 STEP，并从 hash-bound semantic sidecar 生成 solver observation，以实际 owner/adjacency/boundary IDs、direction/bbox 和稳定 semantic key 重建集合；production validator 计算的 missing/unexpected/dangling/orphan 数组为空、coverage=true、assignment=1，且逐字段等于 key report；不得把该结果写成 native Named Selection transfer 已证明；
- [ ] 每个变体记录 vent/orifice/exhaust 三个 branch ID、实际孔数/开孔率和全部文件 SHA256；
- [ ] 006 结束时 P1 只允许 `INCOMPLETE` 或 `PENDING_PEER_REVIEW`，不得由生成模型的同一会话自评 PASS。

## 11. 文件输出

```text
D:\AirJet_P1\AJM-P1-CAD-006\<UTC-run-id>\master\AJM-P1-master.<native>
D:\AirJet_P1\AJM-P1-CAD-006\<UTC-run-id>\<variant-id>\product.<native>
D:\AirJet_P1\AJM-P1-CAD-006\<UTC-run-id>\<variant-id>\product.step
D:\AirJet_P1\AJM-P1-CAD-006\<UTC-run-id>\<variant-id>\fluid.step
D:\AirJet_P1\AJM-P1-CAD-006\<UTC-run-id>\<variant-id>\checks\
C:\Users\admin\Downloads\AIRJET_P1_FULL_PRODUCT_CAD_BUILD_006.txt
```

大型 CAD/STEP/Workbench 文件不进入 Git。Git 只保留生成器、参数/合同表、运行模板和后续审核通过的小型摘要；外部产物用 `logs/external-files.csv` 的字段记录绝对路径、大小、SHA256、软件版本和 Git commit。
