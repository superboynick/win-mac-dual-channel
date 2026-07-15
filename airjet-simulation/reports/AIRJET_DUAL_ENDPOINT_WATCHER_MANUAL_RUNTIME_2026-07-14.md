# AirJet 双端 watcher 手动常驻启用记录

日期：2026-07-14
状态：`WINDOWS_MANUAL_RUNTIME_VERIFIED / MAC_CORE_80_PASS / MAC_DEPLOYMENT_PENDING / NO_AUTOSTART`

## 1. 本轮授权与边界

用户要求提高 Mac/Windows 协作效率，并继续保留此前“不要开机自启动，等用户说时
再启用”的约束。本轮把双端 runtime 源码切换为可由可见桌面显式启动的手动常驻
模式，不注册 LaunchAgent、Scheduled Task、cron、Login Item 或 shell profile。

自动化范围是：轮询 GitHub `main`、验证线性签名历史、fast-forward、识别对端签名
根任务、去重并在可见桌面请求启动 Codex。当前不支持 receipt 驱动的自动 reciprocal
relay，也不允许非零 hop；每次跨端唤醒仍需一个新的签名根任务。

## 2. 实现变更

- Mac manager/watcher/runner runtime：`ENABLED_AFTER_REVIEW`。
- Windows manager/common runtime：`ENABLED_AFTER_END_TO_END`。
- Windows manager 在清除环境变量和启动进程前显式拒绝 TestMode 的 `start/retry`，
  避免隔离测试误启动真实 watcher。
- Mac 连续模式不再在普通同步后退出；只有 `--once` 才结束。关键 watcher 自更新仍
  fail closed，需要人工审查、pull 和重新部署。
- 两端 installer 的登录启动能力没有在本轮调用。

## 3. Windows 验证结果

```text
WINDOWS_CORE_CASES_PASS=54
EXPECTED_PASS_COUNT=54
SIGNED_CHAIN=BEHAVIOR_TESTED
MAC_ONLY_TASK_TIP=BEHAVIOR_TESTED
RETRY_REBUILD=BEHAVIOR_TESTED
RUNTIME_TEST_MODE_GUARD=BEHAVIOR_TESTED
VISIBLE_WAKE=SKIPPED_BY_DESIGN
OVERALL=PASS_CORE_RUNTIME_ENABLED_MANUAL
```

项目 skill 安装与项目审计：

```text
airjet-product-reconstruction=PASS
jupyter-notebook=PASS
pdf=PASS
PROJECT_AUDIT=PASS
required_files=80
manuals=7
csv_files=27
```

首次手动部署暴露出 Git 将固定 Windows OpenSSH 路径误判为 `simple` variant，导致
SSH 443 的 `-p` 参数被拒绝。实现随后固定 `GIT_SSH_VARIANT=ssh`；进一步发现 Git
shell 会吞掉 Windows 反斜杠，因此固定无空格的正斜杠命令路径
`C:/Windows/System32/OpenSSH/ssh.exe`。两项分别增加第 51、52 项回归断言；真实
`ls-remote` 在相同 command/variant 下通过。

修复部署后，Windows manager 从可见桌面手动启动并经独立 status 复核：

```text
INSTALL_RESULT=PASS
AT_LOGON_REGISTERED=false
WATCHER_RUNNING=True
WATCHER_STATE=WATCHING
WATCHER_DETAIL=clean; remote main unchanged; no model invoked
PENDING_EVENT=False
AUTO_START=DISABLED
AIRJET_SCHEDULED_TASKS=0
AIRJET_WATCHER_PROCESSES=1
```

为使外层编排可靠，manager 的成功落点显式返回进程码 0，并增加第 53 项 status
返回码行为断言。随后按用户要求把双端默认轮询周期统一降为 10 秒，并增加第 54 项
Windows 默认周期断言。真实目标任务和可见 Codex wake 仍未执行，因此不改变下方
`WINDOWS_VISIBLE_WAKE=NOT_RUN`。

## 4. Mac 原生矩阵与待完成部署

Windows 上对三份 Mac shell 源码执行语法检查通过。Mac 80 项隔离矩阵不能用 Windows
Git Bash 代替原生 macOS 结果：Git Bash 运行在首个仓库 fixture 因平台差异失败，
没有把它写成 Mac 测试 PASS。

2026-07-14 在原生 macOS、当前任务准备工作树上重新运行矩阵，结果为：

```text
CORE_CASES_PASS=80
EXPECTED_PASS_COUNT=80
TARGET_ENVELOPE_GATE=BEHAVIOR_TESTED
RUNTIME_TEST_MODE_GUARD=BEHAVIOR_TESTED
STATE_ROOT_REPO_BOUNDARY=BEHAVIOR_TESTED
REPORT_ROOT_BOUNDARY=BEHAVIOR_TESTED
VISIBLE_WAKE_TEST=SKIPPED_BY_DESIGN
OVERALL=PASS_CORE_RUNTIME_ENABLED_MANUAL
```

对应命令为：

```sh
sh tools/airjet-git-watcher/tests/test-watch-airjet-git.sh
sh install-skills.sh
python3 codex-skills/airjet-product-reconstruction/scripts/audit_project.py .
```

Mac 真实部署和可见唤醒仍未执行；如需部署，应从可见 Terminal 手动启动且不调用
登录启动 installer：

```sh
sh tools/airjet-git-watcher/mac/manage-airjet-watcher.sh start --poll-seconds 10
```

## 5. Windows 手动部署

Windows 只允许调用不带 `-RegisterAtLogOn` 的 installer 来复制已审查源码，然后从
安装目录的 manager 显式启动。部署前还必须确认 Git clean、0 ahead/0 behind 和
Git 外 trust 哈希正确。登录启动项必须保持不存在。

## 6. 尚未宣称的结果

- `MAC_CORE_80=PASS_CORE_RUNTIME_ENABLED_MANUAL`
- `MAC_VISIBLE_WAKE=NOT_RUN`
- `WINDOWS_VISIBLE_WAKE=NOT_RUN`
- `AUTOMATIC_RECIPROCAL_RELAY=NOT_IMPLEMENTED`
- `LOGIN_STARTUP=NOT_AUTHORIZED`

## 7. Claude CLI 第二模型资源

Windows 已验证 Claude Code CLI `2.1.209` 与本机 Git 外配置。口头简称 `dsv4pro`
不能直接作为 CLI model ID；实际可用名称是 `deepseek-v4-pro`，快速层是
`deepseek-v4-flash`。Pro 无工具 smoke test 返回 PASS，并对本轮关键代码 diff 做了
只读复核，结论为无 blocker。双端可移植 wrapper 和使用边界见
`tools/claude-cli/README.md`；本机 token、gateway URL、settings、session 和 cache
均未写入 Git。Mac 仍需在本机配置后执行 readiness smoke test。

本轮只改变跨端协作工具，不改变 AirJet 工程模型、P0–P6 stage gate、CAD、CFD、
优化或论文状态。
