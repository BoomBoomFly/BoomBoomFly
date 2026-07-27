# Wave 3A H — Preliminary hardware inventory

- 日期：2026-07-27
- 角色：Safety/Test Coordinator（本轮唯一硬件访问线程）
- 分类：`PRELIMINARY_OS_INVENTORY`
- H0 结论：`BLOCKED`
- H2：`NOT_STARTED`
- Evidence 限制：本记录不是正式 H0、bench、SITL、hardware acceptance 或 production
  evidence

## 授权与实际边界

维护者授权只读 hardware inventory 与拆桨 disarmed bench，但本次仅执行不会向设备
发送数据的 OS/udev/USB inventory。没有打开串口、video 或 hidraw device；没有启动
Agent、MAVROS、Offboard、vision、ROS node、hardware launch 或 PX4 SITL；没有写参数、
重启、刷写、arm、切 mode、takeoff 或发送 actuator/VehicleCommand/setpoint。

未读取、输出或保存 USB/设备永久 serial。udev 输出仅保留 DEVNAME、VID:PID、
vendor/model、V4L product、driver 和物理 path 白名单字段。

## 执行的只读 probe

| Probe | 只读目的 | 结果 |
|---|---|---|
| 相关 `/dev` character node 枚举 | 节点存在性，不打开节点 | exit 0 |
| `lsusb` | USB VID:PID 与产品描述 | exit 0 |
| `lsusb -t` | USB interface/driver tree | exit 0 |
| 相关 `/sys/class/tty` symlink 枚举 | 板载 tty sysfs 映射 | exit 0 |
| `udevadm info --query=property --name=...` + 属性白名单 | model/VID:PID/driver/path；过滤 serial | exit 0 |

没有运行可能进行协议握手或写设备的 probe。

## Preliminary OS inventory

### Serial/flight-controller candidates

| OS node | OS mapping | Product/driver identity | 判定 |
|---|---|---|---|
| `/dev/ttyTHS0` | platform `3100000.serial` | udev 仅返回 DEVNAME | 板载 UART；用途和连接端未知 |
| `/dev/ttyTHS1` | platform `3110000.serial` | udev 仅返回 DEVNAME | 板载 UART；用途和连接端未知 |
| `/dev/ttyTHS3` | platform `3130000.serial` | udev 仅返回 DEVNAME | 板载 UART；用途和连接端未知 |
| `/dev/ttyTHS4` | platform `3140000.serial` | udev 仅返回 DEVNAME | 板载 UART；用途和连接端未知 |
| `/dev/ttyACM*` | 未发现 | 无 | 没有可由 OS 识别的 USB CDC 飞控候选 |
| `/dev/ttyUSB*` | 未发现 | 无 | 没有可由 OS 识别的 USB serial 候选 |

存在 `/dev/ttyTHS0` 不证明它连接飞控，也不证明 transport、PX4 identity 或 disarmed。
为避免向未知 UART 发送数据，本次未打开任何 tty。

### USB/video inventory

| Nodes/interface | VID:PID | udev product | Driver | 初步分类 |
|---|---|---|---|---|
| `/dev/video0`–`/dev/video5` | `8086:0b07` | Intel RealSense Depth Camera 435 | `uvcvideo` | RealSense video interfaces；未打开 |
| `/dev/video6`–`/dev/video7` | `0bda:5858` | Generic USB Camera2 | `uvcvideo` | USB camera interfaces；未打开 |
| `/dev/hidraw0` | parent USB tree `0bda:5858` | udev 白名单只返回 DEVNAME | USB tree 显示 `usbhid` | camera-associated HID candidate；未打开 |
| USB interface | `03e7:2150` | Intel Myriad VPU | 无绑定 driver 显示 | accelerator candidate；未打开 |
| USB interface | `0bda:c822` | Realtek Bluetooth Radio | `btusb` | 非飞控控制链 inventory |

USB hubs/root hubs 已观察但不列为被测设备。该表不证明 sensor health、timestamp、frame
或 estimator integration。

