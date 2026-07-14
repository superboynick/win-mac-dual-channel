# Windows Codex 任务：AJM-WIN-P1-FULL-PRODUCT-CAD-BUILD-006

目标：在 005 已证明 P1 CAD 必需工具链可用后，从仓库生成的合同表建立 AirJet Mini Gen1 **完整产品候选 CAD**、完整流体负体积和可复核交接物。本任务不是单 cell，不做物理求解，不宣告 P1 Gate PASS。

仓库：`C:\Users\admin\win-mac-dual-channel`

## 1. 启动硬门槛

本任务必须从 Windows 可见桌面的 Codex 执行。先读取：

1. `AGENTS.md`；
2. `airjet-simulation/PROJECT_STATUS.md`；
3. `airjet-simulation/manuals/01_FULL_PRODUCT_CAD.md`；
4. `airjet-simulation/parameters/P1_CAD_CONTRACT_METHOD.md`；
5. `airjet-simulation/geometry/contracts/README.md`；
6. 本任务引用的全部参数/合同 CSV；
7. `C:\Users\admin\Downloads\AIRJET_ANSYS_STUDENT_CAPABILITY_SMOKE_005.txt`。

先把报告按 `KEY=VALUE` 解析为唯一键。键重复、同一键出现冲突值、缺少任务身份或 40 位 Git commit 时一律拒绝；不能用模糊字符串搜索代替逐键检查。005 报告必须同时满足：

```text
TASK=AJM-WIN-ANSYS-STUDENT-CAPABILITY-SMOKE-005
COMPUTER=LAPTOP-LCCLM2HI
ANSYS_VERSION=2026 R1（允许附带更精确 build 文本）
INSTALL_ROOT=D:\ansys\ANSYS Inc\ANSYS Student\v261
GIT_FETCH=PASS
GIT_CLEAN=true/TRUE/PASS
PROJECT_AUDIT=PASS
OLD_PLE_BASELINE=CLEAN
PARAMETRIC_GEOMETRY=PASS
NAMED_SELECTIONS=PASS
VOLUME_EXTRACT=PASS
FLUID_CONNECTIVITY=PASS
NATIVE_SAVE=PASS
WORKBENCH_GEOMETRY_TRANSFER=PASS
NAMED_SELECTION_TRANSFER=PASS
P1_STAGE_GATE=NOT_RUN
P1_CAD_TOOLCHAIN_READINESS=PASS 或 PASS_WITH_TRANSFER_LIMITATION
STUDENT_TOOLCHAIN_STATUS=PASS_START_P1 或 PASS_START_P1_WITH_LIMITATIONS
```

任一字段缺失/失败、报告不存在，或发现旧 PLE/1055 污染基线，写 `CAD_BUILD_STATUS=BLOCKED_005_GATE` 并停止。STEP 失败本身不阻止开始，但必须继承 005 的传递限制。

读取 005 的 `GIT_COMMIT` 为 `$Report005Commit`，要求：

```powershell
git cat-file -e "$Report005Commit^{commit}"
git merge-base --is-ancestor $Report005Commit HEAD
```

两条均必须退出码 0。005 commit 可以是当前 HEAD 的祖先，但不能是另一条历史或未知对象。报告中还要记录 `REPORT_005_GIT_COMMIT`、当前 `GIT_COMMIT`、005 路径和 SHA256。当前主机名、安装根目录或 Ansys 主版本与 005 不一致时，旧报告失效，重新执行 005。

## 2. 许可与 Student 安全边界

1. 不打开、枚举、读取或修改任何许可文件、本地许可池或许可内容。
2. 不修改、停止或替换许可服务、注册表许可设置、授权环境变量、许可优先级或 checkout 路线。
3. 只允许检查已知污染标记：旧 PLE 卸载项/服务、1055 监听、`ANSYSLMD_LICENSE_FILE=1055@localhost`；不得输出其他授权值。
4. 不运行激活器、补丁、破解器、许可证生成器或第三方许可程序。
5. 遇到 checkout 失败、Student 模型上限或并行限制时，保存当前外部产物、记录原始错误并写 `PARTIAL_CAD_OUTPUT`；不得通过删 cell/孔或改授权继续。

## 3. Git 与环境硬门槛

再执行：

