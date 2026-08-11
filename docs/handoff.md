---
title: BoomBoomFly 当前交接
status: phase-1-sitl-partially-validated
updated: 2026-08-11
---

# BoomBoomFly 当前交接

这是当前工作的唯一交接入口。优先级为：当前用户确认的任务与硬件约束 > 本文 >
[统一技术路线](BoomBoomFly_统一技术路线.md) > 历史资料与旧代码。

## 当前目标

第一阶段仅验证最小飞行闭环：观察一次 PX4 未解锁 → 等待 EKF2 本地定位健康 → RC 解锁上升沿
→ Offboard → 相对本地 home 起飞 1.5 m → 悬停 60 s → 返回 home → Land。

目标追踪、投放、串口 START、实机飞行均不在当前范围。

## 当前实现

| 范围 | 已实现边界 |
|---|---|
| `common` | `boomboom_common` 的 C99 core 和 ROS 2 转换层；core 不依赖 ROS、PX4、Linux、HAL、动态内存、文件系统或 UART。 |
| `offboard_cpp` | 单个 20 Hz `offboard_mission_node`，内部为 `MissionController + Px4Interface`，是三个生产 PX4 控制输入的唯一 writer。 |
| `px4_vision_bridge` | `nav_msgs/Odometry → VehicleOdometry → DDS`；负责坐标、时间、协方差和输入健康。 |
| `communication` | 保留独立仓库边界；第一阶段没有运行节点或协议。 |
| `px4_bringup` | SITL/hardware launch 与分层参数；只编排进程和节点，不承载任务状态机。 |

PX4 与 `px4_msgs` 固定为 v1.16.2，Micro XRCE-DDS Agent 为 v2.4.2。PX4 v1.16 的状态话题使用
`/fmu/out/vehicle_status_v1`。

## 必须保持的行为

- 先观察一次 `DISARMED`；只有 `STICK_GESTURE` 或 `RC_SWITCH` 的解锁上升沿能启动任务。
- 程序不发送 ARM、DISARM 或 Kill；Kill、人工接管和 Offboard 退出由 RC/PX4 决定。
- 飞行反馈只使用 PX4 EKF2 的 `VehicleLocalPosition`；定位失效时原地请求 Land，不盲目返航。
- 进入 Offboard 前，以 20 Hz 预发送至少 1 s，并同时等待匹配 ACK 和实际 `nav_state == OFFBOARD`。
- home 在启动沿冻结；坐标 reset 同步修正 home 和目标；用户或 PX4 使系统退出 Offboard 后不抢回控制权。
- `/offboard/cancel_mission`（`std_srvs/srv/Trigger`）仅在 `HOVER` 接受；随后返回冻结本地 home 并 Land。Land 请求后不可取消，RC 接管、failsafe 与定位失效优先。
- vision bridge 仅在 `TimesyncStatus` 新鲜且输入有效时写入 PX4；任务控制不绕过 EKF2 使用原始 VIO。

## 已有证据

- Humble 工作区已构建 `px4_msgs`、`boomboom_common`、`px4_vision_bridge`、`offboard_cpp` 和 `px4_bringup`；相关 CTest 通过。返航取消新增状态机测试和限定 `offboard_cpp` 构建也已通过。
- Humble `gz_x500` 中，真实 RC 解锁沿已完成 Offboard、1.5 m 起飞、约 60 s 悬停、返回、Land 与解除解锁；程序未发送 ARM、DISARM 或 Kill。
- 外部 ARM 不触发任务；人工切出 Offboard、mission node 退出、以及仅中断 Offboard 心跳时，PX4 接管且 mission 不重抢控制权。
- mission 的本地位置订阅副本断流后，约 238 ms 请求 Land；PX4 接受并完成落地。此证据只覆盖 mission 输入断流，不替代真实 VIO、bridge 或 EKF2 失效。
- 静止合成 `/vision/odometry` 已在未解锁 SITL 被 EKF2 融合；它不代表真实 VIO，且不得在飞行中继续发布。
- Offboard ACK timeout 与拒绝 ACK 的 mission 分支已通过注入验证；PX4 原生模式拒绝已见到，但不是 mission 自身 Offboard 请求的原生拒绝。
- 在 HOVER 调用 `/offboard/cancel_mission` 已完成 SITL 验证：服务成功返回，mission 记录 `RETURN_HOME` 与 `CANCELLED` 原因，随后返航、PX4 接受 Land 命令、收到新的 `landed = true` 样本并解除解锁。状态、事件、ACK 和落地样本已录入独立 rosbag。
- 在 PX4 已解除解锁且无飞行任务时完成一次受控 Micro XRCE-DDS Agent 重连；新 session 建立后 `TimesyncStatus` 恢复为 DDS source，连续样本间隔约为 1.004–1.008 s。本次只证明重连后的恢复，不推断时间域异常根因。

## 未验证与停止条件

- mission 自身 Offboard 请求的 PX4 原生拒绝 ACK，以及 ACK 接受但 `nav_state` 未进入 Offboard 的 timeout。
- `TimesyncStatus` 周期性 ROS epoch/PX4 boot 时间域切换的根因；受控重连后已恢复 DDS 样本，但缺少同一异常前的连续基线，尚不能与自然 time-jump 对比。
- 真实 VIO 的动态、延迟、reset、外参与 EKF2 稳定性；Jetson Orin Nano / Foxy 构建和无桨联调。
- 所有实机解锁、Kill、人工接管、系留和受控飞行步骤。

任一实机前停止条件未通过，均不得进入自主飞行；Humble SITL 结果不能推断 Foxy、Jetson 或 Pixhawk
2.4.8 已通过。

## 下一工作窗口

1. 为自然 time-jump 建立连续的 `TimesyncStatus` 基线，再与已完成的受控 Agent 重连样本比较，定位时间域异常根因。
2. 为 mission 自身的 PX4 原生 Offboard 拒绝和 state-timeout 分别采集匹配 ACK、原始 `nav_state`、mission state/event 与 ulog。
3. 真实 VIO 与 Foxy/Jetson 无桨地面联调通过后，才可按[实机门禁](第一阶段实机门禁清单.md)推进。
