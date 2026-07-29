# 工位1 G4、logger/ULog 与 RC 审计

时间：2026-07-30T02:21:55+08:00  
范围：拆桨、机体固定、ESC 动力隔离；只读检查与离线审计。  
结论：**NO-GO。G4 未完整通过，G5 继续禁止。**

## logger/ULog 结论

当前板上 `ver all` 已直接确认：

- 硬件：`PX4_FMU_V3` / `V30`；
- PX4：`1.16.2`；
- 运行固件 Git SHA：`a8f2dbdfff4792c92f576060ab947f8e588d6f8b`；
- 分支：`flight/rc-channels-dds-v1.16.2`；
- 构建时间：`Jul 29 2026 12:37:51`；
- NuttX：`11.0.0`，OS Git SHA `886acbbdb4f061e5c0ce1a76afbcfa7cb7df9849`。

运行固件 SHA 与本地 PX4 源码 HEAD 一致。板上 NSH、`logger`、`param` 和
`ver` 均真实存在。`logger status` 显示进程正在运行、订阅 124 个话题，但
`Not logging`。

板上实参为：

- `SDLOG_MODE=0`；
- `SDLOG_BOOT_BAT=0`；
- `SDLOG_PROFILE=1`。

PX4 当前源码对 `SDLOG_MODE=0` 的定义是“Arm 时开始，Disarm 时停止”。本轮从未
Arm，且 Arm 被安全边界禁止，因此没有新 ULog 是预期行为，不是 logger 未编入或
启动失败。`SDLOG_BOOT_BAT` 只影响从启动开始记录的模式，对 mode 0 无效。

SD 卡已挂载到 `/fs/microsd`，`df` 显示 122156 个 32 KiB block 可用；日志目录只
包含旧日期和 `sess100`–`sess102`。`/fs/microsd/etc` 不存在，因此没有 SD 卡启动
覆盖脚本。

本轮不需要刷写，也没有修改参数。先前“命令不存在”的记录不能代表当前固件：稳定
USB、三心跳绑定和单一不中断会话已证明当前命令可用。USB CDC 的限制是：主机关闭
串口后，板上 USB MAVLink 可能停止，而 VBUS 未掉电时不会自动恢复。后续板上只读
检查必须在一次 USB 会话中完成；需要第二次会话时先让 USB VBUS 真正掉电。

权威实机证据：

- `docs/evidence/sessions/20260730T015650+0800_logger_shell_identity_help/`
- `docs/evidence/sessions/20260730T021420+0800_px4_post_power_cycle_passive_heartbeat/`
- `docs/evidence/sessions/20260730T021959+0800_logger_sd_single_usb_session_v2/`

## G4 状态矩阵

| 场景 | 地面未解锁证据 | 飞行状态证据 | 当前状态 | 仍缺少的独立证据 |
|---|---|---|---|---|
| RC 丢失 | 真实 RC 在线→丢失→恢复已观测 | 无 | PARTIAL | Arm/任务状态下 `vehicle_status`、`failsafe_flags`、land detector、当次 ULog、恢复 |
| Offboard 丢失 | 只有软件回放 | 无 | NOT AUTHORIZED | 真实 Offboard/Arm 前态、丢失动作、PX4 failsafe/Land、ACK、ULog、恢复 |
| T265 冻结 | 无独立冻结证据 | 无 | NOT AUTHORIZED | 冻结时间线、innovation/fusion reset、failsafe、land detector、ULog、恢复 |
| T265 断流 | G3 已证明断流和恢复 | 无任务态 failsafe | PARTIAL | Arm/任务状态 PX4 动作、failsafe/Land、当次 ULog、恢复 |
| Agent 退出 | DDS publisher 消失和恢复 PASS | gap 内部状态不可见 | BLOCKED | gap 内独立 `vehicle_status`、`failsafe_flags`、land detector、ULog |
| ACK 拒绝 | 只有软件回放 | 无 | NOT AUTHORIZED | 真实命令、真实拒绝 ACK、状态不变、时间线、ULog |
| ACK 超时 | 只有软件回放 | 无 | NOT AUTHORIZED | 真实命令与链路条件、无 ACK 时间窗、PX4 状态、停止/恢复、ULog |
| kill | 未完成真实通道映射 | 无 | NOT AUTHORIZED | 物理开关映射、边沿、ACK/状态、failsafe、land detector、ULog、恢复 |
| 低电 | 无 | 无 | NOT AUTHORIZED | 真实电源条件、battery 状态、failsafe/Land、ULog、恢复 |
| 围栏 | 无 | 无 | NOT AUTHORIZED | 真实位置/围栏越界、failsafe 动作、land detector、ULog、恢复 |

