# 005 T1 CAD→Workbench 学习工作簿

更新时间：2026-07-15
当前状态：**已连续保留到第二十一次签名实跑；第二十二次只完成 RunScript-only 实现与静态审查，
尚未签名 Windows 实跑。SpaceClaim partial CAD 与 STEP+sidecar solver-side reconstruction diagnostic
已分别 PASS，但 external native attach、connected editor scripting、native Named Selection transfer 和
native parameterization 尚未闭合，P1 readiness 继续 BLOCKED。**

这份工作簿随实作同步更新。它记录的不只是最后命令，还包括为什么这样建、哪些 API 只在
本机 v261 证据中出现、第一次尝试可能在哪里失败，以及一次结果最多能支持论文中的哪句话。
这里的几何是可删除的工具链小模型，不是 AirJet 产品单元，更不是整机复原结果。

## 1. 本轮只回答两个问题

1. SpaceClaim v261 能否用固定脚本建立一个可复算的连通流体实体，创建
   `INLET/OUTLET/WALLS`，保存原生文件，并在关闭后重开及 STEP 回读？
2. Workbench 能否只接收上一步同一签名 commit、同一 case、精确 job ID 的原生文件，并在
   Mechanical 中看到一个 body、三个非空 Named Selections 和真实粗网格？

即使两项都通过，允许的表述也只是“P1 所需的部分 CAD 构建/传递工具能力在小模型上通过”。以下内容
仍是 `NOT_RUN`：整机 CAD、执行片结构、动态 CFD、整机气动、CHT、标定与不确定性。

## 2. 为什么先做可解析验证的小流道

正式 AirJet Mini 候选内部结构有大量 `P/I/C/U` 参数。若直接用整机模型测试工具链，失败时
无法区分是 ANSYS API、几何拓扑、产品假设还是网格问题。T1 因而选择一个体积、包围盒和边界
面积都能手算的三段流体体：

| 部分 | 几何 | 坐标范围或定义 | 解析体积 |
|---|---|---|---:|
| cavity | block | `(2,2,1)` 到 `(18,8,3)` mm | `16×6×2 = 192 mm³` |
| inlet | cylinder | 直径 2 mm，构造为 `z=0→1.1 mm`；其中 `z=1→1.1` 与 cavity 重叠 | raw `1.1π mm³`，对 union 的唯一贡献为 `π mm³` |
| outlet | block | `x=18→20, y=3→7, z=1.5→2.5 mm` | `2×4×1 = 8 mm³` |

入口特意向 cavity 内重叠 0.1 mm，避免把“恰好接触是否可合并”混入当前工具链问题；outlet 与
cavity 相交。扣除入口重叠 `0.1π mm³` 后，Boolean union 理论总体积仍为：

```text
V = 192 + π + 8 = 203.1415926535898 mm³
bbox min = (2, 2, 0) mm
bbox max = (20, 8, 3) mm
```

外部另建 `20×10×4 mm` block，只用于证明完整文档能同时保存外体和内部流体。传给 Workbench
的是删除外体后的单流体原生文件，避免下游把第二个实体误当流体域。

## 3. API 不是看名字猜：圆柱三点的实例

本机 v261 XML 把 `CylinderBody.Create` 的三个点简写为：

```text
centerPoint = center of the defining circle
startPoint  = start of the cylinder
endPoint    = end of the cylinder
```

首次静态审查把它解释成“圆心、圆周点、挤出后的圆周点”，但第二次签名运行得到
`200 mm³ / zmin=1 / INLET=0`，证明该解释没有建立预期 z 轴入口。随后重新读取同机官方
`space_claim_geometry.py`：table leg 的第一点和第二点位于轴线两端，第三点由第二点沿半径方向
偏移。可操作的同版本语义因此是：

```text
p1 -> p2 = 轴向量与圆柱高度
p2 -> p3 = 第二个端圆平面内的半径向量
```

所以半径 1 mm、沿 `+z` 从 0 到 1.1 mm 的入口应写成：

```python
CylinderBody.Create(
    Point.Create(MM(10), MM(5), MM(0)),
    Point.Create(MM(10), MM(5), MM(1.1)),
    Point.Create(MM(11), MM(5), MM(1.1)),
    ExtrudeType.ForceIndependent,
)
```

第三版在 Boolean 前直接断言 raw cylinder 为 `1.1π mm³`，bbox 为
`[9,4,0]→[11,6,1.1] mm`；第三次签名运行已确认该断言通过。这个例子比“静态审查发现错误”
更有学习价值：即使使用了同版本 XML，
短参数名仍可能被人错误解释；必须让同版本官方实例和运行后的体积/bbox/面共同约束语义。旧的
错误判断保留在现实日志中，不能把被实跑推翻的推理从项目历史里删除。

## 4. 本机同版本资料从哪里来

以下是 Windows 官方 ANSYS Student v261 安装中的直接依据。路径作为可复核 provenance 记录，
不把厂商整份文档复制进 Git：

| 用途 | 本机路径 | 采用的语义 |
|---|---|---|
| SpaceClaim solid/group/save | `D:\ansys\ANSYS Inc\ANSYS Student\v261\optiSLang\examples\01_tutorial_examples\03_workflows\table\table_load\space_claim\space_claim_geometry.py` | `BlockBody.Create`、`CylinderBody.Create`、`CreateAGroup`、`DocumentSave.Execute` |
| Boolean/Named Selection | `...\space_claim\sc_table.py` | `Combine` 和命名选择示例；Boolean 后仍必须复算拓扑 |
| SC→Workbench→Mechanical | `...\space_claim\table_space_claim_avz.wbjn` | `UpdateUpstreamComponents`、`Refresh`、`SendCommand`、`GetObjectsByName` |
| Workbench import properties | `D:\ansys\ANSYS Inc\ANSYS Student\v261\aisol\CommonFiles\CommonPages\PostImportScripts\PreferenceChanges.wbjn` | `GetGeometryProperties()` 返回对象可直接设置 Named Selection import 字段 |
| v261 SpaceClaim API | `D:\ansys\ANSYS Inc\ANSYS Student\v261\Discovery\SpaceClaim.Api.V261\SpaceClaim.Api.V261.Scripting.xml` | 圆柱三点、Combine、DocumentOpen/Save、VolumeExtract 的精确签名 |

版本优先级是：本机 v261 类型/示例 > 对应版本官方在线文档 > 其他版本博客或录屏。在线
`stable` 页面以后可能前移，不能单独作为 2026 R1 的精确 API 证据。

## 5. 参数化到底通过了什么

T1 脚本先用同一构造函数分别建立 `16×5×2` 和 `16×6×2 mm` block，检查体积从
`160` 变为 `192 mm³`，并检查 `ymax` 变为 `6 mm`。这叫
`SCRIPT_EQUIVALENT_TWO_BUILDS`：证明固定参数输入确实改变几何。

它**不证明**：

- Workbench Parameter Set 已建立；
- CAD feature history 能在 GUI 中编辑；
- 正式 AirJet 产品参数已经锁定；
- 一个保存文件中同时保留了两种状态。

脚本在报告中保存这条路线名，避免以后把等效脚本参数化误写成原生参数表。

## 6. 为什么 Volume Extract 目前写 `NOT_RUN`

当前小模型直接建立 cavity/inlet/outlet 三个负体积，再用 `Combine.Merge` 做 union。它验证的是
`DIRECT_NEGATIVE_VOLUME_BOOLEAN_UNION_EQUIVALENT`。本机 XML 确认 `VolumeExtract.Create` 存在，
但 primary/secondary/cap selection 的无头语义尚未由同版本最小运行确认。

因此报告必须同时写：

```text
volume_extract_api=NOT_RUN
volume_extract_route=DIRECT_NEGATIVE_VOLUME_BOOLEAN_UNION_EQUIVALENT
```

