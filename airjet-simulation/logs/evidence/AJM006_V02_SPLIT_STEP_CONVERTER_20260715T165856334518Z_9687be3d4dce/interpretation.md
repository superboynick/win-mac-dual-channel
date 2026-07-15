# V02 split STEP converter：独立下游 STEP 丢失 972 个界面印记

本次签名运行的 producer 正常生成完整 V02 初步整机两流体区。converter 从 hash-bound native
staging 分别导出 upstream/downstream STEP，两个文件均能回读为一个 closed/manifold body，因此
进程 exit 0；但工程断言按设计判为 FAIL。

关键观测不是“整个产品几何坏了”，而是零厚度共面 imprint 在独立 STEP 表示中不稳定：upstream
回读仍为 2044 faces，但最大包络分量漂移 0.014975 mm；downstream 的包络和体积保持，却从 978
faces 直接愈合为 6 faces，原先 972 个孔口界面印记消失。因此不能放宽 face-count Gate，也不能把
两个独立 STEP 拼接后声称接口已在同一 solver model 内连接。

本轮未启动 Workbench、Mechanical、mesh 或 physics，P1--P6 和 formal 006 继续 `NOT_RUN`。
下一条主路线是新的 V03 pilot：把零厚度 shared/imprinted interface 改成显式有限厚度孔喉，优先
Boolean 成一个连续 single-piece fluid body，再验证 STEP round-trip 和 PyFluent watertight import。
孔喉厚度先使用已登记的 C 类候选 0.10 mm（公开/工程候选范围 0.05--0.20 mm），不得写成产品实测。
