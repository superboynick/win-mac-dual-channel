# P1-P3 48-hour sprint 002 teaching log

This log teaches the reproducible engineering path and its evidence limits. It does not write the
user's paper and does not upgrade a missing run to a result.

## START — signed task reception and baseline boundary

### Input

- Mac-signed root task `ajm-p1-p3-48h-sprint-20260715-002` at commit
  `31436c8d395cafe35a1eeab5e460062e48247da6`.
- P0 public-evidence freeze v1 and the current project status.
- Reviewed ANSYS automation profiles, installed watcher runtime, and Git-external trust roots.
- Measured start memory: 31.435 GiB physical, 9.268 GiB currently available.

### Model or equation

No geometry or physics model was executed at START. The intended dependency is deliberately ordered:

```text
complete-product P1 pilot
  -> P2 S0 displacement/frequency baseline
  -> P3 single-cell transient calibration baseline
```

The order prevents an isolated cell model from silently becoming the product model. The alternate
handoff route is signed-script SpaceClaim authoring followed by STEP plus a hash-bound semantic
sidecar; it does not claim native Named Selection transfer.

### Numerical and software checks

- Git main/clean/0-ahead/0-behind and exact task tip: PASS.
- Mac task signature and Windows trust-root hashes: PASS.
- Installed watcher bytes: 4/4 PASS.
- Project AirJet skills: 6/6 and 12/12 PASS.
- ANSYS static policy: 8 profiles / 5 tools PASS.
- Project audit: 106 required files / 7 manuals / 28 CSV files PASS.
- No ANSYS numerical solve was run; convergence and conservation are therefore `NOT_RUN`.

### Output

- A signed START evidence report.
- This teaching log.
- A first-draft evidence manifest that separates available claims from placeholders.

### Uncertainty and limitations

- Watcher/Codex startup evidence is execution-control evidence, not geometry or physics evidence.
- Available memory was below the signed task's 24 GiB threshold for a medium or larger P3
  dynamic-mesh baseline. Memory must be remeasured immediately before such a run.
- Native `.scdocx` attach, native parameterization, and native Named Selection transfer remain
  unproven. The STEP semantic route is reconstruction, not native transfer.

### Available for writing

The methods record may state that signed task reception and fail-closed static policy checks were
verified before the sprint and that formal engineering Gates remained unchanged.

### Prohibited wording

Do not state that ANSYS capability, full-product CAD, structural response, transient CFD, or any
P1-P6 Gate passed at START. Do not describe a future P2/P3 baseline as measured product behavior.

## Evidence-class reminder

- `D`: direct model-specific or direct run evidence.
- `P`: patent embodiment or range; a constraint, not an exact product fact.
- `I`: image/cross-source inference with derivation and uncertainty.
- `C`: calibration parameter to be identified with multiple metrics.
- `U`: unresolved; alternatives remain explicit.

Later entries must retain these classes and use the fixed sequence: input → model/equation →
numerical checks → output → uncertainty → available/prohibited wording.

## Phase A — archive run #22 and defer the connected route

### Input

- Signed-run commit `1a9696c3930a42cd8a30aafe7093b8acafd6dd59`.
- Suite `AJM005_T1_CONNECTED_SC_SUITE_20260715T021529059815Z_aa1180f6`, case
  `a5c-eedabacc1fc6`.
- SpaceClaim producer `a5c-eedabacc1fc6-f70b77c399ca` and connected Workbench consumer
  `a5c-eedabacc1fc6-027f5de8b724`.
- Fixed 34-byte child-entry sentinel and fail-closed file-channel state machine.

### Model or equation

This phase did not solve a product equation. It tested an observable software state machine:

```text
Workbench Edit
  -> direct RunScript call
  -> entry/build probe
  -> Exit
  -> second probe
  -> failure-pre/failure-post probes when the build contract is not terminal
```

`RunScript=RETURNED` and `entry=ABSENT` are separate observations. Their conjunction does not imply
that the child geometry build ran and failed. Likewise, a suite-level diagnostic failure does not
mean the downstream transfer was executed.

### Numerical and software checks

- Producer: 21.451068 s, exit 0, 8/8 assertions true, `PASS_PARTIAL_CAD_CAPABILITY`.
- Consumer: 136.554323 s, exit 2, root error
  `FAIL_RUNSCRIPT_RETURNED_ENTRY_AND_BUILD_ABSENT`.
- Exact classification: `RUNSCRIPT_RETURNED_ENTRY_ABSENT`.
- Entry and build were absent at post-RunScript, post-Exit, failure-pre, and failure-post; both probe
  error lists were empty.
- Share, save-data, Refresh, Mechanical, mesh, and project save were `NOT_REACHED`.
- All producer 20/20 and consumer 19/19 artifact-manifest entries were rehashed and matched.
- The Git-external ZIP contains 22 selected payloads plus `SHA256SUMS.csv`; its SHA-256 is
  `62b058ef4125704ef4d74624d23b5cc0093315ab29bc613cd0e55cf5d92b7a96`.
- After the correction addendum edits, the staged `suite-summary.json` SHA-256 was recomputed as
  `8535f0b561ed3f9fb4e8d89e84f205821af111880afaa48c8ff7f8551ffb0dec` and matched the
  evidence-manifest row exactly.

### Output

- Condensed Git evidence in
  `logs/evidence/AJM005_T1_CONNECTED_SC_SUITE_20260715T021529059815Z_aa1180f6/`.