## H0 required identity and blockers

| H0 field | 本次状态 | Blocker |
|---|---|---|
| Disarmed confirmation | `UNKNOWN` | 没有现场 Human Operator 的同步确认；OS inventory 无法证明 |
| Airframe/model | `UNKNOWN` | 未进行飞控协议读取，且不允许打开未知 tty |
| Flight controller model/revision | `UNKNOWN` | 无 ttyACM/ttyUSB identity；板载 UART 用途未知 |
| Current PX4 version/git identity | `UNKNOWN` | 需要经批准的只读飞控会话 |
| Bootloader/current firmware target | `UNKNOWN` | 同上 |
| Parameter hash | `UNKNOWN` | 同上；未读写参数 |
| Sensor health | `UNKNOWN` | 仅枚举 USB/V4L 节点，未打开 sensor |
| RC health/takeover | `UNKNOWN` | 无安全只读飞控 session |
| Estimator validity | `UNKNOWN` | 无 PX4 telemetry session |
| DDS endpoint/client identity | `UNKNOWN` | 未启动 Agent 或读取飞控 transport |
| Safety switch / physical disconnect | `UNKNOWN` | 缺现场核验 |
| Arm/prearm health/rejection | `UNKNOWN` | 未建立只读 PX4 status session |

因此无法安全确认 H0 identity 完整性或 disarmed。按 fail-closed 规则，在 OS inventory 后
立即停止设备交互：

```text
H0 IDENTITY: BLOCKED
DEVICE INTERACTION: STOPPED
H1 FIRMWARE CONFIRMATION: NOT_STARTED
H2 PROP-OFF DISARMED BENCH: NOT_STARTED
H3 PROP-OFF ARMED BENCH: NOT_AUTHORIZED_FOR_THIS_SESSION
H4 FAULT VALIDATION: NOT_STARTED
```

## 为什么 H2 未开始

维护者已授权安排 prop-off disarmed bench，但授权不替代当次现场前置确认。本 session
缺少：

- Human Operator 对 disarmed 的同步确认；
- Safety Officer 在场和可验证的物理断电/急停；
- 机体固定与逐电机拆桨复核；
- airframe/FC/PX4/firmware/parameter exact identity；
- 经静态证明不含 `/fmu/in/*` publisher 的 observer-only profile；
- 预期 ROS graph、DDS endpoint、writer/owner cardinality 与 topic type/QoS 清单。

在这些条件书面完成前自动开始 H2 会扩大授权并可能打开未知控制链，因此本次保持
`NOT_STARTED`，不是 bench FAIL，也不是 bench evidence。

## 后续安全入口

1. 由现场 Human Operator 和 Safety Officer 使用
   [Prop-off bench safety runbook](../../runbooks/PROP_OFF_BENCH_SAFETY.md) 完成 H0.1。
2. 维护者批准一个已证明只读、不会发布 `/fmu/in/*` 的 PX4 identity/status 采集方法。
3. 在不暴露永久 serial 的前提下绑定 airframe、FC、PX4/target、parameter hash、
   RC/estimator/DDS/safety identity。
4. H0 完整通过后，另开 session 完成 H2 physical 与 observer-only graph checklist。
5. 若需刷写，先填写 H1 per-artifact 表并取得明确 GO；identity 变化后重做 H0。

## 固定授权状态

```text
READ-ONLY HARDWARE INVENTORY: AUTHORIZED
PROP-OFF DISARMED BENCH: AUTHORIZED
FIRMWARE FLASH: REQUIRES PER-ARTIFACT HUMAN GO
PROP-OFF ARMED BENCH: REQUIRES ON-SITE HUMAN GO
PROPELLER INSTALLATION: NOT AUTHORIZED
INDOOR FLIGHT: BLOCKED
ARM / MODE / TAKEOFF / ABORT AUTHORITY: HUMAN ONLY
PRODUCTION: BLOCKED
FLIGHT: NOT AUTHORIZED
```
