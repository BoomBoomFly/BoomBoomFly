# PX4、DDS、MAVLink 与 Offboard 控制链

## 权威路径

仓库 ADR 将 production 唯一路径冻结为：

```text
ROS 2
  <-> Micro XRCE-DDS Agent
  <-> PX4 v1.16.2 uXRCE-DDS client

mission owner
  -> /offboard/*
  -> offboard_control_node
  -> /fmu/in/{trajectory_setpoint,offboard_control_mode,vehicle_command}
```

MAVROS、MAVLink serial 和 `px4_bringup` 是 forbidden/archive，不是 fallback。
这一规则有文档和静态 profile，但当前 checkout 没有满足规则的安全实现。

## [P0-CTRL-001] 当前 live PX4 writer 绕过已测试的运行时安全门

- 严重度：P0
- 状态：已确认
- 领域：PX4 / DDS / Offboard / Code
- 位置：
  - `src/offboard_cpp/src/node.cpp:20-35,86-91`
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:326-340,405-416`
  - `src/offboard_cpp/CMakeLists.txt:43-77,113-126`
  - `Scripts/test/verify_h0_production.py:52-53`
- 证据：
  - node 直接创建三个 `/fmu/in/*` publisher。
  - FSM 每 20 ms 运行并直接发布 setpoint/mode；VehicleCommand 也直接 publish。
  - `OffboardRuntimeGate` 被编译/测试，但 production node/FSM 没有实例。
  - 当前静态 H0 实测 exit 2：`production SafetyGateAdapter is missing`。
- 影响：
  - authority、lease、ACK、freshness、prestream、restart 和 duplicate-writer
    测试不约束实际飞控写路径。
  - 一旦该节点与真实 Agent/PX4 同图，模式/解锁/设定点命令可能绕过门禁。
- 根因：
  - 当前 checkout 为旧 `976d621…`，不是锁定并测试的 `722e05a…` candidate。
- 建议：
  - 禁止启动当前节点；先恢复/审定 exact candidate。
  - 强制三个 writer 只能由单一 `SafetyGateAdapter` 所有，所有拒绝路径发布计数为 0。
- 前置条件：
  - exact source 冻结；ACK/status/topic/authority contract；隔离 H0/H1/H2。
- 是否涉及硬件：
  - 需要后续现场验证

## [P0-CTRL-002] 默认自动解锁与 mock RC 可进入 production 编译路径

- 严重度：P0
- 状态：已确认
- 领域：Offboard / PX4 / Code / Launch
- 位置：
  - `src/offboard_cpp/CMakeLists.txt:33-35`
  - `src/offboard_cpp/config/ctrl_param.yaml:12-16`
  - `src/offboard_cpp/src/node.cpp:15-18`
  - `src/offboard_cpp/src/lib/input.cpp:143-158`
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:131-170,427-477`
- 证据：
  - `TEXT_RC` 对整个包无条件定义。
  - `takeoff_land.enable_arm` 默认 `true`。
  - 起飞分支只有在 `rc_is_received()` 为真时才校验 RC；RC 不新鲜/从未到达时会跳过该块。
  - 条件满足后调用 `arm_to_disarm(..., true)`，直接发布 ARM command。
  - 未订阅 `VehicleCommandAck`。
- 影响：
  - 错误/未授权的 `/offboard/takeoff_land=1` 与伪造/缺失 RC 条件可能产生模式和解锁请求。
- 根因：
  - 测试宏、安全默认和 production build 未分离；状态确认依赖 VehicleStatus 而非命令 ACK。
- 建议：
  - production 移除 mock 编译路径；`enable_arm=false` 默认。
  - fresh physical RC、kill latch、authority lease、accepted ACK、arming/status 全部作为强制门。
- 前置条件：
  - 固件 RC DDS topic/profile、command ACK topic、人工批准的 SITL 用例。
- 是否涉及硬件：
  - 需要后续现场验证

## [P1-CTRL-003] Offboard RC 安全输入与 PX4 v1.16.2 默认 DDS topic 集不闭合

- 严重度：P1
- 状态：高概率
- 领域：PX4 / DDS / Offboard
- 位置：
  - `src/offboard_cpp/src/node.cpp:50-54`
  - `src/offboard_cpp/include/topics.hpp:7`
  - `src/px4_msgs/msg/VehicleStatus.msg:3-5`
  - `docs/CONTROL_AUTHORITY_MATRIX.md:18-25`
- 证据：
  - Offboard 必须订阅 `fmu/out/rc_channels`。
  - 仓库权威矩阵记录：PX4 v1.16.2 默认 `dds_topics.yaml` 不导出该 topic。
  - `px4_msgs@392e831…` 与 v1.16.2 tag 匹配。
  - VehicleStatus 使用 `MESSAGE_VERSION=1`，代码已正确使用 `vehicle_status_v1`。
- 影响：
  - 默认 firmware 下 RC freshness 永远不满足；如果使用当前 P0 分支，又可能被“无 RC 时跳过”逻辑绕开。
- 根因：
  - 安全设计依赖定制 firmware topic profile，但当前工作区没有绑定 firmware/board 参数卡。
- 建议：
  - 固定 PX4 v1.16.2 firmware SHA、board、`dds_topics.yaml` 和生成消息 hash。
  - 无 `rc_channels` 必须 fail closed，不允许软件 mock 替代。
- 前置条件：
  - PX4 firmware source/生成物与参数快照；不需要先接硬件。
- 是否涉及硬件：
  - 需要后续现场验证

## [P1-VISION-001] 外部视觉 frame、时间与健康契约不足以安全注入 PX4

- 严重度：P1
- 状态：高概率
- 领域：PX4 / DDS / Sensor / Code
- 位置：
  - `src/vision_to_dds/src/vision_to_dds.cpp:78-121`
  - `src/vision_to_dds/src/vision_to_dds.cpp:262-338`
- 证据：
  - 默认直接创建 `/fmu/in/vehicle_visual_odometry` publisher。
  - `timestamp` 使用 ROS node 当前时钟，`timestamp_sample` 使用 TF stamp；未证明两者与 PX4 boot clock 同 epoch。
  - 位置只做平面 yaw 旋转，却固定声明 `POSE_FRAME_FRD`；没有显式 ENU→NED 的 z 轴变换证明。
  - `reset_counter=0`、`quality=1`、协方差为常数；未见 tracker reset、freeze、device
    health、时间回退或 frame identity gate。
- 影响：
  - 启用后可能向 EKF 注入错误轴、错误 epoch 或质量声明过高的外部里程计。
- 根因：
  - 参数化数学变换代替了端到端 frame/time/estimator contract。
- 建议：
  - production 默认不创建 PX4 writer；先实现纯函数 frame/time 转换与 golden tests。
  - 增加 monotonic epoch、reset_counter、quality/covariance、freeze/stale/device health 门。
- 前置条件：
  - 相机型号/序列号、TF tree、PX4 EKF2 参数、时间同步方案。
- 是否涉及硬件：
  - 需要后续现场验证

## [P1-CTRL-004] 缺少可执行且获准的项目级 DDS/SITL orchestration

- 严重度：P1
- 状态：已确认
- 领域：DDS / Launch / Test
- 位置：
  - `Scripts/README.md:104-116`
  - `config/profiles/dds_only_launch.yaml:172-195`
  - `docs/architecture/DEPLOYMENT_TOPOLOGY.md:77-79`
- 证据：
  - Scripts README 明确“当前不存在获准执行的项目级 SITL orchestration”。
  - production profile 仅静态 allowlist Offboard，`production_enabled=false`。
  - `/dev/ttyTHS0:921600` 独占规则有文档，但当前参数/domain/client identity/回滚值为 runtime unverified。
- 影响：
  - 无法以可重复命令验证 Agent→topic→Offboard→failsafe 链；人工拼接命令易混用真机/旧入口。
- 根因：
  - 安全规范、offline test 与实际 orchestration 尚未完成闭环。
- 建议：
  - Phase 2 只为 SITL 建立 exact command card：单 PX4、单 Agent、隔离 domain、
    remapped/virtual transport、writer census、failsafe assertions。
- 前置条件：
  - Phase 0/1 通过，且明确不连接任何 `/dev/tty*`。
- 是否涉及硬件：
  - 否

## QoS、单位与控制状态补充

- 当前 Offboard 对 PX4 输入/输出统一使用 KeepLast(1)、best-effort、volatile；
  这与常见 PX4 ROS 2 sensor-data 风格相近，但本轮没有运行 discovery 验证实际端点兼容。
- Offboard timestamp 以 `now.nanoseconds()/1000` 写微秒，单位正确；时钟 epoch 与 PX4
  是否一致仍需 SITL/transport 验证。
- TrajectorySetpoint 位置/速度单位按米、米每秒；角度按弧度。代码未在接口层编码单位类型。
- MAVROS 源码/旧 launch 仍在磁盘，但 production package/profile 明确禁止；未发现批准的
  DDS+MAVROS 同时运行路径。旧 launch 若手工执行仍可能引发串口/控制权竞争。
