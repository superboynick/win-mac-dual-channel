# AJM-005 T1 CAD transfer suite：第十次 STEP 诊断

第十次真实运行使用签名 commit `6f828feaeaee3f61278a0d3198156592529cc7a7`。SpaceClaim 七项
partial CAD 能力继续通过。Workbench 改用同一 predecessor 已验证并冻结的 STEP，share、save-data、
Model Refresh、Mechanical inspection 与 project save 全部返回。

Mechanical 得到一个 `spaceclaim_cad_t1|AJM005_T1_FLUID` body，并用 1 mm element size 生成
1063 nodes / 513 elements；项目和 inspection 文件均落盘并有 SHA。`INLET/OUTLET/WALLS` 的对象数
和实体数全部为 0，符合 STEP 不承诺保留 SpaceClaim groups 的预期。

该脚本被设计为永不关闭 native transfer Gate：canonical assertions 除 predecessor identity 外都
保持 false，观测只进入 `diagnostic_result`，且 native Named Selection transfer claim 固定 false。
所以 suite 仍为 FAIL，但已经把问题隔离为 native attach/semantic transfer，而不是通用
Workbench→Mechanical→mesh 管线不可用。

下一步建立独立的“STEP + 几何指纹重建 Named Selections”能力路线。它可以支持后续可删除小模型和
整机仿真的工程推进，但必须叫 semantic reconstruction/equivalent route，不能称 native transfer；
原生 driving parameter 与 P1 readiness 仍保持 BLOCKED，P1–P6 NOT_RUN。
