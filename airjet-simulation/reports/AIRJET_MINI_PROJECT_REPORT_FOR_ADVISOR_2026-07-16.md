# AirJet Mini Gen1 整机仿真项目报告

**日期：** 2026-07-16
**研究者：** Nick Zhang
**项目仓库：** github.com/superboynick/win-mac-dual-channel

---

## 1. 项目概述

对 Frore Systems AirJet Mini Gen1 固态主动散热芯片进行全产品 CFD 仿真重建。
所有参数来自公开资料（产品规格书、专利、教程），所有步骤自动化（SpaceClaim + PyFluent）。

## 2. 技术路线

```
公开资料 → 参数提取 → SpaceClaim 参数化CAD → STEP几何 → 
  PyFluent Watertight网格 → 体网格 → (后续)求解器
```

**工具链：** ANSYS Student 2026 R1 (SpaceClaim + Fluent + PyFluent)
**运行平台：** Windows 11 工作站 (Intel Core Ultra 9 275HX, 24 cores)
**许可限制：** Student 版 1M cells/nodes 上限（已申请 Academic Research license）

## 3. 当前进度

### ✅ 已完成（截至 2026-07-16）

| Gate | 内容 | 状态 |
|---|---|---|
| P0 | 项目初始化、环境配置、Git 协作 | ✅ |
| P1 | 参数提取与几何合同 | ✅ |
| P2 | 参数化 CAD (SpaceClaim) | ✅ |
| P3 | CFD 网格生成 | 🔄 99% |
| P4 | 求解器设置 | ⏳ |
| P5 | CHT 共轭传热 | ⏳ |
| P6 | FSI 流固耦合 | ⏳ |

### P3 详细状态

| 指标 | 值 |
|---|---|
| 几何 | 主流体域 451.8 mm³，972 个微喷口，12 单元 (3×4) |
| 面网格 | 334,190 faces，1 fluid + 11 voids |
| 体网格 (诊断) | 39,062 cells，min OQ 0.49 |
| 自动化耗时 | ~6 分钟 (Stage 1: 2min + Stage 2: 4min) |
| 待解决 | Boolean overlap 几何合同 (C6 内收式修复进行中) |

## 4. 关键技术挑战与解决

### 4.1 几何 Boolean 连接
- **问题：** SpaceClaim Boolean Merge 在 perimeter 边界处需要重叠
- **方案 C1 (0.02mm)：** 域选择指向 actuator gap 而非主流体
- **方案 C5 (0.15mm)：** 修复域选择但改变包络 +0.025mm
- **方案 C6 (0.05mm 内收式)：** 代码已提交，待运行验证

### 4.2 Student License 限制
- 1M cells 上限 → 粗网格仅 39K
- 学术网格独立性需 500K-2M cells
- 已联系 Ansys 销售申请 Academic Research License

### 4.3 自动化协作
- Mac ↔ Windows 双端 Git 协作
- Git watcher 自动轮询新任务
- 教学文档一式三份（Mac Downloads + Windows Downloads + Git）

## 5. 产出物清单

### 代码
- `v03_continuous_fluid_producer.py` — SpaceClaim 参数化几何
- `v03_pyfluent_watertight_mesh_consumer.py` — PyFluent 网格
- `save_mesh4.py` — 最小可行网格脚本
- `v03_finite_throat_route_v1.json` — 冻结参数合同

### 文档
- `AIRJET_SIMULATION_REPRODUCTION_GUIDE.md` — 完整复现指南
- `teaching/01-07` — 7 篇教学文档（CFD 基础 → FSI）
- `PAPER_FIRST_DRAFT_STRUCTURE.md` — 论文结构

### 网格
- `v03_mesh.msh.h5` — 35K cells 体网格（已存入 Git）

## 6. 下一步 (48h)

1. C6 Stage 1 运行 → 验证几何合同
2. 如 PASS → C6 Stage 2 mesh → 确认域选择
3. 网格独立性研究（需 Academic license）
4. 论文 first draft 完成

## 7. 需要的支持

- **Ansys Academic Research License** — 已联系销售董如怡
- **计算资源** — 当前单台工作站足够粗网格；精细网格可能需要 cloud
