# AirJet 项目 — 缺口与下一步

## P3 当前阻塞

### C6 几何连接（P3_BLOCKING）

**问题：** SpaceClaim Boolean 不闭合，主流体域和 actuator gap 不连通

**尝试过的方案：**
| 方案 | 结果 |
|------|------|
| C5 0.02mm overlap | ❌ Boolean 容差不识别 |
| C5 0.15mm overlap | ⚠️ 39K cells, OQ 0.49, 域选择待验证 |
| C6 inward 0.05mm | ❌ 加了 4.59mm³, membrane 计数归零 |

**下一步方案（来自 C6 诊断）：**
不移动环 → 在底部腔体界面加冗余桥接实体（bridge solids），完全包含在最终 union 内

**预估：** 1-2 次迭代可解决（C7 候选）

### Student License 1M 限制

**问题：** 体网格超过 1M cells/nodes 会失败

**状态：** 
- ✅ 已联系 Ansys 销售董如怡
- ⏳ 等待 30 天 Academic Research License 批复
- 当前粗网格 35K cells 可正常生成

## P2 Mechanical

| 项目 | 状态 |
|------|------|
| 等效板几何 (P2-S0) | ✅ PASS |
| 模态分析 | ⏳ NOT_RUN（需 license） |
| PZT 材料属性 | ⏳ 候选 PZT-5H |
| 膜片位移估算 | ⏳ 10-50 μm（待验证） |

## P4-P5 完整仿真

| 项目 | 前置条件 |
|------|----------|
| 完整气流仿真 | P3 网格 + P2 膜片位移 |
| CHT 共轭传热 | P3 网格 + 固体材料属性 |
| FSI 流固耦合 | P2 模态 + P3 网格 + System Coupling |

## 论文缺口

| 缺口 | 状态 |
|------|------|
| First draft | 结构已定，内容待填充 |
| Figures & Tables | 清单已建 |
| Methodology 参数溯源 | 证据链文档已完成 |
| 仿真结果 | ⏳ 等待 P3 求解 |
| 网格独立性 | ⏳ 等待 G2/G3 网格 + license |
| 与公开数据对比 | ⏳ 需收集 Frore 性能数据 |

## 即时行动项

1. **Ansys License** — 打电话/发邮件给董如怡
2. **C7 几何候选** — bridge solids 方案（Windows 下次迭代）
3. **论文** — 用现有证据填充 Methodology + Introduction
4. **公开数据** — 收集 Frore 产品性能数据（用于验证）

## 风险

| 风险 | 可能性 | 影响 |
|------|--------|------|
| License 不批 | 中 | P3-P5 全阻塞 |
| 几何连接无法解决 | 低 | Student 版仍需粗网格 |
| 7/17 截止 | 高 | 需优先填充 paper |
