# 现实问题与失败日志

这个文件记录“计划遇到真实电脑后发生了什么”。原始大日志留在 Git 外并登记 SHA-256；
这里保留短错误、区分实验、根因置信度、影响和下一步。不得写许可内容或凭证。

## REAL-20260714-001：通用 Codex 没有执行 005

- Stage/task：005 Student capability smoke
- Machine/operator：Windows / Windows Codex deferred task
- 期望：启动 ANSYS 并生成 005 报告。
- 实际：连续三次只检查 Git/项目审计并输出摘要；没有 ANSYS 进程，没有必需报告。
- 运行差异：先后尝试 workspace-write、加强命令式 prompt、danger-full-access。
- 原始证据：Windows Downloads 中 `AIRJET_005_CODEX_EXEC_LAST_REPORT.txt` 和
  `AIRJET_005_DEFERRED_STATUS.txt`；未复制进 Git。
- 根因判断：通用提示缺少确定的 ANSYS 工具接口、完成断言与产物协议；高置信度。
- 拒绝的 workaround：继续堆叠更强 prompt 或坐标点击，因为仍不可确定、不可复核。
- 影响：005 未运行，P1 不能开始。
- 处置：改用官方 ANSYS API + 专用 skill + hash-pinned MCP。
- 状态：CLOSED_BY_DESIGN_CHANGE

## REAL-20260714-002：临时计划任务不是可持续执行层

- Stage/task：005 deferred launcher
- 实际：临时任务能启动 Codex，但不能保证 ANSYS 动作与报告产生。
- 处置：`AirJet005Deferred` 已删除；脚本和状态留在 Downloads 作为历史证据。
- 边界：不重新注册 Scheduled Task、自启动项或 watcher 自动执行。
- 状态：CLOSED

## REAL-20260714-003：Student 安装有两个非当前阻塞警告

- 观察：官方安装日志曾报告 `python_site_syscplg` 与 `cuDSS` 压缩包解压失败。
- 实测：Workbench 批处理和 Fluent Student 基础 checkout 已成功；不能据此推断 System
  Coupling 或 GPU 稀疏求解可用。
- 影响：005 保留 `SYSTEM_COUPLING_STATUS=UNVERIFIED_WARNING`、
  `CUDSS_STATUS=UNVERIFIED_WARNING`；当前不执行修复安装。
- 状态：OPEN_LIMITATION

## REAL-20260714-004：脚本目录 allowlist 仍然过宽

- Stage/task：ANSYS MCP 安全设计
- 初始设计：调用者可传 engine、脚本相对路径和运行目录。
- 发现：ANSYS journal/Python 本身可调用系统能力，因此“位于批准目录”不等于安全。
- 最小区分：审查 MCP 的调用面和脚本 TOCTOU。
- 根因：把路径约束误当成能力约束；高置信度。
- 处置：调用者现在只能传 `profile_id`/`case_id`；profile 固定 engine、Git blob、SHA、
  timeout、output-root ID 和 reports；删除任意路径/命令/环境入口。
- 影响：增加准备工作，但能让无人值守运行可审计。
- 状态：CLOSED_IN_IMPLEMENTATION_PENDING_WINDOWS_TEST

## REAL-20260714-005：第一版 MCP 仍有真实并发和 Windows 路径漏洞

- 发现：超时依赖客户端 poll；`JOBS` 无锁；校验后从工作树读脚本存在 TOCTOU；
  `resolve()` 会先消解 junction；Popen 运行后才进入 Job Object；几乎完整环境会泄露 token
  或允许 `PYTHONPATH` 注入；manifest 会读取可变 policy 并把大文件读入内存。
- 处置：RLock + 独立 watchdog；从已验签 commit blob 读 policy/script；固定签名指纹；
  lexical 路径逐段拒绝 reparse；`CREATE_SUSPENDED` 后分配 Job Object 再恢复；最小白名单环境；
  Python `-I -B`；冻结 reports；终态后流式哈希和有界 JSON 内联。
- 尚需实测：Windows Job Object 的挂起/恢复、Authenticode inventory、junction 拒绝、
  MCP 并发拒绝和 watchdog 超时。
- 状态：OPEN_UNTIL_WINDOWS_NEGATIVE_TESTS_PASS

## REAL-20260714-006：本机原生格式不能只凭扩展名判断

- 观察：官方 v261 安装内同时存在 `.scdoc` 与 `.scdocx`；Windows 文件关联分别指向
  SpaceClaim 与 AnsysSpeosLauncher。
- 判断：文件关联不是 SpaceClaim API 保存/重开能力证据。
- 处置：T0 同时调用 `DocumentSave.Execute` 保存两种格式；005 T1 再由 SpaceClaim 重开并
  核对 body、包络和名称。
- T0 实测：两轮中 `.scdocx` 都实际存在并进入 artifact manifest；`.scdoc` 的保存调用返回
  success，但文件均不存在。因此命令返回值不是文件落盘证据，T1 以 `.scdocx` 重开为当前
  原生格式主路线，并继续把 `.scdoc` 记为观察到的限制。
- 对论文的影响：方法章节只报告实测成功的原生格式，不使用“应该支持”的措辞。
- 状态：T0_SC_DOCX_PASS_SCDOC_LIMITATION_OPEN_UNTIL_T1_REOPEN

## REAL-20260714-007：共享 Git 在长补丁期间前进了一次

- Stage/task：ANSYS 执行层集成
- 期望：在 Mac 当前 `main` 上完成补丁后直接提交。
- 实际：补丁尚未完成时 Windows 合法推送了 watcher 轮询优化，`origin/main` 从
  `f203739` 前进到 `9af87b3`；Mac 原工作树已有大量 staged 文件，不能安全直接 pull。
- 风险：在脏工作树里 merge/rebase 会把基础版本、Windows 修改和本次补丁混为一体，也可能
  破坏“只允许 fast-forward handoff”的协作规则。
- 处置：把完整补丁固化到 `/private/tmp/airjet-ansys-layer.patch`（SHA-256
  `8e18f271d2bc32ebcd9d234e7d346371819e3146995b209801643b34bf9e9136`），从最新
  `origin/main` 建隔离 worktree，再用三方 apply；确认 watcher 的 `POLL_SECONDS=10` 与新
  ANSYS 层同时存在后，在隔离树完成测试和发布。旧脏树保留为恢复副本，不 reset。
- 教训：并行协作中的“完成”必须定义为已签名 commit + push；长补丁应在最终发布前重放到
  最新可信基线，而不是把同步冲突藏进一次 merge。
- 状态：CLOSED_BY_ISOLATED_INTEGRATION

## REAL-20260714-008：PyFluent 健康值是 Enum，不是裸字符串

- Stage/task：005 / PyFluent T0
- 初始实现：`str(check_health()).upper() == "SERVING"`。
- 审查发现：官方 API 返回 `Status` 枚举，字符串表示可能为 `Status.SERVING`；Fluent 实际健康
  仍会被脚本误判为失败。
- 处置：保留枚举名称用于报告，PASS 断言改用官方布尔属性 `health_check.is_serving`；重新计算
  脚本 SHA-256 并更新 profile 为
  `270a1600906b936fa23fd7f7911920bcb3e44bf361e89ea035b91806f011d266`。
- 对论文的影响：方法中应报告检查的语义字段，不把调试显示字符串当稳定协议。
- 状态：CLOSED_IN_CODE_PENDING_WINDOWS_T0

## REAL-20260714-009：inventory 提示不能代替 submit 的服务端边界

- Stage/task：ANSYS MCP fail-closed 复审
- 发现：设计要求调用者先 `inventory()`，但安全边界不能依赖 agent 遵守调用顺序；旧版
  `submit_job()` 若不自己重验运行环境，会留下直接提交的绕过可能。
- 处置：`submit_job()` 在创建输出目录和进程前强制检查当前解释器必须是固定 venv、精确
  package 版本、路径链无 reparse、四个 ANSYS executable 的 Authenticode 为 Valid 且发布者
  为 ANSYS Inc.；静态测试通过 AST 断言该调用存在，防止以后回归。
- 残余边界：同一管理员账户主动篡改系统文件超出本 MCP 的防御范围；每次提交仍重新验真。
- 状态：CLOSED_IN_CODE_PENDING_WINDOWS_NEGATIVE_TEST

## REAL-20260714-010：PowerShell 5 把预期的 Codex 非零探测包装成错误

- UTC：2026-07-14
- Stage/task：Windows bootstrap / MCP 首次注册
- 期望：`codex mcp get airjet-ansys` 不存在时返回非零，脚本据此进入 add 分支。
- 实际：依赖安装、imports、skill hashes 与 static policy 均 PASS；Windows PowerShell 5 在
  `$ErrorActionPreference='Stop'` 下把原生程序 stderr 包装成 `NativeCommandError`，在读取
  `$LASTEXITCODE` 前终止脚本。MCP 尚未注册，ANSYS 未启动。
- 原始日志：`C:\Users\admin\Downloads\AIRJET_ANSYS_BOOTSTRAP_20260714.log`。
- 根因：把“资源不存在”的预期探测与真正的 bootstrap 失败共用 Stop 语义；高置信度。
- 处置：只在该探测调用周围临时使用 `Continue`、合并捕获输出并读取退出码，随后立即恢复
  原 ErrorActionPreference；后续 remove/add/get 仍保持 fail-closed。
- 对 Gate/论文主张的影响：无工程能力被执行，005 仍 NOT_RUN；该事件只支持自动化方法中的
  Windows 兼容性与失败恢复描述。
- 状态：CLOSED_IN_CODE_PENDING_BOOTSTRAP_RERUN

## REAL-20260714-011：非交互 Codex 把 MCP 批准等待记为 user cancelled

- Stage/task：005 / MCP inventory 首次调用
- 实际：Codex 成功发现 `airjet-ansys.inventory`，但 `codex exec -s read-only` 无人工批准通道，
  tool result 为 `user cancelled MCP tool call`；未启动 ANSYS。
