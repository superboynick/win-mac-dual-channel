# P1 CAD 独立复核方法（007）

状态：复核流程已定义；等待真实 006 产物，当前不能执行或宣布 P1 PASS。

## 1. 为什么需要 007

006 的职责是生成候选 CAD 和证据，只能输出 `PENDING_PEER_REVIEW`。生成模型的同一会话不能同时给自己的 Gate 判 PASS；独立 peer 可以位于 Mac，也可以位于另一个 Windows 会话。007 先校验 006 报告身份、005/006 Git 祖先关系、精确 006 commit 的合同 bundle、运行目录边界、9 个 variant 的必需文件角色、机器检查表、252 行证据映射以及全部外部文件大小/SHA256，再从 **006 commit** 的不可变 `NOT_RUN` Gate 模板生成独立 worksheet。

## 2. 准备 review packet

逐字节保留原始 006 报告和原始 manifest，把完整 Windows 运行目录复制到审查端可只读访问的位置。不得修改 manifest 中的 Windows 路径，也不得只复制挑选过的成功文件。输出目录必须不存在且位于 Git 仓库外：

```bash
python3 airjet-simulation/checklists/prepare_p1_cad_review.py \
  --repo /absolute/path/to/win-mac-dual-channel \
  --report /absolute/path/to/AIRJET_P1_FULL_PRODUCT_CAD_BUILD_006.txt \
  --manifest /absolute/path/to/external-files.csv \
  --run-root /absolute/path/to/AJM-P1-CAD-006/run-id \
  --output-dir /absolute/path/to/AJM-P1-REVIEW-007-run-id
```

脚本用 `PureWindowsPath` 检查每个原路径确实位于报告的 `EXTERNAL_RUN_DIRECTORY` 下，只取相对部分并映射到 Mac `--run-root`。不同盘符、UNC 漂移、`..`、空相对路径、symlink、目录外文件、未入 manifest 的普通文件都会拒绝。报告中的 `RUN_ID`、`EXTERNAL_FILE_MANIFEST`、`MASTER_MODEL_PATH/SHA256` 还要与映射结果和 manifest 精确交叉核对。

007 从 `git show <006-commit>:<path>` 读取 Gate、variant、参数、九条 internal rules、三类 branch 表、layout/thickness、五个 geometry contracts 和两个生成器，重算 `P1_CONTRACT_BUNDLE_SHA256` 及三张核心表哈希。后来的 HEAD 可以包含审查代码修订，但不能拿后来合同替换 006 实际使用的合同。

证据包只有在以下条件全部满足时才输出 `REVIEW_PACKET_PREPARATION=PASS`：报告构型/variant/自动检查字段完整；全局和每 variant 固定文件角色各恰好一份；`REPORT_005_COPY` 的字节、唯一键、工具链身份和 commit 真实匹配；三个派生 variant 各有父项参数 diff 和几何结果 diff；完成状态的 STEP 文件或明确限制日志齐全；九张 `AUTOMATED_CHECKS_CSV` 数值通过；`GATE_EVIDENCE_006_CSV` 精确覆盖 252 个键并引用 manifest 哈希；manifest 数据行数和目录内普通文件数量闭合。

`REVIEW_PACKET_PREPARATION=PASS` 只说明证据包具备进入独立复核的条件，没有给任何 Gate 判 PASS。

## 3. 252 行逐项复核

独立审查者在 `P1_CAD_INDEPENDENT_REVIEW_007.csv` 中只使用以下 `review_status`：

- `NOT_REVIEWED`：准备脚本初始值；最终报告中不得残留；
- `PASS`：证据文件存在、SHA256 匹配、数值满足 tolerance，且截图/CSV/原生重开记录一致；
- `FAIL`：有相反证据或数值不满足；
- `BLOCKED`：证据缺失、无法打开或无法独立判断。
- `LIMITATION_ACCEPTED`：只允许用于 `G4_STEP_TRANSFER` 且该行 `hard_gate=false`、006 为 transfer-limited 完成状态；必须填写 evidence、reviewer、date 和接受理由。

worksheet 中的 `006_measured_value`、`006_suggested_status` 和预填 evidence 只是生成端声明。审查者必须独立填写 `review_status`，不能批量复制 006 建议。

必须逐项核对 9 个变体。三个 `DERIVED_SINGLE_FACTOR` 还要把参数 diff 与父变体对比，证明只有声明的 `changed_factor` 改变。接口复核使用 A/B 两套归属正确的 Named Selections；`{NNN}` 必须完整展开为每个 cell。

Mac 不能原生打开 SpaceClaim 文件时，不能把截图等价为原生重开。006 的可见 Windows 重开/Workbench 传递日志是第一层证据；最终 P1 复核还要求用户或另一可见 Windows 会话抽查母版、主 balanced、一个 sentinel 和三个单因素派生原生文件。

## 4. P1 Gate 判定

只有同时满足以下条件，独立审查报告才可写 `P1_REVIEW_RECOMMENDATION=PASS`：

- 252 行中所有 `hard_gate=true` 均为 `PASS`；
- STEP 行可为 `PASS`，或在上述严格条件下为 `LIMITATION_ACCEPTED`；其他行禁止使用该状态，且原生重开和 Workbench/Named Selection 传递必须 PASS；
- 006 报告、manifest、原生文件、STEP/流体、截图、日志和 worksheet 均有 SHA256；
- Git commit 与输入合同一致，未出现隐藏常量、删 cell/孔或证据升级；
- 用户完成关键原生文件的可见抽查。

任一 hard gate 为 `FAIL/BLOCKED` 时，P1 保持 `INCOMPLETE`，回到新的 006 run；不得覆盖旧 run。准备脚本、仓库审计或 006 完成状态本身都不能替代这一步。

完成 worksheet 和六项原生文件可见抽查记录后，先运行 finalize 校验；仍使用同一 `--repo/--report/--manifest/--run-root/--output-dir`，并增加：

```bash
python3 airjet-simulation/checklists/prepare_p1_cad_review.py \
  --repo /absolute/path/to/win-mac-dual-channel \
  --report /absolute/path/to/AIRJET_P1_FULL_PRODUCT_CAD_BUILD_006.txt \
  --manifest /absolute/path/to/external-files.csv \
  --run-root /absolute/path/to/AJM-P1-CAD-006/run-id \
  --output-dir /absolute/path/to/AJM-P1-REVIEW-007-run-id \
  --finalize-worksheet /absolute/path/to/P1_CAD_INDEPENDENT_REVIEW_007.csv \
  --spot-check-record /absolute/path/to/P1_CAD_NATIVE_SPOT_CHECK_007.csv
```

finalize 会重新校验原始证据、精确 006 commit、243 个 hard Gate、9 个 STEP Gate、`LIMITATION_ACCEPTED` 边界、reviewer/date、全部 evidence 哈希，以及母版、primary balanced、低 cell sentinel 和三个派生原生文件共六项可见抽查。只有全部通过才写 `P1_REVIEW_RECOMMENDATION=PASS`，同时保持 `P1_STAGE_GATE=PENDING_REVIEW_RECORD_COMMIT`；它不会直接篡改 Git 阶段状态。

最终再由单独审核提交把复核摘要和小型结果表纳入 Git，并在 `PROJECT_STATUS.md`、`MODEL_ANNOTATIONS.md` 和阶段 Gate 中记录版本、reviewer、日期、006/007 报告 SHA256。原始 CAD/Workbench/mesh 仍只保留外部路径和哈希。
