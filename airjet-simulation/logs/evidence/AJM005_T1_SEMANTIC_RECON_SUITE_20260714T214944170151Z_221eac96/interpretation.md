# AJM-005 T1 STEP semantic reconstruction：第十五次诊断 PASS

第十五次只把 INLET 的 hard predicate 从 `centroid+area` 换成上一轮实测支持的
`centroid+GeoSurfacePlane+2 edges+abs(z-normal)`。中心容差、OUTLET 的 centroid+area、WALLS
complement、四项 negative controls 和全部 Gate 均未放宽。producer 面积仍留在证据中，但角色是
`DIAGNOSTIC_ONLY`。

签名 commit `7a7f8e0...` 的真实 Windows 运行通过 STEP、semantic sidecar、producer report 与 MCP
manifest 的身份链。Mechanical 得到 1 body/13 faces，唯一分类并重建
`INLET/OUTLET/WALLS=1/1/11`；创建前同名对象为 0，创建后对象数为 1/1/1、实体数为 1/1/11。0 match、
multiple match、overlap 与 incomplete coverage 四项拒绝测试均通过，随后生成 1063 nodes/513
elements 的粗网格并保存 50593-byte Workbench project。

因此 suite 与 Workbench report 可以准确写成
`PASS_STEP_SEMANTIC_RECONSTRUCTION_DIAGNOSTIC`。它证明的是：对这个
`DISPOSABLE_CAPABILITY_FIXTURE_ONLY` 小模型，hash-bound STEP+sidecar 可以在 solver 端确定性重建
边界语义。它不证明 STEP 原生携带语义，不证明 `.scdocx` attach、native Named Selection transfer
或 native driving parameter，也不是 AirJet 产品内部拓扑事实。

canonical native claims 仍全部为 false，P1 CAD toolchain readiness 仍为 BLOCKED，P1--P6 仍
`NOT_RUN`，可见性仍为 `NOT_USER_OBSERVED`。报告中的
`DIAGNOSTIC_PASS_CANNOT_CLOSE_NATIVE_TRANSFER_GATE` 是防止误读的边界声明，不是本轮运行错误。
