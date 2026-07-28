# 拆桨台架验收草案

> **DRAFT — 不得直接执行**
>
> 文档状态：`IMPLEMENTED`（草案已记录）
>
> 验收状态：`UNVERIFIED`
>
> 台架状态：`BLOCKED`
>
> 本轮未访问硬件、未启动节点、未刷写、未写参数、未 arm、未发送 `/fmu/in/*`。

本文是拆桨台架的安全评审输入，不是操作授权、已批准 test card 或台架 evidence。只有所有 P0 关闭、适用 P1 关闭、正式 SITL 为 `SITL_VERIFIED`，且维护者签发精确范围的硬件授权后，才能把本草案转为受控 runbook。production 仍为 `BLOCKED`。

## 1. 目标

在桨叶全部拆除、机体可靠固定、动力区隔离且具备人工急停的实机台架上，分阶段验证：

1. firmware/software/参数/transport 身份一致；
2. `/dev/ttyTHS0` 由唯一 DDS transport 独占；
3. QGroundControl（QGC）通过独立批准链路只读监控，不争用 TELEM2；
4. graph writer、mission owner、Agent 和 PX4 feedback 权威关系；
5. disarmed/no-output、RC/kill、ACK/freshness/PRESTREAM 和 fault latch；
6. 在另行批准后才进行最低能量的 actuator/control test；
7. 停止、断能、日志封存和 firmware/参数/software rollback。

台架通过只允许标记精确候选为 `BENCH_VERIFIED`，不代表桨上测试、自由飞行或 production。

## 2. 允许与禁止

### 允许

- 已签发 test card 内的只读 identity、参数、transport、graph 和 telemetry 检查；
- 默认 disarmed、propulsion power isolated 的预检；
- 已批准的 RC/kill 信号链检查；
- 在所有前序门通过后、按单独授权执行的最低能量 actuator test；
- 保存脱敏 evidence 和实际 rollback 演练。

### 禁止

- 安装任何桨叶或让机体处于自由状态；
- 单人操作或无观察员操作；
- 跳过正式 SITL、P0/P1、安全评审或双人确认；
- 在 test card 之外 arm、切换 mode、发送 setpoint/VehicleCommand 或 `/fmu/in/*`；
- 使用第二条飞控传输作为 production fallback；
- 让 QGC 或历史 serial 与 DDS 共用 `/dev/ttyTHS0`；
- 运行旧 `px4_bringup`、demo/animal、mock RC、swarm 或 precision landing baseline；
- 在台架现场临时构建 firmware、修改源码、变更参数后继续测试；
- 把 runbook 演练、只读 session 或电机未动等同于控制闭环通过。

## 3. 前置条件

### 3.1 工程门

- [ ] 所有 P0 已关闭且有独立 reviewer evidence。
- [ ] 适用于台架的 P1 已关闭：DDS-only 边界、firmware profile、CI、安全测试、SITL、transport identity、参数 schema、runbook/rollback。
- [ ] 精确候选在正式 SITL 中已标 `SITL_VERIFIED`。
- [ ] graph guard、owner/lease、VehicleCommand ACK、freshness、PRESTREAM、RC hard gate、kill latch 和 fault lattice 均不是 `PLANNED`。
- [ ] PX4 v1.16.2 `rc_channels` firmware artifact 已完成 FMUv3 build，source/submodule/toolchain/artifact SHA-256 完整。
- [ ] baseline precision landing 关闭；当前只支持单机根 namespace。
- [ ] evidence schema、日志目录、容量/时钟检查和失败保留策略已就绪。

### 3.2 授权门

- [ ] 维护者批准日期、设备范围、firmware、参数、允许动作和失效时间。
- [ ] safety reviewer 批准每个故障动作、deadline、恢复门和人工复位。
- [ ] test director 签发逐步 test card；默认 `no arm`，任何例外逐项列明。
- [ ] firmware flash、参数写入、Agent 启动、control action 分别获得所需授权；不得由本草案推定。
- [ ] 发生异常时，operator、observer 和 test director 任一人均有无条件 stop 权。

