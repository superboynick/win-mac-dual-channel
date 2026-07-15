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

## REAL-20260714-037：Windows 根审计的 hardcoded profile/runner 清单落后于已批准策略

- UTC：2026-07-14T22:03:12Z
- Stage/task：005 T1 / 第十五次证据提交后的 Windows 精确 handoff 审计
- 触发：Windows 已 fast-forward 到签名 commit `2e0a884fcd437db7cefd02f7775ca223e4967b7f`，
  commit 签名正确，但仓库根 `audit-airjet-project.ps1` 返回两项 FAIL：
  `manifest kind/source/required files changed for airjet-ansys-automation` 与
  `ANSYS profile policy identity/schema/unique-name lock failed`。
- 实际原因：根审计的静态期望仍只有旧 10-file automation skill required list 和 6 个 ANSYS
  profiles；仓库在 commit `4f80fc6...` 已合法加入 semantic runner 与第 7 个 semantic profile，
  `skills-manifest.json`、`profiles.json`、installers 和 MCP policy 都已更新。审计锁本身未同步。
- 为什么 Mac 未提前阻止：Mac 的 Python project audit 检查项目文件/证据不变量，但没有复刻 Windows
  根脚本中的 hardcoded manifest/profile identity lock。两种审计覆盖不同，单端 PASS 不能替代另一端。
- 最小修复：只把 `run_t1_semantic_reconstruction_suite.py` 加入根 Required/ExpectedManifest，并把
  `ajm005-workbench-semantic-reconstruction-t1-v1` 加入 ExpectedProfileIds；不改 profile、runner、
  MCP、skill hash、工程结果或任何 Gate。
- 预提交原生平台验证：将候选审计脚本复制到 Windows Downloads，并显式以当前干净仓库作为
  `-RepoRoot` 执行，返回 `PASS / required_files=105 / manuals=7 / csv_files=28`；候选文件随后删除。
  这证明 PowerShell 语法和新期望清单可用，但仍需提交、拉取后用仓库根脚本再跑一次。
- 证据边界：这是审计器同步缺陷，不影响第十五次原始 ANSYS suite/report/artifact 哈希，也不把 P1
  或 native claims 改为 PASS。修复必须在 Windows 真实执行根审计后才可关闭。
- Git 后原生复测：Windows fast-forward 到签名 commit
  `065295660bc816f754fb4ac417020eed9b90d5f1`，仓库根脚本返回
  `PASS / required_files=105 / manuals=7 / csv_files=28`。
- 状态：CLOSED_WINDOWS_ROOT_AUDIT_POLICY_SYNCHRONIZED

## REAL-20260714-038：145-character native input path 仍无法附加，关闭“仅缩短路径即可修复”假设

- UTC：2026-07-14T22:08:50Z
- Stage/task：005 T1 / 第十六次 native `.scdocx` transfer 短路径单变量复测
- run/jobs：`AJM005_T1_CAD_SUITE_20260714T220850149839Z_51a1f815`；SC
  `a5n-8bc3059cd345-399b0f417639`；WB `a5n-8bc3059cd345-f75ab60f6014`；签名 commit
  `41fa4a604dc04b3a32590a996a29fab7810c6d36`。
- 唯一有意的 runner 行为变量：case ID 从长 `ajm005-cad-xfer-...` 缩为 16-character
  `a5n-<12 hex>`。producer profile/几何构造、native 格式、Workbench journal、五项 assertions、
  `PASS_CAD_TRANSFER_SET` 合同和 Gate 未改。producer 在本轮重新生成 32148-byte `.scdocx`，不主张
  它与历史 native control 在字节层相同。
- 路径观测：SC/WB job directory 均为 102 characters；失败消息中的 frozen native input 完整路径为
  145 characters，显著短于此前长 job。不能再把本轮失败主要归因于 case/job path 太长。
- producer：SpaceClaim 21.456 秒正常退出，八项 assertions 全 true；transfer `.scdocx` 32148 bytes，
  SHA-256 `babdfbee836512c1a6ba602727e7946495b4070538ef26065220305a1e527dcb`；report SHA-256
  `813df1c46d7047d75a8cc0900eb0649ea391fe92eb16a52e603a81f46bba93fd`。
- consumer：predecessor identity、SetFile、显式 SpaceClaim Edit/Exit、ComponentsToShare、
  GetGeometryFileAndSaveData 和 Model container 全部 RETURNED；`Model.Refresh()` 在 280.347 秒后仍
  报告“无法附加几何结构”。geometry transfer 为 direct FAIL；Mechanical inspection、native Named
  Selection transfer、mesh 和 project save 均 `NOT_REACHED`。
- 原始证据：suite/MCP SHA-256 分别为
  `68109b722d0a2fe08b2bb6cb42c2276312659138f4226dca1976f9866d472d0f` 和
  `8b0cf6d7392dbfa2bb71c0303037b327d9741c7936597b78d6511235b7e86127`；WB report/job-state
  SHA-256 分别为 `3020c445a4587f7b2018b6449f58774bacb5f912aa9c001d5d3686c0d4f889e5` 和
  `85feb9d5294c08fffc4198ebfc5523608a1b71b42c32b8447dad5422a527bc0b`；
  2026-07-14T22:14:33.9213117Z 相关进程数为 0。
- 结论：在此前 semantic 长/短路径配对实验中，缩短路径是唯一有意改动并恢复了算法可达性，强支持
  该 route 存在路径敏感；但本轮证明相同控制不足以修复 native `.scdocx` route。两条路径使用不同
  translator/materialization，不能把一条路线的修复外推为另一条路线的一般根因。
- 下一最小实验：保留 MCP 中 frozen predecessor 只读且不变，在 Workbench job root 建立 hash-equal、
  明确 writable 的 native working copy，只让 SetFile/Edit/Exit 使用 working copy；记录 staging 前 SHA、
  属性和 Edit/Exit 后 SHA。若仍失败，再关闭 read-only 假设并转查 native 文件类型/producer 文档结构。
- 对 Gate/论文主张的影响：suite 为 `FAIL_CAD_TRANSFER_SET`；P1 readiness BLOCKED；native geometry/
  Named Selection transfer 未证明；P1--P6 `NOT_RUN`；`VISIBILITY=NOT_USER_OBSERVED`。
- 状态：CLOSED_SHORT_PATH_NOT_SUFFICIENT_OPEN_WRITABLE_STAGING_TEST

## REAL-20260714-039：hash-equal writable staging 仍无法 native attach，关闭 read-only 唯一充分解释

- UTC：2026-07-14T22:34:30Z
- Stage/task：005 T1 / 第十七次 native `.scdocx` transfer writable-staging 有意干预复测
- run/jobs：`AJM005_T1_CAD_SUITE_20260714T223430902023Z_528b9791`；SC
  `a5n-6263df0a5eda-c8286865ca7c`；WB `a5n-6263df0a5eda-860a53afe7a2`；签名 commit
  `3336c75d0ff9a49c738623f7dd5625e37073235f`。
- 有意干预：MCP frozen predecessor 继续只读且不变；Workbench job 内另建初始 size/SHA 相同、
  与 source 完整路径同为 145 characters 的 writable working copy，`SetFile` 只使用 working copy。
  producer 每轮重新生成 native，本轮为 32143 bytes，前轮为 32148 bytes，因此不能把两轮写成
  identical-bytes permission-only paired trial。
- producer：SpaceClaim 21.704 秒正常退出，八项 assertions 全 true；transfer native SHA-256
  `7e1d3729c40b40b659c02b5dc2983cdd84a0dcb4941282db1641578bbdaeb0e8`；report SHA-256
  `b79fd3b6a50a82708652203eb4c008674f722c2a2762b3ff26a2b541739dad94`。
- staging 证据：journal 与事后 PowerShell 均确认 source 为 `ReadOnly, Archive / IsReadOnly=true`，
  working copy 为 `Archive / IsReadOnly=false`；两者均为 32143 bytes、相同 SHA。source 前后字节与
  read-only 位均不变；working copy 运行结束仍存在，前后 size/SHA 未变。后者只表示未观测到文件
  字节变化，不表示 editor 没有尝试写入或没有内部活动。
