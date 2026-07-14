# 005 T1 CAD→Workbench 学习工作簿

更新时间：2026-07-14  
当前状态：**三次签名运行均已保留；第三次解析 union、Named Selections 和原生重开已逐项
通过，但 STEP shape type adapter 失败，第四版待签名运行，aggregate partial CAD/transfer 仍不能
写 PASS。**

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