### 3.3 物理门

- [ ] **全部桨叶已拆除**，逐电机/逐桨位由 operator 与 observer 目视并双签。
- [ ] **机体固定**于能承受最大批准 actuator output 的台架；绑带/夹具避开电机、线束和传感器。
- [ ] 电机扫掠区、碎片区和电池危险区设警戒线，无松散物体。
- [ ] 具备可达的**急停/动力隔离**；observer 无需进入危险区即可操作。
- [ ] 遥控器可用，电量充足，failsafe/kill 控件有清晰物理标识。
- [ ] kill switch 的 PX4 mapping 和 Offboard 消费契约有当前只读证据；历史参数快照不能替代。
- [ ] 电池外观、单体差、总电压、温度和预计测试时长满足批准阈值。
- [ ] 逻辑/伴随计算机供电与 propulsion power 可隔离；接线顺序和保险/限流能力已批准。
- [ ] QGC 监控链路独立于 `/dev/ttyTHS0`，且不会创建第二控制 writer。
- [ ] 测试区域具备适合电池类型的消防/隔离措施和疏散路径。

## 4. 人员角色与双人确认

| 角色 | 最小职责 | 不得跳过的确认 |
|---|---|---|
| test director | 冻结 test card、决定开始/暂停/结束 | 每个 gate 的 go/no-go；scope 变更一律 no-go |
| operator | 操作伴随计算机、RC 和批准步骤 | 逐命令复诵、观察预期、异常立即停 |
| observer / safety officer | 独立观察机体、动力、电池、人员和急停 | 桨叶拆除、固定、急停、RC/kill、危险区清空 |
| evidence recorder | 记录 identity、时间、原始日志、签字 | 日志持续、clock 对齐、结果不被覆盖 |
| firmware/control reviewer | 核对 artifact/profile/状态机契约 | SHA/参数/故障动作与正式 SITL 完全一致 |

最少两名现场人员：operator 与 observer 必须是不同人员。test director 是否可兼任由风险评审决定并记录。每一步采用 challenge-response：test director 读出步骤和预期，operator 回读动作，observer 确认物理状态，recorder 标记时间，随后才执行。

## 5. 设备与版本记录

### 5.1 Source/software

记录而不依赖文档中的旧 HEAD：

```bash
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git rev-parse HEAD
git status --short
git rev-parse HEAD:workspace.lock.repos
```

要求：根 checkout、lock、受管依赖、toolchain、Agent binary 和配置 hash 必须与 `SITL_VERIFIED` 候选一致。任何 dirty 差异必须由现有 receipt 解释；未知差异为 `no-go`。

### 5.2 Firmware

| 字段 | 必填 |
|---|---|
| PX4 release/source | v1.16.2 + exact source SHA |
| submodules/toolchain | 清单/hash |
| board target | `px4_fmu-v3_default` 或维护者批准的实际 target |
| artifact | 文件名、SHA-256、构建 evidence |
| topic profile | `rc_channels` publication；baseline 无 `landing_target_pose` |
| installed identity | 经批准的只读方式确认；无法确认即 `BLOCKED` |
| rollback artifact | 上一已知良好 artifact SHA-256 和可用介质 |

本文不授权刷写。候选未安装时不得继续；安装步骤必须来自另行批准的 firmware runbook。

### 5.3 参数快照

台架前必须通过不争用 DDS transport 的批准只读通道采集当前完整参数快照，并记录 firmware identity、工具/命令、capture time、数量和 hash。2026-07-24 快照只能作为 `HISTORICAL_EVIDENCE` 比较。

至少审查：DDS transport/domain、TELEM2 独占、RC offboard/kill mapping、RC loss、Offboard loss、battery/failsafe、airframe、EKF2/vision disabled baseline。参数的预期值与回滚值由安全评审批准，本文不自行规定。

参数未知、只采关键子集、capture 不完整、firmware 不匹配或没有回滚值：`no-go`。

### 5.4 Transport

