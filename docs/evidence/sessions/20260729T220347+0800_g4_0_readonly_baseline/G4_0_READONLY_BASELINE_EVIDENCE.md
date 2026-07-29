# G4-0 只读安全基线

Session：`20260729T220347+0800_g4_0_readonly_baseline`
日期：2026-07-29（Asia/Shanghai）
结论：**G4-0 PARTIAL / BLOCKED；G4 未执行，整体 NO-GO。**

## 授权与安全边界

用户明确批准在全部桨叶已拆除、机体固定、ESC 动力隔离的条件下，仅重新导出当前完整参数、
准备 ULog、核对 failsafe/围栏/低电配置和零输入 writer。全程：

- 未 Arm，实时 `arming_state` 全部为 `1`（DISARMED）；
- 未发布 `VehicleCommand`，未写 PX4 参数，未启动 offboard、vision 或 mission bridge；
- 未执行 RC 丢失、Offboard 丢失、T265 冻结/断流、Agent 退出、ACK 拒绝/超时、kill、
  低电或围栏等主动 G4 失效注入；
- 唯一 Agent 由生产 guard 启动，结束后 Agent 与串口均已释放。

## 实际执行与结果

| 项目 | 实际结果 | 判定 |
|---|---|---|
| Agent guard | 精确 Agent SHA-256 `4cbc5038cb74391a8ecec3ed6cd94e588530cae937b5498d6796bf2c68433995`；Domain 0；`/dev/ttyTHS0` 921600；`MemAvailable=2299652 KiB`；DMA 高水位以上余量 `270192 KiB` | PASS |
| 真实 DDS 基线 | 连续 `30.014 s`，timesync `30`、vehicle status `60`、land detected `31`、RC `1335` 个样本 | PASS |
| 安全状态 | vehicle status 全程 DISARMED、`failsafe=false`；landed/ground_contact/at_rest 为 true | PASS（只读窗口） |
| `/fmu/in/*` writer | 27 个输入话题的最大 writer 数和最终 writer 数全部为 `0`，包括 actuator、VehicleCommand、offboard、trajectory 和 visual odometry | PASS |
| 当前完整参数重导出 | `/dev/ttyACM0` 15 秒内没有 MAVLink heartbeat，程序退出码 `1`，没有生成可用的当前参数快照 | **FAIL / BLOCKED** |
| failsafe/围栏/低电配置 | 实时状态已取得；配置值只能从历史文件读取，不能认定为当前值 | **PARTIAL / BLOCKED** |
| ULog/SD 卡准备 | DDS 没有 logger 状态输出，USB MAVLink 不可用；无法核对当前 logger、SD 卡和 ULog 文件 | **BLOCKED** |
| UART/DMA/USB 内核错误 | 本 session 时间窗两次过滤均无匹配记录 | PASS（本窗口） |
| 最终释放 | Agent/guard 进程 0；`/dev/ttyTHS0`、`/dev/ttyACM0` owner 0；无 offboard/vision/mission/mock 进程 | PASS |

参数导出命令：

```text
python3 /tmp/g3_px4_param_snapshot.py \
  --device /dev/ttyACM0 \
  --output .../artifacts/parameters-live.json \
  --heartbeat-timeout-s 15 \
  --overall-timeout-s 60
```

原始结果：

```text
FAIL: no MAVLink heartbeat
PARAM_EXPORT_EXIT_CODE=1
```

因此本 session 不生成虚假的 `parameters-live.json`，也不把已有
`docs/2026.7.29.params` 表述为当前飞控参数。

## 真实 Domain 0 只读状态

30 秒窗口的主要频率：

| 话题 | 样本 | 实测频率 |
|---|---:|---:|
| timesync status | 30 | 0.9995 Hz |
| vehicle status | 60 | 1.9991 Hz |
| land detected | 31 | 1.0329 Hz |
| RC channels | 1335 | 44.4798 Hz |
| vehicle local position | 2911 | 96.9892 Hz |
| battery status | 2955 | 98.4552 Hz |

