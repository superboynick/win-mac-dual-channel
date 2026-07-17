# 双线并行计划

## Codex A — ANSYS Track（继续，不放弃）
| 任务 | 状态 |
|---|---|
| SpaceClaim CAD 几何 | ✅ 自动产出STEP |
| Fluent 水密网格 | ✅ 25+连跑一致 |
| Fluent CFD 求解 | 🔄 BC修复中 |
| Mechanical 模态分析 | ⏳ 待启动 |
| Mechanical 谐响应 | ⏳ 待启动 |
| → 输出 membrane_params.json | ⏳ |

## Codex B — OpenFOAM Track（新增）
| 任务 | 状态 |
|---|---|
| Docker + OpenFOAM 安装 | ⏳ |
| 单cell CFD（动网格） | ⏳ |
| 整机 CFD | ⏳ |
| CHT 共轭传热 | ⏳ |
| → 输出 cell_results.json | ⏳ |

## 耦合（A ↔ B 通过 Git）
```
A 跑 Mechanical → membrane_params.json → B 用作动网格BC
B 跑 CFD       → cell_results.json     → A 与数据表验证
```

## 为什么两条线都要
- ANSYS：有 Mechanical（压电），网格管线成熟，已有25+连跑数据
- OpenFOAM：无网格限制，CFD能力强，可做整机
- **两个互补，不是取代关系**