```powershell
cd C:\Users\admin\win-mac-dual-channel
git fetch origin
if ($LASTEXITCODE -ne 0) { throw 'GIT_FETCH_FAILED' }
git remote get-url origin
git rev-parse --abbrev-ref HEAD
git rev-parse --abbrev-ref --symbolic-full-name '@{u}'
git status --short --branch
git status --porcelain
git rev-parse HEAD
git rev-list --left-right --count HEAD...origin/main
powershell -ExecutionPolicy Bypass -File .\audit-airjet-project.ps1
python .\airjet-simulation\parameters\build_p1_cad_inputs.py --check
python .\airjet-simulation\parameters\build_p1_cad_contracts.py --check
```

要求 fetch 本次明确成功、origin 精确为 `https://github.com/superboynick/win-mac-dual-channel.git`、当前分支为 `main`、upstream 为 `origin/main`、工作树干净、ahead/behind=`0/0`、审计 PASS、两个生成器 PASS。任一命令非零或条件不符，写 `CAD_BUILD_STATUS=BLOCKED_GIT_OR_ENVIRONMENT`，记录原始错误并停止。禁止使用 fetch 失败前缓存的 `origin/main` 判定 0/0；禁止 pull 后继续处理未知修改，禁止 reset/clean/rebase/force。

还要求开始时 `C:` 可用空间至少 10 GiB、`D:` 至少 20 GiB、可用物理内存至少 8 GiB；不足时按环境阻断，不打开 CAD。

## 4. 输出边界

创建一次性运行目录：

```text
D:\AirJet_P1\AJM-P1-CAD-006\<UTC-run-id>\
```

不要把含 `< >` 的占位符当成真实路径。实际创建命令：

```powershell
$RunId = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$RunRoot = Join-Path 'D:\AirJet_P1\AJM-P1-CAD-006' $RunId
New-Item -ItemType Directory -Path $RunRoot -ErrorAction Stop | Out-Null
$Report005Copy = Join-Path $RunRoot 'inputs\AIRJET_ANSYS_STUDENT_CAPABILITY_SMOKE_005.txt'
New-Item -ItemType Directory -Path (Split-Path $Report005Copy) -Force | Out-Null
Copy-Item -LiteralPath 'C:\Users\admin\Downloads\AIRJET_ANSYS_STUDENT_CAPABILITY_SMOKE_005.txt' -Destination $Report005Copy -ErrorAction Stop
```

CAD 脚本、原生模型、STEP、流体体、Workbench 项目、截图、日志和哈希清单全部写入该目录，不写入 Git 工作树。最终摘要另存：

`C:\Users\admin\Downloads\AIRJET_P1_FULL_PRODUCT_CAD_BUILD_006.txt`

任务期间禁止修改、提交或推送 Git。不得保存许可证、密钥或授权数据。

开始建模前、每完成一个变体/分支后、最终生成哈希后都运行 `git status --porcelain`。任何时点非空，立即停止并记为 `PARTIAL_CAD_OUTPUT`（尚未建模则 `BLOCKED_GIT_OR_ENVIRONMENT`）；只报告新增/修改路径，不读取未知文件内容，不 reset/clean/覆盖。

## 5. 母版和证据合同

尽量使用 SpaceClaim/Discovery 的可重放脚本或参数化 API；若某一步只能 GUI 完成，记录操作和截图。建立一个母版，不手工复制四份互不关联的 CAD。

坐标和命名完全服从：

- `parameters/p1_cad_parameter_map.csv`；
- `parameters/p1_model_form_variants.csv`；
- `parameters/p1_vent_geometry_candidates.csv`；
- `parameters/p1_orifice_pattern_candidates.csv`；
- `parameters/p1_planform_exhaust_candidates.csv`；
- `parameters/p1_internal_geometry_rules.csv`；
- `geometry/contracts/p1_cad_features.csv`；
- `geometry/contracts/p1_cad_feature_parameter_bindings.csv`；
- `geometry/contracts/p1_cad_interfaces.csv`；
- `geometry/contracts/p1_cad_named_selections.csv`。