- Two run-index rows and reality item `REAL-20260715-050`.
- Route state `DEFERRED_CURRENT_HOST_ROUTE`; no further connected marker probes in this sprint.
- Next-route requirement: signed SpaceClaim authoring followed by hash-bound STEP and semantic
  sidecar reconstruction.

### Uncertainty and limitations

- No immediate outer-process observation was captured when the suite ended. A delayed archive-time
  check found zero related processes, but it cannot prove immediate cleanup.
- A same-host/session runtime positive control that deliberately writes both entry and build files was
  `NOT_RUN`. Synthetic validator-state tests do not replace that runtime control, so absence is not a
  loader or session root-cause result.
- The absent entry is bounded to this run and these checkpoints. It does not prove that `.py` is
  unsupported or that the child can never run.
- External native attach, native parameterization, and native Named Selection transfer remain
  `NOT_PROVEN`.
- The fixture is disposable toolchain evidence, not a full-product model.

### Available for writing

The methods record may state that the direct RunScript call returned but the fixed child entry and
build report were not observed in this run, with exact classification
`RUNSCRIPT_RETURNED_ENTRY_ABSENT`. It may state that this evidence motivated deferring the current
connected route and adopting a hash-bound STEP plus semantic-sidecar route for further testing.

### Prohibited wording

Do not state that the child build executed and failed, that Python script files are unsupported,
that connected transfer failed or passed, or that Mechanical/mesh/project work was reached. Do not
upgrade P1 readiness or any P1-P6 engineering Gate from this diagnostic.

## 2026-07-15 — V02 split STEP 为什么进程成功仍必须判工程失败

### 本轮做了什么

同一受审 MCP 会话先重新生成完整 V02 两流体区，再从 native staging 分别删除另一 body，导出
`upstream.step` 和 `downstream.step`。两者都被 SpaceClaim 成功回读，因此 converter 进程是
`PROCESS_EXITED_0`；但 runner 继续比较 body 数、封闭性、face count、bbox 和 volume，没有把
“软件没崩”当成“工程可用”。

### 关键数据

- upstream：1 body、closed/manifold、2044→2044 faces；bbox 最大分量漂移 0.014975 mm。
- downstream：1 body、closed/manifold、bbox/volume 保持；978→6 faces。
- 结论：`FAIL_SPLIT_STEP_CONVERTER / SPLIT_STEP_BODY_SHAPE_OR_FACE_COUNT_NOT_PRESERVED`。
- Workbench、Mechanical、mesh、physics、formal 006、P1--P6：全部 `NOT_RUN`。

### 为什么 978→6 比“文件能打开”更重要

downstream native 的 978 faces 包含 972 个孔口界面印记和 6 个外表面。独立 STEP 回读只剩 6 faces，
说明 translator 把共面孔口印记愈合掉了。几何外包络和体积不变并不等于内部接口语义仍存在；如果
放宽 face-count Gate，后续模型会看起来像一个正常盒体，却没有可识别的 972 孔口连接。

### 为什么下一版改成真实孔喉

V02 把上下流体区放在零厚度共享平面两侧，太依赖 CAD kernel 保存 imprint/shared-face identity。
V03 将用 0.10 mm C 类候选厚度建立 972 个真实圆柱 throat，并优先 Boolean 为一个连续流体体。
这把“接口语义”变成不可被平面 healer 轻易删除的三维流道。0.10 mm 是建模候选，不是产品实测；
后续必须对 0.05--0.20 mm 做不确定性扫描。

### 论文中现在可以与不可以写什么

可以写：本项目用 round-trip topology fingerprint 发现独立 STEP 表示会消除零厚度孔口印记，因而
转向显式有限厚度流道表示。不能写：AirJet Mini 的真实孔板厚度是 0.10 mm、split STEP 证明产品
内部没有孔、或本轮已经完成网格/CFD/P1。

## 2026-07-15 — 为什么 Fluent 显示 volume mesh complete 仍不能写 mesh PASS

V03 high-resolution consumer 已通过 STEP import、4 inlet/1 outlet/972 throat role queries、局部
sizing、surface mesh 与 boundary type update。Fluent transcript 内部报告 1,580,277 cells、12 cell
zones、min OQ 0.23064141；随后 Student license error 在 API 返回前发生。

判断链必须写完整：内存态生成 → 超 Student 1M 限额且出现 12 zones → API 抛错 → 脚本没有运行
mesh_exists/单区/972 occupancy/integrity/Student guard → 没有 `.msh.h5`/hash。前几级是已观察能力，
最后交付仍是 FAIL。不能用 Fluent 的 “cells were created” 一句跳过自动化 postconditions。

C1 只把分辨率降低并把尺寸增大到 throat 0.075、surface 0.05--0.75、volume 0.75 mm，用于拓扑和可保存性诊断。
它不改变 972 throats，不允许合并多 zones，也不代表网格独立性。

## 2026-07-15 — P2-S0 为什么只是 CAD 前置基线

Windows 已真实生成 7×7 mm 中央锚固等效板，Native/STEP round-trip、语义区域、体积和文件哈希
16/16 闭合。它证明我们有可送进 Mechanical 的几何，不证明真实 AirJet 膜片、材料或频率。

三个 EQ-A/B/C 行是 paired C-class sensitivity candidates。Mechanical、modal、harmonic、physical
amplitude 都是 `NOT_RUN`，所以论文只能把它放在“方法与模型准备”，不能放在“结构结果”。下一步必须
在同一 MCP session 重跑 producer 后立刻接 modal smoke，因为旧 job identity 不跨 server restart。
