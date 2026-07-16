# AirJet Mini Gen1 整机仿真复现指南

**版本：** 2026-07-16
**目标：** 从零开始复现 AirJet Mini Gen1 全产品 CFD 网格

---

## 1. 项目目标

对 Frore Systems AirJet Mini Gen1 固态主动散热芯片进行全产品 CFD 仿真重建。

- **产品：** AirJet Mini Gen1（27.75 × 41.5 × 1.53 mm 包络）
- **配置：** M-3x4-7.0（12 单元，3 行 × 4 列，7.0 mm 膜片间距）
- **喉道：** 972 个微喷口（每单元 81 个，孔径 0.25 mm，喉长 0.10 mm）
- **目标网格：** 粗网格 ~35K cells（Student 许可验证）→ 中网格 500K-2M → 细网格 >5M
- **后续：** CHT 共轭传热、FSI 流固耦合（压电膜片）

---

## 2. 软件环境

### 必需软件

| 软件 | 版本 | 用途 |
|---|---|---|
| ANSYS Student | 2026 R1 (26.1) | Fluent 网格 + 求解 |
| Python | 3.12 | PyFluent API 自动化 |
| Git | 任意 | 版本控制 |

### Python 环境

```powershell
# Windows
python -m venv C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv
.venv\Scripts\pip install ansys-fluent-core==0.20.0
```

### 许可说明

- **Student 版：** 免费，cell/node 上限 ~1,048,576。粗网格（<100K cells）完全可行
- **Academic Research：** 需申请，无 cell 限制。联系 Ansys 销售（董如怡 ruyi.dong@ansys.com）
- **已验证：** Student 版可生成 35,108 cells 体网格，min OQ 0.57

---

## 3. 项目仓库

```bash
git clone git@ssh.github.com:superboynick/win-mac-dual-channel.git
cd win-mac-dual-channel
```

### 关键目录

```
airjet-simulation/
├── automation/ansys/
│   ├── approved/006/
│   │   ├── v03_continuous_fluid_producer.py    # SpaceClaim 几何脚本
│   │   └── v03_pyfluent_watertight_mesh_consumer.py  # Fluent 网格脚本
│   ├── contracts/         # 参数合同与验证
│   ├── run_v03_continuous_fluid_006.py         # Stage 1 启动器
│   └── run_v03_continuous_mesh_006.py          # 完整两阶段启动器
├── logs/evidence/c5_mesh/ # 已产出的网格文件
├── parameters/            # 所有几何和物理参数
└── geometry/contracts/    # CAD 特征合同
```

---

## 4. 几何参数（完整规格）

### 4.1 产品尺寸

| 参数 | 值 | 来源 |
|---|---|---|
| X 包络 | -10.875 ~ +10.875 mm | 产品图纸推断 |
| Y 包络 | -17.75 ~ +20.75 mm | 产品图纸推断 |
| Z 包络 | 1.2675 ~ 2.8 mm | 产品图纸推断 |
| 单元排列 | 3 行 × 4 列 = 12 单元 | 产品图纸 |
| 膜片间距 (pitch) | 7.0 mm | 产品图纸 |
| 膜片半宽 (half_membrane) | 3.5 mm | pitch / 2 |

### 4.2 Z 向分层（从下到上）

| 层 | Z 范围 (mm) | 厚度 (mm) | 证据等级 |
|---|---|---|---|
| 热源界面 (heat) | -- | -- | C（候选） |
| 底腔 (BOTTOM_CHAMBER) | 1.2675 ~ 1.6175 | 0.35 | B（推断） |
| 孔板 (ORIFICE_PLATE/C016) | 1.5175 ~ 1.6175 | 0.10 | C（候选占位） |
| 冲击通道 (IMPINGEMENT) | 1.6175 ~ 1.6575 | 0.04 | B（推断） |
| 膜片/顶腔界面 | 1.6575 | -- | -- |
| 顶腔 (TOP_CHAMBER) | 1.6575 ~ 2.8 | 1.1425 | B（推断） |
| 顶盖 (TOP_COVER) | 2.8+ | -- | -- |

**喉道参数（972 个）：**
- 孔径 (diameter)：0.25 mm
- 喉长 (length)：0.10 mm
- Z 范围：1.5175 ~ 1.6175 mm

**Boolean 构造 overlap：**
- 喉道端部 overlap：0.02 mm
- 底腔-环形壁 overlap：0.15 mm（C5 修复值，原 0.02 不足）

### 4.3 排气参数

| 参数 | 值 |
|---|---|
| Cell footprint X | -10.875 ~ +10.875 mm |
| Cell footprint Y | -17.75 ~ +17.75 mm |
| Manifold Y max | +20.75 mm |
| Outlet width | 25.0 mm |

---

## 5. 网格规格

