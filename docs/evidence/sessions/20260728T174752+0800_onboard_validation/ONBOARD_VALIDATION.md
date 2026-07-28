# 机载技术验证（2026-07-28）

本记录只保留影响 DDS Offboard、T265 视觉定位和室内试飞判断的技术结果。
会话终端转录、重复交接稿、临时补丁和旧 `.repos` 快照已删除；当前依赖身份
只以仓库根目录的 `workspace.lock.repos` 为准。

## 软件与运行环境

| 组件 | 实测结果 |
|---|---|
| 机载计算机 | Ubuntu 20.04.6 LTS，aarch64，Orin Nano |
| 飞控板 | Pixhawk 2.4.8（现场提供）；PX4 `board target` 尚未读取确认 |
| ROS / RMW | ROS 2 Foxy，`rmw_fastrtps_cpp` 1.3.2 |
| RealSense apt SDK | 2.56.5 |
| RealSense 本地 SDK | 2.50.0 |
| RealSense ROS wrapper | 4.0.4，链接本地 2.50.0 SDK |
| Micro XRCE-DDS Agent | v2.4.2 |
| Fast DDS | v2.12.2 |

`vision_to_dds` 的锁定版本完成构建和测试。完整 DDS 工作区构建成功；
`offboard_cpp` 和视觉测试通过。`px4_msgs` 的生成 Python uncrustify 结果文件
仍有一个与控制逻辑无关的测试错误。

## T265 与 D435

| 检查 | T265 | D435 |
|---|---|---|
| 设备 | Intel RealSense T265，FW 0.2.0.951 | Intel RealSense D435，FW 5.13.0.50 |
| 流 | 6DOF pose 约 180–200 Hz | depth/color 640x480@30 |
| ROS topic | `/t265/pose/sample` 约 199.54 Hz | 相机检查约 30 Hz |
| TF | `odom_frame -> t265_pose_frame` 约 199.55 Hz | 不进入当前 PX4 定位链 |
| 时间戳 | odom/TF 严格递增；中位延迟约 6.3/6.6 ms | depth 曾出现少量重复/回退时间戳 |
| 重连 | 两轮释放和重新枚举成功 | 两轮释放和重新枚举成功 |
| 外参 | T265 到机体的旋转和平移未知 | 无机体位姿契约 |

双相机同时运行 12 秒时，T265 约 174.75 Hz，D435 深度和彩色约
30.33 Hz；两者均能完整释放设备。

## 视觉 DDS 契约

T265 驱动提供 `/t265/pose/sample` 和动态 TF，但不提供
`/vision/source_epoch` 或 `/vision/quality`。锁定的
`t265_health_adapter_node` 提供：

| Topic | 类型 / QoS | 行为 |
|---|---|---|
| `/vision/source_epoch` | `std_msgs/msg/UInt32`; KeepLast(1), BEST_EFFORT, VOLATILE | 启动和重连边界递增 |
| `/vision/quality` | `std_msgs/msg/Int8`; KeepLast(1), BEST_EFFORT, VOLATILE | 20 Hz；无源为 0；协方差映射到跟踪质量 |

单元测试覆盖正常输入、冻结、重连、时间戳回退和质量映射。机载 ROS 图已观察
到适配器连接，但尚未用真实运动和遮挡捕获完整的质量下降与 epoch 变化。

## PX4 DDS 输出

一个 Agent 通过 `/dev/ttyTHS0`、921600 baud 连接。检查期间没有第二条飞控传输、
第二个 Agent、旧 bringup、`/fmu/in/*` writer 或串口竞争进程。

| Topic | 发布者 | 实测频率 | 时间 |
|---|---:|---:|---|
| `/fmu/out/vehicle_status_v1` | 1 | 1.97 Hz | 中位延迟 21.27 ms |
| `/fmu/out/rc_channels` | 0 | 缺失 | 无样本 |
| `/fmu/out/battery_status` | 1 | 92.53 Hz | 中位延迟 10.89 ms |
| `/fmu/out/vehicle_odometry` | 1 | 66.84 Hz | 中位延迟 12.16 ms |
| `/fmu/out/vehicle_land_detected` | 1 | 0.99 Hz | 中位延迟 12.74 ms |
| `/fmu/out/vehicle_command_ack` | 1 | 事件 topic | 无命令期间无样本 |
| `/fmu/out/timesync_status` | 1 | 0.99 Hz | RTT 约 9.3 ms |

检查到的 27 个 `/fmu/in/*` endpoint 均没有 ROS publisher。Agent 停止后，
串口 owner 和 `/fmu/*` 图均消失。

## 当前技术缺口

1. PX4 参数快照显示 `EKF2_EV_CTRL=0`，外部视觉尚未进入 EKF2。
2. T265 到机体的旋转、平移和坐标轴约定尚未测量验证。
3. 真实遮挡、快速运动、冻结和重连下的 quality/epoch 行为尚未闭环。
4. `/fmu/out/rc_channels` 在当前 DDS 图中缺失。
5. Offboard 丢失、RC 丢失、定位丢失和低电量的室内动作尚未验证。
6. 正式 PX4 DDS SITL、拆桨台架和有限运动包线尚未完成。

PX4 固件、机架和参数细节见同日的
[PX4 参数审计](../20260728T213311+0800_px4_parameter_audit/PX4_PARAMETER_AUDIT.md)。

## 保留的技术数据

| 文件 | 内容 |
|---|---|
| `artifacts/environment.latest.json` | 机载环境与版本 |
| `artifacts/d435_frames.csv` | D435 单机帧数据 |
| `artifacts/dual_d435_frames.csv` | 双相机运行帧数据 |
| `artifacts/px4_output_metrics.json` | PX4 DDS 输出频率与时间指标 |

这些文件是 2026-07-28 的测量记录，不替代当前运行时检查。
