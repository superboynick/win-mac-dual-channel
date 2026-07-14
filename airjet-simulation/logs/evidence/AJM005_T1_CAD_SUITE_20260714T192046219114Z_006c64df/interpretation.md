# AJM-005 T1 CAD transfer suite：第三次失败

第三次真实运行使用签名 commit `74e855733613baa80d7d821b961c629268f4ba59`。正确的圆柱向量与
Boolean 前指纹均通过；最终 union 为 `203.14159265358984 mm³`、bbox
`[2,2,0]→[20,8,3] mm`、单片闭合，`INLET/OUTLET/WALLS=1/1/11`。原生 `.scdocx` 关闭后
重开得到相同体积、bbox、拓扑与命名组。因此第二轮发现的几何构造问题已经由新签名运行关闭。

STEP 仍未通过，但失败位置更精确：`GetRootPart().GetAllBodies()` 已得到唯一 body；其 `Shape`
运行时类型为 `TrimmedSpace`。这个 v261 `ITrimmedSpace` occurrence 暴露 Volume 等通用有限区域
属性，不暴露 native `Modeler.Body.PieceCount`；旧通用指纹函数因此抛出 AttributeError。同版本
接口审查确认 `IDesignBody.Master.Shape` 才是提供 `PieceCount/IsClosed/IsManifold` 的
`Modeler.Body`。第四版因此用 occurrence shape 验证放置后的 bbox/volume，用 master shape 验证
`PieceCount=1`、`IsClosed=true` 与 `IsManifold=true`，并记录两者 runtime type 和拓扑来源；
没有因交换格式类型不同而降低 STEP Gate。

本轮 declared report 仍是 `FAIL_DIRECT`，Workbench 仍是 `BLOCKED_UPSTREAM`，所以尚不能写
`PASS_PARTIAL_CAD_CAPABILITY` 或 CAD transfer PASS。P1 readiness 仍因原生参数化保持 BLOCKED，
P1–P6 仍 NOT_RUN。所有原始文件留在 Windows，仓库只保存带哈希的凝练证据。