- 区分实验：在用户已明确授权 YOLO 的前提下，仅对该非交互 Codex 会话启用免批准；服务端
  profile、Git 签名、SHA、固定路径、最小环境和 Job Object 边界保持不变。
- 结果：inventory `ready=true`，四个 executable 均 `Valid / ANSYS Inc.`，包版本与 Git commit
  精确匹配。
- 原始日志：Windows Downloads 下 `AIRJET_ANSYS_MCP_INVENTORY_20260714*.jsonl`。
- 状态：CLOSED_BY_SCOPED_NONINTERACTIVE_APPROVAL

## REAL-20260714-012：LLM 可以调 MCP，但不适合作为一秒一次的轮询器

- Stage/task：SpaceClaim T0 与后续四引擎 suite
- 观察：SpaceClaim 约 20 秒完成；Codex 为等待终态重复输出完整 job JSON，单次 T0 消耗大量
  上下文，虽正确但低效，也会让运行记录被自然语言噪声淹没。
- 处置：保留 Codex/MCP 首次贯通证据，同时增加无参数 `run_t0_suite.py`。它通过官方 MCP
  Python client 调用同一五工具接口，固定四个 profile，不能接受路径、命令或环境输入；每秒
  poll，一次写出 suite JSON。MCP 仍是唯一 ANSYS 执行边界。
- 安全复审附带发现：安装到 `.codex` 的 server 副本需要与签名 Git commit 中的 server blob
  自校验；现已在每次 inventory/submit 的 Git invariant 中加入 SHA 比对，防止安装副本漂移。
  suite runner 也在 inventory PASS 后将自身字节与该精确 commit 的 runner blob 比对；输出名使用
  微秒 UTC 与随机后缀，避免两个调度器同秒覆盖汇总证据。
- 对论文的影响：区分“LLM 选择已审 profile”和“确定性状态机等待求解”；方法可复现性提高，
  但 T0 仍不构成工程能力结果。
- 状态：CLOSED_IN_CODE_PENDING_SUITE_RUN

## REAL-20260714-013：进程内 RLock 不能阻止两个 MCP server 同时提交

- Stage/task：T0 suite release review
- 发现：Codex 注册的 stdio server 与确定性 suite runner 会各自启动一个 Python 进程；原
  `JOBS_LOCK` 和活动任务表仅在进程内有效，两个入口同时 submit 可绕过全机单任务约束。
- 风险：Student 资源竞争、输出/许可 checkout 并发以及两个 Job Object 同时运行；不会扩大
  命令面，但会降低无人值守确定性。
- 处置：submit 在启动前创建 `Global\AirJetAnsysAutomation-OneJob` 固定名 Windows event；
  `Global` 跨 Windows session 生效；若对象已存在立即
  `BLOCKED_ONE_JOB_AT_A_TIME_CROSS_PROCESS`。handle 冻结进 Job，只有任务真正终态才关闭；
  server 异常退出时 Windows 关闭进程全部 handle，对象随之消失，不留下永久锁。
- 验证计划：suite 前后检查无残留 ANSYS/MCP；负测试并行启动第二个固定 profile，必须在
  进程创建前被拒绝。
- Windows 候选测试：同一 server 内第二次 acquire 被拒绝、释放后可重新 acquire；两个独立
  SSH/Python 进程同时竞争时第二个也被拒绝。现场进程显示 SSH 为 Session 0、可见 Codex 为
  Session 1；代码已使用 `Global`，但没有为测试临时注册 Scheduled Task 或注入 GUI 进程，
  因此实际跨 session acquire/release 仍记为未直接观察。
- T0 suite 后检查：签名重试结束后 SpaceClaim/Workbench/Mechanical/Fluent 自动化相关进程
  数量为 0，说明本次四任务串行运行没有留下长尾进程；这不替代尚未直接观察的 Session 0/1
  跨 session 竞争测试。
- 状态：CODE_AND_CROSS_PROCESS_PASS_CROSS_SESSION_NOT_DIRECTLY_OBSERVED

## REAL-20260714-014：Fluent 版本显示与异步退出造成首次 T0 误判和长尾进程

- Stage/task：PyFluent T0 / 首次 deterministic suite
- 实际：health=`SERVING`，settings/TUI 均存在，`get_fluent_version()` 返回类型为官方
  `FluentVersion`，其字符串显示为 `Ansys Fluent 2026 R1`。旧断言在显示字符串里搜索
  `26.1/261`，因此写出 `FAIL_DIRECT / CONTROL_ASSERTION_FAILED`。`solver.exit()` 默认
  `wait=False`，返回后 Fluent/Cortex/MPI 子进程仍存活；Job Object 正确保持 RUNNING，没有把
  Python 根进程退出 0 误报为终态。
- 区分实验：Windows 实际 SDK 源码确认 `get_fluent_version() -> FluentVersion`，
  `FluentConnection.exit(timeout=None, timeout_force=True, wait=False)`；`wait` 可给秒数并在超时
  后 force exit。
- 根因：把人类显示文本当版本协议；同时没有为本地 Fluent 退出设置 bounded wait。高置信度。
- 处置：版本断言改为对象等于 `pyfluent.FluentVersion.v261`，同时记录 `.value`；launch 使用
  `cleanup_on_exit=True`，finally 使用 `exit(timeout=30, timeout_force=True, wait=60)`。MCP
  watchdog 与 Job Object 仍是外层 600 秒兜底。
- 对 Gate/论文主张的影响：首次 PyFluent 为真实 FAIL_CONTROL，不得改写；前三个 profile 的
  独立报告不受影响。修复后必须新 job ID 重跑，不能覆盖首次证据。
- 签名重试：commit `6265043003dfb44b2b694ef3e91cfd84d7cc832b` 上的新 job
  `ajm005-pyfluent-suite-20260714t175525010049z_2b301826-9e8a5ce26c8b` 返回
  `PROCESS_EXITED_0 / PASS_CONTROL`；类型化版本等于 `FluentVersion.v261`，`.value=26.1.0`，
  bounded exit wait=60 s；suite 后相关进程数为 0。
- 状态：CLOSED_BY_SIGNED_RETRY_FIRST_FAILURE_PRESERVED

## REAL-20260714-015：Workbench 显示名不等于完整模板键

- Stage/task：Workbench T0 / 首次 deterministic suite
- 实际：`GetTemplate(TemplateName="Static Structural")` 等无 solver 查询均提示模板不存在，
  但同一脚本随后用 `TemplateName="Static Structural", Solver="ANSYS"` 成功创建 `SYS` 并保存
  `.wbpj`。因此安装和结构模块存在，失败来自查询键。Fluent 的 UI 显示名是
  `Fluid Flow (Fluent)`，官方 ACT 示例的脚本键却是 `TemplateName="Fluid Flow"`。
- 证据：官方 Workbench 2026 R1 Scripting Guide 的结构示例明确给出 `Solver="ANSYS"`；官方
  ACT Workbench 示例使用 `GetTemplate(TemplateName="Fluid Flow")`。
- 处置：结构、Modal、Harmonic Response 使用 `Solver="ANSYS"`；Fluent 使用内部模板名
  `Fluid Flow`，报告仍用用户可读的 `Fluid Flow (Fluent)`。首次 FAIL_DIRECT 不改写，新 SHA
  profile 必须重跑。
- 对 Gate/论文主张的影响：只修正控制面键，不证明任何静力、模态、谐响应或 CFD 求解能力。
- 签名重试：commit `6265043003dfb44b2b694ef3e91cfd84d7cc832b` 上的新 job
  `ajm005-workbench-suite-20260714t175525010049z_2b301826-cf2bdb7d6029` 返回
  `PROCESS_EXITED_0 / PASS_CONTROL`；四个模板映射为 true 且 `.wbpj` 保存。仍未执行实际结构或
  CFD 求解。
- 状态：CLOSED_BY_SIGNED_RETRY_FIRST_FAILURE_PRESERVED

## REAL-20260714-016：T0 四路全绿仍不能写 005 工程能力通过

- UTC：2026-07-14T17:56:49Z
- Stage/task：005 / T0 signed retry
- 期望：先证明四个官方自动化入口可控，再开始工程小模型。
- 实际观察：SpaceClaim、Workbench、PyMechanical、PyFluent 四个固定 profile 全部
  `PROCESS_EXITED_0 / PASS_CONTROL`；完整 suite 为 `PASS_CONTROL_SET`。但 SpaceClaim 只建了
  一个方块，Mechanical 只做连接与算术，Fluent 只做 health/API 检查。
- 风险：若把“软件能启动、API 存在”直接写成 `PASS_005_CAPABILITY`，会跳过参数化/命名/传递、
  真实 FEA/CFD 求解、质量守恒和保存重开这些技术断言，并错误解锁正式整机 CAD。
- 处置：suite、run index、论文映射和项目状态统一保留
  `engineering_capability=NOT_RUN`、`P1_STAGE_GATE=NOT_RUN`；T1 拆成可独立终止和判定的 CAD、
  transfer、Mechanical、Fluent 能力探针。
- 对论文的影响：当前只允许写“验证了四个官方接口的确定性可控性”；不能写“验证了 AirJet
  模型或 ANSYS 工程求解能力”。
- 状态：CLOSED_BY_EVIDENCE_SEMANTICS_T1_REQUIRED

## REAL-20260714-017：跨 zsh→SSH→PowerShell 的 `$_.Name` 被外层错误解释

- UTC：2026-07-14
- Stage/task：005 T1 / 查找本机 v261 官方示例，只读资料定位
- 期望：递归筛选安装目录中的 SpaceClaim/Workbench 脚本和 XML。
- 实际观察：一条包含 PowerShell `Where-Object { $_.Name ... }` 的远程命令转义层次错误；外层
  shell 破坏了 `$_`，PowerShell 输出大量属性/语法错误。随后一次用 `cmd where` 处理含空格
  路径也因参数拆分失败。两次均为只读，没有启动 ANSYS、修改安装或读取许可内容。
