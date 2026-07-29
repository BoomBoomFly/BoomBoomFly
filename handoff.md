# BoomBoomFly 普通飞行阶段交接

更新时间：2026-07-30（Asia/Shanghai）

## 当前结论

项目仍为 **NO-GO / 禁止装桨飞行**。G0、G1、G2、G3 已有软件或真实拆桨证据；按“每个
场景必须有当次独立日志”的严格口径，G4 的 10 个场景目前为 **0/10 完整 PASS**，其中 RC
丢失、T265 断流、Agent 退出只有地面未解锁或数据面部分证据，其余 7 项尚未授权。G5 未执行
且禁止执行。

最小飞行闭环的软件实现目标是：

`WAIT_START → PRESTREAM → OFFBOARD → ARM → TAKEOFF → HOVER_3S → HOME_DESCEND → PX4 Land → landing_confirmed → Disarm → COMPLETE`

普通垂直任务固定为 mission ID `3`，测试配置为 0.5 m、上升不超过 0.3 m/s、下降不超过
0.2 m/s。比赛 1.5 m 配置仅保存，不得用于当前实机阶段。

## 代码身份

| 仓库 | 生产分支 | 当前交接提交 |
|---|---|---|
| `BoomBoomFly/BoomBoomFly` | `master` | 本交接分支基于 `12a9adb798cacfc61664409b04f94a5886ff44a9` |
| `BoomBoomFly/offboard_cpp` | `DDS` | `e24bb3facfcf4126ad7b3d216a768a040758e895` |
| `BoomBoomFly/vision_to_dds` | `master` | `470cf59cf8fbcddd17b12e9d31f084e87f5f2fac` |
| `BoomBoomFly/communication` | `main` | `e6d6126acd16050216e5f091e61d58a96ef3ed65` |
| PX4 source | 本地固定提交 | `a8f2dbdfff4792c92f576060ab947f8e588d6f8b` |

当前已刷 PX4 包 SHA-256 为
`fa0fafe9ff25ec503498124631b2880c0255f02cd64394555fcf077a556a725b`。Agent 二进制 SHA-256
为 `4cbc5038cb74391a8ecec3ed6cd94e588530cae937b5498d6796bf2c68433995`。

2026-07-30 实机参数导出为 `docs/2026.7.30.params`，SHA-256：
`a9d100fb9d67e115df94c3005b511ddc0b09ec7645b1b995c7366474ba58667c`。用户提供的
`docs/2026.7.29.params` 和 `docs/px4_fmu-v3_default.px4` 是本地输入/回滚资产，不纳入
Git 提交。

本机当前源码检出与根仓固定的生产内容提交不一致：`offboard_cpp=9daa6dd...`、
`vision_to_dds=449cd5b...`、`communication=2e4b050...`；固定生产提交仍分别为
`e24bb3f...`、`470cf59...`、`e6d6126...`。在重新冻结候选和重跑对应门禁前，不得把当前
工作区视为新的生产候选。

## 已完成

- Offboard 时间估算改为 timesync PX4 时间加单调时钟增量；按话题拆分 freshness，并有
  60 秒实机历史频率回放和时间冻结/倒退/断流 fail-closed 测试。
- 普通垂直任务、ACK 事务、3 秒悬停、1 Hz landed 连续样本确认、PX4 Land 和 Disarm 闭环
  已在 Domain 231 隔离回放通过。
- `/mission/start` 统一为 `std_msgs/msg/UInt32`，带 mission/session/seq/freshness 去重。
- 生产 RC 只来自真实 `/fmu/out/rc_channels`；非法、断流或 signal lost 均 fail-closed。
- T265 生产链默认关闭，必须显式 production/vision 开关和实测外参；唯一视觉 writer、质量、
  epoch、冻结/倒退/断流恢复测试已完成。
- 实测外参使用 `t265_pose_frame -> base_link`：
  `[-0.082, -0.015, 0.108] m`、单位四元数。
- G2 真实 RC/DDS/Agent 拆桨验证、620 秒干净启动 soak 和零 `/fmu/in/*` writer 已通过。
- G3 EV position/height 融合、aid source、innovation/test ratio、`time_last_fuse`、断流退出、
  epoch 防重放和显式 reset 恢复已通过；没有启用 EV velocity/yaw。
- G4 circuit breaker A1 和真实 RC ground/disarmed 丢失恢复只构成部分证据，不等同于
  飞行状态失效验证。
- Agent DDS 退出约 49.063 秒和恢复已直接观测；退出前后均 DISARMED、POSCTL、
  `failsafe=false`、`landed=true`，输入 writer 为 0。
- 已确认板上运行固件为 `a8f2dbdfff4792c92f576060ab947f8e588d6f8b`、PX4 v1.16.2、
  PX4_FMU_V3；在同一次 USB CDC shell 会话中 `logger`、`param`、`ver` 均可用。
