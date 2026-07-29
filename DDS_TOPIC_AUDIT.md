# DDS 与 PX4 输出审计

审计时间：2026-07-29（Asia/Shanghai）
判定：**H1 BLOCKED**。本轮没有启动 Agent、没有发送 `/fmu/in/*`、没有 Arm 或启动电机。

## 证据范围与身份

- 当前实时快照：2026-07-29，设备处于静止、无 Agent/飞控 ROS 节点状态。
- 历史实机采样：仓库内 2026-07-28 evidence；它能说明当时的链路表现，不能代替今天的复测。
- PX4 源码：`external/PX4-Autopilot`，干净 HEAD
  `54f0455ffcd755534539a7cf33a09a20bf71d29d`，tag `v1.16.2`。
- 运行版本历史记录：Pixhawk 2.4.8、`PX4_FMU_V3`、PX4 v1.16.2。
- 参数快照 SHA-256：
  `f669480ed8fd3f8066a6ab3132667a4be5a13dce956f7f23139efeff409222ce`。
- `dds_topics.yaml` SHA-256：
  `8b2999386e0d8a384fdf014106273c3cf8fa310c98746148e3f205c9b5ffb7fe`。
- 根仓库 evidence index 当前没有可验证条目；所以下表明确区分“当前快照”和“历史采样”。

## 当前 Agent、串口和 ROS 图

| 检查项 | 当前结果 | 判定 |
|---|---|---|
| Micro-XRCE-DDS Agent 进程 | 0 个 | 安全静止态；不是 H1 运行态 |
| PX4/offboard/vision ROS 进程 | 0 个 | H0 当前快照无生产 writer |
| `/dev/ttyTHS0` owner | 无进程持有 | 无串口竞争 |
| 设备权限 | `root:dialout`, `0660` | 启动用户仍需属于 `dialout` |
| shell `ROS_DOMAIN_ID` | 未设置，即 ROS 2 默认 0 | 建议运行命令显式固定为 0 |
| PX4 `UXRCE_DDS_DOM_ID` | 0（参数快照） | 与目标一致 |
| `ros2 topic list --no-daemon -t` | 仅 `/parameter_events`、`/rosout` | 当前没有 `/fmu/out/*` |
| `ros2 node list --no-daemon` | 空 | 当前没有活节点 |
| `MicroXRCEAgent --version` | 当前 PATH 中找不到命令 | Agent v2.4.2 的可执行文件/来源未纳管 |

一次较早的 daemon 查询曾返回残留 vision topic 名称，但无对应节点或进程。最终以
`--no-daemon` 的空节点、无 `/fmu/*` 快照为准；正式测试必须继续使用 no-daemon 查询，
避免把 discovery cache 当作实机 publisher。

仓库没有保存能够证明“只启动一个 Agent”的 systemd unit 或精确启动脚本。官方串口形式的
候选命令是：

```bash
MicroXRCEAgent serial --dev /dev/ttyTHS0 -b 921600
```

这只是后续 H1 拆桨测试的命令草案，本轮未执行。启动前必须记录可执行文件绝对路径、
`--version`、二进制 SHA-256、运行用户、PID、完整 argv，并通过 `lsof`/`fuser` 证明它是
唯一串口 owner；所有 ROS 检查进程显式使用 `ROS_DOMAIN_ID=0`。

## 历史 `/fmu/out/*` 重点采样

以下数据来自 2026-07-28 的实机 evidence，不代表当前在线状态。频率是采样窗口观测值，
不是接口保证值。

| Topic | ROS 类型 | publisher | 样本/频率 | PX4 stamp | 结论 |
|---|---|---:|---|---|---|
| `/fmu/out/rc_channels` | `px4_msgs/msg/RcChannels` | **0** | 0 / 无 | 无 | **BLOCKED** |
| `/fmu/out/vehicle_land_detected` | `px4_msgs/msg/VehicleLandDetected` | 1 | 10 / 0.991 Hz | 严格递增；中位延迟 12.740 ms | 历史 PASS |
| `/fmu/out/vehicle_command_ack` | `px4_msgs/msg/VehicleCommandAck` | 1 | 0 / 事件型 | 本轮未发命令，无法验证 | publisher 可见；行为未验证 |
| `/fmu/out/vehicle_status_v1` | `px4_msgs/msg/VehicleStatus` | 1 | 20 / 1.972 Hz | 严格递增；21.270 ms | 历史 PASS |
| `/fmu/out/vehicle_odometry` | `px4_msgs/msg/VehicleOdometry` | 1 | 669 / 66.844 Hz | 严格递增；12.161 ms | 历史 PASS |
| `/fmu/out/timesync_status` | `px4_msgs/msg/TimesyncStatus` | 1 | 10 / 0.987 Hz | 严格递增；12.677 ms | RTT 约 9.3 ms，历史 PASS |
| `/fmu/out/battery_status` | `px4_msgs/msg/BatteryStatus` | 1 | 926 / 92.528 Hz | 严格递增；10.889 ms | 历史补充证据 |

精确 PX4 v1.16.2 源码中的 `/fmu/out` DataWriter QoS 为
`BEST_EFFORT + TRANSIENT_LOCAL + KEEP_LAST`，生成配置的深度参数为 0。该项是源码证据；
历史 evidence 没有保留每个运行端点的完整 QoS dump，H1 复测必须用
`ros2 topic info -v` 再记录实际 publisher/subscriber 兼容性。

