# AirJet 项目 — 快速启动指南

## 回到 Windows 后需要做的事

### 1. 启动 Daemon（核心——不要跳过）
```powershell
# Windows PowerShell 窗口
cd C:\Users\admin\win-mac-dual-channel
git pull --ff-only
tools\airjet-daemon\windows\start.bat
```

### 2. 启动 Codex A（ANSYS 线）
```powershell
# 新开一个 Codex 窗口
git pull --ff-only
# 读取任务文件（如果有）
type %USERPROFILE%\.codex\airjet_task.md
```
说：`继续 ANSYS 任务：SpaceClaim CAD + Mechanical + Fluent 网格`

### 3. 启动 Codex B（OpenFOAM 线）
```powershell
# 再开一个 Codex 窗口
git pull --ff-only
# 安装 Docker Desktop（如果没装）
# 然后拉 OpenFOAM
docker pull opencfd/openfoam-default
```
说：`安装 Docker + OpenFOAM，准备单 cell CFD 仿真`

### 4. Daemon 自动做的事
- 每 10 秒检查 Git 新 commit
- 发现 MAC_TASK → 写入 `.codex\airjet_task.md`
- 发现耦合状态变化 → 写入 `.codex\coupling_signal.txt`
- 终端标题显示：🟢 正常 / 📨 有新任务

## 文件地图

| 你要找什么 | 在哪里 |
|---|---|
| 论文 | airjet-paper/main.tex |
| 复现指南 | airjet-simulation/AIRJET_SIMULATION_REPRODUCTION_GUIDE.md |
| 硬件测试计划 | airjet-simulation/HARDWARE_TEST_PLAN.md |
| 网格结果 | airjet-simulation/logs/evidence/c5_mesh/ |
| CFD 求解 | airjet-simulation/logs/evidence/c7_solve/ |
| 网格脚本 | save_mesh6.py |
| 求解脚本 | solve_cfd6.py |
| 双 Codex 协议 | airjet-simulation/coupling/COUPLING_PROTOCOL.md |
| Daemon | tools/airjet-daemon/ |
