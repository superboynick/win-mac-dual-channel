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

确定性 suite runner 一次串行执行多个 MCP job 时，可使用一个
`AJM005_T0_SUITE_<timestamp>_<nonce>/` 聚合目录，条件是：

- `run-index.csv` 仍为每个 job 单独一行；
- `suite-summary.json` 逐项保留 job/profile/commit/script/report SHA、终态和外部目录；
- `interpretation.md` 明确区分 suite 结论与各 job 结论；
- 完整原始 suite JSON 及大文件仍用绝对路径、字节数和 SHA-256 登记；
- 聚合摘要自身不是原始 manifest，不能伪造一个并不存在的 manifest SHA。
