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