只要 union 后满足 body count、解析体积、`PieceCount=1` 和 closed solid，它可以关闭“得到单一
流体实体”的等效能力字段，却不能宣称实际调用过 Volume Extract。正式 P1 若必须从实体外壳
抽取封闭内腔，仍要另做 Volume Extract 实测。

## 7. Named Selection 为什么不能用 face index

Boolean、保存重开和 STEP 导入都可能改变面编号。脚本按几何谓词找边界：

- `INLET`：bbox center 约 `(10,5,0) mm`，面积约 `π mm²`；
- `OUTLET`：bbox center 约 `(20,5,2) mm`，面积约 `4 mm²`；
- `WALLS`：同一流体 body 中排除上述两面的其余全部面。

容差为位置 `0.05 mm`、面积 `0.05 mm²`。必须得到恰好一个入口、一个出口和至少一个 wall；
随后关闭文档再打开 `.scdocx`，重新按 group 名检查 cardinality。STEP 只检查几何指纹，不预设
它会保留 Named Selections、参数或内部 persistent ID。

## 8. 下游为什么只认 predecessor job ID

Workbench 不能读取“Downloads 里最新的 `.scdocx`”。那种做法存在竞态，也无法证明输入来自
哪次运行。MCP 的下游 profile 只接受一个不含路径的 predecessor job ID，并由服务器检查：

```text
同一 MCP 进程内已知 job
同一 case_id
上游 profile 精确匹配
同一 git_head
同一 output_root_id
终态 PROCESS_EXITED_0 且 exit_code=0
声明报告 status/engineering_capability=PASS_PARTIAL_CAD_CAPABILITY
license_arguments_added=false
```

服务器只复制 policy 明列的三个文件；复制前后分别计算大小和 SHA-256，再生成只读
`predecessor-manifest.json`。Workbench 只收到服务器生成的 `AIRJET_PREDECESSOR_DIR`，调用者
不能传任意路径、环境变量、命令或脚本。

## 9. Workbench/Mechanical 实际要证明什么

下游 journal 执行：

1. 复核 predecessor manifest、上游报告和 `.scdocx` SHA；
2. 建立 Static Structural system；
3. 打开 Named Selection import，`SetFile` 导入上一步原生文件；
4. 对 Model 执行 `UpdateUpstreamComponents()` 和 `Refresh()`；
5. 用 `SendCommand(Language="Python")` 在 Mechanical 数据模型内检查 body 和三个名称；
6. 生成 `1 mm` 粗网格，要求节点数和单元数都大于零；
7. 保存 `.wbpj`，报告项目和 inspection JSON 的大小、SHA。

这不是静力分析：没有材料、载荷、约束或求解。选择 Static Structural 只是为了取得一个可由
Mechanical 数据模型无头检查和网格化的 Model cell。

## 10. 第一次实跑前的预期失败清单（事前记录保留）

下面是首次实跑前写下的风险快照。它保留预测与后来实际问题的差异，不随结果倒改成“早就知道”。
其中“错误圆柱语义下 Boolean Success 不足以证明目标 union”、STEP 根层 query 和 collection
类型已分别在前两次运行中暴露；恰好面接触 tolerance 没有被独立检验，Workbench/Mechanical
项仍因上游阻塞而没有运行：

- `Combine.Merge` 对恰好接触的三个 solid 在 v261 中是否保留单一 closed piece；
- `.scdocx` 由 Workbench `SetFile` 直接消费时是否完整传递 group；
- Mechanical v261 中 collection 的 `Count` 与 body 的 `Nodes/Elements` 暴露形式；
- `Refresh()` 后是否已经完成生成粗网格所需的完整上游 update；
- batch 模式是否产生需外层 Job Object 清理的子进程。

任何一项失败都保留原 job/report/stderr 哈希；修改需新 script SHA、签名 commit、case/job ID。
不能覆盖旧文件，也不能把异常捕获后仍返回能力 PASS。

## 11. 运行完成后怎样用于你自己的论文

若两项都通过，方法部分最多可写：

> 在 ANSYS 2026 R1 Student 的签名固定脚本上，以可解析流道验证了脚本参数重建、单连通流体
> 实体、原生/STEP 回读，以及 Named Selections 向 Workbench Mechanical 粗网格的传递。

这句话还必须带 run ID、commit、script/report/artifact SHA 和限制：小模型仅验证工具链，不是
AirJet 产品几何或性能。若失败，论文方法记录实际限制和替代路线，不能删掉失败只保留最终绿灯。

## 12. 学完这轮你应能回答

1. 为什么解析体积与 bbox 比“软件没有报错”更强？
2. 为什么圆柱 API 的三个点不是凭直觉排列？
3. 为什么等效参数化、Volume Extract 和 Workbench 参数表是三件不同的事？
4. 为什么 STEP 回读不检查 Named Selection 保留？
5. 为什么 Workbench 不能读取“最新文件”？
6. 为什么 Model 网格生成通过仍不是静力求解通过？
7. 为什么一次能力 PASS 不能提升 P1 Gate？

答案不需要背代码；要能沿“来源 → 输入身份 → 几何/数值断言 → 原生产物 → 主张边界”的链条
解释。这也是以后你自己写论文 Methods 和 Limitations 的骨架。

## 13. 实跑记录 1：类型边界比函数名更具体

首次签名运行使用 commit `96f0799e98b264cc4efb8c914b4df734c5814158`。SpaceClaim 实际完成
两次临时几何构建，报告得到：

```text
width 5 mm -> volume 160 mm³, bbox ymax 5 mm
width 6 mm -> volume 192 mm³, bbox ymax 6 mm
```

这关闭了脚本等效参数重建的第一项实测不确定性。随后 group cardinality 复核失败：

```text
TypeError: expected Array[str], got list
```

本机 XML 的函数签名是 `CreateByGroups(System.String[])`。`["INLET"]` 在 Python 语法中虽然
是序列，却不是 script host 要求的 .NET `String[]`。修订版显式构造：

```python
from System import Array, String
Selection.CreateByGroups(Array[String]([name]))
```

这里有三个值得保留的现实点：

1. 同一脚本中的 `FaceSelection.Create(python_list)` 已被 host 接受，不代表所有 API 都做同样
   的隐式集合转换；必须服从每个重载的精确签名。
2. ANSYS wrapper 最终退出码为 0，但脚本已捕获异常并写 `FAIL_DIRECT`；因此工程判定必须读
   declared report，不能只看 process terminal state。
3. Workbench 没有“失败”，而是根本未运行，应记 `BLOCKED_UPSTREAM`，不能用一个虚构的
   Workbench error 填表。

完整外部 suite JSON 的 SHA-256 是
`154b3174653df43f273fc8621d1ea6ed9bdaeaac032c28478c2cafa35bd011c5`；仓库只保存凝练、脱敏的
evidence summary。修复必须用新 commit、script SHA 和 job ID 运行，旧失败不改写。

## 14. 实跑记录 2：Success、闭合、文件存在仍可能全部不够

第二次签名运行使用 commit `aa914a65bf3a8292ae2c6ec9f781fa2fb4381179`。上一轮
`Array[String]` 修复有效，脚本完成 group 查询、三份文件保存和两次重开。结果却是：

```text
Combine.Merge.Success = true
expected volume         = 203.14159265358978 mm³
actual volume           = 200.0 mm³
expected bbox zmin      = 0 mm
actual bbox zmin        = 1 mm
INLET / OUTLET / WALLS  = 0 / 1 / 10
piece_count / closed    = 1 / true
STEP size               = 15137 bytes
STEP root body count    = 0
```

`200 = 192 + 8` 精确表明最终 body 只有 cavity 与 outlet 的体积；bbox 与入口面计数提供了独立
交叉验证。单片且闭合只说明这个错误 body 自己合法，并不说明设计要求的三个分支都存在。原生文件
成功保存并重开，也只是忠实保存了错误的 200 mm³ 几何，所以 aggregate native-reopen 仍 FAIL。

