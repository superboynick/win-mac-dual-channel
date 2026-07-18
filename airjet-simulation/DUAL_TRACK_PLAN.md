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

## Codex B — OpenFOAM Track（Mac 恢复审计；P3–P5 均 NOT_RUN）
| 任务 | 状态 |
|---|---|
| 本机工具链只读清点 | `TOOLING_NOT_INSTALLED`；smoke `NOT_RUN` |
| P3 单-cell 瞬态 CFD 校准（非整机结果） | `NOT_RUN` — 等待 P1 chambers/orifices、P2 displacement field 与 tooling smoke |
| P4 整机气动 | `NOT_RUN` — 等待 P1 完整流体体积与 P3 传递接口 |
| P5 整机 CHT | `NOT_RUN` — 等待 P4 整机流场 |
| → P3 传递接口/证据包 | `NOT_CREATED` — 仅有 pending schema |

## 耦合（A ↔ B 通过 Git）
```
A/P2 经审计位移场 → B/P3 单-cell 传递校准 → B/P4 整机气动
B/P4 整机流场     → B/P5 整机 CHT       → P6 多指标标定/验证
```

## 为什么两条线都要
- ANSYS：有 Mechanical（压电），网格管线成熟，已有25+连跑数据
- OpenFOAM：候选开源 CFD/CHT 路线；本机 tooling、资源与整机可行性尚待 smoke/P3/P4/P5 分级验证
- **两个互补，不是取代关系**