- consumer：working-copy stage、SetFile、显式 SpaceClaim Edit/Exit、ComponentsToShare、
  GetGeometryFileAndSaveData 和 Model container 全部 RETURNED；整个 WB job 282.115 秒，异常点仍是
  `Model.Refresh()` 无法附加 staged `.scdocx`。journal 没有单独计时 Refresh。Mechanical inspection、
  native Named Selection transfer、mesh 与 project save 均 `NOT_REACHED`。
- 原始证据：suite/MCP SHA-256 分别为
  `3f27305504e5f9a56f3e65332029871c510da840211f71691d466129aa87a7fe` 与
  `0e13158e1b1cb946a58b6420eeb227a1afbcd90450772fc09986433fc6cc01b2`；WB report/job-state
  SHA-256 分别为 `afa8112e57d4ad6fc2b412fb99a5b5f59669e505a83464b428e609b33d34ae94` 与
  `4ec64e97f42165cb627cdea03063fa844354d145bbb8837a68d4d34381e98391`；
  2026-07-14T22:40:19.9791271Z 相关进程数为 0。
- 结论：可以关闭“job-local hash-equal writable staging 足以修复当前 native attach route”和
  “read-only 是唯一充分解释”这两个窄假设。不能全局排除权限为多因素之一，也不能写成 SpaceClaim
  从不需要可写文件。
- 下一最小实验：不再叠加 chmod、复制位置或更短路径；保留 producer/frozen evidence/短 case/
  五项 assertions，只改为 Workbench 空 Geometry cell 连接的 SpaceClaim editor 内部创建 disposable
  native document，再 share 到 Mechanical。该实验必须是独立 diagnostic profile，禁止用 STEP
  semantic reconstruction 冒充 external native transfer。
- 对 Gate/论文主张的影响：suite 为 `FAIL_CAD_TRANSFER_SET`；顶层
  `PARTIAL_CAD_TRANSFER_ONLY` 只指 SpaceClaim producer partial capability；直接 blocker 是 native
  Refresh attach，`NATIVE_PARAMETERIZATION_NOT_RUN` 是后续仍开放的 hard blocker。P1 readiness
  BLOCKED；P1--P6 `NOT_RUN`；`VISIBILITY=NOT_USER_OBSERVED`。
- 状态：CLOSED_WRITABLE_STAGING_NOT_SUFFICIENT_OPEN_CONNECTED_EDITOR_DIAGNOSTIC

## REAL-20260714-040：在 Windows 误用 Unix skill installer，入口选择失败但正确入口立即通过

- UTC：2026-07-14T22:33:00Z
- Stage/task：005 T1 / commit `3336c75...` Windows handoff
- 触发：Windows 精确拉取和签名验证后，从 Git Bash 调用 `install-skills.sh`；第一条目录镜像命令返回
  `rsync: command not found`。
- 原因：仓库有平台专用入口。`.sh` 依赖 macOS/Unix 已有的 `rsync`；Windows 正确入口是
  `install-skills.ps1`，其镜像后端为系统 `robocopy`。这是操作入口选择错误，不是 skill 内容、Git、
  ANSYS 或许可故障。
- 恢复：立即运行仓库根 `install-skills.ps1`；automation/product/jupyter/pdf 四个 skill 的规范化
  SHA 与必需文件数全部 PASS，随后根审计 `required_files=105/manuals=7/csv_files=28` 和 MCP static
  policy `profiles=7/tools=5` 均 PASS。
- 教学结论：跨平台仓库不能只看文件名中的“install”；应先按平台手册选入口，并把复制工具依赖纳入
  preflight。失败发生在第一条复制命令，未留下部分更新后的错误能力声明。
- Gate 影响：NONE；此问题在 ANSYS suite 启动前已关闭，不能用于解释本轮 native attach 失败。
- 状态：CLOSED_CORRECT_WINDOWS_INSTALLER_USED

## REAL-20260714-041：connected editor 首轮在 build report 落盘前失去可观测性

- UTC：2026-07-14T23:09:03Z
- Stage/task：005 T1 / 第十八次、首轮独立 connected SpaceClaim document diagnostic
- run/jobs：`AJM005_T1_CONNECTED_SC_SUITE_20260714T230903934067Z_ad740c2f`；SC
  `a5c-ab68b630caaa-6338801f9872`；WB `a5c-ab68b630caaa-a6a5526bae67`；签名 commit
  `f15aae34c6a3b7cf1d5fe3ea07b63cdee2b3e33a`。
- 设计边界：Workbench 从 `GeometryFilePath=""` 的空 Geometry cell 进入 connected SpaceClaim；
  没有 `SetFile`、`DocumentOpen` 或 external `DocumentSave`。前驱只复制 producer report 作为 control，
  不消费 `.scdocx`、STEP 或 sidecar。该 profile 无论成败都不改 external/native/P1 canonical claims。
- producer：24.460107 秒正常退出，八项 assertions 全 true；transfer native 为 32142 bytes、
  SHA-256 `23dcfa4309d7b0a850eb99e7431d609d1e3cbfc4d5425cffc9a5d9bab1896cb1`；report
  SHA-256 `29d8f21ed4d5d4372fd3f8ada318d6a6e16771c4bb7b0a6d9a021e2904b49d26`。
- consumer reach：前驱 control PASS、空 Geometry cell RETURNED、connected `Edit` RETURNED、
  `RunScript` RETURNED、`Exit` RETURNED；随后检查
  `connected_spaceclaim_build.json` 时发现文件不存在，精确错误为
  `FAIL_CONNECTED_EDITOR_BUILD_REPORT_MISSING`。share/save-data/Refresh/Mechanical/mesh/project 全部
  `NOT_REACHED`。前驱 report 前后 size/SHA 不变。
- 可观测性缺口：嵌入脚本在建立 `result` 和 `try/except` 前读取 `AIRJET_JOB_DIR`；如果 connected
  SpaceClaim 进程未继承该变量，就会在最早处退出且无法写报告。该解释合理但未证实；早期 import/API
  异常、RunScript 异常不传播或落盘时序仍是并列解释。
- 原始证据：suite/MCP SHA-256 分别为
  `58d5fb4dde9e4c8627f4850225ed884e666082036b8ca37429a1290636922f5b` 与
  `7ea09aa4de55cc6ec73df5f68bbdbd10216b8f0f3f4987e8af22c3103cfb0ecd`；WB report/job-state
  SHA-256 分别为 `1e29128b0312c853820428e7bc9be6fb3c409db3ecd151841b2ce699c82f786d` 与
  `6f19c6eb7c58d9ed9feb6072bb65ac111daf360368f513f0f6e08993c5a3d71c`；
  2026-07-14T23:13:56.0285117Z 相关进程数为 0。
- 下一最小实验：不改几何和 transfer 合同，只把绝对 job/report path 嵌入 build script，并在任何
  SpaceClaim import/API 前写 early sentinel；顶层捕获 stage/type/traceback。先恢复可观测性，再按
  精确异常决定是否修 route。
- Gate/论文影响：suite 为 `FAIL_CONNECTED_SPACECLAIM_TRANSFER_DIAGNOSTIC`；这不是 external native
  transfer 失败的新证据，也不是许可/安装根因。P1 readiness BLOCKED；P1--P6 `NOT_RUN`；
  `VISIBILITY=NOT_USER_OBSERVED`。
- 状态：OPEN_EXPLICIT_PATH_AND_EARLY_SENTINEL_DIAGNOSTIC

## REAL-20260714-042：临时验证包装器出现三次假失败，项目合同本身随后均通过

- UTC：2026-07-14T23:00:00Z--23:09:00Z
- Stage/task：connected diagnostic preflight / Mac 与 Windows 外层验证器
- 现象一：Mac 临时哈希检查器把 profile 字段写成 `id/script_sha256`，而真实 schema 是
  `profile_id/sha256`；第二次又假设嵌入变量名为大写 `SPACECLAIM_SCRIPT`，实际为
  `connected_spaceclaim_script`。两次 AssertionError 都来自临时复核器，不来自项目 audit 或 journal。
