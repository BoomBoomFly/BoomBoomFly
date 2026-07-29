# PX4 v1.16.2 参数变更计划（仅计划，未执行）

审计时间：2026-07-29T08:40:45+08:00。当前结论：`BLOCKED`，不允许装桨起飞。

本文件不授权写参。表中“当前值”均是 2026-07-28 QGroundControl 快照的最后已知值，
不是 2026-07-29 在线读回值。本轮没有 Agent、飞行 ROS 节点或在线飞控参数通道，任何
变更前必须重新导出完整参数。禁止批量写参；每组变更都要先 SITL，再拆桨、固定机体并
隔离电机功率验证。Arm、Disarm、Offboard、Land、Kill 仍需用户对相应测试单独明确授权。

## 证据与版本边界

- 参数快照：`docs/evidence/sessions/20260728T213311+0800_px4_parameter_audit/raw/px4_2026-07-28.params`，974 项，无重复，SHA-256 `f669480ed8fd3f8066a6ab3132667a4be5a13dce956f7f23139efeff409222ce`。
- 运行固件身份：PX4 v1.16.2 stable，`PX4_FMU_V3`，Git `54f0455ffcd755534539a7cf33a09a20bf71d29d`。
- 本地 PX4 源码：同一 SHA、标签 `v1.16.2`、工作树干净。
- 官方依据：[PX4 v1.16 参数参考](https://docs.px4.io/v1.16/en/advanced_config/parameter_reference)、[外部位置估计](https://docs.px4.io/v1.16/en/ros/external_position_estimation)、[Safety/Failsafe](https://docs.px4.io/v1.16/en/config/safety)。未采用其他版本的参数含义。
- `EKF2_EV_CTRL=0` 已明确证明最后已知配置没有融合外部视觉。看到 `/fmu/out/vehicle_odometry` 不能反证 EKF 已接受 EV。

## 每次修改前的强制留档

在一个新的、不可变 evidence 会话中保存以下内容，缺一项就停止：

| 字段 | 必须保存的内容 |
|---|---|
| 原始参数 | 修改前完整 `.params`、待改参数的在线读回、文件 SHA-256 |
| Git | 根仓库、`offboard_cpp`、`vision_to_dds`、`px4_msgs`、PX4 源码完整 SHA 与 dirty 状态 |
| 固件 | `ver all`、板型、构建时间、运行 `.px4`/`.bin` SHA-256；当前运行二进制哈希尚缺失 |
| 命令 | 原样记录参数名、旧值、新值、操作者使用的 QGC/NSH 命令；禁止未审阅脚本批量写入 |
| 时间 | Asia/Shanghai ISO-8601 开始、结束时间 |
| 回滚 | 本文件中的旧值、单项回滚命令、重启要求、读回与行为验证 |
| 测试 | 拆桨照片/检查单、ULog、QGC events、ROS/DDS 原始输出、观察者签字 |

每组只在前一组完成“写入—重启（若要求）—在线读回—拆桨验收—回滚演练”后继续。

## 外部视觉

| 参数 | 最后已知值 | v1.16.2 含义 | 建议候选 | 修改前置条件 | 拆桨验收 | 回滚值 |
|---|---:|---|---|---|---|---:|
| `EKF2_EV_CTRL` | `0` | bit0 水平位置、bit1 垂直位置、bit2 3D 速度、bit3 yaw | H2 完成后的首个 H3 候选 `3`；可先用 `1` 分阶段验证。暂不启用 bit2/bit3 | `odom_frame -> base_link` 外参、FRD 转换、时间戳、协方差、冻结/重连全通过；真实视觉 writer 唯一 | 手持静止/五方向动作；`cs_ev_pos=true`，启用垂直时 `cs_ev_hgt=true`；`estimator_aid_src_ev_pos.fused=true` 且 `time_last_fuse` 前进；无持续 rejection；`cs_ev_vel/cs_ev_yaw=false` | `0` |
| `EKF2_HGT_REF` | `1` GPS | 0 Baro、1 GPS、2 Range、3 Vision；Vision/Range 只宜平坦表面 | 垂直 EV 合格时 `3`；否则 `0` Baro。最终必须二选一，不猜 | Z 符号、尺度、静态漂移、遮挡和重连跳变合格；bit1 已启用 | 重启后检查 `cs_ev_hgt`、`z_valid`、高度创新、origin/reset；视觉失效时按预期降级 | `1` |
| `EKF2_EV_DELAY` | `0 ms` | EV 测量相对 IMU 的延迟，0–300 ms，需重启 | `TBD_MEASURED`，不能把约 6 ms 到达延迟直接当作该参数 | 同时记录 T265 capture stamp、`timestamp_sample`、PX4 timesync 与 ULog | 前后/上下受控运动，调到 EV innovation 不呈持续相位差；重启并读回 | `0` |
| `EKF2_EV_POS_X` | `0 m` | T265 跟踪原点相对 CoG 的 PX4 body FRD X，向前正 | `TBD_MEASURED_FRD` | 测量 CoG 到跟踪原点，不量外壳边缘；完成 FLU→FRD 换算 | 绕 CoG 做 pitch/yaw，杆臂补偿后无明显位置圆弧 | `0` |
| `EKF2_EV_POS_Y` | `0 m` | FRD Y，向右正 | `TBD_MEASURED_FRD` | 同上 | 绕 CoG 做 roll/yaw 验证；右侧安装应得到正值 | `0` |
| `EKF2_EV_POS_Z` | `0 m` | FRD Z，向下正 | `TBD_MEASURED_FRD` | 同上 | 绕 CoG 做 roll/pitch 验证；传感器在 CoG 上方应得到负值 | `0` |

实际组件位于 `src/vision_to_dds`，本轮修改前 HEAD 是 `72bd682`，不是用户声明的
`42a0688`；本地对象库仍无法解析后者。当前实现用相邻 TF 位置差分生成 NED velocity，并使用
配置的 velocity variance；它不是未经滤波验证的 T265 原生速度证据，所以
`EKF2_EV_CTRL` bit2 仍不得启用。quality/source epoch adapter 已存在并通过软件测试，quality
来自 RealSense covariance 编码而非固定值；但真实 topic、冻结和拔插恢复未完成 live 验证，
实现身份和外参也未绑定前仍不得进入 H3。

## Offboard、RC 与电池失效

| 参数 | 最后已知值 | v1.16.2 含义 | 建议候选 | 修改前置条件 | 拆桨验收 | 回滚值 |
|---|---:|---|---|---|---|---:|
| `COM_OF_LOSS_T` | `1.0 s` | Offboard proof-of-life 丢失到触发 failsafe 的超时 | 初始候选 `0.5 s`，最终按健康 writer 最大间隔和调度抖动确定 | H3 已通过；唯一 writer、真实 RC、kill、authority、人工触发/arm enable、control mode 与 ACK 全部新鲜 | 经单独授权进入拆桨 Offboard 后停止唯一 writer，测量丢失判定和动作时序 | `1.0` |
| `COM_OBL_RC_ACT` | `0` Position | 0 Position、1 Altitude、2 Stabilized、3 Return、4 Land、5 Hold、6 Terminate、7 Disarm | 室内候选 `4` Land；不选 Return | local position/height、land detector 与 Land 行为已通过；不得依赖不可用 Position | 停 writer 后最终进入 Land，不得进入 Position/Return；检查 `COM_FAIL_ACT_T` 叠加延迟 | `0` |
| `COM_RC_LOSS_T` | `0.5 s` | 最后真实 RC/Joystick setpoint 后判失联；官方要求保持较短 | 暂保留 `0.5 s` | 必须恢复真实 `/fmu/out/rc_channels`，确认帧率、`signal_lost` 与 receiver failsafe；禁止 mock | 关闭遥控器/断接收链，测量 RC lost 时刻与 channel 冻结行为 | `0.5` |
| `NAV_RCL_ACT` | `2` Return | 1 Hold、2 Return、3 Land、5 Terminate、6 Disarm | 室内候选 `3` Land | 真实 RC、kill、模式切换均通过，Land 可用 | 拆桨授权状态下触发 RC loss，最终 Land 且绝不 Return | `2` |
| `COM_LOW_BAT_ACT` | `0` Warning | 0 Warning、2 critical/emergency 均 Land、3 critical Return/emergency Land | `2` Land | 校准 power module；当前 `BAT1_CAPACITY=-1`，不能信任容量；先官方 failsafe simulation | 用限流可调电源/仿真触发，禁止深放真实电池；验证事件、Land 与恢复 | `0` |

关联参数 `COM_FAIL_ACT_T=5.0 s` 会给多类失效动作增加 Hold 延迟。室内候选应另案评估
`0–1 s`（首个测试候选可为 `0`），但它不在本轮授权范围；不能把
`COM_RC_LOSS_T=0.5` 误写成 0.5 秒内已经完成 Land。`COM_RCL_EXCEPT=0` 当前没有忽略
Offboard 下的 RC loss，应保留。真实 RC publisher 缺失时本组全部 `BLOCKED`。

## 围栏与运动包线

| 参数 | 最后已知值 | v1.16.2 含义 | 建议候选 | 修改前置条件 | 拆桨验收 | 回滚值 |
|---|---:|---|---|---|---|---:|
| `GF_MAX_HOR_DIST` | `0 m` | Home 水平圆柱半径；0 禁用 | `TBD_SITE`，不大于“起飞点到最近障碍－机体半径－最大停车距离－余量” | 当前 `GF_SOURCE=0` 依赖 global position/Home；必须先证明室内 Home/GPOS 有效，否则不得声称该围栏可用 | 手持越界，验证 breach、时序和动作 | `0` |
| `GF_MAX_VER_DIST` | `0 m` | Home 上方最大距离；0 禁用 | `TBD_SITE`，由净空、机体高度、停车距离和余量计算 | 同上 | 升降夹具手持越界验证 | `0` |
| `MPC_XY_VEL_MAX` | `12 m/s` | 所有速度控制模式的水平绝对上限 | 首次室内候选 `0.5 m/s` | 加速度、jerk、yaw rate 也要另审；先 SITL | 超限 setpoint 被 PX4 截断，状态/日志无饱和异常 | `12` |
| `MPC_Z_VEL_MAX_UP` | `3 m/s` | 所有上升速度控制模式绝对上限，最小 0.5 | `0.5 m/s` | 同时审计下降速度上限 | 超限升速 setpoint 被截断 | `3` |
| `MPC_TKO_SPEED` | `1.5 m/s` | Takeoff climb rate，v1.16 最小 1.0 | `1.0 m/s` | 先 SITL；同时确认 `MPC_TKO_RAMP_T=3 s` | 升降夹具观察 takeoff 状态/setpoint，不得把该参数写成 0.5 | `1.5` |
| `MPC_LAND_SPEED` | `0.7 m/s` | Land descend rate，v1.16 最小 0.6 | `0.6 m/s` | 同时检查 `MPC_LAND_ALT1/2/3=10/5/1 m` 和 crawl 速度 | 拆桨验证低高度 Land setpoint 和着陆检测 | `0.7` |
| `COM_DISARM_LAND` | `2.0 s` | 连续检测 landed 后自动 disarm；非正值禁用 | 暂保留 `2.0 s` | land detector 无运动中误判；Disarm 测试另获授权 | 人工抬放不误判；落地约 2 秒后自动 disarm | `2.0` |

`GF_ACTION=2` 在 v1.16 是 Hold，不是 Return。若确实证明 Home/GPOS 围栏可用，配套室内
候选是 `GF_ACTION=5` Land；它属于关联参数，必须单独留档和验证。只有 local VIO 时应
保留物理防护/系留与应用层 local envelope，不能以 PX4 Home 围栏代替。

## Circuit breaker

magic key 表示 breaker 已启用，也就是相应检查/动作被禁用。四项不得一起批量写。

| 参数 | 最后已知值与效果 | 建议候选 | 修改前置条件 | 拆桨验收 | 回滚值 |
|---|---|---|---|---|---:|
| `CBRK_IO_SAFETY` | `22027`：禁用 IO safety | 实机 safety button 可用时 `0` | 只读确认 `safety_button_available`、IO 接线和 `COM_PREARM_MODE=0` | 未按 safety 必须阻止 Arm，按下后状态正确；Arm 另需授权 | `22027` |
| `CBRK_SUPPLY_CHK` | `894281`：禁用 commander 电源有效性检查 | `0` | 校准 power module，确认 5V rail/battery telemetry；克隆板若不能报告则继续 BLOCKED | 正常电池供电通过；异常/拔除供电产生明确 preflight fault | `894281` |
| `CBRK_USB_CHK` | `197848`：禁用 USB connected 检查 | `0`（官方推荐） | 使用电池/power module，生产测试断开 USB | 接 USB 阻止飞行解锁检查，断开并重启恢复 | `197848` |
| `CBRK_FLIGHTTERM` | `121212`：禁用 FailureDetector/FMU-loss termination；不影响 RC/DL/geofence/takeoff failure | `TBD_RISK_REVIEW`；仅在“立即终止优于继续运动”有书面结论时才考虑 `0` | 审计 `FD_FAIL_R/P=60°`、触发约 0.3 s、输出与现场风险；先 failsafe simulation | 隔离电机功率，用输出状态/逻辑分析验证；不能用 takeoff 翻转检查代替空中 termination | `121212` |

## PX4 接受视觉的 H3 判据

以下条件必须同时满足，仅有 ROS writer 或 PX4 输出 odometry 不算：

1. `estimator_status_flags.cs_ev_pos=true`；启用垂直 EV 时 `cs_ev_hgt=true`。
2. 当前首阶段未启用的 `cs_ev_vel`、`cs_ev_yaw` 保持 false。
3. ULog/uORB `estimator_aid_src_ev_pos.fused=true`，`time_last_fuse` 持续推进，
   `innovation_rejected` 不持续置位，test ratio 不持续越门限。
4. `/fmu/out/vehicle_local_position` 的 `xy_valid/z_valid` 符合配置，时间戳单调，reset
   counter 不异常增长。
5. 静止、前移、右移、抬高、顺时针偏航符号与量级正确；遮挡、冻结、断开、重连
   不继续使用冻结位置。

当前 `EKF2_EV_CTRL=0` 直接使第 1 条失败：PX4 尚未实际接受外部视觉。
