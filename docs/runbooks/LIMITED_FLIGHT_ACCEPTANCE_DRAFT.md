# 有限实机控制验收草案

> **DRAFT — 不构成飞行或控制授权**
>
> 文档状态：`IMPLEMENTED`（草案已记录）
>
> 验收状态：`UNVERIFIED`
>
> 有限实机：`BLOCKED`
>
> production：`BLOCKED`

本轮没有访问硬件、启动 Agent/节点、写参数、刷 firmware、arm、切 mode 或发送 `/fmu/in/*`。本文只描述有限实机的治理和安全门；任何真实控制必须由维护者针对精确飞行器、候选版本、人员、场地、时间窗和 test card 另行书面授权。

## 1. 目标与非目标

目标：在已完成拆桨台架验收后，于批准的最小地理/高度/速度/时长包线内，用最小增量证明有限的 DDS-only 控制场景，并验证人工接管、停止、evidence 和回滚流程。

非目标：production enable、常规任务、swarm、precision landing、性能极限、未知环境、无人监督或自动扩大包线。通过某个 test card 只能将该精确场景标为 `FLIGHT_VERIFIED`；未列能力继续为 `UNVERIFIED`。

## 2. 允许与禁止

### 允许

- 只在批准 test card 的场地、时间、气象、人员、飞行器和精确版本范围内操作；
- 飞前只读 identity、参数、transport、graph、telemetry 和 health 检查；
- 按 test card 单步执行最小包线控制，并在每步之间回到批准安全状态；
- pilot in command（PIC）或 safety pilot 随时人工接管/叫停；
- 保存脱敏日志、飞行记录和飞后 rollback evidence。

### 禁止

- 未经新的明确授权 arm、mode、setpoint、VehicleCommand 或 `/fmu/in/*`；
- 在现场修改源码、临时构建/刷写 firmware、写参数后继续飞行；
- 使用第二条飞控传输作为 production fallback，或让其与 DDS 争用 `/dev/ttyTHS0`；
- 使用 demo、animal、mock、旧 bringup、swarm 或 baseline precision landing；
- 单人飞行、无观察员、无独立人工控制/kill、超出批准地理或动力包线；
- 自动串联多个 test case、失败后自动恢复 ACTIVE 或未经复核重复起飞；
- 把 SITL、台架、QGC 显示或历史实机 session 作为本次飞行通过证据。

## 3. 前置条件

### 3.1 工程与验证

- [ ] 所有 P0 和本次适用 P1 已关闭，无风险接受替代安全验收。
- [ ] 同一精确 root/lock/toolchain/Agent/PX4 artifact/profile/参数候选为 `SITL_VERIFIED` 和 `BENCH_VERIFIED`。
- [ ] 拆桨台架已实际完成控制、fault、kill/RC、stop 和 rollback；不只是 runbook 桌面演练。
- [ ] graph guard、owner/lease、ACK/freshness、PRESTREAM、fault lattice、结构化诊断和 CI 合并门均启用。
- [ ] firmware/参数/software/transport rollback 在拆桨台架实际成功。
- [ ] 视觉如不在 test scope 内必须机械禁用 publisher；如在 scope 内，其 frame/time/EKF2/profile 已单独验收。
- [ ] baseline precision landing 关闭；单机根 namespace 约束保持。

### 3.2 授权、法规与风险

- [ ] 维护者签发精确飞行授权及失效时间。
- [ ] 独立 safety review 批准 hazard analysis、fault action、deadline、接管和终止卡。
- [ ] test director 签发逐步 test card，列出允许的 arm/mode/setpoint 边界；本文不提供这些命令。
- [ ] 场地、空域、法规、保险、人员资质和地面安全要求已确认。
- [ ] 地理围栏、高度、速度、姿态、距离、时长、风、能见度、降水、温度和电池阈值有数值门；未填写即 `BLOCKED`。
- [ ] 外部人员/无线电/导航干扰和失联场景已纳入风险评审。

### 3.3 人员

