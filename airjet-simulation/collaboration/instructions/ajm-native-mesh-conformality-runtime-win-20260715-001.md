# Windows runtime task: fixed-input native mesh conformality diagnostic

Windows 负责本任务的 ANSYS 实跑和原始证据冻结。Mac 已在签名 commit
`9f4e3de7a47db3b2e9260ff4319ad7228b6dbca4` 完成 17-profile 静态包、Python/MCP policy/
Mac project audit；Windows 已对同一 commit 完成 Python 与 PowerShell project audit，均 PASS。
本信封是新的 schema-v2 根任务：`parent_task_id=NONE`、`hop=0`、`max_hops=0`，不得改写。

## 开始门槛

1. 先 `git fetch origin`；工作树必须 clean、`main`、可 ff-only 到包含本任务的 target tip，随后
   `HEAD == origin/main`、ahead/behind=`0/0`。逐提交签名必须通过 Git 外 allowed-signers 信任。
2. 严格读取并执行
   `airjet-simulation/windows-prompts/AJM_WIN_V02_NATIVE_MESH_CONFORMALITY_006.md`。
3. 先运行：

```powershell
C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe `
  .\airjet-simulation\automation\ansys\test_run_v02_topology_observer_006.py

python -B .\codex-skills\airjet-ansys-automation\scripts\test_airjet_ansys_mcp_policy.py
python -B .\codex-skills\airjet-product-reconstruction\scripts\audit_project.py --repo .
powershell -NoProfile -File .\audit-airjet-project.ps1 -RepoRoot .
```

任一失败立即停止，不启动 ANSYS。

## 唯一允许的 ANSYS 任务

只运行：

```powershell
C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe `
  .\airjet-simulation\automation\ansys\run_v02_native_mesh_conformality_006.py
```

runner 必须只生产一次 V02 producer，然后让两个独立 observer 复用同一个 predecessor job 和
同一 `product_two_zone.scdocx` SHA。observer 只允许 0.5 mm、无物理 Mechanical 网格；禁止
Edit、Solve、材料、载荷、结构、Fluent、CFD、CHT、删孔、删 cell、改变网格尺寸、正式九变体
006，以及 split STEP fallback。

首次 submit/attach/mesh/validator 失败必须原样停止；不得自动重试、绕过、改阈值或覆盖摘要。
失败也必须保留已返回的 producer、repeat #1/#2 terminal state、manifest、report、inventory、WBPJ、
stdout/stderr 与错误检查点。结束后确认本任务拥有的 ANSYS/MCP 进程树为 0；不得结束用户或其他
会话拥有的进程。

## 结果边界

PASS 只允许写：同一 frozen native SHA 的两个 preliminary Mechanical observer 都达到
`972_SHARED_SINGLE_FACE / SHARED_ID_MEMBERSHIP_CONFIRMED`，0.5 mm 网格的 global/body counts
为正，972 个目标 face region 非空，body node-set 交集精确等于目标界面 node union，且没有额外
contact/connection object 或 unexpected shared nodes；两个关键观察签名一致。

即使 PASS，也不得写 Fluent/CFD interface、网格质量/独立性、物理结果、产品内部真实结构、
formal 006 或 P1。`P1-P6=NOT_RUN`、`PHYSICS=NOT_RUN`、`VISIBILITY=NOT_USER_OBSERVED`。

## 证据和 Git

原始大产物留在 `D:\AirJet_P1\AJM-P1-CAD-006\`。Git 只加入凝练证据：执行 commit、job IDs、
native SHA、terminal states、真实错误、topology/mesh/contact/node/element counts、artifact size/SHA、
process cleanup、声明边界。同步更新 `MODEL_ANNOTATIONS.md`、`PROJECT_STATUS.md`、
`logs/REALITY_AND_FAILURE_LOG.md` 与 `logs/run-index.csv`；不得改写既有历史事实。

完成后重新运行四项静态检查与 `git diff --check`，签名 commit，正常 push。Windows 可以写并
解决与自己本任务文件相关的非分叉变更；如已发生双边分叉，停止并报告，禁止 reset/rebase/force。

固定回报：

```text
RUNTIME_TASK=PASS|FAIL
GIT_HEAD_EXECUTED=<40hex>
PRODUCER_JOB=<id|NOT_SUBMITTED>
OBSERVER_1_JOB=<id|NOT_SUBMITTED>
OBSERVER_2_JOB=<id|NOT_SUBMITTED>
FIXED_NATIVE_SHA256=<64hex|NOT_REACHED>
FINAL_STATUS=<literal>
TOPOLOGY_RESULT=<literal|NOT_REACHED>
TOPOLOGY_DETAIL=<literal|NOT_REACHED>
MESH_CONFORMALITY=<literal|NOT_REACHED>
REPEATABILITY=<literal|NOT_REACHED>
ANSYS_PROCESS_COUNT_AFTER=<integer>
SPLIT_STEP_EXECUTION=NOT_RUN
FORMAL_006=NOT_RUN
P1-P6=NOT_RUN
PHYSICS=NOT_RUN
VISIBILITY=NOT_USER_OBSERVED
GIT_READY=<full signed Windows result commit|NOT_COMMITTED>
```
