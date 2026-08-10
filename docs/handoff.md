---
title: BoomBoomFly 当前交接
status: phase-1-sitl-normal-path-validated-pending-faults-and-vision
updated: 2026-08-10
---

# BoomBoomFly 当前交接

第一阶段的软件骨架、包重构和包级验证已经完成。当前实现范围是最小飞行闭环；SITL 已证明
PX4 → uXRCE-DDS Agent → ROS 2 的关键状态数据流，并已在虚拟摇杆触发下完成一次正常 SITL
最小闭环。故障矩阵、视觉融合、Foxy 和实机门仍未验证。

## 当前入口

- [统一技术路线](BoomBoomFly_统一技术路线.md)：第一阶段已确认的边界与后续路线。
- [第一阶段实施计划](第一阶段实施计划.md)：已执行工作、验证结果和未完成门。
- [第一阶段实机门禁清单](第一阶段实机门禁清单.md)：仅供现场操作员逐项批准，不由程序执行。

## 已完成实现

| 范围 | 当前结果 |
|---|---|
| `common` | `boomboom_common` ROS 包；纯 C99 core、固定宽度 POD、status/state/fault/event/log 接口和 ROS 2 转换层。core 不依赖 ROS、PX4、Linux、HAL、动态内存、文件系统或 UART。 |
| `offboard_cpp` | 一个 20 Hz `offboard_mission_node`；内部 `MissionController + Px4Interface`。它是三个生产 PX4 控制输入的唯一 writer，并对 PX4 v1.16 的版本化状态话题订阅 `/fmu/out/vehicle_status_v1`。 |
| `px4_vision_bridge` | 独立 Git 仓库从 `vision_to_dds` 原子迁移而来；现在仅提供 DDS `nav_msgs/Odometry → VehicleOdometry`。 |
| `communication` | 保留独立 Git 边界，但第一阶段没有 ROS 包、串口节点或 START 协议。 |
| `px4_bringup` | `sitl.launch.py` 和 `hardware.launch.py` 加三层参数配置；只编排 DDS Agent、视觉 bridge 和 mission node。 |

Legacy T265、MAVROS、比赛 launch、START/session/epoch、authority lease、旧 SafetyGate/FlightSequence
和重复串口 `common` 已退出第一阶段活动范围。`ros2_foxy_vision_to_mavros` 保留历史但由
`COLCON_IGNORE` 排除。

## 第一阶段运行不变量

- 必须先观察一次 PX4 `DISARMED`，仅接受 RC switch/stick 的解锁上升沿。
- 程序不发送 ARM、DISARM 或 Kill；RC/PX4 负责这些操作。
- 以 PX4 EKF2 `VehicleLocalPosition` 作为飞行反馈；定位失效时原地 Land，不盲目返航。
- Offboard 在 20 Hz 预发送至少 1 秒后请求，且必须同时得到 ACK 接受与实际 `OFFBOARD` 状态。
- 起飞 home 在解锁沿冻结；默认起飞 1.5 m、悬停 60 s、保持高度返回本地 home 后请求 Land。
- 坐标 reset 会修正 home 和目标；人工切出 Offboard 或 PX4 failsafe 后不自动抢回控制权。
- vision bridge 统一完成 ENU/FLU→NED/FRD、旋转复合、协方差、freshness 与 PX4 boot-time 映射；
  缺失或过期 `TimesyncStatus` 时不发布视觉输入。

## 已验证

- PX4 与 `px4_msgs` 固定在 `v1.16.2`；Micro XRCE-DDS Agent 固定在 `v2.4.2`。
- `px4_msgs`、`boomboom_common`、`px4_vision_bridge` 和 `offboard_cpp` 已在 Humble 工作区构建。
- CTest：common 2/2、vision bridge 3/3、offboard controller 1/1 通过。
- 新 launch 文件已通过 Python 语法检查；`px4_bringup` 的 setuptools build 通过；`git diff --check` 通过。

## 2026-08-10 SITL 集成状态

### 已完成的实际证据

- PX4 `v1.16.2` 已构建 `gz_x500` SITL；Gazebo 中已生成 `x500_0`。
- Humble 工作区已重新构建 `px4_msgs`、`boomboom_common`、`px4_vision_bridge`、
  `offboard_cpp` 和 `px4_bringup`，对应可执行文件可被 `ros2` 找到。
- Micro XRCE-DDS Agent `v2.4.2` 已构建并由 `px4_bringup/sitl.launch.py` 启动，UDP
  `8888` 已监听；Agent 日志确认 PX4 client session 建立并创建 DDS 实体。
- ROS 2 侧已以 best-effort QoS 实际采到 `/fmu/out/vehicle_local_position`、
  `/fmu/out/timesync_status` 与 `/fmu/out/vehicle_status_v1` 样本。后者是 PX4 v1.16
  `VehicleStatus.MESSAGE_VERSION = 1` 的版本化运行时话题，不是基础名
  `/fmu/out/vehicle_status`。
