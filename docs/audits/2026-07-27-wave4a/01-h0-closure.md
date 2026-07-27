# H0 静态关闭复核

结论：`H0: NO-GO`。以下问题均按 `current_audit` 的原验收标准复核；没有任何条目被以旧日志、隔离或 mock 改写成 `FIXED`。

## BBF-W4A-H0-001 — 正式 Offboard gate/ACK 未接入

- 严重级别：P0；历史结论：`BBF-CUR-001` STILL_OPEN。
- 当前文件和行号：`src/offboard_cpp/src/node.cpp:28-35,86-91`；`src/lib/CtrlFSM.cpp:339-340,405-416`。
- 当前证据：node/FSM 直接发布 trajectory setpoint、offboard mode 和 VehicleCommand；无 `OffboardRuntimeGate` 实例或 `VehicleCommandAck` subscription。standalone gate PASS 只覆盖另一条离线路径。
- 状态：OPEN；影响：ACK reject/timeout、stale input、DDS/PX4/Agent/node restart 不能证明零输出。
- 修复：唯一 adapter 收敛所有 writer，并将 authority/lease/epoch、ACK、fresh status、timesync、PRESTREAM、restart reset 置于 gate 内。
- 验收命令：对生产 FSM/adapter 的 fake transport tests 覆盖 reject/timeout/stale/restart/duplicate writer，所有失败场景三类 writer count=0。
- 阻塞 H0-H6：是。

## BBF-W4A-H0-002 — auto-arm、TEXT_RC、RC/kill 闭环缺失

- 严重级别：P0；历史结论：`BBF-CUR-002` STILL_OPEN。
- 当前文件和行号：`src/offboard_cpp/CMakeLists.txt:33-35`；`config/ctrl_param.yaml:12-16`；`src/lib/param.cpp:10-12,35`；`CtrlFSM.cpp:434,471,621-739`。
- 当前证据：production `TEXT_RC` 与 `enable_arm: true` 仍存在，ARM/mode 路径没有 correlated accepted ACK；RC 未收到时检查可跳过。
- 状态：OPEN；影响：输入/配置错误可到达 arm/mode 请求。
- 修复：默认 `enable_arm=false`、移除 production mock；fresh physical RC、独立 kill latch、authority 与 accepted ACK 为硬门；恢复不得自动 ACTIVE。
- 验收命令：fake transport 在 no/stale/lost RC、kill、reject/timeout/restart、invalid config 时 ARM/MODE count=0。
- 阻塞 H0-H6：是。

## BBF-W4A-H0-003 — 串口第二执行链仅被 discovery 隔离

- 严重级别：P0；历史结论：`BBF-CUR-003` REGRESSED。
- 当前文件和行号：`src/communication/Serial/serial_driver_ros/src/serial_main.cpp:13-39`、`serial_driver.cpp:6-32`、`COLCON_IGNORE:1-3`。
- 当前证据：`/cmd_vel` callback 仍通向构造即开端口和 write；本轮 marker 只令 boundary discovery=0。
- 状态：TECHNICALLY ISOLATED FOR DISCOVERY, P0 OPEN；影响：手工 build/run 仍可产生串口执行输出。
- 修复：获批 canonical source 后删除直达路径，实施 enable/owner/lease/watchdog/finite-range/physical interlock/fault-close。
- 验收命令：fake backend 在 no-enable/no-lease/stale/disconnect/exit 时 write count=0，且 static/launch test 无 `/cmd_vel`→writer。
- 阻塞 H0-H6：是。

## BBF-W4A-H0-004 — 串口身份与协议错误

- 严重级别：P1；历史结论：`BBF-CUR-004/005` OPEN。
- 当前文件和行号：`workspace.repos:21-24`、`config/profiles/dds_only_packages.yaml:27-29`；ROS `serial_driver.cpp:35-60,74-96`；STM32 `Serial.c:153-219`、`test_serial_parser.c:101-105`。
- 当前证据：nested source/path 没有 receipt；ROS additive checksum/no tail 与 STM32 CRC16/tail 不同；ASan/UBSan host test exit 134，255+1 被 `uint8_t` 回绕。
- 状态：OPEN；影响：不可重复恢复，畸形帧/断线不能证明 fail-closed。
- 修复：书面批准 origin/SHA/path/disposition，定义单一版本化 schema，并完整覆盖 CRC/tail/odd/partial/reorder/disconnect。
- 验收命令：golden-vector cross-check 和 sanitizer negative matrix 全部 exit 0，错误帧/断线零输出。
- 阻塞 H0-H6：是。

## BBF-W4A-H0-005 — 依赖治理与可重现性缺失

- 严重级别：P1；历史结论：`BBF-CUR-006/007/008` STILL_OPEN。
- 当前文件和行号：`workspace.lock.repos:1-19`（Offboard :12-15）；PX4 `src/modules/uxrce_dds_client/dds_topics.yaml`。
- 当前证据：Offboard checkout `976d...` 不等于 lock `cded...`；PX4 `54f...` 是 shallow 且未入 lock，ARM toolchain/board/RC endpoint 未批准；第一次 H1 entrypoint 因 boundary exit 2 未到 colcon。
- 状态：OPEN；影响：无法重建同一源码、PX4 profile 或当前 H1 artifact。
- 修复：批准 immutable source/submodule/toolchain/board/RC lock 和 serial disposition，随后重新执行 isolated H1。
- 验收命令：offline lock verifier + source/message/profile hash verifier + `/tmp` `Scripts/test/test_dds_only.sh` 全部成功。
- 阻塞 H0-H6：H0-H2、H4-H6 是。

## BBF-W4A-H0-006 — Vision health 未闭环

- 严重级别：P1（启用视觉 profile 时 P0 影响）；历史结论：`BBF-CUR-009` STILL_OPEN。
- 当前文件和行号：`src/vision_to_dds/src/vision_to_dds.cpp:262-350`，publish `:305,338`，固定 reset/quality `:335-336`。
- 当前证据：未发现 frame/time/epoch/reset/dropout/nonfinite fake publisher unit suite。
- 状态：NOT_VERIFIED/OPEN；影响：异常视觉输入可能污染 PX4 estimator。
- 修复：纯函数 health gate + fake publisher seam，默认 production disabled。
- 验收命令：zero/backward/future/freeze/reset/dropout/NaN/Inf matrix 均 publish count=0。
- 阻塞 H0-H6：H0（启用视觉）、H2-H6 是。