- 已确认 logger 进程存在但未记录，原因是 `SDLOG_MODE=0` 且 `SDLOG_BOOT_BAT=0`，因此
  未 Arm 的当次会话没有新 ULog 是符合配置的结果，不需要重新刷写固件。

## Logger / ULog 结论

“本地固件包含 logger，但板上 shell 无 logger/param/ver”的矛盾已解决。此前观察来自不完整
或错误的 shell 连接路径；PX4 USB CDC shell 必须在 VBUS 重连后保持同一条连续会话。完整只读
证据位于：
`docs/evidence/sessions/20260730T021959+0800_logger_sd_single_usb_session_v2/`，
`SHA256SUMS` 文件 SHA-256：
`68e8b41c96c993ac1fe9eea14e12a25d854381f771125ccf3a21103767e98b52`。

SD 卡已挂载且有空间；`logger status` 显示模块运行但未 logging。当前 `SDLOG_MODE=0`、
`SDLOG_BOOT_BAT=0`、`SDLOG_PROFILE=1`。因此仍需为每个 G4 场景获取当次独立 PX4 内部证据；
历史 ULog、publisher 消失或 Agent 数据面恢复都不能替代该证据。

完整 G4/Logger/RC 审计和 10 张独立授权卡草案位于：
`docs/evidence/sessions/20260730T022155+0800_workstation1_audit/`。

## RC 映射与数据采集

- QGC/参数确认：飞行模式通道 5、Offboard 通道 6、Arm 通道 7、Emergency Kill 通道 8。
- 通道 8 是 B 按键并直接映射 PX4 Kill；通道 7 是 A 按键并直接映射 PX4 Arm。二者不得再
  同时复用为应用层 activation/arm_enable/recovery。
- 通道 9、10 是连续滚轮，不适合作为恢复开关；独立 recovery 通道仍未确定。
- `contest_task1.yaml` 和 `vertical_test.yaml` 继续保持四个操作通道为 `-1`、阈值 `2.0`
  的 fail-closed 配置，未写入生产配置。
- 新增只读 18 通道映射工具 `Scripts/runtime/rc_channel_mapper.py` 及单元测试。
- T265 静止 15 秒 rosbag 已采集，SHA-256：
  `29ea448e0cdaf24ce3d6317e0bb49d2714a736ae8dde453e0afd89dc96c40071`；tracker confidence
  为 2，只能作为中等置信度静止基线。
- D435 在正式安装位、约 85 cm 的台架目标数据已采集，rosbag SHA-256：
  `ccde3dd2ae6d74099b3227f9a4431e95c8f7abd6af77d1132e06f46f2b72774f`。小车未安装，
  该数据不得表述为小车任务证据。两份超过 100 MB 的 rosbag 保留在本机，不纳入普通 Git
  提交。

## 已执行验证

- 权威四包 clean build/test：见
  `docs/evidence/sessions/20260729T162319+0800_vertical_flight_stage/`，50 tests PASS。
- G1 Domain 231 回放：60 秒历史频率、完整状态序列、ACK 拒绝/超时、kill、RC/odom/timesync
  丢失、Land/Disarm 全部 PASS。
- G2、G3 和已完成 G4 项的真实日志见 `FLIGHT_STAGE_READINESS.md` 中逐 session 索引。
- 最新根仓 runtime 回归：
  `python3 -m unittest discover -s test/runtime -p 'test_*.py' -v`，
  40 tests PASS。

## 门禁状态

| 门 | 状态 | 说明 |
|---|---|---|
| G0 | PASS | 精确 SHA、权威构建测试、launch/类型/单 writer/生产依赖门禁已有证据 |
| G1 | PASS | Domain 231 隔离回放全闭环已有证据 |
| G2 | PASS | 真实拆桨 RC/DDS/Agent soak 已有证据 |
| G3 | PASS | 真实拆桨 T265/EKF position/height 融合及断流恢复已有证据 |
| G4 | BLOCKED | 严格矩阵 0/10 完整 PASS；3 项部分证据、7 项未授权 |
| G5 | PROHIBITED | 不得装桨、Arm、启动电机或飞行 |

## 唯一当前硬阻塞与下一步

当前硬阻塞是 **G4 真实拆桨失效证据不完整**。logger/ULog 的运行态矛盾已经解决，但尚未
产生任何一个同时满足“单一故障、准确前置状态、PX4 内部状态、当次独立日志、恢复结果”的
完整 G4 PASS。

唯一下一步是：保持拆桨、固定和 ESC 动力隔离，先冻结一个与根仓生产锁一致的候选并重新执行
G0/G1 验证；完成后再逐张取得 G4 授权，不得把多种故障合并为一次测试。

任何 G4 主动失效、参数修改、Domain 0 输入 writer、固件刷写、装桨、Arm 或电机动作都不能
由本交接文档自动授权。