- 已将 mission node 的 `VehicleStatus` 订阅改为 `/fmu/out/vehicle_status_v1`，仅重建
  `offboard_cpp` 后重启本地 Agent、vision bridge 和 mission node（PX4/Gazebo 保持运行）。
  mission node 实际经过 `WAIT_DISARMED → WAIT_LOCALIZATION → READY`。
- `px4_vision_bridge` 仍处于 `waiting_input_and_timesync`，因为尚未提供 `/vision/odometry`。
  在 `READY` 状态下连续 3 秒未收到 `/fmu/in/offboard_control_mode` 样本；没有发送 ARM、
  DISARM、Kill、Offboard 请求或起飞命令。
- QGroundControl 虚拟摇杆随后触发了允许的解锁沿。mission node 日志记录完整正常路径：
  `OFFBOARD_PRESTREAM → REQUEST_OFFBOARD → TAKEOFF → HOVER → RETURN_LOCAL → LAND_REQUEST →`
  `WAIT_LANDED → COMPLETE → WAIT_DISARMED → WAIT_LOCALIZATION → READY`。其中 prestream
  约 1 秒，起飞至稳定约 8 秒，悬停约 62 秒；Land 后由 PX4 进入 disarmed，程序未发送
  ARM、DISARM 或 Kill。
- QGC 画面在任务期间显示 `Flying / Offboard`。mission 只能由 `STICK_GESTURE` 或
  `RC_SWITCH` 解锁沿离开 `READY`，因此本次进入 `OFFBOARD_PRESTREAM` 是虚拟摇杆触发
  允许来源门禁的运行时证据。
- Windows 端 QGroundControl 已连接到 SITL，界面显示 `Ready To Fly`，证明 PX4 的 MAVLink
  GCS 链路和 Gazebo 飞行器可用。

### 已解决的 DDS 阻塞

- 原先的错误判断是订阅了基础名 `/fmu/out/vehicle_status`。PX4 client 对版本化
  `VehicleStatus` 自动追加 `_v1`，因此实际 publisher 位于
  `/fmu/out/vehicle_status_v1`。其余两条关键话题不带此后缀。
- Agent 使用 Humble Fast DDS `2.6.12` 构建，但本次 SITL 已实际建立 session、创建 DDS
  实体并传输上述关键样本；它不再是当前 SITL DDS 阻塞。该依赖组合仍不能替代 Foxy/Jetson
  或实机验证。

### 2026-08-11 Jetson/Foxy 感知依赖基线

- `manifests/perception.repos` 已固定 `librealsense v2.56.5`
  (`38a41441971387197193ad3aeae3cefe6a11f2cb`) 与 `realsense-ros 4.56.4`
  (`bafc21080c5c8e259dadbb309797949aee0dd950`)。该 Wrapper 的 CMake 要求
  `realsense2 >= 2.56`，与机载端现有 `2.56.5` 匹配。
- Humble 开发机已成功构建 `librealsense2 2.56.5`；`realsense2_camera` 配置已越过
  SDK 版本检查，当前仅因本机缺少 `diagnostic_updater` 停止。Jetson/Foxy 部署前需安装
  `ros-foxy-diagnostic-updater`，并在目标机重新完成 Wrapper 构建与相机运行验证。
- `px4_vision_bridge` 仍只接收标准 `nav_msgs/Odometry` 的 `/vision/odometry`，不直接调用
  RealSense API，因此本次版本适配不改变 PX4 DDS 注入接口。

### 已验证的正常飞行步骤（仅 SITL）

- 已使用 QGroundControl 虚拟摇杆完成一次允许来源的解锁沿、Offboard 握手、1.5 m 起飞、
  60 s 悬停、返回本地 home、Land 和 landed/disarmed 收口。QGC 工具栏 Arm 按钮的外部命令
  来源拒绝路径尚未验证。
- 未提供 `/vision/odometry` 输入，故未验证视觉 bridge 的 `VehicleOdometry` 发布或 EKF2
  视觉融合。

## 尚未验证，仍是放行条件

- PX4 SITL 的故障矩阵：外部命令解锁拒绝、状态/定位过期、ACK 拒绝/超时、人工切出 Offboard、
  PX4 failsafe、Offboard-loss 和 mission node 退出。
- PX4 对视觉数据的实际 timesync、EKF2 融合与本地位置稳定性。
- D435i 的 VIO 算法、安装方向、frame 和外参；硬件配置不含伪造外参。
- Jetson Orin Nano / ROS 2 Foxy 构建与无桨地面联调。
- 所有实机解锁、Kill、人工接管、系留和受控飞行步骤。

## 下一工作窗口

下一步先在 SITL 执行外部命令解锁拒绝、Offboard-loss/人工接管和定位失效收口；随后提供合成
`/vision/odometry` 验证视觉输入与 EKF2 融合。不要恢复旧协议或旧控制节点，也不要把 Humble
SITL 结果当作 Foxy 或实机验证结论。
