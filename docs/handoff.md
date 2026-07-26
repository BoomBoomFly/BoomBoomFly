# BoomBoomFly 窗口交接

> 更新时间：2026-07-26T16:46:43+08:00
> 工作区：`/home/c/BoomBoomFly`
> 当前阶段：P0-03，**OFFBOARD CONTRACT PUBLISHED / FIRMWARE PROFILE BLOCKED / FAIL-CLOSED**
> production：**DISABLED**

## 给新窗口的直接指令

```text
读取 /home/c/BoomBoomFly/docs/handoff.md。
保留四个第三方 dirty checkout，不 reset/clean/覆盖。
Offboard 对 `/fmu/out/vehicle_status_v1` 的修复已通过 PR #2 合并到
`DDS@cded3dc5`，根 lock 已同步，9 项 gtest 已通过。从“下一步”开始：准备隔离
PX4-Autopilot v1.16.2 源码、
锁定工具链和证据模板，再为 DDS 输出增加 `rc_channels` 并完成静态生成、SITL
和 FMUv3 构建验证，但不刷写。TELEM2 是专用 DDS transport，
不得与 MAVLink 复用。未经新授权，不访问硬件、不写 PX4 参数、不刷固件、不 arm、
不切 mode、不发送 setpoint/vehicle command，也不启动 Agent、Offboard 或视觉链路。
```

## 1. 当前仓库状态

