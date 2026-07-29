# 地面站数据契约（工位 4）

本阶段只定义通信与状态数据，不实现完整地面站 UI。机器可校验的权威契约位于
`config/profiles/dds_integration_contract.yaml`。

| 话题 | 类型 | 生产者 | 含义 |
|---|---|---|---|
| `/mission/start` | `std_msgs/msg/Bool` | `mission_bridge` | 已通过协议、CRC、session 和去重检查的 START 事件；`true` 表示启动 |
| `/mission/id` | `std_msgs/msg/UInt32` | `mission_bridge` | START 帧携带的任务编号，不再复用启动触发话题 |
| `/uav/mission_state` | `std_msgs/msg/String` | `flight_sequence_node` | 无人机任务状态机当前状态，仅在状态变化时发布 |
| `/car/link_state` | `std_msgs/msg/String` | `mission_bridge` | 车端链路、session、心跳、阶段与统计快照 |
| `/mission/fault` | `std_msgs/msg/String` | `mission_bridge` | 串口丢失、心跳超时、任务中止等事件型故障 |

`/uav/mission_state` 和 `/car/link_state` 分离，避免无人机任务状态与车端通信状态互相覆盖。
`/mission/fault` 只承载事件，不作为周期状态快照。

桥接串口帧仍使用：

`0x0F 0xF0 LEN DATA CRC16_LO CRC16_HI 0xFF`

CRC 为 CRC16/MODBUS，覆盖帧头、长度和 DATA。DATA 的前三字节为
`MSG_TYPE | SESSION_ID | SEQ`。不同 session 的非 START 帧会被丢弃，同一
`(session, seq)` 在去重窗口内只处理一次；START 可显式切换 session 并清空去重窗口。
