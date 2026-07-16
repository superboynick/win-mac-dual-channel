# AirJet Mini Gen1 仿真论文 — 章节大纲

## Title (候选)

"Numerical Reconstruction of Frore AirJet Mini Gen1: Full-Product CFD Mesh Generation and Validation"

## Abstract（摘要）

- 背景：固态散热是新兴技术
- 目标：对 AirJet Mini Gen1 进行整机 CFD 仿真重建
- 方法：SpaceClaim 参数化 CAD + PyFluent 自动化网格
- 结果：35K cells 体网格，OQ 0.57，全自动流程
- 结论：验证了仅基于公开数据的仿真重建可行性

## 1. Introduction（引言）

### 1.1 固态散热背景
- 传统风扇 vs 固态散热的优劣
- Frore Systems AirJet 的技术原理
- 现有文献的仿真研究（几乎没有）

### 1.2 研究目标
- 在没有实物的情况下，仅凭公开数据重建完整 CFD 模型
- 验证参数化自动化流程
- 为后续优化和设计改进提供基础

### 1.3 论文结构
- Section 2: 方法
- Section 3: 几何建模
- Section 4: 网格生成
- Section 5: 结果与讨论
- Section 6: 结论

## 2. Methodology（方法）

### 2.1 参数采集与分级
- 证据分级系统（A/B/C/D）
- 关键参数来源（见 EVIDENCE_CHAIN_COMPLETE.md）
- 不确定参数处理（C016 候选值）

### 2.2 几何建模流程
- SpaceClaim + Python API
- Boolean 合并策略
- STEP 导出验证

### 2.3 网格生成流程
- Fluent Watertight 工作流
- 局部尺寸控制
- Poly-hexcore 体网格

### 2.4 自动化与版本控制
- MCP 架构
- Git 版本控制
- 合同层验证

## 3. Geometry Reconstruction（几何重建）

### 3.1 包络尺寸
- 27.75 × 41.5 × 1.53 mm
- Z 向分层详解

### 3.2 喉道阵列
- 12 单元 × 81 孔 = 972 孔
- 孔径 0.25mm，孔距 0.70mm
- 坐标精确推导

### 3.3 流体域提取
- Boolean 挑战
- Overlap 策略演进

## 4. Mesh Generation（网格生成）

### 4.1 网格策略
- 面网格尺寸范围
- 喉道局部细化

### 4.2 网格质量
- 35K cells, OQ 0.57
- Free face = 0, Multi face = 0
- 972 孔全占用验证

### 4.3 自动化验证
- 合同层 15 项检查
- MCP 两阶段流程

## 5. Results and Discussion（结果与讨论）

### 5.1 几何保真度
- STEP round-trip 验证
- 体积误差分析

### 5.2 网格质量分析
- OQ 分布
- 孔周围网格特征

### 5.3 局限性
- Student License 1M 限制
- 主流体域识别问题
- 无实物验证

## 6. Conclusion（结论）

- 仅凭公开数据可实现 AirJet 整机参数化 CFD 重建
- 全自动流程验证通过
- 未来工作：求解器、CHT、FSI、参数扫描

## References（参考文献）

- Frore Systems 专利
- AirJet 产品资料
- ANSYS Fluent 文档
- PZT 材料数据库

## Figures（图表清单）

| 编号 | 内容 | 状态 |
|------|------|------|
| Fig 1 | AirJet 工作原理示意 | ⏳ |
| Fig 2 | 12 单元 × 972 孔布局 | ✅ 数据已有 |
| Fig 3 | 体网格截面 | ⏳ 需截图 |
| Fig 4 | OQ 分布直方图 | ⏳ 需数据 |
| Fig 5 | 自动化流程图 | ✅ 可画 |
| Fig 6 | 孔占用验证 | ✅ 数据已有 |
