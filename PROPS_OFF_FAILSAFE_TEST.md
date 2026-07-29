# 拆桨失效测试计划（H4，未执行）

状态：`BLOCKED / NOT RUN`。本文件只定义未来测试，不授权 Arm、Disarm、Offboard、
Land、Kill、写 PX4 参数或发布 `/fmu/in/*`。所有实机测试先拆桨；涉及上述动作时，
必须由用户对具体用例另行明确授权。

## 当前不得开始 H4 的原因

- H1 未通过：当前没有 Agent 或 `/fmu/out/*` publisher，历史记录中
  `/fmu/out/rc_channels` 为 0 publisher。
- H2 未通过：`t265_pose_frame -> base_link` 外参未知。
- H3 未通过：最后已知 `EKF2_EV_CTRL=0`，PX4 没有融合 EV。
- `offboard_cpp` 当前 checkout `976d621` 没有把 `OffboardRuntimeGate` 接入生产
  `offboard_node`；该类只被测试直接调用。
- 生产节点会在启动后以 50 Hz 无条件发布 trajectory setpoint 和 control mode；
  `CMakeLists.txt` 还全局启用了 `TEXT_RC`，会覆盖真实 RC 模式/档位值。禁止把它作为
  实机生产 writer 启动。
- 生产节点没有订阅 command ACK，也没有生产路径中的 kill、authority、人工激活、
  manual arm enable 或 ACK correlation/freshness 闭环。

以上任一项存在都必须 fail closed；mock RC 只能用于单元测试/仿真，绝不用于生产解锁。

## 通用前置与留档

1. 拆除全部桨叶，拍照确认；机体固定在不可翻倒夹具上，划定人员禁入区。
2. 对只需逻辑验证的步骤断开/隔离 ESC 电机功率；需要检查 PWM/DSHOT 时使用逻辑分析仪
   或无桨电机，并由观察者控制独立断电。
3. 准备真实 RC、经验证的物理 kill、主电源硬断、限流电源和电池防火措施。
4. H1–H3 必须均 PASS；唯一生产 writer 身份固定，禁止第二 Agent、第二 writer 和旧 bringup。
5. 保存修改前完整参数、全部 Git SHA、`ver all`、运行固件二进制 SHA-256、命令、时间、
   旧值和单项回滚步骤。参数在线读回必须与计划一致。
6. 保存 ULog、QGC event、`failsafe_flags`、`vehicle_status_v1`、`vehicle_control_mode`、
   `vehicle_land_detected`、`vehicle_command_ack`、`vehicle_local_position`、
   `estimator_status_flags`、RC 与 timesync 原始输出。
7. 先在 PX4 v1.16.2 SITL/failsafe simulation 复现，再在实机拆桨执行。

## 每次用例的停止条件

出现下列任一情况立即断开生产 writer并硬断电，保留日志，不在同一会话临时改参重试：

- `/fmu/out/rc_channels` 不新鲜、`signal_lost` 语义不对、channel_count 越界或出现 mock writer；
- kill、authority、manual activation、manual arm enable、setpoint、control mode 或 ACK 任一不新鲜；
- 两个 Agent、两个 `/fmu/in/*` writer、串口 owner 变化或 ROS domain 不为 0；
- T265 时间戳回退、冻结未被拦截、source epoch 未变化、外参/坐标符号不一致；
- command ACK 拒绝/超时/身份不匹配仍继续发布；
- 失效动作是 Return、Position，或与批准的 Land/Hold 策略不同；
- 意外输出、电机转动、飞控重启、供电异常、estimator reset/innovation 持续拒绝。

## 测试矩阵

