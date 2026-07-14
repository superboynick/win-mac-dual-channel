# P1 整机 CAD 输入合同：生成方法与证据边界

状态：可执行输入已生成，CAD 尚未运行，`P1_STAGE_GATE=NOT_RUN`。

这组文件把 P0 冻结的公开证据转换成 Windows 可以直接读取的整机 CAD 输入。它的作用是消除“建模时临场猜尺寸”，不是证明 AirJet Mini 的量产内部结构已经被识别。

## 1. 唯一生成入口

在仓库根目录运行：

```powershell
python .\airjet-simulation\parameters\build_p1_cad_inputs.py --check
python .\airjet-simulation\parameters\build_p1_cad_contracts.py --check
```

若需要根据已审核的上游注册表重新生成，去掉 `--check`。所有由这两个脚本生成的 CSV 均禁止手工修改；应修改有证据来源的上游表或生成脚本，再重新生成并审计。

第二个生成器输出：

- `p1_model_form_variants.csv`：6 个交付/残差变体，加上 vent、孔距解释和排气平面的 3 个单因素派生变体，共 9 个可审计运行 ID；
- `p1_cad_parameter_map.csv`：每个变体的 CAD 变量、值、单位、来源、证据类和用途限制；
- `p1_orifice_pattern_candidates.csv`：喷孔节距定义的三种解释及其数学冲突；
- `p1_vent_geometry_candidates.csv`：两套、每套 4 个顶盖开口的可重建坐标；
- `p1_planform_exhaust_candidates.csv`：每个整机配置两套单侧排气平面分支；
- `p1_internal_geometry_rules.csv`：cell 中心/膜片、每 cell 底腔、中央锚 datum、分区 datum、共享顶腔、外围转移间隙、侧壁、残差数值封闭和喷孔落点的 9 条无隐藏常量 R0 构造规则；
- `geometry/contracts/*.csv`：部件、参数绑定、接口、Named Selections 和开放问题合同；
- `checklists/p1_cad_gate_matrix.csv`：每个变体的验收行，初始全部为 `NOT_RUN`。

## 2. 坐标系

整机 CAD 使用中心坐标：`X` 为 27.5 mm 宽度方向，`Y` 为 41.5 mm 长度和主排气方向，`Z=0` 为底部热扩散参考面，`+Y` 是当前候选产品出口。

图像测量表使用 `x=[0,27.5]`、`y=[0,41.5]` 的矫正平面坐标。转换为 CAD 中心坐标时：

```text
x_cad = x_rectified - 27.5/2
y_cad = y_rectified - 41.5/2
```

这个变换只改变坐标原点，不提高图像证据精度。

## 3. 顶盖开口的两套候选

`VENT_FLOW_BBOX_R0` 使用 `official_image_measurements.csv` 已存的矫正包围框：长轴取包围框中心线，宽度取包围框宽度，证据类为 `I`。

`VENT_UPPER_CENTERLINE_P013_R0` 使用第二张官方渲染的 homography 中心线，并以专利候选 `P013=0.75 mm` 作为槽宽。因为它混合了图像和专利输入，只能作为 `C` 类工程分支。

两套各有 `V01..V04`。四个对象只是“图上画出的四个开口对象”，不等于四个真实进气组、四个 cell 或制造公差。一次 CAD 重建必须完整选择同一 `candidate_set_id` 的四行，不能混拼最顺眼的坐标。

## 4. 喷孔节距为什么保留三种解释

对圆孔直径 `d=0.25 mm`、目标无限方阵开孔率 `phi=10%`，由面积闭合得到：

```text
p_phi = d * sqrt(pi/(4*phi)) = 0.700624 mm
```

因此 `PHI_DERIVED_SQUARE` 是第一版可建 CAD 候选，但实际孔板裁切后仍必须重新统计孔数和开孔率。

若把 `P008=0.5 mm` 解释为中心节距，R0 无限方阵开孔率约为 `19.635%`，超过当前 8--12% 优选范围和 15% 广义上界。它被保留为冲突哨兵，不能静默删除；这只说明“该 R0 方阵解释不自洽”，不能否定专利中的其他孔形、区域或 `s` 定义。

若把 `P008` 解释为边缘间距，则中心节距为 `d+s=0.75 mm`，无限方阵开孔率约为 `8.727%`，可作为第二 CAD 分支。任何分支都不是量产孔距事实。

## 5. 单侧排气候选

公开剖面只直接支持单侧集成出口的定性拓扑，`C005` 的精确三维尺寸仍未知。为使 CAD 可执行，`p1_planform_exhaust_candidates.csv` 对每个配置给出两个 `C` 类闭合分支：

