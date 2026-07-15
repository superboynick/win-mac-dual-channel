# AJM-WIN-V02-NATIVE-TOPOLOGY-OBSERVER-006

目标：在同一受审 MCP 会话运行 V02 producer → native staging Workbench/Mechanical topology observer。
这只是完整 12-cell/972-hole preliminary 几何的传递诊断；禁止 Edit、网格、求解、正式 006 和 P1 PASS。

## 硬门槛

1. 仅读取当前签名 `GIT_READY`；`main`、clean、`0/0`、签名与项目 audit 必须通过。
2. 运行：

```powershell
C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe `
  .\airjet-simulation\automation\ansys\test_run_v02_topology_observer_006.py

C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe `
  .\airjet-simulation\automation\ansys\run_v02_native_topology_observer_006.py
```

3. runner 必须使用同一 MCP server 进程重新生成 producer，并只把以下四件冻结产物交给 observer：

```text
v02_preliminary_producer.json
product_two_zone.scdocx
v02_face_inventory.json
native_reopen.json
```

4. observer 只能从 job-local staging 读取 native；禁止直接修改 predecessor，禁止 `Edit`、
`GenerateMesh`、`Solve`、结构/CFD/CHT 和九变体 campaign。

## 输出与判读

固定摘要：

```text
D:\AirJet_P1\AJM-P1-CAD-006\V02_NATIVE_TOPOLOGY_OBSERVER_RUN_SUMMARY.json
```

观察成功只允许写 `PASS_PRELIMINARY_NATIVE_TOPOLOGY_OBSERVER`；必须同时报告真实
`topology_result/topology_detail`。无论结果有利与否，均保持：

```text
formal_006_completion=false
p1_stage_gate=NOT_RUN
p1_p6_gates=NOT_RUN
mesh=NOT_RUN
physics=NOT_RUN
visibility=NOT_USER_OBSERVED
```

保存 raw job、stderr、report、inventory、project 与 artifact manifest；失败不得绕过或覆盖。