| 角色 | 职责 |
|---|---|
| PIC | 对是否起飞和是否继续拥有最终决定权；保持法规责任 |
| safety pilot | 持有独立人工控制和 kill/接管能力，只关注飞行安全 |
| test director | 读 test card、控制节奏、禁止现场扩 scope |
| observer | 监视空域、地面人员、机体、天气和边界；可无条件叫停 |
| evidence recorder | 监控日志/时钟/identity，记录每次 go/no-go 和事件 |
| control/firmware reviewer | 飞前核对候选与 `BENCH_VERIFIED` identity 一致 |

PIC 与 safety pilot 是否允许同一人由法规和 safety review 决定；默认视为不同人员。所有控制交接必须使用口令、复诵和确认，不接受默示交接。

## 4. 设备状态

- 飞行器结构、紧固件、重心、桨叶型号/方向/紧固、动力系统和防护完成独立适航检查；桨叶安装只能在所有无桨检查完成、飞行授权生效后进行。
- RC 发射机/接收机、人工接管和 kill 使用当前 mapping；电量足够且有备份计划。
- 主电池和备用电池状态、单体差、温度、循环/损伤记录满足批准阈值。
- QGC 通过独立批准链路监控；不得占用 DDS 专用 `/dev/ttyTHS0`，不得形成 ROS/PX4 command 竞争。
- 地面站、伴随计算机、PX4、定位/视觉（如适用）和记录设备时钟可关联。
- 起降区、缓冲区、人员边界、fire containment、急救和通信均就绪。
- 当前仓库历史记录没有可用 PX4 USB；若 QGC 独立链路仍未确定，则有限实机为 `BLOCKED`。

## 5. 软件、firmware、参数和 transport

### 5.1 Source/software identity

飞前在不启动控制链时记录：

```bash
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git rev-parse HEAD
git status --short
git rev-parse HEAD:workspace.lock.repos
```

根 HEAD、lock、所有受管依赖/dirty receipt、toolchain、Agent binary、profile/config hash 必须与 `BENCH_VERIFIED` 候选一致。任何未知 dirty 状态、现场 rebuild 或 binary/hash 差异均 `no-go` 并重新执行离线检查。

### 5.2 Firmware

- PX4 v1.16.2 exact source/submodule/toolchain 和 FMUv3 artifact SHA-256 必须与台架通过件一致。
- installed identity 必须通过批准只读方法确认；不能仅依据文件名、QGC 显示的版本号或历史 git hash。
- `rc_channels` profile 必须存在；baseline 不加入 `landing_target_pose`。
- 现场不得刷写。artifact 不一致时重新执行离线检查、正式 SITL 和拆桨台架。

### 5.3 参数快照

- 飞行前通过批准只读通道采集完整 current snapshot，绑定 installed firmware、capture time、工具和 hash。
- 与 `BENCH_VERIFIED` snapshot 逐项比较；任何未批准差异为 `no-go`。
- 2026-07-24 历史快照只能标 `HISTORICAL_EVIDENCE`，不能证明当前 transport、RC、failsafe 或 EKF2 参数。
- 飞行后重复采集并比较；意外参数变化触发设备隔离和调查。

### 5.4 Transport

- 单飞行器、单 PX4 client、单 Micro XRCE-DDS Agent、单 root namespace `/`、单批准 ROS domain。
- `/dev/ttyTHS0:921600` 仅由 DDS Agent 独占；第二 Agent、历史 serial 或其他飞控传输禁止复用。
- client key、domain、system/component identity 和 Agent command/profile 与台架一致。
- QGC 只使用独立批准链路；链路中断是否立即终止由 test card 定义，但不能切换到 TELEM2 fallback。

## 6. 检查命令与预期结果

本文只列飞前只读检查，不授权启动 Agent 或控制 action。只有批准链路已启动且飞行器保持 disarmed、test director 宣布进入 preflight gate 后，才可运行：

```bash
ros2 node list
ros2 topic list -t
ros2 topic info -v /fmu/out/vehicle_status_v1
ros2 topic info -v /fmu/out/rc_channels
ros2 topic info -v /fmu/out/battery_status
ros2 topic info -v /fmu/out/vehicle_odometry
ros2 topic info -v /fmu/out/vehicle_land_detected
ros2 topic info -v /fmu/out/vehicle_command_ack
ros2 topic info -v /fmu/in/trajectory_setpoint
ros2 topic info -v /fmu/in/offboard_control_mode
ros2 topic info -v /fmu/in/vehicle_command
ros2 topic info -v /offboard/cmd
ros2 topic info -v /offboard/cmd_mode
ros2 topic info -v /offboard/takeoff_land
```

