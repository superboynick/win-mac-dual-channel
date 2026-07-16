# 第2课：Fluent Watertight 网格工作流详解

## 为什么选 Watertight？

Fluent 2026 R1 提供两种网格工作流：
- **Watertight**：适合"不漏水"的封闭几何 → 我们用它
- **Fault-tolerant**：适合有缝隙的复杂几何

AirJet 流体域经过 Boolean 运算后是封闭的 → Watertight。

## 工作流 7 步

### 1. Import Geometry
```python
meshing.workflow.TaskObject['Import Geometry'].Execute()
```
把 SpaceClaim 导出的 STEP 文件读入 Fluent。

### 2. Add Local Sizing
```python
meshing.workflow.TaskObject['Add Local Sizing'].Execute()
```
在关键区域（972 个微孔）加更细的网格。
- 孔径 0.25mm → 局部尺寸 0.075mm（孔径的 30%）
- 表面尺寸：0.05mm（min）到 0.75mm（max）

### 3. Generate Surface Mesh
```python
meshing.workflow.TaskObject['Generate the Surface Mesh'].Execute()
```
生成面网格。输出：三角形覆盖所有流体表面。

### 4. Describe Geometry
```python
meshing.workflow.TaskObject['Describe Geometry'].Execute()
```
关键步骤！告诉 Fluent 几何类型：
- `setup_type`：流体域是有边界的封闭体积
- 识别哪些面是 inlet，哪些是 wall

**我们最大的 bug 在这里**：Fluent 选了 actuator gap（13.5mm³）而非主流体（451.8mm³）。
修复：反向边界法向量 + material point 指定。

### 5. Update Regions
```python
meshing.workflow.TaskObject['Update Regions'].Execute()
```
根据 Describe Geometry 的结果创建流体区域。

### 6. Add Boundary Layers（可选）
在壁面附近加棱柱层。目前 C5 粗网格跳过。

### 7. Generate Volume Mesh
```python
meshing.workflow.TaskObject['Generate the Volume Mesh'].Execute()
```
生成体网格。选择 poly-hexcore（多面体-六面体混合）。

## PyFluent API 要点

所有操作通过 Python 调用，不需要 GUI：
```python
import ansys.fluent.core as pyfluent

solver = pyfluent.launch_fluent(
    mode="meshing",
    precision="double",
    processor_count=1,
    ui_mode="no_gui"
)

meshing = solver.meshing
# ... 执行工作流步骤
```

## 我们踩过的坑

| 问题 | 原因 | 修复 |
|------|------|------|
| 域选错（13.5 vs 451.8 mm³） | 边界法向量朝内 | 反转法向 + 加 material point |
| Boolean 不闭合 | 0.02mm overlap 太小 | 0.15mm overlap |
| CRLF 哈希不匹配 | Windows autocrlf | canonical LF 归一化 |
| Student 许可 1M cell 限制 | Student 版 | 等 Academic Research |
| 972 孔占用检查过松 | 接受 12/972 | 强制 972/972 |

## 验证清单（C5 PASS 条件）

网格完成后必须验证：
- [x] 面网格：fluid + 11 voids
- [x] 体网格：≥ 1 cell, < 1M cells
- [x] 972/972 孔占用（每个孔都穿过网格）
- [x] 12 个 actuator gap 排除
- [x] 流体区域连通（graph connected）
- [x] OQ ≥ 0.15（我们的标准）
- [x] free face = 0, multi face = 0
- [x] .msh.h5 文件有 SHA256 哈希

## 下一步

第3课 → 深入网格质量与独立性验证