- 现象二：Windows 在同一 PowerShell 进程中调用 `install-skills.ps1` 后，外层直接检查
  `$LASTEXITCODE`；installer 已打印四项 PASS，但变量保留了内部 native command 的旧值，外层误抛
  `INSTALL_SKILLS_FAILED`。改为每个 `.ps1` 用独立 `powershell.exe -File` 进程执行后真实退出码为 0。
- 恢复证据：profile 数 8、tools 数 5；Python project audit
  `required_files=106/manuals=7/csv_files=28`；四个 skill hash/必需文件均 PASS；Windows 工作树保持
  clean，HEAD 和签名 commit 均为 `f15aae34...`。
- 教学结论：验证器也必须对 canonical schema 编程；`$LASTEXITCODE` 是最近 native command 状态，
  不是任意 PowerShell script block 的可靠返回值。把 preflight 红字当作 ANSYS 根因会制造错误因果链。
- Gate 影响：NONE；这些问题都在 ANSYS suite 启动前关闭，未修改任何物理/几何结果。
- 状态：CLOSED_VALIDATOR_AND_PROCESS_EXIT_CONTRACT_CORRECTED

## REAL-20260714-043：Workbench 记录 RSM/ProgramData 警告，但当前没有因果链指向 connected 失败

- UTC：2026-07-14T23:09:36Z
- Stage/task：005 T1 connected Workbench CoreEvents 环境噪声审查
- 原始观察：`JobManagerUnAvailable` 报告未安装 Remote Solve Manager；其初始化同时抛出
  `System.ArgumentException: 需要绝对路径信息`，调用栈位于
  `ApplicationConfiguration.ProgramDataDirectoryPathByVersion`。CoreEvents/Fatal/recorded journal
  SHA-256 分别为 `5dd828a5...`、`83238038...`、`7d7d4383...`。
- 因果边界：本轮没有请求远程队列或远程求解；警告之后 project 仍创建，connected Edit、RunScript、
  Exit 都返回。当前失败是 build report 不存在，日志没有把该文件缺失连接到 RSM。
- 采取的处理：保留 warning 与堆栈，不安装额外 RSM、不修许可、不把它用于解释本轮失败。只有未来
  实际调用远程队列/求解或相同绝对路径异常直接阻断所需 API 时，才重新升级该问题。
- Gate 影响：NONE_OBSERVED；P1--P6 状态不变。
- 状态：OBSERVED_NONBLOCKING_NO_CAUSAL_LINK

## REAL-20260714-044：literal-path early sentinel 三个检查点均缺失，排除 child env 路径的充分解释

- UTC：2026-07-14T23:34:50Z
- Stage/task：005 T1 / 第十九次、connected child 可观测性单变量复测
- run/jobs：`AJM005_T1_CONNECTED_SC_SUITE_20260714T233450354994Z_6e14c202`；SC
  `a5c-df21627f7ebc-5782e518b714`；WB `a5c-df21627f7ebc-a117ae4ce96f`；签名 commit
  `0b32f5d14b8e90d469e23f8de27c23f8b5406a62`。
- 有意改动：fixture、empty-cell Edit/RunScript/Exit、predecessor control、transfer/Mechanical 合同均
  不变；child 的 job/report/sentinel 绝对路径改由 outer journal 注入，entry sentinel 在所有 imports
  和 SpaceClaim API 前写。环境变量只记录，不参与 child 输出寻址。
- producer：20.364381 秒正常退出，八项 assertions 全 true；transfer native 32140 bytes，SHA-256
  `f52632131899ad25835b1b91eef6098ef96743f78297a887641322b19eb450b6`；report SHA-256
  `67d64539ecf7ce6142239cc16718cf4aaa9794045b65e13b15110592ffef4fb3`。
- consumer：empty cell、Edit、RunScript、post-RunScript probe、Exit、post-Exit probe 全 RETURNED；
  post-RunScript `1784072246.0402832`、post-Exit `1784072246.042282`、failure probe 与 post-Exit
  相同，Exit 前后约 2 ms。三个点均为 entry sentinel absent/build report absent，且没有 probe error；
  Workbench messages 为空。精确终态为 `FAIL_CONNECTED_EDITOR_ENTRY_SENTINEL_MISSING`。
- 直接约束：literal path + import 前 sentinel 仍不存在，所以 child 中 `AIRJET_JOB_DIR` 缺失、陈旧或
  指错 job 已不能作为本轮“报告写错位置”的充分解释。仍不能排除更宽泛的 editor/broker 环境、
  file-based dispatch、错误会话或 child 对该路径无写权限。
- 官方边界：v261 Workbench guide 与 SpaceClaim API 均明确 `.py`、`.scscript` 都受支持。因此不能
  写“.py 非法”。下一轮若只换扩展名，测试的是当前 wrapper 的实现 dispatch 差异，不是文档合法性。
- 原始证据：suite/MCP SHA-256 分别为
  `d1ecddb82ae9733ad349893a1993483a73d3dab0079715e69d9ab1275195f639` 与
  `8917489f0f80ccd9fd1eca0b8e0a57bcf551b739d1e87002998d60340a4bc686`；WB report/job-state
  SHA-256 分别为 `f7fd0056589a55ad296f0c29cd50998acabe4108ae91cc76a2d5cc3187e4cea8` 与
  `06f28010f61bb7a3a6d7a7f4371a27a292c058fbca4b2279052c4e5f6f019525`；
  2026-07-14T23:39:42.1722279Z 相关进程数为 0。
- Gate/论文影响：connected transfer 仍未到达；external `.scdocx` attach/native semantics/native
  parameterization 均未在本轮测试。P1 readiness BLOCKED；P1--P6 `NOT_RUN`；visibility
  `NOT_USER_OBSERVED`。
- 下一步：先不做相同字节的 `.py`→`.scscript` 改名，因为官方只证明两种格式都受支持，没有证明
  两者的合法序列化可逐字节等价。下一轮在同一 opened editor 用官方
  `SendCommand(Language="Python")` 写独立 absolute sentinel，再保留现有 `.py` RunScript，形成
  inline/file 对照；`.scscript` 只有在取得合法格式或等价性证据后再测。
- 状态：CLOSED_CHILD_ENV_PATH_NOT_SUFFICIENT_OPEN_FILE_DISPATCH_AB

## REAL-20260715-045：batch connected editor 的 SendCommand 在检查点前空引用

- UTC：2026-07-15T00:06:34Z
- Stage/task：005 T1 / 第二十次、connected inline/file scripting channel 对照
- run/jobs：`AJM005_T1_CONNECTED_SC_SUITE_20260715T000634035436Z_65a14fe2`；SC
  `a5c-f6fbb9281baa-925d273ad30c`；WB `a5c-f6fbb9281baa-76d5b2fa4acb`；签名 commit
  `abb1d9a5def19ceb2410db154439c8a6864e9d3a`。
- 有意改动：在同一 `Interactive=False` connected editor 中，先用
  `SendCommand(Language="Python")` 写独立 fixed-bytes inline marker，再保留现有 `.py` RunScript。
  marker 以 exact size/SHA 判定；四态与 delayed 状态显式写入 suite，不能用“文件存在”冒充 PASS。
- preflight 现实坑：审查时发现 Windows text mode 会把 LF 转成 CRLF，所以 inline 与 file-entry marker
  均改为 binary `wb` + fixed bytes + close，并由两名只读审查员复核。否则真实 child entry 会被误判
  FILE_FAIL；该问题在 ANSYS 启动前已关闭。
- producer：20.202426 秒正常退出，八项 assertions 全 true；transfer native 32139 bytes，SHA-256
  `2ec0f65426a92d05d184a437c1a66a91d8cccf6aae6575fed5961d47e094a857`；report SHA-256
  `1a8f42dbe53b2c5d7ffa2446c731aad1bdd1a5e469aa026371db4b5511266e63`。
- consumer：empty cell 和 Edit RETURNED；`source_geometry.SendCommand(...)` 为 CALLED 后直接抛
  `未将对象引用设置到对象的实例。`，没有 RETURNED，也未到 post-SendCommand probe。正常路径的
  RunScript、Exit、build contract、share/Refresh/Mechanical/mesh/project 均 `NOT_REACHED`；failure
  cleanup Exit RETURNED。consumer 总时长 256.035317 秒，但无 API 分段计时，不能把全部时间精确
  归给 SendCommand。
