# ADR-0001：DDS-only 控制权与视觉权威路径

- 状态：**Accepted**
- 决策日期：2026-07-23
- 所属任务：P0-02
- 决策范围：BoomBoomFly 的 PX4 command/setpoint、外部视觉和上层任务控制权
- 不包含：PX4 firmware/board/参数选择、Agent transport、控制代码安全修复和 launch 实现

## 背景

P0-01 已将旧飞控传输、旧 bringup 和旧 serial 从默认受管源码中移除，并把 `offboard_cpp:DDS`、`vision_to_dds:master` 纳入核心。

当前受管源码中：

- `offboard_control_node` 直接发布：
  - `fmu/in/trajectory_setpoint`
  - `fmu/in/offboard_control_mode`
  - `fmu/in/vehicle_command`
- `vision_to_dds_node` 发布：
  - `/fmu/in/vehicle_visual_odometry`
  - 可选 `/fmu/in/landing_target_pose`
- `offboard_demo_node` 与 `animal_testing_node` 都发布：
  - `offboard/cmd`
  - `offboard/cmd_mode`
  - `offboard/takeoff_land`
- `mock_rc_control.py` 可发布 `/fmu/out/rc_channels` 并修改 Offboard 参数。

源码当前没有 owner/lease、publisher 身份校验或图级排他门，因此仅从“包已存在”无法保证运行时单一控制权。

## 决策

### 1. 唯一 PX4 传输

生产候选只允许 PX4 uXRCE-DDS：

```text
ROS 2 ↔ Micro XRCE-DDS Agent ↔ PX4 uXRCE-DDS client
```

不保留备用飞控传输链；production、bench、SITL 和 read-only profile 均只使用 DDS。

### 2. 单机 namespace

当前基线只支持一个 PX4，使用根命名空间：

```text
/fmu/in/*
/fmu/out/*
/offboard/*
```

`offboard_swarm_control.launch.py` 生成 `/drone1/fmu/*` 等相对命名空间，但仓库没有对应多 Agent、PX4 namespace、domain、端口或车辆身份契约，因此不属于批准路径。

任何多机支持必须另立 ADR，明确：

- 每机 PX4 client key/namespace；
- 每机独立 Agent 或经过证明的共享 Agent 隔离；
- transport、domain、端口和 vehicle identity；
- 每机独立控制 owner 和视觉 owner；
- 跨机命令不可达性验证。

### 3. 唯一 PX4 控制写入者

`offboard_control_node` 是唯一允许发布以下话题的节点：

| 话题 | 消息 | 唯一 owner |
|---|---|---|
| `/fmu/in/trajectory_setpoint` | `px4_msgs/msg/TrajectorySetpoint` | `/offboard_control_node` |
| `/fmu/in/offboard_control_mode` | `px4_msgs/msg/OffboardControlMode` | `/offboard_control_node` |
| `/fmu/in/vehicle_command` | `px4_msgs/msg/VehicleCommand` | `/offboard_control_node` |

同一 ROS graph 中只允许一个 `/offboard_control_node`。任何直接写这三个话题的 mission、demo、脚本、通信节点或调试工具均违反本 ADR。

此决策不表示当前 `offboard_control_node` 已达到实机安全要求。它在 P0-05 完成前仍禁止进入 production。

### 4. 唯一外部视觉写入者

`vision_to_dds_node` 是唯一允许发布以下话题的节点：

| 话题 | 消息 | 唯一 owner |
|---|---|---|
| `/fmu/in/vehicle_visual_odometry` | `px4_msgs/msg/VehicleOdometry` | `/vision_to_dds_node` |
| `/fmu/in/landing_target_pose` | `px4_msgs/msg/LandingTargetPose` | `/vision_to_dds_node`，仅精降 profile |

约束：

- 默认 `enable_precland=false`。
- 不允许同时运行第二个 EKF 外部视觉注入节点。
- 在坐标、时间、质量、reset 和 freeze 检测完成前，视觉输出只能用于离线/SITL/隔离验证。
- 单设备相机检查时，应把 PX4 输出参数重映射到隔离话题，或不启动 `vision_to_dds_node`。

### 5. 唯一上层任务 owner

`offboard_control_node` 当前订阅：

- `/offboard/cmd`
- `/offboard/cmd_mode`
- `/offboard/takeoff_land`

任一运行 profile 同时只能选择一个上层任务 owner。候选包括：

- `offboard_demo_node`：仅 SITL/受控测试；
- `animal_testing_node`：仅 SITL/受控测试；
- 未来正式 mission/arbiter 节点。

`offboard_demo_node` 与 `animal_testing_node` 不得同时运行，也不得与未来 mission owner 同时发布上述话题。

由于当前消息没有 owner ID、lease、sequence 或 ACK，本 ADR 只能冻结规则，不能在运行时强制执行。production 的正式 owner 必须是 P0-05 实现的 control-authority/arbiter；在此之前 production profile 保持禁用。

### 6. PX4 反馈权威

`/fmu/out/*` 的权威来源只能是目标 PX4 经 Agent 转发的 DDS 数据。