外包络只能锁定 `27.5 x 41.5 x 2.8 mm`。所有 `CAND/REF/U` 名称和证据标签保留。`C017_SUPPORT_ALLOWANCE_REF`、`C019_TOP_REF`、`C019_BOTTOM_REF` 只能是 construction/reference geometry：不得参与 Boolean、不得赋材料/质量、不得传给结构或 CHT、不得作为物理产品层导出。另建的 `FLUID_DOMAIN_CLOSURE_DATUM_C` 只能按 `RESIDUAL_NUMERICAL_CLOSURE_R0` 提供流体边界 datum；它不是残差实体。`CENTRAL_ANCHOR_CAND_TEMPLATE` 是 P 存在/拓扑 prior 下的 C 类方形 construction datum，`CELL_PARTITION_CAND_TEMPLATE` 是零厚度 ownership/naming datum；二者均无材料、质量、Boolean、solver/export，且不得进入 fluid union。`FLEX_KEEP_OUT_U` 仅为参考禁入区。

流体域必须直接构造并 union 合同声明的 top plenum、perimeter gaps、bottom chambers、orifice throats、impingement channel、manifold 和 spout，再做 Volume Extract/连通复核。禁止使用“整个外包络减去所有候选固体”作为流体域，因为那会把 `C017/C019` 未识别区错误地当成空气。

## 6. 必须建立的整机几何

每个配置都必须包含完整产品，而不是周期 cell：

```text
四个候选顶盖进气槽
  -> 共享 R0 顶部配气空间与全部 cell 顶腔
  -> 每个 cell 的膜片外围转移间隙
  -> 每个 cell 底腔
  -> 每个 cell 对应孔板实际喷孔
  -> 覆盖全部喷孔的整机冲击通道
  -> +Y 单侧排气汇流区
  -> 产品 +Y 外包络面上的唯一候选出口
```

建立完整顶盖、候选侧框流体壁代理、零厚度 cell-partition datum、膜片和非物理 central-anchor datum、孔板、热扩散面以及上述流体负体积。共享部件只建一次；不能在每个 cell 中复制共享板造成重叠，也不能把两个 datum 当成物理部件。

默认 R0 选择：

```text
selected_vent_candidate_set_id=VENT_FLOW_BBOX_R0
selected_orifice_pattern_id=<configuration_id>__PHI_DERIVED_SQUARE
selected_exhaust_branch_id=<configuration_id>__EXH_FULL_WIDTH_RECT_R0
selected_cell_geometry_rule_id=CELL_CENTER_AND_TILE_R0
selected_central_anchor_rule_id=CENTRAL_ANCHOR_SQUARE_DATUM_R0
selected_bottom_chamber_rule_id=BOTTOM_CHAMBER_PER_CELL_SQUARE_R0
selected_cell_partition_rule_id=CELL_PARTITION_DATUM_R0
selected_top_chamber_branch_id=TOP_SHARED_PLENUM_R0
selected_perimeter_gap_branch_id=PERIM_SPLIT_GAP_R0
selected_side_frame_closure_branch_id=SIDE_WALL_BOUNDARY_R0
selected_residual_closure_branch_id=RESIDUAL_NUMERICAL_CLOSURE_R0
selected_orifice_grid_rule_id=ORIFICE_PER_CELL_CENTERED_CLIP_R0
```

默认只是可复查工程分支，不是产品事实。

## 7. 构型与敏感性输出

从同一母版生成 `p1_model_form_variants.csv` 的全部 9 行。前 6 行是交付/残差变体：

- `M-3x4-7.0` 的 `C020=0.25/0.50/0.75`；
- `M+S-3x5-6.0` balanced；
- `L-2x4-8.0` balanced；
- `S-3x5-5.5` balanced。

后 3 行是以 `M-3x4-7.0__R50_BALANCED` 为父项、已经有独立 variant ID 和完整 Gate 行的单因素派生变体：

1. `M-3x4-7.0__R50_VENT_UPPER`：只把顶盖改为 `VENT_UPPER_CENTERLINE_P013_R0`；
2. `M-3x4-7.0__R50_ORIFICE_EDGE_GAP`：只把喷孔改为 `M-3x4-7.0__P008_AS_EDGE_GAP`；
3. `M-3x4-7.0__R50_EXHAUST_HALF_TAPER`：只把排气改为 `M-3x4-7.0__EXH_CENTER_HALF_TAPER_R0`。

对每个派生变体导出与父项的参数 diff，必须证明除 `changed_factor` 对应的 branch ID 外其他参数和内部规则逐项相同。

`P008_AS_CENTER_PITCH_SENTINEL` 只保留为数学冲突记录，不作为交付 CAD。不得为了绕过 Student 限额减少 cell、删除孔、合并关键流体路径或缩小整机；若完整构型达到软件限制，保存已完成产物并写 `PARTIAL_CAD_OUTPUT`。

