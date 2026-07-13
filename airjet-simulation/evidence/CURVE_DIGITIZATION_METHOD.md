# AirJet Mini 性能曲线数字化方法

状态：P0 可复现临时读图值；尚未因实测或厂商原始数据而升级为精确曲线。

## 原件与渲染

- 原件：`AirJet_research/official/AirJet_Mini_Data_Sheet.pdf`
- SHA256：`822fbb7e9735a5505734a291083fed7901c1fdfa01cb7de369679e4d41fd19bd`
- PDF：1 个纵向长页，612 × 1548 pt
- 固定渲染命令：

```bash
pdftoppm -png -r 150 -f 1 -singlefile AirJet_Mini_Data_Sheet.pdf airjet-mini-page
```

预期完整页 PNG 为 1275 × 3225 px。`airjet_mini_curve_pixels.csv` 的所有坐标都相对于这张完整页，不相对于裁图。

## 坐标轴

绘图区像素边界：

- 左/右：`x0=289`、`x1=975`
- 下/上：`y0=3017`、`y1=2529`
- 横轴：AirJet Mini power，0–1.2 W
- 左纵轴：net heat dissipation，0–4.5 W
- 右纵轴：inside-system acoustics measured at 50 cm，0–25 dBA

右轴含义由 PDF 提取文字和视觉渲染双重确认，不是流量。

## 换算

对于像素点 `(x, y)`：

`x_value = x_min + (x - x0) / (x1 - x0) * (x_max - x_min)`

`y_value = y_min + (y0 - y) / (y0 - y1) * (y_max - y_min)`

点坐标取曲线 marker 中心，允许约 ±2 px 人工定位差；公开图线宽、marker 大小和轴读数误差更大，所以正式临时不确定度保守使用净热 ±0.10 W、噪声 ±0.7 dBA。1 W 的 4.25 W 与 21 dBA 另由同页规格表交叉确认。

## 自动复核

```bash
python3 airjet-simulation/evidence/digitize_airjet_mini_curve.py --repo . --check
```

脚本从像素坐标重算功耗、净热和噪声，与版本化目标 CSV 比较。它不修改输入文件。若渲染 DPI、原 PDF、坐标或目标点变化，检查会失败，必须同时更新来源记录与决策档案。