- `EXH_FULL_WIDTH_RECT_R0`：从阵列 `+Y` 边缘到产品 `+Y` 外包络面保持阵列全宽；
- `EXH_CENTER_HALF_TAPER_R0`：从阵列全宽线性收敛到居中的半宽出口。

歧管长度严格由 `41.5/2-array_span_y/2` 计算，出口高度暂取 `P010` 冲击通道高度。它们用于连通性和模型形式敏感性，不用于声称量产歧管/喷口尺寸，也不能在未校准前作气动结论。

实际 R0 在膜片阵列外缘再保留 `P014/2` 的 cell tile 余量，因此歧管起点和长度按 `41.5/2-(array_span_y/2+P014/2)` 生成；这是一条显式 C 类 cell-tile 解释。

## 6. 未识别流路细节如何变成可重复候选

`p1_internal_geometry_rules.csv` 解决九个会迫使 CAD 操作者临场猜测的问题：

- cell 中心节距为 `P001+P014`，每个膜片位于同尺寸 Voronoi tile 中心；
- 每 cell 底腔是与膜片同中心、边长 `P001` 的方形流体体，从膜片底面向下延伸 `C018`；
- 中央锚只建立边长 `P012`、位于膜片 Z 区间的 C 类方形 construction datum，不做 Boolean、不赋材料/质量、不进入求解器；
- cell partition 只建立阵列内部 tile 中面上的零厚度 ownership/naming datum，不占用外围间隙流体，也不声称真实隔墙；
- R0 顶腔为四个选定 vent polygon 与完整 cell tile footprint 的包络裁剪凸包，Z 范围来自所选厚度变体；
- 外围转移间隙是 `tile square - membrane square`，每侧 R0 间隙为 `P014/2`，从底腔贯通至顶腔；
- 侧壁只是所有声明流体体在外包络上的 wall face 集合，不建立虚假的已识别 side-frame 固体；
- `C017/C019` 区间既不当空气也不当真实固体。只直接构造合同声明的流体体并求 union，严禁采用“外包络减所有候选固体”得到流体域；厚度边界 datum 只用于数值封闭，不进入材料、质量或求解器；
- 每个 cell 的喷孔网格在膜片中心重新起算，只保留完整圆落在膜片方形代理区内的孔，edge margin 为 `d/2`，R0 不排除中央锚投影，之后必须重数实际孔和开孔率。

以上规则都为 `C` 类工程闭合，作用是让同一输入得到同一 CAD；它们不会关闭共享/分隔顶腔、真实间隙截面、side frame 或活动孔板形状等开放问题。

## 7. 证据分离的部件合同

`p1_cad_features.csv` 分别记录一个特征的：

- 是否存在；
- 拓扑关系；
- 精确几何；
- 是否选择该分支。

这些证据等级可能不同。例如官方剖面支持热扩散面和单侧出口“存在/拓扑”，但不支持其精确厚度和截面。`C017`、`C019_TOP`、`C019_BOTTOM` 只是厚度记账参考体，禁止材料、质量、结构、CHT、Boolean 和求解器导出。

接口和 Named Selections 必须按稳定特征 ID 重建，禁止依赖会随 Boolean 改变的面序号。每个接口使用分别归属 A/B feature 的一对面集；`{NNN}` 按 `001..N_CELL` 展开，不能把一个 owner 的 selection 同时冒充接口两侧。外部入口/出口域是 P1 可选、P4 必需；产品内部从 vent opening 到 product outlet 的路径是 P1 必需。`p1_cad_open_questions.csv` 的全部问题保持 `OPEN`，完成候选 CAD 不会自动将它们升级为产品事实。

## 8. P1 Gate 解释

`p1_cad_gate_matrix.csv` 的 252 行覆盖 9 个运行变体，初始均为 `NOT_RUN`。三条单因素分支具有独立 variant ID、父变体、changed factor、完整 branch ID 和完整 Gate 行。Windows 006 可以在外部运行目录生成证据和建议值，但不能在任务内宣告 `P1 PASS`。独立复核至少要确认：

- 同一参数化母版可生成四个整机配置；
- 入口到单侧出口完整连通，且每个 cell 都接入完整路径；
- 厚度闭合、无干涉、无零厚度/碎片/孤立流体；
- Boolean 后实际孔数、开孔面积和盲孔数重新统计；
- Named Selections 能稳定传入 Workbench；
- 原生文件、STEP、流体体积、截图、运行日志和 SHA256 可追溯；
- 未知质量单列，不用随意材料把候选模型强行凑成 11 g。

P1 通过只表示“候选整机 CAD 满足当前证据和数值建模要求”，仍不表示内部结构被实物验证。