任何一项没有当次、独立、可校验日志，都不能判 PASS。publisher 消失只证明 DDS
数据面退出，不能证明 PX4 执行了 failsafe 或 Land。

## 独立授权卡

以下卡片均为草案，未获逐项明确授权前不得执行。一次只能执行一张卡，不得合并故障。

### G4-RC-LOSS

- 前置状态：拆桨、固定、ESC 隔离、硬断电可用；真实 RC、唯一 Agent、零输入 writer；
  logger 当次记录能力先独立确认。
- Arm/Offboard：飞行状态验证需要，当前禁止；地面未解锁复验不需要。
- 故障动作：仅关闭 RC 发射机或断开已确认的 RC 链路。
- 预期 PX4 动作：必须按批准时冻结的参数给出，不能由参数值代替实测。
- 观测：`vehicle_status_v1`、`failsafe_flags`、`vehicle_land_detected`、
  `rc_channels`；如涉及命令同时记录 ACK。
- ULog：`vehicle_status`、`failsafe_flags`、`vehicle_land_detected`、
  `input_rc`/`rc_channels`、commander events。
- 停止条件：意外 Arm、mode、Return、Land、Kill、电机输出或观测链丢失。
- 恢复：恢复 RC，确认连续稳定样本和预期模式；再停止采集。
- 回滚：停止 Agent，释放串口，恢复原始物理连接；不改参数。
- 需批准：RC 断开/关闭；若要飞行状态证据，还需单独批准 Arm/Offboard。

### G4-OFFBOARD-LOSS

- 前置状态：G0–G3 保持有效；当次 ULog 已确认；RC 和 kill 已真实映射。
- Arm/Offboard：需要，当前禁止。
- 故障动作：只停止已批准的 Offboard setpoint 源，不停止 Agent。
- 预期 PX4 动作：按冻结的 `COM_OF_LOSS_T`/相关动作参数验收。
- 观测：`vehicle_status_v1`、`failsafe_flags`、land detector、命令 ACK、
  Offboard freshness。
- ULog：vehicle status、failsafe、land detector、offboard control mode、
  trajectory setpoint、commander events。
- 停止条件：动作与批准卡不符、RC/kill 不可用、观测丢失或电机异常。
- 恢复：恢复 setpoint 只用于观测恢复；不得据此自动重新进入 Offboard。
- 回滚：退出测试进程、停止 Agent、恢复生产启动状态。
- 需批准：Arm、进入 Offboard、停止 setpoint 源。

### G4-T265-FREEZE

- 前置状态：真实 T265/EKF 融合稳定；冻结器不发布新的 `/fmu/in/*` writer。
- Arm/Offboard：飞行状态验证需要，当前禁止。
- 故障动作：冻结现有视觉源的时间戳/样本必须由已审核工具完成；不得伪造证据。
- 预期 PX4 动作：innovation/fusion timeout 后进入冻结参数所定义的动作。
- 观测：vehicle status、failsafe flags、land detector、EKF aid source/status。
- ULog：vehicle odometry、estimator status、aid source、failsafe、commander events。
- 停止条件：估计跳变超限、非预期 reset、意外模式或观测链丢失。
- 恢复：解除冻结，要求时间戳单调、连续融合和 reset 计数解释完整。
- 回滚：停止冻结工具，恢复唯一视觉链；不改 PX4 参数。
- 需批准：冻结 T265 数据；若需要任务态证据，另批 Arm/Offboard。

