# G2 固件刷写与真实 RC/DDS 拆桨验证

时间：2026-07-29（Asia/Shanghai）
范围：仅刷写指定 FMUv3 固件，并执行 G2 的真实 PX4/RC/DDS/Agent 拆桨验证。
最终判定：**刷写 PASS；G2 FAIL/BLOCKED；禁止进入 G3–G5。**

## 安全边界

用户在操作前明确确认全部桨叶已拆除、机体固定、ESC 动力隔离，并明确批准刷写
`px4_fmu-v3_default.px4`（SHA-256
`e67291b15f982bb5028af8d7598e3236884045cd8f2b7ad7a81f75a16cff5fed`）及随后仅执行 G2。

本次没有启动 offboard、vision、mission_bridge 或 mock；没有发布 `/fmu/in/*`，没有发送
`VehicleCommand`，没有 Arm、电机动作、写参数、G3、G4 或 G5。

## 固件和回滚材料

| 项目 | 路径 | 大小 | SHA-256 | 判断 |
|---|---|---:|---|---|
| 刷写目标 | `/home/c/px4_ws/external/PX4-Autopilot/build/px4_fmu-v3_default/px4_fmu-v3_default.px4` | 1,900,443 | `e67291b15f982bb5028af8d7598e3236884045cd8f2b7ad7a81f75a16cff5fed` | 与授权值一致 |
| 用户提供备份 | `docs/px4_fmu-v3_default.px4`（未跟踪，未修改） | 1,900,443 | `e67291b15f982bb5028af8d7598e3236884045cd8f2b7ad7a81f75a16cff5fed` | 与目标逐字节同一身份 |
| 用户提供参数文件 | `docs/2026.7.29.params`（未跟踪，未修改） | 33,685 | `2c3b9c6ea6efa4e5fdbb25fa0edc3cd0261f883408b7ae10729ca8c52e1105b0` | 保留；不作为本轮写参依据 |

备份文件可以重新刷入同一目标固件，但因为它与目标哈希完全相同，不能证明能够恢复刷写前的
旧 DDS 行为。未执行回滚。

## 刷写结果

执行命令：

```text
python3 -u Tools/px_uploader.py --port /dev/ttyACM1 \
  build/px4_fmu-v3_default/px4_fmu-v3_default.px4
```

官方 uploader 识别 `board id 9,0`、STM32F42x，固件解包镜像 2,052,073 bytes；Erase、
Program、Verify 均达到 100%，随后执行 Reboot，进程退出码 0。原始 uploader 日志 SHA-256
为 `00fb0b046f8ba5c6c16a5246930904ff0941abef8538bcf6a387d231668ebfe1`；仓内仅保存脱敏摘要，
不保存硬件唯一序列号。

刷写后曾通过 `/dev/ttyACM0` 完整读取 974 个参数。完整临时 JSON 的 SHA-256 为
`522652317e3ddfd6d386a1b79473533619b0c45a62dd7b0ce1bf1dd5ee1f5617`。与 G2 串口直接相关的
实测值：

```text
MAV_1_CONFIG=0
UXRCE_DDS_CFG=102        # 本固件生成元数据：TELEM 2
SER_TEL2_BAUD=921600
UXRCE_DDS_DOM_ID=0
UXRCE_DDS_SYNCT=1
SYS_AUTOSTART=4001
EKF2_EV_CTRL=3
```

读取参数是只读诊断，没有执行参数写入。刷写后 USB 枚举为
`26ac:0011 / PX4 FMU v2.x`，与本地 FMUv3 NuttX 应用配置的产品 ID 和字符串一致。

## 唯一 Agent 与 DDS 结果

Agent 源码 SHA 为 `57d086216d01ec43121845d385894a25987f8a2c`；本地构建二进制：

```text
/tmp/boomboomfly_g2_agent/install/bin/MicroXRCEAgent
SHA-256 1a64daa54225a41c8e0e1f333481b7d9c4341c20939b1dce44b43e7ea45580b3
```

完整启动参数：

```text
MicroXRCEAgent serial -D /dev/ttyTHS0 -b 921600 -v 6
```

首次启动期间实测：

- Agent 进程恰好 1 个；
- `/dev/ttyTHS0` owner 恰好 1 个，且为该 Agent；
- 没有 offboard、vision、mission_bridge 或其他 PX4 控制节点；
- Agent 在电源循环后持续运行仍未收到 XRCE client，verbose 日志为 0 bytes；
- `ROS_DOMAIN_ID=0 ROS2CLI_NO_DAEMON=1 ros2 topic list -t` 只有
  `/parameter_events` 和 `/rosout`，没有任何 `/fmu/*`；
- USB MAVLink shell 同期也未在等待窗口内建立连接。

按用户要求重试串口后，唯一 Agent 成功创建 PX4 DDS 实体：

- `/fmu/out/rc_channels` 类型为 `px4_msgs/msg/RcChannels`，publisher 恰好为 1；
- publisher 是 PX4 经 Agent 创建的 bare DDS endpoint，QoS 为 BEST_EFFORT、TRANSIENT_LOCAL；
- `/fmu/in/offboard_control_mode`、`trajectory_setpoint`、`vehicle_command` 和
  `vehicle_visual_odometry` 均为 publisher 0、PX4 subscription 1；
- 实际 RC 为 18 通道、约 44 Hz、RSSI 41；主摇杆和多路拨杆均观察到实时变化，通道范围包含
  接近 `-1..1` 的行程；
- 同一 55 秒只读窗口记录 2,169 个 RC 样本和 49 个 timesync 样本；
- `signal_lost` 状态转换为 `true → false → true`，证明真实 RC 丢失和恢复可见；
- 但约第 49–50 秒后 RC 与 timesync 同时停止，复现此前会话的数据面冻结。该现象不是单独的
  RC topic timeout，因为独立的 timesync 也同步停止。

55 秒监视器 SHA-256 为
`56c67352558b2a7f6ddb70b3e26f8883850356e5e02542e075f9f0d4c5c47649`。三次 Agent verbose
日志均为 0 bytes；ROS 端实测计数和时间戳是本次稳定性判断的依据。

最终停止 Agent 后再次确认：Agent 0 个、`/dev/ttyTHS0` 无 owner、Domain 0 无 `/fmu/*`。

## G2 验收

| 条件 | 结果 |
|---|---|
| 指定 SHA 固件完成 Erase/Program/Verify/Reboot | **PASS** |
| 唯一 Agent、唯一串口 owner | **PASS（运行窗口）** |
| `/fmu/out/rc_channels` publisher 恰好为 1 | **PASS** |
| 类型为 `px4_msgs/msg/RcChannels` 且来自真实 PX4 | **PASS** |
| 实际摇杆/拨杆变化可见 | **PASS：18 通道，约 44 Hz** |
| RC 断开/恢复时 `signal_lost` 正确 | **PASS：观察到 true→false→true** |
| XRCE 数据持续性 | **FAIL：约 49–50 秒后 RC 与 timesync 同时停止** |
| 未经授权的 `/fmu/in/*` writer 为 0 | **PASS** |
| Agent 停止后 UART 释放 | **PASS** |

当前唯一硬阻塞是：**PX4 TELEM2 uXRCE-DDS client 与 Jetson `/dev/ttyTHS0` Agent 能建立链路，
但数据面在约 49–50 秒后冻结。** 在取得 PX4 端 `uxrce_dds_client status`/启动日志并证明
链路可持续运行前，不得把 G2 标记为 PASS。
