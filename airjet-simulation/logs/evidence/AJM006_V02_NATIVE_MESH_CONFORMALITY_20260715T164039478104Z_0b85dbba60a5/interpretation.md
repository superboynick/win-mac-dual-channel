# V02 native mesh diagnostic：attach 前置失败

本次签名运行没有到达 Mechanical inventory 或网格。producer 正常生成完整 V02 native，
但 Workbench 在 `Model.Refresh()` 附加 job-local、hash-equal staging `.scdocx` 时失败。
因此 `mesh_generation=NOT_REACHED`，不能写成“网格失败”或“共节点失败”。

至此同一 native observer 路线共有一轮 attach PASS、两轮 attach FAIL；三个 producer native
文件的 SHA 与大小均不同。该事实证明当前 native save→Workbench attach 路线在现有受审流程中
不可重复，但尚未证明具体是哪一种 native 内部序列化差异导致。observer #2 按 fail-closed 规则
未提交，split STEP 未自动运行，结束后相关进程数为 0。

下一步是单独签名并运行已冻结的 split-STEP fallback。它只改变 solver handoff 表示，不改变
12-cell/972-hole 整机、两流体区或参数；converter PASS 仍不等于同一 solver 模型内连接、网格、
正式 006 或 P1 PASS。