| ID | 失效/门 | 额外前置 | 未来刺激（需相应授权） | PASS 判据 | 必存证据 |
|---|---|---|---|---|---|
| H4-01 | 默认无 writer | 无 Arm，无输入 writer | 冷启动机载机与飞控；不启动生产 launch | `/fmu/in/*` publisher 全为 0，Agent 最多一个，串口 owner 唯一 | 进程、串口、ROS graph、时间 |
| H4-02 | 真实 RC 新鲜度 | 固件已发布 `rc_channels`；禁止 mock | 开/关遥控器、receiver failsafe；不 Arm 也先完成帧级测试 | 正常时频率/时间戳稳定；断链在 `COM_RC_LOSS_T` 范围内体现 `signal_lost`/failsafe；冻结帧不能被当新鲜 | RC 类型/QoS/频率、通道、loss 时间线 |
| H4-03 | 物理 kill | kill 映射、输出策略和硬断均复核 | 经 Kill 明确授权，在隔离电机功率条件触发/释放物理开关 | 状态与输出进入批准的 kill/lockdown；软件 writer不能解除；恢复必须人工显式完成 | RC 通道、actuator/output、status、事件 |
| H4-04 | authority/人工激活 | gate 已接入生产 writer；envelope/correlation/source epoch 固定 | 拒绝、过期、错误 identity、fault-latched、未人工激活、arm-enable=false 各一次 | 任一不满足时发布计数保持 0；只有完整新鲜门链可进入 prestream | authority decision、graph epoch、writer ID、gate event |
| H4-05 | setpoint/control mode freshness | 真实 RC 和 authority 均通过 | 分别停止 setpoint、停止 control mode、制造旧/未来/不单调 stamp | 立即 fail closed，不发 vehicle command；不能保持旧 setpoint 继续控制 | 每路接收/发送 stamp、gate event |
| H4-06 | prestream | H4-04/05 通过 | 提供至少批准持续时间/样本数的单调 setpoint，再制造间隙 | 过短、样本不足、间隙过大均不准模式命令；完整 prestream 才进入 wait-ACK | sample count/duration/max gap |
| H4-07 | command ACK | ACK topic 实际可见；command identity/correlation 已实现 | 经模式命令授权，分别测试 accepted、denied、temporary reject、timeout、错 command/target/source | 只有匹配且新鲜的 accepted ACK 可继续；其他全部 0 publish/fault | command sequence、ACK 全字段、gate state |
| H4-08 | vehicle control/status | `vehicle_status_v1`、`vehicle_control_mode` 新鲜 | 制造 stale、错误 nav state、PX4 重启/source epoch 变化 | 非 OFFBOARD、stale 或 epoch 变化立即撤销 readiness；需重新完整 prestream/ACK | status/control mode/epoch 时间线 |
| H4-09 | Offboard 丢失 | `COM_OBL_RC_ACT` 已批准为室内动作；H3有效 | 经 Offboard+Arm 明确授权后停止唯一 writer | 在 `COM_OF_LOSS_T + COM_FAIL_ACT_T` 预期窗口进入批准动作；室内不得 Return/Position；writer 停止后不再发命令 | failsafe_flags、nav_state、Land/ACK 时序 |
| H4-10 | RC 丢失 | 真实 RC publisher 与 kill 已通过；`NAV_RCL_ACT` 已批准 | 经 Arm/Offboard 授权后关闭 transmitter/断 receiver | 最终进入批准的 Land；不得 Return；物理 kill仍有效 | RC loss、failsafe、nav_state、输出 |
| H4-11 | 视觉遮挡/冻结 | H3 已证明融合；health/epoch gate 已接入 | 遮挡镜头、冻结 source、停止相机、USB 重连分别测试 | 冻结样本不再进入 PX4；融合停止/位置 validity 与批准策略一致；重连 epoch 增加且不能自动恢复 authority | 原始 T265、TF、EV writer、EKF aid/status/ULog |
| H4-12 | T265 时间回退/跳变 | 同上 | 真实重连与快速运动；不得伪造生产数据 | 非单调、过旧、跳变数据被 gate 拒绝；PX4 reset counter/innovation 行为可解释 | capture/receive/PX4 时间、quality、epoch |
| H4-13 | 低电量 | 电池/功率模块校准；`COM_LOW_BAT_ACT` 已批准 | 先 simulation；实机用限流电源逐级触发，禁止深放电池 | warning/critical/emergency 阈值、事件与 Land 动作正确；无 Return | 电压、电流、remaining、warning、status |
| H4-14 | 围栏 | 有效 global position 与 Home 已证明；否则本项 BLOCKED | 拆桨手持跨越水平/垂直边界 | breach 在预期阈值触发 `GF_ACTION=Land`；不得 Return；若只具 local VIO，不得声称此项 PASS | Home/GPOS、距离、breach/action |
| H4-15 | Land 与落地自动上锁 | land detector 已验证 | 经 Land/Disarm 授权执行无桨 Land 流程并人工抬放 | 运动中不误报 landed；落地持续约 `COM_DISARM_LAND` 后自动 disarm；ACK/状态一致 | land_detected、arming_state、ACK、输出 |
| H4-16 | supply/USB/IO safety breakers | 每项单独修改且有回滚 | 正常/异常供电、USB 接入、safety button 未按/按下 | 恢复的检查能阻止不安全状态；克隆板无法提供信号则 BLOCKED，不旁路 | preflight events、power、safety state |
| H4-17 | flight termination | 完成书面风险评审；绝不与前三个 breaker 批量改 | 只在 simulation 后、隔离电机功率和 Terminate 明确授权下触发 | FailureDetector/FMU-loss 输出与批准策略一致；硬后果可由独立断电控制 | failure flags、actuator/output、事件 |

## 用例记录模板

```text
test_id:
authorization_scope:
props_removed_by / observed_by:
motor_power_isolated:
started_at / ended_at:
root_sha / offboard_sha / vision_sha / px4_sha:
firmware_sha256:
parameter_snapshot_sha256:
agent_pid / serial_owner / ROS_DOMAIN_ID:
single_writer_identity:
stimulus_time:
expected_action / observed_action / action_time:
kill_verified:
artifacts_and_sha256:
rollback_command / rollback_verified:
result: PASS | BLOCKED | FAIL
limitations:
```

H4 只有在全部适用用例 PASS、无 mock RC、无未解释异常且回滚演练完成后才可通过。
当前一个用例也未获执行授权，故 H4 为 `BLOCKED`，不允许装桨起飞。
