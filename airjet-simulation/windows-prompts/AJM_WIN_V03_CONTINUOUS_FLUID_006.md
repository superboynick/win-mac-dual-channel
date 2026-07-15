# AJM-WIN-V03-CONTINUOUS-FLUID-006

目标：运行 AirJet Mini Gen1 整机 3x4/12-cell V03 连续流体域几何 pilot。V03 保留 972 个
直径 0.25 mm、有效长度 0.10 mm 的显式孔喉，并用 0.001 mm 数值重叠把原两体合并为一个
closed/manifold 连续流体体。本轮仅验证 SpaceClaim native/STEP 往返和边界计数；不运行
Workbench、Mechanical、Fluent、网格或物理。

必须从 clean、签名、`main == origin/main` 的提交执行。先运行：

```powershell
C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe `
  .\airjet-simulation\automation\ansys\test_run_v03_continuous_fluid_006.py
python -B .\codex-skills\airjet-ansys-automation\scripts\test_airjet_ansys_mcp_policy.py
python -B .\codex-skills\airjet-product-reconstruction\scripts\audit_project.py --repo .
powershell -NoProfile -File .\audit-airjet-project.ps1 -RepoRoot .
```

期望分别出现 `AJM006_V03_CONTINUOUS_FLUID_GUARDS=PASS_ALL`、
`profiles=18 tools=5`、两端项目审计 PASS 且 `required_files=149`。任一失败立即停止。

唯一允许的 ANSYS 命令：

```powershell
C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe `
  .\airjet-simulation\automation\ansys\run_v03_continuous_fluid_006.py
```

固定摘要：

```text
D:\AirJet_P1\AJM-P1-CAD-006\V03_CONTINUOUS_FLUID_RUN_SUMMARY.json
```

PASS 必须同时满足：单一 continuous body；native/STEP 重开均为 one-piece、closed、manifold；
972 个孔喉侧壁与冻结 XY 一一对应；12 个 cell 各 81 孔；4 inlet、1 outlet、12/12 membrane、
1 heat wall；主 report 小于 MCP 128 KiB inline 上限；7 个产物 hash/size 一致。

C016=0.10 mm 仍是 C 类探索候选，并非实测产品参数。即使 PASS，也不得宣称 formal 006、P1、
网格、Fluent、CHT 或物理已完成。首次失败必须保留原始 report/manifest/stdout/stderr 并停止，
不得重试、删孔、删 cell、放宽容差或改格式绕过。
