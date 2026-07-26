# SITL 正常流程场景

> 规范版本：`1.0.0`
>
> 场景数：12
>
> 当前场景状态：全部 `BLOCKED`
>
> 验证边界：本目录只冻结机器可读验收契约；本轮没有运行 PX4 SITL、ROS 节点或硬件。

本文件是 `docs/verification/scenarios/normal/` 的人工可读索引。JSON 文件是
离线 validator 和未来正式 SITL runner 的输入，不是运行结果。合成 timeline 只能用于验证
解析器和断言器，不能满足 `px4_sitl` 的权威 source identity，也不能关闭 PX4 contract 门。

## 场景目录

| Scenario ID | 正常流程 | 初始状态 → 期望状态 | 主 deadline | 权威 source | 当前 blocker |
|---|---|---|---|---|---|
| `SITL-NORMAL-001` | 建立 DDS session 并匹配 profile identity | `BOOT` → `SESSION_READY` | `6s` | locked PX4 SITL / Agent identity | T00、T01、T08 |
| `SITL-NORMAL-002` | baseline topic/type/QoS/source/publisher 基数 discovery | `SESSION_READY` → `GRAPH_READY` | `3500ms` | locked PX4 SITL；批准的 ROS writer | T00、T01、T03、T08 |
| `SITL-NORMAL-003` | 接收 fresh、same-epoch `vehicle_status_v1` | `WAIT_INPUTS` → `STATUS_READY` | `1600ms` | PX4 SITL | T00、T01、T03、T08 |
| `SITL-NORMAL-004` | 接收 valid、fresh `battery_status` | `WAIT_INPUTS` → `BATTERY_READY` | `1600ms` | PX4 SITL | T00、T01、T05、T08、安全决策 |
| `SITL-NORMAL-005` | 接收 valid、fresh `vehicle_odometry` | `WAIT_INPUTS` → `ODOMETRY_READY` | `1600ms` | PX4 SITL | T00、T01、T03、T05、T08、安全决策 |
| `SITL-NORMAL-006` | 接收 fresh `vehicle_land_detected` | `WAIT_INPUTS` → `LAND_STATE_READY` | `1600ms` | PX4 SITL | T00、T01、T03、T05、T08、安全决策 |
| `SITL-NORMAL-007` | 接收 PX4-origin `rc_channels` | `WAIT_INPUTS` → `RC_READY` | `1600ms` | PX4 SITL；不接受 mock/replay | T00、T01、T02、T05、T08 |
| `SITL-NORMAL-008` | 合并 feedback、identity、owner、writer readiness | `WAIT_INPUTS` → `PRESTREAM` | `600ms` | PX4 SITL / approved owner / sole writer | T00–T05、T08、安全决策 |
| `SITL-NORMAL-009` | 连续不少于 `1s` 且不少于 20 个有效 PRESTREAM sample | `PRESTREAM` → `MODE_PENDING` | `1700ms` | sole Offboard writer | T01、T03、T04、T06、T08 |
| `SITL-NORMAL-010` | correlation 匹配的 VehicleCommand ACK `ACCEPTED` | `MODE_PENDING` → `MODE_PENDING_ACKED` | `1100ms` | PX4 SITL | T01、T03、T04、T06、T08 |
| `SITL-NORMAL-011` | ACK 后由 fresh、same-epoch VehicleStatus 确认 mode | `MODE_PENDING_ACKED` → `ACTIVE` | `700ms` | PX4 SITL | T01、T03–T06、T08、安全决策 |
| `SITL-NORMAL-012` | 正常退出、撤销 authority、清空缓存并确认零残留 | `SCENARIO_TERMINAL` → `CLEAN` | `6s` | approved orchestrator / recorder | T00、T01、T04、T06、T08 |

## 冻结的断言结构

每个 JSON 场景都包含 schema 要求的全部顶层字段，并使用以下统一表达：

