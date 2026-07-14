# AJM-005 T1 STEP semantic reconstruction：第十四次 solver topology 观测

第十四次只在 13-face 失败图中增加 `SurfaceType`、edge count 和 centroid normal；分类、容差、短路径
和 Gate 不变。全部 13 个面的三类 API 都返回，error 字段均为 null。入口位置 face 44 被观测为
`GeoSurfacePlane`、2 edges、normal `[0,0,-1]`，centroid 仍精确为 `[10,5,0] mm`。圆柱侧壁 face 45
为 `GeoSurfaceCylinder`；矩形 outlet face 54 为 plane、4 edges、`[1,0,0]`。

在这一个 disposable fixture 中，`centroid=[10,5,0] + plane + 2 edges + abs(z-normal)=1` 只匹配 face
44；producer area 仍保留为诊断量，但不适合作为 solver hard anchor。下一轮的唯一算法变量将只把
INLET predicate 从 centroid+area 改为 centroid+solver-topology；OUTLET 继续 centroid+area，WALLS
继续 complement，1/1/11、互斥、全覆盖和四项 negative controls 不变。

这项校准规则只属于 005 可删除小模型，不可复制成 AirJet 产品内部事实。suite 当前仍 FAIL；
Named Selections 和 mesh 尚未到达，P1 readiness 继续 BLOCKED，native claims 全 false。