- 根因及置信度：命令依次经过本机 zsh、SSH 远端命令行和 PowerShell parser，`$`、引号与空格
  有三层语义；高置信度。
- 处置：停止宽泛递归命令，改用已知 literal path、无 `$_` 的 `Select-String`，并用 `scp` 只取
  两个已定位官方样例到临时目录核对。后续复杂 PowerShell 应采用已审脚本/编码传输，不在一行
  命令中叠加三层插值。
- 对 Gate/论文主张的影响：没有工程能力运行，P1–P6 不变；该问题只属于复现基础设施现实。
- 状态：CLOSED_BY_LITERAL_PATH_AND_SCOPED_COPY

## REAL-20260714-018：CylinderBody 三点语义曾被静态误判（已纠正）

- UTC：2026-07-14
- Stage/task：005 T1 / SC-CAD-T1 发布前审查
- 初稿：入口三点为 `(10,5,1)`、`(10,5,0)`、`(11,5,0)` mm，并预期得到沿 z 的直径 2 mm
  圆柱。
- 当时的静态解释：发布前审查把本机 XML 的 `centerPoint/startPoint/endPoint` 短标签错误解释为
  “定义圆圆心、圆周起点、该圆周点的挤出终点”。初稿会混置半径和轴向，但这一轮审查提出的
  替代点组后来也被实跑推翻。
- 处置：在签名提交和 ANSYS 实跑前改为 `(10,5,0)`、`(11,5,0)`、`(11,5,1)`；最终仍由
  body 体积、bbox、入口面积及重开结果复核，而不是因 API 调用未报错就判 PASS。
- 对论文的影响：方法记录“同版本参数语义 + 解析几何指纹”的双重验证；没有生成产品结论。
- 后续纠正：第二次签名运行得到 `200 mm³ / zmin=1 / INLET=0`，推翻了上述静态解释。重新读取
  同机官方 `space_claim_geometry.py` 后确认实际向量语义是 `p1→p2` 为轴线、`p2→p3` 为半径；
  XML 的 `centerPoint/startPoint/endPoint` 短标签不足以单独确定几何。正确的 z 轴点组是
  `(10,5,0)`、`(10,5,1.1)`、`(11,5,1.1)`。旧判断不删除，作为“文档短描述必须被官方实例和
  实跑几何共同验证”的反例；完整运行证据见 REAL-20260714-022。第三次签名运行的 raw inlet
  `1.1π mm³`、union、bbox 和入口面断言均通过，确认纠正后的向量语义。
- 状态：CLOSED_BY_SIGNED_RETRY_FIRST_MISREAD_PRESERVED

## REAL-20260714-019：脚本重建参数变化不等于原生参数化

- UTC：2026-07-14
- Stage/task：005 T1 / 原生参数化硬门槛
- 初稿：依次创建 `16×5×2` 与 `16×6×2 mm` 临时块，验证体积从 160 变 192 mm³ 后删除，
  并把断言命名为 `parametric_geometry`。
- 发布审查：这只能证明 `SCRIPT_EQUIVALENT_TWO_BUILDS`；最终 `.scdocx` 没有已验证的 driving
  dimension/native parameter，也没有证明保存重开后参数仍可修改。若据此把
  `P1_CAD_TOOLCHAIN_READINESS` 写 PASS，会越过 005 的原生参数化硬门槛。
- 处置：断言改名为 `script_parameterization_equivalent`，报告显式写
  `native_parameterization=NOT_RUN` 与 `p1_cad_hard_gate=BLOCKED_NATIVE_PARAMETERIZATION`。
  CAD→Workbench 小链路即使全过也只写 `PASS_CAD_TRANSFER_SET`，P1 readiness 保持 BLOCKED。
- 拒绝的 workaround：不把“可以改 Python 常量”改写为“原生参数化”；不因急于开始整机 CAD
  而放宽 Gate。
- 下一步：通过同版本官方 API、受控 GUI record 或可审计 feature/parameter route 建立并重开
  真正 driving parameter，再用新 profile 关闭该硬门槛。
- 状态：OPEN_KNOWN_TOOLCHAIN_GAP_PARTIAL_T1_ALLOWED

## REAL-20260714-020：终态文件的现场哈希不能代替冻结 manifest

- UTC：2026-07-14
- Stage/task：005 T1 / MCP predecessor 证据链审查
- 初稿：下游提交时读取上游终态报告，现场计算源文件 SHA，复制后再计算目标 SHA。
- 审查发现：上游终态到下游提交之间，同一 OS 用户仍可同时改写报告与原生文件；复制前后相等
  只能证明“复制一致”，不能证明它仍是先前 suite 看见的产物。
- 处置：第一次 `artifact_manifest()` 在 MCP 内存中冻结完整 manifest；下游必须来自同一 MCP
  进程，并把每个 policy artifact 的当前 size/SHA 与冻结值比较。服务器同时核对 profile、case、
  commit、output root、probe、required assertions、P1 Gate 和许可参数标记，再生成只读 predecessor
  manifest。冻结后的改写会与内存快照不符并 fail-closed；第一次 manifest 之前的文件状态就是
  首次快照的权威输入，无法识别同一 OS 用户在冻结前已做的篡改。
- 残余边界：冻结前仍属于当前 OS-user trust boundary；脚本也仍以当前 OS 用户权限运行，MCP
  不是 OS sandbox。防线依赖签名 commit、脚本
  SHA、静态审查和冻结 handoff，而不是声称子进程无法读取其他用户可读文件。
- 状态：CLOSED_IN_CODE_PENDING_WINDOWS_NEGATIVE_TEST

## REAL-20260714-021：v261 `CreateByGroups` 不接受普通 Python list

- UTC：2026-07-14T18:52:33Z
- Stage/task：005 T1 / 首次 SC-CAD-T1 实跑
- Machine/operator：LAPTOP-LCCLM2HI / Mac Codex via SSH and fixed MCP
- run/job/profile：`AJM005_T1_CAD_SUITE_20260714T185233920643Z_14b42b18` /
  `...-6a64cc458c40` / `ajm005-spaceclaim-cad-t1-v1`
- 期望：创建三个 Named Selection 后用 group 名复核 cardinality。
- 实际观察：脚本先成功完成 5/6 mm 两次构建，解析体积为 160/192 mm³；随后
  `Selection.CreateByGroups(["INLET"])` 抛出 `TypeError: expected Array[str], got list`。
  SpaceClaim wrapper 进程退出 0，但 declared report 为 `FAIL_DIRECT`，所以 suite 正确判
  `FAIL_CAD_TRANSFER_SET`，Workbench 写 `BLOCKED_UPSTREAM` 且未启动。
- 原始证据：完整 suite JSON SHA-256
  `154b3174653df43f273fc8621d1ea6ed9bdaeaac032c28478c2cafa35bd011c5`；MCP stderr SHA-256
  `ff61e776c064942549a3d68bc543f2a9133adcaf97646dc4d9cbdf8f67759304`；declared report SHA-256
  `7a13ce774598ac076002af46a21bd5af73ca0779337d592d990967c8c27581e7`。
- 根因及置信度：v261 XML 签名为 `CreateByGroups(System.String[])`；Python list 没有被该
  script host 隐式转换为 .NET string array。错误文本与签名一致，高置信度。
- 处置：显式 `from System import Array, String`，统一用
  `Array[String]([name])` 调用；重新计算 profile script SHA，并用新签名 commit/new job 重跑。
- 拒绝的 workaround：不跳过重开后的 group 检查，不因 wrapper exit 0 写能力 PASS，不手改旧报告。
- 对 Gate/论文主张的影响：首次运行证明脚本等效参数变化可执行，但全部 partial CAD capability
  仍 FAIL；P1 readiness BLOCKED，P1–P6 NOT_RUN。
- 状态：CLOSED_IN_CODE_PENDING_SIGNED_RETRY_FIRST_FAILURE_PRESERVED

## REAL-20260714-022：Array 修复后入口未进入最终流体，STEP 回读为空

- UTC：2026-07-14T19:03:12Z
- Stage/task：005 T1 / 第二次 SC-CAD-T1 实跑
- Machine/operator：LAPTOP-LCCLM2HI / Mac Codex via SSH and fixed MCP
- run/job/profile：`AJM005_T1_CAD_SUITE_20260714T190312403805Z_81461dd4` /
  `...-a3fdb92e5107` / `ajm005-spaceclaim-cad-t1-v1`
- 期望：三段负体积 union 为 `203.14159265358978 mm³`，bbox 从 `z=0` 到 `3 mm`，并能
  创建 `INLET/OUTLET/WALLS`、原生重开和 STEP 回读。
- 实际观察：`.NET Array` 修复有效，脚本越过首次 TypeError 并完成保存/重开。Boolean 返回
  `Success=true`，但最终体积为 `200 mm³ = 192 + 8`、bbox `zmin=1 mm`、`INLET=0`；面清单
  没有面积约 `π mm²` 的入口圆面。`piece_count=1`、`is_closed=true` 只描述剩余 body，不能证明
  设计中的入口存在。原生文件忠实重开了同一错误几何，所以 aggregate `native_reopen=false`。
  STEP 是 15137-byte、以 `ISO-10303-21` 开头的非空文件，但单参数
  `DocumentOpen.Execute(step_path)` 后根层 `Bodies.Count=0`；该轮没有记录全层 body 数。
- 原始证据：完整 suite JSON SHA-256
  `5a1197520c39a3b80434e078d55519c5c1b6a5bc3c96910e3fa2dd90dc0a726`；MCP stderr SHA-256
  `224ba0e83c60418b25577548b620ed783a3c6cf6b4cc37833078684f574718ad`；declared report SHA-256
  `112d510dfb088c24251ee2275256b5b3641f3e372d80649b57e9d405b39b191e`；STEP SHA-256
  `d04b26e497047e22a90db1da4cbef2fbbc7ed7ea2ef41b9ee8026b58b7d0a847`。
