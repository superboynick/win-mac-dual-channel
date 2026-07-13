# AJM-P0-v001 产品证据冻结记录

日期：2026-07-13  
目标：AirJet Mini Gen1 完整产品公开证据约束复原  
Gate：**PASS - P0 evidence freeze v1**  
重要边界：P0 PASS 不代表内部结构已证实，不代表 P1–P6 CAD/结构/仿真 Gate 通过。

## 1. 冻结的直接产品目标 D

| 项目 | 冻结值 | 来源 |
|---|---:|---|
| 外包络 | 27.5 x 41.5 x 2.8 mm | Mini Data Sheet page 1 metric table |
| 最大电功耗 | 1 W | 同上 |
| 总热耗散 | 5.25 W @ 85 C die / 25 C ambient | 同上 |
| 净热移除 | 4.25 W @ 同工况 | 同上 |
| 压力能力 | 1750 Pa | 同上；对应流量未公开 |
| 系统内噪声 | 21 dBA at 50 cm | 同上；不是局部 CFD 压力目标 |
| 重量 | 11 g | 同上 |

热账户冻结为 `4.25 W net + 1.00 W device power = 5.25 W total`。功耗-净热/50 cm 系统噪声四点由 `CURVE_DIGITIZATION_METHOD.md`、原始像素 CSV 和复算脚本共同保存。

## 2. 产品图证据 D/I/U

两张 Gen1 官方产品透视图分别做独立 homography，并用 10,000 次 Monte Carlo 传播四角 `+/-3 px` 与 vent 端点 `+/-2 px` 的选择误差：

- 两张图都画出四个 elongated top vent objects；它们进入 `I` 类顶盖候选，不升级为量产 inlet-group count；
- 跨视图 vent 中心横向差为约 `1.57-2.67 mm`，长轴差最高约 `0.72 mm`；跨视图差作为 model-form uncertainty，优先级高于单视图像素区间；
- 官方剖面直接支持多膜片、脉冲射流、底部热扩散面、处理器接触关系和单侧 integrated spout 排气的定性拓扑；
- 官方剖面只允许锁定总厚度 2.8 mm。内部层厚、腔高、孔板和冲击间隙继续为 `P/C/U`，不从示意色块缩放；
- 绿色波形、箭头和 Schlieren 图不用于数 cell、喷孔、速度或流量。

复现入口：

- `OFFICIAL_IMAGE_COORDINATE_METHOD.md`；
- `extract_official_image_geometry.py`；
- `analyze_official_vent_views.py`；
- `official_image_measurements.csv`；
- `annotated_figures/gen1_vent_homography_results.csv`；
- `annotated_figures/gen1_vent_cross_view_comparison.csv`；
- `annotated_figures/*.png`。

## 3. 专利候选证据 P

`patent_product_component_map.csv` 已把下列整机候选部件映射到本地 PDF 页码、FIG.、专利印刷 column/line：

- 中央锚定和替代锚定；
- 顶腔、底腔和膜片周边转移路径；
- 孔板、冲击通道和通用排气 duct/chimney；
- 多 cell、共享顶板/孔板和相位驱动。

中央锚定被选为 R0 主候选架构，是因为它同时与专利族和官方机理图相容；它仍不是 Mini 量产结构事实。edge anchor、adhesive support、rotational anchor、分隔/共享腔等替代版本必须保留。

参数注册表和 ledger 已移除 `paragraph 864/866` 一类误导定位；这些数字曾是网页抽取行号，不是正式专利段落号。当前统一使用本地 PDF 页码 + printed column/line + figure。

## 4. 布局候选冻结

`build_layout_candidate_scores.py` 由明确的 A0 假设生成 `layout_candidate_scores.csv`：

- 原始 family 组合 34 个；
- 去重后唯一几何 32 个；
- A0 下 23 个可装入、9 个 `FAIL_CONFIG_A0`；
- A0：侧余量 1.0 mm、进排气总预留 5.0 mm、cell 壁 0.25 mm、方形膜片投影代理。

当前工作顺序：

1. `M-3x4-7.0`：`PRIMARY-P0`，12 cells，A0 余量 4.00/7.75 mm；
2. 唯一几何 `M+S-3x5-6.0`：`ALTERNATE-P0`，15 cells，余量 7.00/5.50 mm；
3. `L-2x4-8.0`、`S-3x5-5.5`：低 cell 与小 cell model-form sentinels。

这只是 P1/P2/P3 的实验顺序，不是产品真实 cell 数概率。当前只打了 geometry 15% 和 complexity 5%，`score_coverage_pct=20`；image/modal/power/flow/thermal 均保持空白，不重新归一化制造假高分。`S_image` 要等每个完整 P1 CAD 投影到两张产品图后才能评分。

## 5. P0 Gate 逐项证据

- [x] Mini 尺寸、功耗、净/总热、压力、噪声、重量与曲线进入注册表/曲线 CSV；
- [x] 官方图保存原始对象身份、角点、vent 端点、homography、像素误差、Monte Carlo 与跨视图差；
- [x] 核心专利与整机部件建立精确定位映射，并明确产品适用边界；
- [x] 求解器输入注册表使用 `D/P/I/C/U`，包含范围/不确定度、推导父项、可调性、来源和用途；
- [x] Mini、G2、PAK 数据用途边界写入 `SOURCE_PROVENANCE.md` 和产品选择记录；
- [x] Layout-L/M/S 去重、硬门槛、未评分字段和 P0 工作主/备选已记录。

## 6. 仍未识别、但已冻结为未知

- Mini 真实 cell 数、行列、pitch 与活动区；
- 真实锚定、膜片材料层叠、阻尼、驱动电压和相位图；
- 独立/分组/共享顶腔与孔板；
- 孔形、`separation s` 的图义、孔数与生产开孔率；
- 排气歧管截面、spout 内部尺寸；
- spreader/TIM 材料和厚度、1 W 自热空间分配；
- 数值流量曲线和隔离模块声学；
- 1750 Pa 对应流量条件。

这些未知量不妨碍开始多候选 P1 CAD，但阻止“精确数字孪生”或“量产内部结构已还原”的表述。

## 7. P1 入口与停止条件

P1 可以开始的内容：锁定 27.5 x 41.5 x 2.8 mm 外壳、双视图候选顶盖开口、单侧 spout 拓扑，并用相同外壳建立 PRIMARY/ALTERNATE/sentinel 的完整装配与流体负体积。

P1 仍需先完成 CAD/CAE 软件与许可证选择。Windows 当前没有检测到 ANSYS、Fluent、Mechanical、SpaceClaim、Workbench 或 COMSOL；因此不能把“P0 PASS”误写成“已经能跑最终整机 CFD/CHT”。

停止条件：如果新公开 D 类资料、实物/CT 或软件中的几何连通检查否定当前候选，应新建 `AJM-P0-v002` 或 P1 变更记录，不能静默覆盖 v001。
