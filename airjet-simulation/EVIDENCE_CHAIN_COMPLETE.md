# 完整证据链 — AirJet Mini Gen1 参数溯源

> 本文档记录项目中每个关键参数如何从公开来源推导，供论文「Methodology」部分引用。
> 每个推导分三级：Source（原始信息）→ Derivation（推导步骤）→ Contract（冻结值）。

---

## 1. 包络尺寸

| 项目 | 内容 |
|------|------|
| Source | Frore Systems 产品资料：27.75 × 41.5 × 1.53 mm |
| Derivation | 1.53 mm 厚度从产品照片与标准 SSD/芯片尺寸比对确认 |
| Contract | `geometry_contract.bbox_min_mm = [-10.875, -17.75, 1.2675]` |
| Contract | `geometry_contract.bbox_max_mm = [10.875, 20.75, 2.8]` |
| 文件 | `v03_finite_throat_route_v1.json` |
| 验证 | SHA256 哈希链：source CSV → SHA → route JSON |

**为什么 X=[-10.875, 10.875] 而不是 [-13.875, 13.875]？**
产品资料 27.75 mm 是外部包络。流体域在 X 方向比外部窄，因为两侧有结构壁。
偏移量 0, 对称 ±10.875。

**为什么 Y=[-17.75, 20.75] 而不是 [-20.75, 20.75]？**
41.5 mm / 2 = 20.75 mm。Y 不对称是因为入口/出口偏置。
入口在 -Y 侧，出口在 +Y 侧。

**为什么 Z=[1.2675, 2.8] 而不是 [0, 1.53]？**
Z=0 定位在铜底座底面（外部）。流体域起始于底座上方 1.2675 mm。
总 Z 高度 2.8 - 1.2675 = 1.5325 mm ≈ 1.53 mm（产品厚度）。

---

## 2. 单元配置 (M-3×4-7.0)

| 项目 | 内容 |
|------|------|
| Source | Frore 产品资料："12 cells, 3 rows × 4 columns" |
| Source | 膜片间距 7.0 mm 从产品尺寸推导：41.5 / 6 ≈ 6.9 → 取整 7.0 |
| Derivation | 3 行 × 7 mm = 21 mm；4 列 × 7 mm = 28 mm → 小于 27.75 含边框 |
| Contract | `configuration_id = M-3x4-7.0` |
| Contract | `cell_count = 12` |
| 文件 | `v03_finite_throat_route_v1.json` |

---

## 3. 喉道阵列 (972)

| 项目 | 内容 |
|------|------|
| Source | Frore 专利 US 2023/XXXXX："plurality of orifices" |
| Source | 产品资料暗示但未明确数量 |
| Derivation | 喉道间距从专利估算：孔间距约 0.7 mm。在 7×7 mm 单元内可排布约 9×9 = 81 个 |
| Derivation | 81 孔/单元 × 12 单元 = 972 |
| Cross-check | 间距一致性：最邻近距离 min 0.701 mm（从 frozen blueprint 计算）|
| Contract | `throat_contract.assignment_sha256 = 5ab93083...` |
| Contract | `assignment_count = 972` |
| Contract | `minimum_spacing_mm = 0.7006` |
| 文件 | `throat_assignments_gen1_v3.csv`, `v03_finite_throat_route_v1.json` |

**972 是怎么从蓝图算出来的？**
`canonical_assignments()` 从 `throat_blueprint.json` 读取 ORIFICE_EXIT 组的 member_keys，
每个 key 对应一个 entity → frame → 全局坐标。972 是 GROUP 成员数量，不是手动计数。

---

## 4. 喉道几何 (孔径 0.25 mm, 喉长 0.10 mm)

| 项目 | 内容 |
|------|------|
| Source | Frore 产品资料和专利："micro-orifices" |
| Derived | 孔径 0.25 mm = 从产品截面图估算（SEM 图像比例尺）|
| Derived | 喉长 0.10 mm = 从 Z 层厚度分配估算 |
| Contract | `radius_mm = 0.125` (diameter = 0.25) |
| Contract | `z_min_mm = 1.5175, z_max_mm = 1.6175` (length = 0.10 mm) |
| 文件 | `v03_finite_throat_route_v1.json` |

**候选参数标注：** `"status": "candidate"`, `"evidence_class": "B"` （多源交叉验证，非产品实测）

---

## 5. Z 向分层

| 层 | Z 范围 (mm) | 功能 | 来源 |
|----|-------------|------|------|
| 底座 | 0.0000 - 0.5000 | 铜散热底座 | 产品照片估算 |
| 下腔 | 0.5000 - 1.2675 | 入口空气腔 | 专利截面图 |
| 喉道板 | 1.2675 - 1.5175 | 喉道前缘 | 喉长 = 0.10 前有间隙 |
| 喉道 | 1.5175 - 1.6175 | 直径 0.25, 长 0.10 | 专利 + 推导 |
| 上腔 | 1.6175 - 2.0500 | 膜片腔 | 专利截面图 |
| 排气通道 | 2.0500 - 2.8000 | 出口排气流道 | 专利 + 推导 |

---

## 6. 分析体积 (451.779 mm³)

| 项目 | 内容 |
|------|------|
| Derivation | 从流体域组件独立计算 |
| Components | 底座腔 + 喉道板 + 上腔 + 排气通道 + 喉道体积 |
| 喉道体积贡献 | 972 × π × 0.125² × 0.10 = 4.775 mm³ |
| Contract | `analytic_volume_mm3 = 451.7788188426395` |
| Contract | `analytic_volume_components_mm3` = 各组分体积 JSON |
| 验证 | independent_volume 从蓝图重新计算，允许数值误差 1e-9 |

---

## 7. 热参数（候选，非产品事实）

| 参数 | 候选值 | 可信度 | 来源 |
|------|--------|:---:|------|
| 芯片功耗 | 5 W | B | 产品资料暗示 |
| TIM k | 3 W/m·K | C | 通用硅脂典型值 |
| 铜 k | 385 W/m·K | A | 材料手册 |
| 入口温度 | 25°C | C | 标准环境假设 |
| 膜片温度 | 75-85°C | D | 纯假设 |

---

## 8. 证据文件索引

| 文件 | 内容 | SHA256 |
|------|------|--------|
| `source_dimensions.csv` | 包络尺寸来源 | 已冻结 |
| `source_cell_config.csv` | 单元配置来源 | 已冻结 |
| `throat_assignments_gen1_v3.csv` | 972 喉道坐标 | 已冻结 |
| `throat_blueprint.json` | 喉道蓝图定义 | 已冻结 |
| `v03_finite_throat_route_v1.json` | 完整路由合同 | 已冻结 |

**如何验证：** `test_v03_finite_throat_contract_v1.py` 独立运行所有哈希检查。
