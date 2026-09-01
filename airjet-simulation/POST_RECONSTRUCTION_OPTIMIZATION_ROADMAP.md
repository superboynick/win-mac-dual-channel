# AirJet Mini 重建后优化落地路线

版本：O0.1
日期：2026-09-01
状态：`PLANNED_LOCKED_UNTIL_P6_PASS`

## 1. 启动边界

本路线只在 AirJet Mini Gen1 的 P1--P6 正式 Gate 全部通过后启动。当前 P1--P6
仍未通过，所以现在只允许冻结接口、变量候选、目标、约束和产物格式，不允许运行 DOE、
代理模型或优化求解。P7 Mini G2 迁移不是首轮筛选的硬前置，但在声称跨代稳健性前必须完成。

优化对象仍是完整产品。单 cell、周期模型和降阶模型只用于筛选或构造传递关系；每个入选
设计最终都必须回到无对称简化的整机 P4/P5 模型复算。不得为了 Student 限额删 cell、删孔、
截断进排气路径，或把单喷嘴通用 CHT 当成 AirJet 整机优化结果。

## 2. 重建与设计的隔离

- P6 通过时冻结 `AJM-P6-BASELINE-vNNN`：Git commit、参数账本、校准后验、网格/时间步、
  P4/P5 原生文件哈希和验证集结果必须一起锁定。
- D 类产品事实保持不可调；P/I/C/U 参数保留原证据等级。优化变量另建 design lineage，
  不能把优化后的数值回写成“AirJet Mini 真实参数”。
- 校准变量先用于识别基线，设计变量再相对基线改变。禁止在同一黑箱循环中一边拟合产品、
  一边宣称找到更优设计。
- turbulence、接触模型、声学传播等 model-form 分支作为不确定性分支，不作为优化器可随意
  选择的“获利变量”。

机器可读候选见 `parameters/post_reconstruction_optimization_registry.csv`。P6 后必须从实际
后验和制造约束重新生成 v1，不得直接把当前候选范围当成量产范围。

## 3. 目标与硬约束

首轮采用四目标最小化，并同时报告原始物理量与相对基线变化：

1. `f1 = R_th`，同时报告 `Tmax`，避免仅靠改变热源定义获得虚假降温；
2. `f2 = sigma_T`，约束热点和温度均匀性；
3. `f3 = P_airjet`，需要时附加流体功 `Delta_p * V_dot` 作为诊断；
4. `f4 = pressure_ripple_rms`，仅作为噪声代理。只有补齐系统安装、50 cm 传播和 A 计权后，
   21 dBA 才能成为数值约束。

硬约束：

- Gen1 外包络 `27.5 x 41.5 x 2.8 mm` 保持 D 类锁定；若研究系统级增厚，必须另开集成分支；
- 基准热账户保持 `Q_chip_net=4.25 W`、`P_airjet<=1.00 W`、`Q_total=5.25 W`，不得重复计热；
- 1750 Pa 只作为最大背压能力扫描目标；公开资料没有给出其对应流量，不能伪造成单点 P-Q 目标；
- 保持完整进气、所有建模 cell、孔板、冲击通道、歧管与真实出口的连通；
- 膜片不碰撞，结构频率/位移/总功耗、质量与能量守恒、CHT 能量误差 `<1%` 全部通过；
- CAD 无重叠、零厚度和封死腔体；候选可制造性、最小壁厚和特征尺寸在 O1 前冻结；
- 产品质量 11 g 作为系统质量目标；材料未知时报告质量区间，不用反向伪造材料。

## 4. 分阶段落地

### O0：基线解锁与合同冻结

输入是 P6 PASS、至少三个独立物理层参与校准、一个公开指标留出验证、主模型附近存在稳定
参数区。输出 `baseline-lock-v001.json`、objective YAML、设计变量 v1 和计算预算。任一输入缺失，
状态保持 `BLOCKED_BY_RECONSTRUCTION_GATE`。

