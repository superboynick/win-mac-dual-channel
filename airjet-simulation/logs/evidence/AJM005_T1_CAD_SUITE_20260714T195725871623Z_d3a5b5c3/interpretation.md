# AJM-005 T1 CAD transfer suite：第六次运行

第六次真实运行使用签名 commit `d10fa5192d466c448ea7c04769530434885476e3`。SpaceClaim 的
七项 partial CAD 能力第三次连续通过。Workbench 仍验证了本轮精确 predecessor；独立 Geometry
source system、source `.scdocx SetFile` 和 target Static Structural system 均成功建立。

本轮唯一改变的是数据流拓扑：由“文件直接挂到 Static Geometry”改为“独立 Geometry source
component 调用 `TransferData(TargetComponent=Static.Geometry)`”。调用没有返回，v261 错误为
“几何结构无法使用组件几何结构”。Model update、Mechanical inspection、网格和 project save
全部未到达。这不是前两轮约 160 秒的 CAD attach 失败，而是约 16 秒内暴露的 component
兼容性拒绝。

因此普通 Geometry component→Static Geometry component 不是本机可用的 `TransferData` 组合；
不能因为 `TransferData` 方法本身存在就假定所有 component 类型可相互传递。下一最小实验使用本机
官方 standard Geometry post-import journal 的 `ComponentsToShare=[source_geometry_component]`
架构，继续保持 `.scdocx`、Named Selection 属性、Model update 与全部验收断言不变。完整 suite
仍 FAIL，P1 readiness BLOCKED，P1–P6 NOT_RUN。
