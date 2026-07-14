# Mac / Windows Codex 平级协作协议

## 1. 身份与权限

- Mac Codex 与 Windows Codex 是平级协作者；两端都可以读取、创建、修改、提交和推送仓库内容。
- 用户是目标、优先级和重大取舍的最终决定者。任何一端都不代表用户向另一端建立长期上下级关系。
- “执行端”“复核端”“任务负责人”只描述某一个具体任务的临时角色，不表示机器或 Agent 的等级。
- 软件能力决定任务位置：例如需要可见 Ansys GUI 的工作通常在 Windows 执行；证据整理、脚本审计或独立复核可在任一满足条件的端执行。

## 2. 统一任务入口

GitHub `main` 是两端共享的任务与成果入口。仓库中的 prompt、手册、状态文件和提交记录属于可审计任务包，不是一端对另一端的命令。

任一端可以：

1. 根据用户最新明确指令建立或更新任务文件；
2. 在开始时记录当前 commit、任务范围、允许修改的文件和完成条件；
3. 完成后提交并推送结果；
4. 向用户报告 `GIT_READY=<full_commit>`，由另一端拉取继续。

同一具体任务在同一时间只设一个任务负责人，避免两端同时修改同一批文件。需要独立复核时，复核者不得是生成该证据包的同一会话；复核可以由另一台机器或另一个独立可见会话承担。

## 3. 双向 Git 写入规则

Mac 与 Windows 使用完全相同的流程：

```text
git status --short --branch
git fetch origin
git rev-list --left-right --count HEAD...origin/main
```

- `0 0`：可以开始工作。
- `0 N`：工作树干净时执行 `git pull --ff-only`，再开始工作。
- `N 0`：检查本地提交后可以正常 `git push origin main`。
- `N M` 且两者都非零：已经分叉，停止写入并先整合；不得擅自覆盖任一端。
- 有未知未提交修改：停止并确认所有权；不得清理或覆盖。

两端都禁止使用 `git push --force`、`git push --force-with-lease`、破坏性 `reset` 或以复制文件方式掩盖分叉。这里的“Windows 可以写 Git”指正常 commit/push，不是覆盖提交历史。

## 4. AirJet 项目复核规则

- 生成模型的一端最多把候选状态写成 `PENDING_PEER_REVIEW`，不能给自己的 P1 Gate 判 PASS。
- 独立复核端可以是 Mac，也可以是另一个满足软件和可见性要求的 Windows 会话。
- 原生 SpaceClaim/Workbench 文件的人工抽查必须在能够真实打开这些文件的可见 Windows 桌面完成；这是软件能力要求，不是 Windows 比 Mac 等级更高。
- Git 中的审查结论必须能追溯到生成 commit、复核 commit、外部文件 SHA256、审查人/会话和日期。

## 5. 冲突处理

1. 用户最新的明确指令优先。
2. 已推送且可追溯的工作不得被静默覆盖。
3. 两端结论不同时，把证据、假设和分歧写入 Git，由用户决定方向；不得靠最后一次推送自动决定工程事实。
4. 未通过 stage gate 的工作保持未通过；平级协作不降低证据、审计、许可或物理验证门槛。

## 6. 签名 watcher 的自动化边界

双端 watcher 的技术协议见 `collaboration/README.md`。两端分别使用独立的
Ed25519 commit-signing key；push 权限本身不构成任务授权。自动同步只接受
clean、线性、可 fast-forward 且 incoming 每条 commit 都通过本地 Git 外信任根
验证的历史。任务信封必须是 target tip，并由对端专用 key 再签名。

当前版本只允许 `parent_task_id=NONE, hop=0, max_hops=0` 的根任务。自动 reciprocal
relay、receipt 驱动接力和循环执行均未启用。一个 Codex 可以正常提交并推送成果，
但不能仅因为“任务完成”就自动改写对端信封；新的唤醒必须由主协调会话建立新的
签名根任务。这样可在 receipt 亲子验证器完成以前保持 fail-closed。

测试模式永远不能启动真实 Codex。生产运行在 Mac manager/watcher/runner 和
Windows manager/watcher/runner 三层同时锁定；只有双端隔离测试、真实可见唤醒
和用户观察通过后，才允许修改 runtime 状态并注册登录启动项。
