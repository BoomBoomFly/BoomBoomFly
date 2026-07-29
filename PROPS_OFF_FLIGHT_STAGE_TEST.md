# 普通飞行阶段拆桨验证卡（未来操作，未执行）

状态：**BLOCKED / NOT AUTHORIZED / NOT RUN**。本卡不授权刷写、写参数、Domain 0 输入 writer、
Offboard、Arm、Land、Disarm、Kill 或电机动作。每个有状态改变的步骤都必须由用户对当次动作
另行明确批准。G2 未 PASS 前不得进入 G3，G3 未 PASS 前不得进入 G4。

## G2：刷写后真实 RC/DDS 验证

刷写前停止并记录：

1. 拆除全部桨叶，两人确认；机体固定，ESC 动力隔离，准备独立硬断电。
2. 重新记录当前参数导出及 SHA-256、`ver all`、飞控板型、当前运行固件、目标固件和原固件
   回滚产物 SHA-256。任一无法校验即停止。
3. 只允许一个已识别的 Micro-XRCE-DDS Agent 使用飞控串口；刷写前停止所有
   `/fmu/in/*` writer。
4. 用户明确批准“刷写指定 SHA-256 的 FMUv3 固件”后，才由现场操作者执行刷写。Codex
   本阶段不代执行。

刷写并重启后，先只读验证：

- `/fmu/out/rc_channels` publisher 恰好为 1，类型为 `px4_msgs/msg/RcChannels`，端点来自真实 PX4。
- 实际摇杆和指定拨杆的值、通道号、阈值和边沿与生产 YAML 一致；禁止猜测默认通道。
- 关闭遥控/断开接收机后，`signal_lost` 和 topic timeout 均按真实链路出现；不得注入 mock RC。
- Agent 实例和串口 owner 均恰好为 1；没有旧 Agent、串口争用或第二 Domain 0 participant。
- `/fmu/in/offboard_control_mode`、`trajectory_setpoint`、`vehicle_command`、
  `vehicle_visual_odometry` 在未批准生产启动时 publisher 均为 0。

必须保存原始 `ros2 topic info -v`、`type`、`hz`、带时间戳的有限 echo、进程清单、串口 owner、
刷写工具输出、重启后 `ver all` 和全部文件哈希。任何数量、类型、来源、时间戳或 loss 语义不符，
G2 为 FAIL 并按已验证原固件回滚流程停止。

## G3：T265 与 EKF（仅 G2 PASS 后）

1. 实测并复核 `odom_frame → t265_pose_frame → base_link` 外参；模板中的 TBD 不得带入生产。
2. 先验证静止、前、右、上、顺时针偏航的符号、尺度、时间戳、质量和 source epoch；断流、
   冻结、回退、重连均须 fail closed。
3. 保存修改前完整参数和 SHA-256。不得直接从 `EKF2_EV_CTRL=15` 开始；第一组只启用已验证的
   位置分量。每组写后重新导出并 diff，单独验证和回滚。
4. 保存 `estimator_status_flags`、相应 estimator aid source、`fusion_enabled/fused`、innovation/
   test ratio、`time_last_fuse`、`vehicle_local_position`、reset counter，以及视觉断流/恢复时间线。

只有 ROS writer 或 odometry 数据存在不等于 EKF 接受视觉。

## G4：拆桨失效（仅 G3 PASS 后）

逐项、单独授权并记录：RC 丢失、Offboard 丢失、T265 冻结、T265 断流、Agent 退出、ACK
拒绝/超时、kill、低电和围栏。每项都以 PX4 实际 `vehicle_status_v1`、arming state、failsafe、
land detector、ACK 和 ULog 结果验收，不能依据参数值推断。测试中出现未批准的 mode、Return、
电机输出、writer、时间倒退或 estimator reset 时立即停止并断开生产 writer。

