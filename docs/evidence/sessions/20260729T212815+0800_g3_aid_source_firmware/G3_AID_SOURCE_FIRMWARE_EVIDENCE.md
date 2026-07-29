# G3 EV aid-source 固件与真实融合补证

Session：`20260729T212815+0800_g3_aid_source_firmware`
日期：2026-07-29（Asia/Shanghai）
结论：**G3 PASS；整体继续 NO-GO，G4 未执行。**

## 安全边界

用户明确批准在全部桨叶已拆除、机体固定、ESC 动力隔离的条件下，增加两个只读 EKF
aid-source DDS 输出、构建并刷写固件，然后重新执行 G3。全程：

- `arming_state=1`（DISARMED），未出现其他 arming state；
- 没有发送 `VehicleCommand`，没有启动 offboard、mission bridge 或电机；
- 没有执行 PX4 参数写入；
- 仅在生产视觉窗口创建唯一 `/fmu/in/vehicle_visual_odometry` writer；
- 结束后四个关键 `/fmu/in/*` writer 均为 0，Agent 和 UART 均释放。

## 固件变更、构建与刷写

PX4 源码固定为 clean 提交：

```text
a8f2dbdfff4792c92f576060ab947f8e588d6f8b
uxrce_dds: publish EV estimator aid status
```

`dds_topics.yaml` 新增：

```text
/fmu/out/estimator_aid_src_ev_pos  px4_msgs/msg/EstimatorAidSource2d
/fmu/out/estimator_aid_src_ev_hgt  px4_msgs/msg/EstimatorAidSource1d
```

执行 `make px4_fmu-v3_default` 成功：

| 产物 | 大小 | SHA-256 |
|---|---:|---|
| `px4_fmu-v3_default.px4` | 1,901,211 bytes | `fa0fafe9ff25ec503498124631b2880c0255f02cd64394555fcf077a556a725b` |
| `px4_fmu-v3_default.bin` | 2,053,049 bytes | `1a8ac7c019ab781eb334417be1c4b839334e5b4e1f9fa896120ca7e77ccb83ab` |

链接结果为 flash 2,053,049 bytes / 2,032 KiB（98.67%），SRAM 29,348 bytes / 192 KiB。
工具链为 arm-none-eabi-gcc 9.2.1、CMake 3.16.3、Ninja
1.11.1.git.kitware.jobserver-1。

首次 uploader 从应用 `/dev/ttyACM0` 请求重启后，bootloader 重新枚举为 `/dev/ttyACM1`；
该节点又在第一次 erase 期间重新枚举，旧文件描述符停在 50%。确认新 `/dev/ttyACM0` 仍是
`PX4 BL FMU v3.x` 后终止失效 uploader，并对新节点完整重试。最终结果：

```text
board id 9,0 / STM32F42x
Erase 100%
Program 100%
Verify 100%
Reboot
exit code 0
```

刷写后应用重新枚举为 `26ac:0011 PX4 FMU v2.x`。脱敏过程见三个 flash 日志。

USB MAVLink 的刷写后完整参数列表请求未能稳定完成：一次收到 heartbeat 但 0 个参数，后续请求
没有 heartbeat。因此本 session 不宣称取得参数前后完整 diff。权威参数文件
`docs/2026.7.29.params` 的 SHA-256 仍为
`2c3b9c6ea6efa4e5fdbb25fa0edc3cd0261f883408b7ae10729ca8c52e1105b0`；它只作为已有输入，
没有被写回飞控。实际融合标志证明仅启用 EV position/height，没有启用 EV velocity/yaw。

## Domain 0 输入与端点

guard 使用精确 Agent SHA-256
`4cbc5038cb74391a8ecec3ed6cd94e588530cae937b5498d6796bf2c68433995`。新固件实测两个
aid-source publisher 均为 1，类型正确且来自 PX4；启动视觉前四个关键控制 writer 均为 0。

T265 身份与输入：

```text
serial=952322110550
firmware=0.2.0.951
RealSense ROS=4.0.4
librealsense=2.50.0
frame=odom_frame -> t265_pose_frame
pre-writer samples=999 / 5 s
rate=199.550 Hz
timestamp regressions=0
non-finite=0
```

实测外参 SHA-256 为
`42e48f773f771af91b2b3106b9a48ede6cc60fc29b0267157ae4c2f684f54295`；生产变换是
`t265_pose_frame -> base_link`，平移 `[-0.082,-0.015,0.108] m`，单位四元数。

## 首段 30 秒融合

质量连续稳定为 66、epoch=2 后显式 reset。结果：

| 项目 | 结果 |
|---|---|
| visual odometry | 578 样本；时间戳非递增 0；唯一 writer |
| EV position aid | 600 样本，19.999 Hz；600 fused；0 reject；0 非有限 |
| EV height aid | 600 样本，19.999 Hz；600 fused；0 reject；0 非有限 |
| `time_last_fuse` | position/height 均变化 599 次；倒退 0 |
| 最大水平 innovation | `[0.003191, 0.002213] m` |
| 最大水平 test ratio | `[9.519e-6, 4.580e-6]` |
| 最大高度 innovation/test ratio | `0.006944 m / 2.056e-5` |
| EKF 状态 | EV pos/hgt 全程 true；EV vel/yaw 全程 false；无位置拒绝 |
| local position | 全部 xy/z/vxy/vz valid；dead reckoning 全程 false |
| 飞行状态 | DISARMED；failsafe=false；无控制 writer |

## T265 断流与恢复

仅停止 T265 后的 15 秒窗口：visual odometry 0、quality=0、EV pos/hgt 全部 false、惯性推算
全部 true、XY/VXY 全部 invalid、Z/VZ 保持 valid；DISARMED、failsafe=false、控制 writer 为 0。
aid-source 各出现的 1 个 `fused=true` 样本是 TRANSIENT_LOCAL 缓存值；当前融合状态以 16 个连续
`estimator_status_flags` 样本为准，全部显示 EV 已退出。

重启后 5 秒复位前窗口得到 1,000 个 odometry 样本、quality=66、epoch 从 2 变为 3，但 visual
odometry 仍为 0，EV 融合仍关闭，证明新 epoch 不会自动解锁旧 session。显式 reset 后第二个
30 秒窗口：

- visual odometry 600 样本，reset counter=2，时间戳非递增 0；
- position/height aid 各 600 样本、全部 fused、0 reject、0 非有限；
- 两个 `time_last_fuse` 均变化 599 次、倒退 0；
- 最大水平 test ratio `[3.063e-6,5.815e-6]`，最大高度 test ratio `2.901e-6`；
- EV pos/hgt 全程 true，EV vel/yaw 全程 false，local position 全有效且非 dead reckoning；
- DISARMED、failsafe=false、控制 writer 为 0。

## 释放与判定

按视觉桥、T265、Agent 顺序停止。结束后 10.012 秒内采样 20 次，四个关键输入 writer 的
最大值和最终值均为 0。相关进程 0、UART owner 0；本次 boot 没有 UART/DMA 错误匹配。

G3 的 estimator flags、aid source、fused/rejected、innovation、innovation variance、test ratio、
`time_last_fuse`、local position、reset counter、断流与恢复证据均已取得，故 **G3 PASS**。
G4 尚未授权或执行；整体继续 **NO-GO**，禁止装桨飞行。