## 8. 每个输出的自动检查

每个变体/分支都建立独立子目录并记录：

- 驱动参数、选中的三类 branch ID；
- 实测外包络和 2.8 mm 厚度闭合误差；
- solid/fluid body 数；
- 每个 cell 从进气域到唯一产品出口的图连通结果；
- isolated fluid、干涉、重复面、零厚度/细碎体计数；
- Boolean 后实际孔数、盲孔/丢失孔、实际活动孔板面积、实际开孔面积和开孔率；
- `P004+P006` 位移包络下的最小间隙；
- 所有 required Named Selections 的预期/实际 cardinality；`{NNN}` 展开为 `001..N_CELL`，每个 interface 的 A/B selection 必须分别属于 A/B feature，不能用同一个 owner 的面集冒充两侧；
- 原生保存并重开；
- STEP 导出/重导入；
- Workbench 几何传递和 Named Selections 传递；
- 原生 CAD、STEP、流体体、Workbench、脚本、截图、日志的大小与 SHA256。

切片截图至少包含 XY 顶视、XZ/ YZ 中剖面、完整外形、全部 cell、入口、孔板、冲击通道、歧管、出口和流体连通视图。截图必须能区分实体候选和流体体。

### 8.1 外部 manifest 的固定角色

保留 `logs/external-files.csv` 的九列 header；实际 manifest 写在 `$RunRoot` 中，Git 仓库内模板保持空。每个 `(case_id,file_role)` 恰好一行，路径唯一，时间为带 `Z` 或 `+00:00` 的 UTC，SHA256 为 64 位十六进制，`git_commit` 等于本次 006 的 40 位 commit。`case_id=GLOBAL` 必须覆盖：

```text
BUILD_SCRIPT
MASTER_NATIVE_CAD
REPORT_005_COPY
INPUT_CONTRACT_HASHES
GATE_EVIDENCE_006_CSV
GLOBAL_BUILD_LOG
```

九个正式 variant ID 每个必须覆盖：

```text
VARIANT_PARAMETER_RECORD
NATIVE_CAD
NATIVE_REOPEN_LOG
FLUID_GEOMETRY
WORKBENCH_PROJECT
WORKBENCH_TRANSFER_LOG
AUTOMATED_CHECKS_CSV
SCREENSHOT_XY
SCREENSHOT_XZ
SCREENSHOT_YZ
FLUID_CONNECTIVITY_VIEW
VARIANT_BUILD_LOG
```

三个派生 variant 还必须各有 `PARENT_PARAMETER_DIFF` 和 `PARENT_GEOMETRY_RESULT_DIFF`。`COMPLETE_AWAITING_REVIEW` 每个 variant 必须再有 `STEP_GEOMETRY` 和 `STEP_REIMPORT_LOG`；transfer-limited 状态允许某个 variant 用 `STEP_LIMITATION_LOG` 代替这两项，但至少一个 variant 必须有该限制日志。`$RunRoot` 中除 manifest 自身以外的每个普通文件都必须出现在 manifest，禁止 symlink；不能只列成功文件。`REPORT_005_COPY` 必须是原始 005 报告的逐字节副本，其 SHA256 与最终报告的 `REPORT_005_SHA256` 相同。

### 8.2 机器可读检查表

每个 `AUTOMATED_CHECKS_CSV` 恰好一行，header 固定为：

```text
variant_id,configuration_id,cell_count,connected_cell_count,isolated_fluid_count,interference_count,sliver_count,duplicate_face_count,excluded_datum_feature_ids,actual_orifice_count,blind_or_lost_orifice_count,actual_open_area_pct,minimum_clearance_mm,envelope_x_mm,envelope_y_mm,envelope_z_mm,thickness_closure_error_mm,named_selection_check,native_reopen,workbench_geometry_transfer,named_selection_transfer,step_transfer,c017_c019_physics_guard,anchor_partition_nonphysical_guard
```