- 正确分类：`CHECKPOINT_NOT_REACHED`。failure freeze 中 inline/file-entry/build report 均 absent，
  但 file RunScript 根本没调用，所以不能写成 `INLINE_FAIL_FILE_FAIL`。也不能据此判断 inline Python
  内容、encoding、marker path、权限或 `.py`/`.scscript` loader 失败。
- 环境噪声：GetMessages、stdout、stderr 均为空；CoreEvents 仍有 RSM/ProgramData warning，但没有
  RSM→SendCommand 空引用的调用链。本轮定位依赖 execution reach、traceback 与 recorded journal，
  不把同日志 warning 当根因。
- 证据：suite/MCP SHA-256 为 `fe04b05c...` / `faa900b7...`；WB report/job-state 为
  `4ca13aea...` / `15e172c...`；embedded child `ea7940d7...`；recorded journal/CoreEvents/Fatal 为
  `471b5f3b...` / `7a5637fe...` / `e18e66ec...`。Git 外 raw evidence ZIP 为 85822 bytes、
  22 个 payload，SHA-256 `56dbc5c8...`，已由本 run 的
  `external-raw-evidence-pointer.json` 登记；脱敏进程观察 JSON 记录结束后相关进程数 0。
- 下一步：只把受审 outer journal 的 `Edit(Interactive=False)` 改为 `Edit(Interactive=True)`；其余
  payload、SendCommand、RunScript、path-generation/binding、timeout、fixture 逻辑、cleanup 和 Gate
  合同不变，但 per-run absolute path 与注入后的 bytes 会重生成。marker 精确出现只支持
  `Interactive` mode/session 相关假设；同样空引用只关闭“仅改该参数即可修复”，不能全局排除
  batch/session 因素，之后再做 interactive RunScript-only。
- Gate/论文影响：P1 readiness BLOCKED；P1--P6 `NOT_RUN`；visibility `NOT_USER_OBSERVED`。本轮不是
  AirJet 产品 CAD/MEMS/结构/CFD/CHT 结果。
- 状态：OPEN_INTERACTIVE_TRUE_SINGLE_VARIABLE

## REAL-20260715-046：PowerShell 把 Git 的成功签名 stderr 和换行显示误判为失败

- UTC：2026-07-15T00:03:00Z--00:05:00Z
- Stage/task：commit `abb1d9a...` Windows handoff preflight
- 现象：`git verify-commit` 实际打印 `Good "git" signature` 且退出码为 0，但它把成功诊断写入
  stderr；在 `$ErrorActionPreference='Stop'` 下，PowerShell 先抛 `NativeCommandError`。放宽后捕获的
  格式化错误对象又按控制台宽度把 fingerprint 中间换行，导致 exact substring 检查第二次假失败。
- 原因：外层 wrapper 把 native stderr 渠道当成命令失败，又把面向人的换行渲染当 canonical 数据。
  这不是 commit 签名、Git、skill 或 ANSYS 故障。
- 修正：改用 `git log -1 --format='%G?'` 取得结构化状态 `G`，用 `%GF` 取得未换行的 signer
  fingerprint，并对二者分别 exact compare。随后 skill 12/6/12/4 files、root 106/7/28、policy
  8 profiles/5 tools、HEAD/signature/ahead-behind 全 PASS，工作树 clean 后才启动 ANSYS。
- 教学结论：自动化器不能用“stderr 有字”代替退出状态，也不能从格式化异常对象抽取身份字段；优先
  使用工具提供的 machine-readable format placeholder。
- Gate 影响：NONE；错误发生在 ANSYS 前，未用于解释 run #20 的 SendCommand 失败。
- 状态：CLOSED_MACHINE_READABLE_SIGNATURE_FIELDS_USED

## REAL-20260715-047：Interactive=True 仍不足以通过 SendCommand checkpoint

- UTC：2026-07-15T00:38:05Z
- Stage/task：005 T1 / 第二十一次、connected Edit mode 单参数复测
- run/jobs：`AJM005_T1_CONNECTED_SC_SUITE_20260715T003805172375Z_13dedbfe`；SC
  `a5c-8f6666935605-7a9a0e332873`；WB `a5c-8f6666935605-2ba2edec9fd8`；签名 commit
  `fe84454565b286a12efa8fe1550304212dc64ffb`。
- 单变量合同：受审 outer journal 唯一有意运行变化为 `Interactive=False→True`；profile 只更新
  outer script SHA；AST policy 锁定唯一 Edit、两个 literal True keywords 及
  Edit→SendCommand→RunScript 同一 body 顺序。path-generation/binding 合同、fixture template/逻辑、
  marker payload、timeout、前驱、cleanup、transfer/Mechanical/Gate 不变；每轮 absolute job path 及
  注入该路径后生成的 child/command bytes 会变化。
- producer：21.703735 秒 PASS；transfer native 32147 bytes/SHA `675ea6ca...`；report SHA
  `fbec220d...`。producer 与注入 job path 的 child 每轮重生成，不能把跨 run 全部输入写成 byte-identical。
- consumer：empty cell/Interactive=True Edit RETURNED；SendCommand 再次 CALLED 后在 line 553 抛同一
  中文 NullReference。post-Send、RunScript、正常 Exit、build/transfer/Mechanical/project 未到；cleanup
  Exit RETURNED；failure freeze 三 artifact absent；classification `CHECKPOINT_NOT_REACHED`。
  consumer 总时长 255.783635 秒，无 SendCommand 单独计时。
- 对照结论：run #20/#21 的外部 failure signature 相同，故可关闭“仅把 Interactive 参数改 True 足以
  修复 checkpoint/marker”的窄命题。不能写 interactive/batch 完全等价、真实 GUI 已展示、内部根因
  相同、所有 session 因素已排除、inline payload 或 RunScript loader 失败。
- recorded journal：True 被 canonicalize 为 `Edit(IsSpaceClaimGeometry=True)`；相关 scripting 序列为
  Edit→SendCommand→cleanup Exit，无 RunScript。这证明 Workbench 接受该参数，不证明用户可见 desktop。
- 证据：suite 64137 bytes/SHA `2320b75b...`；MCP 12365/SHA `74232802...`；WB report/job-state
  `0c797244...` / `857865ac...`；embedded child `3cd779b7...`；recorded journal/CoreEvents/Fatal
  `e22bf61e...` / `7809523f...` / `c707a317...`。Git 外 ZIP 85780 bytes、22 payload、SHA
  `7068b5d2...`；结束后相关进程数 0。
- 下一步：保持 Interactive=True，移除/跳过 SendCommand 与 inline marker；让 `.py` RunScript 成为
  唯一 scripting action，建立 file-only reach/classification。entry exact 也只证明 child 进入，
  build/transfer/P1 仍需独立合同。
- Gate/论文影响：P1 readiness BLOCKED；P1--P6 `NOT_RUN`；visibility `NOT_USER_OBSERVED`。
- 状态：CLOSED_INTERACTIVE_ARGUMENT_ONLY_NOT_SUFFICIENT_OPEN_INTERACTIVE_RUNSCRIPT_ONLY

## REAL-20260715-048：PowerShell 双引号中的 `$变量:` 被解析为 drive 语法

- UTC：2026-07-15T00:34:00Z
- Stage/task：run #20 archive Windows sync wrapper
- 现象：异常文本中写 `"...:$Head:$SigStatus:$SigFingerprint"`，PowerShell parser 在执行任何 Git
  命令前报 `InvalidVariableReferenceWithDrive`，因为变量名后的冒号被解释为 drive-qualified variable。
- 修正：改用 `"...:${Head}:${SigStatus}:${SigFingerprint}"` 明确变量边界。随后 fast-forward、签名、
  ahead/behind 与 clean status 全 PASS；未启动 ANSYS，也未修改仓库内容。
- 教学结论：PowerShell 的双引号插值不是简单文本替换；变量后紧跟 `:` 时应使用 `${name}`，并把
  parser failure 与被测 Git/ANSYS failure 分开。
- Gate 影响：NONE；仅是 preflight wrapper 语法错误。
- 状态：CLOSED_BRACED_VARIABLE_INTERPOLATION