运行后重新对照安装内的官方 table-leg 例子，发现此前仅凭 XML 短描述得到的圆柱三点解释是错的。
这形成一条可用于 Methods/Limitations 的因果链：

```text
Array 类型修复
-> 脚本到达几何断言
-> Boolean 返回 Success
-> 解析体积与 bbox 发现入口缺失
-> INLET cardinality 再次确认
-> 原生文件忠实保存错误几何
-> STEP 非空但根层查询为零 body
-> Workbench 因上游不合格而不运行
```

STEP 的 15137-byte 文件已确认以 `ISO-10303-21` 开头，并含一个
`MANIFOLD_SOLID_BREP('AJM005_T1_FLUID', ...)`，因此它不是零字节或无 B-rep 记录的导出；这不
证明实体图完整或可导入，“root bodies 为零”也不能代表全层 body 为零。本机官方
脚本使用 `GetRootPart().GetAllBodies()` 遍历当前 part 与子组件。第三版保持相同 open 并改用
`GetAllBodies()`；第三次运行进入单候选分支，随后在 `TrimmedSpace.PieceCount` 处失败，详见 §15。

本轮最多可以写：解析几何指纹成功阻止了一个 API 返回成功但缺入口的模型进入 Workbench。不能写
三段 union、完整 Named Selections、STEP 可移植性、CAD transfer 或 P1 readiness 已通过。

## 15. 实跑记录 3：逐项 PASS 不等于 aggregate PASS

第三次签名运行使用 commit `74e855733613baa80d7d821b961c629268f4ba59`。第二轮的圆柱语义
纠正被独立数值证据确认：raw inlet、解析 union、bbox、入口圆面、三组 Named Selections 和
原生重开全部通过。关键值是：

```text
raw inlet     = 3.455751918948766 mm³ ≈ 1.1π
union         = 203.14159265358984 mm³ ≈ 192 + π + 8
bbox          = [2,2,0] -> [20,8,3] mm
piece/closed  = 1 / true
groups        = INLET 1 / OUTLET 1 / WALLS 11
native reopen = same volume, bbox, topology and group counts
```

STEP 路线随后用 `GetAllBodies()` 进入唯一候选分支，证明根层 `Bodies.Count` 不是可靠的跨格式
遍历方式。新的失败是：候选 `Shape` 为 `TrimmedSpace`，而通用 fingerprint 假定所有 shape 都有
native `Modeler.Body.PieceCount`：

```text
AttributeError: 'TrimmedSpace' object has no attribute 'PieceCount'
```

本机 v261 API 把 occurrence `IDesignBody.Shape` 定义成 `ITrimmedSpace`：它提供
Volume/SurfaceArea/bbox，却不把 PieceCount/IsClosed/IsManifold 作为通用成员。同版本反射和 XML
同时确认 `IDesignBody.Master.Shape` 是 `Modeler.Body`，才提供这些拓扑属性。第四版因此把字段
来源拆开：

```text
body.Shape        -> occurrence bbox / volume
body.Master.Shape -> PieceCount / IsClosed / IsManifold
body.Faces        -> face count
```

STEP 仍要求全层唯一 DesignBody、正确 volume/bbox、非零 faces、`PieceCount=1`、
`IsClosed=true` 和 `IsManifold=true`。类型适配只改读取路径，不降低验收条件；报告还会保存
occurrence/master 的 runtime type，防止以后再次把接口层级混为一谈。

这次的因果链是：

```text
正确圆柱 axis/radius 语义
-> Boolean 前 raw inlet 指纹 PASS
-> 三段解析 union PASS
-> INLET/OUTLET/WALLS PASS
-> 原生保存与重开 PASS
-> STEP GetAllBodies 进入单候选分支
-> runtime shape = TrimmedSpace
-> 通用 fingerprint 访问 PieceCount 失败
-> SC aggregate FAIL
-> Workbench BLOCKED_UPSTREAM
```

前面的几何/原生断言是真实逐项 PASS，不因后面的异常而删除；但 profile status 是这些必要条件的
合取，STEP 未完成就不能发出 `PASS_PARTIAL_CAD_CAPABILITY`，Workbench 也不允许消费该 predecessor。
这正是“保存局部证据，同时严格执行总体 Gate”的工程习惯。

## 16. 实跑记录 4：生产者 PASS 不等于消费者兼容

第四次签名运行使用 commit `9652054cf6d84467dce877342eb032df12c375a6`。occurrence/master
分层指纹关闭了上一轮 STEP 类型问题，SpaceClaim 七项断言首次全部通过：

```text
script-equivalent parameter rebuild = PASS
analytic three-segment union        = PASS
INLET / OUTLET / WALLS              = 1 / 1 / 11
native save + reopen                = PASS
STEP all-body reimport              = PASS
STEP occurrence / topology          = TrimmedSpace / Master.Shape Body
STEP volume / faces                 = 203.14159265358984 mm³ / 13
STEP piece / closed / manifold      = 1 / true / true
```

这一次 Workbench 不再是 `BLOCKED_UPSTREAM`，而是实际启动并复核了冻结 predecessor 的 commit、
profile、job、report SHA 和 native SHA。结果矩阵是：

| 层级 | 状态 | 实际证据 |
|---|---|---|
| SpaceClaim 建模 | PASS | 解析体积、bbox、拓扑与命名组全部通过 |
| 原生保存重开 | PASS | `.scdocx` 由 SpaceClaim 重开后指纹相同 |
| STEP 几何回读 | PASS | 全层唯一 body，occurrence/master 分层检查通过 |
| predecessor 身份 | PASS | commit/job/profile/report/native SHA 全匹配 |
| Workbench geometry attach | FAIL_DIRECT | `model_component.Refresh()` 无法附加 `.scdocx` geometry structure |
| Named Selection transfer | NOT_REACHED | 没有进入 Mechanical inspection |
| mesh generation | NOT_REACHED | 没有执行 |
| project save | NOT_REACHED | 没有执行 |
| full CAD transfer set | FAIL | 必要条件的合取没有满足 |

### 16.1 为什么一个 false 不一定是“这个功能失败”

declared report 的五个 assertion 字段是固定 schema。异常发生时，后续字段仍保持默认 false。只有
结合 traceback 与控制流，才能区分：

- `predecessor_identity=true`：已执行并 PASS；
- `geometry_transfer=false`：执行到 attach，直接 FAIL；
- 其余三个 false：控制流没有到达，只能写 `NOT_REACHED`。

如果把后面三个都写成独立失败，会虚构实际没有运行的测试；如果只看 SC 的全绿又把 suite 写 PASS，
则会隐去消费者兼容性失败。工程记录必须同时保存局部 PASS 和总体 FAIL。

### 16.2 四层证据不能互相替换

```text
文件身份正确
  -> 只排除复制错文件或 hash 不一致
生产者能够重开
  -> 只证明 SpaceClaim 原生语义自洽
消费者能够附加
  -> 需要 Workbench 用正确路线真正加载
下游语义和网格通过
  -> 还需 Named Selection、body inspection、mesh 与 project 证据
```

本轮只通过前两层，第三层直接失败，第四层未到达。下一轮必须先用 v261 官方证据确定 attach 路线，
然后每次只改变一个假设。STEP 可以作为“Workbench 是否能消费几何”的诊断支路，但 STEP 本身不
承诺保留 SpaceClaim Named Selections，所以 STEP attach 成功也不能单独关闭最终 transfer Gate。

### 16.3 本轮允许与禁止的论文措辞

允许写：在签名、可解析的可删除流道上，SpaceClaim 已验证脚本参数重建、单片闭合 manifold 流体、
三组命名边界、原生保存重开与 STEP 几何回读；冻结 predecessor 的身份与哈希也已在 Workbench
前置检查中通过。

