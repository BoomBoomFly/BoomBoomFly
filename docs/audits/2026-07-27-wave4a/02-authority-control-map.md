# 权威控制链复核

结论：当前不存在可接受的唯一、已验证 production authority chain；`H0: NO-GO`。

| 路径 | 控制/执行能力 | 当前证据 | 判定 |
|---|---|---|---|
| `offboard_node` → `CtrlFSM` | `/fmu/in/trajectory_setpoint`、`offboard_control_mode`、`vehicle_command` | `node.cpp:28-35` 创建 writer；`CtrlFSM.cpp:339-340,405-416` 直接 publish | P0：正式 writer 绕过 tested gate |
| `CtrlFSM` arm/mode | ARM、takeoff/land、OFFBOARD/POSCTL/ALTCTL VehicleCommand | `CtrlFSM.cpp:434,471,506,621-739`；无 ACK subscription | P0：无 ACK/RC/kill 闭环 |
| Offline runtime gate | 可进行 authority/epoch/prestream/ACK/stale/restart 判定 | standalone C++ 和 Python contract PASS；未由 node 使用 | 仅测试 oracle，不是 production authority |
| MAVROS/offboard_py/px4_bringup | MAVROS command/service 与 ttyTHS0 配置 | `src/offboard_py/px4_start_demo.py:46-60,110,117,147,191`；`px4_bringup/.../px4.launch.py:11-44` | DDS-only profile 禁止；源码仍在，未获节点级隔离证据 |
| serial_driver_ros | `/cmd_vel`→serial frame→port write | `serial_main.cpp:13-39`、`serial_driver.cpp:6-32` | P0 第二执行链；仅 discovery quarantine |
| vision_to_dds | PX4 vision messages | `vision_to_dds.cpp:262-350` | disabled/未验证 health gate；不得作为安全输入使用 |

## 发现 BBF-W4A-AUTH-001

- 严重级别：P0；历史结论：DDS-only 是规范，但 live node 未接 gate。
- 当前文件和行号：见上表 offboard 及 `CMakeLists.txt:43-77,113-120`。
- 当前证据：all `/fmu/in/*` writer 与 VehicleCommand 流未收敛；ACK wire message 本身与 tested gate 所需 correlation fields 也未完成 adapter 映射。
- 状态：OPEN；影响：重复控制、拒绝/超时后输出、重启残留状态无法排除。
- 修复：只保留一个 production adapter/writer；MAVROS、serial、历史 demo 都须在 production discovery/launch 为零；写入 authority map/lease/epoch/ACK contract。
- 验收命令：static writer inventory 仅剩 adapter；fake transport duplicate-owner/restart/reject tests 全部零输出；H3 后才可验证隔离 graph。
- 阻塞 H0-H6：是。

## 发现 BBF-W4A-AUTH-002

- 严重级别：P0；历史结论：auto-arm、mock RC、无 ACK 为 OPEN。
- 当前文件和行号：`CMakeLists.txt:33-35`、`ctrl_param.yaml:12-16`、`CtrlFSM.cpp:405-477,621-739`。
- 当前证据：TEXT_RC 与 default auto-arm 仍可编入/加载；不存在 `VehicleCommandAck` ROS subscription。
- 状态：OPEN；影响：arm/takeoff/land/mode 权限未被 fail-closed authority policy 独占。
- 修复：默认关闭 auto-arm，physical RC + kill latch + accepted ACK + human-approved command envelope。
- 验收命令：所有无效输入与 ACK 失败下 ARM/mode/takeoff/land command count=0。
- 阻塞 H0-H6：是。

## 必须采用的目标链

```text
validated inputs + physical RC/kill + authority lease
                 │
                 ▼
single production runtime gate ──(accepted correlated ACK/status/epoch)──► single DDS writer
                 │ failure/restart/stale/timeout
                 └────────────────────────────────────────────────────────► zero output / latched manual recovery
```

Serial、MAVROS、demo、vision 等路径在未获各自审批和验证前不得成为该链的旁路。