## REAL-20260715-049：Run #22 RunScript-only 合同已实现，runtime 仍是 NOT_RUN

- UTC：2026-07-15T01:00:00Z 起；本条记录 pre-run implementation/review，不是 ANSYS run 时间。
- Stage/task：005 T1 / run #22 `Interactive=True + RunScript-only` pre-run implementation。
- 触发：run #20/#21 的 source Geometry `SendCommand` 都在 post-call checkpoint 前抛
  NullReference，目标 `.py RunScript` 两轮均未调用。为直接回答 file route 问题，本轮把该前置 action
  和 inline marker 明确记为 `SKIPPED_BY_EXPERIMENT`；这不等于它们执行后 FAIL，也不证明
  `SendCommand` 在所有 Workbench/SpaceClaim 场景都不可用。
- 实现：outer journal 保持 `Edit(Interactive=True)`，随后只 direct call
  `source_geometry.RunScript(ScriptFile=build_script_path)`；固定 34-byte binary entry sentinel 以 exact
  size/SHA 判定。正常路径在 `POST_EXIT` freeze；仅当异常仍需 connected-build 失败诊断且 build
  contract 尚未返回时，才记录 cleanup 前后 checkpoint、在 `FAILURE_POST_CLEANUP` freeze，并随后
  best-effort capture/parse build JSON。runner 用 schema v2 对
  call outcome、execution reach、entry first-observed/delayed/lost、probe error、freeze/capture 与 build
  state 做跨字段校验；policy 用 AST 锁 owner/cardinality/keyword/order/cleanup，并保留唯一
  `model_container.SendCommand` 给后段 Mechanical inspection。
- 审查中发现并修复的验证器现实问题 1：freeze 后文件可能才出现，也可能在 capture 前消失。第一版
  validator 把“freeze 时分类”和“capture 时 build state”当成同一原子时刻，因而会拒绝 writer 实际可达
  的 late valid/FAIL/invalid JSON 以及 freeze-present/capture-gone。修正后两组证据正交：capture 不会
  倒写成 immediate entry，聚合存在性也不再抹去时序。
- 审查中发现并修复的验证器现实问题 2：`build_report_probe_errors_at` 是历史累计列表，
  `build_report_exists_at_freeze` 却只属于最终 freeze checkpoint。把“历史某次有错”误当“当前 freeze
  有错”会拒绝 `POST_EXIT` 出错但 cleanup 后恢复并明确 absent 的合法路径。现按
  `freeze_probe in build_report_probe_errors_at` 区分当前错误与历史错误，并各有正/反 mutation。
- 审查中发现并修复的静态策略问题：只禁 direct `getattr(source_geometry, ...)` 不足以阻止 alias、
  `__builtins__["get"+"attr"]` 或 IronPython/.NET `GetType→GetMethod→Invoke`。现锁定
  `source_system.GetContainer(ComponentName="Geometry")` 唯一且直接赋给 `source_geometry`，同时禁止
  refetch、method rebinding、subscript dispatch 与上述 reflection surface。静态形状锁仍不是 runtime
  sandbox，也不证明 Windows host 已执行脚本。
- pre-run checks：journal/runner/policy-test SHA-256 分别为 `160b0b4590b1...d28539b`、
  `a6a7a2b13f53...fb2adce`、`74acb8d8f74c...d900903`；profile 绑定 journal SHA。Python 3 compile、
  IronPython 2 grammar、static policy（8 profiles/5 tools）、project audit（106 required/7 manuals/28 CSV）
  与 diff-check 均 PASS，并由两个只读 reviewer 重放关键状态矩阵。以上不是 capability PASS。
- 已知非阻塞限制：freeze 与 capture 不是原子快照；历史 probe error 后当前实现 fail closed、跳过 capture，
  可能损失后来已恢复可读的 child JSON；normal contract/capture error 的部分顶层诊断字段还可进一步做
  双向内容约束。真实 profile script 已由精确 SHA 锁定，capability PASS 另要求 build contract、工程
  assertions 和 artifacts 全通过，所以这些限制不允许制造 PASS，但必须保留在方法局限中。
- 当前实际观察：`run_id=NONE`、`job_id=NONE`、declared report/artifact manifest/raw ZIP=`NONE`、Windows
  runtime=`NOT_RUN`。不能写 RunScript 返回或抛错、entry 出现或缺失、`.py` loader 可用或不可用、
  connected build/transfer/mesh/project 通过、GUI 可见或 P1 通过。
- 下一步：签名 commit/push → Windows `pull --ff-only` 精确同步 → 重装 skill 并核对 installed hashes →
  Windows static policy/preflight → 新 case/job 实跑 → 原始结果与解释分别归档。无论本诊断结果为何，
  external `.scdocx` attach、native Named Selection transfer、native parameterization 和 P1 Gate 都仍需
  独立关闭。
- Gate/论文影响：NONE；`P1_CAD_TOOLCHAIN_READINESS=BLOCKED`，P1--P6 `NOT_RUN`；这条只能支持“实现并
  审查了待运行的 fail-closed instrumentation”，不能支持任何 AirJet 产品几何或物理结果。
- 状态：IMPLEMENTED_PENDING_SIGNED_WINDOWS_RUN

## REAL-20260715-050：RunScript 返回但 child entry/build 未被观测，connected route 冻结

- UTC：2026-07-15T02:15:29.059815Z--2026-07-15T02:18:11.986778Z
- Stage/task：005 T1 / 第二十二次、`Interactive=True + RunScript-only` connected diagnostic。
- Machine/operator：`LAPTOP-LCCLM2HI`；发起 operator 未写入 raw suite，登记为 `NOT_RECORDED`。
- run/jobs：`AJM005_T1_CONNECTED_SC_SUITE_20260715T021529059815Z_aa1180f6`；case
  `a5c-eedabacc1fc6`；SC `a5c-eedabacc1fc6-f70b77c399ca`；WB
  `a5c-eedabacc1fc6-027f5de8b724`；运行 commit
  `1a9696c3930a42cd8a30aafe7093b8acafd6dd59`。
- producer：21.451068 秒、exit 0，八项 assertions 全 true，report SHA-256
  `df5f3e8ecd929fd14c3cbf46673844bc4a29e15b5d8fbb60f581b566f6de2466`；状态只允许写
  `PASS_PARTIAL_CAD_CAPABILITY` / `PASS_PARTIAL_CAD_ONLY`。
- consumer 直接观察：empty Geometry、Edit、direct `.py RunScript`、post-RunScript probe、Exit、
  post-Exit probe 均 RETURNED；source-editor SendCommand 按设计 `SKIPPED_BY_EXPERIMENT`。固定 entry
  sentinel 与 build report 在 post-RunScript、post-Exit、failure-pre、failure-post 四处均 absent，
  entry/build probe-error 列表为空；connected build contract 为 `CALLED`。
- 原始错误：`FAIL_RUNSCRIPT_RETURNED_ENTRY_AND_BUILD_ABSENT`；精确分类
  `RUNSCRIPT_RETURNED_ENTRY_ABSENT`。share、`GetGeometryFileAndSaveData`、Refresh、Mechanical、mesh、
  project save 全部 `NOT_REACHED`。
- 证据：suite JSON 68024 bytes / SHA-256
  `5069fc1a6681cf54f38ac4c8a0793f09cabc3ed9935cd422c57424539e08cadb`；MCP stderr 7173 bytes /
  `68339ac677f1ee0df258714b411a5fd476eee233a17bcb16a8840f72caa73683`；producer/consumer
  manifest 20/20 与 19/19 文件逐项重算一致。Git 外 ZIP 87014 bytes、22 payload 加内部
  `SHA256SUMS.csv`，SHA-256 `62b058ef4125704ef4d74624d23b5cc0093315ab29bc613cd0e55cf5d92b7a96`。
- 进程观察限制：suite 结束瞬间没有外层即时记录；归档时
  `2026-07-15T05:21:32.3964021Z` 的延迟 allowlist 检查为 0 个 ANSYS 进程，不能倒推即时 cleanup。