禁止写：Workbench geometry transfer PASS、Named Selection transfer PASS、Mechanical body
inspection 或粗网格 PASS、Workbench project save PASS、`PASS_CAD_TRANSFER_SET`、Volume Extract
API 已验证、native driving parameter 已验证、005/P1 或整机 CAD 已通过。

## 17. 实跑记录 5：单变量实验要能排除一个窄假设

第五次签名运行只替换 Workbench 的更新语义：

```python
# 第四轮
model_component.UpdateUpstreamComponents()
model_component.Refresh()

# 第五轮，唯一功能变量
model_component.Update(AllDependencies=True)
```

`.scdocx`、Static Structural、Geometry `SetFile`、Named Selection import 属性、冻结 predecessor、
Mechanical 检查和 Gate 全部保持不变。结果是：

```text
geometry_set_file             = RETURNED
model_update_all_dependencies = CALLED, not returned
model_refresh                 = NOT_CALLED_BY_ROUTE
model_container               = NOT_REACHED
mechanical_inspection         = NOT_REACHED
```

错误仍是无法附加 geometry structure。因此这轮真正得到的知识不是“又失败了一次”，而是：旧的
`UpdateUpstreamComponents + Refresh` 顺序不是唯一原因。这个结论很窄，却比同时修改格式、系统模板
和调用顺序更有价值，因为因果归属清楚。

仍然不能写“.scdocx 全局不受支持”。同机 v261 ReaderFilter 明确列出 `*.scdoc;*.scdocx`；本轮只
证明“Static system 内直接 SetFile 后的两种 update 路线都失败”。下一实验改用官方 sample 的
独立 Geometry source→TransferData 架构，同时继续保持 `.scdocx`，把“更新顺序”与“数据流架构”
分开检验。

另一个细节是不同 SpaceClaim run 的原生文件 SHA 可能不同，即使几何断言相同。可复现性不要求
二进制文件跨 run 完全相同；它要求每个消费者精确绑定本轮生产者，并复算体积、bbox、拓扑、组数
和 SHA 身份。不能拿第四轮文件哈希去验证第五轮 predecessor。

## 18. 实跑记录 6：API 存在不等于对象类型组合兼容

第六轮保持文件、更新 API 和所有断言不变，只改变数据流：

```text
.scdocx -> independent Geometry source component
         -> TransferData
         -> Static Structural Geometry component
```

到达矩阵为：

```text
source Geometry system    = RETURNED
source SetFile            = RETURNED
target Static system      = RETURNED
source.TransferData       = CALLED, not returned
Model Update              = NOT_REACHED
Mechanical inspection     = NOT_REACHED
```

v261 原文“几何结构无法使用组件几何结构”说明这个 source/target component 组合被拒绝。这里最容易
犯的推理错误是：看到官方 API 有 `TransferData(TargetComponent=...)`，就认为任何 Component 都
能传给任何 Component。API 签名只定义调用形状，兼容矩阵仍要由模板类型与真实运行决定。

本机 optiSLang sample 的成功 source 是 `PDMReceive/GeoTransfer`，不是普通 Geometry component。
而本机 standard Geometry post-import journal 使用另一条架构：在创建 Static system 时传入
`ComponentsToShare=[source_geometry_component]`，再调用 `GetGeometryFileAndSaveData()`。因此下一轮
测试官方 share 架构，不再猜 `TransferData` 的对象兼容性；`.scdocx` 和下游验收保持不变。

## 19. 实跑记录 7：越过一个边界不代表下一个边界也通过

第七轮的到达矩阵是：

```text
source Geometry / SetFile                 = RETURNED
Static CreateSystem(ComponentsToShare=...) = RETURNED
GetGeometryFileAndSaveData                 = RETURNED
Model.Update(AllDependencies=True)         = CALLED, not returned
Mechanical inspection                      = NOT_REACHED
```

与第六轮相比，失败从 `TransferData` 兼容性检查移动到了 downstream Model update。这是进步，但不能
写成 geometry transfer PASS：source/share 层通过只说明数据流关系建立，真正让 Mechanical Model
消费几何仍失败。

同机官方 journal 在前三步后用的是 Model container `Refresh()`，而当前代码为保持上轮单变量用了
Component `Update(AllDependencies=True)`。下一轮现在只改变这一处，便能检验官方 share topology
是否必须配套 container refresh。若同时加入显式 SpaceClaim Edit，就会把“更新 API”和“CAD editor
启动”混在一起，失去因果可识别性。

## 20. 实跑记录 8：官方调用也必须由真实运行验证

第八轮只把 share route 后的更新从 Component Update 改成官方 journal 录制的 Model container
`Refresh()`。结果仍是在 Refresh 内无法附加 `.scdocx`，且后续未到达。

这说明“代码与官方 sample 一致”是采用一个实验假设的理由，不是它一定成功的证据。sample 的文件
来源、安装组件、许可、会话状态与当前环境都可能不同。当前可以关闭的是“share route 只因选错
Update API 才失败”这一窄假设；不能关闭的是 CAD editor 启动/文件 attach 问题。

下一轮显式调用 Workbench Geometry container 的
`Edit(Interactive=False, IsSpaceClaimGeometry=True)`，让 source `.scdocx` 由 Workbench 管理的
SpaceClaim editor 实际打开，再退出并继续同一 share/refresh 路线。若 Edit 自身失败，根因定位会
从 downstream Model 进一步前移到 CAD editor attach；若 Edit/Exit 返回而 Refresh 仍失败，则说明
“能在 editor 打开”仍不等于“Workbench 下游能附加”。

## 21. 实跑记录 9：能打开文件仍不等于能下传模型

第九轮的显式 `Edit/Exit` 都返回，但 Model Refresh 仍 attach 失败。现在证据链变成：

```text
字节身份正确                         PASS
SpaceClaim 独立脚本原生重开          PASS
Workbench 管理的 SpaceClaim Edit/Exit PASS
ComponentsToShare/save-data          PASS as reached calls
downstream Model attach               FAIL_DIRECT
Mechanical body/name/mesh             NOT_REACHED
```

这正好展示了多软件 CAD 链为什么不能用“文件能打开”作为终点。每个软件的 document model、数据
传递对象和下游 consumer 都可能使用不同内部接口。

下一轮改用 STEP 不是为了绕过并宣布成功，而是诊断：如果 STEP 能让 Mechanical 得到 body 并生成
mesh，就说明 Workbench→Mechanical 求解管线基本可用，问题集中在 native geometry attach/semantic
transfer；如果 STEP 也失败，则问题范围更广。STEP 不保留当前 SpaceClaim groups，所以 Named
Selection transfer 必须继续 FAIL，完整 transfer set 仍不能 PASS。

## 22. 实跑记录 10：诊断 PASS 可以与 suite FAIL 同时成立

第十轮只把冻结 source 从 `.scdocx` 换成同一 producer 已回读并绑定 SHA 的 STEP。它不是替代最终
合同，而是为了回答一个窄问题：Workbench→Mechanical→mesh→project 这段通用管线到底能不能走通。

| 层级 | 真实观察 | 本轮能否关闭 |
|---|---|---|
| frozen STEP identity | predecessor、STEP SHA 与 producer report 全匹配 | PASS |
| source/share/save-data | `SetFile`、`ComponentsToShare`、`GetGeometryFileAndSaveData()` 返回 | PASS as reached |
| Model consumer | Model container `Refresh()` 返回 | PASS as reached |
| Mechanical geometry | 1 body，名称为 `spaceclaim_cad_t1\|AJM005_T1_FLUID` | 诊断 PASS |
| Mechanical mesh | 1063 nodes / 513 elements | 诊断 PASS |
| project persistence | `.wbpj` 50588 bytes，保存返回且有 SHA | 诊断 PASS |
| upstream semantic labels | `INLET/OUTLET/WALLS` 对象与实体全为 0 | FAIL / absent |
| native transfer claim | 脚本固定为 false | 不可关闭 |
| suite | `FAIL_CAD_TRANSFER_SET`，exit 2 | 按设计 FAIL |