### G4-T265-DISCONNECT

- 前置状态：与冻结卡相同，并完成 T265 USB owner 检查。
- Arm/Offboard：飞行状态验证需要，当前禁止。
- 故障动作：物理断开 T265，不能同时停止 Agent。
- 预期 PX4 动作：按冻结的 EKF/导航参数验收。
- 观测与 ULog：同冻结卡，并记录 USB 断开/恢复时间。
- 停止条件：其他 USB 设备受影响、估计跳变或非预期动作。
- 恢复：重连 T265，确认设备身份、时间戳、融合恢复。
- 回滚：恢复原端口和原线缆。
- 需批准：断开/重连 T265；任务态验证另批 Arm/Offboard。

### G4-AGENT-EXIT

- 前置状态：当次 ULog 已真实开始；Agent SHA、唯一串口 owner、Domain 0 图已冻结。
- Arm/Offboard：若验收 Land/failsafe，需要，当前禁止。
- 故障动作：只停止唯一 Agent，不动 RC、T265 或 setpoint 源。
- 预期 PX4 动作：按批准时冻结的数据链路/Offboard 参数验收。
- 观测：Agent 外部只能证明 DDS 消失；gap 内必须依靠独立 ULog。
- ULog：vehicle status、failsafe flags、land detector、offboard mode、commander events。
- 停止条件：无独立日志、Agent 无法唯一恢复、串口争用或内存/DMA 门禁失败。
- 恢复：经 guard 重启同一 Agent，核验 publisher 与状态恢复。
- 回滚：停止 Agent并释放 `/dev/ttyTHS0`。
- 需批准：停止/启动 Agent；任务态验证另批 Arm/Offboard。

### G4-ACK-REJECT

- 前置状态：命令和预期拒绝原因冻结；记录发送方身份和唯一 writer。
- Arm/Offboard：按被测命令决定；当前不批准任何 Arm/Offboard 命令。
- 故障动作：发送一条预期被 PX4 拒绝的真实命令，不伪造 ACK。
- 预期 PX4 动作：返回真实拒绝 ACK，vehicle state 不改变。
- 观测：ACK、vehicle status、failsafe flags、land detector。
- ULog：vehicle command/ack、commander events、vehicle status。
- 停止条件：命令被接受或状态改变。
- 恢复：停止命令源，确认状态连续稳定。
- 回滚：恢复无输入 writer 图。
- 需批准：准确命令及其发送。

### G4-ACK-TIMEOUT

- 前置状态：定义真实超时形成机制和最大窗口，不能丢弃/伪造 ACK。
- Arm/Offboard：通常需要真实命令事务，当前禁止。
- 故障动作：仅执行批准的真实链路中断或 PX4 无响应条件。
- 预期 PX4 动作：客户端超时并 fail-closed；PX4 状态由独立观测证明。
- 观测：命令发送时间、ACK 窗口、vehicle status、failsafe、land detector。
- ULog：vehicle command/ack、commander events、状态和 land detector。
- 停止条件：超出批准时限、状态未知或恢复失败。
- 恢复：恢复唯一链路，不自动重发危险命令。
- 回滚：停止输入进程并恢复只读图。
- 需批准：准确命令及准确链路中断动作。

### G4-KILL

- 前置状态：完成真实 18 通道映射；选择最不易误触的锁定式物理开关。
- Arm/Offboard：验证 kill 效果需要 Arm，当前禁止。
- 故障动作：只切换已确认的 kill 开关一次。
- 预期 PX4 动作：由批准卡明确，不能用软件状态机模拟。
- 观测：RC 原始通道、vehicle status、failsafe、land detector、ACK/commander events。
- ULog：input RC、vehicle status、failsafe、actuator armed、land detector。
- 停止条件：通道不唯一、边沿不稳定、映射与卡不符。
- 恢复：先回安全位，再按明确流程处理；不得自动重 Arm。
- 回滚：生产 YAML 保持 fail-closed，直到映射经用户签字确认。
- 需批准：物理 kill 切换；Arm 需另批。

### G4-LOW-BATTERY

