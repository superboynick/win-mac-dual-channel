# V02 topology observer 修正版：STEP 路线发生单侧接口几何丢失

签名 commit `9699df565d5b93bfe8bf8354834af7fc5f79624c` 在一个 MCP 会话内重新生产 hash-bound V02，并由 observer 导入 Workbench/Mechanical。producer 与 observer 均 exit 0；八项 observer assertions 全 true，最终状态为 `PASS_PRELIMINARY_TOPOLOGY_OBSERVER`。这里的 PASS 表示“观测过程闭合”，不表示导入拓扑可用于求解。

Mechanical 保留两个 body 和名称。按持久化名称绑定后，upstream 为 body `4288`、100 faces；downstream 为 body `7231`、978 faces。downstream 在接口平面保留 972 个与期望 XY 一一对应的 0.25 mm imprint faces，另有一个大界面 face；upstream 对应的 972 个孔口面全部缺失。两个 body 之间没有重复 actual face ID、shared candidate 或 coincident opposite-normal pair。没有生成网格，因此不能声称 shared nodes 或 conformal mesh。

孔口识别使用 0.25 mm bounding-box spans、单边界环、平面类型和 XY/Z 容差；face area 只保留作诊断。原因是 SpaceClaim native、STEP reopen 与 Mechanical 三个几何内核对同一面给出的分解/面积并不稳定，而 bbox 和离散 XY 合同在本轮可复核。

结论是当前 STEP handoff 不能作为两区连通求解器拓扑的正式路线：它保留下游 972 个 imprint，却丢失上游孔喉/出口界面。下一步必须改用能在 solver 侧保留或重建两侧 972-interface 的 native/connected/re-authoring 路线；正式九变体 006 暂不启动。`formal_006_completion=false`，P1--P6 均为 `NOT_RUN`。
