# AJM005 T0 签名重试：通过证据解释

## 判定

- process terminal state：四个 job 均为 `PROCESS_EXITED_0`，退出码 0。
- control status：四个固定 profile 均为 `PASS_CONTROL`，suite 为 `PASS_CONTROL_SET`。
- engineering capability：仍为 `NOT_RUN`；这轮没有执行 005 T1 工程小模型。
- visibility：`NOT_USER_OBSERVED`。
- Gate effect：P0 保持 PASS；P1--P6 全部 `NOT_RUN`。

## 这轮真正证明了什么

在 clean、已签名、与 `origin/main` 同步的 commit
`6265043003dfb44b2b694ef3e91cfd84d7cc832b` 上，固定 MCP 可以串行控制 SpaceClaim、
Workbench、Mechanical 和 Fluent，读取每个批准脚本的精确 Git blob，得到声明报告和原生
小产物，并在结束后把自动化相关进程数降为 0。Workbench 使用内部模板键，PyFluent 使用类型
化版本对象和有界退出等待，复测不再出现首轮故障。

## 这轮不能证明什么

- SpaceClaim 方块不证明参数化腔体、流体负体积、连通或 Named Selections；`.scdoc` 仍未形成。
- Workbench 模板存在并保存项目，不证明几何/Named Selection 传递。
- PyMechanical 连接与算术，不证明网格、静力、模态、谐响应或压电求解。
- PyFluent health/API 存在，不证明网格、20 次迭代、质量守恒、case/data 重开、并行或 CHT。
- 因而不能写 `PASS_005_CAPABILITY`、`PASS_START_P1`，也不能把它当 AirJet 产品结果。

下一步是签名的 T1 能力探针；每项只能用实际小模型和原生产物关闭 005 对应字段。
