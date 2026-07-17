# AirJet Daemon v3 — Git 监控 + 耦合信号 + 任务分发

## 功能
1. 🟢 Git 每 10s 轮询
2. 📨 检测到 TASK.env → 自动写入 ~/.codex/airjet_task.md
3. 📡 检测到耦合状态变化 → 写入 ~/.codex/coupling_signal.txt
4. 🔔 OS 通知 + 终端标题实时状态

## 启动
- Mac: `sh tools/airjet-daemon/mac/start.sh`
- Win: `tools\airjet-daemon\windows\start.bat`

## 耦合信号
当 coupling/COUPLING_STATUS.md 显示：
- membrane_params.json WRITTEN → OpenFOAM Codex 该干活了
- cell_results.json WRITTEN → ANSYS Codex 该验证了

## Codex 如何读取
```bash
cat ~/.codex/airjet_task.md      # 新任务
cat ~/.codex/coupling_signal.txt  # 耦合信号
```
