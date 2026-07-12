# 操作手册 07：算例、注释与 Git 交接

## 1. 算例编号

格式：`AJM-P<stage>-<layout>-<physics>-vNNN`

示例：

- `AJM-P1-M-CAD-v001`
- `AJM-P2-M-PIEZO-v003`
- `AJM-P3-M-CELL-CFD-v005`
- `AJM-P4-M-FULL-AIR-v002`
- `AJM-P5-M-FULL-CHT-v001`

## 2. 每次运行必须记录

- 日期、机器、软件和版本；
- Git commit 与参数 registry 版本；
- CAD/mesh/case/data 的实际路径及 SHA256；
- 物理模型、边界、材料、网格数和质量；
- CPU 核数、RAM 峰值、运行时间；
- 收敛/周期稳定、质量与能量误差；
- 主要输出和异常；
- 这次结果能说明什么、不能说明什么；
- 下一步和是否通过 stage gate。

## 3. Git 中保存

- Markdown 手册与日志；
- 参数 CSV/YAML；
- journal、UDF、PyFluent/Python 脚本；
- 小型结果 CSV、关键截图和图表源；
- 外部大文件校验和与路径索引。

不保存：许可证、凭据、完整大型 `.cas/.dat`、超大网格和全部瞬态场。

## 4. Windows 工作流

开始：

```powershell
cd C:\Users\admin\win-mac-dual-channel
git pull
git status
```

结束：

```powershell
git add airjet-simulation
git commit -m "airjet: describe completed modeling step"
git push
```

若 `git status` 显示不认识的修改、分支分叉或 pull 冲突，停止并先让 Codex检查，不自动 reset/rebase/force push。

## 5. 大文件索引

在 `logs/external-files.csv` 保存：

`case_id,file_role,absolute_path,size_bytes,sha256,created_at,software_version`

Windows 和 Mac 路径不同，但通过 `case_id + sha256` 确认是同一个模型文件。
