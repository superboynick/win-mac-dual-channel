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