- 结论边界：最强结论只是 direct RunScript call 已到达并返回，但本轮没有观察到 child entry/build。
  不能写 build 已执行后失败、`.py` 不受支持、connected transfer 已失败/通过、GUI 已被用户观察或
  P1 已通过。
- workaround 决策：当前 connected external-geometry route 标为
  `DEFERRED_CURRENT_HOST_ROUTE`；本冲刺不再追加 connected 探针。迁移到签名 SpaceClaim 脚本建模和
  hash-bound STEP + semantic sidecar 的 solver-side reconstruction route，不把它冒充 native transfer。
- Gate/论文影响：`P1_CAD_TOOLCHAIN_READINESS=BLOCKED`；external native attach、native
  parameterization、native Named Selection transfer 均 `NOT_PROVEN`；P1--P6 `NOT_RUN`；visibility
  `NOT_USER_OBSERVED`。
- 状态：PRESERVED_AND_ROUTE_DEFERRED

## REAL-20260715-051：v2 wrapper 丢失扩展语法绑定，反射最小修复后 005 同轮端到端 PASS

- UTC：诊断/修复链 2026-07-15T09:41Z 起；最终 PASS run 为
  `2026-07-15T10:04:43.733301Z--10:06:02.423387Z`。
- Stage/task：005 T1 alternate-route v2 confirmation；目标是在同一签名 commit 内连通 SpaceClaim
  producer 与 Workbench semantic reconstruction consumer。
- 前三次正式失败：commit `5f369ba...` 已通过 campaign Git-LF source identity，但 v2 wrapper 用
  `globals().copy()` 执行 v1 base 后在 `GetAllBodies()` 报 `AttributeError`；commit `85439eb...` 显式
  import/call `PartExtensions` 时 SpaceClaim exit 0 却没有任何声明报告；commit `edce0f4...` 改回宿主
  globals 后仍在同一扩展语法处失败。三轮都 fail closed，consumer 未越过 producer gate。
- 最小区分实验：一次性 Windows SpaceClaim 诊断打开同一 STEP，观测
  `root Bodies=0 / Components=1`；直接扩展与
  `MethodInfo.Invoke(None, Array[Object]([part]))` 都返回同一唯一 body。诊断只确认 API 绑定路线，不是
  AirJet 产品结构证据。
- 根因判断：v1 脚本被 v2 `execfile` 动态编译时没有直接脚本入口的 IronPython extension-method
  syntax binding；`.NET` 类型和静态方法本身仍可用。置信度高，因为反射/direct 同体诊断与随后正式
  suite PASS 形成前后闭环。
- 修复：commit `9a88b7ad26d5d5c9f35d8a5f956df7038cfca0fd` 只在 base 中按类型名、方法名和单参数
  overload 反射调用 v261 `PartExtensions.GetAllBodies(IPart)`，并重绑 wrapper/profile/route 的完整
  SHA 链；所有静态 policy、runner guards、semantic negative tests 与双项目审计先 PASS。
- 最终 run：`AJM005_T1_ALTERNATE_ROUTE_SUITE_20260715T100443733301Z_d1743e81`；producer/consumer
  都为 `PROCESS_EXITED_0 / capability PASS`，suite
  `PASS_ALTERNATE_ROUTE_SEMANTIC_CONFIRMATION`。原始 suite JSON 201157 bytes / SHA-256
  `dc3c52688fbd63a41f3ace4afceb55a1294c5464c4d0940636f2122a4e2f4ab0`；closeout SHA-256
  `8a1065da67e7e35d511845a8fadfdf0f7757c39490513486b7cf5ff0d6082cf9`。
- 主要产物：STEP SHA-256 `268011ef6f82d1e7c404c37de64e6bf533a5bbcf5373cdcee0a31ec4c0958a86`；
  producer/consumer v2 report 分别为 `6f2b007d...` / `359eb526...`；Workbench project 50555 bytes，
  SHA-256 `168406bd...`。完整 79 文件、7.9 MB 成功目录保留在 Windows Downloads，并复制到 Mac
  `Downloads/AirJet-005-PASS-20260715-d1743e81/`；Git 保存脱敏 summary、closeout 和解释。
- Gate/论文影响：`P1_CAD_TOOLCHAIN_READINESS=PASS` 仅限 alternate route，技术建议
  `START_006_ALTERNATE_ROUTE_ONLY`；`P1_STAGE_GATE=NOT_RUN`，external native attach、native
  parameterization、native Named Selection transfer 仍 `NOT_PROVEN`，P2--P6 仍 `NOT_RUN`。
- 状态：PASS_START_P1_ALTERNATE_ROUTE_ONLY

## REAL-20260715-052：V02 首跑在几何前暴露 IronPython 字符缓冲差异

- UTC：`2026-07-15T11:29:33.575122Z--11:29:58.248998Z`。
- Stage/task：006 V02 preliminary full-product CAD；job
  `AJM006-V02-PRELIMINARY-09d11b707907`；commit `d94f9c83...`。
- 期望：由同一签名提交冻结 15 个依赖后，建立 12-cell/972-hole 两流体区整机 CAD。
- 实际：SpaceClaim exit 0，但 producer 在任何 body 创建前，于 canonical dependency hash 的
  `data.replace(b"\r\n", b"\n")` 抛 `TypeError: expected a character buffer object`；runner exit 2 / fail closed。
- 解释边界：十项 assertion 的 raw `false` 是异常前默认值，含义是 `NOT_REACHED`，不能写成十项几何
  独立失败。此轮没有评价 Boolean、ShareTopology、native/STEP 或产品几何。
- 根因及修复：V261 IronPython 的 binary read 字符缓冲语义与 CPython 3 `bytes` 不同。commit
  `da39751c...` 只把 CRLF canonicalization 改为该宿主接受的字符路径，并重绑 producer/profile/runner
  SHA；几何、孔数和 Gate 未放宽。
- 证据：producer `3762d767...`；runner summary `e3321e36...`；stdout `51c89ce...`；MCP stderr
  `13132223...`。Windows 原始 job、Git condensed evidence 和 Downloads ZIP 均保留。
- Gate/论文影响：P1--P6 `NOT_RUN`；只可写“首跑发现并修复宿主兼容问题”。
- 状态：CLOSED_BY_SIGNED_RETRY

## REAL-20260715-053：第二跑建立完整 native CAD，但 STEP 形状容差 fail closed

- UTC：`2026-07-15T11:32:49.014468Z--11:34:52.716636Z`。
- Stage/task：006 V02 preliminary；job `AJM006-V02-PRELIMINARY-bc1b12e43d39`；commit
  `da39751c...`。
- 实际观察：12 个 cell、972 个直径 0.25 mm 孔、两个 single-piece/closed/manifold 流体实体均建成；
  `INLET/OUTLET=4/1`、`MEMBRANE_TOP/BOTTOM=12/12`、孔口两侧 `972/972`、`HEAT_WALL=1`；native
  保存/重开和 group fingerprints PASS。实际膜片面积代理孔隙率 `8.1144453106%`。
- 唯一失败：STEP 重导 upstream 最大 bbox 漂移 `0.014975 mm`，超过原通用 `0.005 mm`；最大体积差
  约 `0.003997 mm^3`。十项断言为 9 true/1 false，runner 因 `step_export_reimport=false` 拒绝 PASS。
- 最小区分修复：commit `64b57303...` 只给 STEP shape round-trip 绑定实测覆盖的 `0.02 mm` bbox
  tolerance；native 仍用 `0.005 mm`。报告新增实际 delta 与容差，不删除 STEP assertion。
- 表示限制：STEP downstream face decomposition 从 native 978 faces 合并为 6；preliminary STEP
  shape equality 本来不锁 face count，但这不能证明 shared/coincident interface identity。
- 证据：producer `7525eaf7...`；runner summary `97eb334d...`；stdout `ff942375...`；MCP stderr
  `b3045747...`。
- Gate/论文影响：仍为 `FAIL_PRELIMINARY`；P1--P6 `NOT_RUN`。
- 状态：CLOSED_BY_MEASURED_TOLERANCE_RETRY

## REAL-20260715-054：第三跑 V02 preliminary producer 十项断言全部 PASS

