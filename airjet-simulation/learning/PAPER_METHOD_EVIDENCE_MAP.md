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
| Methods / toolchain | ANSYS 自动化是否可确定执行 | 005 T0 | 工具小模型 | C | 固定 v261 路径与版本 | 官方 batch/gRPC 控制探针 | 四个 `ajm005-*-t0-v1` | API 版本、确定断言、正常退出、报告/原生文件 hash | 首轮 `AJM005_T0_SUITE_20260714T174206637091Z_61fb4628` 保留 FAIL；签名重试 `AJM005_T0_SUITE_20260714T175525010049Z_2b301826` 为 4/4 PASS | “在签名 commit 6265043 上验证了 SpaceClaim、Workbench、Mechanical 与 Fluent 官方接口的确定性可控性” | T0 本身不证明 005 工程能力；T1 SpaceClaim partial CAD 通过但 Workbench transfer set 仍失败；P1–P6 未运行/未通过；可见性未由用户观察 | AVAILABLE_FOR_WRITING |
| Methods / CAD readiness | 可删除流道的几何和 solver-side boundary semantics 是否能按固定合同建立 | 005 T1 partial | 可删除流道 | C | 005 §3 尺寸、hash-bound STEP 与 semantic sidecar | 两次脚本重建、negative-volume union、原生/STEP 重开、solver-side topology reconstruction | `ajm005-spaceclaim-cad-t1-v1` + `ajm005-workbench-semantic-reconstruction-t1-v1` | report/STEP/sidecar/manifest 身份；1 body/13 faces；唯一 1/1/11；互斥/全覆盖；4 项 negative controls；创建前后 cardinality；1063/513 粗网格；project hash | 前十四次保留 API、union、native attach、路径与跨-kernel area 失败；第十五次 `...221eac96` / commit `7a7f8e0...` 为 semantic diagnostic PASS；第十六次 `...51a1f815` / commit `41fa4a6...` 证明 145-character native path 仍 attach FAIL；第十七次 `...528b9791` / commit `3336c75...` 证明 writable-staging intervention 仍在 Model.Refresh attach FAIL；第十八次 connected `...ad740c2f` / commit `f15aae3...` 只到 empty cell/Edit/RunScript/Exit 返回，因 build report 缺失而在 transfer 前 fail closed；第十九次 `...6e14c202` / commit `0b32f5d...` 的 literal-path import 前 sentinel 在同-run 三个时点仍 absent，关闭 child env 指错输出位置的充分解释；第二十次 `...65a14fe2` / commit `abb1d9a...` 在 batch Edit 返回后由 SendCommand 直接空引用，分类 `CHECKPOINT_NOT_REACHED`，本轮 RunScript 未调用；第二十一次 `...13dedbfe` / commit `fe84454...` 在受审 outer journal 中只把 `Interactive=False` 改为 literal True，得到相同外部 failure signature，关闭“该单参数改动足以修复”的窄命题；per-run absolute path 和注入后的 child/command bytes 会随 case 变化 | 可写“在签名的可删除小模型上，验证了 hash-bound STEP+semantic sidecar 的 solver-side deterministic reconstruction diagnostic：唯一重建 1/1/11 边界，负向检查、粗网格与工程保存通过”；还可写“短路径和本轮可写 working copy 均不足以修复当前 native attach route”；connected 只能写“SendCommand 在 Interactive False/True 两轮均未到 post-call checkpoint，因此 True 单参数不足；两轮 file RunScript 与 transfer 均未到达” | fixture calibration；不是 AirJet 产品拓扑；不是 STEP/native semantic transfer；不能把相同外部错误文本写成内部根因相同，不能由 recorded journal 的 True 默认写法声称用户可见 desktop；不能把 outer journal 单参数误称整组输入 byte-identical；不能全局排除 session/权限为多因素之一；不能把 `CHECKPOINT_NOT_REACHED` 写成两通道都失败，也不能据两轮评价 inline Python 内容或 `.py` loader；`.py` 是官方支持格式，不能写成非法；native Named Selection transfer 和 native parameterization 未证明；没有产品结构/CFD/CHT 求解；P1–P6 未通过 | AVAILABLE_FOR_WRITING |
| Methods / diagnostic instrumentation | file-only RunScript 诊断能否无歧义地区分 call、entry timing 与 build state | 005 T1 run #22 | 可删除 connected fixture | D | run #20/#21 reach、fixed 34-byte entry sentinel、literal path child | direct RunScript-only；normal/failure checkpoint；freeze/capture 正交状态机 | `ajm005-workbench-connected-spaceclaim-t1-v1`；outer journal SHA `160b0b45...` + runner SHA `a6a7a2b1...` | exact size/SHA；outcome/reach/checkpoint/first-observed/delayed/lost/build-state 交叉约束；producer/consumer 20/19 manifest 项逐文件复算 | suite `AJM005_T1_CONNECTED_SC_SUITE_20260715T021529059815Z_aa1180f6`；SC `a5c-eedabacc1fc6-f70b77c399ca`；WB `a5c-eedabacc1fc6-027f5de8b724`；summary/raw ZIP SHA 分别由 evidence pointer 锁定 | 可写“direct RunScript 调用返回，但本轮四个检查点均未观测到 fixed child entry 或 build report；精确分类为 `RUNSCRIPT_RETURNED_ENTRY_ABSENT`，当前 route 因此被 deferred” | 不能写 child build 已执行后失败、`.py` 不受支持、connected transfer 已失败/通过、share/Refresh/Mechanical/mesh/project 已执行、GUI 可见或 P1 已通过；freeze/capture 非原子；suite 结束瞬间没有即时外层 process observation；同 host/session runtime positive control `NOT_RUN` | AVAILABLE_FOR_WRITING |
| Methods / full-product topology observation | 完整 12-cell/972-hole 候选的两区接口能否经当前 STEP handoff 保留 | 006 V02 preliminary observer | 全产品 preliminary CAD | C/I | hash-bound V02 STEP、冻结 predecessor manifest、972 点 XY 合同 | STEP→Workbench Geometry→Mechanical GeoData inventory；name/z 角色绑定；bbox/plane/edge/XY-Z topology classifier | `ajm006-spaceclaim-v02-preliminary-v1` + `ajm006-workbench-v02-topology-observer-v1`；commit `9699df5...` | predecessor immutable；2 bodies/1078 unique face IDs；downstream 972/972 XY；upstream 0/972；shared/pair/cross-body duplicate=0；project/report/inventory hash | producer `AJM006-V02-PRELIMINARY-13950bddaec8`；observer `AJM006-V02-PRELIMINARY-2fb76257a827`；evidence `AJM006_V02_TOPOLOGY_OBSERVER_20260715T122907417508Z_2fb76257a827` | 可写“对完整 12-cell/972-hole 候选模型进行了 hash-bound STEP→Workbench topology observation；下游 972 个孔印记保留而上游对应界面丢失，因此拒绝当前两区传递路线” | preliminary 候选不是已识别的量产内部结构；observer PASS 不是 P1 PASS；无 mesh，不能写 conformal mesh、shared nodes 或 mesh failure；结论只适用于当前 V02 STEP 两区 handoff，不能推广为 STEP 普遍失效 | AVAILABLE_FOR_WRITING |
| Methods / topology route candidate | Parasolid x_t 是否比当前 STEP 保留完整两区接口 | 006 V02 diagnostic | 全产品 preliminary CAD | C/I | 同一冻结 V02 native、STEP archive、x_t solver candidate | native staging→x_t export/reopen→Mechanical GeoData observer；逐角色 envelope/face count 与逐对界面几何 | `ajm006-spaceclaim-v02-parasolid-converter-v1` + `ajm006-workbench-v02-parasolid-topology-observer-v1` | predecessor tree/manifest immutable；x_t reopen；solver body face-count/bbox/volume；972 XY/shared/coincident classification；manifest job/phase | Mac 静态包和 guards 已通过；Windows run/job/artifacts 尚无 | 目前只能写“已建立并静态审计 Parasolid 对照实验方法，等待真实运行” | 没有 Windows/ANSYS terminal evidence；不得写 x_t 成功或失败、mesh、P1 或产品真实拓扑 | NOT_RUN |
| Methods / solver readiness | 结构与流动最小求解 | 005 T1 | 可删除小模型 | C | 005 §4--5 | 静力 FEA；稳态层流 CFD | 待批准 T1 profiles | 有限结果、结果导出、质量平衡、case/data 重开 | 待运行 | 仅报告实际通过和受限功能 | 不等于 AirJet 结构/气动结果 | NOT_RUN |
| Geometry method | 整机 CAD 候选生成 | P1 | 全产品 | D/P/I/C/U | P1 registry/contracts | 同一母版 9 variants | 006 profiles 待建 | 252 Gate rows + independent review | 无 | 尚不可写成完成结果 | 005 与 006/007 未完成 | NOT_RUN |