- `/dev/ttyTHS0:921600` 仅供本次单一 Micro XRCE-DDS Agent 使用；device owner、Agent PID/binary/command/profile 进入记录。
- Agent 启动前检查端口无 owner；启动后检查恰好一个批准 owner；停止后检查端口释放。
- 不允许第二个 Agent 或历史 serial 进程。
- QGC 必须使用维护者批准的独立链路；当前仓库记录没有可用 PX4 USB，因此 QGC 链路未定义时台架为 `BLOCKED`。
- ROS domain、根 namespace、client key、system/component identity 与正式 SITL profile 一致。

## 6. 日志与证据准备

日志根目录必须由 evidence 系统为本次 run ID 创建；不得使用个人 home 路径写入文档。开始前确认：

- source/firmware/parameter/profile/Agent identity 文件；
- PX4 log、Agent transcript、ROS logs、graph snapshots、QGC telemetry log；
- 独立时间源和时钟偏差记录；
- 原始 stdout/stderr、退出码、事件 timeline；
- 物理 checklist、双签、脱敏照片或等价证据；
- 充足磁盘空间和失败日志不可覆盖策略；
- firmware/参数/software/transport rollback manifest。

日志路径不可用、写入中断、时间戳回退或磁盘不足均为立即停止条件。

## 7. 分阶段 test card 草案

每个 gate 独立 go/no-go；失败后禁止跳到下一 gate。

### Gate B0 — 断能物理检查

设备状态：propulsion power isolated，飞控/伴随计算机是否供电由已批准接线图决定。

1. 双人确认桨叶拆除、机体固定、危险区清空。
2. 确认急停/动力隔离可达且标签清楚；不通过软件验证。
3. 确认 RC 和 kill 控件物理状态符合 test card 的 safe position。
4. 检查电池、线束、极性、保险/限流和供电隔离。
5. 确认 QGC 独立监控链路、日志和 rollback 包可用。

预期：所有物理门双签。任一不确定即 `no-go`。

### Gate B1 — Identity 与只读参数

保持 propulsion power isolated、disarmed：

1. 记录 root/lock/toolchain/Agent/profile identity。
2. 按单独批准步骤确认 installed firmware identity。
3. 采集当前完整只读参数，比较批准 target 和 rollback 值。
4. QGC 以只读监控权限显示一致的 firmware、disarmed、battery 和 failsafe 状态。
5. 确认 QGC 没有占用 `/dev/ttyTHS0`，没有创建 ROS control writer。

预期：identity 和参数完全匹配。任何差异不得现场修后继续；回到变更流程并重新执行离线检查。

### Gate B2 — DDS transport 只读

保持 Offboard、mission owner 和 vision writer未启动；不发布 `/fmu/in/*`。

未来批准的只读检查可包括：

```bash
ros2 node list
ros2 topic list -t
ros2 topic info -v /fmu/out/vehicle_status_v1
ros2 topic info -v /fmu/out/rc_channels
ros2 topic info -v /fmu/out/battery_status
ros2 topic info -v /fmu/out/vehicle_odometry
ros2 topic info -v /fmu/out/vehicle_land_detected
ros2 topic info -v /fmu/out/vehicle_command_ack
```

预期：一个 PX4 participant/client、一个 Agent、权威 PX4 输出存在且 freshness/type/QoS/source 匹配；没有 `/fmu/in/*` ROS writer。此门只证明 transport/feedback，不是 control 验收。

### Gate B3 — Disarmed graph guard 与 no-output

保持 propulsion power isolated、disarmed：

1. 启动受管 graph guard 和 Offboard，但不授予 mission lease。
2. 检查控制 input publisher 基数和节点身份。
3. 在 RC/status/odom/battery 任一缺失或 owner 未授权时，断言控制消息计数为 0。
4. 按 test fixture 注入 duplicate writer/owner；真实 graph 不得连接 mock feedback。
5. 证明冲突时拒绝 ACTIVE、锁存且不自动恢复。

预期：只验证 fail-closed 门，不 arm、不切 mode。