- 根因分层：入口没有进入最终几何为运行直接证据。运行后对照本机官方 v261
  `space_claim_geometry.py`，确认 `p1→p2` 定义轴线、`p2→p3` 定义半径；旧点组实际建立沿 x
  而非沿 z 的圆柱，和体积/bbox/面证据一致，圆柱点语义根因为高置信度。STEP 文件内已确认有
  `MANIFOLD_SOLID_BREP`，所以它不是零字节或完全没有 B-rep 记录的导出；这仍不证明实体拓扑完整
  或可被 v261 正确导入。根层 body 为 0 仍不能区分“实体在子组件”与“导入没有落地”，需检查
  全层 body。
- 最小修正/区分实验：用正确三点建立 `z=0→1.1 mm` 圆柱，Boolean 前断言其原始体积
  `1.1π mm³` 与 bbox `[9,4,0]→[11,6,1.1] mm`；0.1 mm overlap 后 union 解析体积仍为
  `192 + π + 8 mm³`。STEP 保持相同 open，只把检查改为官方 `GetAllBodies()` 并同时记录根层、
  component 和全层计数；若全层仍为 0，再以独立新 job 检验显式 ImportOptions。只有新签名运行的
  体积、bbox、面和回读断言通过，才能把这两条解释提升为已关闭。
- 拒绝的 workaround：不因 `Combine.Success` 或文件非空写 PASS；不把闭合但缺入口的 body 送入
  Workbench；不把 Workbench 的 `BLOCKED_UPSTREAM` 写成执行失败。
- 对 Gate/论文主张的影响：本轮最多证明几何指纹成功阻止错误模型下传。三段 union、完整 Named
  Selections、STEP 可移植性、CAD→Workbench 传递均未通过；P1 readiness BLOCKED，P1–P6 NOT_RUN。
- 后续签名结果：commit `74e855733613baa80d7d821b961c629268f4ba59` 的第三轮确认正确 raw
  inlet、`192+π+8` union、`INLET/OUTLET/WALLS=1/1/11` 和原生重开全部通过；几何问题关闭。
  STEP `GetAllBodies()` 进入唯一候选后暴露新的 `TrimmedSpace.PieceCount` 类型假设，转入
  REAL-20260714-023，不把它倒写成本轮 STEP PASS。
- 状态：CLOSED_GEOMETRY_BY_SIGNED_RETRY_STEP_SUPERSEDED_BY_REAL023

## REAL-20260714-023：STEP 导入返回 TrimmedSpace，通用指纹错误假设 PieceCount

- UTC：2026-07-14T19:20:46Z
- Stage/task：005 T1 / 第三次 SC-CAD-T1 实跑
- Machine/operator：LAPTOP-LCCLM2HI / Mac Codex via SSH and fixed MCP
- run/job/profile：`AJM005_T1_CAD_SUITE_20260714T192046219114Z_006c64df` /
  `...-ad5b474ac3ed` / `ajm005-spaceclaim-cad-t1-v1`
- 已关闭的上一轮问题：raw inlet 为 `3.455751918948766 mm³ ≈ 1.1π`，bbox 为
  `[9,4,0]→[11,6,1.1] mm`；union 为 `203.14159265358984 mm³ ≈ 192+π+8`，bbox
  `[2,2,0]→[20,8,3] mm`、`PieceCount=1`、`IsClosed=true`；Named Selections 为
  `INLET/OUTLET/WALLS=1/1/11`。原生重开得到相同体积、bbox、拓扑和 group cardinality。
- 实际失败：STEP `GetAllBodies()` 已进入唯一候选分支，候选 `Shape` 的运行时类型为
  `TrimmedSpace`；通用 `body_fingerprint` 随后访问 `.PieceCount`，抛
  `AttributeError: 'TrimmedSpace' object has no attribute 'PieceCount'`。因此 STEP 指纹未完成，
  declared report 仍为 `FAIL_DIRECT`，Workbench 仍 `BLOCKED_UPSTREAM`。
- 根因及置信度：同一个 DesignBody 风格对象的 `Shape` 并不保证是 native `Modeler.Body`；本机
  v261 API 将通用 `ITrimmedSpace` 定义为有限三维区域并保证 Volume/SurfaceArea 等属性，但没有
  `PieceCount/IsClosed`。代码把类型特定属性当成通用属性是高置信度根因；没有证据证明 STEP
  几何损坏或导入失败。
- 最小修正：同版本 API/反射确认 `GetAllBodies()` 返回 `IDesignBody`；occurrence `body.Shape`
  只保证 `ITrimmedSpace`，适合放置后的 bbox/volume，而 `body.Master.Shape` 是提供
  `PieceCount/IsClosed/IsManifold` 的 `Modeler.Body`。第四版分别从 occurrence 和 master 取得
  几何/拓扑，仍硬性要求单片、闭合、manifold，不因类型适配而降低 STEP Gate。artifact size/SHA
  也移到保存后立即写入，避免后续重开异常丢失已生成文件的身份。
- 原始证据：suite JSON SHA-256
  `d0abda66ef330b3a5e742e674e7abd07cb36e82a80465ab4098ccd7688c4f900`；report SHA-256
  `c7ba37fc8e314dcd43bc59a7882c6b64d99d00aa1cb317edab85c35c6c6f9717`；STEP SHA-256
  `ea3fce9bf63a061bc8263446ebb8c6b071cb3ab8a3aad7b30be317be78e94bda`。19:21:43Z 现场
  ANSYS 相关进程数为 0。
- 对 Gate/论文主张的影响：本轮允许记录“解析 union、Named Selections 和原生重开通过”；不能
  写 STEP 可移植性、CAD transfer、Volume Extract API、原生 driving parameter 或 005/P1 PASS。
- 后续签名结果：commit `9652054cf6d84467dce877342eb032df12c375a6` 的第四轮用
  occurrence/master 分层指纹确认 STEP 为唯一全层 body、单片、闭合、manifold，且体积/bbox/面数
  与原生模型一致；STEP 类型适配问题关闭。新的 Workbench attach 失败转入 REAL-20260714-024。
- 状态：CLOSED_BY_SIGNED_RETRY_WORKBENCH_ATTACH_MOVED_TO_REAL024

## REAL-20260714-024：SpaceClaim partial CAD 首次通过，Workbench 无法附加原生 geometry structure

- UTC：2026-07-14T19:33:05Z
- Stage/task：005 T1 / 第四次 CAD transfer suite
- Machine/operator：LAPTOP-LCCLM2HI / Mac Codex via SSH and fixed MCP
- run/jobs/profiles：`AJM005_T1_CAD_SUITE_20260714T193305538549Z_ff27aa8a`；SpaceClaim
  `...-e4a23016e42d` / `ajm005-spaceclaim-cad-t1-v1`；Workbench `...-c8c7b3931516` /
  `ajm005-workbench-transfer-t1-v1`。
- 已关闭的上一轮问题：SpaceClaim 七项断言全部为 true。STEP 回读得到 `root bodies=0`、
  `components=1`、`all bodies=1`；occurrence `TrimmedSpace` 提供 `203.14159265358984 mm³` 和
  `[2,2,0]→[20,8,3] mm`，`Master.Shape` 的 `Body` 提供 `PieceCount=1`、`IsClosed=true`、
  `IsManifold=true`，faces=13。SC declared report 首次为 `PASS_PARTIAL_CAD_CAPABILITY`。
- 实际失败：MCP 把精确 predecessor report、`.scdocx` 与 STEP 冻结复制给 Workbench；commit、
  job、profile、report/native SHA 全部匹配，`predecessor_identity=true`。脚本调用
  `Geometry.SetFile` 与 `UpdateUpstreamComponents()` 后，在 `model_component.Refresh()` 报“无法附加
  geometry structure”。Workbench phase=`FAILED_PROCESS`、exit=2、declared report=`FAIL_DIRECT`。
- 控制流解释：直接失败只有 geometry attach。Named Selection inspection、Mechanical 粗网格和
  project save 都没有开始；报告中的三个 false 布尔字段应解释成 `NOT_REACHED`，不能伪造为三次
  独立功能测试失败。
- 原始证据：外部 suite JSON SHA-256
  `049d78b5c30db084857dd332094a1d1855dfe0f3828a23ec5a8a95cdaeff51d9`；MCP stderr SHA-256
  `9dcedb2085c4705915d2e9aee012219f11e07614cac2bd250175d11abf405cca`；SC report SHA-256
  `e15d108f72807014f84f363b700682888c0dd02bc9bbdccaf7961ef6c6da47ac`；WB report SHA-256
  `83c00e77bf21a227cc1a0a074bdfcac346a282ba7c498dc22e2a3862d6c16dae`；结束后
  2026-07-14T19:39:38.4726831Z 现场相关进程数为 0。
- 已排除/未排除：高置信度排除“拿错 predecessor”与“SC 自己不能重开该原生文件”；高置信度定位
  失败到 `Model.Refresh()`。尚不能区分 `.scdocx` 是否不是该 Workbench Geometry attach 路线的
  支持格式、是否需要不同 geometry container/transfer 路线，或 update/refresh 次序是否错误；也
  不能据此宣称文件损坏或 Mechanical 缺少能力。
- 最小区分实验：先核对同机 v261 官方 journal/API；每个新签名 suite 只改变一个 attach/import
  假设，并把 `SetFile`、`UpdateUpstreamComponents`、`Refresh` 的到达状态分别写入 declared report。
  STEP 可用来诊断 Workbench 是否能消费几何，但 STEP 不承诺 Named Selections，不能单独关闭最终
  transfer Gate。
