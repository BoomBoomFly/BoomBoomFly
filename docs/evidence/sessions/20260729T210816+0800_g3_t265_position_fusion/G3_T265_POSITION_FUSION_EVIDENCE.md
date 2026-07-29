# G3 T265 位置融合拆桨实测证据

Session：`20260729T210816+0800_g3_t265_position_fusion`

日期：2026-07-29（Asia/Shanghai）

## 范围与安全边界

用户明确授权在全部桨叶已拆除、机体固定、ESC 动力隔离的条件下，通过 guard 启动唯一
Micro XRCE-DDS Agent，并在真实 ROS Domain 0 创建唯一
`/fmu/in/vehicle_visual_odometry` writer，验证 T265 位置融合、断流和恢复。

本 session：

- 没有 Arm；
- 没有发送 `VehicleCommand`；
- 没有启动 offboard、mission bridge 或电机；
- 没有写 PX4 参数；
- 没有启用视觉速度或航向融合；
- 没有进入 G4 或 G5。

## 锁定输入

```text
T265 serial: 952322110550
T265 firmware: 0.2.0.951
RealSense ROS: 4.0.4, exact source 8abb4657c0add15f87b0edbfb67eaba2c1c2c439
librealsense runtime: 2.50.0
vision_to_dds: 470cf59cf8fbcddd17b12e9d31f084e87f5f2fac
Agent SHA-256: 4cbc5038cb74391a8ecec3ed6cd94e588530cae937b5498d6796bf2c68433995
measured extrinsics SHA-256: 42e48f773f771af91b2b3106b9a48ede6cc60fc29b0267157ae4c2f684f54295
parameter snapshot SHA-256: 2c3b9c6ea6efa4e5fdbb25fa0edc3cd0261f883408b7ae10729ca8c52e1105b0
```

实测外参为 `t265_pose_frame -> base_link`：

```text
translation_m: [-0.082, -0.015, 0.108]
rotation_xyzw: [0, 0, 0, 1]
```

参数快照记录 `EKF2_EV_CTRL=3`，即只启用水平和垂直位置；`EKF2_EV_QMIN=50`，
`EKF2_HGT_REF=3`，`EKF2_EV_POS_{X,Y,Z}=0`。外参已在伴随计算机变换到
`base_link`，因此 PX4 传感器位置偏移保持零，避免重复补偿。本 session 没有执行
`param set`；结束时快照哈希保持不变。USB CDC 没有 MAVLink heartbeat，也不响应只读
NSH `param show`，因此没有把旧快照冒充成实时参数回读。实际融合标志用于验证有效配置。

## 启动前门禁

guard preflight PASS：

```text
ROS_DOMAIN_ID=0
serial=/dev/ttyTHS0
baud=921600
Agent exact SHA matched
MemAvailable=2403636 KiB
DMA free-above-high=1344780 KiB
```

Agent 建链后连续 10 秒审计全部 `/fmu/in/*` publisher 为 0。T265 writer 启动前 5 秒：

```text
samples=998
rate=199.548 Hz
frame=odom_frame
child=t265_pose_frame
timestamp regressions=0
invalid samples=0
visual writer count=0
```

## 正常位置融合

T265 的启动瞬间低置信度样本使视觉桥按设计锁存 `QUALITY_LOW`，writer 端点存在但输出
样本为 0。质量稳定为 66、source epoch 为 2 后，显式调用
`/vision_to_dds_node/reset_fault`；服务返回成功，完成双 TF 样本预热后才开始输出。

首段 30 秒结果：

```text
visual output: 600 samples, 19.999 Hz
output timestamp non-increasing: 0
quality: 66
source epoch: 2
writer count: exactly 1
VehicleCommand/Offboard/TrajectorySetpoint writers: 0

cs_ev_pos=true
cs_ev_hgt=true
cs_ev_vel=false
cs_ev_yaw=false
cs_inertial_dead_reckoning=false
horizontal/vertical position reject samples=0
innovation_fault_status_changes remained 195

vehicle_local_position:
  xy/z/vxy/vz valid for 2992/2992 samples
  dead_reckoning=false
  final NED position=[-0.0188, -0.0807, -0.1104] m

arming_state=DISARMED
failsafe=false
```

## T265 断流和恢复

受控停止 T265 后，视觉桥报告 `INPUT_TIMEOUT` 并停止输出。15 秒断流窗口：

```text
visual output samples=0
quality=0
cs_ev_pos=false
cs_ev_hgt=false
cs_ev_vel=false
cs_ev_yaw=false
cs_inertial_dead_reckoning=true
vehicle_local_position xy/vxy invalid, z/vz valid
VehicleCommand writer=0
arming_state=DISARMED
failsafe=false
```

重启 T265 后：

```text
quality=66
source epoch: 2 -> 3
visual output before reset=0
PX4 EV fusion before reset=false
```

这证明新 epoch 不会自动解锁旧 session。稳定后再次显式 reset，第二段 30 秒恢复结果：

```text
visual output: 600 samples, 19.999 Hz
output timestamp non-increasing: 0
output reset_counter=2
cs_ev_pos=true
cs_ev_hgt=true
cs_ev_vel=false
cs_ev_yaw=false
position reject samples=0
vehicle_local_position all validity flags=true
dead_reckoning=false
arming_state=DISARMED
failsafe=false
VehicleCommand writer=0
```

## 未满足的 G3 证据

当前刷入固件的 `dds_topics.yaml` 只导出
`/fmu/out/estimator_status_flags`，没有导出 `estimator_aid_src_ev_pos` 或 estimator
innovations。Domain 0 实际话题清单也没有这些端点。因此本 session 无法取得：

- EV aid source 的逐轴 innovation；
- innovation test ratio；
- `time_last_fuse`。

不能用 `cs_ev_pos/cs_ev_hgt` 或 reject 标志冒充上述证据。补齐它们需要一个额外、明确授权的
证据通道，例如保存包含这些 uORB 主题的 ULog，或修改 DDS 输出清单、重建并另行批准刷写。

## 最终释放与结论

按顺序停止视觉桥、T265 和 Agent。结束后：

```text
Domain 0 writer audit: PASS, 20 samples over 10 seconds
/fmu/in/offboard_control_mode=0
/fmu/in/trajectory_setpoint=0
/fmu/in/vehicle_command=0
/fmu/in/vehicle_visual_odometry=0
related processes=0
/dev/ttyTHS0 owners=0
current-boot UART/DMA matched errors=0
```

G3 结论为 **PARTIAL PASS / BLOCKED**：真实 T265 位置融合、融合退出、epoch 防重放和人工复位恢复
均通过；但强制要求的 aid-source innovation/test-ratio/time-last-fuse 证据缺失。不得进入 G4，
不得声称可以装桨飞行。
