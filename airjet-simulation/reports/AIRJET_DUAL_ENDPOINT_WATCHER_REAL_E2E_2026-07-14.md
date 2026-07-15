# AirJet 双端 watcher 部分 E2E：到 runner 后失败

日期：2026-07-14（America/Los_Angeles；Windows 证据时间为 UTC）

## 1. Mac→Windows 签名任务

- Mac-signed task commit：`afd17c577c12b784c8575adeeff6d4d2cf4ae189`
- Task ID：`ajm-p1-p3-48h-sprint-20260715-001`
- Windows watcher 由用户在可见 PowerShell 手动启动；PID `42536`，无开机启动项。
- watcher 成功发现远端变化、验证线性签名链和 Mac-only task-tip signer、fast-forward
  到 task commit、创建 event/pending/processed claim，并请求 runner。
- Windows repo 在失败后仍为 clean，`HEAD=origin/main=afd17c5...`，ahead/behind `0/0`。

因此，Mac→Windows 的 Git 获取、任务验签、任务分类、去重 claim 和 runner 请求已有
真实运行观察；本仓库保存人工核验摘要，Git 外状态原件未纳入版本控制。这不是隔离
fixture，也还不是 watcher→Codex 成功闭环。

## 2. 首次 Codex 启动失败

Git 外状态准确记录为：

```text
phase=CODEX_FAILED
old_commit=1a9696c3930a42cd8a30aafe7093b8acafd6dd59
new_commit=afd17c577c12b784c8575adeeff6d4d2cf4ae189
task_id=ajm-p1-p3-48h-sprint-20260715-001
report=NOT_CREATED
```

状态文件位于 `%LOCALAPPDATA%\AirJetGitWatcher\`；pending 与 processed claim 的
`created_at/updated_at` 为 `2026-07-15T03:04:55Z`。它们属于 Git 外机器证据，不提交
原文件；本报告只保存已核验字段。runner 启动请求不等于 Codex 工程执行成功。

Codex readiness 独立检查：

```text
codex-cli=0.144.4
login=Logged in using ChatGPT
OPENAI_API_KEY_PRESENT=False
short_read_only_prompt=PASS
```

失败不属于 Git 签名、Codex 登录或 AirJet 工程。runner 原实现把包含完整 signed
instruction 的 `$prompt` 作为 `codex.cmd` 最后一个命令行参数。Windows npm `.cmd`
shim 经过 `cmd.exe`，长参数受到较短的命令行限制。12,000 字符、仅执行
`codex --version` 的无模型对照探针本次返回 exit 1 和“输入行太长”；相同 CLI、登录
和环境下的短 read-only prompt 返回 `WATCHER_CODEX_SHORT_SMOKE_PASS`、exit 0。

任务没有进入模型执行，没有生成 Codex final report，也没有修改 AirJet 工程文件。
processed ledger 按设计阻止同一 task ID 自动重放。

## 3. 修复合同

修复候选同时覆盖两个 PowerShell 5.1 边界：`git show` 的 native stdout 捕获期间临时
使用 UTF-8 并恢复原 console encoding；完整 prompt 再通过无 BOM UTF-8 stdin 交给
`codex exec ... -`，命令行不包含 `$prompt`。Windows 矩阵新增中文 blob 捕获和
fake `.cmd`/native child 行为测试，验证长中文 stdin、无 BOM、terminal dash、prompt
不在 argv、非零退出码传播，以及正常/异常路径的工作目录、global/console encoding
恢复；新预期计数为 72。

提交前把五个 candidate runtime 文件和测试脚本复制到 Windows Downloads 隔离目录，
未覆盖正式 repo/runtime。Windows PowerShell 5.1 完整矩阵结果为：

```text
WINDOWS_CORE_CASES_PASS=72
EXPECTED_PASS_COUNT=72
OVERALL=PASS_CORE_RUNTIME_ENABLED_MANUAL
VISIBLE_WAKE=SKIPPED_BY_DESIGN
```

其中 `git_utf8_blob_exact`、`transport_stdin_utf8_exact`、
`transport_prompt_not_argv`、`transport_exit_propagation`、编码和目录恢复断言均 PASS。

修复路径另做了真实 CLI 对照：把 12,000 字符合成 prompt 通过相同 PowerShell 5.1
`$OutputEncoding=UTF8(no BOM)` 管道交给 `codex exec ... -`，read-only、low-effort
运行返回 `WATCHER_CODEX_LONG_STDIN_PASS` 和 exit 0。它证明该 12,000 字符合成 prompt
能够越过 `.cmd` argv 限制；它仍只是绕开 watcher 的传输 smoke，不是 AirJet 工程执行。

当前证据边界：

```text
REAL_PARTIAL_E2E=MAC_TO_WINDOWS_PASS_THROUGH_RUNNER_REQUEST_MODEL_NOT_ENTERED
ISOLATED_BEHAVIOR_MATRIX=PASS_72_OF_72_FAKE_CHILD_NO_REAL_CODEX
DIRECT_CLI_TRANSPORT_SMOKE=PASS_REAL_CODEX_BUT_BYPASSES_WATCHER_AND_SIGNED_TASK
FIX_DEPLOYMENT=PENDING
SECOND_REAL_MAC_TO_WINDOWS_E2E=NOT_RUN
REAL_WINDOWS_TO_MAC_WAKE=NOT_RUN
```

第二次 Mac→Windows 闭环至少要求：新 task ID、更新后 runner 读取 signed instruction、
真实 Codex 生成 final report 且 exit 0、processed/pending 进入一致终态、watcher 恢复
轮询。用户未亲眼确认窗口时仍保持 `NOT_USER_OBSERVED`；该方向成功也不等于
Windows→Mac 的真实 watcher wake 已经通过。

本文件只记录传输层 E2E 与修复。它不改变 P0–P6 状态，不把 watcher runner 请求写成
用户肉眼确认的 Codex 窗口，不把 short smoke 写成 AirJet 工程执行。修复提交属于
watcher critical update，必须手工 fast-forward、测试和部署；旧 task ID 不可复用，
后续需由新的 Mac-signed root task 进行第二次真实 E2E。