预期：

- PX4/Agent/vehicle/profile identity 全部匹配；telemetry fresh，battery/RC/status/odom/landed 合法；
- 三个 `/fmu/in/*` 控制 topic 只有 `/offboard_control_node` 一个批准 writer；
- 三个 `/offboard/*` topic 只有当前 arbiter lease owner；
- 没有旧 bringup、mock、demo/animal、swarm、第二 Agent 或未知 writer；
- 未授予 lease、未完成 readiness/PRESTREAM 时，控制 payload 发布计数为 0；
- vision 不在 scope 时 publisher 为 0；在 scope 时只有已批准 `/vision_to_dds_node`；
- QGC 与 ROS graph 不构成第二控制源，且未占用 `/dev/ttyTHS0`。

`ros2 topic info` 不能独立证明 PX4 消费、RC 物理映射或安全行为；这些必须已有 SITL/台架 evidence 并由本次 health 交叉确认。

## 7. 飞行 test card 阶段

精确 arm/mode/setpoint 命令和自动故障动作不在本草案中给出。批准 test card 至少应包含以下 gate，且每一步独立双签：

### F0 — 场地和身份

确认人员、适航、场地、天气、空域、source、firmware、参数、transport、QGC、日志、rollback。所有人复诵 stop/接管口令。未全绿不得安装/激活动力进入后续步骤。

### F1 — Disarmed readiness

确认 graph、feedback、RC/kill、owner 无 lease时 no-output、PX4/Agent reboot 检测和日志。此阶段不 arm、不进入 Offboard。

### F2 — 人工接管与终止能力

按批准 test card 在地面/台架已证明的基础上复核 RC、kill、QGC 和口令链。任何控件、状态或人员响应不一致立即 no-go。

### F3 — 最小控制场景

只执行一个已在 SITL 和拆桨台架通过的场景；包线由数字限制定义。进入下一步前必须回到批准稳定状态、保存事件、由 PIC/observer/test director 重新 go。

### F4 — 批准故障场景

默认 `BLOCKED`。只有 hazard analysis 证明可在飞行中安全注入、且对应动作/deadline 已经 SITL 和台架通过，才可纳入。RC/DDS/odom/status/battery/owner/vision loss、PX4 reboot 和 Agent restart 不得为“完整矩阵”而盲目实飞注入；无法安全注入的项目保留 `UNVERIFIED` 或由低层证据覆盖。

### F5 — 结束与飞后

PIC 确认终止飞行；按批准程序 disarm、动力隔离、移除桨叶后进入飞后检查。封存日志，采集飞后参数，检查硬件，执行必要 rollback。任何异常都不安排同日自动复飞。

## 8. go 条件

仅当以下全部成立，PIC 才可对 test card 当前一步给出 go：

- 本次精确候选 `SITL_VERIFIED` 且 `BENCH_VERIFIED`；所有适用 P0/P1 关闭；
- 授权、法规、场地、空域、天气、包线和人员有效；
- source/software/firmware/参数/transport/QGC/logging/rollback identity 完全匹配；
- 飞行器、电池、RC、kill、人工接管、地理围栏和起降区通过；
- graph writer/owner/Agent 基数正确，所有权威 feedback fresh；
- 上一步完成且没有 open anomaly；
- PIC、safety pilot、test director、observer、recorder 均明确同意；
- stop/接管动作和通信链路已复诵。

go 只对当前一步和限定时间有效，不自动继承到下一步。

## 9. no-go 条件

- 拆桨台架只有文档或只读结果，没有实际 `BENCH_VERIFIED`；
- 任一 P0/P1 未关闭、重开或只做风险接受；
- 当前 firmware/参数未知，或与台架候选有任何未批准差异；
- QGC 无独立链路、DDS 串口不独占、出现未知/重复 writer/owner/Agent；
- 人员不足、角色不清、通信/接管/kill 未确认；
- 电池/机体/桨叶/动力/传感器/定位/日志/clock/场地/天气任一超限；
- test card 未填写数字包线、fault action、deadline、rollback 或授权失效时间；
- 需要现场修改代码、参数、firmware 或扩大 scope 才能继续；
- 任一参与者不同意继续。

