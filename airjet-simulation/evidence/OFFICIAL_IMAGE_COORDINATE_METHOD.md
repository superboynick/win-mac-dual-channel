# AirJet Mini Gen1 官方图坐标化与误差规则

状态：P0 可复现提取 v1。目标不是把营销图变成制造图，而是把**能测的图像约束**和**不能测的内部未知量**明确分开。

## 1. 原始证据身份

- 文件：本地研究包 `official/AirJet_Mini_Data_Sheet.pdf`；
- SHA256：`822fbb7e9735a5505734a291083fed7901c1fdfa01cb7de369679e4d41fd19bd`；
- 页面：1 页，`612 x 1548 pt`；
- 官方直接包络：`27.5 x 41.5 x 2.8 mm`；
- 当前复核 Poppler：`26.07.0`。

产品底图是嵌入式位图，不是工程矢量模型。`pdfimages -png` 的相关对象如下：

| 对象 | 尺寸 | SHA256 | 用途 |
|---|---:|---|---|
| RGB object 006 | 636 x 387 | `13d513ff90069afa96ec034ca0d4ae03e5c18205014e4508bc9b7bd702dfbe0d` | 带流向的 Gen1 产品透视图 |
| soft mask 007 | 636 x 387 | `f711b34baa31b0050ea642b0d7167af1e6aa29b4be4fab3a1da57570e79341fb` | object 006 透明蒙版 |
| RGB object 004 | 547 x 257 | `c5286aadcf3a42d338b70cfeaed8fa27f0a6f171cb7621981e34f96378ff4956` | 上方第二产品透视图 |
| soft mask 005 | 547 x 257 | `fb7c08ad552f432f5d70c52e3f34749da17a8a7eb8b4d2b04322b57cd011dcb2` | object 004 透明蒙版 |

300 dpi 全页渲染为 `2550 x 6450 px`，当前文件 SHA256 为 `9686da3780d01f757daff44c145c1f110ac9121580a33b97f8ff42ac9be949fa`。600 dpi 会增加箭头和文字的渲染像素，但不会增加上述嵌入底图的真实细节。

## 2. 坐标系与四点透视校正

所有原生图像坐标以左上角为 `(0,0)`，`x` 向右、`y` 向下。整流后的产品顶面定义：

- `X = 0..27.5 mm`：产品宽度；
- `Y = 0..41.5 mm`：从 flex/rear 侧指向 integrated-spout/outlet 侧；
- 输出分辨率 `20 px/mm`，即 `550 x 830 px`。

636 x 387 图的顶面角点按输出顺序为：

```text
Q0 rear-left    = (318, 53)
Q1 rear-right   = (538, 172)
Q2 outlet-right = (241, 337)
Q3 outlet-left  = (22, 221)
```

547 x 257 图在 PDF placement 中翻转；为了保持相同的 rear-to-outlet 坐标，角点顺序为：

```text
Q0 rear-left    = (463, 130)
Q1 rear-right   = (274, 221)
Q2 outlet-right = (21, 110)
Q3 outlet-left  = (207, 8)
```

使用 8 参数 homography：

```text
X = (h11*x + h12*y + h13) / (h31*x + h32*y + 1)
Y = (h21*x + h22*y + h23) / (h31*x + h32*y + 1)
```

四角每个坐标采用 `+/-3 px` 人工选择范围。禁止用单一 mm/px 比例替代 homography，因为透视图两个方向和前后边的缩放不同。

## 3. 画出的四个 vent 如何提取

vent 中心线来自亮色区域的连通分量和 PCA 长轴，不是手工猜真实开孔：

```text
min(R,G,B) >= 120
max(R,G,B) - min(R,G,B) <= 28
8-connected component
component area > 900 px
PCA long axis
1st and 99th projection percentiles
```

原始端点保存在 `annotated_figures/gen1_vent_homography_results.csv`。两个视图分别变换，不能先把图叠在一起再制造一个虚假的“精确平均图”。

允许结论：官方渲染**画出了四个 elongated top vent objects**，它们可约束第一版顶盖候选开口的位置与对称关系。

禁止结论：

- 四个画出对象等于四组真实量产进气口；
- 一个 vent 对应一个 cell；
- vent 数可以推出 cell 行列数；
- 渲染边缘可以给出制造公差；
- vent 长度/位置的纯像素置信区间就是产品几何置信区间。

