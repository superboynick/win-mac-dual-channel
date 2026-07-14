# AirJet 项目的 Skills 与 Git 同步方式

## 最佳架构

```text
GitHub private repository
  ├── AirJet 项目文件
  ├── 自建 skill 源码
  ├── skills 版本锁与 SHA256
  └── Mac/Windows 安装脚本
           │ git pull --ff-only
           ▼
Mac/Windows 工作副本
           │ install-skills 脚本
           ▼
~/.codex/skills 运行副本
```

Git 管理可审计源文件；`.codex` 保持为本机运行状态。不要把整个 `.codex` 放进 Git，因为其中可能包含登录状态、缓存、SQLite 状态和机器专属配置。

Mac 与 Windows 是平级写入端。任何一端都可以建立任务文件、提交成果并正常 push；GitHub `main` 是共享事实源，不是 Mac 向 Windows 单向下发命令的通道。具体任务可以临时指定执行端和独立复核端，完整规则见 `PEER_COLLABORATION_PROTOCOL.md`。

## 当前固定技能

| Skill | 类型 | 用途 | 版本来源 |
|---|---|---|---|
| `airjet-product-reconstruction` | 项目自建 | 证据等级、整机目标、阶段路由、审计和 Windows 操作 | 当前私有仓库 |
| `jupyter-notebook` | OpenAI 官方 | 布局枚举、曲线数字化、参数识别、结果分析 | `openai/skills@49f948f` |
| `pdf` | OpenAI 官方 | 官方数据表/专利的文字提取、页面渲染和报告检查 | `openai/skills@49f948f` |

锁文件：`codex-skills/skills-manifest.json`。

其中 `SKILL.md` 的 SHA256 按 UTF-8 文本、把 CRLF/CR 统一成 LF 后计算；因此 Git 在 Windows 与 macOS 的换行差异不会被误报成内容变化。`codex-skills/**` 也通过 `.gitattributes` 固定为 LF。

## Windows

```powershell
cd C:\Users\admin\win-mac-dual-channel
git status --short --branch
git fetch origin
git pull --ff-only
powershell -ExecutionPolicy Bypass -File .\install-skills.ps1
powershell -ExecutionPolicy Bypass -File .\audit-airjet-project.ps1
```

脚本同步项目 skill，检查两个官方 skill；官方 skill 缺失或版本不同时，从锁定的 OpenAI commit 下载；最后核对三个入口文件 SHA256，并确认清单声明的全部必需文件存在。

强制重新拉取官方 skill：

```powershell
.\install-skills.ps1 -RefreshOfficial
```

## Mac

```bash
cd /Users/zhangjianxiao/win-mac-dual-channel
sh ./install-skills.sh
```

Mac 脚本同步项目 skill，并核对当前已安装的两个官方 skill。官方 skill 更新应使用 `skill-installer`，然后有意识地更新锁文件。

## 跨机器 subagent 规则

`AGENTS.md` 和项目 `SKILL.md` 共同保存 subagent 规则，因此任一端提交并推送后，另一端通过 `git pull --ff-only` 和对应安装脚本即可加载同一规则。真正的长任务或多部分任务可使用 1–2 个边界明确的 subagent 分担独立研究、审计或测试；当前具体任务的负责人必须亲自读取 skill、保持该任务所有权、整合并验证结果，并在交接前结束所有 subagent。这种任务责任不构成 Mac/Windows 之间的长期层级。不得用 subagent 模拟空闲常驻，也不得绕过审批、stage gate、证据规则、Git 安全或可见 GUI 要求。

本机监听器的 PID、日志、pending event、缓存、凭据和绝对路径不进入 Git；Mac 与 Windows 只同步经审查的规则和可移植源码。

Mac 的手动循环 Git 检查与可见 Codex 唤醒脚本位于 `tools/airjet-git-watcher/`。源码已同步，但 2026-07-14 独立审计发现当前版本会自动快进工作树，且没有结构化 `target=mac` 任务信封也可能唤醒 Codex，因此目前是 `DISABLED_PENDING_HARDENING`，不得执行 `start`。完成任务信封、自动快进例外、状态目录边界和写权限收缩后，必须重新审计，并由用户明确授权才可运行；不得安装 LaunchAgent、cron 或 Login Item。

## 更新规则

1. 修改仓库中的 `codex-skills/airjet-product-reconstruction`。
2. 运行官方 skill 校验器和项目审计。
3. 更新 manifest 中项目 skill 的 SHA256。
4. 提交并推送。
5. 两台机器先检查状态并 `git pull --ff-only`，再运行安装脚本。
6. 新开 Codex 会话验证 skill 被发现。

Windows 上的可见会话从已登录桌面执行：

```powershell
.\launch-airjet-codex-visible.ps1
```

脚本会设置窗口标题、进入仓库并启动新 Codex；它不会从 SSH 服务会话伪造一个“已显示”的窗口。

## 为什么不直接同步 `.codex`

完整同步 `.codex` 容易混入系统 skill、缓存、凭据或机器差异；官方 skill 也会与项目历史纠缠。当前方案只把“应该一致的东西”纳入 Git，并对安装副本做哈希验证。
