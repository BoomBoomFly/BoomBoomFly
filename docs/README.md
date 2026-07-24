# BoomBoomFly 文档

> 更新时间：2026-07-24T23:23:12+08:00
> 状态：P0-03 software published for review / hardware blocked / production disabled

## 权威文档

- [窗口交接](handoff.md)：当前工作区、实机 PX4、验证结果、阻塞项和下一步。
- [控制权矩阵](CONTROL_AUTHORITY_MATRIX.md)：唯一 writer、topic 与 profile 约束。
- [ADR-0001](adr/0001-dds-only-control-authority.md)：DDS-only 控制权决策。
- [Offboard / px4_msgs 兼容性证据](evidence/OFFBOARD_PX4_MSGS_COMPAT_20260724.md)：
  exact checkout、15 项核验、构建/测试和 topic 决策。
- Offboard 修复提交 `0c41de3e` 已推送，草稿 PR
  [BoomBoomFly/offboard_cpp#1](https://github.com/BoomBoomFly/offboard_cpp/pull/1) 待合并。
- [PX4 参数快照](evidence/PX4_PARAMS_20260724T203458+0800.json)：实机 972/972
  参数的原始只读采集结果。

## 清理结果

- 已删除由 handoff 取代的 8 份旧状态报告；不得从旧路径恢复过期结论。
- 已删除可再生的 `build/`、`install/`、`log/`；需要时重新执行 colcon。
- 保留 ADR、控制权矩阵、handoff 和两份证据，它们用途不同，不是重复文件。

状态变化只更新 `handoff.md`；架构决策更新 ADR/矩阵；原始或可复现实验结果放入
`evidence/`。文档不得把构建成功表述为已获准连接或控制实机。