完成状态要求 cell 连通数等于配置值，isolated/interference/sliver/duplicate/blind-or-lost 均为 0，实际孔数大于 0，开孔率 8--12%，最小间隙非负，包络误差和厚度闭合误差不大于 `1e-6 mm`，命名/重开/传递和两个 physics guard 字段均为 `PASS`。interference/sliver/duplicate 只统计导出的物理候选实体和 required fluid bodies；`excluded_datum_feature_ids` 必须逐字记录 `ENVELOPE_REF;SIDE_FRAME_PROXY_U;FLEX_KEEP_OUT_U;CELL_PARTITION_CAND_TEMPLATE;CENTRAL_ANCHOR_CAND_TEMPLATE;C017_SUPPORT_ALLOWANCE_REF;C019_TOP_REF;C019_BOTTOM_REF;FLUID_DOMAIN_CLOSURE_DATUM_C;SPOUT_SOLID_CAND_U;TIM_EQUIVALENT_C;CHIP_HEAT_SOURCE_C`，不允许操作者现场决定计数范围。正常完成的 `step_transfer=PASS`；限制状态至少一个 variant 为 `LIMITATION_RECORDED`，且该 variant 必须同时具有 `STEP_LIMITATION_LOG` 和 `G4_STEP_TRANSFER=LIMITATION_RECORDED`。

全局 `GATE_EVIDENCE_006_CSV` 必须与冻结 Gate 模板具有完全相同的 252 个键，header 固定为：

```text
gate_item_id,variant_id,measured_value,evidence_original_path,evidence_sha256,secondary_evidence_original_path,secondary_evidence_sha256,006_suggested_status,notes
```

每行必须引用 manifest 中同一路径/哈希；不用第二证据时两个 secondary 字段同时留空。九条 `G0_005_TOOLCHAIN` 必须直接引用 `REPORT_005_COPY`。三个派生 variant 的 `G4_SINGLE_FACTOR_ISOLATION` 必须用 primary/secondary 两组引用同时覆盖本 variant 的 `PARENT_PARAMETER_DIFF` 和 `PARENT_GEOMETRY_RESULT_DIFF`。006 对已完成 build gate 只能建议 `PASS`；`P1_INDEPENDENT_REVIEW` 九行必须为 `BLOCKED`；transfer-limited 状态下 `G4_STEP_TRANSFER` 才可建议 `LIMITATION_RECORDED`。这些只是 006 建议，不得写入独立 reviewer 状态。

### 8.3 固定输入 commit 和哈希

006 必须从当前 commit 的 Git blob 计算合同哈希，不能从可能被随后修改的工作树猜测。合同 bundle 精确包含：

```text
airjet-simulation/checklists/p1_cad_gate_matrix.csv
airjet-simulation/parameters/p1_model_form_variants.csv
airjet-simulation/parameters/p1_cad_parameter_map.csv
airjet-simulation/parameters/p1_internal_geometry_rules.csv
airjet-simulation/parameters/p1_orifice_pattern_candidates.csv
airjet-simulation/parameters/p1_vent_geometry_candidates.csv
airjet-simulation/parameters/p1_planform_exhaust_candidates.csv
airjet-simulation/parameters/p1_layout_configuration_matrix.csv
airjet-simulation/parameters/p1_thickness_budget.csv
airjet-simulation/geometry/contracts/p1_cad_features.csv
airjet-simulation/geometry/contracts/p1_cad_feature_parameter_bindings.csv
airjet-simulation/geometry/contracts/p1_cad_interfaces.csv
airjet-simulation/geometry/contracts/p1_cad_named_selections.csv
airjet-simulation/geometry/contracts/p1_cad_open_questions.csv
airjet-simulation/parameters/build_p1_cad_inputs.py
airjet-simulation/parameters/build_p1_cad_contracts.py
```

算法是：对每个 `git show <GIT_COMMIT>:<repo-relative-path>` 的原始字节取 SHA256，再按仓库相对路径排序，拼成每行 `path<TAB>sha256<LF>`，最后对整段 UTF-8 字节取 SHA256。把逐文件表保存为 `INPUT_CONTRACT_HASHES`，并报告 bundle、Gate、variant、internal-rules 四个哈希。007 会从 006 commit 独立重算，不接受当前 HEAD 的替代文件。

## 9. 质量与真实性规则

P1 不知道完整材料/密度。只能报告已知或明确假定部分的体积/候选质量，并把距离官方 11 g 的未解析质量单列。禁止随意赋密度把模型强行凑到 11 g。

候选 CAD 成功生成不关闭 `p1_cad_open_questions.csv`；禁止把专利/图像/工程闭合候选改写为 `D` 类或生产几何。任何尺寸偏离生成表必须记录原值、改值、理由、影响和证据等级，不能静默修形。

## 10. 最终报告

报告至少包含：

