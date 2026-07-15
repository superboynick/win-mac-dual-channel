# Windows → Mac signed watcher E2E 001 结果

## 字面状态

```text
TASK_ID=ajm-git-windows-to-mac-e2e-20260715-001
NONCE=AJM-BIDI-20260715-W2M-6F1C9A42
TASK_COMMIT=ccb50116c116c251b914e07a098a9ceca4b27774
WINDOWS_TASK_SIGNATURE=PASS
GIT_PRECHECK=PASS
SKILL_INSTALL=PASS
PROJECT_AUDIT=PASS
MAC_WATCHER_TESTS=80_OF_80_PASS
WAKE_CHANNEL=SIGNED_GIT_WATCHER
REAL_WINDOWS_TO_MAC_WAKE=PASS
MAC_WATCHER_RUNTIME=NOT_RUNNING
MAC_AUTOSTART=ABSENT
GUI_VISIBILITY=NOT_USER_OBSERVED
CAD=NOT_RUN
ANSYS=NOT_RUN
CFD=NOT_RUN
OPTIMIZATION=NOT_RUN
PAPER=NOT_RUN
ROUNDTRIP_STATUS=PARTIAL
BLOCKERS=AUTOMATIC_CHILD_SANDBOX_DENIED_GIT_WRITE_AND_NETWORK;PRIMARY_COORDINATOR_RECOVERY_REQUIRED
```

`REAL_WINDOWS_TO_MAC_WAKE=PASS` 只表示 Windows 签名任务已被 Mac watcher
真实接收并启动独立 Codex。`ROUNDTRIP_STATUS=PARTIAL` 表示该自动子
Codex 没有自主完成 Git result/receipt 回程；本报告由原始主协调
会话核对证据后恢复。两个状态不得合并成“完全自动双向闭环 PASS”。

## 任务和 Git 证据

- Windows task commit：`ccb50116c116c251b914e07a098a9ceca4b27774`。
- 直接父提交：`d8c3962aa2476f22146091a2461778fa53e01173`。
- 签名：Good SSH signature，Windows 指纹
  `SHA256:oI3/MIlKz1mgLV3+5n1coQxynaqQOzxqi0GHxreGEdc`。
- commit 只修改 `airjet-simulation/collaboration/MAC_TASK.env` 并新增对应
  instruction；两者都是 `100644` regular blob。
- envelope 是严格 11 字段 schema v2 root task，`source=windows`、
  `target=mac`、`parent_task_id=NONE`、`hop=0`、`max_hops=0`。
- 任务执行前与本报告形成前均复核 clean `main`、
  `HEAD=origin/main=TASK_COMMIT`、ahead/behind `0/0`。

## 真实 watcher 调用证据

Git 外状态根：
`~/Library/Application Support/AirJetGitWatcher/`。

watcher 已从 C1 线性 fast-forward 到 `ccb50116...`，并产生：

- 签名任务快照 `events/mac-task-ccb50116....env`；
- 与 old/new commit 绑定的 wake prompt；
- 不可重放 claim
  `processed/ajm-git-windows-to-mac-e2e-20260715-001.claim/state`；
- runner 将 claim 从 `CLAIMED` 更新到 `CODEX_STARTED`；
- Terminal 中实际启动的独立 `codex exec`；
- 终态 claim `phase=CODEX_EXITED_0`；
- `events/completed-ajm-git-windows-to-mac-e2e-20260715-001-ccb50116....state`；
- watcher status `TASK_COMPLETED`。

用户没有亲眼确认 Terminal/Codex 窗口，因此可见性必须保持
`NOT_USER_OBSERVED`。

## 预检与测试

主协调会话在启动真实 wake 前完成：

- `install-skills.sh`：4 个 skill 与必需文件哈希全部 PASS；
- AirJet project audit：PASS，`required_files=106`、`manuals=7`、`csv_files=28`；
- Mac watcher 隔离矩阵：`CORE_CASES_PASS=80`、`EXPECTED_PASS_COUNT=80`、
  `OVERALL=PASS_CORE_RUNTIME_ENABLED_MANUAL`；
- trust 目录/文件权限为用户独占，三个固定 SHA256 匹配；
- 未发现 LaunchAgent、cron、login item 或其他 autostart 注册。

## 自动回程失败与恢复边界

被 watcher 启动的子 Codex 以 `workspace-write` 和 `approval_policy=never`
运行。它能读取和审核任务，但当前子会话权限策略拒绝写入
`.git/FETCH_HEAD`，且不允许网络 DNS/SSH；因此它无法独立 fetch、commit
或 push。子 Codex 准确 fail-closed，没有修改仓库，并把不能执行的测试
记为未执行，而不是伪造 PASS。

本报告是主协调会话的受限恢复：它可以证明真实 Windows→Mac
wake，但不能证明自动子会话的 Git 回程。因此本次总结为
`ROUNDTRIP_STATUS=PARTIAL`。修复 child Git/network 能力前，不得宣称
无人值守的完整双向 Git 闭环。

## AirJet 工程边界

本任务没有运行 CAD、ANSYS、CFD、优化或论文代写，也没有改变
P0–P6 结论。P0 仍为 `PASS v1`，P1–P6 仍未通过。
