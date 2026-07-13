# Windows Codex 提示：AJM-WIN-P1-READINESS-001

你正在 Windows 机器 `LAPTOP-LCCLM2HI` 上接手 AirJet Mini Gen1 整机数字复原项目。本轮只做 **P1 交接就绪与 CAD 就绪核验**，不要创建 CAD，不要修改、提交或推送仓库文件。允许的非仓库写入只有：更新用户级 Codex skills、必要时修正用户级 reasoning effort，以及写 Downloads 报告。

仓库：`C:\Users\admin\win-mac-dual-channel`

按顺序执行：

1. 运行 `git status --short --branch`、`git status --porcelain`、`git branch --show-current`、`git remote get-url origin`、`git rev-parse HEAD`、`git rev-parse --abbrev-ref --symbolic-full-name @{u}`、`git fetch origin`、`git rev-list --left-right --count HEAD...origin/main`。要求 branch=`main`、upstream=`origin/main`、origin=`https://github.com/superboynick/win-mac-dual-channel.git`、porcelain 为空、ahead/behind=`0/0`。任一不符时，先写 `P1_BLOCKED` 报告再停止后续核验；不要运行 skill 安装器，不自动合并、不覆盖。
2. 运行：

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install-skills.ps1
   powershell -ExecutionPolicy Bypass -File .\audit-airjet-project.ps1
   ```

3. 阅读：`AGENTS.md`、`airjet-simulation/PROJECT_STATUS.md`、`airjet-simulation/evidence/P0_EVIDENCE_FREEZE_RECORD.md`、`airjet-simulation/evidence/OFFICIAL_IMAGE_COORDINATE_METHOD.md`、`airjet-simulation/evidence/patent_product_component_map.csv`、`airjet-simulation/evidence/layout_candidate_scores.csv`、`airjet-simulation/parameters/full_product_parameter_registry.csv`、`airjet-simulation/manuals/01_FULL_PRODUCT_CAD.md`、`airjet-simulation/checklists/full_product_stage_gates.md`。
4. 确认 Windows 新会话默认 `model_reasoning_effort = "high"`；若缺失，只修改该设置并记录“新会话生效”。不要输出配置文件中的其他内容、密钥或敏感值。
5. 只读复查当前已安装的 CAD/CAE 软件、版本和许可线索，至少包括 ANSYS Workbench/SpaceClaim/Mechanical/Fluent、COMSOL、SolidWorks、FreeCAD、Salome、OpenFOAM、Python/Jupyter。不要安装软件。
6. 复核 C:、D: 空间与 RAM 是否相比 `WINDOWS_ENVIRONMENT_REPORT.md` 有变化。
7. 验证 `C:\Users\admin\Downloads\AirJet_simulation_bundle_2026-07-12_v2.zip` 的 SHA256 为 `96f65ca6e5c8b8d4bc2b4acdeeb78d9917cf3c5ec2c159055daf88fa3ea261a4`，以及解压后的 `official\AirJet_Mini_Data_Sheet.pdf` 为 `822fbb7e9735a5505734a291083fed7901c1fdfa01cb7de369679e4d41fd19bd`。若解压目录位置不同，只读搜索后记录实际路径；不要重复下载。
8. 将完整结果写到 `C:\Users\admin\Downloads\AIRJET_P1_READINESS_REPORT.txt`，并在窗口中输出简要结论。

报告必须包含：

- `ACTION_BOUNDARY=DO_NOT_CREATE_CAD`
- `MODEL_BOUNDARY=WORKING_CANDIDATES_NOT_PRODUCT_FACT`
- `P0_GATE_BOUNDARY=P0_EVIDENCE_ONLY_P1_P6_NOT_PASSED`
- `PRESSURE_BOUNDARY=1750_PA_CAPABILITY_FLOW_UNKNOWN`
- `HANDSHAKE_STATUS=P1_HANDOFF_READY`：仅当 Git 干净且 0/0、skill 安装 PASS、项目审计 PASS、P0 record 可读、research ZIP/PDF 哈希 PASS、reasoning effort 已是 `high`；否则写 `HANDSHAKE_STATUS=P1_BLOCKED` 并列出精确原因。
- `P1_CAD_STATUS=READY`：仅当检测到可用的参数化 CAD 路线及其许可；否则写 `P1_CAD_STATUS=BLOCKED`，并准确列出缺少的软件/许可证。`P1_HANDOFF_READY` 与 `P1_CAD_STATUS=BLOCKED` 可以同时成立。
- 当前 commit、ahead/behind、审计结果、软件/许可、RAM/磁盘、推荐的 P1 CAD 路线。
- 明确写出：P0 PASS 只是证据冻结；P1-P6 尚未通过。
- 明确写出：`M-3x4-7.0` 是工作主候选，`M+S-3x5-6.0` 是工作备选；二者都不是真实量产布局事实。
- 明确写出：1750 Pa 是压力能力，不是已知对应流量工作点。

完成报告后停止，等待下一条明确指令。不要开始建模，不要修改 Git 文件。
