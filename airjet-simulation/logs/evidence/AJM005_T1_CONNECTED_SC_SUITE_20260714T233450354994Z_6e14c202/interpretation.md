# AJM-005 T1 connected SpaceClaim：literal-path early-sentinel 复测

本轮只增强 connected child 的可观测性，不改变 empty Geometry、Edit、RunScript、Exit、fixture 几何、
predecessor report-only control、Mechanical 验收或 Gate 边界。child 的 job/report/sentinel 路径由
Workbench 外层以绝对路径注入；entry sentinel 在任何 Python/.NET import 和任何 SpaceClaim API 前
写入。因此它不再依赖 child 中的 `AIRJET_JOB_DIR` 才能留下“已经进入”的证据。

producer 以 20.364381 秒 PASS。connected Workbench job 记录 empty cell、Edit、RunScript、
post-RunScript probe、Exit 和 post-Exit probe 均 RETURNED。三个观测点属于同一次 job，而不是三次
复现：post-RunScript 为 `1784072246.0402832`，post-Exit 为 `1784072246.042282`，failure probe 与
post-Exit 相同。Exit 前后约 2 ms；三个点均没有 entry sentinel、build report 或 probe error，且
Workbench message snapshot 为空。

这足以关闭“child 中 `AIRJET_JOB_DIR` 缺失/错误只是把报告写到错误位置”作为第二轮的充分解释。
它不能关闭更宽泛的启动环境、broker、editor session 或文件访问问题。更重要的是，它仍没有证明
fixture 几何失败：child 的第一条无 import 文件写入都没有被观测到，share、Refresh 和 Mechanical
从未到达。

v261 官方 Workbench guide 明确写明 Geometry `RunScript` 对 SpaceClaim 接受 `.py` 与 `.scscript`；
SpaceClaim API XML 也明确支持两者并给出 `.py` 示例。因此不能声称 `.py` 是非法输入。官方资料没有
证明“把相同 Python 字节只改 suffix”就构成合法且等价的 `.scscript` 序列化；这种试验即使为负，也
不能单独关闭 extension dispatch。下一项更清晰的对照是在同一 opened editor 先用官方
`SendCommand(Language="Python")` 写独立 absolute sentinel，再保留现有 `.py` RunScript，直接区分
inline scripting channel 与 file-based loader。`.scscript` 只在先获得合法格式/等价性证据后再测。

suite 仍为 `FAIL_CONNECTED_SPACECLAIM_TRANSFER_DIAGNOSTIC`，P1 readiness BLOCKED，P1--P6
`NOT_RUN`，可见性为 `NOT_USER_OBSERVED`。本轮不能写 connected transfer、external `.scdocx`
attach、native Named Selection transfer、native parameterization 或完整产品 CAD 的通过/失败。