## 10. 立即停止条件

任一人员可叫停且无需解释。至少包括：

- 超出 geofence、批准高度/速度/姿态/距离/时长或场地边界；
- 非预期航迹、姿态、振动、动力、声音、温度、电流、电池或结构状态；
- RC/kill/人工接管/QGC/地面通信失效或状态不一致；
- DDS loss、Agent restart、PX4 reboot、VehicleStatus stale、odometry loss、battery stale、owner loss、vision loss/freeze；
- ACK 拒绝/超时/错配、fault event/deadline 偏离批准状态表；
- graph 出现额外 writer、第二 Agent 或 identity/domain/namespace 变化；
- GPS/定位/视觉/气象/能见度/空域/人员条件超出批准限制；
- 日志、时钟或 evidence recorder 中断；
- PIC、safety pilot、observer、test director 或 recorder 任一喊停。

具体应执行 Land、Position、保持 PX4 failsafe、停止 Offboard 输出还是人工接管，必须由逐飞行阶段 hazard analysis 和批准应急卡决定。本文不替安全评审做选择；未决定时有限实机保持 `BLOCKED`。

## 11. 预期结果与判定

- test card 中每个正常步骤的状态、ACK、feedback、轨迹误差和 deadline 落在批准范围；
- stop/接管发生时，事件顺序与批准卡一致且无自动恢复 ACTIVE；
- 所有 writer/owner/transport 身份全程不变；
- 飞后参数无意外变化，硬件检查无异常；
- raw logs、QGC/PX4/ROS timeline 和人员观察可以相互关联；
- 未运行或不可安全注入的场景明确为 `UNVERIFIED`，不得因相邻场景通过而提升。

任一步失败使该 run 为 no-go；不得通过删除异常区间、重跑取最好结果或口头解释改成通过。

## 12. evidence 要求

- 书面授权、法规/场地批准、hazard analysis、test card 版本和人员签字；
- root remote/branch/HEAD/status、lock/dependency/toolchain/Agent/profile/config identity；
- PX4 source/submodule/artifact/installed identity 和 SHA-256；
- 飞前/飞后完整参数快照及差异；
- 飞行器配置、电池、RC/kill、QGC 独立链路、DDS 串口 owner 和物理检查；
- graph/topic/type/QoS/source inventory、lease/owner、ACK/freshness/fault event；
- PX4 flight log、Agent/ROS logs、QGC log、地面观察和统一 timeline；
- 每一步 go/no-go/stop 的时间、发令人、响应和实际结果；
- 包线数据、异常、skipped/not-applicable/`UNVERIFIED` 项；
- 飞后硬件检查、参数差异、rollback 和设备隔离结果；
- 公开摘要不得含真实硬件唯一标识、个人 home 路径或未脱敏联系人。

## 13. rollback 与失败处置

1. 按批准应急卡安全终止当前飞行，不在空中尝试临时软件修复。
2. 落地后确认 disarmed、动力隔离；移除桨叶，回到拆桨台架物理状态。
3. 停止所有 ROS writer 和 Agent，确认 DDS 串口释放；封存原始 evidence。
4. 采集飞后完整参数并核对 firmware/source/profile identity。
5. 在拆桨台架按已演练 manifest 恢复已知良好 firmware、参数、software 和 transport。
6. 重新执行相应的离线检查、正式 SITL 和拆桨台架；影响边界不明时从离线检查开始。
7. rollback 失败或硬件异常时锁定/隔离飞行器，状态为 `BLOCKED`，不得复飞。

rollback 后不自动恢复有限实机资格；必须完成 anomaly review 并获得新的授权。

## 14. 完成条件与后续边界

只有批准 test card 的全部 required step 通过、无 open P0/P1/anomaly、evidence 完整、飞后/rollback 处理完成且 independent reviewer 签字，才能把该精确场景标为 `FLIGHT_VERIFIED`。

有限实机通过不自动启用 production：

- production 继续 `BLOCKED`；
- 扩大包线、新 mission、视觉、precision landing、不同 firmware/参数/硬件均是新验证对象；
- production enable 需要独立 release manifest、known limitations、rollback、owner 权限和维护者决策，不由一次有限实机飞行授权。
