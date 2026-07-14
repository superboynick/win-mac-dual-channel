# AirJet 双端 watcher 手动常驻启用记录

日期：2026-07-14
状态：`WINDOWS_VALIDATED / MAC_DEPLOYMENT_PENDING / NO_AUTOSTART`

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
WINDOWS_CORE_CASES_PASS=51
EXPECTED_PASS_COUNT=51
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
SSH 443 的 `-p` 参数被拒绝。实现随后固定 `GIT_SSH_VARIANT=ssh`，并增加第 51 项
回归断言；真实 `ls-remote` 在同一 variant 下通过。

## 4. Mac 待完成验证

Windows 上对三份 Mac shell 源码执行语法检查通过。Mac 80 项隔离矩阵不能用 Windows
Git Bash 代替原生 macOS 结果：Git Bash 运行在首个仓库 fixture 因平台差异失败，
没有把它写成 Mac 测试 PASS。Mac 在 fast-forward 到本提交后必须原生运行：

```sh
sh tools/airjet-git-watcher/tests/test-watch-airjet-git.sh
sh install-skills.sh
python3 codex-skills/airjet-product-reconstruction/scripts/audit_project.py .
```

全部通过后，从可见 Terminal 手动启动，不调用 installer：

```sh
sh tools/airjet-git-watcher/mac/manage-airjet-watcher.sh start --poll-seconds 180
```

## 5. Windows 手动部署

Windows 只允许调用不带 `-RegisterAtLogOn` 的 installer 来复制已审查源码，然后从
安装目录的 manager 显式启动。部署前还必须确认 Git clean、0 ahead/0 behind 和
Git 外 trust 哈希正确。登录启动项必须保持不存在。

## 6. 尚未宣称的结果

- `MAC_CORE_80=NOT_RUN_ON_MAC_AFTER_ENABLE`
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
