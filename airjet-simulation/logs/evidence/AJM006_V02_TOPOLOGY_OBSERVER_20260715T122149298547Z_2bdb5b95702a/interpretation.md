# V02 topology observer 首次观测：原始 inventory 有效，角色分类被修正

同一 MCP 会话在签名 commit `d984890b84e3bf168c24f4ff869d474ac07e9fa4` 依次完成 producer 与 observer，两个 job 均 exit 0，observer 的 Workbench import、Mechanical entity inventory 和 project save 均真实返回。该轮不是失败运行；它留下了首份真实 solver-side body/face inventory。

随后审计发现分类器把“较多 faces 的 body”当作 upstream。Mechanical 实际保留了 body name，而 body `7231` 的名称和 z 范围指向 downstream、body `4288` 指向 upstream；不同几何内核的 face 数变化使 face-count 角色绑定不稳定。因此本轮原始 inventory 与执行到达证据保留，但 role-specific 计数和无限定的 `MIXED_OR_OTHER` 解释被修正版 job `AJM006-V02-PRELIMINARY-2fb76257a827` 取代。

该缺陷没有修改原始产物，也没有产生 P1 证据。`formal_006_completion=false`，P1--P6 均为 `NOT_RUN`。