- 现实教学：`文件身份正确 ≠ 生产者能重开 ≠ 消费者能附加 ≠ 下游语义和网格通过`。suite 是这些
  必要条件的合取；保留 SC partial PASS 不会让整套 suite 变成 PASS。
- 对 Gate/论文主张的影响：允许写 SpaceClaim 签名小模型已通过脚本重建、解析 union、命名边界、
  原生重开和 STEP 几何回读；不得写 Workbench transfer、Named Selection transfer、Mechanical
  inspection、粗网格、project save、Volume Extract API、原生 driving parameter、005 或 P1 PASS。
- 状态：OPEN_WORKBENCH_GEOMETRY_ATTACH_ROUTE_PENDING_SIGNED_RETRY_SC_PASS_PRESERVED

## REAL-20260714-025：Model.Update(AllDependencies=True) 未关闭同一 attach 失败

- UTC：2026-07-14T19:47:56Z
- Stage/task：005 T1 / 第五次 CAD transfer suite
- run/jobs：`AJM005_T1_CAD_SUITE_20260714T194756378277Z_87034366`；SC
  `...-8dc6d985f23d`；WB `...-04b25837c835`。
- 单变量假设：第四轮可能因 `Model.UpdateUpstreamComponents(); Model.Refresh()` 的更新顺序导致
  attach 失败。保持 `.scdocx`、Static Structural、Geometry `SetFile`、Named Selection import
  属性、predecessor 身份和 Mechanical 检查不变，只替换为
  `Model.Update(AllDependencies=True)`。
- 实际结果：SC 七项再次 PASS。WB predecessor identity PASS；`geometry_set_file=RETURNED`、
  `model_update_all_dependencies=CALLED` 但未 RETURNED；错误仍为 Static Structural Model 更新失败，
  无法附加 `.scdocx` geometry structure。`model_refresh=NOT_CALLED_BY_ROUTE`，model container、
  Mechanical inspection、mesh 和 project save 全部 `NOT_REACHED`。
- 原始证据：suite SHA-256
  `cc64f6e8da11d01b45e1eb412753abc816be5c58ef1b2e7772e197216756568b`；MCP stderr SHA-256
  `2de5b54aa653cc5b72be38c77011ed57c54d2d52073648066b289b7b0420f5a4`；SC/WB report SHA-256
  分别为 `654518f1204e2579a3047a76f4d8f2c21fe4919bb468751d129ba5760baf897b` 和
  `21389b0defc6719f42cdb069a32cfc8c6aac1f3a06133893b65b2701dd6c85c6`；
  2026-07-14T19:51:21.6178890Z 现场相关进程数为 0。
- 结论边界：新运行排除了“只有旧 update/refresh 顺序导致失败”的窄假设；它没有证明 `.scdocx`
  在 v261 所有 Workbench 路线都不受支持，也没有测试 Mechanical 本身。官方 ReaderFilter 仍列出
  `*.scdoc;*.scdocx`，所以不能用本次失败反推格式全局不支持。
- 下一最小实验：保持 `.scdocx` 不变，改用同机官方 sample 的独立 Geometry source 与
  `TransferData(TargetComponent=Static.Geometry)` 架构；不得在同轮同时换 STEP、`.scdoc` 或
  DesignModeler，否则无法归因。
- 对 Gate/论文主张的影响：SC partial PASS 可复现；完整 transfer set 仍 FAIL。P1 readiness
  BLOCKED，P1–P6 NOT_RUN。
- 状态：CLOSED_UPDATE_ORDER_HYPOTHESIS_TRANSFERDATA_ROUTE_PENDING

## REAL-20260714-026：普通 Geometry component 的 TransferData 组合被 v261 拒绝

- UTC：2026-07-14T19:57:25Z
- Stage/task：005 T1 / 第六次 CAD transfer suite
- run/jobs：`AJM005_T1_CAD_SUITE_20260714T195725871623Z_d3a5b5c3`；SC
  `...-9aaa10ed5333`；WB `...-94beffc74bdc`。
- 单变量假设：保持 `.scdocx`、Named Selection import 属性、Model update 和验收不变，把文件从
  Static system 内直接 attach 改为独立 Geometry source，再调用
  `source_component.TransferData(TargetComponent=static_geometry_component)`。
- 实际结果：source system、source `SetFile` 和 target Static system 均 RETURNED；
  `TransferData=CALLED` 但未返回，v261 原文是“几何结构无法使用组件几何结构。”Model update、
  Mechanical inspection、mesh 和 project save 均 `NOT_REACHED`。WB 约 16.1 秒结束，不同于前两轮
  约 160 秒的 attach 尝试。
- 根因边界：`TransferData` 是真实 Component API，但普通 Geometry component→Static Geometry
  component 的具体组合在本机被明确拒绝。方法存在不等于任意 component 类型兼容；尚未测试
  standard Geometry 的 `ComponentsToShare` 路线。
- 原始证据：suite/MCP SHA-256 分别为
  `a23aadc8539f4fcf95958343e2edbb86a06d3fd3fea2741061309c38a85e6b0c` 和
  `52ac612bbfb82df1c23d4787cf341cd449e646c2165ef6f907cb3da916284b37`；SC/WB report SHA-256
  分别为 `29f59c1f0b57644cada442c866ae1db87cd13fc1bcd3cf0628f2ea3b3f2588cc` 和
  `04547dc9c2e7eee8398fdcad87fcc88cddb4a89e27e8160f3cfb74f2fedac505`；
  2026-07-14T19:58:27.4612580Z 现场相关进程数为 0。
- 下一最小实验：改用本机官方 `StaticStructuralANSYS.wbjn` 的
  `CreateSystem(ComponentsToShare=[source_component])` 和 `GetGeometryFileAndSaveData()` 架构；
  不同时修改文件格式、更新 API、Mechanical 检查或断言。
- 对 Gate/论文主张的影响：SC partial PASS 再次可复现；Workbench geometry transfer 仍 FAIL，
  P1 readiness BLOCKED，P1–P6 NOT_RUN。
- 状态：CLOSED_INCOMPATIBLE_TRANSFERDATA_COMBINATION_COMPONENTS_TO_SHARE_PENDING

## REAL-20260714-027：ComponentsToShare 越过兼容性检查，但 Component Update 仍 attach 失败

- UTC：2026-07-14T20:04:15Z
- Stage/task：005 T1 / 第七次 CAD transfer suite
- run/jobs：`AJM005_T1_CAD_SUITE_20260714T200415495276Z_fcec8c5a`；SC
  `...-7be4e428a252`；WB `...-eaaa26a0fe20`。
- 单变量假设：用同机官方 `StaticStructuralANSYS.wbjn` 的
  `CreateSystem(ComponentsToShare=[source_component])` 和 source
  `GetGeometryFileAndSaveData()` 替换第六轮不兼容的 `TransferData`；其余保持不变。
- 实际结果：source system/SetFile、shared Static system 和 GetGeometryFileAndSaveData 全部
  RETURNED，证明官方 share 数据流越过第六轮兼容性拒绝。随后保持不变的
  `Model.Update(AllDependencies=True)=CALLED` 但未返回，再次报告无法附加 `.scdocx` geometry
  structure；Mechanical inspection、mesh、project save 均 NOT_REACHED。
- 根因边界：不能再把失败归咎于普通 component 的 `TransferData` 兼容性；当前直接失败位于 share
  route 后的 downstream Model Component update。官方同机 journal 此处用 Model container
  `Refresh()`，两种更新 API 在 share topology 中尚未对比。
- 原始证据：suite/MCP SHA-256 分别为
  `d7663dfeed1f17731b6c5c2656495126a66a748dc0fd0a482bfff3fbee9c80d2` 和
  `091913fced46e9dd99f051dbfd8b68ad24adc05820bf508bc55f0a72d4883d58`；SC/WB report SHA-256
  分别为 `b7706e27fdff8c17e48021ca1ed242713114e0e6cea5d96dfadeb75dc6d10f06` 和
  `587e0a04d4a56ba2e2645eb1bf7c06097ee2e6c3f9c2bbf8d79c91494b2320c8`；
  2026-07-14T20:07:45.2710015Z 现场相关进程数为 0。
- 下一最小实验：保持 share/save-data route 不变，只用同机官方 Model container `Refresh()` 替换
  Component `Update(AllDependencies=True)`；若仍 attach 失败，再单独测试显式
  `Edit(Interactive=False, IsSpaceClaimGeometry=True)`。
- 对 Gate/论文主张的影响：官方 share topology 建立成功，但 geometry transfer 仍 FAIL；SC
  partial PASS 可复现，P1 readiness BLOCKED，P1–P6 NOT_RUN。
- 状态：OPEN_OFFICIAL_MODEL_CONTAINER_REFRESH_PENDING

## REAL-20260714-028：官方 Model container Refresh 仍无法附加 .scdocx

- UTC：2026-07-14T20:13:03Z
- Stage/task：005 T1 / 第八次 CAD transfer suite
- run/jobs：`AJM005_T1_CAD_SUITE_20260714T201303434255Z_6dbb18a9`；SC
  `...-a2d230d5fb6d`；WB `...-3b17344528db`。
- 单变量假设：保持已越过的 `ComponentsToShare` 与 save-data 路线，只把下游
  `Model Component.Update(AllDependencies=True)` 换成同机官方 journal 的 Model container
  `Refresh()`。
- 实际结果：Model container RETURNED，`Refresh=CALLED` 但未返回；仍报告无法附加本轮精确
  predecessor `.scdocx`。Mechanical inspection、mesh、project save 仍 NOT_REACHED。
- 结论边界：share topology 中两种更新 API 都出现同一 attach 失败，update API 选择这一假设关闭；
  仍不能断言 `.scdocx` 格式全局不支持，因为 Workbench 管理的 SpaceClaim editor 尚未显式打开该
  文件。
