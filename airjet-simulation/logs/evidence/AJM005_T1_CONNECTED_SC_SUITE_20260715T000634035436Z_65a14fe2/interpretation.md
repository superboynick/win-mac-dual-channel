# AJM-005 T1 connected SpaceClaim：inline control 在桥接调用处抛错

本轮在同一个 `Interactive=False` connected SpaceClaim editor 中，把固定字节的 inline sentinel
`SendCommand(Language="Python")` 放在现有 `.py` `RunScript` 前。两种 marker 使用同一 job root，
但有独立文件名和精确 size/SHA 合同；inline 必须在紧接 `SendCommand` 的检查点出现，延迟出现不能
冒充 PASS。journal 和 runner 还显式保留四态，避免把 `inline fail/file pass` 淹没在总体 capability
状态里。

producer 以 20.202426 秒 PASS。consumer 的 empty Geometry cell 与 `Edit` 都 RETURNED；第一个脚本
调用 `source_geometry.SendCommand(...)` 进入 `CALLED` 后直接抛出
`未将对象引用设置到对象的实例。`，没有到达 RETURNED 或 post-SendCommand probe。failure probe
中 inline sentinel、file-entry sentinel 和 build report 均不存在；cleanup `Exit` RETURNED，前驱
report 前后 size/SHA 不变。最准确的分类是 `CHECKPOINT_NOT_REACHED`，不是
`INLINE_FAIL_FILE_FAIL`，因为 `.py` `RunScript` 在本轮根本没有调用。

Workbench consumer 总时长为 256.035317 秒，但 journal 没有给 `SendCommand` 单独计时，因此不能
把全部 256 秒写成该 API 的精确耗时。replay journal 的相关 editor scripting 序列记录了 Edit、
SendCommand 和 cleanup Exit，没有记录 RunScript；这与 execution reach 一致。`GetMessages`、
stdout、stderr 都为空；这说明排障不能只等软件自己打印
错误，必须用 outer reach、traceback、artifact probe 和 replay journal 联合定位。

该结果不能证明 inline Python 的内容、encoding、marker 路径或写权限有错，因为异常可能发生在命令
交给 SpaceClaim interpreter 之前；也不能对 `.py`/`.scscript` loader 做本轮新判断。share、
GetGeometryFileAndSaveData、Refresh、Mechanical、mesh 和 project 全部未到达，所以不能写成
connected transfer、几何算法或网格失败。CoreEvents 再次出现 RSM/ProgramData 绝对路径 warning，
但本轮没有请求 RSM，日志也没有建立它到 SendCommand 空引用的调用链，仍只归档为环境噪声。

v261 官方 Workbench Geometry API 把 `Interactive` 定义为 interactive/batch，默认值为 true；官方
SpaceClaim 示例使用默认 interactive Edit。本机官方 SpaceClaim remote interface 说明
`RunScript(string,bool)` 的第二个参数是 `useAsMacro` 且 SpaceClaim 不需要它，未给出用该参数修复
SendCommand 的依据。下一项最小实验因此只把 `Edit(Interactive=False)` 改为
`Edit(Interactive=True)`，其他 inline payload、SendCommand、RunScript、路径、清理、超时和 Gate
合同保持不变：若 inline marker 精确出现，只能说 `Interactive` 参数变化与结果变化相伴并支持
mode/session 相关假设，不能直接证明内部 scripting bridge 根因；若仍同一空引用，只能关闭“仅改
这个参数即可修复”的窄命题，不能全局排除 batch/session 因素，下一步再做 interactive
RunScript-only。

原始 suite/MCP、两 job 的关键报告/输入/replay/CoreEvents、producer native/STEP 与前驱证据已装入
Git 外 `..._RAW_EVIDENCE.zip`，内部 `SHA256SUMS.csv` 覆盖 22 个 payload 文件；路径、85822-byte
size 和 SHA-256 `56dbc5c8fd867ac9b0130340cccae9687be3c2effaebbd5599f032cecd078bd0`
登记在同目录 `external-raw-evidence-pointer.json`。Git 只保留脱敏 summary、interpretation、pointer
和进程观察 JSON。

suite 仍为 `FAIL_CONNECTED_SPACECLAIM_TRANSFER_DIAGNOSTIC`，P1 readiness BLOCKED，P1--P6
`NOT_RUN`，可见性为 `NOT_USER_OBSERVED`。本轮只改进工具链诊断，不是 AirJet 产品 CAD、MEMS、
结构、CFD 或 CHT 结果。