RC 为 18 通道，`signal_lost=false`，RSSI 41。电池消息显示 connected、15.863 V、
remaining 0.651、warning 0、faults 0、power input valid；但 temperature 和
time_remaining 为非有限值，cell voltage 全为 0，容量字段为 0。它证明当前有电池状态流，
不证明低电阈值、来源映射或剩余时间估算已配置正确。

PX4 同时报告：

```text
pre_flight_checks_pass=false
gcs_connection_lost=true
local_position_invalid=true
local_velocity_invalid=true
offboard_control_signal_lost=true
```

`vehicle_status.failsafe=false`，表示拆桨静止状态下没有进入全局 failsafe；上述
`FailsafeFlags` 是当前缺失资源/模式要求标志，不能解释为失效动作已通过。
`pre_flight_checks_pass=false` 是当前明确的 Arm/主动 G4 测试 NO-GO 条件。

## 历史参数候选，不是当前配置

历史文件 `docs/2026.7.29.params` 的 SHA-256 为
`2c3b9c6ea6efa4e5fdbb25fa0edc3cd0261f883408b7ae10729ca8c52e1105b0`，文件头 PX4 Git 为
`54f0455ffc000000`，早于当前 aid-source 固件。历史候选包括：

- `GF_MAX_HOR_DIST=0`、`GF_MAX_VER_DIST=0`：当时围栏距离限制看似关闭；
- `COM_FLT_TIME_MAX=-1`：当时没有最大飞行时限；
- `BAT1_SOURCE=0` 且电压/电流模拟通道均为 `-1`：当前来源映射必须重新核对；
- `COM_ARM_SDCARD=1`、`SDLOG_MODE=0`：存在日志策略候选，但没有当前 logger/SD 卡证据；
- `COM_RC_LOSS_T=0.5`、`COM_OF_LOSS_T=0.5`、`COM_OBL_RC_ACT=4`、
  `COM_LOW_BAT_ACT=2`：均须在实时导出后逐项审计；
- `EKF2_RNG_CTRL=0`：历史快照没有假设 range aid。

完整候选清单在 `artifacts/historical-parameter-candidates.txt`，其中显式记录
`current_verified=false`。本次没有参数写入，也没有参数前后 diff。

## ULog 准备状态

当前 `dds_topics.yaml` 未导出 logger status。USB MAVLink 又无 heartbeat，所以本次无法：

- 查询实时 logger 状态；
- 确认 SD 卡是否健康、空间是否充足；
- 列出或校验本次启动产生的 ULog；
- 证明 `COM_ARM_SDCARD`、`SDLOG_MODE` 等当前实际值。

因此 ULog 准备状态为 **BLOCKED / 未验证**，不能进入主动 G4 失效测试。

## 证据校验

`python3 Scripts/evidence/validate_index.py` 返回 PASS、exit code 0、issues 为空。
随后误以为另外两个校验器支持无参数全仓模式，直接调用
`validate_evidence.py` 和 `validate_manifest.py`；两者因缺少必需的 metadata/manifest 参数返回
CLI usage exit code 2。本 session 与相邻 G3 session 一样没有这两类清单，因此这两个退出码不是
证据内容校验失败，也不计为 PASS。原始输出和退出码均保留，没有删除或掩盖。

本 session 的报告与全部原始产物由 `SHA256SUMS` 覆盖，并使用
`sha256sum -c SHA256SUMS` 逐项复核。

## 收尾与下一步

Agent 已停止，两个串口均无 owner；本 session 没有 UART/DMA/USB 内核错误匹配。
G4-0 只是只读准备步骤，不满足 G4 的任何主动失效场景验收，**G4 仍为 BLOCKED**。

下一步需要新的明确授权：保持拆桨、固定和 ESC 动力隔离，仅重插 Pixhawk USB 或重启飞控以
恢复 USB MAVLink，然后只读导出完整参数、读取 logger/SD 卡状态并重新确认
`pre_flight_checks_pass`；仍不写参数、不 Arm、不发 VehicleCommand。