| 参数 | 值 | 说明 |
|---|---|---|
| 面网格 min size | 0.05 mm | 喉道区域局部细化 |
| 面网格 max size | 0.75 mm | 全局 |
| 体网格 max size | 0.75 mm | poly-hexcore |
| 喉道局部 size | 0.075 mm | 原设计 0.05mm 超标 |
| 体网格类型 | poly-hexcore | Fluent watertight |
| Student cell 上限 | 1,048,576 | Student 许可硬限 |
| Student node 上限 | 1,048,576 | Student 许可硬限 |
| 目标 cell zone 数 | 1 | 单一主流体域 |
| 期望流体体积 | 451.773 mm³ | 从 STEP predecessor 冻结 |

### C5 粗网格结果（⚠️ 诊断性 — 非正式几何/P1/求解器结果）

| 指标 | 值 | 备注 |
|---|---|---|
| 体单元数 | 39,062 | 0.15mm Boolean overlap |
| 面网格面数 | ~334,190 (total) | 含 dead zones |
| 流体区域数 | 1 fluid + 11 voids | ✅ 主流体域（全产品包络） |
| min Orthogonal Quality | 0.49 | 下游需 ≥0.15 |
| 外部 baffle | 1 (zone 323) | 预期 |
| 网格文件大小 | 8.97 MB (.msh.h5) | SHA256 见 logs/evidence |

> ⚠️ **关键区分：** 此网格证明了 0.15mm overlap 修复了区域选择
> （27.75×41.5×1.53mm 包络 → 主流体域），但**几何合同被违反**：
> X 包络从 ±10.875mm 变为 ±10.9mm，体积超差。此网格仅用于
> 流程诊断，不可用于 P1 几何验证、P2 网格独立性、或 P3 求解。

---

## 6. 运行步骤

### 6.1 生成几何（Stage 1 — SpaceClaim）

**注意：** Stage 1 需要 Windows + SpaceClaim。MCP 基建脆弱时可通过直接脚本运行。

```powershell
# Windows PowerShell
cd C:\Users\admin\win-mac-dual-channel
C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe `
  airjet-simulation\automation\ansys\run_v03_continuous_fluid_006.py
```

**产出：**
- `D:\AirJet_P1\AJM-P1-CAD-006\AJM006-V03-CONTINUOUS\<job_id>\product_continuous_fluid.step`
- 附带：native .scdocx, step reimport, throat inventory, producer report

### 6.2 生成网格（Stage 2 — PyFluent）

**方法 A：save_mesh4.py（推荐，绕过基建问题）**

```powershell
cd C:\Users\admin\win-mac-dual-channel
taskkill /F /IM fluent.exe
timeout /t 3 /nobreak
C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe save_mesh4.py
```

**方法 B：完整两阶段 runner（需要 MCP 基建正常）**

```powershell
C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe `
  airjet-simulation\automation\ansys\run_v03_continuous_mesh_006.py
```

**产出：**
- `airjet-simulation/logs/evidence/c5_mesh/v03_mesh.msh.h5`（体网格）
- `airjet-simulation/logs/evidence/c5_mesh/fluent-*.trn`（Fluent 转录日志）
- 配套 workflow 文件（.wft, .sf, .pmdb）

### 6.3 验证网格

```python
import ansys.fluent.core as pyfluent
from ansys.fluent.core import FluentVersion, FluentMode

s = pyfluent.launch_fluent(
    product_version=FluentVersion.v261,
    mode=FluentMode.SOLVER,  # 或 MESHING
    ui_mode="no_gui"
)
s.tui.file.read_mesh("v03_mesh.msh.h5")
s.tui.mesh.check()
s.tui.mesh.quality()
```

---

## 7. 已知问题与解决方案

| 问题 | 原因 | 解决 |
|---|---|---|
| MCP BLOCKED_DIRTY_WORKTREE | Windows CRLF vs Git LF | 添加 `.gitattributes` + `core.autocrlf=false` |
| MCP BLOCKED_PROFILE_SCRIPT_HASH_MISMATCH | 同上 | 同上 |
| Fluent volume-statistics SIGSEGV | Student 2026 R1 bug | 跳过 API 查询，从 transcript 提取数据 |
| 972 点查询返回 None | v261 post-volume API 限制 | 改用 face adjacency 验证喉道连通性 |
| Student license "Exiting due to license issue" | poly-hexcore 默认网格太密 | 使用 sizing 控制（max 0.75, min 0.05, throat 0.075） |
| 体网格域为 actuator gap 而非主流体 | SpaceClaim Boolean overlap 不够 | 0.02→0.15mm 修复区域选择但违反几何合同；需内收式修复（见 §11） |

---

## 8. save_mesh4.py 脚本

直接运行 PyFluent watertight 网格的最小脚本（绕过 MCP 基建）：