exit 2 不是网格器崩溃。脚本故意把 canonical transfer assertions 与 diagnostic observations 分开：

```text
canonical contract:
  geometry_transfer=false
  named_selection_transfer=false
  mesh_generation=false
  project_save=false

diagnostic_result:
  body_geometry_available=true
  mesh_generated=true
  project_saved=true
  native_named_selection_transfer_claim=false
```

这类“双层结果”很重要。canonical contract 回答“原生 CAD 传递合同是否完成”；diagnostic result
回答“为了定位故障，哪些下游能力被真实观察到”。如果为了让 suite 变绿而把 STEP 的 mesh 结果写进
native assertion，就会把交换格式的几何可达性伪装成原生语义传递。

### 22.1 传输链不止是“文件能不能打开”

建议把 CAD→求解器链拆成七层：

```text
bytes identity
  -> topology
  -> geometry body
  -> semantic labels
  -> solver objects
  -> mesh
  -> project persistence
```

本轮关闭了 STEP 路线的 bytes、topology/geometry、mesh 和 persistence 诊断；semantic labels 没有
出现。它由此证明通用 Workbench/Mechanical 管线可用，并把 native 问题定位得更窄，但没有跨过
semantic/native Gate。

### 22.2 下一实验为什么叫 semantic reconstruction

下一步以冻结 STEP 和 hash-bound sidecar 为输入，在 Mechanical 枚举 13 个面，依据 centroid、area、
normal、surface type、adjacency 与容差做唯一匹配，再创建三组 solver Named Selections。小模型的
预期硬检查为：

- `INLET`：唯一圆面，`z=0`，中心约 `[10,5,0] mm`，面积约 `pi mm^2`；
- `OUTLET`：唯一端面，`x=20`，中心约 `[20,5,2] mm`，面积约 `4 mm^2`；
- `WALLS`：剩余 11 面；三组互斥，并集覆盖全部 13 面。

这条路线重建的是求解器侧语义，不是从 `.scdocx` 原生传过来的语义。即使它通过，也只能写
`PASS_STEP_SEMANTIC_RECONSTRUCTION_DIAGNOSTIC`；`named_selection_transfer`、native attach、native
parameterization 和 P1 readiness 仍必须保持 false/BLOCKED，除非未来另立合同并经独立审核。

## 23. 第十一次实验设计：先分离合同，再写重建算法

状态：**SOLVER TOPOLOGY CAPTURED; INLET TOPOLOGY-ANCHOR RETEST PENDING**。

最初可以在现有 native transfer profile 里加一个 `diagnostic_result`，但这仍有命名层面的污染。
最终设计把执行对象拆开：

| 合同 | profile / runner | 唯一允许的成功含义 |
|---|---|---|
| native transfer | `ajm005-workbench-transfer-t1-v1` / `run_t1_cad_suite.py` | 原生 attach、上游 Named Selection 传递、mesh、project 的完整 partial CAD transfer |
| STEP semantic reconstruction | `ajm005-workbench-semantic-reconstruction-t1-v1` / `run_t1_semantic_reconstruction_suite.py` | frozen STEP + sidecar 在求解器侧确定性重建边界，仅诊断 |

semantic runner 的源代码静态禁止出现 `PASS_CAD_TRANSFER_SET`。它即使 exit 0，也同时固定：

```text
p1_cad_toolchain_readiness = BLOCKED
p1_cad_blocker = NATIVE_PARAMETERIZATION_AND_NATIVE_TRANSFER_NOT_PROVEN
p1_p6_gates = NOT_RUN
canonical_native_claims = all false
```

### 23.1 Sidecar 为什么不是“另一个手工参数文件”

producer 先保存 STEP，再形成单向哈希链：

```text
STEP bytes + size + SHA
  -> semantic sidecar 引用 STEP SHA、producer/case、body/face 指纹和 1/1/11 规则
    -> producer report 引用 sidecar size/SHA
      -> MCP predecessor manifest 再冻结 report、STEP、sidecar 三者
        -> Workbench 在 Reset 前重新计算并比较全部身份
```

sidecar 不保存跨导入稳定的 face ID。它保存 producer 已验证的几何语义：坐标/面积单位、13-face
fixture、INLET/OUTLET 的 centroid/area 指纹、WALLS complement 和分区互斥/全覆盖要求。Mechanical
导入后才读取本次 transient face IDs。

### 23.2 Mechanical 算法和单位风险

同机 v261 官方脚本确认的最小路线是：

```text
GeoData.Unit
GeoData.Assemblies -> assembly.AllParts -> part.Bodies -> body.Faces
face.Id / face.Centroid / face.Area
UnitsManager.ConvertUnit(CAD unit -> mm / mm^2)
CreateSelectionInfo(GeometryEntities) -> Ids
Model.AddNamedSelection() -> Name / Location
```

几何值按 CAD unit 报告，不能假定天然是 mm。第十一次实跑若发现 `ConvertUnit`、`AllParts`、
`body.Suppressed` 或 list→`selection.Ids` 在 v261 host 不兼容，应直接 fail closed 并保存完整 face map，
不能用 `×1000` 或 GUI 点选悄悄绕过。

### 23.3 创建树对象前先跑哪些拒绝测试

实际 face 分类和任何 Named Selection 创建之前，脚本先执行四个纯 partition 负向 control：

- `INLET=0` 必须拒绝；
- `INLET>1` 必须拒绝；
- inlet/outlet ID 重叠必须拒绝；
- 三组覆盖不全必须拒绝。

真实输入还要检查 sidecar/STEP/report/manifest SHA 链、13 个唯一 face IDs、实际 1/1/11、同名对象
不存在、创建后 entity counts 精确等于 1/1/11。任何一项失败都保留 report/inspection，不生成
diagnostic PASS。

### 23.4 第一次运行为什么还不能评价重建算法

签名 commit `4f80fc6...` 的第十一次运行中，producer 与输入身份链都通过：STEP、sidecar、report、
MCP manifest 一致，Workbench 的 `SetFile`、share 和 save-data 也返回。真正失败发生在
`Model.Refresh()` 保存/附加临时 `SYS.mechdb` 时，执行顺序如下：

```text
producer 1/1/11 + STEP/sidecar SHA          PASS
predecessor + semantic sidecar identity     PASS
Workbench source/share/save-data            PASS
Model.Refresh                               CALLED -> host attach exception
Mechanical body/face traversal              NOT_REACHED
partition negative controls                 NOT_REACHED
Named Selection reconstruction              NOT_REACHED
mesh/project                                NOT_REACHED
```

这说明报告中的 `semantic_reconstruction=false` 是“未到达导致的 false”，不是“13 个面被错误分类”。
写实验记录时必须同时看 assertion 和 `execution_reach`；只看布尔值会把基础设施故障误判成算法故障。

失败 `SYS.mechdb` 路径长 237，job root 比第十次成功 STEP 诊断长 12 个字符。系统已启用 long paths，
且第十次 job 中存在 253-character 路径，因此不能简单宣布 `MAX_PATH=260` 根因。仍值得做短 case ID
复测，因为 legacy 子组件可能不采用系统长路径能力，而 case ID 在 root 中重复两次。这个实验只改
一个变量；无论通过或失败，都能关闭一个窄假设。

### 23.5 短路径复测怎样把基础设施问题变成算法问题

只缩短 case prefix 后，job root 从 176 变为 154 字符。`Model.Refresh()`、Mechanical command 和
project save 全部返回，说明短路径确实恢复了算法可达性。这个结果对 path-budget sensitivity 是强
支持，但不是对 Windows 260 字符规则的普遍证明：具体 ANSYS 子组件是否 long-path-aware 仍未知。

