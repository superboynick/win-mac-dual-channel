# AirJet Daemon — 双端常驻协作程序

## 功能
1. **防休眠** — 保持电脑不休眠（Mac: `caffeinate`, Win: `powercfg + SetThreadExecutionState`）
2. **Git 监控** — 每 10 秒轮询 origin/main，检测到新 commit 自动处理
3. **任务分发** — 读取 `MAC_TASK.env` / `WINDOWS_TASK.env` 自动写入 Codex prompt 文件
4. **状态共享** — 通过 `watcher-state.json` 共享双端状态

## 启动

### Mac
```bash
sh tools/airjet-daemon/mac/daemon.sh
```

### Windows
```powershell
powershell -NoProfile -ExecutionPolicy RemoteSigned -File tools\airjet-daemon\windows\daemon.ps1
```

## 工作原理
```
[任一 Codex 推送到 Git]
       ↓
[双端 daemon 检测到新 commit]
       ↓
[读取 TASK.env → 写入 .codex/airjet_prompt.txt]
       ↓
[Codex 下次对话自动读取 prompt]
```

## 文件结构
```
tools/airjet-daemon/
├── mac/daemon.sh          ← Mac 守护脚本
├── windows/daemon.ps1     ← Windows 守护脚本
├── watcher-state.json     ← 双端共享状态
└── README.md              ← 本文件
```

## 注意事项
- 双端 daemon 必须同时运行
- 需要 SSH key 已配置（git push/pull 免密）
- `airjet_prompt.txt` 由 Codex 自动读取
