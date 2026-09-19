# PX4 SITL 起飞—悬停—降落验证

记录日期：2026-09-19。测试对象为本机 PX4/Gazebo SITL；未连接实机。正常流程通过，另完成任务节点停止后的控制层降落交接验证。

## 实现职责与接口

`uav_mission` 和 `uav_control` 是独立 ROS 2 节点。任务节点通过 `uav_interfaces` 发送目标、读取状态并请求离散命令，不跨包持有控制对象。接口包位于 `ros_ws/src/uav_control/uav_interfaces/`，随 `uav_control` 仓库发布；colcon 构建通过额外 base path 发现该嵌套包。

| 接口 | 类型 | 方向与用途 |
| --- | --- | --- |
| `/uav_control/target` | `geometry_msgs/msg/PoseStamped` | 任务节点发布单一目标，`frame_id=map`，ROS 本地 ENU 坐标 |
| `/uav_control/state` | `uav_interfaces/msg/VehicleState` | 控制节点发布连接、模式、解锁、位置有效性、着陆状态和命令完成结果 |
| `/uav_control/command` | `uav_interfaces/srv/FlightCommand` | 任务节点请求 Offboard、解锁、降落或上锁；服务应答只代表控制层接受/转发请求 |
| `/mavros/setpoint_position/local` | `geometry_msgs/msg/PoseStamped` | 控制节点唯一发布；20 Hz 独立 setpoint 周期 |

`uav_mission` 负责等待有效新鲜的连接、位置和地面状态，记录起飞位置与航向，完成当前位置 Offboard 准备，逐步确认模式和解锁状态，升高 1.0 m，满足位置阈值连续 2 秒后悬停 10 秒，再请求降落并确认着陆和最终上锁。等待、命令和着陆都由非阻塞状态机推进。

`uav_control` 订阅 MAVROS 的飞控状态、本地位置和 ExtendedState，发布统一状态，并独占 MAVROS 位置 setpoint。MAVROS 本地位置使用 best-effort 传感器 QoS，因此位置订阅使用 `SensorDataQoS`。ROS `map` 位姿按 ENU 表达，MAVROS setpoint 插件负责转换到 PX4 所需的 NED 表达；本实现不手动二次转换。

控制目标超过 1 秒未更新时，如果位置仍新鲜，控制节点在当前位置维持 setpoint 直到最多 3 秒的交接窗口，并请求 `/mavros/cmd/land`；进入 `AUTO.LAND` 后不再把预期停止的任务目标流判作故障。位置或飞控状态失效时，控制层不伪造新目标，让 PX4 的 Offboard 丢失保护接手。任务失败或取消时，任务状态机进入安全降落并等待明确的地面、上锁确认。

服务调用被接受与飞控实际完成状态分开处理。`FlightCommand` 回应中的 `dispatched` 仅表示请求已被控制层接收/转发；异步 MAVROS 回应进入 `/uav_control/state`，任务还要观察飞控确实进入 `OFFBOARD`、解锁、`AUTO.LAND` 或最终上锁，才推进下一阶段。

本次运行路径只实现 MAVROS。任务层没有 `FlightControlInterface` 对象依赖；若控制包保留该接口，只能用于控制包内部后端隔离。DDS、规划器、OpenVINS、真实相机和复杂任务框架均未接入。旧固定目标发布器已从 `setpoint.launch.py` 移除；启动测试时只运行任务节点作为目标来源。

## 版本、坐标和安全参数

| 项目 | 本次环境 |
| --- | --- |
| 主机 | Ubuntu 22.04.5 |
| ROS 2 | Humble |
| PX4 | v1.17.0；SITL 模型 `gz_x500` |
| Gazebo Sim | 8.14.0（Harmonic） |
| MAVROS | ROS 2 `ros2` 分支，提交 `e4f39208aa87`，版本 2.15.1 |
| MAVLink SITL 连接 | PX4 Onboard UDP local 14580 / remote 14540；MAVROS `udp://:14540@127.0.0.1:14580` |
| GCS | QGroundControl；PX4 的 `mavlink status` 显示 `GCS heartbeat valid` 后才解锁 |