- UTC：`2026-07-15T11:39:39.945030Z--11:41:35.667587Z`。
- Stage/task：006 V02 preliminary；job `AJM006-V02-PRELIMINARY-1082d551ee85`；commit
  `64b57303b324aa1c98890d4241462814678af41f`；producer SHA `e575c045...`。
- 结果：job `PROCESS_EXITED_0`、runner exit 0 / `PASS_PRELIMINARY_PRODUCER`、producer
  `PASS_PARTIAL_CAD_CAPABILITY`；十项 assertions 全 true。实测计数仍为 12 cell、972 holes、
  2 bodies、4/1、12/12、972/972、1 heat wall；native 与 STEP reimport 均为两个 closed/manifold body。
- STEP 量化：最大 bbox delta `0.014975 mm < 0.02 mm`；最大 volume delta
  `0.003996774 mm^3 < 0.005 mm^3`。容差与 delta 同时写入 `step_reimport.json`。
- 证据：六个声明产物逐项 size/SHA 与 38-file MCP manifest 闭合；producer `41255373...`；runner
  summary `3b35b820...`；stdout `11970c4a...`；MCP stderr `8335263e...`。
- 三份归档：Windows 原始 job；Mac Downloads 113-file byte-verified 副本；Mac/Windows Downloads
  ZIP 15767164 bytes，SHA `f4ef73b5...`；Git 保存三轮 condensed evidence。
- 结论边界：这只证明一个主候选的 preliminary full-product CAD 生产能力。`formal_006_completion=false`；
  STEP interface representation、solver semantic reconstruction、九变体/252 Gate、mesh/physics 均未评价。
- 下一步：依据真实 native/STEP face decomposition 设计并注册 observer；不得仅凭
  `ShareTopology.Success` 选择正式 shared-face schema。
- Gate/论文影响：P1 stage 与 P1--P6 继续 `NOT_RUN`。
- 状态：PASS_PRELIMINARY_PRODUCER_ONLY

## REAL-20260715-055：observer runner 首版在 ANSYS 前暴露 isolated Python sibling import

- Stage/task：006 V02 topology observer runner preflight；未创建 MCP/ANSYS job。
- 实际：Windows automation venv 以 Python `-I` 启动 runner 时，`from run_v02_preliminary_006 import ...` 抛 `ModuleNotFoundError`。isolated mode 不把脚本 sibling 目录自动放入 `sys.path`。
- 修复：commit `d984890...` 改用 `importlib.util.spec_from_file_location` 从受审绝对 sibling path 装载 producer runner，并增加回归 guard；未改 ANSYS journal、几何、阈值或 Gate。
- Gate/论文影响：NONE；异常发生在 ANSYS 前，不能用来解释任何几何结果。P1--P6 `NOT_RUN`。
- 状态：CLOSED_BEFORE_ANSYS_BY_SIGNED_RUNNER_FIX

## REAL-20260715-056：首次 topology inventory 有效，但 face-count 角色绑定被实测推翻

- UTC：suite `2026-07-15T12:21:49.298547Z--12:24:23.472341Z`；observer job `AJM006-V02-PRELIMINARY-2bdb5b95702a`。
- commit/profile：`d984890b84e3bf168c24f4ff869d474ac07e9fa4`；`ajm006-workbench-v02-topology-observer-v1`；script SHA `dd38228b...`。
- 实际：producer 与 observer 均 exit 0，Workbench import、Mechanical inventory 和 project save 返回；body IDs 7231/4288、face counts 978/100 是真实观测。
- 缺陷：旧 classifier 把 face 较多者绑定为 upstream，但持久化名称和 z 范围显示 7231 是 downstream、4288 是 upstream。跨内核 face decomposition 变化使该身份假设失效。
- 处置：原始 job/report/inventory/runner summary 全部保留；role-specific 计数和无限定解释标记为 superseded，不删除或改写原始证据。修正版改用 persisted name 和 z fallback。
- Gate/论文影响：观测执行 PASS 不等于当前分类可用；formal 006 与 P1--P6 均 `NOT_RUN`。
- 状态：RAW_OBSERVATION_VALID_CLASSIFIER_ROLE_BINDING_SUPERSEDED

## REAL-20260715-057：修正版 observer 确认 STEP handoff 单侧接口几何丢失

- UTC：suite `2026-07-15T12:29:07.417508Z--12:31:39.219916Z`；producer `...-13950bddaec8`；observer `...-2fb76257a827`。
- commit/profile：`9699df565d5b93bfe8bf8354834af7fc5f79624c`；observer script SHA `790247a2...`。
- 结果：suite `PASS_PRELIMINARY_TOPOLOGY_OBSERVER`；Mechanical upstream ID 4288/100 faces、downstream ID 7231/978 faces。downstream 接口 973 faces=972 个期望 XY 印记+大面 7158；upstream candidates 0、缺失 972。shared candidate、opposite-normal pair、cross-body duplicate 都为 0。
- 分类：`MIXED_OR_OTHER / UPSTREAM_ORIFICE_GEOMETRY_LOST_DOWNSTREAM_972_IMPRINTS_RETAINED`。孔口以 0.25 mm bbox、plane、单环和 XY/Z tolerance 识别；area 只作跨内核诊断。
- 证据：observer report SHA `078ae541...`；inventory SHA `e9ca1166...`；corrected runner summary SHA `38421836...`。Mac/Windows Downloads ZIP 20441827 bytes、SHA `10bb5025...` 一致，payload 158 files。
- 结论边界：observer PASS 表示观测闭合；无 mesh，不能声称 shared nodes、conformality 或 mesh failure。当前 STEP 两区路线被拒绝，但不推广为所有 STEP route 失败。
- 下一步：改变 native/connected/re-authoring 或受审 solver-side interface reconstruction 表示并重新 observer；修复前不启动正式九变体 006。
- Gate/论文影响：`formal_006_completion=false`；P1--P6 `NOT_RUN`。
- 状态：PASS_PRELIMINARY_OBSERVER_ROUTE_REJECTED

## REAL-20260715-058：Parasolid pilot 只完成 Mac 静态包，Windows terminal 尚未运行

- Stage/task：006 V02 Parasolid x_t route discovery static preparation。
- 实际：新增 native→x_t converter、x_t→Workbench/Mechanical observer、同进程三阶段 runner、
  两个 hash-pinned diagnostic profiles 和固定 Windows prompt。
- 静态结果：runner guards 16/16 PASS；MCP policy `14 profiles / 5 tools` PASS；Mac project audit
  `144 required files` PASS；converter/observer 脚本 SHA 分别为 `f330ce67...` / `624dbb7d...`。
- 审计修复：逐对共面几何、`AdjacentBodies`、逐角色 face-count/bbox/volume、predecessor 完整树和
  manifest 不可变、staging exact、manifest job/phase terminal binding，以及过强 topology-preserved
  措辞均已收紧。
- 未观察：Windows/ANSYS 未运行；没有 `product.x_t`、converter report、Mechanical inventory、
  `.wbpj` 或 route assessment 的真实 terminal evidence。
- Gate/论文影响：NONE；只能写“静态诊断包已准备”，不能写 x_t 路线成功/失败、mesh 或 P1 结果。
- 下一步：等待用户确认 Windows 恢复，再从 signed `GIT_READY` 执行唯一固定 runner；失败也原样保留。
- 状态：STATIC_READY_WINDOWS_NOT_RUN

## REAL-20260715-059：Parasolid converter 首次 Windows 试跑在 SpaceClaim 未注入 Reset 处 fail closed

- Stage/task：006 V02 Parasolid x_t diagnostic pilot；converter stage。
- commit/profile：`a7194071a2791c391557ef33e6600bc2adddbfba`；
  `ajm006-spaceclaim-v02-parasolid-converter-v1`。
- 接手证据：Windows HEAD 精确匹配、签名有效、clean、`0/0`、audit `144 files PASS`；静态
  guards 16/16 PASS；MCP inventory ready，Student executables/package versions 通过。
- 实际：producer job `AJM006-V02-PRELIMINARY-89a076e1807a` exit 0，`PASS_PARTIAL_CAD_CAPABILITY`；
  converter job `AJM006-V02-PRELIMINARY-18989d677c3e` 在打开 staging native 前调用未注入的
  `Reset()`，报告 `NameError: name 'Reset' is not defined`。未导出 x_t，observer 未启动。