```text
TASK=AJM-WIN-P1-FULL-PRODUCT-CAD-BUILD-006
RUN_ID=
COMPUTER=LAPTOP-LCCLM2HI
ANSYS_VERSION=2026 R1（可附更精确 build）
INSTALL_ROOT=D:\ansys\ANSYS Inc\ANSYS Student\v261
GIT_COMMIT=
GIT_FETCH=
GIT_ORIGIN=https://github.com/superboynick/win-mac-dual-channel.git
GIT_BRANCH=main
GIT_UPSTREAM=origin/main
GIT_CLEAN=
GIT_AHEAD_BEHIND=0/0
FINAL_GIT_CLEAN=PASS/FAIL
PROJECT_AUDIT=
P1_INPUT_GENERATOR_CHECK=
P1_CONTRACT_GENERATOR_CHECK=
C_FREE_GIB=
D_FREE_GIB=
AVAILABLE_RAM_GIB=
OLD_PLE_BASELINE=CLEAN
LICENSE_SAFETY_CHECK=PASS/FAIL
REPORT_005_PATH=
REPORT_005_SHA256=
REPORT_005_GIT_COMMIT=
P1_CAD_TOOLCHAIN_READINESS=
EXTERNAL_RUN_DIRECTORY=
MASTER_MODEL_PATH=
MASTER_MODEL_SHA256=
P1_CONTRACT_BUNDLE_SHA256=
GATE_TEMPLATE_SHA256=
VARIANT_TABLE_SHA256=
INTERNAL_RULES_SHA256=
CONFIGURATIONS_REQUESTED=4
CONFIGURATIONS_BUILT=
BASE_OR_RESIDUAL_VARIANTS_REQUESTED=6
BASE_OR_RESIDUAL_VARIANTS_BUILT=
DERIVED_SINGLE_FACTOR_VARIANTS_REQUESTED=3
DERIVED_SINGLE_FACTOR_VARIANTS_BUILT=
TOTAL_VARIANTS_REQUESTED=9
TOTAL_VARIANTS_BUILT=
PARAMETER_DIFF_CHECK=PASS_ALL_3_DERIVED/FAIL
GEOMETRY_RESULT_DIFF_CHECK=PASS_ALL_3_DERIVED/FAIL
ENVELOPE_CHECK=PASS_ALL_9/FAIL
THICKNESS_CLOSURE_CHECK=PASS_ALL_9/FAIL
FLUID_CONNECTIVITY_CHECK=PASS_ALL_9/FAIL
ISOLATED_FLUID_CHECK=PASS_ALL_9/FAIL
INTERFERENCE_CHECK=PASS_ALL_9/FAIL
SLIVER_CHECK=PASS_ALL_9/FAIL
ORIFICE_INTEGRITY_CHECK=PASS_ALL_9/FAIL
CLEARANCE_CHECK=PASS_ALL_9/FAIL
CONNECTED_CELL_COUNT_BY_VARIANT=
ISOLATED_FLUID_COUNT_BY_VARIANT=
INTERFERENCE_COUNT_BY_VARIANT=
SLIVER_COUNT_BY_VARIANT=
ACTUAL_ORIFICE_COUNT_BY_VARIANT=
ACTUAL_OPEN_AREA_PCT_BY_VARIANT=
BLIND_OR_LOST_ORIFICE_COUNT_BY_VARIANT=
MINIMUM_CLEARANCE_BY_VARIANT=
NAMED_SELECTION_CARDINALITY_CHECK=PASS_ALL_9/FAIL
NATIVE_SAVE_REOPEN=PASS_ALL_9/FAIL
STEP_EXPORT_REIMPORT=PASS_ALL_9/LIMITATION_RECORDED/FAIL
WORKBENCH_GEOMETRY_TRANSFER=PASS_ALL_9/FAIL
NAMED_SELECTION_TRANSFER=PASS_ALL_9/FAIL
C017_C019_PHYSICS_GUARD=PASS_ALL_9/FAIL
ANCHOR_PARTITION_NONPHYSICAL_GUARD=PASS_ALL_9/FAIL
UNRESOLVED_MASS_ACCOUNT=
EXTERNAL_FILE_MANIFEST=
EXTERNAL_FILE_MANIFEST_SHA256=
MANIFEST_DATA_ROW_COUNT=
ERROR_MESSAGES=
TRANSFER_LIMITATION_SCOPE=NONE/STEP_ONLY
P0_STAGE_GATE=PASS
P1_STAGE_GATE=NOT_STARTED/INCOMPLETE/PENDING_PEER_REVIEW
P2_STAGE_GATE=NOT_RUN
P3_STAGE_GATE=NOT_RUN
P4_STAGE_GATE=NOT_RUN
P5_STAGE_GATE=NOT_RUN
P6_STAGE_GATE=NOT_RUN
CAD_BUILD_STATUS=
```

