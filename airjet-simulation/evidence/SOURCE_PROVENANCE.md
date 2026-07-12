# AirJet 复原资料来源与参数溯源

## 1. 产品直接资料

### AirJet Mini Data Sheet

Mac：`/Users/zhangjianxiao/Downloads/AirJet_research/official/AirJet_Mini_Data_Sheet.pdf`  
Windows：研究 ZIP 解压后的 `AirJet_research/official/AirJet_Mini_Data_Sheet.pdf`

支持：

- 外形 27.5 × 41.5 × 2.8 mm；
- 最大功耗 1 W；
- 总热耗散 5.25 W、净热移除 4.25 W；
- 85 °C die / 25 °C ambient 工况；
- 功耗—净热/送风量曲线；
- 产品横截面、膜片、脉冲射流、热扩散面和排气方向。

限制：横截面是官方示意，不可直接当制造图；曲线数字化存在读图误差。

### AirJet Mini G2 Product Card EN

Mac：`.../official/AirJet_Mini_G2_Product_Card_EN.pdf`

支持：G2 外形/厚度、公开热移除能力、代际横截面和进排气示意。  
用途：Mini Gen1 完成后的迁移目标。  
限制：当前本地卡片缺少 Mini Gen1 那样完整的多点标定曲线。

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
- 6–8 mm 执行片、20–25 kHz 例；
- 10–60 μm 位移；
- 顶腔 200–300 μm；
- 孔径 200–300 μm、孔距 400–600 μm；
- 开孔率 8–12%；
- 冲击间隙 200–300 μm；
- 30–60 m/s 量级喷速；
- 多 cell、共享板和反相驱动实施例。

限制：所有尺寸均作为专利实施例范围，不等同于 Mini Gen1 精确生产值。

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
