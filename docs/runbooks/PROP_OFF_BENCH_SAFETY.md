# Prop-off bench safety runbook

- 状态：**Proposed**
- 日期：2026-07-27
- owner：Safety/Test Coordinator
- 适用范围：H0 只读 identity、H1 单 artifact 刷写确认、H2 拆桨 disarmed 台架、
  H3 拆桨 armed actuator test、H4 台架故障验证
- 不包含：装桨、室内自由飞行、自动 arm/mode/takeoff、production promotion

本文是 fail-closed 操作门，不表示任何步骤已经执行或通过。每次执行必须绑定精确
repository、dependency、hardware、firmware、parameter、profile、operator 和现场时间。
历史记录或 mock/static/parser 结果不能替代当次 identity 与现场 GO。

## 授权矩阵

| 活动 | 当前授权 | 执行边界 |
|---|---|---|
| Read-only hardware inventory | `AUTHORIZED` | 仅只读识别、连接验证和状态采集 |
| Prop-off disarmed bench | `AUTHORIZED` | 必须先满足本文 H0/H2 当次现场门 |
| Firmware flash | `REQUIRES_PER_ARTIFACT_HUMAN_GO` | 只授权确认单中的一个 exact artifact |
| Prop-off armed bench | `REQUIRES_ON_SITE_HUMAN_GO` | 人工选择 mode、人工 arm、人工 disarm/abort |
| Propeller installation | `NOT_AUTHORIZED` | 不得安装螺旋桨 |
| Indoor flight | `BLOCKED` | 所有书面字段完整且最终 GO 前保持阻塞 |
| Arm / mode / takeoff / abort | `HUMAN_ONLY` | Codex、脚本和 ROS node 无此权限 |
| Production | `BLOCKED` | 台架通过也不自动 promotion |
| Flight | `NOT_AUTHORIZED` | 本 runbook 不授予飞行权限 |

维护者的设备访问授权不隐含写参数、重启、刷写、arm、mode、actuator、装桨或飞行
授权。任何歧义按权限较小的一侧处理。

## 角色与独占控制

- **Safety/Test Coordinator**：唯一 inventory/runbook/evidence owner；维护停止状态，
  不发送 arm/mode/takeoff/actuator 命令。
- **Human Operator/Pilot**：唯一 arm、mode、takeoff、disarm 和 abort authority。
- **Safety Officer**：独立 GO/NO-GO 和立即物理断电权；不得与自动化角色合并。
- **Observer/Recorder**：只读记录批准字段和事件，不控制飞行器。
- **Firmware Approver**：只对 H1 表中一个 exact artifact 作 GO/NO-GO。

Safety Officer、Human Operator 和物理断电手段任一缺席，所有 H2 以后步骤均
`NO-GO`。其他软件工作线程不得接触硬件。

## 全局禁止与立即停止条件

全阶段禁止：

- Codex、脚本或 ROS node 自行 arm、切 mode、takeoff 或 abort；
- 未确认 exact airframe/FC/target/hash/rollback 的 firmware flash；
- 未经独立批准写 PX4 参数或重启飞控；
- 装桨运行、室内自由飞行或把 mock/static 结果登记为 bench evidence；
- 输出不必要的永久唯一标识、USB serial、网络凭据或个人信息；
- 启动 Agent、Offboard、vision 或 hardware launch；
- readiness 前向 `/fmu/in/*` 发布任何消息。

以下任一条件立即物理中止并停止后续项目：

- identity 缺失/变化，或 firmware/parameter/profile 与确认记录不一致；
- 无法证明 disarmed、全部螺旋桨已拆除、机体固定或断电手段可达；
- unexpected writer、duplicate owner、graph/source epoch 变化；
- stale/future/backward timestamp、clock jump、错误 type/QoS/frame；
- invalid estimator、RC/人工接管不可用、safety switch/急停不可用；
- 实际 failsafe 与预先书面 expected failsafe 不一致；
- 任何现场人员喊停，或记录/通信不完整。

停止后不得自动恢复或继续下一项。清除故障只能回到 `READY`/disarmed，必须重新
完成适用 checklist 和人工 GO，绝不自动进入 `ACTIVE`。

## H0 — Disarmed read-only identity

### H0.1 入口门

- [ ] Human Operator 现场确认飞控 **disarmed**，并记录确认时间。
- [ ] Safety Officer 可直接触达物理断电/急停。
- [ ] 不启动任何可能写串口、ROS 或 DDS 的进程。
- [ ] 明确本轮允许使用的只读 probe 和输出字段；永久 serial 默认过滤。
- [ ] 当前连接拓扑已记录，设备重枚举时立即停止。

若无法在不发送设备数据的条件下证明 disarmed，H0 只能执行 OS preliminary
inventory；不得打开串口或开始协议握手，结论为 `BLOCKED`。

### H0.2 允许采集字段