### Gate B4 — RC 与 kill 信号链

先保持 propulsion power isolated、disarmed：

1. 由 observer 指示 operator 操作真实 RC 模式/kill 控件。
2. 确认 `/fmu/out/rc_channels` 来自 PX4，function mapping、freshness、signal_lost 和物理控件一致。
3. 验证 RC 未收到、stale、signal_lost、错误 mapping 时 arm/mode 请求计数为 0。
4. 验证 kill 的去抖、边沿、最高优先级锁存和人工复位诊断。
5. 任何需要实际 actuator response 的 kill 验证推迟至 Gate B5，并须单独批准。

预期：mock 参数或 publisher 不能满足任何通过条件。kill 具体响应时间由批准安全契约给出，未给出则 `BLOCKED`。

### Gate B5 — 最低能量 actuator/control（默认 `BLOCKED`）

该 gate 不因本文存在而获准。必须有包含能量上限、允许 arm/mode/command、单步时长和停止动作的单独 test card。执行前再次双签：桨叶拆除、机体固定、急停、RC、观察员、电池、供电隔离、串口独占、QGC、日志和 rollback。

建议按最小增量排列，每步之间完全回到 disarmed/安全态：

1. 无 mission owner 的 no-output；
2. 只验证 PRESTREAM 门，不进入 ACTIVE；
3. ACK reject/timeout 场景；
4. 获批后才验证单个正常事务；
5. 获批后才验证 RC/kill/owner/DDS/status/odom/battery fault。

本草案不提供 arm、mode、VehicleCommand 或 setpoint 命令。具体自动故障动作必须由 safety review 决定，存在 Land/Position/停止输出争议时保持 `BLOCKED`。

### Gate B6 — 清理与实际 rollback

1. 结束 test card，确认 disarmed，按批准顺序隔离 propulsion power。
2. 停止 ROS writer 和 Agent，确认 `/dev/ttyTHS0` 释放。
3. 保存并 hash 所有日志、飞前/飞后参数和配置差异。
4. 在拆桨固定状态下按 rollback manifest 恢复已知良好 firmware/参数/software/profile。
5. 重复 B1/B2 的 identity 和只读检查，证明恢复成功。
6. rollback 失败则锁定设备、标 `BLOCKED`，不得进入有限实机。

## 8. 故障场景与安全评审门

| 故障 | 当前行为 | 台架预期 | 状态 |
|---|---|---|---|
| RC loss | 现有实现策略不闭合 | 由安全评审定义飞行阶段动作；互锁必须 fail-closed | `BLOCKED` |
| DDS loss / Agent restart | 重连安全未证明 | lease/epoch/PRESTREAM 清零，不自动恢复；具体 PX4 动作待定 | `BLOCKED` |
| odometry loss | 当前首帧/freshness 缺陷已审查发现 | 无效 setpoint 不进入 PX4；具体降级待定 | `BLOCKED` |
| VehicleStatus stale / PX4 reboot | ACK/status 闭环未实现 | 旧事务失效、需人工重新授权；具体动作待定 | `BLOCKED` |
| battery stale | 当前缺少一致策略 | 不继续未批准任务；具体动作待定 | `BLOCKED` |
| mission owner loss | owner/lease 未实现 | lease 撤销且旧 setpoint 清除；具体动作待定 | `BLOCKED` |
| vision loss | 坐标/时间/健康未闭环 | baseline 默认关闭；启用 profile 的具体动作待定 | `BLOCKED` |

任何一行未从 `BLOCKED` 转为已批准且有 SITL 证据前，不得在台架注入。

## 9. go 条件

- 物理、人员、授权、source、software、firmware、参数、transport、QGC、日志和 rollback checklist 全部双签；
- 所有 P0、适用 P1 关闭，正式 SITL 为 `SITL_VERIFIED`；
- 每个运行 gate 的前一 gate 通过；
- 结果严格匹配批准状态表/deadline；
- 无未知 publisher、mock、串口竞争或身份漂移；
- rollback 在本台架实际成功；
- independent reviewer 无未解决文档/运行 P0/P1。