首次尝试时 PX4 明确拒绝解锁，理由是 `No connection to the GCS`。打开 QGroundControl 后，PX4 确认 GCS 心跳并报告 `Ready for takeoff!`；没有通过关闭健康检查来绕过该阻塞。PX4 SITL 的 Data Link Loss 默认启用，仿真要求连接 GCS、SDK 或其他 MAVLink 应用，见 [PX4 v1.17 SITL failsafe 文档](https://docs.px4.io/v1.17/en/simulation/failsafes)。

PX4 shell 中现场读取的控制通信失效参数如下，测试期间没有修改：

| 参数 | 实测值 | 含义与验证边界 |
| --- | --- | --- |
| `COM_OF_LOSS_T` | `1.0 s` | Offboard 控制流丢失后的等待时间 |
| `COM_OBL_RC_ACT` | `0`（Position） | v1.17 文档定义的 Offboard 丢失动作；实际是否进入该备用动作还与 RC 状态有关 |
| `NAV_DLL_ACT` | `2`（Return） | GCS/Data Link 丢失后的动作 |

PX4 v1.17 要求先连续发送超过 1 秒、频率高于 2 Hz 的 Offboard setpoint 才允许切入 Offboard；低于 2 Hz 后按 `COM_OF_LOSS_T` 和 `COM_OBL_RC_ACT` 执行失效动作。控制节点以 20 Hz 发布，并在准备阶段持续发送当前位置目标。参数解释见 [PX4 v1.17 Offboard 文档](https://docs.px4.io/v1.17/en/flight_modes/offboard)。本次停止的是任务节点，控制节点仍运行并主动请求 Land，因此 PX4 的“Offboard setpoint 完全丢失”备用动作只核对了配置，没有单独触发验证；`COM_OBL_RC_ACT=0` 也不能描述成自动降落。

## 配置参数

任务参数位于 `ros_ws/src/uav_mission/config/mission.yaml`：

| 参数 | 值 |
| --- | ---: |
| `takeoff_height_m` | 1.0 |
| `horizontal_tolerance_m` | 0.20 m |
| `vertical_tolerance_m` | 0.15 m |
| `stable_duration_s` | 2.0 s |
| `hover_duration_s` | 10.0 s |
| `ready_timeout_s` | 30 s |
| `command_timeout_s` | 5 s |
| `takeoff_timeout_s` | 30 s |
| `landing_timeout_s` | 45 s |
| `state_timeout_s` | 1.0 s |

控制参数位于 `ros_ws/src/uav_control/config/control.yaml`：

| 参数 | 值 |
| --- | ---: |
| `publish_rate_hz` | 20 Hz |
| `state_timeout_s` | 2.5 s |
| `position_timeout_s` | 0.5 s |
| `target_timeout_s` | 1.0 s |
| `land_handover_timeout_s` | 3.0 s |
| `command_queue_timeout_s` | 3.0 s |

未放宽用户要求的起飞高度、阈值、稳定时长或悬停时长。

## 构建与接口验证

为保留工作区原有 `ros_ws/build`、`install` 和 `log` 产物，本次构建使用 `/tmp/boomboomfly_sitl_20260919`：

```bash
cd /home/aa/BoomBoomFly/ros_ws
source /opt/ros/humble/setup.bash
source /home/aa/BoomBoomFly/ros_ws/install/setup.bash
colcon --log-base /tmp/boomboomfly_sitl_20260919/log build \
  --base-paths src/uav_control/uav_interfaces src \
  --packages-select uav_interfaces uav_control uav_mission uav_bringup \
  --build-base /tmp/boomboomfly_sitl_20260919/build \
  --install-base /tmp/boomboomfly_sitl_20260919/install
source /tmp/boomboomfly_sitl_20260919/install/setup.bash
```

`uav_interfaces`、`uav_control`、`uav_mission`、`uav_bringup` 首轮构建通过；最后一次代码修改后，`uav_control` 和 `uav_mission` 再次构建通过。colcon 使用已有 install 中的 `mavros_msgs`，并给出该包未在此次临时构建中重建的提示。

隔离 domain 的 ROS smoke 命令及最终输出：

```bash
ROS_DOMAIN_ID=42 python3 /home/aa/BoomBoomFly/ros_ws/src/uav_control/test/smoke_test.py
```

```text
PASS: fresh unified state; no default target; dynamic ENU target at 20.27 Hz
```

测试先确认新鲜统一状态和地面状态、没有任务目标时不发布固定目标，再确认动态目标坐标和方向被转发，并测得 setpoint 发布频率 20.27 Hz。另在正常 SITL 中实际观察到两节点状态/命令往返、MAVROS 模式和解锁切换，以及统一位置状态，因此 ROS 通信验证不只依赖离线 smoke。

## 启动、停止与复现命令

先按以下顺序打开四个终端。QGroundControl 由操作者在桌面端启动。

终端一启动 PX4 SITL：

```bash
cd /home/aa/BoomBoomFly/ros_ws/upstream/PX4-Autopilot
HEADLESS=1 make px4_sitl gz_x500
```

终端二启动 MAVROS：

```bash
source /opt/ros/humble/setup.bash
source /home/aa/BoomBoomFly/ros_ws/install/setup.bash
ros2 launch mavros px4.launch fcu_url:=udp://:14540@127.0.0.1:14580
```

终端三启动控制与任务节点：

```bash
source /opt/ros/humble/setup.bash
source /home/aa/BoomBoomFly/ros_ws/install/setup.bash
source /tmp/boomboomfly_sitl_20260919/install/setup.bash
ros2 launch uav_bringup sitl_flight.launch.py
```

检查连接、单一 setpoint 发布者和飞控状态：

```bash
ros2 topic echo /mavros/state --once
ros2 topic info /mavros/setpoint_position/local --verbose
ros2 topic echo /uav_control/state
```

正常流程结束时，任务节点打印 `PASS` 并退出；此时按 `Ctrl+C` 停止仍运行的 bringup/控制节点，再按 `Ctrl+C` 停止 MAVROS 和 PX4。停止任务节点的专门试验中，任务进程停止后应保持控制节点、MAVROS、PX4 和 QGroundControl 运行，直到确认着陆和上锁。

单独复现任务节点停止试验时，使用独立终端分别启动控制和任务节点：

```bash
source /opt/ros/humble/setup.bash
source /home/aa/BoomBoomFly/ros_ws/install/setup.bash
source /tmp/boomboomfly_sitl_20260919/install/setup.bash
ros2 launch uav_control setpoint.launch.py
```

```bash
source /opt/ros/humble/setup.bash
source /home/aa/BoomBoomFly/ros_ws/install/setup.bash
source /tmp/boomboomfly_sitl_20260919/install/setup.bash
ros2 run uav_mission mission_node --ros-args \
  --params-file /tmp/boomboomfly_sitl_20260919/install/uav_mission/share/uav_mission/config/mission.yaml
```

在任务终端看到 `Flight stage: HOVER` 后按 `Ctrl+C` 停止**任务进程**，不要停止控制进程。控制日志应出现 `mission target timed out`、`requesting MAVROS land while localization is fresh` 和 Land 命令接受；随后应观察到 PX4 进入 `AUTO.LAND`、着陆并上锁。任务节点被主动停止时不会打印正常任务 `PASS`；这个试验只判定控制层失联处置结果。

## 实际结果与日志

### 正常起飞—悬停—降落：PASS

- PX4 实际进入 `OFFBOARD`，实际解锁；任务从当前位置升高 1.0 m。
- 目标误差连续满足水平 `≤ 0.20 m`、垂直 `≤ 0.15 m` 至少 2 秒后进入悬停；随后悬停完整 10 秒。
- 正常降落阶段观察到 PX4 `AUTO.LAND`；飞控报告地面状态，MAVROS 接受上锁请求，最终状态 `armed=false`。
- 任务节点实际输出：`PASS: Offboard, arm, 1 m takeoff, stable hold, 10 s hover, AUTO.LAND handover, landed and disarmed confirmed`。
- 悬停期间最大水平误差 `0.044356 m`，最大高度误差 `0.042743 m`，最大航向误差 `0.001780 rad`；最终水平位移 `0.037461 m`，最终相对起飞高度 `-0.033986 m`。

### 悬停时停止任务节点：控制层安全降落通过

- 任务日志最后阶段为 `HOVER`，任务进程停止后没有发出正常任务 Land 命令。
- 控制节点在 1 秒目标超时后记录定位仍有效，请求 Land；MAVROS 接受，PX4 切换到 `AUTO.LAND`。
- PX4 控制台记录 `Landing detected` 和 `Disarmed by landing`。最终 ROS 遥测为 `state_valid=true`、`connected=true`、`position_valid=true`、`landed_state=LANDED_ON_GROUND`、`armed=false`；最终绝对 `map` 坐标约为 `(-0.084, -0.094, 0.014) m`。
- 这次子试验验证的是“任务节点停止、控制节点仍工作”的主动降落交接，不是 PX4 Offboard setpoint 全部丢失后的备用动作试验。

### 过程中发现并修正的失败

- 首次联通后本地位置订阅 QoS 不兼容，控制节点收不到 MAVROS best-effort 位置；改为传感器 QoS 后收到新鲜位置。
- PX4 因没有 GCS 心跳拒绝解锁。操作者打开 QGroundControl 后心跳有效，未更改或关闭该健康检查。
- 首次成功解锁时任务仍发布地面高度目标，PX4 未起飞；日志实测起飞目标误差约 1 m 并触发安全降落。修正为确认解锁后更新到起飞高度，并重新运行。
- 首次完整降落时控制节点把 AUTO.LAND 期间停止目标流误判为任务超时，造成最终上锁命令受安全锁拒绝。修正降落交接期间的目标超时判据和安全命令重试后，后续正常流程 PASS。

### 日志路径

- PX4 控制台：`ros_ws/sitl_logs/2026-09-19/px4.log`
- MAVROS 控制台：`ros_ws/sitl_logs/2026-09-19/mavros.log`
- 最终正常流程：`ros_ws/sitl_logs/2026-09-19/mission_normal_pass.log`
- 任务停止试验：`ros_ws/sitl_logs/2026-09-19/mission_stop_task.log`
- 对应控制节点日志：`ros_ws/sitl_logs/2026-09-19/mission_stop_control.log`
- PX4 ULog：`ros_ws/upstream/PX4-Autopilot/build/px4_sitl_default/rootfs/log/2026-09-19/12_07_12.ulg`（正常流程）和 `12_08_44.ulg`（任务节点停止试验）。
- 独立临时构建输出：`/tmp/boomboomfly_sitl_20260919/log/`；原工作区的 `ros_ws/build`、`install`、`log` 未清理或覆盖。

## 验证范围

| 层级 | 结果 |
| --- | --- |
| 编译 | 通过：接口、控制、任务、bringup 首轮构建；最终控制和任务修改增量重建通过 |
| ROS 接口与通信 | 通过：隔离 smoke 20.27 Hz；SITL 中状态、目标、服务请求和飞控状态确认均有实际往返 |
| PX4 SITL | 通过：正常飞行 PASS；任务节点停止时控制层成功请求降落并最终着陆上锁 |
| 实机 | 未验证：没有连接真实飞控、飞机、相机或机载定位系统 |
| PX4 Offboard 丢流备用动作 | 参数已现场读取，行为未单独触发；任务停止试验由仍运行的控制节点主动发出 Land |
| VIO / OpenVINS / D435i | 未接入、未验证 |

执行 SITL 时没有提交或推送代码；本次后续发布按独立仓库分别提交，未把其他未提交文件混入。

## 官方资料

- [PX4 v1.17 Offboard 模式与 Offboard 丢失行为](https://docs.px4.io/v1.17/en/flight_modes/offboard)
- [PX4 v1.17 Gazebo SITL 启动](https://docs.px4.io/v1.17/en/sim_gazebo_gz/index)
- [PX4 v1.17 SITL Data Link Loss 安全检查](https://docs.px4.io/v1.17/en/simulation/failsafes)
- [MAVROS ROS 2 坐标系约定与 ENU/NED 转换](https://github.com/mavlink/mavros/blob/ros2/docs/frames.md)
- [MAVROS ROS 2 本地位置话题与 QoS](https://github.com/mavlink/mavros/blob/ros2/docs/plugins/std/local_position.md)
