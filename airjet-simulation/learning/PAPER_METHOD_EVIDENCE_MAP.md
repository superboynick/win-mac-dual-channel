# 论文方法—证据映射

这不是论文正文，而是帮助你自己写作时从每个方法主张追溯到输入、脚本、验证指标、run 和
产物哈希。只有 `status=AVAILABLE_FOR_WRITING` 的行可作为对应措辞的直接依据。

## 1. 当前允许的总述

可以写：项目采用公开证据约束的多候选整机数字复原，先验证工具链，再按 P1--P6 Gate
生成并复核 CAD/结构/CFD/CHT 证据。

现在不能写：已经确定量产内部 MEMS 结构、已经复现整机性能、已经验证 1750 Pa 对应流量、
已经用 CFD 拟合 21 dBA，或 P1--P6 已通过。

## 2. 映射表

| paper_section | question_or_claim | stage | model_scale | evidence_class | inputs | numerical_method | engine/profile/script | verification | run_ids/artifacts | allowed_wording | limitations | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Methods / toolchain | ANSYS 自动化是否可确定执行 | 005 T0 | 工具小模型 | C | 固定 v261 路径与版本 | 官方 batch/gRPC 控制探针 | 四个 `ajm005-*-t0-v1` | API 版本、确定断言、正常退出、报告/原生文件 hash | 待运行 | “验证了所用软件接口的可控性” | 不能推断工程能力或产品结果 | PENDING_RUN |
| Methods / CAD readiness | 参数化流体几何是否可传递 | 005 T1 | 可删除流道 | C | 005 §3 尺寸 | 参数更新、Boolean/Volume Extract、STEP/Workbench transfer | 待批准 T1 profiles | 重开尺寸、单连通体、Named Selection cardinality | 待运行 | 仅在完整断言通过后写“CAD 工具链就绪” | 不等于 P1 整机 CAD | NOT_RUN |
| Methods / solver readiness | 结构与流动最小求解 | 005 T1 | 可删除小模型 | C | 005 §4--5 | 静力 FEA；稳态层流 CFD | 待批准 T1 profiles | 有限结果、结果导出、质量平衡、case/data 重开 | 待运行 | 仅报告实际通过和受限功能 | 不等于 AirJet 结构/气动结果 | NOT_RUN |
| Geometry method | 整机 CAD 候选生成 | P1 | 全产品 | D/P/I/C/U | P1 registry/contracts | 同一母版 9 variants | 006 profiles 待建 | 252 Gate rows + independent review | 无 | 尚不可写成完成结果 | 005 与 006/007 未完成 | NOT_RUN |

## 3. 写作前必须补齐

- 每项数值方法对应的控制方程、离散格式、网格/时间步独立性和收敛阈值；
- 每个图表的生成脚本、输入 run ID 和数据 SHA-256；
- 训练/校准与验证数据分离；
- 负结果、Student 限制和未识别内部结构；
- 从 005 到 P1--P6 的 Gate 记录，而不是只引用软件截图。

005 只能支持“方法工具链已经验证或存在限制”，不能成为 AirJet 产品性能结果。
