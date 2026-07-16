# AirJet Mini Gen1 仿真论文 — V2 结构（含实物验证）

## 1. Introduction
- 固态主动散热背景（消费电子、迷你PC散热瓶颈）
- AirJet Mini Gen1 工作原理（压电膜片 → 微喷口阵列 → 冲击射流）
- ZOTAC ZBOX PI430AJ 作为首个商用 AirJet 产品
- 现有文献缺口：无公开的整机仿真 + 实物对照研究
- **本文贡献：首次基于实物拆解的 AirJet Mini 整机仿真重建 + 实验验证**

## 2. Hardware Teardown & Geometry Extraction ⭐ 新增
### 2.1 Device Acquisition
- ZOTAC ZBOX PI430AJ（开箱商品，ZOTAC 官方商店直购）
- 运送至 Pomona, CA 91767

### 2.2 Teardown Procedure
- 拆解步骤记录（照片）
- AirJet Mini 模组取出
- 关键尺寸测量（游标卡尺）：X, Y, Z 包络，孔径，孔间距，膜片尺寸

### 2.3 Geometry Validation
- 实测尺寸 vs 之前 CAD 参数对比表
- 修正 C016（孔板厚度）、membrane pitch、Z-stack 等占位参数
- 实物照片 + 标注尺寸图

### 2.4 Fluid Domain Extraction
- 从 AirJet Mini 实物逆向出流体域
- 12 单元 × 972 微孔喉道确认

## 3. Numerical Method
### 3.1 CAD & Meshing（已有，用校准后的参数更新）
- SpaceClaim 参数化 CAD（参数源从公开数据 → 实物测量）
- Fluent Watertight + Poly-hexcore
- 网格统计：34,883 cells, OQ 0.53

### 3.2 CFD Setup
- 边界条件（基于实物风扇曲线/压降推算）
- 湍流模型
- 求解器设置

### 3.3 Mesh Independence（如有时间）
- 不同 sizing 的网格对比

## 4. Results
### 4.1 Mesh Quality（已有）
- 18 次一致运行证明可重复性
- 区域识别：1 fluid + 11 voids

### 4.2 CFD Results
- 速度场、温度场（需要真实 BC）
- 出口流量 vs 产品规格对比

### 4.3 Experimental Validation ⭐ 新增
- ZBOX PI430AJ 运行热像图
- 仿真 vs 实测温度对比
- 误差分析

## 5. Discussion
### 5.1 Parameter Sensitivity
- C016 候选值 0.10mm → 实测值的影响
### 5.2 Simulation Limitations
- Student license cell limit
- Boundary type collapse
### 5.3 Hardware Insights
- 拆解中发现的未公开设计细节

## 6. Conclusion
- 首次 AirJet Mini 整机仿真 + 实物验证
- 方法可复现
- 为 CHT/FSI 全耦合仿真奠基

---

## 实物拆解 — 待办清单

当 ZBOX 到货后立即做：
1. [ ] 开箱拍照（多角度）
2. [ ] 拆机 → 取出 AirJet Mini 模组
3. [ ] 游标卡尺测量：
   - X × Y × Z 包络
   - 孔板厚度（C016 从 0.10mm 占位 → 实值）
   - 膜片可见尺寸
   - 孔间距（验证 pitch 7.0mm）
   - 孔数量（验证 972 个）
   - 进出口尺寸
4. [ ] 显微镜/放大镜拍摄微孔阵列
5. [ ] 通电运行 → 热像图（手机热像仪或借实验室的）
6. [ ] 记录运行噪音（手机 APP）

## 论文照片清单
- Fig 1: ZBOX PI430AJ 产品外观
- Fig 2: 拆解过程 — AirJet Mini 模组取出
- Fig 3: AirJet Mini 标注尺寸图（X/Y/Z/孔阵列）
- Fig 4: 微孔阵列显微照片
- Fig 5: SpaceClaim CAD 截图（含参数标注）
- Fig 6: Fluent 网格截图（切面显示 cell zones）
- Fig 7: CFD 速度/温度云图
- Fig 8: 热像图 vs 仿真温度对比
- Table 1: 实测参数 vs 仿真参数 vs 文献参数
- Table 2: 网格质量统计

---

## 与旧版对比

| 旧版（纯仿真） | 新版（仿真+实物） |
|---|---|
| 参数来自专利/推断 | 参数来自实物测量 |
| 无实验验证 | 热像图 + 误差分析 |
| 纯数值贡献 | 方法学 + 实验对照 |
| 适合课程作业 | 适合期刊投稿 |
