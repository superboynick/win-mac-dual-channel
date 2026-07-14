# AirJet 双端任务信封协议

本目录只保存可审计的任务授权、任务正文和结果回执。GitHub `main`
仍是唯一共享事实源；Mac 与 Windows Codex 是平级执行端。机器外的签名私钥、
信任根、进程状态、日志和 Codex 报告不得提交到 Git。

## 1. 为什么任务必须是签名的 tip commit

普通 Git push 凭据只能证明某个账号能够推送，不能证明是哪一台受信机器授权
Codex 执行。双端 watcher 因此使用两层验证：

1. `old..target` 的每一条 incoming commit 都必须由 Mac 或 Windows 的专用
   Ed25519 Git signing key 签名；
2. 真正修改目标任务信封的 commit 必须就是 `target`，并且由对端机器的
   signing key 签名。

自动模式只接受最多 100 条的线性历史，拒绝 merge commit、shallow repository、
replace refs、大小写碰撞和同一 incoming range 同时修改两个端点的任务信封。
这样，任务正文、执行上下文和授权签名固定在同一个不可变 commit 上。

## 2. 端点文件

- `WINDOWS_TASK.env`：只能由 Mac signing key 授权，目标是 Windows。
- `MAC_TASK.env`：只能由 Windows signing key 授权，目标是 Mac。
- `instructions/<task-id>.md`：任务正文；必须与任务信封处于同一 target commit。
- `receipts/<task-id>.env`：完成后的不可变回执；回执本身不触发唤醒。

固定任务信封可以被后续新任务替换，但 `task_id` 不得重用。两端各自在 Git
之外保存 processed ledger，因此旧信封或旧 commit 不能重复唤醒。

## 3. 严格 schema v2

信封必须恰好包含以下 11 个字段，不允许未知字段、重复字段或省略字段：

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

发给 Mac 时交换 `source` 与 `target`。`task_id`、`workflow_id` 和非 `NONE`
的 `parent_task_id` 只能使用 1--80 个 ASCII 字母、数字、点、下划线或连字符。
`instruction_path` 必须位于固定的 `instructions/` 前缀下，必须是 target tree
中的普通 blob，最大 64 KiB。信封最大 8 KiB。

首版运行时只接受根任务：`parent_task_id=NONE`、`hop=0`、`max_hops=0`。
任何非零 hop 或非 `NONE` parent 都以 `automatic_relay_not_enabled` 拒绝。
这是刻意的安全边界：receipt 的亲子关系、workflow 连续性和 hop 递增验证器完成
以前，不宣称自动双向接力可用。需要另一端继续时，由当前任务提交结果，主协调
会话再建立一条新的、独立签名的根任务。

## 4. 结果回执

任务的工程结果正常提交并签名后，可再提交一份回执：

```text
schema_version=1
type=result_receipt
workflow_id=ajm-example-workflow
task_id=ajm-example-001
task_commit=<40-or-64-hex-task-commit>
executor=windows
status=complete
result_commit=<40-or-64-hex-result-commit>
summary_path=airjet-simulation/reports/example.md
next_task_id=NONE
```

建议回执 commit 的直接 parent 是 `result_commit`。如果任务被阻塞且没有结果
变更，可以令 `result_commit=task_commit`。回执路径不可覆盖；一个 task ID
只能对应一份回执。当前 watcher 只把回执当作普通数据，不用它自动建立下一条
任务；receipt validator 和自动接力状态均为 `RESERVED_NOT_ENABLED`。

## 5. 执行边界

watcher 只在工作树干净、`main` 正确、远端固定、历史可 fast-forward、签名链
有效且远端 OID 在 runner 启动前仍未变化时唤醒 Codex。runner 从签名 commit
重新读取信封和 instruction，不把本地 pending 文件当作授权来源。Codex 明确
使用 `workspace-write` 与 `on-request`，不得继承 Windows 当前可能更宽的默认
sandbox。

包含 watcher、`.gitattributes` 或 `.gitmodules` 的更新永远需要人工复核和
手动部署。真实可见桌面唤醒在用户观察前只能记录为 `NOT_USER_OBSERVED`；进程
存在、SSH 返回成功或计划任务运行都不能代替用户可见性证据。
