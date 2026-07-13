# AirJet 复原资料来源与参数溯源

## 1. 产品直接资料

### AirJet Mini Data Sheet

Mac：`/Users/zhangjianxiao/Downloads/AirJet_research/official/AirJet_Mini_Data_Sheet.pdf`  
Windows：研究 ZIP 解压后的 `AirJet_research/official/AirJet_Mini_Data_Sheet.pdf`

文件身份：

- PDF 共 1 个纵向长页，文件大小 250263 bytes；
- SHA256：`822fbb7e9735a5505734a291083fed7901c1fdfa01cb7de369679e4d41fd19bd`；
- 研究包内完整逐文件校验表：`AirJet_research/metadata/SHA256SUMS`；该校验表自身 SHA256 为 `091d1534bfe18697323a079a9db254bd8dc74f60ac224b4796fd0bf217b352f8`。

页内定位：上半部横截面支持膜片、脉冲射流、热扩散面、处理器与侧向 spout 的定性关系；下半部 `Metric / AirJet Mini` 表支持尺寸、重量、功耗、背压、噪声和 5.25/4.25 W 工况；最下部 `AirJet Mini Performance` 图支持功耗—净热与功耗—50 cm 系统噪声的数字化点。因 PDF 只有一页，以上均记为 `page 1`，同时使用区块标题定位。

支持：

- 外形 27.5 × 41.5 × 2.8 mm；
- 最大功耗 1 W；
- 总热耗散 5.25 W、净热移除 4.25 W；
- 85 °C die / 25 °C ambient 工况；
- 功耗—净热/系统内 50 cm 噪声曲线；
- 最大背压 1750 Pa、最大噪声 21 dBA、重量 11 g；
- 产品横截面、膜片、脉冲射流、热扩散面和排气方向。

限制：横截面是官方示意，不可直接当制造图；曲线数字化存在读图误差。Poppler 提取出的右轴标题明确为 `Acoustics of AirJet Mini in system measured at 50 cm (dBA)`，因此不得把 12/15/18/21 一列解释为送风量。

### AirJet Mini G2 Product Card EN

Mac：`.../official/AirJet_Mini_G2_Product_Card_EN.pdf`

文件 SHA256：`5f7042dfb2af4a9f37f5a26f792d305d0382b59175d1dfb545a21b96135107b1`。第 2 页表格直接支持：27.1 × 41.5 × 2.65 mm、7 g、7.5 W total heat dissipation（85 °C die / 25 °C ambient）、1.2 W、1750 Pa、21 dBA（inside device at 50 cm）。第 1 页支持代际横截面和进排气示意。
用途：Mini Gen1 完成后的迁移目标。  
限制：卡片没有把 7.5 W 分解为净热与 AirJet 自热，也缺少 Mini Gen1 那样的多点功耗曲线。

### AirJet PAK 1C / 3C

Mac：`.../official/AirJet_PAK_1C.pdf`、`AirJet_PAK_3C.pdf`

支持：

- PAK 1C：30 × 65 × 6.5 mm、8 W、1.3 W、1750 Pa、21 dBA；
- PAK 3C：100 × 65 × 6.5 mm、24 W、4 W、1750 Pa、27 dBA；
- chip 数量、系统进排气和系统装配示意。

用途：背压、功耗扩展和多 chip 系统交叉校验。  
限制：PAK 数据不可直接替换为裸 AirJet Mini 内部参数。

## 2. 结构与机理专利

### US12137540B2 — Centrally anchored MEMS-based active cooling systems

Mac：`.../patents/US12137540B2.pdf`

主要支持：

- 中央锚定、外围悬臂执行片；
- 顶板进气、顶腔、底腔、孔板和冲击通道；
- 结构共振与顶腔声学共振；
- 4–10 mm 广义执行片范围、6–8 mm 优选范围（本地 PDF p.19 printed col.4 lines 1–6；p.21 col.7 lines 43–49）；20–25 kHz 只对应 8 mm 例（p.21 col.7 lines 56–59）；
- 10–60 μm 位移（p.20 col.6 lines 34–41）；
- 顶腔 200–300 μm（p.20 col.6 lines 21–26）；
- 孔宽 200–300 μm、专利孔间隔 `s` 400–600 μm 优选范围（p.22 col.9 lines 26–36）；`s` 的中心距/边距图义仍需确认；
- 开孔率 8–12%（p.22 col.9 lines 36–44）；
- 冲击间隙 200–300 μm（p.20 col.5 lines 47–55）；
- 至少 30 m/s 喷速；部分实施例为至少 45/60 m/s，不存在已公开的 60 m/s 上限（p.19 col.4 lines 6–8；p.20 col.5 lines 1–8）；
- 多 cell、共享板和反相驱动实施例。

限制：所有尺寸均作为专利实施例范围，不等同于 Mini Gen1 精确生产值。

专利定位统一采用“本地 PDF 页码 + 专利印刷 column/line + FIG.”。旧记录中的 `paragraph 864/866` 实为网页抽取行号，不是美国专利正式段落号，已从参数注册表和 ledger 移除。部件级定位、适用性和替代架构见 `patent_product_component_map.csv`。

### US11978690B2 — Anchor and cavity configuration

Mac：`.../patents/US11978690B2.pdf`

主要支持：锚点/腔体关系、上下腔高度、底腔与位移余量、孔位置减少回吸、材料候选、排气 duct/chimney。

### US11802554B2

Mac：`.../patents/US11802554B2.pdf`

主要支持：不同振动执行片排列与锚定/振型候选。  
用途：作为主中央锚定版本的替代结构，不直接混进主 CAD。

### US12320595B2 / US12193192B2 / US12392566B2

主要支持：腔体、声学调谐和频率锁定。  
用途：P2/P3 的共振与驱动控制规划。

## 3. 教程与基础数值资料

### Hot Chips 2024 AirJet tutorial

Mac：`.../papers/Hot_Chips_2024_AirJet_tutorial.pdf`

支持：官方工作机理、MEMS 脉冲射流、冲击换热、系统集成和性能叙述。  
限制：厂商教程，不作为独立学术验证。

### Synthetic Jet Fluid Heat Transfer Numerical

Mac：`.../prior_art/Synthetic_Jet_Fluid_Heat_Transfer_Numerical.pdf`

支持：膜片运动边界、瞬态 CFD、冲击换热和数值验证方法。  
限制：一般合成射流，不是 AirJet 产品内部结构证据。

### Hybrid Synthetic Jet Fluid Diode CFD

支持：受限空间、整流、回流控制和 Fluent 数值策略。  
限制：只能迁移方法，不可迁移产品尺寸。

### 2024 Nonlinear Cavity Resonance Synthetic Jet

支持：结构共振、腔体/Helmholtz 共振和非线性响应。  
用途：解释为什么 P3 需要可压缩瞬态而非稳态入口。

### 2023 Multi-Jet Impingement Cooling Modeling

支持：多射流干扰、阵列换热、网格与优化方法。  
用途：P4/P5 的验证方法；不是 AirJet 内部布局来源。

## 4. 来源使用规则

1. 产品尺寸/性能优先用具体型号官方数据表；
2. 内部结构优先用专利，但标成范围或候选；
3. 数值算法用学术论文/软件验证资料；
4. 营销图只支持定性流向和比例推断；
5. 不同代际、不同 PAK 型号数据不得无标记混用；
6. 任何进入求解器的参数必须能在 registry 找到来源和状态；
7. 来源矛盾时保留两个候选，并写入 MODEL_ANNOTATIONS，不静默选一个。
