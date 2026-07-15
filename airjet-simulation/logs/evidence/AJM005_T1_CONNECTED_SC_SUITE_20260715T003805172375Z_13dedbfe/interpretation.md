# AJM-005 T1 connected SpaceClaim：Interactive=True 单参数仍不足

本轮严格保持 run #20 的 empty Geometry route、inline payload、SendCommand、后续 RunScript、literal
path、marker exact size/SHA、fixture、predecessor、timeout、cleanup、transfer/Mechanical assertions
和 Gate 不变；唯一有意运行变化是把
`Edit(Interactive=False, IsSpaceClaimGeometry=True)` 改为 literal `Interactive=True`。静态策略用 AST
锁定唯一 Edit、精确两个 True keyword 及 Edit→SendCommand→RunScript 的同一 `Try.body` 顺序。

producer 以 21.703735 秒 PASS。consumer 的 empty cell 和 `Edit(Interactive=True)` RETURNED；
`SendCommand` 再次只到 CALLED 就在 journal line 553 抛相同外部错误文本
`未将对象引用设置到对象的实例。`。post-Send probe、RunScript、正常 Exit、build contract、share、
Refresh、Mechanical、mesh 和 project 都未到达；failure cleanup Exit RETURNED。三个 artifact 在 failure
freeze 均 absent，分类仍是 `CHECKPOINT_NOT_REACHED`。consumer 总时长 255.783635 秒，但没有
SendCommand 单独 timer，不能把该时长直接当作 API 精确耗时。

与 run #20 比较时，两轮受审 outer journal 的唯一有意运行变化是 `Interactive` 布尔值；两轮可观测
失败签名相同，consumer 时长分别为 256.035317 和 255.783635 秒。producer native/report 与注入绝对
job path 的 child 字节随每次重新生成而变化，因此不能把整组输入称作全字节相同。可以关闭的只有：
“仅把 Interactive 参数改为 True 足以使当前 SendCommand checkpoint/marker 通过”这一窄命题。

Workbench recorded journal 把 literal True canonicalize 为默认写法
`geometry1.Edit(IsSpaceClaimGeometry=True)`，随后记录 SendCommand 与 cleanup Exit，没有 RunScript。
这证明 Workbench 接受并记录了 True 默认模式，不证明 SSH/MCP 条件下建立了用户可见的 interactive
desktop/session；visibility 仍是 `NOT_USER_OBSERVED`。也不能声称两次空引用具有同一内部根因、
inline Python 内容执行失败、RunScript loader 失败，或所有 session 因素已经排除。

下一最小实验保持 `Interactive=True`，让 `.py` RunScript 成为 Edit 后第一个且唯一 scripting action，
完全移除/绕过 SendCommand 和 inline marker，避免前置异常遮蔽 file channel。新分类不应继续套用
inline/file 四态，而应至少区分 call exception、returned+entry exact、returned+entry absent、delayed/
uncertain、entry exact+build missing 和 build contract pass/fail。即使 entry exact，也只证明 child 进入，
还不能宣布 build/transfer/P1 PASS。

Git 外 raw evidence ZIP 为 85780 bytes，包含 22 个 payload 与内部 `SHA256SUMS.csv`，SHA-256
`7068b5d2b81350be65511b0582ac0101fc03d2aec6824df09b0500d487eb3bed`；同目录 pointer 锁定其路径、
大小和哈希。Git 只保留脱敏 summary、interpretation、pointer 与进程观察 JSON。

suite 仍为 `FAIL_CONNECTED_SPACECLAIM_TRANSFER_DIAGNOSTIC`，P1 readiness BLOCKED，P1--P6
`NOT_RUN`，可见性为 `NOT_USER_OBSERVED`。本轮仍只是 disposable tool model 诊断，不是 AirJet 产品
CAD、MEMS、结构、CFD 或 CHT 结果。