`mock_rc_control.py` 仅允许在隔离的自动化测试 domain/namespace 中运行，且不得连接真实 Agent、PX4 或 production graph。它不能作为 bench 或实机遥控器替代。

### 7. communication 边界

`src/communication` 由安装脚本从独立仓库拉取，不存储在根 Git 树，也不属于
PX4 DDS 飞控控制链。它不得发布：

- `/fmu/in/*`
- `/fmu/out/*`
- `/offboard/cmd`
- `/offboard/cmd_mode`
- `/offboard/takeoff_land`

如未来确需向任务层提供 MCU 数据，只能通过另行定义的非飞控接口进入正式
arbiter，不得绕过 owner 或复用 PX4 DDS 输入话题。

## 运行 profile 决策

| Profile | 允许组件 | 控制/视觉权限 | 当前状态 |
|---|---|---|---|
| `offline-static` | 文件、manifest、静态 launch 检查 | 不运行 ROS/PX4 | 可立即使用 |
| `sensor-isolated` | 单一传感器驱动、TF/回放工具 | 不连接 `/fmu/in/*` | 待 P1-03 实现 |
| `px4-read-only` | 单 Agent + PX4 telemetry observer | 不启动 Offboard/视觉输入发布者 | 2026-07-25 专用 TELEM2 transport 已只读验证；后续仍需逐次授权 |
| `sitl-dds` | PX4 SITL、单 Agent、单 Offboard、可选单任务 owner/视觉 owner | 仅隔离 SITL | 当前无项目入口 |
| `bench-dds` | 拆桨/执行器隔离实机、单 Agent | 默认不 arm、不 set mode；逐门放行 | topic/firmware/P0-05 后 |
| `production-dds` | 单 Agent、单 Offboard、单 arbiter、单视觉 owner | 完整控制 | **禁用**，直到全部安全门通过 |

## 当前入口处置

| 入口 | 决策 |
|---|---|
| `px4_bringup/start_all_2025TI.launch.py` | 已退出 manifest；禁止 |
| `px4_bringup/include/px4_fly.launch.py` | 已退出 manifest；禁止 |
| `offboard_swarm_control.launch.py` | 多机契约缺失；禁止 |
| `animal_testing.launch.py` | 默认自动启动任务 owner；只允许未来 SITL profile 显式封装 |
| `offboard_demo.launch.py` | 只允许未来 SITL profile；`auto_start_demo=false` 不能替代控制安全门 |
| `offboard_control.launch.py` | 直接启动 PX4 writer；P0-05 前禁止实机 |
| `mock_rc_control.py` | 仅隔离自动测试 |

当前没有批准用于真实硬件的项目级 launch。

## 强制实施要求

后续实现必须提供：

1. 静态 launch 检查：production graph 中恰好一个控制 writer、一个视觉 writer、一个 Agent、一个 mission owner。
2. 启动前 graph guard：发现额外 publisher、旧 bringup 或 mock feedback 时拒绝进入控制。
3. owner/lease/sequence/timeout/ACK 协议：所有上层命令经 arbiter。
4. Offboard 与 PX4 状态一致性：命令 ACK、mode、arming、preflight、failsafe 和 telemetry freshness。
5. profile allowlist：默认入口不打开真实设备或控制。
6. 测试：重复 owner、owner 消失、旧 owner 重连、视觉双源、mock 混入和 namespace 冲突均必须 fail closed。

## 后果

正面后果：

- 并行飞控传输造成的控制竞争从目标架构中消除。
- PX4 command、setpoint、视觉和上层任务均有唯一 owner。
- communication 与飞控控制边界明确。
- 可以据此实现自动化 graph/launch 门禁。

代价与残余风险：

- 当前源码尚未实现 owner/lease，ADR 不是运行时安全机制。
- 本地旧源码仍可能被人工误启动，需 P1-03 的 profile 隔离和后续安全清理。
- 单机根 namespace 暂不支持 swarm。
- 默认 PX4 v1.16.2 DDS topic 集缺少 RC 安全互锁所需的 `rc_channels`。
- PX4 v1.16.2 实机导出 `/fmu/out/vehicle_status_v1`；Offboard PR #2 已合并修复
  订阅并通过 9 项 gtest，但这不替代 firmware、SITL 或运行安全门。
- production 在 transport 参数/domain/回滚证据、定制 `rc_channels` firmware、
  P0-05、P1-03、P1-04 和 P1-09 完成前保持禁用。

## 证据

- [`workspace.lock.repos`](../../workspace.lock.repos)
- [控制权与发布者矩阵](../CONTROL_AUTHORITY_MATRIX.md)
- [控制权运行契约](../architecture/CONTROL_AUTHORITY.md)
- [视觉里程计契约](../architecture/VISION_ODOMETRY_CONTRACT.md)

## 验收

P0-02 的“决策冻结”在以下条件满足时完成：

- 维护目标明确为 DDS-only；
- PX4 控制、视觉、反馈和上层任务 owner 均唯一；
- namespace 和多机边界明确；
- 禁止入口和 profile 门禁明确；
- 后续实施任务可从本 ADR 直接生成验收测试。

运行时强制执行不属于本 ADR 的完成条件，分别由 P1-03、P1-04 和 P0-05 实现。