- 已闭合的 converter 事实：predecessor identity 与 staging copy hash 通过；其余 converter 断言
  按失败语义保持 false。不能把这次写成 Parasolid 路线失败或几何拓扑结论。
- 处置：Mac 删除该未受审全局调用，重算 converter SHA 为
  `9bd5a21eaaba8cf1d253b7c93fbd4da50828b23b0207046eca76acb441f4fe46`，更新 runner/profile，
  重新通过 16 guards、14-profile policy 和 144-file audit；等待新签名 commit 后只重试一次。
- Gate/论文影响：NONE；P1--P6、mesh、physics、route assessment 均 `NOT_RUN`。
- 状态：CLOSED_BY_SIGNED_SCRIPT_FIX_PENDING_WINDOWS_RETRY

## REAL-20260715-060：v261 Parasolid 导出断言失败
- UTC：2026-07-15
- Stage/task：AJM-006 V02 Parasolid route discovery
- Machine/operator：Windows ANSYS Student 2026 R1 / Codex
- run/job/profile：`AJM006-V02-PRELIMINARY-b3fb40cb13cb` / `ajm006-spaceclaim-v02-parasolid-converter-v1`
- 期望：原生重开通过后导出 `product.x_t` 并进入重开比较。
- 实际观察：`source_native_open=true`、`source_native_exact=true`，但 `parasolid_export=false`；未启动 observer。
- 原始错误短摘：`PARASOLID_EXPORT_ASSERTION_FAILED`。
- 原始日志路径 + SHA-256：Windows `D:\AirJet_P1\AJM-P1-CAD-006\V02_PARASOLID_TOPOLOGY_RUN_SUMMARY.json`（保留原始 job 目录）。
- 假设与最小区分实验：v261 API 文档要求 `ExportOptions.Create()` 并显式设置 `Parasolid.Version`；仅替换导出调用，不改变几何或前置链。
- 结果：签名修补后重试仍失败；job `AJM006-V02-PRELIMINARY-555909407cfe` 通过 native reopen，未生成 `product.x_t`，observer 未启动。
- 根因及置信度：显式 `ExportOptions.Create()` + `ParasolidVersion.V23` 后仍无导出文件，说明当前 Student/SpaceClaim 环境的该导出能力或对象支持仍不可用；置信度中高，尚非整机几何结论。
- 采取/拒绝的 workaround：不绕过断言、不伪造 x_t、不继续重复试跑；保留原生 `.scdocx` 产物并转入 native/Workbench 路线。
- 对 Gate/论文主张的影响：P1--P6、mesh、physics、route assessment 继续 `NOT_RUN`。
- 下一步：以 native `.scdocx` 为主输入推进 Workbench/Mechanical 连接性检查；Parasolid 仅保留为已审计的失败诊断路线。
- 状态：CLOSED_DIAGNOSTIC_ROUTE_BLOCKED

## REAL-20260715-061：V02 STEP solver-side 拓扑观察完成
- UTC：2026-07-15
- Stage/task：AJM-006 V02 preliminary topology observer
- Machine/operator：Windows ANSYS Student 2026 R1 / Codex
- run/job/profile：producer `AJM006-V02-PRELIMINARY-36220012f2a3`；observer `AJM006-V02-PRELIMINARY-32f6ab51f170`
- 期望：在 Workbench/Mechanical 侧读取整机 STEP 交接物并对 972 孔接口进行只读分类。
- 实际观察：`PASS_PRELIMINARY_TOPOLOGY_OBSERVER`；分类 `MIXED_OR_OTHER`；`UPSTREAM_ORIFICE_GEOMETRY_LOST_DOWNSTREAM_972_IMPRINTS_RETAINED`。
- 原始证据：`D:\AirJet_P1\AJM-P1-CAD-006\V02_TOPOLOGY_OBSERVER_RUN_SUMMARY.json` 及 observer job inventory。
- 结果：solver-side inventory 成功生成；上游实体孔几何未保留，下游 972 个 imprint 保留。
- 对 Gate/论文主张的影响：证明了 STEP observer 链路可执行，但接口拓扑不完整；P1--P6、mesh、physics 仍 `NOT_RUN`，不得写成完整流固接口。
- 下一步：native `.scdocx` 只读 Workbench observer 需新建、静态审计、签名注册后再运行。
- 状态：CLOSED_OBSERVATION_WITH_TOPOLOGY_LIMITATION

## REAL-20260715-062：V02 native `.scdocx` observer 确认 972 个共享单面 membership
- UTC：2026-07-15T15:36:44Z--15:41:41Z
- Stage/task：AJM-006 V02 native topology observer diagnostic
- Machine/operator：Windows ANSYS Student 2026 R1 / Codex
- run/job/profile：producer `AJM006-V02-PRELIMINARY-a768ecd0008e` / `ajm006-spaceclaim-v02-preliminary-v1`；observer `AJM006-V02-PRELIMINARY-0600a08e2a83` / `ajm006-workbench-v02-native-topology-observer-v1`
- 期望：只读导入 hash-bound `product_two_zone.scdocx`，实测两侧 972-interface actual IDs 与 membership。
- 实际观察：runner `PASS_PRELIMINARY_NATIVE_TOPOLOGY_OBSERVER`；`972_SHARED_SINGLE_FACE / SHARED_ID_MEMBERSHIP_CONFIRMED`。downstream/upstream 为 body 316/1950、978/2044 faces；两侧各 972 个 XY 候选全部配对，same-ID 与双 body membership 均为 972。
- 原始日志路径 + SHA-256：`D:\AirJet_P1\AJM-P1-CAD-006\V02_NATIVE_TOPOLOGY_OBSERVER_RUN_SUMMARY.json`，SHA256 `459531dfb95a9e8b59d16d1aae862ceaba1402fec4cb45e248efbecdd92c0791`；raw producer/observer job 目录保留。
- 结果：native source/staging/final SHA256 全相同，未调用 Edit，predecessor 最终复核不变；Mechanical inventory 与 `.wbpj` 已保存。
- 采取/拒绝的 workaround：使用固定 job-local hash-equal staging；未回退 STEP/Parasolid/connected route，未 mesh/solve。
- 对 Gate/论文主张的影响：证明 native import topology 中存在 972 个跨两 body 的 shared single-face membership；没有 mesh，因此 shared nodes/conformal mesh、正式 006、P1 与物理结果均未证明。P1--P6 保持 `NOT_RUN`。
- 下一步：建立单独签名、无物理的 mesh conformality 诊断；不直接启动正式九变体或物理求解。
- 关联 decision/annotation/run：AJM-P1-GEO-006；本轮 producer/observer 两条 run-index。
- 状态：PASS_NATIVE_TOPOLOGY_CANDIDATE_MESH_NOT_RUN

## REAL-20260715-063：同一 native observer 路线出现 attach 失败
- UTC：2026-07-15
- Stage/task：AJM-006 V02 native topology observer repeatability evidence
- Machine/operator：Windows ANSYS Student 2026 R1 / Mac Codex via SSH MCP
- run/job/profile：producer `AJM006-V02-PRELIMINARY-939d21f59c47`；observer `AJM006-V02-PRELIMINARY-c1ff3339dcb9`
- 期望：从 hash-equal job-local `.scdocx` staging attach 并复现两体拓扑观察。
- 实际观察：predecessor identity 与 staging SHA 通过；`SetFile` 后 `Model.Refresh()` 报“无法附加几何结构”，Mechanical inventory 未到达。
- 原始证据：raw observer job 保留；该次 summary 后被后续 PASS suite 的固定摘要覆盖，故以 raw report 为准。
- 结果：不能关闭 native route，因为另一次同签名 profile 已 PASS；两轮 producer native SHA 不同，attach 重复性未闭合。
- 对 Gate/论文主张的影响：972 shared membership 是已观察候选，但不能写成稳定 attach 或 conformal mesh；P1--P6、mesh、physics 继续 `NOT_RUN`。
- 下一步：固定 repeatability + 无物理 mesh conformality 诊断；split STEP 仅作 fallback。
- 状态：OPEN_NATIVE_ATTACH_REPRODUCIBILITY

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
