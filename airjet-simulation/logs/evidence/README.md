# 小型运行证据目录

每个 MCP run 使用 `logs/evidence/<run_id>/`，只提交脱敏小文件：

```text
job.json
artifact-manifest.json
<declared-report>.json
interpretation.md
```

原生 CAD、Workbench project、Mechanical database、mesh、Fluent case/data、transcript 和大场
文件留在 Windows 固定输出根，通过 `logs/external-files.csv` 登记路径、大小和 SHA-256。
`interpretation.md` 必须分开写 process terminal state、control status、engineering capability、
visibility 和 Gate effect；不能从退出码直接推断 PASS。
