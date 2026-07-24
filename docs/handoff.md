# BoomBoomFly 窗口交接

> 更新时间：2026-07-24T23:23:12+08:00
> 工作区：`/home/c/BoomBoomFly`
> 当前阶段：P0-03，**SOFTWARE FIXED / HARDWARE BLOCKED / FAIL-CLOSED**
> production：**DISABLED**

## 给新窗口的直接指令

```text
读取 /home/c/BoomBoomFly/docs/handoff.md。
保留四个第三方 dirty checkout，不 reset/clean/覆盖。
从“下一步”开始：先审阅 Offboard PR #1 与对应根 lock/docs PR，再在隔离
PX4 v1.16.2 源码/SITL 中准备并验证 rc_channels DDS topic firmware profile；
独立 DDS transport 需要维护者给出硬件选择并明确授权。未经明确授权，不写 PX4
参数、不刷固件、不 arm、不切 mode、不发送 setpoint/vehicle command，也不启动
Agent、Offboard 或视觉注入链路。
```

## 1. 当前仓库状态

| 项目 | 当前值 |
|---|---|
| 根仓库 | `/home/c/BoomBoomFly` |
| 根发布分支 / base | `agent/update-offboard-lock-docs` / `master@3b296de0` |
| 根工作树 | 本发布仅更新 Offboard lock 与状态文档 |
| Offboard origin | `https://github.com/BoomBoomFly/offboard_cpp.git` |
| Offboard HEAD | `agent/px4-v116-rc-safety@0c41de3cf8d56982bd67a5be56a9e281f3d9fc8f`，clean |
| Offboard 对齐 | 根 lock 已固定 `0c41de3e`；草稿 PR [#1](https://github.com/BoomBoomFly/offboard_cpp/pull/1) 待合并至 `DDS` |
| 旧 Offboard 备份 | 已按维护者要求永久删除；不存在备份 |

已仅恢复原先缺失的 exact checkout：

- `src/px4_msgs@392e831c1f659429ca83902e66820d7094591410` (`v1.16.2`)；
- `src/Micro-XRCE-DDS-Agent`，lock 为
  `57d086216d01ec43121845d385894a25987f8a2c` (`v2.4.2`)；
- `src/vision_to_dds`，lock 为
  `0c3a00137f3c90a4051ac1bc1029ec56beb669b6`。

全部 15 项经逐项只读核验，HEAD 与 origin 均匹配 lock。`librealsense`、
`navigation_msgs`、`realsense-ros`、`vision_opencv` 是保留的既有 dirty 仓库；
Offboard 修复已在独立分支提交并推送，其余 11 项 clean。

正式检查仍会 fail-closed，但现在会先完成整个 manifest 的只读审计：

```bash
bash Scripts/installation/uav_px4_dds_install.sh --verify-only --skip-package-check
```

当前结果为 `planned=15 verified=15 blockers=4`，退出状态码 1。四个 blocker
分别是按维护者要求暂不处理的 `librealsense`、`navigation_msgs`、
`realsense-ros` 和 `vision_opencv`；全部 HEAD 与 origin 仍匹配 lock。
命令没有 clone、fetch、checkout、更新 submodule 或覆盖任何既有仓库。完整记录见
[`evidence/OFFBOARD_PX4_MSGS_COMPAT_20260724.md`](evidence/OFFBOARD_PX4_MSGS_COMPAT_20260724.md)。

## 2. 实机 PX4 基线

所有数据通过 `/dev/ttyTHS0:921600` 只读获取。采集时飞控未解锁、已落地；
没有参数写入、切模、控制命令或刷写。

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

关键参数：

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

结论：当前 `/dev/ttyTHS0` 是 MAVLink TELEM2，不是可直接启动 serial Agent 的
独立 XRCE-DDS transport。若要改参数或端口，必须另开硬件维护审批。

尚缺：实际烧录 `.px4` artifact SHA-256，以及原构建目录的 clean/patch/
submodule 证据。实机 git hash只能确认二进制对应官方 release commit。

## 3. Companion 硬件枚举

| 设备 | 当前观察 |
|---|---|
| 主机 | NVIDIA Orin Nano Developer Kit，aarch64，kernel 5.10.104-tegra |
| PX4 UART | `/dev/ttyTHS0`，Jetson 平台 UART；用户 `c` 在 `dialout` |
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

决策已冻结：

- `/fmu/out/rc_channels` 保留为 Offboard 安全互锁的硬依赖；未来必须使用定制的
  PX4 v1.16.2 DDS firmware profile 导出该 topic。
- baseline 不要求 `/fmu/in/landing_target_pose`；`vision_to_dds` 默认
  `enable_precland=false`，关闭时不创建该 publisher。精降使用独立 profile。
Agent 配置无法凭空增加 firmware 未生成的 topic。
本轮没有构建/刷写 firmware，也没有修改 PX4 参数。

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

发布状态：Offboard 提交 `0c41de3e` 已推送至
`agent/px4-v116-rc-safety`，草稿 PR
[BoomBoomFly/offboard_cpp#1](https://github.com/BoomBoomFly/offboard_cpp/pull/1)
目标为 `DDS`。根 lock/docs 发布分支依赖该 PR，必须在 Offboard PR 合并后再合并。

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

按顺序执行：

1. 先审阅并合并 Offboard PR #1，再合并依赖它的根 lock/docs PR；保留四个第三方 dirty checkout。
2. 在隔离的 PX4-Autopilot v1.16.2 源码中为 DDS 输出加入 `rc_channels`，锁定
   firmware source/submodule/toolchain 与 artifact SHA-256；先做静态生成和 SITL。
3. 选择独立 DDS transport；当前 `/dev/ttyTHS0` 是 MAVLink TELEM2，禁止复用。
4. 根据所选 transport 明确 domain/端口，并验证与单机根 namespace `/` 契约。
5. 任何 PX4 参数写入、重启或刷固件前，必须取得维护者明确授权并准备回滚。
6. firmware/SITL 通过后才做 Agent 只读链路；不启动 Offboard 或视觉注入。
7. Offboard 继续经过 SITL、故障注入和 control-authority 安全门，再到拆桨台架。

当前硬阻塞：没有独立 DDS 物理 transport，实机仅暴露被 MAVLink 占用的 TELEM2；
参数快照仅发现 `UXRCE_DDS_CFG=0`。因此不能安全地自行指定串口/domain 或启动 Agent。
可继续的纯软件工作是准备 PX4 v1.16.2 topic patch、firmware 锁定证据和 SITL 测试；
硬件参数、刷写和串口占用必须串行且另行授权。

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
- [`README.md`](README.md)；
- [`CONTROL_AUTHORITY_MATRIX.md`](CONTROL_AUTHORITY_MATRIX.md)；
- [`adr/0001-dds-only-control-authority.md`](adr/0001-dds-only-control-authority.md)；
- 两份 `evidence/` 原始证据。

已删除八份被本 handoff 取代的旧状态报告：架构、构建、硬件、阶段任务、PX4
基线、仓库状态、风险清单、源码基线。旧 Offboard 备份也已永久删除。

本次另删除被 `.gitignore` 明确排除的可再生 `build/`、`install/`、`log/`，约
227 MB；验证结果已保存在 evidence，需要时可重新执行 colcon 生成这些目录。

最终验证应包括：

```bash
git diff --check
bash Scripts/installation/uav_px4_dds_install.sh --verify-only
git -C src/offboard_cpp status --short --branch
git status --short --branch
```

根基线 `3b296de0` 已在 `master`；Offboard `0c41de3e` 已推送并创建草稿 PR #1。本 lock/docs 更新在独立发布分支中。
