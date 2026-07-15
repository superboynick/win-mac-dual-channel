# AJM005 alternate-route v2 通过解释

- 运行：`AJM005_T1_ALTERNATE_ROUTE_SUITE_20260715T100443733301Z_d1743e81`
- UTC：2026-07-15T10:04:43.733301Z 至 2026-07-15T10:06:02.423387Z
- Windows：`LAPTOP-LCCLM2HI`
- 签名提交：`9a88b7ad26d5d5c9f35d8a5f956df7038cfca0fd`
- suite：`PASS_ALTERNATE_ROUTE_SEMANTIC_CONFIRMATION`
- 原始 suite JSON：201157 bytes，SHA-256 `dc3c52688fbd63a41f3ace4afceb55a1294c5464c4d0940636f2122a4e2f4ab0`
- closeout：3922 bytes，SHA-256 `8a1065da67e7e35d511845a8fadfdf0f7757c39490513486b7cf5ff0d6082cf9`

## 实际证明

SpaceClaim v2 producer 与 Workbench v2 consumer 都在同一已验证 Git 提交下 `PROCESS_EXITED_0`，各自声明报告通过哈希复算和 v2 判据验证。producer 完成脚本等效参数化、流体几何连通、原生保存/重开、STEP 导出/重导、语义侧车与实际源文件哈希链；consumer 完成 predecessor 身份绑定、STEP solver-side 语义重建、1/1/11 边界基数检查、负向控制、粗网格与 Workbench project 保存。

最终关键产物：

- STEP：SHA-256 `268011ef6f82d1e7c404c37de64e6bf533a5bbcf5373cdcee0a31ec4c0958a86`
- producer v2 report：`6f2b007dbda3a22e63da9ab55cfc4791e95ecdc56e135b9612345e0fef358b3b`
- consumer v2 report：`359eb526c005a72cc439cb5788d3e81da6bccae2de107c34b315e78c0fad4a71`
- Workbench project：50555 bytes，SHA-256 `168406bdad78b80d59fa0525cc78745e0a104af3b9523aeee24ee13e8deb369b`

## 根因链

在 v2 wrapper 中用 `execfile(base_path)` 执行历史 v1 脚本时，IronPython 不再提供直接 `Part.GetAllBodies()` 扩展语法绑定；此前的 `globals().copy()` 修复和显式 `PartExtensions` import 均未关闭该差异。一次性 Windows 诊断实际观测到 STEP 根层 `Bodies=0`、`Components=1`，直接扩展与 `.NET MethodInfo.Invoke` 都返回同一唯一 body。commit `9a88b7a...` 因此改为精确反射调用 v261 的单参数 `GetAllBodies(IPart)`；正式 suite 随后通过。该诊断支持的是宿主绑定根因，不是 AirJet 产品结构结论。

## 主张边界

本次只证明 alternate CAD/semantic handoff toolchain 可用于下一阶段完整产品 006，不是 P1 Stage PASS，也不是产品几何已完成。以下继续保持：

- `P1_STAGE_GATE=NOT_RUN`
- `P1_CAD_TOOLCHAIN_SCOPE=ALTERNATE_ROUTE_ONLY`
- external native attach / native parameterization / native Named Selection transfer 均 `NOT_PROVEN`
- connected route 仍 `DEFERRED_CURRENT_HOST_ROUTE`
- P2--P6 均 `NOT_RUN`

closeout 的技术建议是 `START_006_ALTERNATE_ROUTE_ONLY`，Student toolchain 状态为 `PASS_START_P1`。