### O1：物理筛选与可行域清理

先做单因素正负扰动与 Morris 筛选，逐项检查几何、结构、流体、热和功耗链。离散布局、相位、
材料与连续尺寸分开编码。任何违反硬约束的样本作为 infeasible 标签保留，不用裁剪或改阈值救活。
输出 active-variable list、无效域分类器和冻结的 DOE schema。

### O2：分层 DOE

- 低成本层：P2/P3 传递模型与整机 P4a/P5 降阶模型，用 LHS 覆盖 active variables；
- 高成本层：对 DOE 边界、交互强区和初始 Pareto 区补充整机求解；
- 样本数由 active dimension、交叉验证误差和可用算力自适应决定，不预先承诺一个虚假的固定数；
- 所有样本写入不可变 run matrix，包含 Git/输入/网格/求解器/产物 SHA 和失败原因。

### O3：代理模型与多目标搜索

连续变量优先使用高斯过程或经过交叉验证的响应面；混合离散变量可使用分支代理或树模型。
代理模型至少报告留一/折叠验证、NRMSE、最大误差和可行性分类错误。目标响应 NRMSE 高于 10%
或硬约束附近出现假可行点时，不运行正式 Pareto 搜索，先自适应补点。搜索采用 NSGA-II 或
多目标贝叶斯 EHVI，输出 Pareto 集，不输出单一“神奇最优值”。

### O4：整机高保真确认

从 Pareto 前沿选基线、膝点、最低温、最低功耗和最均匀五类代表设计；去重后逐一用 P4b/P5
整机模型复算，并重复关键网格/时间步检查。代理与真实求解差异必须落在预先登记的不确定度内，
否则回到 O2 补点和 O3 重训。

### O5：稳健优化

对 P6 后验、I 类图像误差、制造公差、TIM/材料和 model-form 分支做 Monte Carlo 或多保真传播。
硬约束采用至少 95% 满足概率；同时报告中位数、5--95% 区间和最坏可信情形。优先选择稳健膝点，
而不是名义工况下最激进的极值点。

### O6：工程交付

交付 baseline-versus-design 对照、Pareto 图、全产品场结果、守恒/独立性证据、制造敏感性、失败域、
参数 lineage 和局限性。设计编号使用 `AJM-O<阶段>-<族>-vNNN`，明确写成“公开证据约束模型上的
设计候选”，不称为 Frore 实际下一代结构或精确数字孪生。

## 5. 预定文件接口

P6 解锁后创建：

```text
airjet-simulation/optimization/
  baseline-lock-v001.json
  design-variable-registry-v001.csv
  objective-definition-v001.yaml
  run-matrix-v001.csv
  surrogate-validation-v001.json
  pareto-v001.csv
  robust-selection-v001.csv
airjet-simulation/automation/optimization/
  build_campaign.py
  validate_campaign.py
  fit_surrogate.py
  select_confirmation_cases.py
airjet-simulation/results_summary/
  optimization-report-v001.md
```

ANSYS 执行仍只能通过审计、hash-pinned profile；原生 CAD、mesh、case/data 和瞬态场留在 Git 外。
优化脚本不得直接修改 Git、证据等级或 D 类参数。

## 6. 首轮建议优先级

1. 在已校准 cell/布局不变时筛选 `H/D`、孔径/开孔率/板厚、排气歧管和相位图；
2. 再加入驱动频率/位移，但受 P2/P3 后验、碰撞和 1 W 总功耗约束；
3. 热扩散板与 TIM 作为系统集成分支，和 AirJet 本体几何 Pareto 分开报告；
4. cell 数/布局属于高成本离散 model family，只在连续变量路线稳定后比较；
5. G2 迁移用于检查结论是否跨代成立，不反向混入 Gen1 训练集。

当前执行入口仍是 AJM-009/C7；本路线不改变任何 P1--P6 状态。
