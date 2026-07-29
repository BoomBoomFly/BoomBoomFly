# 普通飞行阶段拆桨验证卡与执行状态

状态：**G2 PASS / G3 PASS / G4 部分执行且仍 BLOCKED**。用户已明确授权两次固件刷写、G2 拆桨
验证、G3 真实 Domain 0 视觉位置融合、G4 breaker A1，以及 G4-A2 真实 RC 丢失/恢复和 Agent
退出。真实 RC、UART DMA 门禁、干净 boot 620 秒 soak、实测外参、EV position/height aid-source、
innovation/test ratio/time_last_fuse、视觉断流恢复、breaker 写后持久化和 RC loss ground/disarmed
响应均取得真实证据。未授权后续刷写、写参数、Offboard、Arm、Land、Disarm、Kill 或电机动作。
其余 G4 场景仍须逐项取得明确授权。

## G2：刷写后真实 RC/DDS 验证

2026-07-29 当次执行结果：

- 指定固件 Erase/Program/Verify/Reboot PASS；
- 唯一 Agent 和唯一 `/dev/ttyTHS0` owner PASS；
- `/fmu/out/rc_channels` publisher=1、类型正确、约 44 Hz，18 通道真实变化 PASS；
- RC `signal_lost` 丢失/恢复转换 PASS，关键 `/fmu/in/*` publisher=0 PASS；
- XRCE 数据面约 49–50 秒后冻结，RC 与 timesync 同时停止；后续内核诊断确认 Jetson 低内存
  导致 `/dev/ttyTHS0` UART RX DMA descriptor 分配失败；
- 临时暂停开发语言服务、将 available memory 提升至约 1.3 GiB 后，120 秒 RC/timesync 对照
  PASS 且内核无新增分配错误；随后生产门禁和干净启动 soak 已验收；
- 后续 Agent 只允许经 `Scripts/runtime/px4_dds_agent_guard.py` 启动；门禁默认要求
  MemAvailable 至少 1024 MiB、DMA free-above-high 至少 256 MiB，并拒绝开发语言服务；
- 新 boot `3268e759-5043-48a8-92ae-44afb959ae95` 下完成 620.011 秒只读 soak：RC
  44.364 Hz、timesync 0.990 Hz，最大间隔分别 57.0 ms 和 1.033 s；时间戳倒退 0，125 次
  图检查的输入/输出 writer 违例 0，本次 boot 内核 page-allocation/UART RX descriptor 错误 0；
- soak 最低 MemAvailable 2,266,704 KiB，最低 DMA free-above-high 271,228 KiB，均高于门限；
- Agent 已停止且 UART 已释放；
- 刷写/RC、UART DMA 根因和生产门禁证据分别见
  `docs/evidence/sessions/20260729T174904+0800_g2_flash_rc_dds`、
  `docs/evidence/sessions/20260729T183138+0800_g2_uart_dma_diagnostic` 和
  `docs/evidence/sessions/20260729T190953+0800_agent_memory_guard`；干净 boot soak 见
  `docs/evidence/sessions/20260729T195311+0800_g2_clean_boot_soak`。

后续重新执行 G2 前停止并记录：

1. 拆除全部桨叶，两人确认；机体固定，ESC 动力隔离，准备独立硬断电。
2. 重新记录当前参数导出及 SHA-256、`ver all`、飞控板型、当前运行固件、目标固件和原固件
   回滚产物 SHA-256。任一无法校验即停止。
3. 只允许一个已识别的 Micro-XRCE-DDS Agent 使用飞控串口；刷写前停止所有
   `/fmu/in/*` writer。
4. 如果诊断需要再次刷写、回滚或写参数，必须重新取得对应当次动作的明确批准。

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

2026-07-29 G3 已完成并 PASS。新固件导出 EV position/height aid-source；两段各 30 秒真实融合
均取得 600 个 position 和 600 个 height aid 样本，全部 fused、0 reject、0 非有限，
`time_last_fuse` 连续递增且无倒退，test ratio 远低于 1。T265 断流后视觉输出为 0、EV 融合退出、
PX4 进入惯性推算；恢复后 source epoch 从 2 变为 3，显式 reset 前不自动输出，reset 后融合恢复。
全程零参数写入、零 VehicleCommand、DISARMED、无电机动作。完整证据见
`docs/evidence/sessions/20260729T212815+0800_g3_aid_source_firmware`。刷写后 USB MAVLink 完整参数
列表未稳定重导出，因此没有把已有参数文件冒充实时 diff；真实 estimator flags 证明仅融合位置和
高度，未融合速度或航向。

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

2026-07-29 G4-A2 结果：RC 在线→丢失→恢复由 `RcChannels.signal_lost` 和
`FailsafeFlags.manual_control_signal_lost` 双重确认；可观察窗口内 PX4 始终 DISARMED、POSCTL、
`failsafe=false`、landed，五类时间戳倒退 0，104 次图检查的 `/fmu/in/*` writer 违例 0，RC
ground/disarmed 场景 PASS。Agent Ctrl-C 后数据停止且五个 publisher 在 DDS 租约到期后变为 0；
重连后直接读取状态仍为 DISARMED/POSCTL/non-failsafe/landed，RC 恢复在线，最终 Agent/串口释放。

但 Agent 退出同时切断唯一观测链；`SDLOG_MODE=0` 且本次从未 Arm，因此 gap 内没有 ULog 可证明
PX4 内部 mode/failsafe/Land。Agent 数据面断流/恢复 PASS，gap 内行为补证仍 BLOCKED，不得把
publisher 消失写成已经验证的 PX4 failsafe/Land。完整证据见
`docs/evidence/sessions/20260729T232726+0800_g4_a2_rc_agent_loss`。