- 原始证据：suite/MCP SHA-256 分别为
  `b6c8bd3532e9c7a0e75127e8d7662b31523b23cfe1ac9d22c098357a7aef3195` 和
  `9dcedb2085c4705915d2e9aee012219f11e07614cac2bd250175d11abf405cca`；SC/WB report SHA-256
  分别为 `8825b8f09e066a4a1aa9fd0ddeab460963724d67d8a8714d04a9b02297684e7c` 和
  `50e877c2e4e716b8a33b4d82347b20d41a69fdb241222b59efe72357b250f067`；
  2026-07-14T20:16:31.3344349Z 现场相关进程数为 0。
- 下一最小实验：保持 share/refresh 不变，只在 source SetFile 后调用
  `Edit(Interactive=False, IsSpaceClaimGeometry=True)` 并 `Exit()`；到达标记区分 Edit/Exit、
  save-data 与 Refresh。
- 对 Gate/论文主张的影响：geometry transfer 仍 FAIL；SC partial PASS 可复现，P1 readiness
  BLOCKED，P1–P6 NOT_RUN。
- 状态：CLOSED_SHARE_UPDATE_API_HYPOTHESIS_EXPLICIT_SPACECLAIM_EDIT_PENDING

## REAL-20260714-029：显式 SpaceClaim Edit/Exit 通过，下游 Model 仍无法附加

- UTC：2026-07-14T20:22:14Z
- Stage/task：005 T1 / 第九次 CAD transfer suite
- run/jobs：`AJM005_T1_CAD_SUITE_20260714T202214703116Z_110addbb`；SC
  `...-0685330b1eba`；WB `...-e99499f00453`。
- 单变量假设：保持 share/save-data/Refresh 不变，只在 source SetFile 后显式
  `Edit(Interactive=False, IsSpaceClaimGeometry=True)` 并 `Exit()`。
- 实际结果：Edit 和 Exit 都 RETURNED；source、share、save-data 也 RETURNED。WB 总时长约
  280.3 秒，随后 Model Refresh 仍无法附加同一 `.scdocx`，Mechanical inspection、mesh、project
  save NOT_REACHED。运行后相关进程数为 0。
- 结论边界：Workbench 管理的 SpaceClaim editor 能打开/关闭该文件，不等于 downstream Model 能
  attach；不能把错误归为文件完全不可读或 CAD editor 根本无法启动。native attach 路径在 editor
  materialization 后仍失败。
- 原始证据：suite/MCP SHA-256 分别为
  `178fabef7718eb1be35db5d08ef6b793adf2eb871e946ca085c062208149864a` 和
  `8b0cf6d7392dbfa2bb71c0303037b327d9741c7936597b78d6511235b7e86127`；SC/WB report SHA-256
  分别为 `d2719ffa3ec38f97553a820bdf915040fe1035152ffbd8d3671e9d93dc43debf` 和
  `19fce639167035b661402784e9b1c7dc8876e7bb1cd46b20d780a2c906605387`；
  2026-07-14T20:28:03.3201340Z 现场相关进程数为 0。
- 下一最小实验：用本轮生产者已回读验证的 STEP 替换 `.scdocx` 作为 Workbench source，测试几何
  body 与 mesh 管线；明确把 Named Selection transfer 预期保留为 false，不得以 STEP 几何通过
  宣布完整 CAD transfer PASS。
- 对 Gate/论文主张的影响：native `.scdocx` downstream attach 仍 FAIL；SC partial PASS 可复现，
  P1 readiness BLOCKED，P1–P6 NOT_RUN。
- 状态：OPEN_STEP_DIAGNOSTIC_TO_ISOLATE_MECHANICAL_PIPELINE

## REAL-20260714-030：STEP 几何、Mechanical 粗网格与 Workbench 项目通过诊断，但上游三组语义为 0

- UTC：2026-07-14T20:35:27Z
- Stage/task：005 T1 / 第十次 STEP 管线诊断
- run/jobs：`AJM005_T1_CAD_SUITE_20260714T203527395289Z_f90b26f2`；SC
  `...-3df5c11853cd`；WB `...-f87db5b98356`；签名 commit
  `6f828feaeaee3f61278a0d3198156592529cc7a7`。
- 单变量假设：相对已经到达 `ComponentsToShare`、save-data 与 Model container `Refresh()` 的
  native baseline，只把冻结 source 从 `.scdocx` 换为同轮生产者已回读验证的 STEP；不调用
  SpaceClaim Edit，并把全部 native transfer canonical assertions 保持 false。
- 实际到达：STEP predecessor identity、source system/`SetFile`、`ComponentsToShare`、
  `GetGeometryFileAndSaveData()`、Model container/`Refresh()`、Mechanical inspection 与 project
  save 全部 RETURNED。
- 诊断观察：Mechanical 得到 1 个 body（`spaceclaim_cad_t1|AJM005_T1_FLUID`），1 mm 粗网格为
  1063 nodes / 513 elements，`workbench_transfer_t1.wbpj` 已保存；但
  `INLET/OUTLET/WALLS` 的对象数和实体数均为 `0/0/0`。
- 为什么进程退出码仍为 2：这是预设的 diagnostic guard，不是 mesher crash。脚本只把 body、mesh、
  project 观察写入 `diagnostic_result`；canonical assertions 除 predecessor identity 外全部固定为
  false，并以 `STEP_DIAGNOSTIC_ROUTE_CANNOT_CLOSE_NATIVE_TRANSFER_GATE` fail closed。
- 高置信结论：同机 Workbench→Mechanical 几何消费、粗网格和项目保存管线本身可用；前九轮的
  失败范围因此收窄到 native `.scdocx` attach/semantic bridge，而不是 Mechanical 或网格整体不可用。
- 不能外推：本轮 STEP 没有携带三组上游语义，不能据此宣称所有 STEP 导出器都必然丢名称，也不能
  宣称 native Named Selection transfer、native driving parameter 或 P1 readiness 通过。
- 原始证据：suite/MCP SHA-256 分别为
  `44cf146552f2eb04d5592337da7555e286f4dfa67b396bd5489fad5425630085` 和
  `ce2f98dd4139f3315be47b3d6496a65be124407b8b68577290ed8f5c8ee218bd`；SC/WB report SHA-256
  分别为 `699ca4555cb62d41b407acf61354022cfab40c897288fe612edb54f4528f2d81` 和
  `580f6927809bf765d2f502dafe5c5a60962e67824142b7aaee8e56c2907b2964`；STEP/inspection/project
  SHA-256 分别为 `9154a265bd28204ebaa2fc61f446a8378fe53b856ff25c08ec824f825357213e`、
  `f2948bda7a9a512d7f4f2a87bdf74f90c065fa5318438979956854419d3ebc54`、
  `bdb3165331091483e2cb90a2b3d6b2d734e98748ac2eed4bf8d14851fc744b20`；
  2026-07-14T20:36:44.5588359Z 现场相关进程数为 0。
- 采取的下一路线：冻结 STEP 与 hash-bound semantic sidecar，在 Mechanical 按面几何、邻接和容差
  唯一匹配后确定性创建 `INLET/OUTLET/WALLS`。该能力必须称 semantic reconstruction，不能称
  native transfer；还要做 0 match、multiple match、重叠、覆盖不全和 sidecar SHA 错的负向测试。
- 对 Gate/论文主张的影响：SC partial PASS 可复现；STEP body/mesh/project 只获诊断 PASS；native
  attach、Named Selection transfer 与 native driving parameter 仍阻塞；P1 readiness BLOCKED，
  P1–P6 NOT_RUN。
- 状态：CLOSED_STEP_PIPELINE_DIAGNOSTIC_SEMANTIC_RECONSTRUCTION_PENDING

## REAL-20260714-031：运行前审查阻止 semantic reconstruction 污染 native transfer 合同

- UTC：2026-07-14T21:00Z（设计/静态审查阶段）
- Stage/task：005 T1 / 第十一次实验实现前审查
- 发现的问题：最初的最小改法是在既有 `ajm005-workbench-transfer-t1-v1` 与
  `run_t1_cad_suite.py` 内加入 solver-side semantic reconstruction，同时把 canonical native
  assertions 保持 false。字段层面虽没有伪报，但 profile 身份和 runner 名称仍会把两类合同混在一起。
- 风险：未来只看 profile/run 名或聚合脚本的人可能把 reconstruction 的局部 PASS 误读为 native
  transfer 的进展；更严重时，后续维护者可能为“让 suite 变绿”而改写原生 transfer assertion。
- 采取的修正：保留/恢复 native profile 与 native runner；新增独立
  `ajm005-workbench-semantic-reconstruction-t1-v1`、独立 Workbench journal 和独立
  `run_t1_semantic_reconstruction_suite.py`。新 runner 的唯一成功态是
  `PASS_STEP_SEMANTIC_RECONSTRUCTION_DIAGNOSTIC`，且静态测试禁止其中出现
  `PASS_CAD_TRANSFER_SET`。
- 二次审查又发现 producer 的统一 `all(assertions)` 会让 sidecar 故障反向阻塞 native suite。现已把
  producer status 只绑定原有七项 CAD capability assertions，同时仍在 report 中记录第八项
  `semantic_sidecar`，并只让 semantic predecessor 强制要求它为 true。这样两条合同不仅名字分开，
  上游判定也不再反向耦合。
- 另一实现现实：Workbench journal 外层用 `%` 注入路径，Mechanical 内嵌脚本也用 `%d/%s` 格式化。
  若不把内层百分号写成 `%%`，外层会提前消费占位符。当前用 AST 提取、真实格式化并再次 compile
  内嵌脚本，避免等到 ANSYS 启动后才发现字符串插值错误。
- 证据边界：本条只证明合同和静态实现经过 fail-closed 审查；Windows/ANSYS 第十一次实跑仍
  `NOT_RUN`，不能写 semantic reconstruction PASS。
- 状态：CLOSED_BY_INDEPENDENT_PROFILE_AND_RUNNER_SPLIT_RUNTIME_PENDING

