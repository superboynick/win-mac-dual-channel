# V02 native `.scdocx` topology observer：972 个共享单面 membership 已观测

签名 tip `0fa89686820c737f7dc98ce94dea27252e4d8b86` 下，固定 runner 在同一 MCP
进程重新生成完整 V02 preliminary producer，再把四件 hash-bound predecessor 产物交给
Workbench/Mechanical native observer。producer 与 observer 均 `PROCESS_EXITED_0`；runner 为
`PASS_PRELIMINARY_NATIVE_TOPOLOGY_OBSERVER`，八项 observer assertions 全 true。

Mechanical 实际枚举两个 body：downstream 为 body 316/978 faces，upstream 为 body 1950/2044
faces。两侧各有 972 个与期望 XY 完整对应的孔接口候选；972 对均引用同一个 actual face ID，
且 membership 同时包含两个 body。精确分类是
`972_SHARED_SINGLE_FACE / SHARED_ID_MEMBERSHIP_CONFIRMED`。这与 STEP 路线只保留下游 imprint、
丢失上游孔几何的结果不同。

native staging 的 source/copy/final SHA256 均为
`5a0e0cc48c01d7989a3436c3079ea15b7d547fb234797002e900973b703f3887`；没有调用 Edit，冻结
predecessor 最终复核不变。Mechanical inventory 和 Workbench project 均已保存并有独立哈希。

本轮没有生成网格，因此不能声称 shared nodes、conformal mesh、流体连通求解或数值稳定性。
runner 也没有发出独立 `route_assessment` 字段，所以证据只支持把 native 路线列为“下一次无物理
mesh 诊断候选”，不能直接写成 mesh-ready 或正式 006/P1 PASS。`formal_006_completion=false`，
P1--P6 均保持 `NOT_RUN`。