- 前置状态：电源方案、最低安全电压和硬断电责任人明确；禁止改参数或注入假电量。
- Arm/Offboard：飞行状态验证需要，当前禁止。
- 故障动作：只使用批准的真实可控电源条件，不允许危险放电。
- 预期 PX4 动作：按冻结的电池 failsafe 参数验收。
- 观测：battery status、vehicle status、failsafe、land detector。
- ULog：battery status、failsafe、commander events、vehicle status。
- 停止条件：电芯越界、发热、供电不稳或非预期动作。
- 恢复：切换到安全电源并确认状态恢复。
- 回滚：恢复原电源，不修改参数。
- 需批准：准确电源操作；任务态验证另批 Arm/Offboard。

### G4-GEOFENCE

- 前置状态：围栏参数和坐标系冻结；真实定位稳定；当次 ULog 已开始。
- Arm/Offboard：真实飞行状态验证通常需要，当前禁止。
- 故障动作：只执行批准的真实越界路径；不得伪造位置作为实机证据。
- 预期 PX4 动作：按冻结围栏动作参数验收。
- 观测：global/local position、vehicle status、failsafe、land detector。
- ULog：position、geofence result/events、vehicle status、failsafe、land detector。
- 停止条件：定位质量下降、围栏身份不明或动作与卡不符。
- 恢复：回到围栏内并确认连续恢复。
- 回滚：恢复原场地与启动状态，不改参数。
- 需批准：真实越界动作；Arm/Offboard 另批。

## RC 映射与配置建议

`contest_task1.yaml` 和 `vertical_test.yaml` 当前
`kill_channel`、`activation_channel`、`arm_enable_channel`、
`recovery_channel` 均为 `-1`，阈值为 `2.0`。这是故意 fail-closed，必须保留，
直到真实映射完成并由用户确认。

历史证据只能给出候选：

| 物理用途 | 候选通道索引 | 低/中/高 | 建议阈值 | 结论 |
|---|---:|---|---|---|
| kill | 7 | 未独立测量 | 取实测稳定档位中点 | 仅候选，不可写生产配置 |
| activation/Offboard | 5 | 未独立测量 | 取实测稳定档位中点 | 仅候选，不可写生产配置 |
| arm_enable | 未知 | 未测量 | 未定 | 保持 `-1` |
| recovery | 未知 | 未测量 | 未定 | 保持 `-1` |

映射时使用 `Scripts/runtime/rc_channel_mapper.py`，一次只拨动一个物理开关，
记录 18 通道的最小值、最大值、稳定值、边沿与 `signal_lost`。kill 必须选用最明确、
最不易误触、最好带机械锁定的独立两段开关；不得与 activation、arm_enable 或
recovery 共用物理开关。用户签字确认前不得修改生产 YAML。

## 本轮代码与验证

新增只读工具和测试：

- `Scripts/runtime/rc_channel_mapper.py`
- `test/runtime/test_rc_channel_mapper.py`

`python3 -m unittest discover -s test/runtime -p 'test_*.py' -v`：
40 tests，PASS。

`python3 Scripts/evidence/validate_index.py`：PASS。  
`validate_manifest.py` 与 `validate_evidence.py` 的无参数调用按当前 CLI 会返回用法错误，
因为前者要求 manifest 与 `--kind`，后者要求 metadata；仓库没有可直接替代的当前
release/rollback manifest，证据索引目前为空。不能把该 CLI 契约问题表述为证据 PASS。

当前 offboard、vision、communication checkout 与根仓锁定的生产内容 SHA 不一致，
因此不能把本轮离线检查升级为新的 G0 全量复验。

## 当前门禁

- G0：历史 PASS；本轮未重新宣称，因为依赖 checkout 漂移。
- G1：PASS。
- G2：PASS。
- G3：PASS。
- G4：**BLOCKED**。
- G5：**PROHIBITED**。

唯一建议的后续工作是先完成真实 RC 只读通道映射；该动作需要另行批准连接 DDS 串口、
启动唯一 Agent，并由操作员一次只拨动一个开关。