## REAL-20260714-032：sidecar 身份通过，但 Workbench 在算法执行前无法保存/附加 Mechanical 数据库

- UTC：2026-07-14T21:09:52Z
- Stage/task：005 T1 / 第十一次 STEP semantic reconstruction 真实运行
- run/jobs：`AJM005_T1_SEMANTIC_RECON_SUITE_20260714T210952085661Z_4c81dce0`；SC
  `...-22072d808273`；WB `...-fafc99fff120`；签名 commit
  `4f80fc6aa461163635fb7c4d9e0fece008ac0e66`。
- 期望：冻结 STEP、producer report、semantic sidecar 与 MCP manifest 身份一致后，在 Mechanical
  枚举 13 个面，执行四项负向 partition controls，唯一重建 `INLET/OUTLET/WALLS=1/1/11`，再生成
  粗网格并保存 project。
- producer 实际结果：SpaceClaim 19.954 秒正常退出。原有七项 partial CAD assertions 与新增
  `semantic_sidecar` 都为 true；STEP 为 17219 bytes、SHA-256
  `64b012aae023ca273e9c0de4bf308dff5f7900b6f346c8c134d48ea75ddd7662`；sidecar 为 4075 bytes、
  SHA-256 `00632d1dc50af445a7e286c9fd348b30b2f4299dc843f2b6a85ffb98b9ded7cd`。
- consumer 实际到达：predecessor identity、semantic sidecar identity、source `SetFile`、
  `ComponentsToShare`、save-data 与 Model container 都通过；`Model.Refresh()` 已调用。
- 原始错误短摘：Workbench 报告无法保存临时
  `...\\temp\\WB_admin_45360_3\\wbnew_files\\dp0\\global\\MECH\\SYS.mechdb` 的 Mechanical 数据库，
  并“无法附加几何结构”。WB 77.704 秒后 exit 2 / `FAIL_DIRECT`。
- 关键边界：Mechanical inspection、face enumeration、semantic reconstruction、negative controls、
  mesh 与 project save 全部 `NOT_REACHED`。所以本轮不是“算法分类失败”，而是 host 在算法入口前
  失败；不能依据 false assertions 评价面匹配规则本身。
- 原始证据：suite/MCP SHA-256 分别为
  `947b320ae0d1dd5bd4e05a4dae1e4cf4dcd8946580f24050d590d1c741a6683a` 和
  `59e96bf6b923a7ae0f89497cde9bc50dcd11a2df5fccf0347b17546d134d1894`；SC/WB report SHA-256
  分别为 `9613af45b8b7dfcd2eea77e7c21ce3f6f327df05c55e7e5056980ecfbc5c985c` 和
  `8b2a93c67c665f0474f12bfe7ac6b287786a5de931997914c179189de4e53574`；
  2026-07-14T21:14:35.8301194Z 相关进程数为 0。
- 路径检查：成功的第十次 WB job root 长 164，第十一次长 176；失败消息中的 `SYS.mechdb` 路径长
  237。Windows `LongPathsEnabled=1`，而第十次成功 job 内可观察到 253-character 文件，所以“超过
  Windows 260 字符”不是已证实根因。但某个 legacy Mechanical/Workbench 子组件仍可能使用更低的
  内部预算，且第十一次 case ID 在 job root 中出现两次；该假设置信度为低到中，必须单变量复测。
- 下一最小实验：只把 semantic runner case prefix 从 `ajm005-semantic-recon-` 缩为
  `ajm005-sem-`；profile、journal、STEP route、sidecar、assertions 和成功合同全部不变。若到达
  Mechanical，再评价单位转换、face API、负向 controls 和 1/1/11；若同点失败，关闭路径假设并
  转查项目名/临时目录/Workbench project materialization。
- 对 Gate/论文主张的影响：suite 为
  `FAIL_STEP_SEMANTIC_RECONSTRUCTION_DIAGNOSTIC`；所有 canonical native claims 为 false；P1
  readiness BLOCKED，P1–P6 NOT_RUN。
- 状态：OPEN_SHORT_CASE_ID_SINGLE_VARIABLE_RETEST

## REAL-20260714-033：短路径越过 attach，真实 partition 首次暴露 INLET 0 / OUTLET 1 / WALLS 12

- UTC：2026-07-14T21:21:01Z
- Stage/task：005 T1 / 第十二次 semantic reconstruction 短路径单变量复测
- run/jobs：`AJM005_T1_SEMANTIC_RECON_SUITE_20260714T212101506753Z_e604cf53`；SC
  `...-db1044630176`；WB `...-e3349c39cebd`；签名 commit
  `0fe714fdba9746aff2ef8cda23e5f2657e4d0f8e`。
- 唯一代码变量：runner case prefix 从 `ajm005-semantic-recon-` 缩为 `ajm005-sem-`；WB job root
  从 176 降到 154 字符。profile、Workbench journal、分类容差、sidecar 合同、MCP 和成功判定均
  未改变。
- 路径假设结果：上一轮 `Model.Refresh()` 在保存/附加临时 `SYS.mechdb` 时失败；本轮
  `Model.Refresh`、Mechanical inspection command、semantic reconstruction command 和 project save
  全部 RETURNED。短路径对 legacy Workbench/Mechanical path-budget sensitivity 提供强支持，但不
  等于证明所有相关组件都遵循或违反单一 `MAX_PATH=260` 规则。
- producer：SpaceClaim 21.454 秒正常退出，八项 report assertions 全 true；STEP SHA-256
  `2bb42781b556d5b378b7d8af222ef964cf388c9ff106346028a30030261711f9`，sidecar SHA-256
  `05b3689af6944b3b86e384152633aba29424a5354bc7fc0bc5abf6fac28327ea`。
- consumer 真实结果：Mechanical 已越过 body count、13-face count 与 pure partition control 段，
  在真实分区硬检查得到
  `SEMANTIC_RECONSTRUCTION_CLASS_COUNT_MISMATCH:{'INLET': 0, 'WALLS': 12, 'OUTLET': 1}`。
  因此未创建三组 Named Selections、未 mesh；仅保存 50593-byte 诊断 project。
- 新发现的可观察性缺陷：`face_details`、candidate IDs 与 `negative_controls` 已在内存形成，但旧脚本
  只在全部 validation 和 mesh 成功后才把它们合并进 inspection。失败文件只有 exception/traceback，
  所以 report 中 body/negative-controls 仍为 false。控制流可帮助定位，但不得把未保存的值补写为
  PASS。
- 原始证据：suite/MCP SHA-256 分别为
  `13049b1e65162f5329a335597131b20709dc2d02bd97192bcb1462e5c7bc90f1` 和
  `9c569072213a885ec5d65e36b6c221b1e0fe3592d585f8892ac1821160d177a7`；SC/WB report SHA-256
  分别为 `eb06f75055cd75ed46472d653503ae2433498dfd330c3e2d11680533a8ab0cc3` 和
  `89afc8b0f6fab5d631d9adeb0b45c5b4532e71223985a33d7458e86575ff0434`；inspection/project SHA-256
  分别为 `a0480879536f9fa9f7d2c46dcb5b6b9608b1c6d21821379d843d2329b8e682e4` 和
  `df443b0d41ba99fbe68ab85826d39ab4ae1641fec691248f03bf056153b9d7b1`；
  2026-07-14T21:22:09.1452895Z 相关进程数为 0。
- 下一最小实验：只增强 fail-path observability——在真实 partition validation 前把 `cad_unit`、
  body/face count、13-face centroid/area map、candidate IDs 与四项 negative controls 写入 inspection
  对象。分类规则和 `0.02 mm / 0.02 mm²` 容差保持不变；拿到实际 inlet 候选附近面值后再提出单变量
  修正。
- 对 Gate/论文主张的影响：suite 仍
  `FAIL_STEP_SEMANTIC_RECONSTRUCTION_DIAGNOSTIC`；semantic reconstruction/mesh false；canonical
  native claims 全 false；P1 readiness BLOCKED，P1–P6 NOT_RUN。
- 状态：OPEN_PREVALIDATION_FACE_MAP_OBSERVABILITY_RETEST

## REAL-20260714-034：入口中心精确匹配，但跨 STEP 的圆形区域面积锚点不稳定

- UTC：2026-07-14T21:31:01Z
- Stage/task：005 T1 / 第十三次 semantic reconstruction 失败面图观测
- run/jobs：`AJM005_T1_SEMANTIC_RECON_SUITE_20260714T213101596271Z_f453bd4b`；SC
  `...-5371050d9748`；WB `...-e53a6a0403db`；签名 commit
  `d107c40dbcc549cb75d43bb097b193cade73eb00`。
- 唯一实现变量：在 face-count guard 前保存 body/13-face map/candidate IDs，在 negative/real partition
  guard 前保存四项 negative controls；短路径、几何、classification 和 0.02 容差不变。
- 可观察性结果：body=1、faces=13、四项 negative controls 全 true、project save true 已成为显式
  report assertions；semantic reconstruction 与 mesh 仍 false。失败仍稳定复现 0/1/12。
- 入口直接对比：sidecar 期望 `[10,5,0] mm`、`3.141592653589787 mm²`；Mechanical face 44 为
  `[10,5,0] mm`、`2.0 mm²`。中心最大绝对差为 0，但面积绝对差为
  `1.141592653589787 mm²`，超过 0.02 面积容差约 57 倍，所以它被放入 WALLS。
- 相邻圆柱区域也发生变化：producer curved wall 约 `6.283185 mm²`，Mechanical face 45 为
  `5.832786321640015 mm²`，centroid 为 `[10.0506402,5,0.5016318] mm`；底面则由 producer 约
  `92.858407 mm²` 变成 Mechanical `94.0 mm²`。矩形 outlet 仍以 `[20,5,2] mm / 4 mm²` 精确匹配。