源码 `dds_topics.yaml` 配置的 24 个输出是：

```text
register_ext_component_reply  arming_check_request  mode_completed
battery_status  collision_constraints  estimator_status_flags
failsafe_flags  manual_control_setpoint  message_format_response
position_setpoint_triplet  sensor_combined  timesync_status
vehicle_land_detected  vehicle_attitude  vehicle_control_mode
vehicle_command_ack  vehicle_global_position  vehicle_gps_position
vehicle_local_position  vehicle_odometry  vehicle_status
airspeed_validated  vtol_vehicle_status  home_position
```

配置名是 `/fmu/out/vehicle_status`；历史 ROS 图出现 `/fmu/out/vehicle_status_v1`，属于消息
版本兼容/转换后的接口表现。H1 复测必须同时记录两者，确认 offboard 实际订阅名和类型，
不能仅凭源码文件名推定运行图。

## `rc_channels` 缺失根因

结论明确：PX4 v1.16.2 的 `src/modules/uxrce_dds_client/dds_topics.yaml` 没有
`/fmu/out/rc_channels` publication。`RcChannels.msg` 在 PX4 与当前 `px4_msgs` 中都存在且
定义一致，因此根因不是消息类型缺失，也不是 Agent、Domain ID 或 QoS；它是 FMUv3 固件
构建输入的输出白名单缺项。重启 Agent 不会修复。

仅供审查的最小源码修改是把下列条目放在 `manual_control_setpoint` 附近：

```yaml
  - topic: /fmu/out/rc_channels
    type: px4_msgs::msg::RcChannels
```

本轮没有应用该修改，也没有构建或刷写。

## 固件修复与回滚方案（未经授权不得执行）

### 构建前记录

1. 拆桨，断开动力电，确认飞控和 Jetson 供电路径。
2. 保存当前完整参数、`ver all`、根仓库/PX4/px4_msgs SHA、时间、命令和串口拓扑。
3. 取得并校验当前可回刷的原始 v1.16.2 FMUv3 `.px4` 文件；记录 SHA-256。
4. 检查 PX4 worktree、submodule 和 ARM 工具链版本。当前环境的工具链可用性有冲突证据，
   必须在构建当次重新验证，不能靠 PATH 推断。
5. 用独立提交保存上述单行 topic 修改，便于审计和 `git revert`；禁止 reset/checkout 用户工作区。

### 未刷写构建命令草案

```bash
cd /home/c/px4_ws/external/PX4-Autopilot
git rev-parse HEAD
git status --short
git submodule status --recursive
arm-none-eabi-gcc --version
make px4_fmu-v3_default
sha256sum build/px4_fmu-v3-default/px4_fmu-v3-default.px4
```

PX4 该 target 的标准产物是上面的
`build/px4_fmu-v3-default/px4_fmu-v3-default.px4`；构建结束仍须从构建日志和文件检查双重
确认该路径及 target 身份，不能对其他板型产物刷写。

### 将来单独授权后才允许的刷写

```bash
make px4_fmu-v3_default upload
```

刷写必须是另一个明确批准的、拆桨任务。禁止 `force upload`。刷写后先恢复/核对参数，再只读
验证 `/fmu/out/rc_channels` 的真实 publisher、类型、QoS、频率、stamp 和 RC 通道运动。

### 回滚

- 源码：对专用修改提交执行 `git revert <commit>`，不 reset/checkout。
- 飞控：用 QGroundControl 的 Custom Firmware 入口刷回已归档且校验过 SHA-256 的原始
  v1.16.2 FMUv3 固件，再恢复保存的参数文件。
- 回滚后重新记录 `ver all`、参数 diff、Agent/串口和所有重点输出。
- 目前没有归档“飞控当前运行二进制”的可回刷文件及 SHA，因此**回滚链尚未成立，禁止刷写**。

主要风险包括 FMUv3 的 flash/RAM 余量、消息生成代码增量、921600 串口带宽、PX4 与
`px4_msgs` 类型版本一致性、bootloader/USB 连接中断，以及参数在刷写后的迁移。必须保存
构建大小比较和完整日志。

## H1 通过条件

H1 只有在一次新的拆桨、只读实机窗口中同时满足以下条件才通过：

1. 唯一且已纳管的 Micro-XRCE-DDS Agent v2.4.2 持有 `/dev/ttyTHS0`，Domain 0。
2. 没有重复 Agent、串口竞争或未经授权的 `/fmu/in/*` publisher。
3. 六个重点输出都有预期真实 publisher；事件型 ACK 只验证 publisher/格式，不为取样发送命令。
4. 记录全部 `/fmu/out/*` 的类型、实际 QoS、频率、PX4 stamp 单调性和冻结检测。
5. `/fmu/out/rc_channels` 来自真实 PX4/RC 输入，并能在拆桨下跟随实际 RC；不得 mock。
6. 固件、参数、Agent、命令、Git SHA、时间和回滚产物形成可复核 receipt。

`rc_channels` 仍为 0 publisher，所以 H1 保持 **BLOCKED**；不得用伪造 RC 解锁安全门。
