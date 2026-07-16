# 04 — SpaceClaim 参数化几何

**目标：** 理解 AirJet Mini 几何如何在 ANSYS SpaceClaim 中通过 Python API 构建

---

## 1. 为什么参数化

AirJet Mini 有 972 个微喷口、12 个单元。手动 CAD 不可行。参数化意味着：
- 改一个数字（如膜片间距）→ 全部几何自动更新
- 可追溯到论文中的每个尺寸来源
- 可复现——别人拿到代码就能重建

## 2. 坐标系统

| 轴 | 含义 | 范围 |
|---|---|---|
| X | 宽度方向（短边） | -10.875 ~ +10.875 mm |
| Y | 长度方向（长边） | -17.75 ~ +20.75 mm |
| Z | 厚度方向（垂直） | 0 ~ 1.53 mm |

原点在膜片区域几何中心。

## 3. Z 向分层

AirJet 在厚度方向分为多个功能层：

```
Z = product_top_z      → 顶部盖板
Z = plenum_top_z       → 集气腔顶部
Z = membrane_top_z     → 膜片腔顶部
Z = bottom_z_max       → 膜片腔底部
Z = bottom_z_min       → 底腔底部
Z = interface_z        → 孔板/喉道界面
Z = orifice_top_z      → 喷口出口
Z = heat_z             → 散热器底面
```

## 4. 构建流程（`v03_continuous_fluid_producer.py`）

### Step 1: 主流体域（upstream block）
```
X: footprint_x_min → footprint_x_max
Y: footprint_y_min → footprint_y_max
Z: membrane_top_z → plenum_top_z
```

### Step 2: 排气 risers
每个排气槽创建一个 block，从 plenum 延伸到产品顶部。

### Step 3: 12 个单元
每个单元创建：
- **Bottom block** — 膜片下方空腔
- **4 个 Ring blocks** — 膜片四周的环形间隙（L, R, B, T）
- **81 个 Orifice cylinders** — 微喷口（半径 0.125mm，喉长 0.10mm）

### Step 4: 下游域（downstream block）
```
X: footprint_x_min → footprint_x_max
Y: footprint_y_min → manifold_y_max
Z: heat_z → interface_z
```

### Step 5: Boolean Merge
`Combine.Merge(upstream, downstream)` → 单一连续流体域

## 5. 关键参数

| 参数 | 值 | 来源 |
|---|---|---|
| membrane_mm | 7.0 | 产品图估算 |
| pitch_mm | 7.0 | 膜片间距 = 单元间距 |
| throat_length_mm | 0.10 | 专利 US11510341 |
| throat_radius_mm | 0.125 | 孔径 0.25mm |
| numerical_overlap_mm | 0.02 | 圆柱/面 Boolean 重叠 |
| perimeter_boolean_overlap_mm | 0.05 | Ring/Membrane Boolean 重叠（内收式） |

## 6. 几何合同（Contract）

每次 Stage 1 产出必须验证：

1. **1 个闭合流形实体** — 不是多个碎片
2. **972 个喉道** — 每个孔口面都在
3. **体积 ±0.08mm³** — 与冻结参考值一致
4. **包络 ±0.001mm** — X/Y/Z bounds 不变
5. **边界标定** — Inlet/Outlet/Wall faces 正确

## 7. 当前已知问题

| 问题 | 状态 |
|---|---|
| Boolean 连接 | 0.05mm 内收式修复待验证 |
| 主流体域 vs actuator gap | 0.15mm 诊断已证明可修复 |
| CRLF 行尾 | .gitattributes 已永久修复 |

---

**下一课：** [05 PyFluent 自动化网格](#)
