# AJM-005 T1 connected SpaceClaim：首轮可观测性失败

本轮使用独立的 connected-document diagnostic，而不是修改已有 external `.scdocx` transfer profile。
Workbench 从 `GeometryFilePath=""` 的空 Geometry cell 启动 SpaceClaim，执行仓库签名的 build script，
再计划将该 Geometry component share 到 Static Structural。前驱只提供 `spaceclaim_cad_t1.json` 作为
对照，没有把 `.scdocx`、STEP 或 sidecar 交给 connected route。

SpaceClaim producer 先以 24.460107 秒正常退出，八项 assertions 全 true。connected Workbench job
随后确认前驱身份和空 Geometry cell；`Edit(Interactive=False, IsSpaceClaimGeometry=True)`、
`RunScript(ScriptFile=...)`、`Exit()` 都返回。失败发生在 journal 检查嵌入脚本报告时：
`connected_spaceclaim_build.json` 不存在，因此报告为
`FAIL_CONNECTED_EDITOR_BUILD_REPORT_MISSING`。share、save-data、Model container、Refresh、Mechanical
inspection、Named Selection 检查、mesh 和 project save 都未到达。

这个 reach 不能证明嵌入脚本成功执行，也不能证明几何构造失败。当前脚本在建立自己的 `result` 和
`try/except` 之前读取 `AIRJET_JOB_DIR`；如果 connected SpaceClaim 进程没有继承该环境变量，脚本会在
最早处退出且无法写自诊断报告。其他仍开放的解释包括：`RunScript` 的异常没有传播到 Workbench、
脚本在任何早期 import/API 处失败，或 `RunScript` 返回语义与报告落盘时序不同。现有证据只能把问题
定位为“build report 未生成”，不能把环境变量假设写成已确认根因。

下一次最小实验只改善可观测性：由 Workbench 在生成 build script 时嵌入绝对 report/job path，并在
任何 SpaceClaim API/import 前写 early sentinel；随后用顶层 catch 写出 stage、exception type 和
traceback。几何、connected editor route、predecessor scope、Mechanical 合同和 Gate 边界不变。
若 sentinel 仍不存在，再转查 `RunScript` 启动/脚本格式；若 sentinel 存在且报告给出异常，再只修该
精确错误。

suite 保持 `FAIL_CONNECTED_SPACECLAIM_TRANSFER_DIAGNOSTIC`，P1 readiness BLOCKED，P1--P6
`NOT_RUN`，可见性为 `NOT_USER_OBSERVED`。本轮没有测试 external `.scdocx` attach、native Named
Selection transfer、native parameterization 或完整产品 CAD，不能将其写成上述能力的失败或通过。

Workbench CoreEvents 另记录了 RSM 未安装/ProgramData 绝对路径警告。该警告出现在 project 创建前，
但本轮未请求远程队列或求解，且之后 Edit/RunScript/Exit 均返回；它作为现实环境噪声保留，目前没有
证据把它与 build-report 缺失建立因果关系。
