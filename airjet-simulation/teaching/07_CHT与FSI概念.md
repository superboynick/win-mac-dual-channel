# 第7课：CHT 共轭传热与 FSI 流固耦合

## CHT（Conjugate Heat Transfer）

普通 CFD 只算流体。CHT 同时算**流体 + 固体**的热量传递。

AirJet 传热路径：芯片 → TIM → 散热器 → 空气

### Fluent CHT 设置
1. 划分固体域网格
2. 设定材料（铝 6061）
3. 设定热源（5-10W）
4. 耦合面自动同步
5. 求解能量方程

## FSI（Fluid-Structure Interaction）

压电膜片振动 → 腔体压力变化 → 驱动空气 → 反作用力

| 类型 | 数据流 | AirJet |
|------|--------|--------|
| 单向 | Mechanical→CFD | 先试 |
| 双向 | Mechanical↔CFD | 后续 |

## 许可证需求

| 仿真 | 模块 |
|------|------|
| 纯 CFD | Fluent |
| CHT | Fluent（内置） |
| 模态 | Mechanical |
| FSI | Fluent + Mechanical + System Coupling |

## 当前状态
- ✅ CFD 网格 (C5 PASS)
- ⏳ CFD 求解 (等 license)
- ⏳ CHT / FSI (P4-P5)
