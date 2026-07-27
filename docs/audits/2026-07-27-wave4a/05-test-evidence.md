# Wave 4A — H2 故障注入与纯软件测试证据

审查日期：2026-07-27（Wave 4A Thread D）  
范围：仅现有的 pure-software 单元、standalone 与 fixture 测试；不改源码。  
基线：`master@0ed9d148bfbfd22253142172bbfe93c51106fdfa`，Offboard
`976d6217d73a28b72e64300e2dd04bcbeeee30d7`。本报告已在执行前完整读取
`docs/current_audit/00,02,03,04,05,07,08,09` 及当时已有的 Wave 4A
`03-serial-safety.md`、`04-build-evidence.md`；不以旧的通过日志代替本轮实际结果。

安全边界：没有运行 `ros2 launch`、`ros2 run`、SITL、PX4、MicroXRCEAgent、MAVROS、
`/fmu/in/*` 发布、串口/相机/LiDAR 驱动或设备探测；没有打开 `/dev/tty*`。所有新增二进制
和 Python cache 位于 `/tmp`。`SERIAL_HOST_TEST` 在 host parser 编译中排除了 UART
interrupt/HAL 回调。

## 结论

```text
H2: NO-GO
```

本轮确认 tested `OffboardRuntimeGate` 的纯内存状态机覆盖并通过 ACK 全结果、ACK 超时/
迟到、错误关联、预热、陈旧/未来 status、时钟回退和显式 restart/旧 epoch ACK。它的
`publish_count` 只是 synthetic instrumentation，并没有 ROS publisher 或 PX4 consumer。
当前正式节点仍有独立的直接 publisher 路径（基线 finding `BBF-CUR-001`），所以这些 PASS
绝不能提升为 live 节点或 H3 证据。

STM32 parser 的唯一现有 ASan/UBSan host test **实际失败**：试图构造
`SERIAL1_MAX_DATA_LEN + 1` 时，长度为 `uint8_t` 而 `SERIAL1_MAX_DATA_LEN` 为 255，
转换后为 0，因而并未触发长度错误。这保留了 `BBF-CUR-005`。ROS 串口 response decoder
仍以 `j + 1` 读取 payload 而无 odd-length 拒绝，且没有 fake transport 的 disconnect/
timeout/exit 测试。视觉节点不存在对应的 unit test，传感器掉线、时间跳变和 reset counter
也没有被纯软件测试覆盖。

因此 H2 的“全部目标测试实际执行、全部通过、正式节点与测试共用核心状态机”均未满足。

## 本轮实际执行结果

| 命令 | Exit | 结果与边界 |
|---|---:|---|
| `/usr/bin/g++ -std=c++17 -Wall -Wextra -Wpedantic -I src/offboard_cpp/include src/offboard_cpp/src/lib/offboard_runtime_gate.cpp src/offboard_cpp/test/test_offboard_runtime_gate.cpp -o /tmp/boomboomfly_wave4a_h2_offboard_runtime_gate` | 0 | 只编译 transport-neutral gate 和 standalone test；无 ROS 依赖。 |
| `/tmp/boomboomfly_wave4a_h2_offboard_runtime_gate` | 0 | 输出 `B2 runtime gate: all pure-software checks passed`。 |
| `PYTHONPYCACHEPREFIX=/tmp/boomboomfly_wave4a_h2_pycache python3 -m unittest discover -s test -p 'test_*.py' -v`（`src/offboard_cpp`） | 0 | 12/12 test-only Python contract-oracle tests PASS；文件头明确其不是 production integration。 |
| `PYTHONPYCACHEPREFIX=/tmp/boomboomfly_wave4a_h2_pycache python3 -m unittest discover -s test -p 'test_*.py' -v`（root） | 0 | 152/152 static/fixture/offline tests PASS；含 authority、launch guard、boundary fixtures 和 synthetic contract，但不驱动 live node。 |
| `/usr/bin/gcc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -DSERIAL_HOST_TEST -I src/communication/Serial/Serial_32/include src/communication/Serial/Serial_32/src/Serial.c src/communication/Serial/Serial_32/test/test_serial_parser.c -o /tmp/boomboomfly_wave4a_h2_serial_parser` | 0 | host-only STM32 parser 编译成功；不链接/调用 HAL UART。 |
| `/tmp/boomboomfly_wave4a_h2_serial_parser` | **134** | `assert(status == LOG_STATUS_SERIAL_LENGTH_ERROR)` 在 `test_serial_parser.c:105` abort；ASan/UBSan 没有报告越界，因为测试在该断言处停止。 |

本报告不把现有 Wave 4A serial boundary report 的 9/9 Python fixture PASS 当作 parser
fault matrix，也不把 root 152/152 或 Offboard 12/12 当成 PX4、DDS Agent、节点或硬件测试。

## 覆盖矩阵