`CAD_BUILD_STATUS` 只能是：

```text
BLOCKED_005_GATE
BLOCKED_GIT_OR_ENVIRONMENT
PARTIAL_CAD_OUTPUT
COMPLETE_WITH_TRANSFER_LIMITATION_AWAITING_REVIEW
COMPLETE_AWAITING_REVIEW
```

006 绝不输出 `P1_STAGE_GATE=PASS`。即使全部自动检查成功，也只能写 `PENDING_PEER_REVIEW`，保留产物并停止，等待独立 peer 审计和用户查看。peer 可以位于 Mac 或另一个 Windows 会话，但不能是生成这些产物的同一会话。

状态必须按以下规则唯一映射：

- `BLOCKED_005_GATE`：005 身份、唯一键、主机/版本/安装根、commit 祖先关系、纯净许可基线或 P1 必需能力任一失败；`P1_STAGE_GATE=NOT_STARTED`。
- `BLOCKED_GIT_OR_ENVIRONMENT`：正式建模前的 fetch/origin/upstream/clean/0-0/audit/generator/磁盘/内存任一失败；`P1_STAGE_GATE=NOT_STARTED`。
- `PARTIAL_CAD_OUTPUT`：已经开始建模，但 4 配置、9 个有独立 ID/Gate 的 variants、单因素 diff、9 条内部几何规则、原生重开、完整连通、零孤立体、零干涉/碎片/盲孔、required 成对 Named Selections、Workbench 几何/Named Selection 传递或完整 SHA256 manifest 任一未完成；`P1_STAGE_GATE=INCOMPLETE`。
- `COMPLETE_WITH_TRANSFER_LIMITATION_AWAITING_REVIEW`：上一条全部完成，唯一剩余失败是 005 已知或 006 复现的 STEP 导出/重导入限制；`P1_STAGE_GATE=PENDING_PEER_REVIEW`。
- `COMPLETE_AWAITING_REVIEW`：4 个配置、9 个变体及全部硬检查、原生/STEP/Workbench 传递和 manifest 均完成；`P1_STAGE_GATE=PENDING_PEER_REVIEW`。

报告的 `CAD_BUILD_STATUS` 和 `P1_STAGE_GATE` 必须各出现一次，不能同时列出多个值。完成状态仍然只是等待独立复核，不是 P1 PASS。

## 11. 仓库审计锁（不是报告输出）

下列 ASCII 行把关键语义固定给双审计器；执行者不得把它们复制成多个报告值，也不得删去对应正文要求：

```text
REPORT_005_PARSE=UNIQUE_KEYS_REJECT_DUPLICATES_AND_CONFLICTS
REPORT_005_IDENTITY=TASK_COMPUTER_ANSYS_VERSION_INSTALL_ROOT_COMMIT
LICENSE_POLICY=NO_LICENSE_FILE_POOL_SERVICE_REGISTRY_ENV_PRIORITY_CHECKOUT_MUTATION
RESOURCE_THRESHOLDS_GIB=C_FREE_GE_10_D_FREE_GE_20_AVAILABLE_RAM_GE_8
GIT_RECHECK=BEFORE_BUILD_AFTER_EACH_VARIANT_AFTER_FINAL_MANIFEST
STATUS_MAP_BLOCKED_005_GATE=NOT_STARTED
STATUS_MAP_BLOCKED_GIT_OR_ENVIRONMENT=NOT_STARTED
STATUS_MAP_PARTIAL_CAD_OUTPUT=INCOMPLETE
STATUS_MAP_COMPLETE_WITH_TRANSFER_LIMITATION_AWAITING_REVIEW=PENDING_PEER_REVIEW
STATUS_MAP_COMPLETE_AWAITING_REVIEW=PENDING_PEER_REVIEW
P1_PASS_PROHIBITED=006_CAN_ONLY_REACH_PENDING_PEER_REVIEW
005_TRANSFER_LIMITATION_INHERITANCE=REQUIRED
```