## 4. 像素误差和跨视图系统误差

`analyze_official_vent_views.py` 使用固定 seed `20260713`，每个视图运行 10,000 次 Monte Carlo：

1. 四个包络角点的 x/y 独立均匀扰动 `[-3,+3] px`；
2. vent 两个 PCA 端点的 x/y 独立均匀扰动 `[-2,+2] px`；
3. 每次重新计算 homography；
4. 保存 vent 中心、长轴长度的中位数和 95% 区间。

Monte Carlo 只传播**像素选择误差**。`gen1_vent_cross_view_comparison.csv` 还单独保存两张官方渲染之间的差值；目前中心横向差达到毫米量级，明显大于简单 `+/-2 px` 所暗示的精度。因此 CAD 初值必须把跨视图差作为 model-form uncertainty，不得只引用 Monte Carlo 的窄区间。

## 5. 官方剖面能和不能支持什么

`annotated_figures/gen1_cross_section_annotated.png` 记录：

- `D`：总厚度 2.8 mm（同时由 metric table 直接报告）；
- `D` 定性：多膜片、脉冲射流、底部热扩散面、处理器接触关系、单侧 integrated spout 排气；
- `U/C/P`：顶腔、底腔、膜片层叠、孔板、冲击间隙和扩散板的真实厚度。

原生截面底图的外部顶/底边约为 `y=59/178`，119 px 对应画出的 2.8 mm；这个比例只能描述**示意图像本身**。内部色块边界的像素误差即使只有约 0.1 mm，仍没有包含示意图的未知系统误差，因此不得把内部色块直接锁为 CAD 厚度。

绿色波形不能数膜片，黄色箭头不能数喷孔或求喷速，蓝色/红色箭头数量不能求流量或 inlet/outlet 数；Schlieren 图片没有空间尺、时间基准、流量、压力和曝光信息，不能反算速度或体积流量。

## 6. 复算命令

从本地 PDF 提取对象和渲染页面：

```bash
mkdir -p airjet-simulation/tmp/pdfs/p0-mini-datasheet
pdfimages -png "$PDF" airjet-simulation/tmp/pdfs/p0-mini-datasheet/extracted
pdftoppm -r 300 -png -singlefile "$PDF" airjet-simulation/tmp/pdfs/p0-mini-datasheet/mini-datasheet-300dpi
```

生成主要标注图、截面和测量表：

```bash
python3 airjet-simulation/evidence/extract_official_image_geometry.py \
  --rgb airjet-simulation/tmp/pdfs/p0-mini-datasheet/extracted-006.png \
  --mask airjet-simulation/tmp/pdfs/p0-mini-datasheet/extracted-007.png \
  --page-render airjet-simulation/tmp/pdfs/p0-mini-datasheet/mini-datasheet-300dpi.png \
  --out-dir airjet-simulation/evidence/annotated_figures
```

生成双视图 homography、Monte Carlo 和跨视图差：

```bash
python3 airjet-simulation/evidence/analyze_official_vent_views.py \
  --flow-rgb airjet-simulation/tmp/pdfs/p0-mini-datasheet/extracted-006.png \
  --flow-mask airjet-simulation/tmp/pdfs/p0-mini-datasheet/extracted-007.png \
  --upper-rgb airjet-simulation/tmp/pdfs/p0-mini-datasheet/extracted-004.png \
  --upper-mask airjet-simulation/tmp/pdfs/p0-mini-datasheet/extracted-005.png \
  --out-dir airjet-simulation/evidence/annotated_figures
```

依赖：Poppler (`pdfimages`, `pdftoppm`) 和 Pillow。脚本首先校验对象 SHA256；原图不匹配时停止，不静默继续。

## 7. 对 P0/P1 的实际影响

- 顶盖第一版可以使用四个**候选** vent envelope，并保留两视图差异；
- Gen1 官方图仍不支持精确 active-area fraction、flex 占用、spout 截面或内部 cell 数；相关 registry 项保持 `I/C/U`；
- `S_image` 目前不对 Layout-L/M/S 给正向分，因为所有候选都尚未建立可与顶盖/剖面共同投影比较的完整 P1 CAD；
- P1 中若某候选违背“顶部取气、单侧 spout、完整冲击通道”这一 D 类拓扑，才可按图像证据淘汰。
