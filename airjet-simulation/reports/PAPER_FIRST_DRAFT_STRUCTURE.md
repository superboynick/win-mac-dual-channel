# AirJet Mini Gen1 仿真论文 — First Draft 结构

## 建议章节

### 1. Introduction
- 固态主动散热背景
- AirJet Mini Gen1 工作原理（压电膜片 → 微喷口阵列 → 冲击射流）
- 现有文献缺口（无公开整机仿真）
- 本文贡献

### 2. Geometry Reconstruction
- 数据来源：产品数据表、专利、公开文献
- 参数提取方法
- 几何简化假设
- 12 单元 × 972 孔布置
- Z 向分层（底腔 → 孔板 → 冲击通道 → 顶腔）

### 3. Numerical Method
- SpaceClaim 参数化 CAD
- ANSYS Fluent watertight meshing workflow
- Poly-hexcore 体网格
- PyFluent Python API 自动化
- 网格独立性计划

### 4. Results — Mesh
- 粗网格：35,108 cells, OQ 0.57
- 面网格质量
- 区域识别（1 fluid + 11 voids）
- 已知局限

### 5. Future Work
- CHT 共轭传热
- FSI 流固耦合
- 网格独立性验证
- 实验验证

## 证据状态（论文中需标注）
- A 级证据（产品数据表直接）：标注为 "per manufacturer"
- B 级证据（专利/图纸推断）：标注为 "estimated from patent"
- C 级证据（工程占位）：标注为 "placeholder value, pending calibration"