只有完成全部批准 gate 后才能记为 `BENCH_VERIFIED`。只完成 B0–B2 应记录对应只读范围，不得整体通过。

## 10. no-go 条件

- 任一 P0 未关闭或适用 P1 未关闭；
- 仅有历史参数/transport evidence，当前 firmware/参数未知；
- 桨叶未全部拆除、机体未固定、急停/RC/kill/QGC/观察员/双签任一缺失；
- 电池异常、供电不能隔离、危险区未清空；
- `/dev/ttyTHS0` owner 不唯一或 QGC 需要复用该端口；
- HEAD/lock/artifact/profile/参数与 `SITL_VERIFIED` 候选不一致；
- 日志、时间同步、磁盘或 rollback 不可用；
- test card 含未评审故障动作或要求现场临时修改；
- 任一人员无法明确回答当前 gate、预期结果和 stop 动作。

## 11. 立即停止条件

任一人员可叫停；出现以下任一项必须停止当前 gate，不得自动重试：

- 人员进入危险区、固定装置松动、机体/电池/线束移动；
- 非预期电机/舵机动作、转速、振动、电流、温度、烟雾、气味或噪声；
- 急停、RC 或 kill 无效、延迟超限或状态与物理控件不一致；
- PX4/Agent/Offboard/QGC 状态、ACK 或 fault event 偏离 test card；
- DDS、RC、odom、status、battery、owner、vision 或日志意外丢失；
- 未知/重复 writer、第二 Agent、串口 owner 变化；
- firmware reboot、时钟回退、参数变化或 source identity 不再可信；
- observer、operator、test director 或 recorder 任一发出 stop。

停止后的默认人工措施是执行已批准的急停/动力隔离流程并保持人员远离危险区。是否请求 Land、Position 或停止 Offboard 输出不得由本文临时决定；必须来自已批准的分阶段安全状态表。

## 12. rollback 要求

rollback manifest 至少包含：

- 已知良好 PX4 artifact、source/submodule/toolchain、SHA-256 和可用介质；
- 台架前完整参数快照、target/rollback 差异、写入和核验步骤；
- root/lock/dependency/software/profile/Agent 版本与 hash；
- transport/domain/client key/namespace/system identity；
- 断能、恢复、重启、只读复验、失败隔离顺序；
- 负责人、双签、最大允许时间和失败升级联系人（未知时由维护者填写后方可执行）。

rollback 必须在本台架、拆桨固定条件下实际演练成功。桌面解析通过只能记为 `STATICALLY_VERIFIED`，不能记为 `BENCH_VERIFIED`。

## 13. evidence 要求

- 授权单、test card 版本、人员角色和逐 gate 双签；
- 桨叶拆除、机体固定、警戒区、急停、RC、供电隔离和 QGC 状态的脱敏记录；
- root/lock/dependency/toolchain/Agent/PX4 source/artifact/profile/参数 hash；
- `/dev/ttyTHS0` 启动前、运行中和停止后的 owner 记录；
- QGC 独立链路和只读权限说明；
- graph/topic/type/QoS/source、ACK、freshness、fault event 和响应 deadline；
- PX4/Agent/ROS/QGC 原始日志、退出码和事件 timeline；
- 飞前/飞后参数快照、差异和 rollback 实际结果；
- 每个 skipped/not-applicable/failed/unverified 项的理由；
- 敏感设备唯一标识只进入受控 evidence；公开摘要必须脱敏。

## 14. 有限实机入口

有限实机仍为 `BLOCKED`，直到：

1. 本 runbook 已由草案转为批准版本并按精确候选完整执行；
2. 候选状态为 `BENCH_VERIFIED`，不是只读 transport verified；
3. firmware/参数/software/transport rollback 在台架实际成功；
4. 所有适用 P0/P1 关闭且没有重新打开；
5. 有限实机风险评估、场地/法规/保险、飞行包线、人员和应急卡获批；
6. 实机控制获得新的明确书面授权。
