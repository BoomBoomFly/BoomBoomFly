# 串口控制链隔离与协议安全复核

审查日期：2026-07-27  
范围：`src/communication/Serial/serial_driver_ros` 与同级 `Serial_32` 固件解析器  
基线：`docs/current_audit/00,02,03,04,05,07,08,09` 已完整读取；root
`master@0ed9d148bfbfd22253142172bbfe93c51106fdfa`，nested serial
`master@87f3907f0b3b906d474a8d1e1dc9677ab0c4298f`。  
硬件访问：否。未运行 ROS 节点、DDS Agent、MAVROS、PX4/SITL，未打开 `/dev/tty*`。

## 结论

处置判定：**隔离候选（不是保留/重构/移除的维护者最终决定）**。根仓库中的旧
`src/serial_driver_ros` gitlink 已删除；实际 nested repo 位于 root 未跟踪的
`src/communication/Serial/serial_driver_ros`，而 `workspace.repos` 仍指向不同的
`../communication`。因此该源码、origin、canonical path 与 receipt 仍未获治理批准。

本轮唯一源码改动为新增
`src/communication/Serial/serial_driver_ros/COLCON_IGNORE:1-3`。它使该包不被 DDS-only
生产 discovery/build 发现；它**没有**批准该来源、没有实现 authority/lease/watchdog，
也没有消除手工构建该源码时的直接串口路径。其效果是生产发现隔离，而非完整运行时
fail-closed 修复。

`verify_package_boundary.py` 现在 PASS，说明当前 production package boundary 不再
发现串口包；这不是 H0 GO 的充分证据。串口源码中的直接执行链、协议不一致和 parser
测试失败仍使 H0 为 NO-GO、H2 为 NO-GO，H1/H3 不得进入。

## Finding BBF-W4A-SER-001

- 严重级别：P0（历史 `BBF-CUR-003`）
- 历史结论：`/cmd_vel` 直接写串口、无 authority/watchdog/interlock；H0 阻塞。
- 当前文件和行号：`serial_main.cpp:13-25,31-39` 默认 `/dev/ttyUSB0`、订阅
  `/cmd_vel` 并把速度传给通信层；`serial_driver.cpp:6-12,26-32` 构造时打开传入端口并
  写帧；`script/send_demo.py:9-20` 周期发布非零 `/cmd_vel`；
  `config/serial_config.yaml:1-4` 默认 `/dev/ttyS1`。
- 当前证据：静态扫描命中 `serial_port_(port, ...)`、`serial_port_.write(frame)`、
  `/cmd_vel` subscription/publisher。没有对 owner、lease、enable、watchdog、有限值、
  范围、断线或退出状态的实现证据。
- 状态：**TECHNICALLY ISOLATED FOR PRODUCTION DISCOVERY；P0 OPEN**。
- 影响：若绕过隔离而手工构建/运行，任意 `/cmd_vel` 仍可打开并写入物理串口；不得把
  `COLCON_IGNORE` 误报为 runtime arbitration。
- 修复：维护者须先批准唯一 origin/SHA/path/package disposition；随后将设备 backend
  置于唯一授权控制器后，仅在 explicit enable、有效 owner/lease、fresh watchdog、
  物理 interlock 和受审计 shutdown 全满足时才允许输出。默认与失联状态必须零输出/关闭。
- 验收命令：在 fake transport 上证明无 enable/lease、过期、断线、退出时 write count=0；
  static scan/launch test 证明不存在 `/cmd_vel` 直达 writer；真实设备测试另需单独授权。
- 是否阻塞 H0-H6：H0 是；H1 是（来源治理）；H2 是；H3-H6 是。

## Finding BBF-W4A-SER-002

- 严重级别：P1（历史 `BBF-CUR-004`）
- 历史结论：旧 gitlink、未跟踪 communication、manifest/profile 实际路径冲突导致
  package boundary exit 2。
- 当前文件和行号：`COLCON_IGNORE:1-3`；profile 仍在
  `config/profiles/dds_only_packages.yaml:27-29` 将 `serial_driver` 禁止路径写为
  `src/serial_driver_ros`；`workspace.repos:21-24` 仍为 `../communication`。
- 当前证据：`COLCON_IGNORE` 后 `verify_package_boundary.py` 返回 0，full discovery
  为 75 个包且 authoritative discovery 仅为 `offboard_cpp`、`px4_msgs`、
  `vision_to_dds`。这确认 production discovery 为 0；但并不解析 nested origin/receipt。
- 状态：**机械性 boundary 阻塞已缓解；canonical source/path P1 OPEN**。
- 影响：可安全避免未知串口包进入 DDS-only build，但 clean restore、审计和未来授权
  仍不可重复。
