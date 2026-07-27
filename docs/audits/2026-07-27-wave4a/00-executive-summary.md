# Wave 4A 执行摘要

审查日期：2026-07-27。基线已完整读取：`docs/current_audit/00,02,03,04,05,07,08,09`。
审查对象为 root `master@0ed9d148bfbfd22253142172bbfe93c51106fdfa`、Offboard
`976d6217d73a28b72e64300e2dd04bcbeeee30d7`、PX4 `v1.16.2@54f0455f`。

## 最终结论

```text
H0: NO-GO
H1: NO-GO (current entrypoint stopped before colcon; build/test NOT-RUN)
H2: NO-GO
H3: NOT-RUN
H4: NOT-RUN
H5: NOT-RUN / BLOCKED
H6 READINESS: NOT READY

P0 OPEN: YES
P1 OPEN: YES
HARDWARE ACCESSED: NO
FORMAL SITL RUN: NO
PROPELLERS INSTALLED: NOT VERIFIED
SOURCE FILES MODIFIED: YES — only nested serial `COLCON_IGNORE` quarantine marker
TESTS RUN: YES — partial pure-software suites; serial parser suite failed
REPORTS CREATED: YES — 00 through 09 in this directory
```

H6 不能进入。没有执行 ROS node、DDS Agent、MAVROS、PX4/SITL、串口或任何硬件操作；本报告也不构成 H5/H6 授权。

## 本轮可验证进展

- 未治理串口 ROS 包增加 `src/communication/Serial/serial_driver_ros/COLCON_IGNORE:1-3`，DDS-only discovery 的 package-boundary 当前通过（75 packages）。这是 build/discovery 隔离，不是执行链修复。
- Offboard standalone runtime gate、Offboard Python contract（12/12）及 root static/fixture（152/152）通过；这些均是离线/纯软件证据。
- 新鲜 `/tmp` H1 入口曾执行但在旧 serial path boundary 前置校验 exit 2 时停止；之后 quarantine 使 boundary 通过，但 H0 仍为 NO-GO，未再次启动 colcon。

## 仍然阻塞 H0 的最短事实链

1. 正式 `offboard_node` 在 `src/offboard_cpp/src/node.cpp:28-35` 创建三个 `/fmu/in/*` writer，`CtrlFSM.cpp:339-340,405-416` 直接 publish；未接入已测试 gate，未订阅 `VehicleCommandAck`。
2. `CMakeLists.txt:33-35` 仍无条件 `TEXT_RC`，`config/ctrl_param.yaml:12-16` 仍 `enable_arm: true`；ARM/mode 命令没有 ACK/RC/kill 完整闭环。
3. 串口源码仍有 `/cmd_vel`→构造即开设备→`write()` 路径（`serial_main.cpp:13-39`、`serial_driver.cpp:6-32`）。quarantine 可被手工 build/run 绕过。
4. ROS/STM32 协议不一致，且 parser ASan/UBSan host test 在 `test_serial_parser.c:105` 实际失败（exit 134）。
5. communication/serial canonical origin/path/receipt 未决；Offboard HEAD 未被 root exact lock 恢复；PX4 source/submodule/toolchain/board/RC profile 未纳管。
6. vision frame/time/reset/dropout fail-closed 行为没有目标 unit evidence。

详细 finding、状态、修复及验收命令见 [08-findings-register.md](08-findings-register.md)；逐门禁与人工安全条件见 [07-h5-h6-safety-checklist.md](07-h5-h6-safety-checklist.md)。

## 按依赖顺序的最短剩余关键路径

1. 维护者书面确定 communication/serial 的 exact origin/SHA/path/disposition；保持 quarantine，不得把 validator 放宽。
2. 将正式 Offboard 的所有控制 writer、ACK/status/timesync/restart、authority/lease、RC/kill 接入同一生产 gate；默认 auto-arm 关闭并移除 production mock。
3. 在获批 serial 源中移除 `/cmd_vel` 直达 writer，加入 explicit enable/lease/watchdog/physical interlock/fault-close；统一 CRC16/tail/even-length schema，使完整 sanitizer/fault matrix 通过。
4. 批准并锁定 Offboard、PX4 source/submodules/toolchain/board/RC profile 以及 serial disposition；补齐 vision health gate/tests。
5. 重做 H0；仅在 H0 GO 后，在全新 `/tmp` 完成 H1 build/test receipt；随后完成 H2、隔离 H3、H4 前置评审。
6. 之后才可请求独立授权、执行 H5，并在 H0-H5 均满足及二人拆桨确认后再次请求 H6 授权。
