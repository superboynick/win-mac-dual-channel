# 005 T1 CAD→Workbench 学习工作簿

更新时间：2026-07-14  
当前状态：**脚本与证据协议在发布审查中；尚未运行，任何能力字段都不能写 PASS。**

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
| inlet | cylinder | 直径 2 mm，`z=0→1 mm` | `π×1²×1 = π mm³` |
| outlet | block | `x=18→20, y=3→7, z=1.5→2.5 mm` | `2×4×1 = 8 mm³` |

三体只在完整公共面相接，Boolean union 后理论总体积为：

```text
V = 192 + π + 8 = 203.1415926535898 mm³
bbox min = (2, 2, 0) mm
bbox max = (20, 8, 3) mm
```

外部另建 `20×10×4 mm` block，只用于证明完整文档能同时保存外体和内部流体。传给 Workbench
的是删除外体后的单流体原生文件，避免下游把第二个实体误当流体域。

## 3. API 不是看名字猜：圆柱三点的实例

本机 v261 XML 对 `CylinderBody.Create` 的三个点定义为：

```text
centerPoint = 定义圆的圆心
startPoint  = 圆周上的起点
endPoint    = 对应圆周点沿挤出方向移动后的终点
```

所以半径 1 mm、沿 `+z` 从 0 到 1 mm 的入口必须写成：

```python
CylinderBody.Create(
    Point.Create(MM(10), MM(5), MM(0)),
    Point.Create(MM(11), MM(5), MM(0)),
    Point.Create(MM(11), MM(5), MM(1)),
    ExtrudeType.ForceIndependent,
)
```

初稿把三个点理解成了“轴起点、轴终点、半径点”。静态审查通过 XML 参数名发现错误，并在
任何签名提交和运行前修正。这个例子说明：函数存在只证明 API 可见；参数语义必须由同版本
文档、官方样例和运行后的几何指纹共同确认。

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

## 10. 第一次实跑前的预期失败清单

这些是待实验消除的不确定性，不是已发生的结果：

- `Combine.Merge` 对恰好接触的三个 solid 在 v261 中是否保留单一 closed piece；
- `.scdocx` 由 Workbench `SetFile` 直接消费时是否完整传递 group；
- Mechanical v261 中 collection 的 `Count` 与 body 的 `Nodes/Elements` 暴露形式；
- `Refresh()` 后是否已经完成生成粗网格所需的完整上游 update；
- batch 模式是否产生需外层 Job Object 清理的子进程。

任何一项失败都保留原 job/report/stderr 哈希；修改需新 script SHA、签名 commit、case/job ID。
不能覆盖旧文件，也不能把异常捕获后仍返回能力 PASS。

## 11. 运行完成后怎样用于你自己的论文

若两项都通过，方法部分最多可写：

> 在 ANSYS 2026 R1 Student 的签名固定脚本上，以可解析流道验证了参数驱动几何、单连通流体
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
