# AirJet Mini 整机数字复原：当前状态

更新时间：2026-07-14
状态口径：**P0 公开证据冻结 v1 已通过；P1–P6 CAD/物理仿真阶段尚未通过。**

## 1. 已完成

- 目标锁定为 AirJet Mini Gen1；G2 作为第二阶段迁移对象，并记录其公开单点规格。
- 第一代 Mini 的外形、功耗、总热、净热、压力能力、系统噪声和重量已进入参数注册表。
- 官方性能图右轴已纠正为 50 cm 系统噪声，不是流量；曲线点有 PDF 哈希、像素坐标、转换公式和自动复算脚本。
- 专利尺寸已按 `P` 类候选范围记录；膜片长度、孔间隔 `s`、最低喷速和中央锚定均未伪装成 Mini 产品实测值。
- 已建立 Layout-L/M/S 的整机候选搜索框架与可执行 notebook；候选能放入外形只表示几何可行，不表示内部结构已确认。
- 已完成 P1–P6 操作规划、仿真注释规则、阶段 Gate、运行日志/Git 规则和 Windows 交接手册。
- Mac/Windows skills 有版本锁、规范化 SHA256、必需文件清单和跨平台安装脚本。
- 项目 Python 审计、Windows PowerShell 审计、skill 安装和曲线复算都有自动化入口。
- Windows 硬件、软件、研究 ZIP 和 Python 已实测，结果写入 `WINDOWS_ENVIRONMENT_REPORT.md`。
- Windows 已完成第三方 PLE 清理并保留纯净官方 Ansys Student 2026 R1；核心程序签名、旧 1055/环境变量清理经 Mac SSH 复核。Workbench/Fluent 基础 Student checkout 已由 Windows 可见会话报告，但完整 P1–P5 能力仍待 005；详见 `reports/AJM_WIN_ANSYS_STUDENT_CLEANUP_2026-07-14.md`。
- Gen1 两张官方产品透视图已分别做 homography、10,000 次像素误差 Monte Carlo 和跨视图差比较；四个画出 vent 只作为 `I` 类顶盖候选，不用于推断 cell 数。
- 官方剖面已标注：只锁总厚度和定性流路，不缩放内部层厚或数绿色波形。
- 核心专利已建立产品部件映射表，定位改为本地 PDF 页码 + FIG. + printed column/line；中央锚定仍是候选，不是量产事实。
- Layout 候选已由 34 个 family 组合去重为 32 个唯一几何；A0 下 23 个可装入，工作主/备选为 `M-3x4-7.0` 与 `M+S-3x5-6.0`，当前评分覆盖率仅 20%。
- P0 Gate 证据与限制已冻结在 `evidence/P0_EVIDENCE_FREEZE_RECORD.md`。
- P1 的四个工作布局已生成求解器无关配置表；`TB0-PLACEHOLDER` 厚度表严格闭合 2.8 mm，并显式保留 0.735 mm 未识别残差，未把占位层伪装成产品事实。
- P1 可执行 CAD 合同已生成：6 个交付/残差变体 + 3 个单因素派生变体、342 条参数映射、3 类喷孔解释、两套四开口 vent、每配置两套单侧排气分支、9 条内部几何 R0 构造规则，以及 feature/成对 interface/Named Selection/open-question 表；252 条 Gate 行仍全部 `NOT_RUN`。
- Windows 006 完整产品 CAD 任务已写好，但受 005 工具链报告硬门槛约束；当前没有正式 CAD 产物。
- 006 后的 007 独立复核已定义：先核验真实 005 副本、精确 006 commit 合同 bundle、9 个 variant 固定角色/机器检查/252 行 evidence 和完整目录 SHA256，再生成 worksheet；finalize 还会校验 243 个 hard Gate、9 个 STEP Gate 与 6 项原生文件可见抽查。当前没有 006 产物，所以 007 也未运行。

## 2. 尚未完成，不能声称完成

| 阶段 | 当前状态 | 缺失的实际产物 |
|---|---|---|
| P0 证据冻结 | **PASS v1** | 若得到新 D 类资料、实物/CT 或发现证据冲突，需建立 v2；当前内部未知量不会被伪装成已解决 |
| P1 整机 CAD | 输入合同完成，CAD 未开始（Student 工具链待 005） | 先验证参数化、Named Selections、Volume Extract 和 Workbench 传递；通过后按 006 建立完整装配/流体负体积并独立审核 |
| P2 执行片结构 | 未开始 | 材料栈候选、模态、谐响应、位移场、功耗闭合 |
| P3 单 cell 动态 CFD | 未开始 | 网格/时间步独立性、周期稳定、质量守恒、降阶传递关系 |
| P4 整机气动 | 未开始 | 全部 cell/孔板/歧管/出口模型、压力能力扫描、相位对比 |
| P5 整机 CHT | 未开始 | 扩散板/TIM/热源/自热、温度场和 5.25/4.25 W 热账户 |
| P6 标定与不确定性 | 未开始 | 训练/验证分离、灵敏度、候选布局后验、失败回退记录 |

仓库审计 PASS 只表示文件、表结构和证据不变量没有被破坏。P0 的独立 Gate 记录已经 PASS，但这**不等于 P1–P6 任何 CAD/物理 Gate PASS**。ZIP、Git 和 skills 能让另一台 Codex 读懂项目，但不能替代 CAD、网格、求解结果和人工工程判断。

## 3. 下一步执行顺序

1. 在 Windows 可见桌面执行 `windows-prompts/AJM_WIN_ANSYS_STUDENT_CAPABILITY_SMOKE_005.md`；不在 SSH 后台判定 GUI PASS。
2. 005 的 P1 CAD 工具链就绪度通过后，执行 `windows-prompts/AJM_WIN_P1_FULL_PRODUCT_CAD_BUILD_006.md`：同一母版生成 4 个整机配置、6 个交付/残差变体和主配置 3 个有独立 ID/Gate 的单因素派生变体。006 最多写 `PENDING_PEER_REVIEW`，不能由生成模型的同一会话自评 P1 PASS。
3. 已提交的 Ansys 30 天官方试用申请继续等待；只有 entitlement 实际激活后才执行 004，不让等待阻塞 Student 可完成的 P1 工作。
4. 先闭合 2.8 mm 厚度预算、四个候选顶盖 vent、单侧 spout 和全流路连通，再允许给 `S_image`/`S_geometry` 正式评分。
5. P1 Gate 通过后，才按 P2 → P3 → P4 → P5 → P6 顺序推进；不以高保真单 cell 替代整机主线。

## 4. 用户需要理解的边界

- “尽可能像产品”在无实物条件下意味着：外部直接数据锁定，内部未知保留候选，用多个公开系统指标筛选；不是把专利图直接宣称为量产 Mini 内部。
- `1750 Pa` 是公开压力能力，公开资料没有给出该压力对应流量；必须另做低背压流量/热输运算例和压力能力扫描。
- `21 dBA` 是产品装入系统后、50 cm、A 计权条件；没有安装声学和传播模型时，只能做趋势代理，不能把局部 CFD 压力脉动直接数值拟合为 21 dBA。
- 第一篇论文由用户撰写；仓库提供可复核的模型、方法、参数来源、运行记录和图表源数据，不代写结论。
