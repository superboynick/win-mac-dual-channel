# Windows Codex 接手说明

交接日期：2026-07-13
目标机器：`LAPTOP-LCCLM2HI`，用户 `admin`  
仓库：`C:\Users\admin\win-mac-dual-channel`

## 当前目标

完整复原第一代 AirJet Mini 产品，不是单喷嘴、单 cell 或参数优化。单 cell 仅作为结构和动态 CFD 校准子模型。设计改进等整机复原完成后再开始。

## Windows Codex 启动后先读

1. `AGENTS.md`
2. `airjet-simulation/README.md`
3. `airjet-simulation/AIRJET_MINI_FULL_PRODUCT_MASTER_PLAN.md`
4. `airjet-simulation/PROJECT_STATUS.md`
5. `airjet-simulation/WINDOWS_ENVIRONMENT_REPORT.md`
6. `airjet-simulation/DECISION_AND_REASONING_ARCHIVE.md`
7. `airjet-simulation/evidence/SOURCE_PROVENANCE.md`
8. `airjet-simulation/evidence/P0_EVIDENCE_FREEZE_RECORD.md`
9. `airjet-simulation/evidence/OFFICIAL_IMAGE_COORDINATE_METHOD.md`
10. `airjet-simulation/evidence/patent_product_component_map.csv`
11. `airjet-simulation/evidence/layout_candidate_scores.csv`
12. `airjet-simulation/parameters/full_product_parameter_registry.csv`
13. `airjet-simulation/checklists/full_product_stage_gates.md`
14. `airjet-simulation/manuals/01_FULL_PRODUCT_CAD.md`
15. `airjet-simulation/windows-prompts/AJM_WIN_P1_READINESS_001.md`

先安装并核对固定 skills：

```powershell
cd C:\Users\admin\win-mac-dual-channel
powershell -ExecutionPolicy Bypass -File .\install-skills.ps1
powershell -ExecutionPolicy Bypass -File .\audit-airjet-project.ps1
```

只有两条命令均返回 `PASS` 后，才继续工作。审计通过表示交接文件与关键证据不变量一致；P0 Gate 已有单独 PASS 记录，但 P1–P6 尚未通过。

## 研究资料

Windows Downloads 应有：

`C:\Users\admin\Downloads\AirJet_simulation_bundle_2026-07-12_v2.zip`

Expected SHA256:

`96f65ca6e5c8b8d4bc2b4acdeeb78d9917cf3c5ec2c159055daf88fa3ea261a4`

解压后将得到 `AirJet_research`，包含产品数据表、Hot Chips 教程、专利和基础 CFD 论文。PDF 不提交 Git。

解压后的 `official\AirJet_Mini_Data_Sheet.pdf` 还应为：

`822fbb7e9735a5505734a291083fed7901c1fdfa01cb7de369679e4d41fd19bd`

完整逐文件哈希在 `AirJet_research\metadata\SHA256SUMS`；先验证 ZIP，再用该表定位任何单文件损坏或版本差异。

## 当前工作阶段

`AJM-P0-v001` 公开证据冻结已通过；尚未进入 P1 CAD 定版。Windows Codex 应先：

1. 阅读 `WINDOWS_ENVIRONMENT_REPORT.md`；硬件已实测，但仍须记录实际安装的 CAD/CAE 软件、版本、许可证和求解模块；
2. 确认研究 ZIP 与 Mini PDF 哈希；不需要重做已经版本化的曲线、图像 homography、专利映射或 Layout 去重；
3. 将 Windows Codex 默认 reasoning effort 设为 `high`；复杂故障/关键 Gate 审核可临时升 `xhigh`；Mac 证据协调端保持 `xhigh`；
4. 选择 P1 CAD 路线后，用同一 27.5 x 41.5 x 2.8 mm 外壳建立 `M-3x4-7.0` 工作主候选、`M+S-3x5-6.0` 备选和两个 sentinel；
5. 先完成 2.8 mm 厚度预算和完整入口-上下腔-孔板-冲击通道-歧管-spout 连通检查，再给任何布局正式图像/几何分；
6. 不启动高保真单 cell 作为主线；只有 P1 Gate 通过后才进入 P2/P3。

可见窗口启动使用仓库脚本：

```powershell
powershell -ExecutionPolicy Bypass -File .\launch-airjet-codex-visible.ps1
```

该脚本只允许在当前交互桌面会话启动；若从 SSH 运行会明确拒绝，防止产生用户看不见的后台 Codex。

下一轮可直接粘贴的只读 P1 就绪提示保存在 `airjet-simulation/windows-prompts/AJM_WIN_P1_READINESS_001.md`。SSH/Git 可以可靠同步该文件；QQ 当前不是项目的自动化传输依赖。

## 安全规则

- 不把旧 `AIRJET_SIMULATION_PROJECT.md` 当主线；它已归档。
- 不从宣传图直接断言 cell 数。
- 不把专利范围写成产品实际精确值。
- 不自动进行参数优化或论文写作。
- 不提交许可证、密钥、大型 case/data/mesh。
- 修改前 `git status`；发现未知修改或分支分叉立即停止。
