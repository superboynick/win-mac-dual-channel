# 操作手册 01：AirJet Mini 完整产品参数化 CAD

状态：规划版，等待 Windows CAD 软件和版本确认后补充逐按钮截图。  
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
│   ├── BOTTOM_ORIFICE_OR_SPOUT_PLATE
│   ├── HEAT_SPREADER
│   └── FLEX_PLACEHOLDER
├── 20_ACTIVE_ARRAY
│   ├── CELL_001 ... CELL_N
│   ├── CENTRAL_ANCHORS
│   ├── MEMBRANES
│   └── CELL_PARTITIONS
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

- 执行片有效长度初值 8 mm；
- 中等数量单元，排气歧管和 flex 留出明确空间；
- 作为第一版完整装配体。

### Layout-S

- 执行片较小、单元数较多；
- 用于测试官方横截面中的“多个膜片”是否更容易解释；
- 风险：总功耗和制造复杂度升高。

三个布局共用相同外壳、出口和热扩散面。不要分别手动画三份文件；使用参数表/configuration 驱动阵列数量、行列数、间距和活动区尺寸。

## 6. 第四步：cell 子组件

每个 `CELL_nnn` 包含：

- 中央锚点；
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
- [ ] Layout-L/M/S 可切换且外壳不变；
- [ ] STEP、原生 CAD、剖面图和参数表均已导出。

## 11. 文件输出

```text
geometry/product_assembly/AJM-P1-M-v001.<native>
geometry/product_assembly/AJM-P1-M-v001.step
geometry/fluid_volumes/AJM-P1-M-fluid-v001.step
geometry/layouts/layout_constraints-v001.csv
results_summary/P1-M-cross-sections-v001.pdf
logs/AJM-P1-M-v001.md
```

大型 CAD/网格若不适合 Git，Git 中保留参数表、截图、STEP 的轻量替代版本或外部文件校验值。
