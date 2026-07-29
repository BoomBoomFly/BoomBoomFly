# 首次 0.5 m 悬停卡（未来操作，禁止本次执行）

状态：**NO-GO / NOT AUTHORIZED**。本卡只是未来现场核对单，不是 Arm、装桨或飞行授权。
只有 G0–G4 均有本机、当次、可校验的 PASS 证据后，才可重新出具 go/no-go；即便结论为 GO，
也必须停下来取得用户对“当次装桨、Arm、0.5 m 短时悬停”的明确批准。

## 必须全勾选的前置

- [ ] G0–G4 evidence 均为 PASS，无过期/替代/dirty SHA。
- [ ] 当次完整参数导出、运行固件、代码、外参、工具链和回滚产物 SHA-256 已复核。
- [ ] 真实 RC、物理 kill、arm enable、activation 边沿和 recovery 均完成拆桨验证。
- [ ] T265/EKF 正在融合已验证的位置分量，质量、innovation、reset 和断流恢复正常。
- [ ] 单 Agent、串口唯一、所有 `/fmu/in/*` writer 数量和身份符合清单，无 mock。
- [ ] 场地、净空、围护、观察员、硬断电、消防和电池状态满足现场风险评审。
- [ ] 用户已明确批准当次装桨、Arm 和 0.5 m 悬停。

## 保守任务包线

- 仅 `mission.task_id=3` / `VERTICAL_TEST`；禁止赛题配置和动态降落。
- 目标高度 0.5 m；上升不超过 0.3 m/s；悬停 3 s；下降不超过 0.2 m/s。
- XY 目标保持起飞点；不得使用未经当次参数审计的高速度上限。
- 最长任务时限必须在生产配置中生效；超时、任一 freshness、quality、authority 或 ACK 失败即
  进入已在 G4 证明的安全动作。
- 必须完成 PX4 Land、连续有效 landed 样本确认和 Disarm ACK，才能标记 COMPLETE。

现场任何一项未勾选、证据不一致或操作者有疑问，结论均为 NO-GO。Codex 不会在没有新授权时
发送 VehicleCommand、Arm、启动电机或指导继续飞行。

