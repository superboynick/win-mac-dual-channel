# Windows Ansys Student 清理与纯净基线

日期：2026-07-14
主机：`LAPTOP-LCCLM2HI`
Git 基线：`13b6919deb92124882df61fc9be1d0d525aa06b7`

## 结论

`WINDOWS_ANSYS_STUDENT_CLEANUP_STATUS=PASS`

Windows 可见会话完成第三方 `Ansys PLE Licensing 2026 R1` 卸载，并验证官方 Ansys Student 2026 R1 的 Workbench/Fluent 基础启动与 Student 本地许可签出。Mac 随后通过 SSH 复核卸载项、服务、进程、端口、环境变量、官方安装路径和核心程序数字签名；复核项一致。

这表示授权环境已经具备可判定的官方 Student 基线，但不表示 P1--P5 工程能力已全部通过。下一步必须运行 `AJM_WIN_ANSYS_STUDENT_CAPABILITY_SMOKE_005.md`。

## Windows 可见会话报告

- MSI 卸载返回 0；
- PLE 服务、安装/ProgramData 残留、厂商注册项、防火墙规则、计划任务、启动项和 hosts 修改均报告为 0；
- `lmgrd/ansyslmd` 进程、1055 监听均为 0；
- Machine/User `ANSYSLMD_LICENSE_FILE=1055@localhost` 已清除；
- 官方 Student 安装根目录：`D:\ansys\ANSYS Inc\ANSYS Student\v261`；
- Workbench 批处理启动退出码 0；
- Fluent 报告成功签出并归还 `cfd_base`、`cfd_solve_level1`、`cfd_solve_level2`，来源为 Student 本地许可池；
- 测试结束后无 Ansys/许可进程残留。

上述 Fluent checkout 历史来自 Windows 可见会话报告；没有在 Downloads 找到独立报告文件供 Mac 复读，因此不把它升级为 Mac 独立复现结果。

## Mac SSH 再验证

- Git 工作树干净，HEAD 与 `origin/main` 为 0/0；
- PLE 卸载注册项：0；
- PLE 服务：0；
- `lmgrd/ansyslmd` 进程：0；
- 1055 监听：0；
- Machine/User `ANSYSLMD_LICENSE_FILE`：空；
- 官方 Student 根目录存在；
- `RunWB2.exe`、`fluent.exe`、Mechanical APDL `ansys.exe`、`SpaceClaim.exe` 均为 `Authenticode=Valid`，签名主体 `ANSYS Inc.`；
- 复核结束时 Ansys 相关进程：0。

SSH 没有启动 GUI 或求解器，也没有读取/修改许可文件、服务配置、注册表授权值或 Student 本地许可池。

## 已知安装警告

Student 安装日志曾报告 `python_site_syscplg` 与 `cuDSS` 两个压缩包解压失败。当前报告只确认 Workbench/Fluent 基础启动和清理状态；System Coupling 与相关 GPU 稀疏求解功能仍为 `UNVERIFIED/WARNING`。在 P2--P5 真正需要这些功能前，应使用官方安装器执行修复并重新做针对性测试，不能把警告静默忽略。

## 当前工程边界

- P1：取决于 005 中 SpaceClaim 参数化、Named Selections、Volume Extract、原生保存和 Workbench 几何传递；STEP 导出失败只形成交接限制，不是唯一硬门槛。
- P2：取决于 Mechanical 最小求解、Modal/Harmonic 与压电/Mechanical APDL coupled-field 路线。
- P3--P5：取决于 Fluent 瞬态可压缩、Dynamic Mesh、UDF/profile、CHT、可用核数和实际 Student 模型规模限制。
- 30 天官方试用申请继续作为后续扩展路线；申请未激活时不替代当前 Student 基线。
