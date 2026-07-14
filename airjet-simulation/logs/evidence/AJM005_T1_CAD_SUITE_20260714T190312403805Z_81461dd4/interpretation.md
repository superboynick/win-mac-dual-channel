# AJM-005 T1 CAD transfer suite：第二次失败

第二次真实运行使用签名 commit `aa914a65bf3a8292ae2c6ec9f781fa2fb4381179`，证明上一轮
`.NET String[]` 修复有效：脚本完成 Named Selection 查询、原生文件和 STEP 保存以及两次重开，
不再出现类型异常。新的几何断言暴露了两个需要分别区分的问题。

第一，v261 `Combine.Merge` 返回 `Success`，但结果体积只有 `200 mm³`、bbox 最低点为
`z=1 mm`、`INLET=0`；预期应为 `203.14159265358978 mm³`、`zmin=0`。签名运行后再对照本机
官方 v261 `space_claim_geometry.py`，确认旧脚本把 XML 的三点短描述解释反了：官方实例以
`p1→p2` 定义圆柱轴线、`p2→p3` 定义半径；旧点组实际建立的是沿 x 而不是沿 z 的圆柱。
因此进程成功和 Boolean 命令成功都不能代替几何指纹。修复采用正确向量语义，并把圆柱延伸到
`z=1.1 mm` 与 cavity 形成 0.1 mm 重叠；扣除重叠后解析 union 体积仍是
`192 + π + 8 mm³`。下一次报告会在 Boolean 前先断言原始圆柱的体积和 bbox。

第二，STEP 文件是非空的 ISO-10303-21 文本，且文件内有一个
`MANIFOLD_SOLID_BREP('AJM005_T1_FLUID', ...)`，但单参数 `DocumentOpen.Execute(step_path)` 后
根层 body count 为 0。本机官方脚本遍历 `GetRootPart().GetAllBodies()`，v261 API 说明它同时返回
当前 part 和子组件中的 body。修复因此保持 open 路线不变，只改为记录 root body、component 和
all-body count；若 all-body 仍为 0，再以独立新 job 检验显式 `ImportOptions.Create()`，不在一次
重试里混合两个 STEP 假设。

本轮 SpaceClaim declared report 为 `FAIL_DIRECT`；Workbench 正确写
`BLOCKED_UPSTREAM`，没有启动。P1 readiness 仍 BLOCKED，P1–P6 仍 NOT_RUN。原 suite、report、
job state、日志和 STEP 的哈希全部保留；修复只允许用新脚本 SHA、签名 commit 和新 job 重试。
