# Windows runtime task: V02 split STEP converter fallback

Windows 负责本任务的 ANSYS/SpaceClaim 实跑和原始证据冻结。此前 frozen native attach 路线已有
一次 PASS、两次 FAIL；最新一次失败已经在签名 commit
`b1e98f1fb33ec230074c15ab6dcc00838b8921ce` 留档，失败发生在 Workbench 附加 native
`product_two_zone.scdocx`，尚未进入 Mechanical inventory、topology 或 mesh。该重复故障触发预先
规划的 split STEP 转换回退，但不授权宣称 native 几何、网格或物理已经失败。

本信封是新的 schema-v2 根任务：`parent_task_id=NONE`、`hop=0`、`max_hops=0`，不得改写。

## 开始门槛

1. `git fetch origin`；工作树必须 clean、当前分支为 `main`，只允许 ff-only 到包含本任务的目标
   commit。随后必须 `HEAD == origin/main`、ahead/behind=`0/0`，并验证新提交签名。
2. 严格读取并执行
   `airjet-simulation/windows-prompts/AJM_WIN_V02_SPLIT_STEP_CONVERTER_006.md`。
3. 先运行：

```powershell
C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe `
  .\airjet-simulation\automation\ansys\test_run_v02_parasolid_topology_006.py

python -B .\codex-skills\airjet-ansys-automation\scripts\test_airjet_ansys_mcp_policy.py
python -B .\codex-skills\airjet-product-reconstruction\scripts\audit_project.py --repo .
powershell -NoProfile -File .\audit-airjet-project.ps1 -RepoRoot .
```

任一失败立即停止，不启动 ANSYS。

## 唯一允许的 ANSYS 任务

只运行：

```powershell
C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe `
  .\airjet-simulation\automation\ansys\run_v02_split_step_converter_006.py
```

runner 只允许同一受审 MCP 会话运行一次 V02 producer，然后对其 immutable native predecessor
进行 upstream/downstream 独立 STEP 转换与回读。禁止启动 Workbench、Mechanical、Fluent、网格、
求解、物理、正式九变体 006、删孔、删 cell、改尺寸或自动改用其他格式。

首次 submit/conversion/reimport/validator 失败必须原样停止，不得重试、改阈值、覆盖摘要或绕过。
失败也须保留已返回的 producer/converter job、terminal state、manifest、report、stdout/stderr 和错误
检查点。结束后只确认本任务拥有的 ANSYS/MCP 进程树为 0，不得终止其他会话进程。

## 结果边界

只有 upstream/downstream STEP 分别回读为单一 closed/manifold body，face counts 精确为 2044/978，
包络、体积、source chain 与 artifact hash 全部满足冻结合同，才允许
`PASS_PRELIMINARY_SPLIT_STEP_CONVERTER`。

即使 PASS，也只证明两个独立 STEP 转换产物保留了各自的初步几何计数和封闭性；不得写两体已经
在同一 solver model 组合、接口相邻或共享、conformal mesh、Fluent/CFD、物理结果、formal 006 或
P1。`P1-P6=NOT_RUN`、`MESH=NOT_RUN`、`PHYSICS=NOT_RUN`、
`VISIBILITY=NOT_USER_OBSERVED`。

## 证据和 Git

原始大产物留在 `D:\AirJet_P1\AJM-P1-CAD-006\`。Git 只加入凝练证据：执行 commit、job IDs、
native SHA、terminal states、真实 conversion/reimport counts、包络/体积、artifact size/SHA、process
cleanup 与声明边界。同步更新 `MODEL_ANNOTATIONS.md`、`PROJECT_STATUS.md`、
`logs/REALITY_AND_FAILURE_LOG.md` 和 `logs/run-index.csv`；不得改写既有事实。

完成后重新运行四项静态检查和 `git diff --check`，签名 commit，正常 push。若双边分叉，停止并
报告，禁止 reset/rebase/force。

固定回报：

```text
RUNTIME_TASK=PASS|FAIL
GIT_HEAD_EXECUTED=<40hex>
PRODUCER_JOB=<id|NOT_SUBMITTED>
CONVERTER_JOB=<id|NOT_SUBMITTED>
FIXED_NATIVE_SHA256=<64hex|NOT_REACHED>
FINAL_STATUS=<literal>
UPSTREAM_REIMPORT=<literal|NOT_REACHED>
DOWNSTREAM_REIMPORT=<literal|NOT_REACHED>
FACE_COUNTS=<literal|NOT_REACHED>
ANSYS_PROCESS_COUNT_AFTER=<integer>
WORKBENCH=NOT_RUN
MESH=NOT_RUN
FORMAL_006=NOT_RUN
P1-P6=NOT_RUN
PHYSICS=NOT_RUN
VISIBILITY=NOT_USER_OBSERVED
GIT_READY=<full signed Windows result commit|NOT_COMMITTED>
```