- 结论边界：这证明当前 `GeoFace.Area` 对包含圆形入口的跨 kernel face 不是稳定绝对锚点；没有证明
  STEP 丢失整个 inlet，也没有授权删除所有面积检查。13-face 总数仍保持，入口中心仍存在。
- 原始证据：suite/MCP SHA-256 分别为
  `f272f5d9afa2d087362565df1b4fb04bd7960c0cf231b226e2536e21489ad315` 和
  `51c1430cd0c136ff2fa95fc605d828ec8d5c9204df4443e524ba15577904948a`；SC/WB report SHA-256
  分别为 `801367ffcb411bc3d48a08995d983b04539fbf9044856d47a51c8d53ad7eba02` 和
  `91918d1894ed2b5e3b7df2e27df543eda9a0f2dbeb00a236fdea8ecb629e00b9`；inspection/project SHA-256
  分别为 `2f7303143fc5231672ee2808a5099dcb34353efec67d855586253fc5409b21a6` 和
  `b4099dc5d99f21ded82c159067f9026b6adcde39ffad2d6381ab42ec28bfd21b`；
  2026-07-14T21:32:05.9021874Z 相关进程数为 0。
- 下一最小实验：保持 classification 不变，只在每个 solver face 的失败面图增加 `SurfaceType`、
  edge count 与 centroid normal（API 不可用时保存 error/null，不猜值）。若 face 44 被观测为唯一
  planar、单边界环、z-normal 且中心匹配，下一轮再把入口合同单变量改成 centroid+topology anchor，
  area 退为诊断量；outlet 仍保持 centroid+area。
- 对 Gate/论文主张的影响：suite 仍 FAIL；Named Selections/mesh NOT_REACHED；canonical native
  claims 全 false；P1 readiness BLOCKED，P1–P6 NOT_RUN。
- 状态：OPEN_SOLVER_FACE_TOPOLOGY_OBSERVABILITY_RETEST

## REAL-20260714-035：入口 solver topology 已观测，支持用局部拓扑替代不稳定面积硬锚点

- UTC：2026-07-14T21:40:25Z
- Stage/task：005 T1 / 第十四次 solver face topology 观测
- run/jobs：`AJM005_T1_SEMANTIC_RECON_SUITE_20260714T214025424158Z_01e34e81`；SC
  `...-34da26e8e08a`；WB `...-64daf4bc354b`；签名 commit
  `63d84405522a9f07b8f629dceae3b24c798869d6`。
- 唯一变量：每个 face 记录 `SurfaceType`、edge count 与 centroid normal；三类 API 独立
  fail-soft，失败时保存 error/null。classification、0.02 容差、短路径和 Gate 未改。
- API 实测：13 个 face 的 surface/edge/normal 全部返回，所有 error 字段均 null。入口位置 face 44
  为 `GeoSurfacePlane`、2 edges、normal `[0,0,-1]`；其 centroid 仍为 `[10,5,0] mm`。相邻 face 45
  为 `GeoSurfaceCylinder`、4 edges；outlet face 54 为 plane、4 edges、normal `[1,0,0]`。
- 唯一性：在当前 13-face disposable fixture 中，`centroid=[10,5,0] + plane + 2 edges +
  abs(normal)=[0,0,1]` 只命中 face 44。它比不稳定的跨-kernel `area=π` 更适合作为 solver-side
  calibration anchor。
- 原始证据：suite/MCP SHA-256 分别为
  `628eb8ee3ff24ccef387d74e4efdfe0d879dd18e4a2c1e40b5597450bf456f48` 和
  `cc4721645dfb547cb240b52ebb551397713240113ae4d52029ef185b0f0f4512`；SC/WB report SHA-256
  分别为 `d751215238d836e7c21c5c07929723b150b361409cf07ed0a4eab304b0363462` 和
  `ec505cff47b43b546ca872a5a0800c2a28ee881f778ce93b59819931e94c2602`；inspection/project SHA-256
  分别为 `e81d748c698f779968975244521a37f5e2b7fdd4fc061b693ec7652ee44f2222` 和
  `d1848a313153ed93dc1e2e1bc13d57b9035e49698dac6b4b08c95fd81b418a34`；
  2026-07-14T21:42:11.2801302Z 相关进程数为 0。
- 下一最小实验：只把 INLET predicate 从 centroid+area 改为
  centroid+`GeoSurfacePlane`+2 edges+abs(z-normal)，并在 report 明确把 producer area 标为
  `DIAGNOSTIC_ONLY`、规则来源标为 `REAL-20260714-034/035`。OUTLET 继续 centroid+area，WALLS 继续
  complement，四项 negative controls 与 1/1/11 硬检查不变。
- 结论边界：该 topology 规则只校准 005 可删除 fixture，不是 AirJet 产品内部边界事实，也不关闭
  native transfer/parameterization Gate。
- 对 Gate/论文主张的影响：当前 suite 仍 FAIL；Named Selections/mesh NOT_REACHED；canonical native
  claims 全 false；P1 readiness BLOCKED，P1–P6 NOT_RUN。
- 状态：OPEN_INLET_SOLVER_TOPOLOGY_ANCHOR_SINGLE_VARIABLE_RETEST

## REAL-20260714-036：STEP 语义重建诊断通过，但原生传递与 P1 仍保持阻塞

- UTC：2026-07-14T21:49:44Z
- Stage/task：005 T1 / 第十五次 solver-side semantic reconstruction 单变量复测
- run/jobs：`AJM005_T1_SEMANTIC_RECON_SUITE_20260714T214944170151Z_221eac96`；SC
  `...-8166d373d69f`；WB `...-8332804d3611`；签名 commit
  `7a7f8e098adf51743c7121dbdfb25ebf4756336d`。
- 唯一算法变量：INLET 从 centroid+area 改为 centroid+`GeoSurfacePlane`+2 edges+
  abs(z-normal)。centroid tolerance、OUTLET centroid+area、WALLS complement、1/1/11 硬检查、
  四项 negative controls 和 Gate 均未改变。规则只作用于
  `DISPOSABLE_CAPABILITY_FIXTURE_ONLY`，来源为 REAL-034/035；producer inlet area 保留为
  `DIAGNOSTIC_ONLY`。
- producer/身份链：SpaceClaim 21.704 秒正常退出，八项 assertions 全 true；STEP 17197 bytes，
  SHA-256 `ca883117a85380a0bf1b0d8633a0d19d88e68f22db7528ff9effdbdb120debf6`；sidecar
  4064 bytes，SHA-256 `43beda43a8446e649bd360765e74584c39307ad33e781c3f64da4e1186adad84`；
  producer report/sidecar/STEP/MCP frozen manifest 身份全部通过。
- consumer：Workbench 31.357 秒正常退出。Mechanical 实测 1 body/13 faces，候选和重建 face IDs
  均为 INLET `[44]`、OUTLET `[54]`、WALLS `[45,46,47,48,49,50,51,52,53,55,56]`；创建前
  三个同名对象计数均为 0，创建后对象数为 1/1/1、实体数为 1/1/11。
- 负向与下游结果：0 inlet、multiple inlet、overlap、incomplete coverage 四项 synthetic negative
  controls 全部拒绝；生成 1063 nodes/513 elements 粗网格；保存 50593-byte project。七项 diagnostic
  assertions 全 true。
- PASS 的准确名称：Workbench report 与 suite 均为
  `PASS_STEP_SEMANTIC_RECONSTRUCTION_DIAGNOSTIC`。这只证明 hash-bound STEP+sidecar 在该可删除
  fixture 上能确定性重建 solver-side boundary semantics；STEP 本身没有被宣称携带 native semantics。
- 原始证据：suite/MCP SHA-256 分别为
  `b354d7d4243773efef51dea483ce724b867c5dd262f62b5b3046d63fb4621aff` 和
  `387fddb8d64bbe9b1263681bc1b18ff5325001ec2c56d1438098e9bfa13f5b92`；SC/WB report SHA-256
  分别为 `39299cac95889d64d7172b64147cb2073d464ec35dc357fd562ae8b2af52bc57` 和
  `fc7e862ac05545a615a334185fffa16d9fa60e4f2d61e96e696bc7431d26d53a`；inspection/project
  SHA-256 分别为 `d0c6ac7c0174f3e145f088837c18b283cb172681056cd88870fd70957136b9eb` 和
  `758dfd38368c3d29afaddda8a02d1f9de24370a6dd468f920c615c03fcf3c990`；
  2026-07-14T21:50:50.6127980Z 相关进程数为 0。
- 报告中的 `DIAGNOSTIC_PASS_CANNOT_CLOSE_NATIVE_TRANSFER_GATE` 是防止把诊断 PASS 倒写成 native
  transfer PASS 的边界声明，不是运行异常。
- 对 Gate/论文主张的影响：canonical geometry transfer、Named Selection transfer、native attach、
  native parameterization 与 P1 readiness claims 仍全部 false；P1 readiness BLOCKED，P1--P6
  `NOT_RUN`；`VISIBILITY=NOT_USER_OBSERVED`。粗网格不是结构/CFD/CHT 求解结果。
- 下一步：继续独立关闭 native `.scdocx` attach、native Named Selection transfer 和 native driving
  parameter 三项 blocker，然后运行 Mechanical/Fluent 可删除 T1 小模型；不启动 006。
- 状态：CLOSED_STEP_SEMANTIC_RECONSTRUCTION_DIAGNOSTIC_PASS_NATIVE_GATES_OPEN

## 新条目模板

```text
## REAL-YYYYMMDD-NNN：标题
- UTC：
- Stage/task：
- Machine/operator：
- run/job/profile：
- 期望：
- 实际观察：
- 原始错误短摘：
- 原始日志路径 + SHA-256：
- 假设与最小区分实验：
- 结果：
- 根因及置信度：
- 采取/拒绝的 workaround：
- 对 Gate/论文主张的影响：
- 下一步：
- 关联 decision/annotation/run：
- 状态：
```
