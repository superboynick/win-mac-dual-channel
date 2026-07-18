# 双 Windows Codex 并行执行计划

状态基线：P0 已通过；P1-P6 均未通过。两个 Windows Codex 是独立完整求解线，Mac 只负责协调、审计和 Git 集成。

## Codex A — 完整 ANSYS 主线（强制走通）

`P1 SpaceClaim CAD → P2 Mechanical → P3 Fluent 单 cell → P4 Fluent 整机气动 → P5 ANSYS CHT → P6 校准与不确定性`

当前最先任务是正式 C7 两阶段网格 runner。已有 34,883-cell 网格只覆盖 actuator-gap tile，且只有一个 generic wall zone；所有零流求解均为失败诊断，不能作为 P3/P4 结果。

## Codex B — 完整 OpenFOAM 复算线

`T0 工具链 smoke → P3 单 cell 独立复算 → P4 整机气动复算 → P5 整机 CHT 复算 → P6 交叉验证`

Mac 只读审计确认本机没有 OpenFOAM；这不是 Codex B 的运行结果。B 必须在独立 Windows worktree 中验证实际工具链，未获安装授权时先完成 source-only 静态准备，不得用 mutable image 或 placeholder AirJet physics 冒充结果。

## 边界与交集

- A 与 B 可以共享冻结几何、D/P/I/C/U 参数、边界合同、schema 和只读结果。
- A 不修改 B 的 OpenFOAM case、脚本或运行目录；B 不修改 ANSYS approved profiles、scripts 或原生产物。
- 同一故障只设一个 owner。另一方最多做只读独立复核，不重复试跑。
- A 的 ANSYS 结果不能被 B 替代；B 的独立复算不能被 A 的 Fluent 结果替代。
- 两线都不得越过 P1-P6 Gate；单 cell 永远只是校准子模型。

## 协调与验收

执行合同见 `DUAL_WINDOWS_EXECUTION_CONTRACT.md`。每个任务必须提交 scope、owner、ETA、检查点、产物、验收条件和 blocker。Mac 协调端到点催交，以 Git 证据验收；进程存在、脚本 exit 0 或口头完成均不算交付。
