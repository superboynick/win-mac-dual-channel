# AJM005 T0 首轮：失败证据解释

## 判定

- process terminal state：四个 job 中两个 `PROCESS_EXITED_0`、一个 `FAILED_PROCESS`、一个
  `TIMED_OUT`。
- control status：SpaceClaim 与 PyMechanical 为 `PASS_CONTROL`；Workbench 与 PyFluent 为
  `FAIL_CONTROL`；因此 suite 为 `FAIL_CONTROL_SET`。
- engineering capability：`NOT_RUN`。没有参数化腔体、Named Selection/Workbench 传递、
  Mechanical 静力求解、Fluent 网格/流动求解或质量守恒证据。
- visibility：`NOT_USER_OBSERVED`。
- Gate effect：P0 保持 PASS；P1--P6 全部 `NOT_RUN`。

## 为什么失败仍必须保留

Workbench 成功保存项目和 `SYS`，却因把 UI 显示名当作完整脚本键而失败。PyFluent 已经返回
`SERVING`，但脚本把 `Ansys Fluent 2026 R1` 人类显示文本当作版本协议；随后默认异步退出又让
Fluent/Cortex/MPI 进程树继续存活。两者都说明“程序打开了”不是稳定的自动化断言。

这轮记录不能被后来的 PASS 覆盖。它用于说明：

1. 显示字符串与内部类型/键要分开验证；
2. 根 Python 进程退出不等于整个求解器进程树已退出；
3. 修复必须改变签名脚本 SHA，并用新 job ID 复测；
4. watchdog 和 Job Object 没有把长尾进程误报为成功。

完整 suite JSON 以 Windows 路径和 SHA-256 固定在 `suite-summary.json`。仓库只保存脱敏凝练
摘要；原生 `.scdocx`、`.wbpj` 和完整 job 目录仍留在 Windows。
