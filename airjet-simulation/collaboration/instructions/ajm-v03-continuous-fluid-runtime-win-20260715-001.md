# Windows runtime task: V03 full-product continuous-fluid pilot

Windows 负责在 ANSYS Student 2026 R1 上执行 V03 SpaceClaim pilot，并冻结原始证据。本任务不启动
Workbench、Mechanical、Fluent、mesh 或 physics。

## 开始门槛

1. `git fetch origin`，只允许 clean `main` 通过 `git pull --ff-only` 前进到包含本任务的签名提交。
2. 确认 `HEAD == origin/main`、ahead/behind=`0/0`、`git verify-commit HEAD` 成功。
3. 严格读取并执行
   `airjet-simulation/windows-prompts/AJM_WIN_V03_CONTINUOUS_FLUID_006.md`。
4. focused guard、MCP policy、Python audit、PowerShell audit 任一失败即停止，不启动 ANSYS。

## 唯一运行任务

只运行一次：

```powershell
C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe `
  .\airjet-simulation\automation\ansys\run_v03_continuous_fluid_006.py
```

runner 只能调用固定 hash-pinned profile
`ajm006-spaceclaim-v03-continuous-throat-pilot-v1`。不得手工运行 producer，不得改 profile、阈值、
输入 CSV、孔数、尺寸或报告。首次 submit/SpaceClaim/native reopen/STEP reopen/validator 失败原样停止，
不得自动重试。

## 证据边界

原始大产物留在 `D:\AirJet_P1\AJM-P1-CAD-006\`。必须保留 runner summary、job state、artifact
manifest、producer report、stdout/stderr、native、STEP 和三个 inventory/source-chain JSON。

只有 runner literal 返回 `PASS_PRELIMINARY_V03_CONTINUOUS_FLUID_PRODUCER` 才可写 PASS。它只证明
初步完整产品流体域的连续几何和往返计数通过，仍为 `formal 006=NOT_RUN`、`P1-P6=NOT_RUN`、
`mesh=NOT_RUN`、`physics=NOT_RUN`、`PyFluent=NOT_RUN`、`visibility=NOT_USER_OBSERVED`。

完成后可把凝练结果提交 Git；不得加入大 CAD 文件。签名 commit、正常 push，分叉时停止，禁止
reset/rebase/force。固定回报：

```text
RUNTIME_TASK=PASS|FAIL
GIT_HEAD_EXECUTED=<40hex>
JOB_ID=<id|NOT_SUBMITTED>
FINAL_STATUS=<literal>
PRODUCER_STATUS=<literal|NOT_REACHED>
CONTINUOUS_BODY=<literal|NOT_REACHED>
NATIVE_REOPEN=<literal|NOT_REACHED>
STEP_REIMPORT=<literal|NOT_REACHED>
THROAT_COUNT=<integer|NOT_REACHED>
CELL_COUNTS=<literal|NOT_REACHED>
BOUNDARY_COUNTS=<literal|NOT_REACHED>
ANSYS_PROCESS_COUNT_AFTER=<integer>
WORKBENCH=NOT_RUN
MESH=NOT_RUN
PHYSICS=NOT_RUN
P1-P6=NOT_RUN
VISIBILITY=NOT_USER_OBSERVED
GIT_READY=<signed result commit|NOT_COMMITTED>
```
