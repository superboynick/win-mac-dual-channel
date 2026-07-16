# P2 Mechanical 模态分析设置

## 目标
对 AirJet Mini Gen1 压电膜片等效板进行模态分析，获取固有频率和振型。

## 几何
- 等效板：7×7 mm，厚度待定
- 边界条件：四边固支（clamped）
- 材料：PZT-5H（候选）

## ANSYS Mechanical 设置
1. Static Structural → Modal
2. 材料属性：E, ν, ρ（从 PZT-5H 数据表）
3. 网格：四面体或六面体，~5000 elements
4. 求解：前 6 阶模态

## 预期结果
- 基频：~10-20 kHz（AirJet 工作频率范围）

## 状态
- CAD：PASS（P2-S0 equivalent plate producer）
- Mechanical：NOT_RUN（等待许可）
