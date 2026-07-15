# AJM-WIN-V02-PARASOLID-TOPOLOGY-OBSERVER-006

## 任务性质

这是 AirJet Mini Gen1 整机 V02 的诊断性 Parasolid 路线试验，不是正式 006 完成任务，也不是 P1 Gate。只允许执行仓库内固定的三阶段 runner：

1. SpaceClaim V02 preliminary producer；
2. 冻结 native 的 job-local staging copy 转换为 `product.x_t` 并回读；
3. Workbench/Mechanical 只读拓扑 observer。

三阶段必须在同一个 MCP server 进程内依次运行。禁止直接启动 `RunWB2.exe`、SpaceClaim、Workbench、Mechanical 或其他 solver job；禁止启动网格、结构、CFD、CHT 或九变体。

## Git 身份硬门

Mac 协调端必须另行给出 `GIT_READY=<40 位完整 commit>`。没有该值就停止。以下操作都在 PowerShell 执行：

```powershell
$ErrorActionPreference = 'Stop'
$Repo = 'C:\Users\admin\win-mac-dual-channel'
$ReadyCommit = '<GIT_READY_40HEX_FROM_MAC>'
Set-Location $Repo

if ($ReadyCommit -notmatch '^[0-9a-f]{40}$') { throw 'BLOCKED_INVALID_GIT_READY' }
if ((git branch --show-current).Trim() -ne 'main') { throw 'BLOCKED_NOT_MAIN' }
if ((git rev-parse --abbrev-ref '@{upstream}').Trim() -ne 'origin/main') { throw 'BLOCKED_WRONG_UPSTREAM' }
if (@(git status --porcelain).Count -ne 0) { throw 'BLOCKED_DIRTY_BEFORE_PULL' }

git fetch origin
$Divergence = (git rev-list --left-right --count HEAD...origin/main).Trim() -split '\s+'
if ([int]$Divergence[0] -ne 0) { throw 'BLOCKED_LOCAL_AHEAD_OR_DIVERGED' }
if ([int]$Divergence[1] -gt 0) { git pull --ff-only origin main }

$Head = (git rev-parse HEAD).Trim()
if ($Head -ne $ReadyCommit) { throw "BLOCKED_HEAD_MISMATCH actual=$Head expected=$ReadyCommit" }
git verify-commit HEAD
if ($LASTEXITCODE -ne 0) { throw 'BLOCKED_UNSIGNED_OR_UNVERIFIED_COMMIT' }
if (@(git status --porcelain).Count -ne 0) { throw 'BLOCKED_DIRTY_AFTER_PULL' }
$Divergence = (git rev-list --left-right --count HEAD...origin/main).Trim() -split '\s+'
if ([int]$Divergence[0] -ne 0 -or [int]$Divergence[1] -ne 0) { throw 'BLOCKED_NOT_0_AHEAD_0_BEHIND' }

powershell -NoProfile -ExecutionPolicy RemoteSigned -File .\audit-airjet-project.ps1 -RepoRoot $Repo
if ($LASTEXITCODE -ne 0) { throw 'BLOCKED_PROJECT_AUDIT_FAILED' }
```

任一硬门失败：原样保存终端输出并停止。禁止用编辑、commit、push、reset、clean、rebase、force、跳过签名或弱化断言来绕过。

## 固定运行命令

```powershell
$Python = 'C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe'
$Test = '.\airjet-simulation\automation\ansys\test_run_v02_parasolid_topology_006.py'
$Runner = '.\airjet-simulation\automation\ansys\run_v02_parasolid_topology_006.py'
$Summary = 'D:\AirJet_P1\AJM-P1-CAD-006\V02_PARASOLID_TOPOLOGY_RUN_SUMMARY.json'

& $Python -I -B $Test
if ($LASTEXITCODE -ne 0) { throw "BLOCKED_STATIC_GUARDS exit=$LASTEXITCODE" }

& $Python -I -B $Runner
$RunnerExit = $LASTEXITCODE
Write-Host "RUNNER_EXIT=$RunnerExit"
if (Test-Path -LiteralPath $Summary) { Get-Content -Raw -LiteralPath $Summary }
if ($RunnerExit -ne 0) { throw "PARASOLID_PILOT_FAILED exit=$RunnerExit" }
```

不要传入许可参数，不读取或修改许可、注册表、服务、防火墙、环境变量或安装目录。

## 唯一允许的成功语义

- runner：`PASS_PRELIMINARY_PARASOLID_TOPOLOGY_OBSERVER`；
- converter：`PASS_PARTIAL_CAD_CAPABILITY`，12 个 assertions 全真；
- converter 的 native source/open/x_t reimport face counts 都为 `[978, 2044]`；
- `source_native_mutated=false`，`representation_conversion=true`；
- converter predecessor 完整目录树和 staging workspace 最终复核不变；
- observer：`PASS_PRELIMINARY_PARASOLID_TOPOLOGY_OBSERVATION`，8 个 assertions 全真；
- observer 的 body 角色绑定有效，逐角色 face count、bbox、volume 与 x_t 回读相符；
- topology result/detail 必须属于 runner 中锁定的合法组合；
- `route_assessment` 单独报告。只有界面分类为 shared/coincident、逐对几何重合、solver face counts 与整机 envelope/volume 均保持时，才可为 `PASS_CANDIDATE_ROUTE_TO_MESH`。

即使为 `PASS_CANDIDATE_ROUTE_TO_MESH`，也只代表“允许进入下一次网格诊断”，不代表 shared node、conformal mesh、P1 或任何论文结果已通过。所有运行都必须保持：

- `formal_006_completion=false`；
- P1 和 P2-P6：`NOT_RUN`；
- mesh：`NOT_EVALUATED_NO_MESH`；
- physics：未运行。

## 回报与保存

成功或失败都不删除、不覆盖原始 job 目录。回报：

- `GIT_COMMIT`、签名验证、clean、ahead/behind、项目审计；
- producer/converter/observer 三个 job ID 和 phase；
- converter/observer 状态及 assertions；
- `topology_result`、`topology_detail`、`route_assessment` 与 basis；
- runner summary 路径、MCP stderr 路径、三个 raw job 目录；
- `product.x_t`、`parasolid_reimport.json`、`source_chain.json`、solver inventory 和 `.wbpj` 是否存在及哈希。

运行结束后停止，不修改、提交或推送 Git，等待 Mac 协调端验收。