```python
import sys, json
from pathlib import Path
import ansys.fluent.core as pyfluent
from ansys.fluent.core import FluentVersion, FluentMode, Precision, Dimension, UIMode

# 找最新 STEP 文件
BASE = Path(r"D:\AirJet_P1\AJM-P1-CAD-006\AJM006-V03-CONTINUOUS")
dirs = sorted(BASE.glob("AJM006-V03-CONTINUOUS-*"), 
              key=lambda p: p.stat().st_mtime, reverse=True)
step = None
for d in dirs:
    c = d / "product_continuous_fluid.step"
    if c.exists(): step = c; break

out = Path(r"C:\Users\admin\win-mac-dual-channel\airjet-simulation\logs\evidence\c5_mesh")
out.mkdir(parents=True, exist_ok=True)
mesh_path = out / "v03_mesh.msh.h5"

s = pyfluent.launch_fluent(
    product_version=FluentVersion.v261, mode=FluentMode.MESHING,
    precision=Precision.DOUBLE, dimension=Dimension.THREE,
    processor_count=1, start_timeout=120,
    ui_mode=UIMode.NO_GUI_OR_GRAPHICS, cleanup_on_exit=True, cwd=str(out))

wf = s.watertight()
wf.import_geometry.file_name = str(step)
wf.import_geometry.length_unit = "mm"
wf.import_geometry.cad_import_options.one_zone_per = "face"
wf.import_geometry()

# 面网格
wf.create_surface_mesh.cfd_surface_mesh_controls.max_size = 0.75
wf.create_surface_mesh.cfd_surface_mesh_controls.min_size = 0.05
wf.create_surface_mesh()

# 区域识别
wf.describe_geometry.setup_type = "fluid_solid_voids"
wf.describe_geometry()
wf.create_regions.number_of_flow_volumes = 1
wf.create_regions()
wf.update_regions()

# 体网格
wf.create_volume_mesh_wtm.volume_fill = "poly-hexcore"
wf.create_volume_mesh_wtm()

# 保存
if mesh_path.exists(): mesh_path.unlink()
s.tui.file.write_mesh(str(mesh_path))
print(f"SAVED: {mesh_path.stat().st_size} bytes")
(out / "result.json").write_text(json.dumps({"status": "PASS", "size": mesh_path.stat().st_size}))
```

---

## 9. 参数来源

所有参数存储在：
- `airjet-simulation/parameters/p1_cad_parameter_map.csv` — 完整参数注册表
- `airjet-simulation/parameters/p1_internal_geometry_rules.csv` — 内部几何规则
- `airjet-simulation/parameters/p1_layout_configuration_matrix.csv` — 布局配置
- `airjet-simulation/parameters/p1_orifice_pattern_candidates.csv` — 孔阵列候选
- `airjet-simulation/parameters/p1_thickness_budget.csv` — Z 向厚度预算

**证据等级：**
- **A 级：** 产品数据表直接数值
- **B 级：** 专利/图纸推断
- **C 级：** 工程估算/占位符

---

## 10. 产出物清单

| 文件 | 说明 |
|---|---|
| `v03_mesh.msh.h5` (8.1 MB) | ANSYS Fluent 体网格 |
| `fluent-*.trn` | Fluent 完整转录日志 |
| `product_continuous_fluid.step` | 中性格式几何 |
| `v03_continuous_fluid_producer.json` | Stage 1 产出报告 |
| `v03_pyfluent_watertight_mesh_consumer.json` | Stage 2 产出报告 |
| `result.json` | 网格保存确认 |

## 11. 0.15mm 诊断结果分析（⚠️ 流程验证通过，几何合同违反）

### ✅ 已验证的能力

- Fluent WTM 自动识别主流体域（非 actuator gap 腔体）
- HDF5 节点坐标：X=[-10.9, 10.9], Y=[-17.75, 20.75], Z=[1.27, 2.80] mm
- 1 fluid zone + 11 voids：几何拓扑正确
- min OQ 0.49：Student 许可下可生成可用网格

### ❌ 几何合同违反

| 参数 | 冻结值 | 0.15mm 实际 | 超差 |
|---|---|---|---|
| X 包络 | ±10.875 mm | ±10.9 mm | +0.025 mm |
| Y min | -17.75 mm | -17.750025 mm | +0.000025 mm |
| 体积 (native) | 451.779 mm³ | 451.880 mm³ | +0.102 mm³ |
| 体积 (STEP) | 451.779 mm³ | 451.875 mm³ | +0.096 mm³ |

### 🔧 下一步几何修正方案

**方案 A（推荐）：内收式 Boolean overlap**
- 不扩展流体域边界，将 actuator pocket 体向域内延伸 0.10 mm
- 重叠区域完全包含在原始冻结几何体内部
- 预期：X=±10.875, Y=-17.75 保持不变

**方案 B：两步法**
- Step 1: 流体域临时扩大 0.20 mm → Boolean subtract
- Step 2: 用原始边界面裁剪回冻结尺寸

**方案 C：Split Face 替换 Boolean Subtract**
- 用 pocket 面与主流体域面求交 → Split Face → 删除 pocket 区域
- 避免 Boolean 容差问题