| 风险/场景 | 现有代码和测试证据 | 本轮结果 | 覆盖状态 |
|---|---|---|---|
| authority 拒绝、latch、identity/correlation mismatch | `test_offboard_runtime_gate.cpp:77-101` | PASS，synthetic publish count 为 0 | Gate-only；live 未接入 |
| VehicleCommandAck 全部枚举结果、target/source/command/sequence/correlation/epoch mutation | `test_offboard_runtime_gate.cpp:104-130`; gate checks `offboard_runtime_gate.cpp:158-217` | PASS | Gate-only；无 `VehicleCommandAck` ROS subscription 测试 |
| ACK timeout、late ACK、future ACK | `test_offboard_runtime_gate.cpp:132-147` | PASS | Gate-only |
| 预热 sample 数量/时长、陈旧/未来输入、gap、clock backward | `test_offboard_runtime_gate.cpp:150-192` | PASS | Gate-only；非 live setpoint stream |
| stale/wrong/future VehicleStatus、持续 freshness | `test_offboard_runtime_gate.cpp:195-246`; implementation `:220-262` | PASS | Gate-only；无 PX4/DDS transport |
| process/PX4/Agent restart、旧 ACK epoch | `test_offboard_runtime_gate.cpp:249-271`; implementation `:279-` | PASS | 仅显式 gate restart；未覆盖实际 node/PX4/Agent restart |
| RC no-first-frame/stale/signal loss/NaN | `src/offboard_cpp/test/test_rc_input.cpp:43-126` 存在 | **NOT-RUN** | 需要当前 H1 ROS/gtest build；本轮未运行 colcon/ROS test，且正式 auto-arm/`TEXT_RC` 基线 blocker 未关闭 |
| STM32 CRC16 valid/CRC-error/null arguments | `Serial_32/test/test_serial_parser.c:80-109` | BLOCKED by failing suite | valid/CRC statements在失败断言前执行，但整个 test 非零，不能记 PASS |
| oversize frame | `test_serial_parser.c:99-106`; `serial.h:31-35`; parser `Serial.c:153-170` | **FAIL** | `255 + 1` wraps to 0；该 negative case 未被实现/测试正确表达 |
| short/partial frame、tail、noise/re-sync、odd length、乱序 | ROS decode `serial_driver.cpp:68-104`; STM32 parser | **NOT-RUN / no test** | 没有完整 fault matrix；ROS `j+1` access at `:93-95` 未先拒绝 odd `len` |
| serial disconnect、write failure、watchdog timeout、safe exit | `serial_driver.cpp:6-32`; `serial_main.cpp:13-39` | **NOT-RUN / no fake backend** | 仍可 `/cmd_vel` 直达 writer；没有可断言 write-count=0 的 transport seam |
| 传感器掉线、TF 时间跳变/未来/回退、NaN、quality、reset | `vision_to_dds.cpp:262-350` | **NOT-RUN / no unit tests found** | `last_tf_time_ < stamp` 不是完整 health/epoch gate；`reset_counter=0`、`quality=1` 固定后仍 publish (`:305,338`) |

## Findings 与 H2 影响

### BBF-CUR-001 — P0：正式 Offboard 路径未由已测试 gate 约束

- 历史结论：`STILL_OPEN`；Wave 3B/`current_audit` 明确区分 gate PASS 与 live publisher integration 未完成。
- 当前文件和行号：正式 publisher 仍见 `src/offboard_cpp/src/node.cpp:28-35`、`src/offboard_cpp/src/lib/CtrlFSM.cpp:339-340,416`；本轮通过的 gate 测试仅为 `test_offboard_runtime_gate.cpp:77-283`。
- 当前证据：standalone C++ PASS、Python oracle 12/12 PASS；均无 ROS import/publisher。静态路径仍不能证明正式 publisher 调用 gate。
- 状态：**P0 OPEN；测试仅证明 isolated gate**。
- 影响：DDS disconnect、PX4 restart、Agent restart、stale setpoint、ACK reject/timeout 的 live 控制输出仍无当前测试证据。
- 修复：将唯一 live writer、ACK/status/timesync/epoch 和 restart reset 接入同一 runtime gate，再用 fake transport 对正式 node/FSM 进行 publish-count=0 测试。
- 验收命令：H1 后以 fake clock/transport 运行所有 ACK/timeout/restart/stale cases；拒绝、断线和重启场景三个 `/fmu/in/*` writer count 必须为 0。
- 是否阻塞 H0-H6：**H0、H2、H3-H6 是**。

### BBF-CUR-005 / BBF-W4A-SER-003 — P1：串口 parser 负向测试失败且协议/边界未覆盖

