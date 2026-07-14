# Windows Codex 平级协作与本机任务说明

交接日期：2026-07-13
目标机器：`LAPTOP-LCCLM2HI`，用户 `admin`  
仓库：`C:\Users\admin\win-mac-dual-channel`

Windows Codex 与 Mac Codex 是平级协作者。Windows 可以直接建立/更新任务文件、commit 并正常 push；不需要等待 Mac Codex 批准。执行端与复核端按具体任务和软件能力临时分配，规则见 `PEER_COLLABORATION_PROTOCOL.md`。两端同样禁止 force-push 或覆盖对方未整合的提交。

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
15. `airjet-simulation/parameters/P1_CAD_CONTRACT_METHOD.md`
16. `airjet-simulation/geometry/contracts/README.md`
17. `airjet-simulation/windows-prompts/AJM_WIN_ANSYS_STUDENT_CAPABILITY_SMOKE_005.md`（当前下一轮入口）
18. `airjet-simulation/windows-prompts/AJM_WIN_P1_FULL_PRODUCT_CAD_BUILD_006.md`（005 通过后才执行）
19. `airjet-simulation/checklists/P1_CAD_INDEPENDENT_REVIEW_METHOD.md`（006 完成后由独立审查端执行）

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

`AJM-P0-v001` 公开证据冻结已通过；尚未进入 P1 CAD 定版。第三方 PLE 已清理，当前为纯净官方 Ansys Student 2026 R1 基线；核心签名和清理状态已复核，但完整 CAD/Mechanical/Fluent 能力尚未通过 005。用户另行提交了 30 天官方试用申请，但 entitlement 尚未确认激活。Windows Codex 应先：

1. 阅读 `WINDOWS_ENVIRONMENT_REPORT.md`、`reports/AJM_WIN_ANSYS_STUDENT_CLEANUP_2026-07-14.md` 和历史 `AJM_WIN_ANSYS_CAPABILITY_SMOKE_003_SUMMARY.md`；
2. 确认研究 ZIP 与 Mini PDF 哈希；不需要重做已经版本化的曲线、图像 homography、专利映射或 Layout 去重；
3. 将 Windows Codex 默认 reasoning effort 设为 `high`；复杂故障/关键 Gate 审核可临时升 `xhigh`；承担复杂证据协调或关键 Gate 复核的任一端建议使用 `xhigh`；
4. 当前先执行 `windows-prompts/AJM_WIN_ANSYS_STUDENT_CAPABILITY_SMOKE_005.md`；不等待 30 天试用审批；
5. 005 的 P1 CAD 工具链就绪度通过后，执行 006；用同一 27.5 x 41.5 x 2.8 mm 母版建立全部 9 个正式 variant。输入由两个 P1 生成器、9 条 internal R0 和 `geometry/contracts/` 锁定，不能由 Windows 临场猜测；006 必须保留真实 005 副本、固定角色 manifest、机器检查和 252 行 evidence；
6. 先完成 2.8 mm 厚度预算和完整入口-上下腔-孔板-冲击通道-歧管-spout 连通检查，再给任何布局正式图像/几何分；
7. 006 只能到 `PENDING_PEER_REVIEW`；由独立于生成会话的 peer 执行 007 preparation/finalize，6 项原生文件可见抽查必须在可用 Windows GUI 的会话完成，随后仍需单独审核提交才能记录 P1 Gate；不启动高保真单 cell 作为主线。

可见窗口启动使用仓库脚本：

```powershell
powershell -ExecutionPolicy Bypass -File .\launch-airjet-codex-visible.ps1
```

该脚本只允许在当前交互桌面会话启动；若从 SSH 运行会明确拒绝，防止产生用户看不见的后台 Codex。

## 签名 Git watcher（当前仍锁定）

双端无人值守同步实现位于 `tools/airjet-git-watcher/`。Windows 源码、测试和
installer 已纳入 Git，不再使用旧的 `C:\Users\admin\AirJetGitWatcher` 本地脚本。
协议与 schema 先读：

1. `tools/airjet-git-watcher/README.md`
2. `airjet-simulation/collaboration/README.md`
3. `tools/airjet-git-watcher/wake-policy.md`

当前 `RUNTIME_STATUS=DISABLED_PENDING_END_TO_END`。允许执行 status、隔离测试和
单次 no-wake 同步；禁止直接绕过 manager 调用 watcher/runner。Windows 隔离测试
固定要求 `WINDOWS_CORE_CASES_PASS=50` 与 `EXPECTED_PASS_COUNT=50`。

真实双端可见唤醒通过后，Windows installer 才允许把 watcher 注册为当前用户的
`InteractiveToken`、`Limited`、AtLogOn Scheduled Task。它不是服务，不在 session 0
启动 Codex；installer 不从 Git 导入 trust key，只接受本机预先 bootstrap 且固定
SHA256 正确的 trust 文件。任何窗口在用户肉眼确认前都只能标记
`NOT_USER_OBSERVED`。

当前下一轮入口仍是 `airjet-simulation/windows-prompts/AJM_WIN_ANSYS_STUDENT_CAPABILITY_SMOKE_005.md`。只有其 P1 CAD 必需字段通过后，才打开 006。若 30 天官方试用开通，再使用 004。SSH/Git 可以可靠同步这些文件；旧 001 和 003 保留作历史记录，不再作为当前入口。

## 安全规则

- 不把旧 `AIRJET_SIMULATION_PROJECT.md` 当主线；它已归档。
- 不从宣传图直接断言 cell 数。
- 不把专利范围写成产品实际精确值。
- 不自动进行参数优化或论文写作。
- 不提交许可证、密钥、大型 case/data/mesh。
- 修改前 `git status`；发现未知修改或分支分叉立即停止。Windows 与 Mac 都可正常 commit/push，但都不得 force-push、破坏性 reset 或静默覆盖另一端成果。