算法第一次给出真实分区：

```text
expected: INLET=1, OUTLET=1, WALLS=11
actual:   INLET=0, OUTLET=1, WALLS=12
action:   reject before Named Selection creation and mesh
```

OUTLET 唯一匹配说明 CAD 单位转换和整个坐标框架不太可能完全错误；INLET 单独未命中更可能是入口
面 centroid/area 在 STEP→Mechanical 中与 producer 指纹存在局部差异。但现在还不能放宽容差，因为
旧失败 inspection 没保留 13 个实际面的数值。

这里又出现一个工程记录问题：计算出了 `face_details` 和 negative controls，不等于证据文件保存了
它们。旧脚本只在最后成功路径执行 `inspection.update(...)`；真实 partition 抛错后，except 写出的
inspection 只剩 error/traceback。下一次先把观测更新移到 validation 前，同时保持分类规则不变。
这叫 observability 修复，不叫算法修复。

### 23.6 13 面数值说明了什么

第十三次只前移失败观测，因而可以把“不匹配”分解为两个数：

| quantity | producer sidecar | Mechanical face 44 | absolute delta | tolerance |
|---|---:|---:|---:|---:|
| center x/y/z (mm) | `[10,5,0]` | `[10,5,0]` | `0` | `0.02` |
| area (mm²) | `3.1415926536` | `2.0` | `1.1415926536` | `0.02` |

所以不是“入口位置漂了”，而是面积条件单独拒绝了位于正确位置的面。圆柱侧壁面积和 centroid 也有
变化，而矩形 outlet 完全一致。这种不对称非常像 kernel/trimmed-surface 表示差异；它不支持把所有
跨格式 face area 都当作绝对稳定 ID。

下一步仍不直接改 predicate。先记录 `SurfaceType`、边数和 centroid normal，因为一个入口 cap 更
合理的 solver-side 硬合同可能是：唯一 centroid anchor + planar + 单边界环 + z-normal，再由 13-face
互斥/全覆盖和负向 controls 保护。这个策略只针对 disposable fixture；整机边界需要按其几何和局部
拓扑重新定义，不能复制 `[10,5,0]`。

### 23.7 topology 观测怎样约束下一条 predicate

第十四次结果没有 topology API error。入口候选与两个对照面为：

| role | id | center | surface | edges | normal | area |
|---|---:|---|---|---:|---|---:|
| inlet candidate | 44 | `[10,5,0]` | plane | 2 | `[0,0,-1]` | 2 |
| curved inlet wall | 45 | `[10.0506,5,0.5016]` | cylinder | 4 | `[1,0,0]` | 5.8328 |
| outlet | 54 | `[20,5,2]` | plane | 4 | `[1,0,0]` | 4 |

下一条入口 predicate 可以安全地做一次单变量替换：中心仍来自 hash-bound sidecar；面积只保留为
diagnostic；solver calibration 追加 plane、2 edges 和 `abs(normal)=[0,0,1]`。使用绝对 normal 是因为
STEP 面方向符号可能翻转，而轴向仍稳定。任何一项 API 为 null/error 都不命中，最终仍要求唯一 1 面。

这并不是“从产品图推断入口结构”，而是对 005 fixture 的跨 kernel 语义桥校准。整机 CAD 到来后，
每个产品边界必须有自己的证据来源、局部拓扑合同和负向测试。

### 23.8 第十五次实跑：怎样把一个诊断 PASS 限定在它真正证明的范围

第十四到第十五次只有一个算法变量：入口从 `centroid+area` 改为
`centroid+plane+2 edges+abs(z-normal)`。中心容差仍为 0.02 mm；OUTLET 仍用 centroid+area；WALLS
仍是 complement；1/1/11、互斥、全覆盖和四项拒绝测试没有放宽。

| checkpoint | 第十四次 | 第十五次 |
|---|---|---|
| INLET candidates | 0 | 1，face 44 |
| OUTLET candidates | 1 | 1，face 54 |
| WALLS candidates | 12 | 11 |
| preexisting name objects | 0/0/0 | 0/0/0 |
| created name objects | 未到达 | 1/1/1 |
| created entity counts | 未到达 | 1/1/11 |
| negative controls | 4/4 PASS | 4/4 PASS |
| mesh | 未到达 | 1063 nodes / 513 elements |
| project | 50593-byte 诊断文件 | 50593-byte 完成文件 |

面积降为诊断量不是因为“面积不重要”，而是 REAL-034 已实测同一个入口在 producer 与 Mechanical
分别为 π 和 2 mm²；继续把它用作硬 ID 会稳定地产生假阴性。替代它的 topology anchor 由 REAL-035
在同一个 13-face fixture 上实测，并由唯一性、互斥/全覆盖和 negative controls 共同保护。

因此允许的知识主张是：hash-bound STEP 与 sidecar 可以在 solver 侧对这个可删除小模型确定性重建
边界语义，并继续生成粗网格和保存工程。不能写成 STEP 原生保留 Named Selections、`.scdocx` attach
成功、原生参数对象可更新、AirJet 产品入口具有 2-edge 拓扑，或 P1 CAD 通过。face ID 44/54 也只是
本次 import 实例的瞬时编号，不能进入整机几何合同。

## 24. 第十六次实跑：同一个基础设施变量不能跨格式直接外推

semantic route 从长 job root 缩短后越过了临时 `SYS.mechdb` attach，所以我们把同一变量用于 native
route。native case ID 缩为 16 characters 后，job directory 只有 102 characters，输入 `.scdocx` 的
完整路径为 145 characters；但失败点仍是 `Model.Refresh()` 无法附加 geometry structure，耗时也与
旧 native 失败几乎相同：280.347 秒。

| route | format | short-path outcome | interpretation |
|---|---|---|---|
| semantic reconstruction | STEP + sidecar | 越过 attach 并最终 diagnostic PASS | 某个 legacy 子组件有路径敏感性 |
| native transfer | `.scdocx` | 同一 attach 错误 | 路径缩短不足以解决 native translator/materialization |

这不是矛盾。STEP 是交换格式，Workbench 可重新导入几何；`.scdocx` 是原生文档，可能需要不同的
translator、文档结构或写回行为。MCP 为防止证据被下游改写，会把 predecessor 副本设为只读。若
SpaceClaim Edit/Exit 或 Workbench materialization 需要修改 working document，直接使用 frozen file
可能失败。

下一实验不能解除 frozen evidence 的只读保护。正确做法是在 job root 复制一个 hash-equal working
copy，显式使它可写，记录复制前后 SHA，再只让 Workbench 使用 staging copy。这样既保留输入证据，
又单独测试“工作文档必须可写”这一假设。

## 25. 第十七次实跑：怎样证明一个 workaround 真的生效但仍然无效

第十七次没有直接把 frozen predecessor 改为可写，因为那会破坏输入证据。journal 在 WB job 的
`input/stagingcopy` 下复制 native 文件；`stagingcopy` 与 `predecessor` 都是 11 个字符，因此 source
与 working path 都是 145 characters。复制后先验证不同绝对路径、相同 size/SHA、source read-only、
working writable，任何一项不满足都在启动 Workbench 几何路线前 fail closed。

| observable | frozen source | working copy |
|---|---|---|
| before role | immutable evidence | job-local derivative |
| before attributes | `ReadOnly, Archive` | `Archive` |
| before size/SHA | 32143 / `7e1d3729...` | 32143 / `7e1d3729...` |
| after size/SHA | 不变 | 不变 |
| after read-only | true | false（事后 PowerShell） |

这组观测证明 workaround 确实生效：`SetFile` 消费的是可写副本，不是只读源。它也证明 frozen source
没有被下游偷偷改写。结果仍然失败，所以可以关闭“本轮 writable staging 足以修复”和“read-only 是
唯一充分解释”这两个窄假设。