- 修复：维护者书面决定 canonical origin/SHA/path 与旧 gitlink disposition；以 receipt
  和 exact lock 纳管，或在获批移除前持续隔离。不得通过放宽 package validator 将其纳入
  production。
- 验收命令：治理后，在 clean/offline fixture 验证唯一 source identity、profile/manifest
  一致与 package boundary PASS。
- 是否阻塞 H0-H6：H0 是；H1 是；H2-H6 是（上游未关闭）。

## Finding BBF-W4A-SER-003

- 严重级别：P1（历史 `BBF-CUR-005`）
- 历史结论：ROS 使用 additive checksum/无 tail，STM32 要求 CRC16 + tail；ROS 对
  odd length 有 `j+1` 越界风险。
- 当前文件和行号：ROS `protocol_defs.hpp:9-19`、`serial_driver.cpp:35-60,74-96`；
  STM32 `Serial_32/include/serial.h:20-40`、`Serial_32/src/Serial.c:153-219`；
  STM32 test `test_serial_parser.c:101-105`。
- 当前证据：静态扫描确认 ROS 仍为 `calcChecksum` 单字节加和，无 CRC16/tail；STM32
  规定 `0x0F 0xF0 LEN DATA CRC16_LOW CRC16_HIGH 0xFF`。ROS response loop 在
  `serial_driver.cpp:93-95` 以 `j+1` 解码却未先拒绝 odd `len`。默认
  `SERIAL1_MAX_DATA_LEN=255`，故 test 中 `(uint8_t)(MAX+1)` 在
  `test_serial_parser.c:103` 回绕为 0；在 ASan/UBSan host test 中 assertion
  `status == LOG_STATUS_SERIAL_LENGTH_ERROR` 实际失败。
- 状态：**P1 OPEN；未验证为 FIXED**。
- 影响：两端命令不能按同一 schema 验证；畸形/奇数/截断输入可能被错误解释，且当前
  parser 的长度拒绝测试并未通过。
- 修复：在维护者批准 canonical source 后，将帧 schema（header/type、even max length、
  endianness、CRC16/MODBUS coverage、tail、partial/re-sync）定义为单一版本化契约；共享或
  金样验证两端实现。先拒绝 odd/oversize/CRC/tail/partial frame，任何失败零输出。
- 验收命令：C/C++ golden vector cross-check；partial/odd/oversize/CRC/tail/noise/reorder
  fault matrix；ASan/UBSan host parser；fake backend disconnect/timeout/exit write-count=0。
- 是否阻塞 H0-H6：H0 是（该来源进入范围时）；H1/H2 是；H3-H6 是。

## 已执行的软件证据

| 命令 | 结果 | 边界 |
|---|---:|---|
| `python3 Scripts/test/verify_package_boundary.py --workspace-root /home/c/px4_ws/BoomBoomFly --log-base /tmp/boomboomfly_wave4a_serial_boundary` | 0 / PASS | `COLCON_IGNORE` 后 serial 未被 full discovery 发现；无硬件访问 |
| `python3 -m unittest discover -s test/package_boundary -p 'test_*.py' -v` | 0，9/9 PASS | 纯 Python fail-closed boundary fixtures；`PYTHONPYCACHEPREFIX=/tmp/...` |
| `gcc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -DSERIAL_HOST_TEST ... Serial.c test_serial_parser.c -o /tmp/boomboomfly_wave4a_serial_parser_test && /tmp/boomboomfly_wave4a_serial_parser_test` | 非零 / assertion failed | 仅内存 parser host test；未打开串口；失败位置 `test_serial_parser.c:105` |
| 静态 `grep -RInE` 扫描 | direct path 仍命中 | 未执行 ROS/设备/Agent/PX4/SITL |

第一次以错误 Python module path 调用 boundary unittest 返回 ImportError；随后以
`unittest discover` 重跑并通过。它不影响上述通过结果，也不应被省略。

## 门禁影响与最短剩余路径

```text
H0: NO-GO
H1: NOT-RUN
H2: NO-GO
H3: NOT-RUN
H4: NOT-RUN
H5: NOT-RUN
H6 READINESS: NOT READY
```

最短依赖路径：

1. 维护者书面决定 serial 的 canonical origin/SHA/path/disposition，并保留现有隔离；
2. 在获批的唯一源码中删除 `/cmd_vel` 直达设备路径，接入授权仲裁、watchdog、interlock、
   disconnect/exit 的 fail-closed backend；
3. 统一 ROS/STM32 版本化 CRC16/tail/even-length schema，先使现有 ASan parser test 和
   新增 fault matrix 通过；
4. 将 exact source/receipt/lock/profile 一致化，重做 current H0 审查；
5. 仅在所有 H0 阻塞关闭后，进入隔离 H1 build；H2/H3 仍需完整独立证据。

本项不授权 H5/H6；未访问硬件、未执行 formal SITL、未安装/核验螺旋桨状态。