- `profile` 固定 `environment=SITL`、`transport=UDP`、隔离 ROS domain 和根 namespace；
- `source_identity.bindings` 将每个 endpoint 的 `required_source` 绑定到锁定的
  process artifact、批准 executable 或 lease identity，且 `mock=false`；
- `assertions.endpoint_contracts` 冻结 exact topic、message type、QoS、
  publisher count 和 required source；
- `expected_events` 和 `forbidden_events` 通过 event ID、correlation ID、
  bounded earliest/deadline、count 和显式相对顺序表达时序；
- `assertions.state_transitions` 通过事件 ID 驱动状态迁移，不依赖日志固定行号；
- `timeouts` 都带单位并给出 fail-closed 的 `on_expiry`；
- `cleanup` 有 bounded deadline、动作列表和期望消失的 participant；
- `evidence.acceptance_level=FORMAL_SITL` 表示该场景最终需要正式运行证据，
  不是表示本轮已经执行。

## Topic contract 范围

正常场景覆盖：

- PX4 outputs：
  `/fmu/out/vehicle_status_v1` (`px4_msgs/msg/VehicleStatus`)、
  `/fmu/out/battery_status` (`px4_msgs/msg/BatteryStatus`)、
  `/fmu/out/vehicle_odometry` (`px4_msgs/msg/VehicleOdometry`)、
  `/fmu/out/vehicle_land_detected` (`px4_msgs/msg/VehicleLandDetected`)、
  `/fmu/out/rc_channels` (`px4_msgs/msg/RcChannels`) 和
  `/fmu/out/vehicle_command_ack` (`px4_msgs/msg/VehicleCommandAck`)；
- PX4 inputs：
  `/fmu/in/trajectory_setpoint` (`px4_msgs/msg/TrajectorySetpoint`)、
  `/fmu/in/offboard_control_mode` (`px4_msgs/msg/OffboardControlMode`)、
  `/fmu/in/vehicle_command` (`px4_msgs/msg/VehicleCommand`) 和 baseline 禁用的
  `/fmu/in/vehicle_visual_odometry` (`px4_msgs/msg/VehicleOdometry`)。

当前 Offboard PX4 endpoint 契约使用 `keep_last(1)`、best-effort、volatile。
视觉 publisher 的当前代码路径使用深度 10 的默认 QoS；场景将其 baseline publisher count
冻结为 0。端到端 QoS 仍需要正式运行验证，discovery 本身不证明 PX4 已消费输入。

## Blocker 解释

- T00：提供 workspace、PX4 source/submodule/toolchain 和 binary identity。
- T01：提供 DDS-only package、launch、transport 和隔离 graph 边界。
- T02：提供只增加 `rc_channels` 的 PX4 firmware endpoint manifest 与可追溯 artifact。
- T03：提供 ACK correlation、freshness、epoch、WAIT_INPUTS/PRESTREAM/MODE_PENDING 接口。
- T04：提供 owner/lease 和持续 graph guard。
- T05：提供稳定 fault code、validity policy 和经安全评审的恢复策略。
- T06：提供 required CI 和正式 runner 的持续门禁。
- T08：提供 evidence、release 和 rollback schema。
- `SAFETY_DECISION_REQUIRED`：最终安全动作尚未评审；本规范不自行选择 Land、
  Position 或停止输出。

缺少前置不会删除场景，也不能以 skip 形成通过结果。T02 未完成时
`SITL-NORMAL-007` 保持 `BLOCKED`；T03 未完成时 PRESTREAM、ACK 和 fresh status
相关场景保持 `BLOCKED`。

## 离线校验

单个文件可由离线 validator 读取：

```bash
python3 tools/sitl_acceptance/validate_scenario.py \
  --scenario docs/verification/scenarios/normal/SITL-NORMAL-001.json
```

离线 schema 通过只说明 JSON 结构、边界字段和内部引用合格。它不启动 ROS、不连接
ROS graph、不运行 PX4，也不产生正式 SITL 通过结论。