在确认只读且不会改变设备状态的工具中采集：

- airframe/model identity；
- flight controller model、hardware revision；
- current PX4 version、git/version identity；
- bootloader、current firmware target 与 parameter hash；
- sensor、RC、estimator、DDS endpoint identity/health；
- 串口设备到功能的映射，但不记录不必要永久 serial；
- safety switch、急停/断电方式；
- arm/prearm health 与拒绝原因。

OS 级允许项仅为 `/dev` 节点存在性、USB VID:PID/product、udev/sysfs driver/path
映射。`lsusb -v`、udev `ID_SERIAL*`、设备 EEPROM/serial 查询默认禁止，除非维护者
明确证明该字段必要并批准其受控保存。

### H0.3 H0 判定

所有允许字段必须来自同一现场 session，并互相一致。任何关键字段 unknown、飞控未
映射到确定设备、无法验证 disarmed 或只读工具可能写设备时：

```text
H0 IDENTITY: BLOCKED
DEVICE INTERACTION: STOPPED
H1/H2/H3/H4: NOT STARTED
```

## H1 — Per-artifact firmware flash confirmation

H0 完整通过且维护者说明测试确实需要刷写后，Safety/Test Coordinator 生成以下确认
单。空字段、`TBD`、“以后确认”或 identity/hash/rollback 不一致均为 `NO-GO`。

```text
CURRENT AIRFRAME:
FLIGHT CONTROLLER:
CURRENT FIRMWARE:
TARGET FIRMWARE:
TARGET SHA/HASH:
PARAMETER BACKUP:
ROLLBACK IMAGE:
BOOTLOADER RECOVERY:
HUMAN APPROVER:
DECISION: GO / NO-GO
```

附加门：

- [ ] target 与 FC/bootloader compatibility 由人工复核；
- [ ] parameter backup 完整性和恢复方式已验证；
- [ ] rollback image exact hash 与 recovery procedure 已验证；
- [ ] 供电稳定、物理断电和 bootloader recovery 人员在场；
- [ ] GO 明确只授权表中一个 exact artifact。

刷写 GO 不授权参数写入、arm、mode、actuator 或 flight。刷写后 identity 变化，必须
回到 H0 重新采集；不得沿用刷写前通过状态。

## H2 — Prop-off disarmed bench

H2 当前可被人工安排，但不自动开始。每次必须先完成并签署：

### H2.1 Physical gate

- [ ] 操作区清空，非必要人员进入 exclusion zone 之外；
- [ ] 机体可靠固定；
- [ ] **逐电机确认全部螺旋桨已拆除**；
- [ ] 电池/台架供电额定值、电流限制与接线已复核；
- [ ] 物理断电手段可立即触达且做过不带载演练；
- [ ] Safety Officer 现场在场；
- [ ] Human Operator 持续确认 flight controller 为 disarmed；
- [ ] H0 exact identity 与本次 release/profile 一致；
- [ ] 未获得单独 H1 GO 时不刷写，未获参数写授权时不写参数。

### H2.2 Read-only software/graph gate

使用获批、observer-only profile，先证明它不含 `/fmu/in/*` publisher，再启动观察。
不得由 Codex 启动 Agent/Offboard/vision/hardware launch。记录：

- [ ] ROS graph epoch 和预期 node allowlist；
- [ ] DDS client/endpoint identity 与 writer cardinality；
- [ ] topic name、type、QoS 和 namespace；
- [ ] control writer 与 owner cardinality 均符合批准 profile；
- [ ] sensor health、timestamp monotonicity、frame 和 estimator validity；
- [ ] RC health 与人工接管链路；
- [ ] safety switch、prearm/arm health 与拒绝原因；
- [ ] Offboard heartbeat、ACK、freshness、PRESTREAM 仅作只读观察；
- [ ] readiness 前所有 `/fmu/in/*` 实际 publish count **恰为 0**。

若观察 profile 自己可能发布 `/fmu/in/*`，H2 `NO-GO`。H2 不要求也不允许为了“验证
计数”发送测试 setpoint/VehicleCommand。

### H2.3 H2 stop/go record

```text
SESSION ID:
REPOSITORY HEAD:
DEPENDENCY/PROFILE ID:
AIRFRAME / FC / FIRMWARE:
PARAMETER HASH:
PROPS REMOVED VERIFIED BY:
DISARMED VERIFIED BY:
POWER LIMIT / PHYSICAL DISCONNECT:
SAFETY OFFICER:
GRAPH / DDS IDENTITY:
/fmu/in/* PRE-READINESS PUBLISH COUNT:
STOP CONDITIONS ARMED:
DECISION: GO / NO-GO
```

H2 GO 只授权 disarmed observation，不自动授权 H3。

## H3 — Prop-off armed actuator test

H3 不得由 Codex 自动开始。即使 H2 通过，也必须取得当场独立人工 GO：

