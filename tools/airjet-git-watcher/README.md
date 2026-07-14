# AirJet signed dual-endpoint Git watcher

> Runtime status: `DISABLED_PENDING_END_TO_END`（2026-07-14）。Mac 端 80 项与
> Windows 端 50 项隔离行为测试通过，但真实双端 Codex 窗口和登录启动尚未完成。
> 在用户观察真实可见唤醒以前，不得把 runtime 常量改为 enabled，也不得注册
> LaunchAgent 或 Scheduled Task。

本工具让 Mac 与 Windows 通过 GitHub `main` 同步 AirJet 仓库，并只对对端专用
签名 key 授权的任务启动 Codex。没有更新时不调用模型。普通 signed commit 只
同步数据；只有严格的目标任务信封才可请求唤醒。

## 文件与机器外状态

- `mac/`：watcher、runner、manager 和 LaunchAgent installer。
- `windows/`：PowerShell 5.1 对称实现、manager 和 InteractiveToken AtLogOn
  installer。
- `tests/`：只使用临时 bare Git 仓库，不联系 GitHub、不启动真实 Codex。
- `wake-policy.md`：被唤醒 Codex 的权限和交付规则。
- `airjet-simulation/collaboration/README.md`：签名任务信封 schema 与设计理由。

机器外状态固定为：

```text
Mac:     ~/Library/Application Support/AirJetGitWatcher/
Windows: %LOCALAPPDATA%\AirJetGitWatcher\
```

其中包含 trust、pending、processed claim、event 和 log。签名私钥、trust 根、
Codex 报告和运行状态不得提交 Git。生产 trust 文件由固定 SHA256 再校验；测试
模式只能使用临时路径，并被 runner 硬禁止启动真实 Codex。

## Git 与签名验证

每轮检查固定 repository、`main`、`origin/main`、SSH 443 remote、clean worktree、
non-shallow 和 fast-forward 关系。`old..target` 最多 100 条且必须是无 merge 的
线性历史；每条 commit 都必须由本地 Git 外 `allowed_signers` 中的 Mac 或 Windows
专用 Ed25519 key 验证通过。

任务信封必须只在 target tip 修改一次：

- `MAC_TASK.env` 只能由 Windows task signer 授权；
- `WINDOWS_TASK.env` 只能由 Mac task signer 授权；
- 同一 incoming range 改动两个端点、任务不在 tip、错误 key、unsigned、revoked
  key 或重复 task ID 都会 fail closed。

runner 在启动前重新核对 HEAD、clean、remote OID、全链签名、对端 task-tip 签名
和 committed instruction，并用 atomic processed claim 保证同一任务至多一个
runner 获得执行权。watcher、`.gitattributes` 和 `.gitmodules` 更新始终阻断，
需要人工审查和手动部署。

## 任务 schema

当前只启用无自动接力的根任务：

```text
schema_version=2
type=task
source=mac
target=windows
action=wake_codex
task_id=ajm-example-001
workflow_id=ajm-example-workflow
parent_task_id=NONE
hop=0
max_hops=0
instruction_path=airjet-simulation/collaboration/instructions/ajm-example-001.md
```

发给 Mac 时交换 source/target。信封必须恰好 11 个字段；instruction 必须是固定
目录下的 100644 普通 blob。自动 reciprocal relay 与 receipt 驱动接力当前为
`RESERVED_NOT_ENABLED`，不能用非零 hop 绕过。

## Codex 执行模式

任务使用可见 Terminal/PowerShell 窗口启动 `codex exec`，固定：

```text
sandbox=workspace-write
approval=never
reasoning_effort=high
```

`never` 是针对用户明确授权的无人值守任务；写权限仍限定于仓库和专用报告目录。
任务正文来自 signed commit，而不是 mutable pending 文件。进程、session 和 Explorer
证据只能证明启动请求处于交互桌面，用户肉眼确认前仍必须记录
`NOT_USER_OBSERVED`，不能写成 visible PASS。

## 隔离测试

Mac：

```sh
cd /Users/zhangjianxiao/win-mac-dual-channel
sh tools/airjet-git-watcher/tests/test-watch-airjet-git.sh
```

预期：

```text
CORE_CASES_PASS=80
EXPECTED_PASS_COUNT=80
OVERALL=PASS_CORE_RUNTIME_DISABLED
```

Windows：

```powershell
cd C:\Users\admin\win-mac-dual-channel
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\airjet-git-watcher\tests\test-watch-airjet-git-windows.ps1
```

预期：

```text
WINDOWS_CORE_CASES_PASS=50
EXPECTED_PASS_COUNT=50
OVERALL=PASS_CORE_RUNTIME_DISABLED
```

## 当前安全命令

runtime locked 时只允许 status 和真实仓库的单次 no-wake 同步：

```sh
sh tools/airjet-git-watcher/mac/manage-airjet-watcher.sh status
sh tools/airjet-git-watcher/mac/manage-airjet-watcher.sh once
```

```powershell
powershell -NoProfile -ExecutionPolicy RemoteSigned -File .\tools\airjet-git-watcher\windows\Manage-AirJetWatcher.ps1 -Action status
powershell -NoProfile -ExecutionPolicy RemoteSigned -File .\tools\airjet-git-watcher\windows\Manage-AirJetWatcher.ps1 -Action once
```

`start`、`retry`、真实 wake 和 startup registration 当前均由 manager、watcher、
runner/installer 多层拒绝，不能通过直接调用子脚本绕过。

## E2E 通过后的登录启动

Mac 使用当前可见用户的 LaunchAgent；Windows 使用当前登录用户、
`InteractiveToken`、`Limited` 的 AtLogOn Scheduled Task。两者是“用户登录后启动”，
不是无桌面系统服务，因为 Codex 窗口必须属于真实 GUI session。

解锁后的安装入口为：

```sh
sh tools/airjet-git-watcher/mac/install-mac-watcher.sh install --poll-seconds 180
```

```powershell
powershell -NoProfile -ExecutionPolicy RemoteSigned -File .\tools\airjet-git-watcher\windows\Install-AirJetWatcher.ps1 -RegisterAtLogOn
```

installer 默认不注册；只有代码中的 runtime gate 已在 E2E 后显式变更，注册分支
才会通过。Windows installer 还要求预先 bootstrap 且哈希正确的 Git 外 trust，
不会从仓库自动导入任何公钥。
