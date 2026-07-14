# AirJet 双端 Git watcher 实现记录

> 历史状态说明：本文件记录最初的 runtime-disabled 实现边界。2026-07-14 后续的
> 手动常驻启用状态以 `AIRJET_DUAL_ENDPOINT_WATCHER_MANUAL_RUNTIME_2026-07-14.md`
> 为准；下方测试输出和禁用结论保留为当时记录，不应改写为新结果。

日期：2026-07-14
任务：让 Mac 与 Windows 在用户不持续值守时，通过 GitHub `main` 安全同步并按
签名任务唤醒各自 Codex。
当前结论：`IMPLEMENTED_AND_ISOLATED_TESTED / RUNTIME_DISABLED_PENDING_E2E`

## 1. 问题与取舍

旧流程依赖用户看到 Git 变化后手工通知另一端。旧 Windows 本地 watcher 还存在
四个根本问题：任意 commit 都可能唤醒、源码不在 Git、SSH session 0 不能证明
窗口可见、GitHub 非交互认证失效。因此不能直接设为开机启动。

本轮采用 GitHub `main` 作为唯一共享事实源，但不把 push 权限等同于执行授权。
两端各自使用独立的 Ed25519 commit-signing key；每条 incoming commit 都必须由
本地 Git 外 allowlist 验证，任务 tip 还必须由对端专用 key 再验证。

选择 SSH 443 是因为两端 VPN/网络对 GitHub SSH 22 不稳定，而 443 实测可以
non-interactive `ls-remote`。HTTPS/GCM 在 Windows SSH 会话中会尝试 wincredman，
不适合作为无人值守 transport。

## 2. 签名与信任根

专用 signing key 与 transport/login key 分离，降低权限耦合。私钥和 trust 均在
Git 外；仓库只保存验证代码和固定 trust SHA256，不保存私钥。

- Mac signing fingerprint：
  `SHA256:jdxP5xJrt8J7PKjeCrJmrEeoAH44u9NxBICo41HwMuc`
- Windows signing fingerprint：
  `SHA256:oI3/MIlKz1mgLV3+5n1coQxynaqQOzxqi0GHxreGEdc`

Mac trust root：
`~/Library/Application Support/AirJetGitWatcher/trust/`

Windows trust root：
`%LOCALAPPDATA%\AirJetGitWatcher\trust\`

验证强制指定 SSH format、fully trust、allowed signers、KRL 和绝对 ssh-keygen。
生产模式再校验 trust 文件固定 SHA256；symlink/reparse、错误 owner/权限、错误 hash
或 revoked signer 均 fail closed。

## 3. 任务协议

schema v2 使用 11 个 exact fields。任务信封必须是 incoming target tip，同一 range
只能修改一个执行端信封，instruction 必须与信封位于同一 signed commit。

首版刻意只允许：

```text
parent_task_id=NONE
hop=0
max_hops=0
```

原因是 receipt parent、workflow 连续性和 hop 递增验证器尚未实现。与其只有字段
没有约束，不如禁用 automatic reciprocal relay。Windows 或 Mac 完成任务后可以
正常提交结果，但下一次唤醒必须由主协调会话建立新的 signed root task。

## 4. 防护范围

- 固定 repo、branch、upstream、SSH 443 remote；拒 shallow。
- clean worktree；只允许 verified fast-forward；拒 ahead/diverged。
- incoming 最多 100 条、无 merge、逐 commit 验签。
- 任务只能在 tip 修改一次；对端 key 专门授权。
- envelope/instruction 只接受 100644 regular blob、固定大小、ASCII 安全路径、
  无 traversal/casefold/Windows device-name 问题。
- 清理 Git object/worktree/config 注入环境；禁 replace refs；Windows 拒危险有效
  Git config，允许标准 LFS filter。
- watcher、`.gitattributes`、`.gitmodules` 变更永远人工部署。
- runner 从 signed commit 重建 instruction，不信任 mutable prompt/pending 内容。
- atomic processed claim 防止同一 task 双启动；claim 后再次核对 HEAD、clean、
  remote 和签名链。
- test mode 永远不能启动真实 Codex；production manager/watcher/runner 三层 runtime
  gate，installer 也有注册 gate。

## 5. 无人值守执行方式

被授权任务使用 `codex exec`，固定 `workspace-write`、`approval=never`、
`reasoning_effort=high`。`never` 来自用户对整晚无人值守的明确授权；文件写范围仍
限定为仓库和专用 watcher report 目录。

watcher 在 runner 工作期间不继续同步；runner 退出后，watcher核对 pending 与
processed claim 的 terminal phase，一致时归档完成事件再恢复轮询。失败状态保留，
不自动重复执行可能已有副作用的任务。

Mac 将使用 GUI 用户 LaunchAgent；Windows 将使用当前登录用户的
InteractiveToken/Limited AtLogOn task。两者都不是无桌面的系统服务。

## 6. 已完成验证

Mac 本地临时 bare-Git 测试：

```text
CORE_CASES_PASS=80
EXPECTED_PASS_COUNT=80
OVERALL=PASS_CORE_RUNTIME_DISABLED
```

Windows PowerShell 5.1 临时 bare-Git 测试：

```text
WINDOWS_CORE_CASES_PASS=50
EXPECTED_PASS_COUNT=50
OVERALL=PASS_CORE_RUNTIME_DISABLED
```

Windows 测试在 `%TEMP%` 的候选副本执行；未修改正式 Windows repo、未安装代码、
未注册计划任务。Python 项目审计当前 PASS。

## 7. 仍未完成的 Gate

1. 把本实现作为 Mac-signed critical commit 推送。
2. Windows 手工 `pull --ff-only`，在 runtime locked 状态复跑 PowerShell 5.1 test
   和项目审计。
3. 手工部署两端候选代码，但不注册 startup。
4. 完成一次 Mac-signed Windows task 和一次 Windows-signed Mac task 的真实 GUI
   E2E；记录 session/process/report。用户未观察时只能写 `NOT_USER_OBSERVED`。
5. E2E 技术证据通过后，用独立 signed commit 解锁 runtime，再安装 LaunchAgent 与
   InteractiveToken AtLogOn task。
6. 验证两端 clean、`0 ahead / 0 behind`、startup loaded/running 和普通 commit 不
   唤醒。

以上 Gate 未完成前保持 `DISABLED_PENDING_END_TO_END`，不得为了“整晚运行”跳过。
