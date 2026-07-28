# 控制权与发布者矩阵

> 权威决策：[ADR-0001](adr/0001-dds-only-control-authority.md)  
> 当前结论：规则已冻结，但源码尚未实现 owner/lease；production 仍禁用。

## 1. PX4 输入白名单

| PX4 输入 | 唯一允许节点 | 条件 | 额外 publisher 处理 |
|---|---|---|---|
| `/fmu/in/trajectory_setpoint` | `/offboard_control_node` | SITL/bench/production 对应门禁通过 | fail closed |
| `/fmu/in/offboard_control_mode` | `/offboard_control_node` | 同上 | fail closed |
| `/fmu/in/vehicle_command` | `/offboard_control_node` | 同上；ACK/状态门待 P0-05 | fail closed |
| `/fmu/in/vehicle_visual_odometry` | `/vision_to_dds_node` | 单视觉 profile；坐标/时间/健康已验证 | fail closed |
| `/fmu/in/landing_target_pose` | `/vision_to_dds_node` | 仅显式精降 profile | fail closed |

`Micro XRCE-DDS Agent` 是 transport bridge，不是 ROS 侧控制决策 owner；同一 profile 只允许一个与目标 PX4 对应的 Agent。

### Firmware topic 可用性

- PX4 v1.16.2 默认 `dds_topics.yaml` 不导出 `/fmu/out/rc_channels`。Offboard
  保留该安全互锁，因此控制 profile 必须使用经过锁定和验证的定制 firmware。
- PX4 v1.16.2 的 `VehicleStatus.msg` 为 `MESSAGE_VERSION=1`，实机导出
  `/fmu/out/vehicle_status_v1`。Offboard 已通过 PR #2 合并集中常量修复并通过
  9 项 gtest；该修复没有放宽任何运行门禁，`rc_channels` profile 完成前仍必须
  fail-closed。
- baseline 不要求 `/fmu/in/landing_target_pose`；`enable_precland=false` 时视觉节点
  不创建该 publisher。精降只能由独立 firmware/profile 显式启用。
- 2026-07-24 参数快照中的 `UXRCE_DDS_CFG=0` 与 TELEM2 状态已经过期。
  维护者调整后，`/dev/ttyTHS0:921600` 已成功建立 XRCE session；当前只批准
  显式授权的 `px4-read-only` 验证，不代表 bench 或 production 获批。

## 2. 上层命令白名单

| 内部话题 | 消费者 | 每个 profile 允许的发布者 |
|---|---|---|
| `/offboard/cmd` | `/offboard_control_node` | 一个 mission owner |
| `/offboard/cmd_mode` | `/offboard_control_node` | 与 `/offboard/cmd` 相同 owner |
| `/offboard/takeoff_land` | `/offboard_control_node` | 与 `/offboard/cmd` 相同 owner |
| `/offboard/trigger` | mission owner | 仅 `/offboard_control_node` 发布 |

允许的 mission owner 是互斥集合：

```text
offboard_demo_node
XOR animal_testing_node
XOR future_control_authority_node
```

正式 production 只允许未来 `control_authority_node`；demo/animal 仅用于隔离 SITL。

## 3. 反馈与 mock

| 反馈 | 权威来源 | 非权威来源 |
|---|---|---|
| `/fmu/out/vehicle_odometry` | PX4 → Agent | bag/mock，除非隔离测试 |
| `/fmu/out/vehicle_status_v1` | PX4 → Agent | 任意脚本 |
| `/fmu/out/rc_channels` | PX4 → Agent | `mock_rc_control.py` |
| `/fmu/out/battery_status` | PX4 → Agent | 任意脚本 |
| `/fmu/out/vehicle_land_detected` | PX4 → Agent | 任意脚本 |

隔离测试必须使用独立 ROS domain 或显式测试 namespace，不能与真实 Agent 同图。

## 4. 禁止发布者

以下组件不得出现在 DDS production graph：

- `px4_bringup` 旧入口；
- `mock_rc_control.py`；
- `offboard_demo_node`；
- `animal_testing_node`；
- 多个 `offboard_control_node`；
- 多个 `vision_to_dds_node`；
- `src/communication` 对 `/fmu/*` 或 `/offboard/*` 的任何发布。

## 5. Namespace 契约

当前单机基线：

| 项目 | 值 |
|---|---|
| ROS namespace | `/` |
| PX4 输入 | `/fmu/in/*` |
| PX4 输出 | `/fmu/out/*` |
| 内部命令 | `/offboard/*` |
| Offboard 节点名 | `/offboard_control_node` |
| 视觉节点名 | `/vision_to_dds_node` |

不批准 `/drone1`、`/drone2`、`/drone3` 等 swarm namespace。未来多机必须另立 ADR。

## 6. Profile 矩阵

| 组件 | offline | sensor-isolated | px4-read-only | sitl-dds | bench-dds | production-dds |
|---|---:|---:|---:|---:|---:|---:|
| PX4/SITL | 否 | 否 | 实机只读 | SITL | 实机隔离 | 实机 |
| Agent | 否 | 否 | 1 | 1 | 1 | 1 |
| `offboard_control_node` | 否 | 否 | 否 | 最多 1 | P0-05 后 1 | 1 |
| mission owner | 否 | 否 | 否 | 最多 1 | 默认无 | 仅 arbiter |
| `vision_to_dds_node` | 否 | 隔离输出 | 否 | 最多 1 | 逐门放行 | 1 |
| 旧 bringup | 否 | 否 | 否 | 否 | 否 | 否 |
| mock feedback | 否 | 独立 domain | 否 | 测试专用 | 否 | 否 |
| arm/mode/setpoint | 否 | 否 | 否 | SITL 门禁 | 默认禁止 | 安全门通过后 |

`px4-read-only` transport 已在显式授权下验证通过。`bench-dds` 和
`production-dds` 仍受定制 `rc_channels` firmware、参数/domain/回滚证据和控制
安全门阻塞。表中的 “1” 表示通过相应门禁后的最大允许实例数，不表示默认获准启动；
本地 topic 契约测试通过也不构成启动授权。

## 7. 后续静态与运行验证

2026-07-25 已在 `px4-read-only` profile 执行输出 discovery 和以下只读检查：

```bash
ros2 topic list -t
ros2 topic info -v /fmu/out/vehicle_status_v1
ros2 topic info -v /fmu/out/battery_status
ros2 topic info -v /fmu/out/rc_channels
```

输入与控制权检查只允许在对应隔离 profile 已实现后使用：

```bash
ros2 node list
ros2 topic info -v /fmu/in/trajectory_setpoint
ros2 topic info -v /fmu/in/offboard_control_mode
ros2 topic info -v /fmu/in/vehicle_command
ros2 topic info -v /fmu/in/vehicle_visual_odometry
ros2 topic info -v /offboard/cmd
ros2 topic info -v /offboard/cmd_mode
ros2 topic info -v /offboard/takeoff_land
```

验收断言：

1. 三个控制输入各有且仅有一个 ROS publisher，均为 `/offboard_control_node`。
2. 视觉输入最多一个 publisher，且为 `/vision_to_dds_node`。
3. 三个内部命令话题来自同一个 mission owner。
4. production graph 不包含旧 bringup、demo、animal、mock 或 swarm node。
5. owner 消失、重复或重连时进入安全状态，不沿用陈旧命令。
