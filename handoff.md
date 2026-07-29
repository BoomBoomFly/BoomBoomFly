# BoomBoomFly 普通飞行阶段交接

更新时间：2026-07-30（Asia/Shanghai）

## 当前结论

项目仍为 **NO-GO / 禁止装桨飞行**。G0、G1、G2、G3 已有软件或真实拆桨证据；G4 只完成
部分失效测试，仍缺 Agent 退出期间 PX4 内部 mode/failsafe/Land 的独立证据及其余真实拆桨
失效项目。G5 未执行且禁止执行。

最小飞行闭环的软件实现目标是：

`WAIT_START → PRESTREAM → OFFBOARD → ARM → TAKEOFF → HOVER_3S → HOME_DESCEND → PX4 Land → landing_confirmed → Disarm → COMPLETE`

普通垂直任务固定为 mission ID `3`，测试配置为 0.5 m、上升不超过 0.3 m/s、下降不超过
0.2 m/s。比赛 1.5 m 配置仅保存，不得用于当前实机阶段。

## 代码身份

| 仓库 | 生产分支 | 当前交接提交 |
|---|---|---|
| `BoomBoomFly/BoomBoomFly` | `master` | 以本文件所在合并提交为准 |
| `BoomBoomFly/offboard_cpp` | `DDS` | `e24bb3facfcf4126ad7b3d216a768a040758e895` |
| `BoomBoomFly/vision_to_dds` | `master` | `470cf59cf8fbcddd17b12e9d31f084e87f5f2fac` |
| `BoomBoomFly/communication` | `main` | `e6d6126acd16050216e5f091e61d58a96ef3ed65` |
| PX4 source | 本地固定提交 | `a8f2dbdfff4792c92f576060ab947f8e588d6f8b` |

当前已刷 PX4 包 SHA-256 为
`fa0fafe9ff25ec503498124631b2880c0255f02cd64394555fcf077a556a725b`。Agent 二进制 SHA-256
为 `4cbc5038cb74391a8ecec3ed6cd94e588530cae937b5498d6796bf2c68433995`。

用户提供的 `docs/2026.7.29.params` 和 `docs/px4_fmu-v3_default.px4` 是本地输入/回滚资产，
没有纳入 Git 提交。

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
- G4 circuit breaker A1 和真实 RC ground/disarmed 丢失恢复已通过。
- Agent DDS 退出约 49.063 秒和恢复已直接观测；退出前后均 DISARMED、POSCTL、
  `failsafe=false`、`landed=true`，输入 writer 为 0。

## 最新 G4 日志补证

本次临时将 `SDLOG_MODE` 从 0 改为 2，冷启动确认后执行 Agent gap，再回滚至 0。启用和回滚
事务均只改变 `SDLOG_MODE` 与派生 `_HASH_CHECK`。最终冷启动 974/974 参数与写前逐项
零差异，当前 `SDLOG_MODE=0`。

MAVFTP 只找到 19 个旧 ULog，没有 2026-07-29/30 当次日志；下载的 `sess100`–`sess102`
均嵌入旧的 `SDLOG_MODE=0`，不能证明本次 gap 内状态。USB shell 显示 SD 卡挂载且空间充足，
但 logger/param/ver 命令在该 shell 中不可用；本地已刷构建的配置、ELF 和 map 又明确包含这些
命令。这个运行态矛盾尚未解释。

完整证据：
`docs/evidence/sessions/20260729T234922+0800_g4_agent_gap_ulog/`。

## 已执行验证

- 权威四包 clean build/test：见
  `docs/evidence/sessions/20260729T162319+0800_vertical_flight_stage/`，50 tests PASS。
- G1 Domain 231 回放：60 秒历史频率、完整状态序列、ACK 拒绝/超时、kill、RC/odom/timesync
  丢失、Land/Disarm 全部 PASS。
- G2、G3 和已完成 G4 项的真实日志见 `FLIGHT_STAGE_READINESS.md` 中逐 session 索引。
- 最新根仓 runtime 回归：
  `python3 -m unittest discover -s test/runtime -p 'test_*.py' -v`，
  35 tests PASS。

## 门禁状态

| 门 | 状态 | 说明 |
|---|---|---|
| G0 | PASS | 精确 SHA、权威构建测试、launch/类型/单 writer/生产依赖门禁已有证据 |
| G1 | PASS | Domain 231 隔离回放全闭环已有证据 |
| G2 | PASS | 真实拆桨 RC/DDS/Agent soak 已有证据 |
| G3 | PASS | 真实拆桨 T265/EKF position/height 融合及断流恢复已有证据 |
| G4 | BLOCKED | Agent gap 内部状态无独立日志；其余主动失效项目未完成 |
| G5 | PROHIBITED | 不得装桨、Arm、启动电机或飞行 |

## 唯一当前硬阻塞与下一步

当前硬阻塞是 **G4 真实拆桨失效证据不完整**，尤其是 Agent 退出期间没有当次独立 ULog，
不能证明 PX4 实际 mode/failsafe/Land 结果。

下一步应保持拆桨、固定和 ESC 动力隔离，先在新的只读 session 中复核当前板上 PX4 shell
命令注册、logger 进程和启动脚本，解释“本地构建包含 logger 但板上 shell 命令不可用”的
矛盾。若最终需要修改或重新刷写固件，必须先提交明确的产物 SHA-256、变更内容、回滚镜像和
操作卡，并重新取得用户对刷写的明确授权。

任何 G4 主动失效、参数修改、Domain 0 输入 writer、固件刷写、装桨、Arm 或电机动作都不能
由本交接文档自动授权。