但这不是严格的 permission-only paired trial。SpaceClaim producer 每轮重新生成 native：前轮为
32148 bytes，本轮为 32143 bytes；journal 也增加了观测代码，目录 token 从 `predecessor` 变为
`stagingcopy`。因此严谨说法是“唯一有意的 route intervention”，不是“两份完全相同字节只翻转一个
权限位”。负结果足以否定整个 writable-staging package 的充分性，却不能全局排除权限可能与其他
因素联合作用。

Workbench job 总时长为 282.115 秒，traceback 的异常点是 `Model.Refresh()`；journal 没有给 Refresh
单独计时，所以不能写“Refresh 本身耗时 282.115 秒”。`working_copy_mutated_by_editor=false` 也只
代表前后 size/SHA 没变，不能写成 editor 没有尝试写入或没有内部活动。

下一实验不再继续 chmod、换复制目录或缩路径，而是改变 materialization route：创建空 Geometry
system，进入与该 cell 连接的 SpaceClaim editor，在 connected document 内构造同一个 disposable
fixture，退出 editor 后再 share 到 Static Structural。它若通过，只证明 Workbench-managed connected
document 可用；仍不证明 external `.scdocx` attach 已修复，也不证明 native parameterization 或 P1。

## 26. 第十八次实跑：API 返回不等于内层脚本证据已经产生

connected-document diagnostic 被拆成独立 profile，是为了不改写前十七次 external `.scdocx` attach
历史。它从空 Geometry cell 开始，先硬检查 `GeometryFilePath=""`，再执行非交互 SpaceClaim Edit、
`RunScript` 和 Exit；前驱只给 producer report 作 control，刻意不给 `.scdocx`、STEP 或 sidecar。

首轮 reach 如下：

| checkpoint | observation | what it proves | what it does not prove |
|---|---|---|---|
| predecessor | identity PASS，前后 size/SHA 不变 | control 没被下游改写 | connected 几何已建立 |
| empty Geometry | RETURNED，path 为空 | 没有偷偷 attach external file | editor document 一定可写 |
| Edit | RETURNED | Workbench API 调用没有向外抛错 | SpaceClaim 内层初始化完全成功 |
| RunScript | RETURNED | 外层调用返回 | script 已执行到几何构造或写报告 |
| Exit | RETURNED | 外层退出调用返回 | embedded script 没有早期异常 |
| build report | missing | 预期证据未产生 | 几何算法本身失败 |
| share / Mechanical | NOT_REACHED | 没有后续观测 | transfer 或 mesh 分别失败 |

这里最重要的学习点是“控制 API 的返回值”和“被控制进程产生的工程证据”是两个层次。runner 不能
只因为 `RunScript` 返回就把 `connected_editor_build=true`；它必须要求 build JSON、几何指纹和
Named Groups 精确合同。正因为 fail closed，本轮没有制造一个假 PASS。

当前嵌入脚本的可观测性顺序有缺陷：先 imports，再读取
`os.environ["AIRJET_JOB_DIR"]`，之后才建立 report path、result 和 try/finally。若 connected host 中
变量缺失、陈旧或指向另一个 job，它会在能够自报错之前退出或把报告写到别处。RSM 日志也显示该批
Workbench 环境没有 `PROGRAMDATA`，说明特殊目录环境确实可能与普通进程不同；但 RSM 与 fixture
没有直接因果关系，所以这只能提升环境假设优先级，不能确认根因。

下一轮只修可观测性，不改 fixture 几何和 transfer route：

1. 外层 journal 把绝对 sentinel/report/job path 写入嵌入脚本；
2. sentinel 在任何 import 前用 builtin `open` 落盘；
3. imports 后记录 `os.environ.get("AIRJET_JOB_DIR")` 的真实值；
4. 顶层捕获当前 stage、exception type 和 traceback；
5. build contract 继续要求 1 body、13 faces、闭合/manifold、1/1/11 groups；
6. 只有 build report PASS 才允许 share 和 Mechanical。

判读矩阵：

| sentinel | recorded env | build report | inference |
|---|---|---|---|
| missing | unknown | missing | 优先查 RunScript 未执行、错误会话、脚本读取或目标写权限 |
| present | missing/wrong | present | 环境传播假设得到直接支持 |
| present | correct | missing | 环境假设被削弱，转查 imports/host/final write |
| present | any | FAIL JSON | 按精确 stage/traceback 做下一次单变量修复 |
| present | any | PASS JSON | 才能继续检验 share、Refresh、Named Selection、mesh 和 project |

Workbench job 总时长 136.802 秒，日志中第二次 project-created 到最终外层异常约 120 秒；但没有
分段计时，不能把这 120 秒分配给 Edit、RunScript 或 Exit 的任一个。论文方法记录必须保留这种
时间归因边界。

## 27. 第十九次实跑：一个“缺报告”假设怎样被 early sentinel 否定

第二轮把 child 路径改成 outer journal 注入的绝对路径，并把 sentinel 写入放在 imports 之前。这样
即使 `AIRJET_JOB_DIR` 不存在、Python/.NET import 失败或第一条 SpaceClaim API 失败，也应该至少留下
sentinel；只有 child 没进入、最基本写入不可达或 file dispatch 没发生时，sentinel 才会缺失。

三个检查点都是同一个 Workbench job 的时序快照：

| checkpoint | epoch seconds | sentinel | build report | probe error |
|---|---:|---|---|---|
| immediately after RunScript returned | 1784072246.0402832 | absent | absent | none |
| immediately after Exit returned | 1784072246.042282 | absent | absent | none |
| outer failure catch | 1784072246.042282 | absent | absent | none |

Exit 前后约 2 ms，说明本轮没有观测到“RunScript 返回后，Exit 才触发 child 写入”。这不是三次重复
实验，所以不能写“三次都失败”；严谨说法是“一次运行的三个时点均未观测到 entry”。

这组结果关闭的是窄假设：child `AIRJET_JOB_DIR` 缺失/错误导致 sentinel/report 被写到错误 job。
因为 sentinel 已不读取该变量，这个解释不再充分。它没有关闭更宽泛的 broker 环境、错误 editor
session、child 文件读取或 job path 写权限问题，也没有触及几何构造——第一条 builtin `open` 都没被
观测，几何代码更不可能被单独判定成功或失败。

官方 v261 文档同时支持 `.py` 与 `.scscript`，但没有证明两种合法文件的序列化可以逐字节等价。
把同一 Python 文本只改 suffix 是 loader probe，不是可直接解释的严格 A/B；它若失败，可能是 wrapper
dispatch，也可能是该字节序列并非合法 `.scscript`。因此下一次先加入
`SendCommand(Language="Python")` 的独立 inline sentinel，并保留现有 `.py` RunScript：inline 有而
RunScript 无，才把问题收窄到 file-based loader；两者都无则转查 editor scripting channel/session。
`.scscript` 只有在先得到合法格式/等价性证据后再做。

## 28. 第二十次实跑：`CHECKPOINT_NOT_REACHED` 不是两通道都失败

本轮原计划在同一 editor 内比较 inline `SendCommand` 与 file `RunScript`。为了让这个比较可解释，
两个 marker 都不是简单 `exists`：固定 ASCII bytes 由 binary mode 写入，外层锁定 exact size/SHA；
inline 必须在紧接调用的 checkpoint 精确出现，后来才出现只允许标为 delayed/uncertain。runner 还
要求 suite 显式携带四态：

```text
INLINE_PASS_FILE_PASS
INLINE_PASS_FILE_FAIL
INLINE_FAIL_FILE_PASS
INLINE_FAIL_FILE_FAIL
```

真实 reach 却停在四态之前：

