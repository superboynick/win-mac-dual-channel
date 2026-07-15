# AJM-005 T1 run #22：RunScript 返回，但 child entry/build 未被观测

本轮是可删除 connected fixture 的 `Interactive=True + RunScript-only` 诊断，不是 AirJet 产品 CAD、
MEMS、结构、CFD 或 CHT。producer 在 21.451068 s 内以 `PROCESS_EXITED_0` 结束，八项断言均为真，
状态只允许写成 `PASS_PARTIAL_CAD_CAPABILITY` / `PASS_PARTIAL_CAD_ONLY`。

consumer 的 empty Geometry cell、Edit、direct `.py RunScript`、post-RunScript probe、Exit 和
post-Exit probe 均返回。source-editor `SendCommand` 按实验设计为 `SKIPPED_BY_EXPERIMENT`；这不等于
它在本轮执行后失败，也不意味着 journal 后段不存在 Mechanical `model_container.SendCommand`。

固定 34-byte entry sentinel 在 post-RunScript、post-Exit、failure-pre-cleanup 和
failure-post-cleanup 四个检查点均未被观测；build report 同样 absent，两个 probe-error 列表均为空。
connected build contract 到达 `CALLED` 后，由 runner 以
`FAIL_RUNSCRIPT_RETURNED_ENTRY_AND_BUILD_ABSENT` fail closed。精确分类为：

```text
RUNSCRIPT_RETURNED_ENTRY_ABSENT
```

因此最强结论只有：direct `RunScript` 调用已到达并返回，但本轮未观测到 child entry 或 build 输出。
不能写成几何 build 已执行后失败、`.py` 不受支持、connected transfer 已失败或已通过。share、
`GetGeometryFileAndSaveData`、Refresh、Mechanical inspection、mesh 和 project save 全部
`NOT_REACHED`。

本轮 suite JSON 与两个 job 的全部 artifact-manifest 条目已逐文件复算：producer 20/20、consumer
19/19 的大小和 SHA-256 全匹配。Git 外 raw ZIP 保存 22 个 payload 和内部 `SHA256SUMS.csv`，大小
87014 bytes，SHA-256 `62b058ef4125704ef4d74624d23b5cc0093315ab29bc613cd0e55cf5d92b7a96`；
许可和随机临时文件未收入 ZIP。

run 完成后没有留下即时的外层进程观察。归档时的延迟检查在
`2026-07-15T05:21:32.3964021+00:00` 观察到相关 ANSYS 进程数为 0，但该记录不能倒推 suite 结束瞬间的
cleanup 状态。

同一 host/session 没有另跑一个“保证写出 entry/build”的 runtime positive control；该项为 `NOT_RUN`。
已有静态可达状态测试只验证判定器能接受/拒绝合成状态，不能替代 ANSYS runtime positive control。
因此本轮 absence 只按检查点事实报告，不把它升级为 loader、权限、session 或 child 行为的根因判断。

当前 connected external-geometry route 冻结为：

```text
CONNECTED_ROUTE_STATUS=DEFERRED_CURRENT_HOST_ROUTE
EXTERNAL_NATIVE_ATTACH=NOT_PROVEN
NATIVE_PARAMETERIZATION=NOT_PROVEN
NATIVE_NAMED_SELECTION_TRANSFER=NOT_PROVEN
P1_CAD_TOOLCHAIN_READINESS=BLOCKED
P1_STAGE_GATE=NOT_RUN
P1_P6_GATES=NOT_RUN
```

48 小时冲刺内不再追加 marker-only 或新的 connected 探针。下一工程路线是签名 SpaceClaim 脚本
建模后，以 hash-bound STEP + semantic sidecar 在 solver 侧重建语义；该路线仍不能冒充 native
Named Selection transfer。
