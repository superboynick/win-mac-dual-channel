# V02 第二次实跑：native CAD 成立，STEP 容差未闭合

本轮真实建立了 12-cell/972-hole 两区整机 CAD；两个流体实体均为 single-piece、closed、manifold，4/1 入口出口、12/12 膜片面和 972/972 孔口两侧面全部命中，native 保存/重开和分组也通过。

唯一失败是 STEP 重导入的 upstream 包围盒最大漂移 `0.014975 mm` 超过原先通用 `0.005 mm` 阈值；最大体积差约 `0.003997 mm^3`。因此 runner fail closed。下一轮只把 STEP bbox 容差绑定为有实测依据的 `0.02 mm`，native 路径仍用 `0.005 mm`，并把容差和实际 delta 写入报告。

STEP 中 downstream face decomposition 从 native 的 978 面合并为 6 面；preliminary shape equivalence 不要求 STEP face count，但这意味着 shared/coincident interface 身份仍必须由后续 observer 独立判定，不能把本轮写成 semantic PASS。