## 3. 写作前必须补齐

- 每项数值方法对应的控制方程、离散格式、网格/时间步独立性和收敛阈值；
- 每个图表的生成脚本、输入 run ID 和数据 SHA-256；
- 训练/校准与验证数据分离；
- 负结果、Student 限制和未识别内部结构；
- 从 005 到 P1--P6 的 Gate 记录，而不是只引用软件截图。
- run #22 已具备签名 commit/profile/script/runner SHA、run/job ID、declared reports、逐项复算的 artifact
  manifests、精确 classification 与 visibility，现可作为工具链方法的直接运行证据；它仍不是产品 CAD、
  native transfer 或任何 P1--P6 Gate 证据。

005 只能支持“方法工具链已经验证或存在限制”，不能成为 AirJet 产品性能结果。

## 4. T0 写作时怎样引用失败与成功

方法章节不要只呈现最后的绿色结果。推荐按以下因果链写：

1. 固定 profile、commit、脚本 SHA 和终态协议；
2. 首轮检测到 Workbench 模板内部键和 PyFluent 版本/退出语义错误；
3. 在不放宽执行边界的前提下修正 typed API 与内部键；
4. 用新 commit、新 script SHA、新 job ID 复测；
5. 四路控制集通过，但工程能力保持 `NOT_RUN`。

这可以支持“自动化验证过程具有失败保留和可重复复测机制”。它不能支持任何 AirJet 几何、
结构、流动或热性能主张。
