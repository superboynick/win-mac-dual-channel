# AirJet Daemon v2 — 双端 Git 监控 + 任务分发

## 启动

### Mac
```bash
sh tools/airjet-daemon/mac/start.sh
```
- 在独立终端窗口运行，标题栏显示当前 commit
- 有新任务时：OS 通知 + 声音提示
- 关闭终端窗口即停止

### Windows
```
tools\airjet-daemon\windows\start.bat
```
- 在独立 PowerShell 窗口运行
- 关闭窗口即停止

## 状态显示
| 状态 | 终端标题 | 含义 |
|---|---|---|
| 🟢 AirJet | 正常运行 | 监控中，无新任务 |
| 📨 AirJet | 新任务到达 | 任务已写入 ~/.codex/airjet_task.md |

## 任务文件
有新任务时，daemon 将内容写入 `~/.codex/airjet_task.md`。
Codex 读取方式：
```
codex -f ~/.codex/airjet_task.md
```

## 工作原理
```
Windows Codex 推送 → Git → Mac daemon 检测 → OS 通知 → 写入 airjet_task.md
Mac Codex 推送     → Git → Win daemon 检测 → 写入 airjet_task.md
```

## 与旧 watcher 的区别
- v2 daemon 更轻量：纯 shell/PS，无依赖
- 独立终端窗口，可见可关
- OS 原生通知
- 不依赖 launchd/scheduled tasks
