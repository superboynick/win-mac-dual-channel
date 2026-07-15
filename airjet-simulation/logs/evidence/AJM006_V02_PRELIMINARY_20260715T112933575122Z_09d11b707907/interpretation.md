# V02 第一次实跑：宿主兼容失败

SpaceClaim 进程正常退出，但 producer 在创建任何 CAD 实体之前，于冻结依赖的 canonical hash 中把 CPython 3 `bytes` 写法带入 V261 IronPython 字符缓冲路径，得到 `TypeError: expected a character buffer object`。因此 runner 正确拒绝 PASS。

报告中的十项 `false` 是异常前初始化值，应解释为 `NOT_REACHED`，不能写成十项工程检查各自失败。最小修复只改变 CRLF canonicalization 的字符类型，不改变 12-cell、972-hole、两区几何或 Gate 门槛。P1--P6 仍为 `NOT_RUN`。

原始目录保留在 Windows；逐文件一致副本与三次运行 ZIP 保留在 Mac/Windows Downloads。此目录只保存凝练、可审计的小证据。