| 项目 | 当前值 |
|---|---|
| 根仓库 | `/home/c/BoomBoomFly` |
| 根发布分支 / base | `agent/follow-latest-px4-bringup` / `master@531c9b0` |
| 根工作树 | 发布分支；同步归档 px4_bringup 的维护分支、精确 lock 与相关文档 |
| Offboard origin | `https://github.com/BoomBoomFly/offboard_cpp.git` |
| Offboard HEAD | `DDS@cded3dc5b6906420db3767abd82b2df7ba6ea9f0`，clean |
| Offboard 对齐 | 根 lock 固定 `cded3dc5`；PR [#2](https://github.com/BoomBoomFly/offboard_cpp/pull/2) 已合并 |
| px4_bringup HEAD | `DDS@0fbdcbf6ee53d6927de75af1d98f22cf5bd4f917`，clean |
| px4_bringup 对齐 | 根维护清单跟随 `DDS`，根 lock 固定 `0fbdcbf6`；继续排除出 DDS-only build/launch |
| 旧 Offboard 备份 | 已按维护者要求永久删除；不存在备份 |

已仅恢复原先缺失的 exact checkout：

- `src/px4_msgs@392e831c1f659429ca83902e66820d7094591410` (`v1.16.2`)；
- `src/Micro-XRCE-DDS-Agent`，lock 为
  `57d086216d01ec43121845d385894a25987f8a2c` (`v2.4.2`)；
- `src/vision_to_dds`，lock 为
  `0c3a00137f3c90a4051ac1bc1029ec56beb669b6`。

全部 16 项经逐项只读核验，HEAD 与 origin 均匹配 lock。`librealsense`、
`navigation_msgs`、`realsense-ros`、`vision_opencv` 是保留的既有 dirty 仓库；
Offboard 的 RC 修复已随 PR #1 合并，`vehicle_status_v1` 契约修复已随 PR #2
合并到 `DDS@cded3dc5`，根 lock 已同步；归档 `px4_bringup` 已对齐上游默认
`DDS@0fbdcbf6` 并纳入精确 lock，其余 12 项 clean。

`px4_bringup` 的 `DDS` 分支名称不代表其启动链已迁移到 uXRCE-DDS：当前源码仍会
组合 MAVROS、旧视觉桥和串口节点，并可能争用 `/dev/ttyTHS0:921600`。该包继续位于
`workspace.excluded_packages`，不得用于 production、默认构建或批准 launch。

正式检查仍会 fail-closed，但现在会先完成整个 manifest 的只读审计：

```bash
bash Scripts/installation/uav_px4_dds_install.sh --verify-only --skip-package-check
```

当前结果为 `planned=16 verified=16 blockers=4`，退出状态码 1。四个既有 blocker
仍是按维护者要求暂不处理的 `librealsense`、`navigation_msgs`、`realsense-ros`
和 `vision_opencv`；Offboard HEAD、origin 与根 lock 已重新对齐。
全部仓库 origin 仍匹配预期；审计保持 fail-closed。
命令没有 clone、fetch、checkout、更新 submodule 或覆盖任何既有仓库。完整记录见
[`evidence/OFFBOARD_PX4_MSGS_COMPAT_20260724.md`](evidence/OFFBOARD_PX4_MSGS_COMPAT_20260724.md)。

## 2. 实机 PX4 基线与 transport 变化

下列固件信息和参数通过 `/dev/ttyTHS0:921600` 于 2026-07-24 只读获取。
采集时飞控未解锁、已落地；采集过程没有参数写入、切模、控制命令或刷写。

| 字段 | 实测值 |
|---|---|
| autopilot / vehicle | PX4 / quadrotor，MAVLink system 1 |
| firmware | PX4 Release `1.16.2` |
| PX4 git hash | `54f0455ffcd755534539a7cf33a09a20bf71d29d` |
| 官方对应 | `PX4-Autopilot v1.16.2^{}` 指向同一提交 |
| board | `PX4_FMU_V3`，HW type `V30` |
| MCU | STM32F42x revision 5 |
| OS | NuttX 11.0.0 |
| build | 2026-04-22 14:06:56，variant `default` |
| airframe | `SYS_AUTOSTART=4001`，Generic Quadrotor X |
| HITL | `SYS_HITL=0` |

完整 972/972 参数快照：
[`evidence/PX4_PARAMS_20260724T203458+0800.json`](evidence/PX4_PARAMS_20260724T203458+0800.json)。
文件同时保留 MAVLink wire float、参数类型和解码值。

参数调整前的关键参数：

| 参数 | 值 / 结论 |
|---|---|
| `UXRCE_DDS_CFG` | `0`，DDS client 未配置 |
| `MAV_1_CONFIG` | `102`，TELEM2 用于 MAVLink |
| `SER_TEL2_BAUD` | `921600`，当前 Jetson 链路 |
| `COM_OF_LOSS_T` | `1.0 s` |
| `COM_OBL_RC_ACT` | `0`，Position |
| `COM_RCL_EXCEPT` | `0`，Offboard 未忽略 RC loss |
| `COM_RC_LOSS_T` | `0.5 s` |
| `RC_MAP_OFFB_SW` | `6` |
| `RC_MAP_KILL_SW` | `8` |
| `EKF2_EV_CTRL` | `0`，外部视觉融合未启用 |
| `EKF2_EV_DELAY` | `0`，未标定 |
| `EKF2_EV_POS_X/Y/Z` | `0/0/0`，lever arm 未配置 |

2026-07-25，维护者已自行调整 TELEM2/MAVLink/DDS 参数，并授权重新测试 DDS。
调整后的精确参数值尚未重新采集；当前没有 PX4 USB 或其他 MAVLink 通道可用于
只读参数快照。因此上表及 JSON 必须视为**调整前历史快照**，不得代表当前配置。

调整后的运行验证已确认：

- `/dev/ttyTHS0:921600` 在 Agent 启动前无进程占用；
- PX4 与 Micro XRCE-DDS Agent v2.4.2 建立 client `0x00000001` session；
- DDS participant `/px4_micro_xrce_dds` 创建成功并持续写入真实 payload；
- 测试结束后 Agent 已停止，串口已释放。

尚缺：实际烧录 `.px4` artifact SHA-256，以及原构建目录的 clean/patch/
submodule 证据；还缺调整后的 PX4 参数快照。实机 git hash只能确认二进制对应
官方 release commit。

## 3. Companion 硬件枚举

| 设备 | 当前观察 |
|---|---|
| 主机 | NVIDIA Orin Nano Developer Kit，aarch64，kernel 5.10.104-tegra |
| PX4 UART | `/dev/ttyTHS0:921600`，已验证为专用 XRCE-DDS transport；用户 `c` 在 `dialout` |
| PX4 USB | 未发现 `/dev/ttyACM*` 或 PX4 USB 设备 |
| RealSense | D435，USB3 5000M，serial `227323021826` |
| USB Camera2 | VID:PID `0bda:5858`，serial `200901010001` |
| VPU | Intel Movidius Myriad，`03e7:2150` |
| T265 | 未发现 |
| RPLIDAR | 未发现 `/dev/rplidar` 或 `/dev/ttyUSB*` |

没有启动相机、VPU、雷达或 ROS 硬件节点。

## 4. DDS topic 契约

PX4 v1.16.2 官方默认 `dds_topics.yaml` 已确认包含：

- 输入：`offboard_control_mode`、`trajectory_setpoint`、
  `vehicle_visual_odometry`、`vehicle_command`；
- 输出：`battery_status`、`vehicle_land_detected`、`vehicle_odometry`、
  `vehicle_status`、`vehicle_command_ack`。

默认文件不包含：

- `/fmu/out/rc_channels`：当前 Offboard 的硬依赖；
- `/fmu/in/landing_target_pose`：视觉桥精降路径。

上游来源：
<https://raw.githubusercontent.com/PX4/PX4-Autopilot/v1.16.2/src/modules/uxrce_dds_client/dds_topics.yaml>。

2026-07-25 实机只读 discovery 进一步确认：

- `/fmu/out/battery_status`、`vehicle_land_detected`、`vehicle_odometry`、
  `vehicle_command_ack` 等默认输出均存在；
- `VehicleStatus.msg` 的 `MESSAGE_VERSION=1`，实机实际导出
  `/fmu/out/vehicle_status_v1`；
- discovery 当时锁定的 Offboard 仍订阅 `/fmu/out/vehicle_status`，因此收不到
  实机状态；后续本地修复见第 5 节；
- `/fmu/out/rc_channels` 仍不存在，`ros2 topic info` 返回 unknown topic；
- `BatteryStatus` 已成功解码真实数据，例如 `connected=true`、4 cells、电压约 16 V。

决策已冻结：

- `/fmu/out/rc_channels` 保留为 Offboard 安全互锁的硬依赖；未来必须使用定制的
  PX4 v1.16.2 DDS firmware profile 导出该 topic。
- baseline 不要求 `/fmu/in/landing_target_pose`；`vision_to_dds` 默认
  `enable_precland=false`，关闭时不创建该 publisher。精降使用独立 profile。
Agent 配置无法凭空增加 firmware 未生成的 topic。本次验证没有构建或刷写
firmware，也没有由本工作区发送 PX4 参数写入或任何控制消息；参数调整由维护者
在验证前完成。

## 5. Offboard / px4_msgs 兼容性

当前工作区构建已通过：

```bash
source /opt/ros/foxy/setup.bash
colcon build --packages-up-to offboard_cpp
```

结果：`px4_msgs` 与 `offboard_cpp` 共 2 packages finished。

已修改：

- `BatteryStatus.voltage_v` 与 `VehicleStatus::ARMING_STATE_DISARMED` 兼容；
- RC 从 `1000..2000` PWM 迁移为 v1.16.2 normalized 语义；
- 校验无首帧、`signal_lost`、`channel_count`、配置/物理数组边界、finite/range
  和接收时间 freshness；
- FSM 的 RC 消费点在 invalid/stale 时 fail-closed；
- mock RC 发布器同步为 normalized 有效帧。

测试：

```text
colcon test --packages-select offboard_cpp
7 tests passed, 0 failed

colcon test-result --verbose --test-result-base build/offboard_cpp
Summary: 8 tests, 0 errors, 0 failures, 0 skipped
```

持久证据见
[`evidence/OFFBOARD_PX4_MSGS_COMPAT_20260724.md`](evidence/OFFBOARD_PX4_MSGS_COMPAT_20260724.md)。

实机 DDS 验证发现的状态 topic 契约已修复并通过 PR #2 合并：

- `include/topics.hpp` 集中定义 `fmu/out/vehicle_status_v1`；
- `src/node.cpp` 的生产订阅直接引用该常量；
- `test/test_topic_contract.cpp` 检查精确 topic、生产引用和旧字面量回归；
- 隔离构建 `px4_msgs`、`offboard_cpp` 成功，全量 CTest 2/2 executable、
  共 9 个 gtest case 全部通过，`git diff --check` 通过。

修复提交为 `73569b2db19b6178bfa0a30ac38911175517cc97`，分支
`agent/px4-v116-status-contract`，PR [#2](https://github.com/BoomBoomFly/offboard_cpp/pull/2)
已合并为 `DDS@cded3dc5b6906420db3767abd82b2df7ba6ea9f0`；根 lock 已同步。
由于 `/fmu/out/rc_channels` 仍缺失，任何实机 Offboard 运行继续 fail-closed。

## 6. 仍有效的架构约束

权威决策在 [`adr/0001-dds-only-control-authority.md`](adr/0001-dds-only-control-authority.md)
和 [`CONTROL_AUTHORITY_MATRIX.md`](CONTROL_AUTHORITY_MATRIX.md)：

- production 只允许 PX4 uXRCE-DDS，不允许 MAVROS fallback；
- `/offboard_control_node` 是 trajectory/mode/vehicle command 的唯一 writer；
- `/vision_to_dds_node` 是外部视觉和可选精降目标的唯一 writer；
- 每个 profile 只允许一个 mission owner；
- 当前只支持单机根 namespace `/`；
- owner/lease、graph guard、ACK 和安全状态机未实现前 production 禁用。

## 7. 下一步

Offboard PR #2 与根文档 PR #2 已合并，根 lock 已跟随最新 `DDS@cded3dc5`。
下一阶段分为三条工作线；A、B 可离线并行，C 只准备模板：

1. **A — 可复现源码与工具链**：在隔离目录取得 PX4-Autopilot
   `v1.16.2@54f0455ffcd755534539a7cf33a09a20bf71d29d`，初始化并记录递归
   submodule；锁定 OS/架构、容器 digest 或交叉编译器、CMake、Ninja 和 Python。
2. **B — `rc_channels` firmware profile**：确认 PX4 源码与锁定 `px4_msgs`
   的 `RcChannels.msg` 完全一致，只在 `dds_topics.yaml` publications 增加
   `/fmu/out/rc_channels` / `px4_msgs::msg::RcChannels`，不加入精降 topic。
3. 使用 PX4 自身构建流程完成静态生成，在生成物中确认对应 DataWriter；随后在
   隔离 SITL + UDP Agent 中验证 topic type、QoS、唯一 PX4 publisher 和至少一帧
   来自 PX4 的 payload，禁止用 mock publisher 作为验收证据。
4. SITL 通过后构建 `px4_fmu-v3_default`，记录 flash/RAM 余量，并保存源码 patch、
   submodule 清单、构建日志和最终 `.px4` SHA-256；本阶段不刷写。
5. **C — transport 证据模板**：离线定义调整后参数、数字 DDS domain、Agent binary、
   端口 owner、原始 transcript 和回滚表的采集格式。实际访问硬件、启动 Agent 或
   读取调整后参数仍需新的明确授权；没有独立 MAVLink/NSH 通道时不得复用 TELEM2。
6. 完成上述软件门后，再安排 Agent 只读复验；Offboard 仍需 SITL、故障注入、
   control-authority 安全门和拆桨台架，production 继续禁用。

当前主阻塞是本机缺少隔离 PX4-Autopilot 源码、`arm-none-eabi-gcc/g++`、`gz-sim`
和 PATH 中的 MicroXRCEAgent，以及 firmware 尚未导出 `rc_channels`。TELEM2 transport
本身已只读验证通过，但精确参数、domain 与回滚值仍待另行授权采集。

## 8. 安全与操作边界

未经新授权不要：

- arm、set mode、发送 `/fmu/in/*`、vehicle command 或 setpoint；
- 写 PX4 参数、重启飞控、刷 firmware；
- 启动 Agent、Offboard、vision、MAVROS 或旧 bringup；
- 把 `/dev/ttyTHS0` 同时交给 MAVLink 与 serial Agent；
- reset/clean/强制 checkout；未经新的明确范围，不追加提交或推送；
- 恢复已删除的旧 Offboard 备份或过时状态文档。

## 9. 本轮文件与验证

保留文档：

- 本文件；
- [`CONTROL_AUTHORITY_MATRIX.md`](CONTROL_AUTHORITY_MATRIX.md)；
- [`adr/0001-dds-only-control-authority.md`](adr/0001-dds-only-control-authority.md)；
- 两份 `evidence/` 原始证据。

已删除八份被本 handoff 取代的旧状态报告：架构、构建、硬件、阶段任务、PX4
基线、仓库状态、风险清单、源码基线。旧 Offboard 备份也已永久删除。本轮另删除
与根 README 文档索引重复的 `docs/README.md`。

上一轮另删除被 `.gitignore` 明确排除的可再生 `build/`、`install/`、`log/`，约
227 MB；验证结果已保存在 evidence，需要时可重新执行 colcon 生成这些目录。

最终验证应包括：

```bash
git diff --check
bash Scripts/installation/uav_px4_dds_install.sh --verify-only
git -C src/offboard_cpp status --short --branch
git status --short --branch
```

根文档更新已通过 PR #2 合并为 `master@16a0d8a`；Offboard
`vehicle_status_v1` 修复已通过 PR #2 合并为 `DDS@cded3dc5`。本次根 lock
同步位于 `agent/follow-latest-offboard`。
