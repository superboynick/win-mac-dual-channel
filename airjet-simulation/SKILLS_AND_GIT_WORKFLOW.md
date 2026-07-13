# AirJet 项目的 Skills 与 Git 同步方式

## 最佳架构

```text
GitHub private repository
  ├── AirJet 项目文件
  ├── 自建 skill 源码
  ├── skills 版本锁与 SHA256
  └── Mac/Windows 安装脚本
           │ git pull
           ▼
Mac/Windows 工作副本
           │ install-skills 脚本
           ▼
~/.codex/skills 运行副本
```

Git 管理可审计源文件；`.codex` 保持为本机运行状态。不要把整个 `.codex` 放进 Git，因为其中可能包含登录状态、缓存、SQLite 状态和机器专属配置。

## 当前固定技能

| Skill | 类型 | 用途 | 版本来源 |
|---|---|---|---|
| `airjet-product-reconstruction` | 项目自建 | 证据等级、整机目标、阶段路由、审计和 Windows 操作 | 当前私有仓库 |
| `jupyter-notebook` | OpenAI 官方 | 布局枚举、曲线数字化、参数识别、结果分析 | `openai/skills@49f948f` |
| `pdf` | OpenAI 官方 | 官方数据表/专利的文字提取、页面渲染和报告检查 | `openai/skills@49f948f` |

锁文件：`codex-skills/skills-manifest.json`。

## Windows

```powershell
cd C:\Users\admin\win-mac-dual-channel
git pull
powershell -ExecutionPolicy Bypass -File .\install-skills.ps1
powershell -ExecutionPolicy Bypass -File .\audit-airjet-project.ps1
```

脚本同步项目 skill，检查两个官方 skill；官方 skill 缺失或版本不同时，从锁定的 OpenAI commit 下载；最后核对三个入口文件 SHA256。

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

## 更新规则

1. 修改仓库中的 `codex-skills/airjet-product-reconstruction`。
2. 运行官方 skill 校验器和项目审计。
3. 更新 manifest 中项目 skill 的 SHA256。
4. 提交并推送。
5. 两台机器 `git pull` 后运行安装脚本。
6. 新开 Codex 会话验证 skill 被发现。

Windows 上的可见会话从已登录桌面执行：

```powershell
.\launch-airjet-codex-visible.ps1
```

脚本会设置窗口标题、进入仓库并启动新 Codex；它不会从 SSH 服务会话伪造一个“已显示”的窗口。

## 为什么不直接同步 `.codex`

完整同步 `.codex` 容易混入系统 skill、缓存、凭据或机器差异；官方 skill 也会与项目历史纠缠。当前方案只把“应该一致的东西”纳入 Git，并对安装副本做哈希验证。
