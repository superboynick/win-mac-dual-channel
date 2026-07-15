# AJM-WIN-V02-NATIVE-MESH-CONFORMALITY-006

目标：在一个受审 MCP 会话内重新运行 V02 producer，然后对其冻结的
`product_two_zone.scdocx` 做一次完整 12-cell/972-hole、无物理的 Mechanical
粗网格共节点诊断。两个 observer 必须复用同一个 producer job 的同一 native SHA，以隔离
固定输入下的 attach/mesh 重复性。它不是正式 006，不运行结构、CFD、CHT，也不能宣布 P1 PASS。

## 硬门槛

1. 只执行 Mac 发布的精确 `GIT_READY=<40位提交>`：`main`、clean、与
   `origin/main` 为 `0/0`、签名有效；先运行 Python 与 PowerShell 项目审计。
2. 使用已验证的 automation Python，不启动任意 shell 型 MCP，不读取许可数据：

```powershell
C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe `
  .\airjet-simulation\automation\ansys\test_run_v02_topology_observer_006.py

C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe `
  .\airjet-simulation\automation\ansys\run_v02_native_mesh_conformality_006.py
```

3. runner 必须在同一 MCP server 进程重新生产并冻结以下四件前驱产物：

```text
v02_preliminary_producer.json
product_two_zone.scdocx
v02_face_inventory.json
native_reopen.json
```

4. observer 只能处理 job-local、初始 SHA 等于 predecessor 的 writable native copy。
   唯一允许的新增动作是 `ElementSize=0.5 mm` 和 `GenerateMesh()`；禁止 Edit、Solve、
   材料、载荷、边界条件、减 cell、减孔或静默改变网格尺寸。
5. 首次失败必须原样停下并留证，不自动运行 split STEP fallback，不修改 signed commit。

## PASS 的精确定义

只有以下条件全部成立，runner 才允许返回
`PASS_PRELIMINARY_NATIVE_MESH_CONFORMALITY`：

- native topology 仍是
  `972_SHARED_SINGLE_FACE / SHARED_ID_MEMBERSHIP_CONFIRMED`；
- 同一 producer/native SHA 的两个独立 observer 均达到 terminal PASS，关键拓扑/网格签名一致；
- 不存在自动 contact/connection object；连通性只由共享几何和共享网格节点承担；
- global 与两个 body 的 node/element counts 均大于 0；
- 972 个共享 face mesh region 均有节点；
- 每个目标界面节点 ID 同时属于 upstream/downstream body node set；
- 两个 body 的 node-set 交集精确等于这 972 个目标面的 node union，不存在额外共享节点；
- predecessor 不变、report/inventory/WBPJ 与 MCP manifest 的 size/SHA 闭合。

该 PASS 只证明这一次 preliminary V02 Mechanical 粗网格中的共享节点 ID。它不证明
Fluent zone interface、CFD 网格、网格质量或独立性、任何物理结果、正式九变体 006、
AirJet 产品内部真实结构或 P1 Gate。既有 native attach 一 PASS/一 FAIL 的重复性问题仍保持
`UNRESOLVED`。

## 固定输出与回报

```text
D:\AirJet_P1\AJM-P1-CAD-006\V02_NATIVE_MESH_CONFORMALITY_RUN_SUMMARY.json
```

必须回报：精确 commit、producer/observer job ID、两个 native SHA、最终状态、真实错误、
topology result/detail、global/body node/element counts、972 interface face count、interface/shared
node counts、unexpected shared count、raw report/inventory/WBPJ/manifest SHA，以及：

```text
formal_006_completion=false
p1_stage_gate=NOT_RUN
p1_p6_gates=NOT_RUN
physics=NOT_RUN
visibility=NOT_USER_OBSERVED
```

原始大产物留在 `D:\AirJet_P1\AJM-P1-CAD-006\jobs\`，Git 只提交凝练、脱敏、可哈希复核的
证据摘要；提交前重新跑双审计，签名 commit，并 push 到 `origin/main`。
