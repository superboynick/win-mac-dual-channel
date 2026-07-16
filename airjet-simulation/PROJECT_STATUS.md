# AirJet Mini Gen1 项目状态 — 2026-07-16

## 当前阶段：P3（网格生成）进行中

### 已完成

| 里程碑 | 状态 | 证据 |
|--------|:----:|------|
| P0 公开证据冻结 | ✅ PASS | 972 throat assignments SHA256 匹配 |
| CAD 全参数化 (SpaceClaim) | ✅ PASS | 12 单元 × 972 喉道 |
| PyFluent 自动网格流程 | ✅ PASS | Watertight → surface → volume 全通 |
| 诊断体网格 (0.15mm) | ⚠️ DIAG | 39,062 cells, OQ 0.49, 几何超差 |
| C5 静态冻结 (4 blockers) | ✅ PASS | 20 profiles, 全 contract 测试通过 |
| 教学文档 01-07 | ✅ DONE | 9 篇, ~15K 字, 已同步 Downloads |

### 🔧 进行中

- **C6 几何修复：** Windows 已推送 `bff9665`（内收式 clamped overlap），等待实跑
- **教学文档：** 持续扩充中

### ⏳ 待完成（P3→P4→P5）

| Gate | 内容 | 阻塞 |
|------|------|------|
| P3 | 合规 Stage 1 几何 | 等 C6 实跑验证 |
| P3 | 合规 Stage 2 网格 | 需合规 Stage 1 STEP |
| P4 | 固体域建模 (铜底座+TIM) | 等 P3 通过 |
| P5 | 稳态 CHT 求解 | 等 P4 + Academic license? |

### 📊 关键数字

- 喉道：972，孔径 0.25 mm
- 流体域：451.78 mm³ analytic
- 诊断网格：39,062 cells, min OQ 0.49
- 目标网格：200K → 2M cells（需 Academic license）
- 全自动管道：~6 min (Stage 1 + 2)

### 📧 外部依赖

- **Ansys 销售：** 董如怡 (ruyi.dong@ansys.com)，已联系，等回复
- **许可：** Student 2026 R1 已安装，1M cell/node 上限
