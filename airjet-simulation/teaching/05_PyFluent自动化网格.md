# 05 — PyFluent 自动化网格

**目标：** 理解如何用 Python 驱动 ANSYS Fluent 自动生成体网格

---

## 1. 为什么用 PyFluent

- **不用点 GUI** — 全部 Python 脚本
- **可复现** — 同样的脚本 = 同样的网格
- **可批量** — 改参数后自动重跑
- **可记录** — 完整 transcript 日志

## 2. Watertight 网格工作流

Fluent 的 Watertight Geometry 工作流是最推荐的自动网格方案：

```
Import Geometry → Surface Mesh → Describe Geometry → 
  → Apply Sizing → Volume Mesh → Save
```

## 3. `save_mesh4.py` 详解

这是我们当前使用的最小可行脚本：

### 3.1 导入几何
```python
watertight.import_geometry.file_name = {
    "formats": ["step"], "cad_import_options": {
        "scale_units_original": "mm", "one_piece_per_file": True
    }
}
watertight.import_geometry.file_name = step_file
```

### 3.2 面网格
```python
watertight.surface_mesh.min_size = 0.05       # 最小面尺寸 mm
watertight.surface_mesh.max_size = 0.75       # 最大面尺寸 mm
watertight.surface_mesh.growth_rate = 1.2     # 增长率
watertight.surface_mesh.size_functions = ["curvature", "proximity"]
```

### 3.3 区域描述
Fluent 自动识别：流体区域、壁面、进出口。
关键：capping 自动封闭开口面。

### 3.4 体网格
```python
watertight.volume_mesh.volume_fill = "poly-hexcore"
watertight.volume_mesh.max_cell_length = 0.75
```

Poly-hexcore = 六面体核心 + 多面体过渡层，质量好、单元少。

## 4. 质量指标

| 指标 | 含义 | 目标 |
|---|---|---|
| Orthogonal Quality (OQ) | 网格正交性 | min ≥ 0.15 |
| Skewness | 网格偏斜 | max ≤ 0.85 |
| Aspect Ratio | 长宽比 | max ≤ 50 |

我们的 C5 网格：35K cells, min OQ 0.57 ✅

## 5. 已知坑

### 5.1 Student 许可限制
- 1M cells/nodes 上限
- Poly-hexcore 默认设置可能生成太多单元
- 必须用 sizing 严格控制

### 5.2 Student 2026 R1 bug
- `volume_statistics` API 调用 → SIGSEGV 崩溃
- 解决方案：从 transcript 提取单元数

### 5.3 区域选择
- WTM 默认选最大连通域
- 如主流体域不通 → 选到 actuator gap
- 解决：确保 Boolean Merge 正确连接

## 6. 运行方式

```powershell
# Windows 上
cd C:\Users\admin\win-mac-dual-channel
python airjet-simulation\save_mesh4.py
```

---

**下一课：** [06 网格独立性验证](#)