```text
AIRFRAME FIXTURE VERIFIED BY:
ALL PROPELLERS REMOVED VERIFIED BY:
PERSONNEL EXCLUSION VERIFIED BY:
PHYSICAL DISCONNECT OPERATOR:
HUMAN-SELECTED MODE:
HUMAN ARM OPERATOR:
HUMAN DISARM/ABORT OPERATOR:
COMMAND SOURCE:
ACTUATOR/CHANNEL SCOPE:
MAXIMUM ACTUATOR OUTPUT:
MAXIMUM DURATION:
LOSS-OF-LINK ACTION:
STOP CONDITIONS:
SAFETY OFFICER:
ON-SITE DECISION: GO / NO-GO
```

所有字段必须具体且可测量。Codex 只能记录状态和 evidence，不得发送 arm、mode、
takeoff 或 actuator command。需要 actuator command 时，人工必须确认具体 source、
通道、上限、持续时间和失联动作；Human Operator 执行 arm/mode 并始终拥有即时
disarm/中止权。

输出、时间或模式任一越界立即物理断电，不做自动 retry。

## H4 — Bench fault validation

H4 每项是独立测试；前一项通过不能授权下一项。每项开始前填写：

```text
FAULT CASE:
INITIAL DISARMED/ARMED STATE:
EXPECTED PX4 STATE TRANSITION:
EXPECTED ACTUATOR BEHAVIOR:
EXPECTED EVENT CODE / TIMEOUT:
EXPECTED RC / DATA-LINK BEHAVIOR:
PHYSICAL ABORT TRIGGER:
PARAMETERS READ AND CONFIRMED:
HUMAN OPERATOR:
SAFETY OFFICER:
CASE DECISION: GO / NO-GO
ACTUAL RESULT:
STOP / CONTINUE DECISION:
```

逐项候选：

1. Offboard heartbeat loss；
2. RC loss；
3. data-link loss；
4. stale setpoint；
5. owner/lease loss；
6. estimator invalid；
7. duplicate writer；
8. 进程重启与 source/graph epoch 变化。

fault injection source 必须由人工批准，且不得绕过 H3 authority。实际状态、timeout、
actuator 或 failsafe 与 expected 任一不符，立即物理中止并禁止继续下一项。

执行任何 armed Offboard loss 测试前，必须只读确认并由人工书面解释：

- Offboard 控制信号在进入 Offboard 前持续超过 1 秒；
- 保持频率高于 2 Hz；
- exact `COM_OF_LOSS_T`；
- exact `COM_OBL_RC_ACT`；
- 这些值在室内拆桨固定台架上的具体后果和 abort 方法。

不得使用 PX4 默认值、历史参数快照或“预期默认”代替当次读取和人工决策。

## Indoor flight gate

当前固定状态：

```text
PROPELLER INSTALLATION: NOT AUTHORIZED
INDOOR FLIGHT: BLOCKED
FLIGHT: NOT AUTHORIZED
```

未来只有所有字段由人工书面填写并最终明确 GO，才可提交新的授权审查；本文不会自动
解除阻塞。任何空字段、`TBD` 或“以后确认”均等同 `NO-GO`。

```text
AIRFRAME / TAKEOFF MASS:
FLIGHT CONTROLLER / FIRMWARE:
INDOOR CONTAINMENT DIMENSIONS:
PEOPLE EXCLUSION ZONE:
MAXIMUM ALTITUDE:
MAXIMUM HORIZONTAL RADIUS:
MAXIMUM HORIZONTAL SPEED:
MAXIMUM VERTICAL SPEED:
TAKEOFF / CONTROL / LANDING MODE:
POSITION SOURCE:
RC LOSS ACTION:
OFFBOARD LOSS ACTION:
DATA-LINK LOSS ACTION:
POSITION / ESTIMATOR LOSS ACTION:
LOW-BATTERY ACTION:
BOUNDARY OR GEOFENCE ACTION:
EMERGENCY LANDING AREA:
PHYSICAL KILL / DISARM METHOD:
PILOT:
SAFETY OFFICER:
GO / NO-GO:
```

不得使用 PX4 默认参数替代人工决策。即使该表未来完整，它也只构成重新审查输入，
不会追溯授权 Codex、脚本或 ROS node 控制 arm/mode/takeoff/abort。

## Evidence 与状态升级规则

- preliminary OS inventory 只能标记设备节点和 udev/USB 映射；不是 H0 完整通过。
- 正式 H0/H2/H3/H4 evidence 必须绑定同一 session 的 exact identities、原始只读日志、
  操作员/安全员签字、GO/NO-GO 和停止事件。
- mock/static/parser/unit 结果不得晋级为 SITL、bench、hardware 或 production evidence。
- H2 通过不自动授权 H3；H3/H4 通过不授权装桨、flight 或 production。
- identity、firmware、parameter hash、profile 或现场布置任一变化，退回适用前置门。
