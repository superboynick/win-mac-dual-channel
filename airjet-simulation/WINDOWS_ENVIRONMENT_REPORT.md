# Windows 仿真环境实测与任务分配

采集日期：2026-07-13；Ansys 能力复测更新：2026-07-13
主机：`LAPTOP-LCCLM2HI`
采集方式：从 Mac 经已授权 SSH 运行只读 PowerShell/WMI、`Get-Command`、`nvidia-smi` 和文件哈希检查。

## 1. 实测硬件

| 项目 | 实测值 | 对 AirJet 项目的含义 |
|---|---:|---|
| OS | Windows 11，build 26200 | 可以承载主流 Windows CAD/CAE 软件；具体兼容性仍须按选定求解器版本核对 |
| CPU | Intel Core Ultra 9 275HX，24 core / 24 logical processor | 适合 CAD、网格、结构模型及中小型并行 CFD；最终速度还受求解器许可证核数限制 |
| RAM | 31.43 GiB 总量 | 仅够 P0/P1/P2 与小型 P3 调试；不满足规划中的 P4/P5 整机高保真预算 |
| 当时空闲 RAM | 1.26 GiB | 采集时内存压力很高；开始网格/求解前必须关闭占用程序并重新记录空闲量 |
| GPU | NVIDIA GeForce RTX 5070 Ti Laptop GPU，12227 MiB，driver 592.01 | 适合 CAD 显示和支持 GPU 的局部工作；Fluent/Mechanical 的主要容量判据仍是 RAM、CPU 和许可证，不应以显卡型号代替算力评估 |
| 系统盘 C: | 400.0 GiB，总空闲 29.7 GiB | 空间偏紧，不建议存放高频瞬态 case/data |
| 数据盘 D: | 551.5 GiB，总空闲 62.5 GiB | 可作短期算例盘，但 P4/P5 前仍应准备更大的高速 SSD/外部结果存储 |

Windows WMI 的 `AdapterRAM` 对高显存显卡会错误报告 4 GiB，因此本表采用 `nvidia-smi` 的 12227 MiB，不采用 WMI 数值。

## 2. 实测软件

| 工具 | 当前状态 | 结论 |
|---|---|---|
| Git | `2.54.0.windows.1` | 可用 |
| Codex CLI | `0.144.1` | 可用；需从交互桌面启动才能让用户看见窗口 |
| Python | `3.12.10` | `python` 与直接解释器路径均已验证可运行 |
| Jupyter 命令 | 未找到 | 不阻塞标准库 notebook 构建/审计；需要交互执行 `.ipynb` 时再安装 |
| 官方 Ansys Student 2026 R1 | 纯净基线 PASS；完整能力待 005 | 第三方 PLE 已移除；Workbench/Fluent 基础 Student checkout 由 Windows 可见会话报告，核心 EXE 签名与旧 1055/环境变量清理由 Mac SSH 复核；SpaceClaim/Mechanical/Fluent 工程功能与限制仍须 005 |
| COMSOL | 未找到 | 当前不能用 COMSOL 替代结构/FSI 求解 |
| Siemens/Dassault 安装目录 | 未找到 | 尚未确认有可用的完整产品 CAD 工具 |

早期“未找到”仅表示当时标准命令和标准安装目录未发现。后续可见桌面烟雾测试确认 Ansys 2026 R1 已安装，但“安装存在”仍不等于 CAD/求解能力可用。正式开工前必须以最小几何、最小结构求解、Fluent 单核/八核启动和最小流动求解重新验收。

## 3. 分阶段适用性结论

| 阶段 | 这台 Windows 当前是否适合 | 条件/限制 |
|---|---|---|
| P0 证据冻结、参数台账、notebook | 是 | 当前即可做；notebook 构建脚本只需 Python 标准库 |
| P1 整机 CAD | 硬件适合，Student CAD 待 005 | 验证 SpaceClaim 参数化、Named Selections、Volume Extract、原生传递；STEP 失败只形成交接限制 |
| P2 压电结构/谐响应 | 硬件可做候选模型，Student 能力待 005 | 验证 Mechanical 最小求解、压电/耦合场入口和位移表导出 |
| P3 单 cell 1–5M 瞬态 CFD | 仅适合小网格调试 | 32 GiB 位于预算下缘且当时仅余 1.26 GiB；正式校准建议至少 64 GiB |
| P4a 整机降阶 5–20M | 不适合最终生产算例 | 规划预算 64–128 GiB；可在本机做粗网格流程验证 |
| P4b 整机高保真 20–80M+ | 不适合 | 需要 128–256 GiB 或 HPC |
| P5 整机 CHT 10–40M | 不适合最终算例 | 建议 128 GiB 起，并预留大量高速存储 |

结论：**应把 Windows 作为 CAD/CAE 主工作机，但不能因为 GPU 更强就直接把它当成完整整机求解平台。** Mac 继续承担证据整理、Git、参数表、脚本和轻量后处理；Windows 承担 CAD、网格与求解器操作。P4/P5 最终算例需要升级 RAM/存储或迁移到更大内存工作站/HPC。

## 4. 已验证的交接资产

- 研究资料 ZIP：`C:\Users\admin\Downloads\AirJet_simulation_bundle_2026-07-12_v2.zip`
- SHA256：`96f65ca6e5c8b8d4bc2b4acdeeb78d9917cf3c5ec2c159055daf88fa3ea261a4`
- 解压目录存在；列表包含官方产品卡、教程、专利和基础 CFD 文献。`.DS_Store` 与 `__MACOSX` 是 macOS ZIP 元数据，不作为研究文件计数。
- 项目仓库：`C:\Users\admin\win-mac-dual-channel`
- Python 解释器：`C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe`

## 5. 开始仿真前的机器门槛

1. 运行 `windows-prompts/AJM_WIN_ANSYS_STUDENT_CAPABILITY_SMOKE_005.md`，记录 Student 的 CAD/Mechanical/Fluent 实际能力、可用并行核数和观察到的规模限制；P1 CAD 工具链就绪度未通过时不得开始正式建模，005 本身不通过 P1 整机 Gate。
2. 30 天官方试用 entitlement 若后续开通，再按 004 验证扩展能力，不覆盖当前纯净 Student 基线记录。
3. 关闭高内存占用程序，确认 P3 开始前至少有约 24 GiB 空闲；若达不到，不运行正式动态网格算例。
4. P4 前将 RAM 提升到至少 64 GiB，首选 128 GiB；P4b/P5 仍应准备 128–256 GiB/HPC。
5. 为 case/data/mesh 准备大容量高速盘，并按 `manuals/07_RUN_LOG_AND_GIT.md` 只把哈希和摘要提交 Git。
6. 任何 GUI 菜单操作必须在实际安装版本上验证后，才可从“规划版”升级为“操作版”。

安装日志中的 `python_site_syscplg` 与 `cuDSS` 解压警告目前不阻塞基础 Workbench/Fluent，但 System Coupling 和相关 GPU 稀疏求解保持 `UNVERIFIED/WARNING`；实际需要前必须用官方安装器修复并重新验证。

## 6. 复核命令

```powershell
Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors
Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize,FreePhysicalMemory
& "$env:WINDIR\System32\nvidia-smi.exe" --query-gpu=name,memory.total,driver_version --format=csv,noheader
Get-Volume | Where-Object DriveLetter | Select-Object DriveLetter,Size,SizeRemaining
Get-Command git,codex,python,jupyter,fluent,runwb2 -ErrorAction SilentlyContinue
```

每次正式算例的实际峰值内存、CPU 时间、网格数和软件版本仍须单独写入运行日志；本报告只是交接时的机器快照。
