# AJM-WIN-V02-SPLIT-STEP-CONVERTER-006

目标：同一受审 MCP 会话运行 V02 producer → upstream/downstream 独立 STEP converter。
本轮只验证转换；不启动 Workbench、Mechanical、网格、求解或正式九变体 006。

要求签名 `GIT_READY`、clean `main`、`0/0`、项目 audit 和固定 guards 全部 PASS，然后只运行：

```powershell
C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe `
  .\airjet-simulation\automation\ansys\test_run_v02_parasolid_topology_006.py

C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe `
  .\airjet-simulation\automation\ansys\run_v02_split_step_converter_006.py
```

固定摘要：

```text
D:\AirJet_P1\AJM-P1-CAD-006\V02_SPLIT_STEP_CONVERTER_RUN_SUMMARY.json
```

必须保留 producer/converter raw jobs、reports、manifest、stderr 和以下转换产物：

```text
upstream.step
downstream.step
split_step_reimport.json
v02_face_inventory.json
source_chain.json
```

只有两个 STEP 分别回读为单一 closed/manifold body，且 face counts 为 2044/978、包络和体积保持，
才允许 `PASS_PRELIMINARY_SPLIT_STEP_CONVERTER`。这仍不证明两体已在同一 solver 模型组合、接口相邻、
网格共形、formal 006 或 P1；P1--P6、mesh、physics 始终 `NOT_RUN`。失败不得重试或换格式绕过。
