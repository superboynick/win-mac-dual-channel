# AJM-005 T1 STEP semantic reconstruction：第十三次失败面图观测

第十三次运行只把失败分支 observability 提前到 face-count 与真实 partition validation 之前。分类
规则、短 case ID、STEP route、sidecar 和 `0.02 mm / 0.02 mm²` 容差不变。结果复现
`INLET=0, OUTLET=1, WALLS=12`，但这次 1 body、13 faces、四项 negative controls 与完整 face map
均被机器报告保存；相应 assertions 为 body PASS、negative controls PASS、project save PASS，semantic
reconstruction 和 mesh 仍 FAIL。

入口未匹配的直接原因已量化。Mechanical face 44 的 centroid 正好是 `[10,5,0] mm`，与 producer
入口中心差为 0，但它报告的面积是 `2.0 mm²`，而 sidecar 入口面积是 `π mm²`，差
`1.141592653589787 mm²`，远超 `0.02 mm²`。同一区域的 curved face 45 也从 producer 的约
`6.283185 mm²` 变为 `5.832786 mm²`，且底面 face 51 为 `94.0 mm²`，而 producer 指纹为约
`92.858407 mm²`。矩形 outlet 仍以 `[20,5,2] mm / 4 mm²` 精确匹配。

因此，跨 SpaceClaim→STEP→Mechanical 后，以 `GeoFace.Area` 对圆形入口区域做绝对硬锚点不稳定；
但仅凭 centroid 唯一也还不足以直接成为更一般的整机规则。下一轮只增加 solver-side topology
观测：`SurfaceType`、edge count 与 centroid normal，分类和容差继续不变。确认 face 44 是唯一平面、
单边界环、z-normal 的入口 cap 后，再另立单变量分类合同。

suite 继续 FAIL；没有创建 Named Selections、没有 mesh；native claims 全 false，P1 readiness
BLOCKED，P1–P6 `NOT_RUN`。