- 历史结论：ROS additive checksum/no tail 与 STM32 CRC16+tail 不一致；奇数长度可能越界。
- 当前文件和行号：失败 test `src/communication/Serial/Serial_32/test/test_serial_parser.c:99-106`；`SERIAL1_MAX_DATA_LEN=255` 在 `include/serial.h:31-35`；ROS decoder `serial_driver.cpp:68-104`，尤其 `:93-95`。
- 当前证据：上述 ASan/UBSan host binary exit **134**。失败不是 sanitizer clean pass，且没有 ROS/STM32 cross-schema golden vector、partial/short/tail/noise/reorder/odd-length 或 fake disconnect matrix。
- 状态：**P1 OPEN；H2 failing**。
- 影响：畸形帧、协议漂移及传输断开不能被证明 fail-closed；即使 production discovery 已隔离，该候选源码手工构建时仍有风险。
- 修复：先获 canonical source 授权；实现单一版本化 schema，再补正长度测试表示法并添加 ASan/UBSan negative matrix与 fake backend write-count assertions。
- 验收命令：host parser/golden vectors 在 valid、CRC、tail、oversize、odd、partial、noise/reorder 全部 exit 0；fake disconnect/timeout/exit 均 write count=0。
- 是否阻塞 H0-H6：**H0、H2、H3-H6 是**；H1 另受来源/lock 阻塞。

### BBF-CUR-009 — P1：视觉掉线、时间和 reset fail-closed 没有测试闭环

- 历史结论：frame/time/reset/quality/dropout health gate `STILL_OPEN`。
- 当前文件和行号：`src/vision_to_dds/src/vision_to_dds.cpp:262-350`；publish 位于 `:305,338`，固定 `reset_counter=0`/`quality=1` 位于 `:335-336`。未发现 `src/vision_to_dds` 下 unit test 文件。
- 当前证据：本轮没有能隔离 TF/clock/publisher 的 vision unit target；root 152/152 是静态/fixture suite，不执行该 node。
- 状态：**P1 OPEN；NOT_VERIFIED，不得写 FIXED**。
- 影响：sensor dropout、timestamp backward/future/freeze、TF reset、nonfinite position/quaternion、quality/device health 不能证明会 suppress PX4 output。
- 修复：将 transform/time/epoch/finite/quality 判定抽为纯函数与 fake publisher seam；每个异常 case 断言 publish count=0。
- 验收命令：在不启 ROS hardware node 的 unit suite 中运行 zero/backward/future/freeze/reset/dropout/NaN/Inf matrix，全部 PASS 且 PX4 publish count=0。
- 是否阻塞 H0-H6：**H0（启用视觉）、H2、H3-H6 是**。

## 未覆盖和不能外推的部分

1. 没有执行 colcon/ament gtest 或 `test_rc_input`；H1 当前没有可用的受治理 build receipt，且这不应被隐藏为“all tests”。
2. 没有 live ROS node、DDS graph、PX4、XRCE Agent、MAVROS 或 SITL 测试；因此没有实际 DDS 断线、PX4 restart、Agent restart 或节点重启证据。
3. 没有真实或 fake serial transport integration；无 `/cmd_vel` interlock、断线、timeout、CRC/short/odd/reorder、退出零输出的执行证据。
4. 没有 vision sensor/TF fake integration；没有 sensor dropout 或 timestamp jump 的 output-suppression evidence。
5. 没有硬件访问、formal SITL 或螺旋桨状态核验。

## 最短 H2 剩余关键路径

1. 保持 serial 隔离，先由维护者决定其 canonical source/SHA/path；修正 parser length domain 和统一 ROS/STM32 frame schema。
2. 将正式 Offboard node/FSM 的所有 writer 接入已通过的 gate，并在 H1 受治理 build 后为其提供 fake clock/transport/ACK/status/restart seam。
3. 补齐并实际运行 Offboard（ACK/RC/kill/DDS/PX4/Agent restart/stale/clock/NaN）、serial（CRC/partial/odd/reorder/disconnect/timeout/exit）和 vision（frame/time/reset/dropout/nonfinite）测试矩阵；每个 fail case 都必须输出 0。
4. 仅在所有目标 tests **实际运行且全通过**、并确认正式节点共用同一核心状态机后，才可重新评估 H2；随后另行进行受隔离的 H3 node integration。

```text
H0: NO-GO
H1: NO-GO (current build prerequisite failed; no build receipt)
H2: NO-GO
H3: NOT-RUN
H4: NOT-RUN
H5: NOT-RUN
H6 READINESS: NOT READY

P0 OPEN: YES (BBF-CUR-001; baseline BBF-CUR-002/003 remain upstream)
P1 OPEN: YES (BBF-CUR-005, BBF-CUR-009 and provenance/build blockers)
HARDWARE ACCESSED: NO
FORMAL SITL RUN: NO
PROPELLERS INSTALLED: NOT VERIFIED (not inspected)
SOURCE FILES MODIFIED: NO (this thread; report only)
TESTS RUN: 4 commands/suites PASS (C++ gate, Python oracle 12/12, root fixtures 152/152, parser compile); 1 parser execution FAIL exit 134
REPORTS CREATED: YES — this file
```