| checkpoint | observation | interpretation |
|---|---|---|
| empty Geometry | RETURNED | 没有 external file attach |
| Edit(Interactive=False) | RETURNED | Workbench 外层调用返回 |
| SendCommand | CALLED, then NullReference | post-call checkpoint 未到达 |
| inline marker | absent at failure freeze | 没有证明 inline payload 执行 |
| RunScript | NOT_REACHED | 本轮不能评价 file loader |
| cleanup Exit | RETURNED | 失败清理成功 |
| transfer/Mechanical | NOT_REACHED | 没有 transfer/mesh 结果 |

因此 suite 的 `CHECKPOINT_NOT_REACHED` 是一种比四态更早的状态。把它强行压成
`INLINE_FAIL_FILE_FAIL` 会把“未执行”伪装成“执行后失败”，论文中的因果顺序也会错。

Workbench replay journal 的相关 editor scripting 序列记录了 Edit、SendCommand 和 cleanup Exit，
没有记录 RunScript；这与 outer reach 一致。GetMessages、stdout、stderr 都为空。consumer 总时长
约 256 秒，但没有调用级 timer，所以可写“job
在 SendCommand 调用未返回的路径上结束”，不可写“SendCommand 精确耗时 256 秒”。

下一轮采用受审 outer journal 单变量：只将 `Interactive=False` 改为 `Interactive=True`。官方 API 把它定义为
batch/interactive，且默认是 true；这正好检验 run #19 与 #20 的共同未决因素——`Interactive`
模式变化是否与 connected scripting path 的结果变化相伴。不能同时删除 SendCommand、换
`.scscript`、改 payload、
动几何或修许可，否则即使结果改变也无法归因。case-specific absolute path 和注入后的 child/command
bytes 会按同一 generation/binding 合同重建，因此“单变量”不表示整组输入 byte-identical。

## 29. 第二十一次实跑：单参数未修复只关闭一个窄命题

run #20 与 #21 的受审 outer journal 只把 `Interactive=False` 改为 `True`。静态策略不是靠字符串
搜索，而是用 AST 要求唯一 `source_geometry.Edit`、无 positional/`**kwargs`、两个 keyword 都是
literal True，且 Edit、SendCommand、RunScript 是同一 `Try.body` 的 direct expression 并按顺序执行。

两轮结果：

| item | run #20 False | run #21 True |
|---|---|---|
| empty / Edit | RETURNED / RETURNED | RETURNED / RETURNED |
| SendCommand | CALLED then NullReference | CALLED then same external text |
| post-Send / RunScript | NOT_REACHED / NOT_REACHED | NOT_REACHED / NOT_REACHED |
| artifacts at failure | all absent | all absent |
| cleanup | RETURNED | RETURNED |
| classification | CHECKPOINT_NOT_REACHED | CHECKPOINT_NOT_REACHED |
| consumer duration | 256.035317 s | 255.783635 s |

这足以否定“仅改 Interactive=True 就能修复当前 checkpoint”的命题；不足以证明 interactive 与 batch
内部等价。recorded journal 的默认写法说明参数被 Workbench 接受，却不能证明 SSH/MCP 下真的建立
用户可见 desktop。两次外部错误签名相同，也不等于内部根因已被证明相同。

下一轮不再让已知会抛错的 SendCommand 挡在目标前面：保留 True，让 `.py` RunScript 成为第一个且
唯一 scripting action。分类要改成 file-only，至少区分 call exception、immediate entry exact、
returned entry absent、delayed/exit-triggered、entry exact但build missing、build contract pass/fail。
历史 run #19 可说明 batch RunScript 曾返回但 marker absent，但它的 instrumentation 版本不同，不能
与新轮写成 byte-identical Interactive 因果 A/B。

## 30. 第二十二次实验设计：file-only reachability（实现完成，尚未实跑）

### 30.1 本轮问题和唯一目标 action

本轮不再让已知会在 checkpoint 前空引用的 source-editor `SendCommand` 挡住目标。它保持
`Interactive=True`，把 inline control 明确标为 `SKIPPED_BY_EXPERIMENT`，只问三个可观测问题：

1. direct `.py RunScript` 是未到达、call 内抛异常，还是返回？
2. 固定 entry sentinel 第一次在哪个 checkpoint exact；是否延迟出现或后来丢失？
3. build report 在 freeze 时和稍后 capture 时分别是什么状态？

这不是与历史 run 的整组 byte-identical 单变量实验。case-specific absolute paths、注入路径后的 child
bytes、schema 和 instrumentation 都会变化；可比较的是受审 action/reach 合同，不是全部输入 SHA。

### 30.2 实际控制流

```text
empty Geometry + Edit(Interactive=True)
-> source_geometry.RunScript(ScriptFile=build_script_path)
-> immediate exact entry/build probe
-> source_geometry.Exit()
-> POST_EXIT freeze

或 direct call/后续步骤异常，且仍需 connected-build 失败诊断、build contract 尚未返回
-> FAILURE_PRE_CLEANUP probe
-> guarded cleanup Exit()
-> FAILURE_POST_CLEANUP freeze
-> best-effort build-report capture/parse
```

normal 和 failure freeze 是分类时点；capture 是稍后的诊断证据。若文件在两者之间出现或消失，两个
字段应同时保留，而不是让后者重写前者。它们不是原子 snapshot。若 build state 已 terminal 或 build
contract 已返回，异常处理不会重复执行这组 failure probe/freeze/capture。

### 30.3 判读层级

```text
entry exact
!= build JSON valid
!= build contract PASS
!= geometry share / Refresh PASS
!= Named Selection / mesh / project PASS
!= external native attach / native parameterization PASS
!= P1 PASS
```

即使 classification 最终是 `BUILD_CONTRACT_PASS`，suite 仍要验证所有工程 assertions、声明 artifacts、
predecessor identity 和 manifest；connected fixture 也不能替代 external `.scdocx` route。

### 30.4 为什么需要可达状态和 AST mutation

只检查字段取值会接受不可能组合，例如 `RunScript=EXCEPTION` 却写 build contract RETURNED、failure
capture 已执行却 freeze 仍是 normal checkpoint，或当前 probe 自报错误又确定文件 absent。pure validator
用 writer 的控制流限制这些组合，并以 late arrival、disappearance、历史错误恢复等正向样本防止过严。

只搜索 `SendCommand` 字符串也不够：对象 alias、method rebinding、computed `getattr`、字典下标和 .NET
reflection 都可能绕开 direct-call 数量。AST policy 同时限制 owner、cardinality、argument、order、alias、
refetch 与 reflection；但它仍只是静态审查，不是 runtime sandbox。

### 30.5 待实跑结果表

| field | pre-run value |
|---|---|
| signed commit | `PENDING` |
| Windows exact HEAD | `NOT_SYNCED` |
| case / suite / job IDs | `NONE` |
| RunScript outcome | `NOT_RUN` |
| entry first observed | `NOT_RUN` |
| freeze / capture build state | `NOT_RUN` |
| engineering assertions/artifacts | `NOT_RUN` |
| visibility | `NOT_USER_OBSERVED` |
| P1 Gate | `NOT_RUN` |

实跑前不得把任何一格改为 RETURNED、EXCEPTION、present、absent、PASS 或 FAIL。签名 commit、Windows
clean fast-forward、skill 安装 hash、static policy 和 preflight 都通过后，才创建新的 case/job，并用
真实 report、manifest、raw evidence 和解释文件填写。

### 30.6 自检题

1. 为什么 `SKIPPED_BY_EXPERIMENT` 与 `NOT_REACHED` 是两个不同事实？
2. 为什么 capture 到 late FAIL JSON 不能倒写成“post-RunScript 已有 build report”？
3. 为什么历史 `POST_EXIT` probe error 不等于最终 `FAILURE_POST_CLEANUP` 也出错？
4. 为什么本轮仍保留一个 Mechanical `model_container.SendCommand`？
5. 为什么即使 connected route 全通过，也不能把 external native attach 或 P1 写成 PASS？
