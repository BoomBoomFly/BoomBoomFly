# Wave 4A — Thread G 独立交叉验证登记册

审查时间：2026-07-27（本报告的命令证据截点见 `09-command-evidence.md`）。  
范围：完整阅读 `docs/current_audit/00,02,03,04,05,07,08,09` 和 Wave 4A 在截点前已有的
`03-serial-safety.md`、`04-build-evidence.md`、`07-h5-h6-safety-checklist.md`；随后仅作静态
检查和纯软件验收复跑。没有启动 ROS 节点、PX4、SITL、Agent、MAVROS 或任何设备。

## 独立结论

没有 P0 或 P1 获得可以写为 `FIXED` 的独立证据。`COLCON_IGNORE` 让严格的 DDS-only
package-boundary 验证通过，但它只将未治理串口包从 discovery/build 中排除；不会阻止手工
构建/运行其构造即打开串口、`/cmd_vel` 直达 `write()` 的路径。因此不得把这项机械隔离
叙述为串口运行时安全修复。

同样，`OffboardRuntimeGate` 的 C++ 和 Python contract 都通过，但正式 `offboard_node`
没有实例化该类或订阅 `VehicleCommandAck`；`CtrlFSM` 仍直接发布三个 PX4 输入和
VehicleCommand。离线 gate 测试不是 live node、PX4 消费、SITL 或硬件证据。

```text
H0: NO-GO
H1: NO-GO (current entrypoint previously stopped before colcon; no successful current receipt)
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
SOURCE FILES MODIFIED: YES — this Wave added serial `COLCON_IGNORE`; this Thread G changed no source
TESTS RUN: package-boundary PASS; 12/12 Python gate PASS; standalone C++ gate PASS; serial ASan parser FAIL
REPORTS CREATED: this file
```

## 独立复跑命令与结果

| 命令 | 结果 | 解释边界 |
|---|---:|---|
| `python3 Scripts/test/verify_package_boundary.py --workspace-root /home/c/px4_ws/BoomBoomFly --log-base /tmp/boomboomfly_wave4a_cross_boundary` | PASS | 75 个发现包；authoritative 三包为 `offboard_cpp`、`px4_msgs`、`vision_to_dds`。只证明 serial 被 `COLCON_IGNORE` 排除。 |
| `g++ ... offboard_runtime_gate.cpp test_offboard_runtime_gate.cpp -o /tmp/boomboomfly_wave4a_cross_runtime_gate && /tmp/boomboomfly_wave4a_cross_runtime_gate` | PASS | 输出 `B2 runtime gate: all pure-software checks passed`；该 gate 未接 live node。 |
| `PYTHONPYCACHEPREFIX=/tmp/... python3 -m unittest discover -s src/offboard_cpp/test -p 'test_*.py' -v` | PASS，12/12 | ACK、restart、时钟和 PRESTREAM 的 Python contract；不是 ROS transport 测试。 |
| `gcc -fsanitize=address,undefined ... Serial.c test_serial_parser.c -o /tmp/boomboomfly_wave4a_cross_serial_parser && ...` | FAIL | `test_serial_parser.c:105` 断言期望 `LOG_STATUS_SERIAL_LENGTH_ERROR` 失败；没有打开串口。 |

静态枚举还发现历史 MAVROS 路径仍在 `src/px4_bringup/launch/include/px4.launch.py:11-44`，
其配置含 `src/px4_bringup/config/mavros_params.yaml:4` 的 `/dev/ttyTHS0:921600`。DDS-only
profile 目前把它列为 forbidden，这只是 profile 隔离；没有节点级/进程级证据可以证明未来
错误 launch 时不存在第二控制链。

## Finding XVAL-001 — 正式 Offboard 未接入测试 gate

- Finding ID：`XVAL-001`（`BBF-CUR-001`；`BBF-AUD-001..004,014,017`）
- 严重级别：P0
- 历史结论：runtime gate 只在离线测试中实例化；live publisher 绕过它。
- 当前文件和行号：`src/offboard_cpp/src/node.cpp:28-35` 创建 trajectory/mode/command 三个
  `/fmu/in/*` publisher；`src/lib/CtrlFSM.cpp:339-340,405-416` 直接 publish；
  `CMakeLists.txt:43-77,113-120` 编入 gate library 但没有把它接到 `offboard_node` 的行为边界。
- 当前证据：完整源码 scan 未发现 node 中 `OffboardRuntimeGate` 或
  `VehicleCommandAck` subscription；上述两个离线 gate suite 虽 PASS，仍不能约束 live writer。
- 独立判定：**AGREE — STILL_OPEN**；任何“gate 已接入正式节点”的说法为 **DISAGREE**。
- 影响：ready 前、ACK 拒绝/超时、状态陈旧、DDS/PX4/节点重启或重复 writer 时，真实 FSM
  仍可能发布。
- 修复：使用一个可注入 fake/live transport adapter，将所有三个 writer 和 VehicleCommand
  收敛至同一 gate；接入 ACK/status/epoch/lease/freshness，并要求所有失败分支 publish=0。
- 验收命令：对生产 `CtrlFSM`/adapter 的 fake-transport gtest 覆盖 PRESTREAM、拒绝/超时、
  stale setpoint、DDS/PX4/Agent/node restart、duplicate writer；静态断言只剩 gate 内部 publish。
- 是否阻塞 H0-H6：H0、H2、H3、H4、H5、H6 是；H1 的成功编译不能解除该 promotion blocker。

## Finding XVAL-002 — 自动解锁、TEXT_RC 与命令 ACK 未闭合

- Finding ID：`XVAL-002`（`BBF-CUR-002`；`BBF-AUD-005,016..019`）
- 严重级别：P0
- 历史结论：production `TEXT_RC` 和默认 auto-arm 允许危险 arm/mode 路径，且无 live ACK。
- 当前文件和行号：`src/offboard_cpp/CMakeLists.txt:33-35` 无条件 `TEXT_RC`；
  `config/ctrl_param.yaml:12-16` 为 `enable_arm: true`；`src/lib/param.cpp:11,35` 默认/读取
  auto-arm；`src/lib/CtrlFSM.cpp:152-170,405-477,621-739` 可请求 ARM 与 mode，依赖 status 而非 ACK。
- 当前证据：静态 scan 命中 ARM、OFFBOARD/POSCTL/ALTCTL mode 命令；没有
  `VehicleCommandAck` ROS subscription。无 RC 时，起飞分支仅在“若收到 RC”才做 centred/mode 检查。
- 独立判定：**AGREE — STILL_OPEN**。
- 影响：`offboard/takeoff_land` 触发可到达 auto-arm/mode 请求，且拒绝、相关性错误或超时不能
  用 ACK 闭环阻断。
- 修复：production 默认 `enable_arm=false` 并移除 `TEXT_RC`；fresh physical RC、独立 kill
  latch、single authority、accepted correlated ACK 和 restart-recovery 都成为 ARM/MODE 硬门。
- 验收命令：fake transport 测试无 RC/stale RC/kill/ACK reject-or-timeout/restart/invalid config
  时 ARM/MODE publish count=0，恢复不自动 ACTIVE；production target binary negative-scan 不含 mock。
- 是否阻塞 H0-H6：全部是。

## Finding XVAL-003 — live 启动、故障与陈旧输入 fail-closed 证据不足

- Finding ID：`XVAL-003`（`BBF-CUR-004A`；`BBF-AUD-006..007`）
- 严重级别：P0
- 历史结论：live FSM 缺 WAIT/PRESTREAM、初始值/first-frame/fault lattice/recovery 闭合。
- 当前文件和行号：`src/lib/CtrlFSM.cpp:50-69` 在每 20 ms 构造数据；`:339-340` 无 gate
  条件直接发布；`:281-340` 多个状态后仍在函数尾发布；`src/node.cpp:87-90` 以 50 Hz 调用 FSM。
- 当前证据：离线 gate 的 12+1 suite 通过，但未执行 production FSM fake-transport gtest；
  代码路径与测试对象不同。
- 独立判定：**AGREE — STILL_OPEN**。
- 影响：输入未到、陈旧、时钟跳变、PX4/Agent/节点重启时的真实 publish/command 行为未被证明
  fail-closed。
- 修复：将 validity、epoch、clock、fault latch 和人工恢复放入同一 production state machine，
  并在 restart 清空 transient state。
- 验收命令：表驱动 first-frame/NaN/Inf/stale/clock jump/restart/timeout tests 对实际 adapter
  检查三类 PX4 publish 与 command publish 均为 0。
- 是否阻塞 H0-H6：全部是。

## Finding XVAL-004 — 未治理 serial 仍是第二执行链；COLCON_IGNORE 不是修复

- Finding ID：`XVAL-004`（`BBF-CUR-003`）
- 严重级别：P0
- 历史结论：任意 `/cmd_vel` 可直接打开并写执行串口，无 authority/watchdog/interlock。
- 当前文件和行号：`src/communication/Serial/serial_driver_ros/src/serial_main.cpp:13-25,29-39`
  默认 `/dev/ttyUSB0`、订阅 `/cmd_vel`；`serial_driver.cpp:6-12,26-32` 构造打开端口并
  `serial_port_.write(frame)`；`COLCON_IGNORE:1-3` 仅含 quarantine 说明。
- 当前证据：本线程 boundary PASS，故**同意** `COLCON_IGNORE` 已实现 production discovery
  隔离；但静态 source 仍有 direct open/write，且没有 owner、lease、enable、finite/range、
  watchdog、断线或退出 interlock。
- 独立判定：**AGREE — P0 OPEN；DISAGREE** 于把 boundary PASS 或 quarantine 写成运行时
  fail-closed/问题已修复的任何结论。
- 影响：手工构建/运行或未来错误 profile 仍可形成 DDS/MAVROS 外的串口执行链。
- 修复：先获得维护者对 origin/SHA/path/disposition 的书面决定；在唯一授权 controller 中
  实现 explicit enable + lease + watchdog + physical interlock + zero/close on fault/exit，且移除
  `/cmd_vel` 直达 writer。
- 验收命令：fake backend 对 no-enable/no-lease/stale/disconnect/exit write-count=0；static/launch
  test 无 `/cmd_vel`→writer；真实设备测试必须另获授权。
- 是否阻塞 H0-H6：全部是。

## Finding XVAL-005 — serial 来源、路径和协议均未关闭

- Finding ID：`XVAL-005`（`BBF-CUR-004,005`；`BBF-AUD-010..011`）
- 严重级别：P1
- 历史结论：旧 gitlink/manifest 路径冲突；ROS additive checksum 与 STM32 CRC16+tail 不一致，
  odd-length 存在越界风险。
- 当前文件和行号：root index 仍删除 `src/serial_driver_ros`；
  `workspace.repos:21-24` 仍指向 sibling/moving source；profile 的旧 serial 路径在
  `config/profiles/dds_only_packages.yaml:27-29`；ROS `serial_driver.cpp:35-60,74-96`，
  STM32 `Serial_32/src/Serial.c:153-219`，host test `test_serial_parser.c:101-105`。
- 当前证据：boundary 从历史 exit 2 变为 PASS，故对“discovery 机械阻塞已隔离”判
  **AGREE**；但 canonical receipt/lock 没有，且本线程 ASan/UBSan parser test 在 line 105
  失败，故来源和协议均非 FIXED。
- 独立判定：**AGREE — P1 OPEN**（AUD-010 的特定 boundary 症状缓解，不等于 AUD-010/011
  的治理验收关闭）。
- 影响：clean restore 和协议安全不可证明；若此代码再次纳入路径，错误帧可造成不安全解释。
- 修复：维护者选择 exact canonical source；统一版本化 CRC16/tail/even-length schema；
  严格拒绝 odd/oversize/partial/noise/CRC/tail 错误并以 fake backend fail-closed。
- 验收命令：governed clean offline restore、两端 golden vectors、partial/CRC/odd/oversize/fuzz
  sanitizer 和 disconnect/timeout tests 全 PASS。
- 是否阻塞 H0-H6：H0、H1、H2、H3、H5、H6 是；H4 同样不得使用未治理执行链。

## Finding XVAL-006 — PX4、Offboard 锁定与构建可复现性未闭合

- Finding ID：`XVAL-006`（`BBF-CUR-006..008`；`BBF-AUD-012..013`）
- 严重级别：P1
- 历史结论：PX4/px4_msgs identity 有改善，但 PX4 immutable governance/toolchain/board/RC
  profile、Offboard root lock 和 current H1 receipt 均未满足。
- 当前文件和行号：`workspace.lock.repos:1-19` 没有 PX4，`:12-15` 的 Offboard lock 是
  `cded3dc5...`；live checkout 是 `976d6217...`；H1 entrypoint 在
  `Scripts/build/build_dds_only.sh:84-100`。
- 当前证据：只读复核 root `0ed9d148...`、Offboard `976d6217...`、px4_msgs
  `392e831c...`、PX4 `54f0455f...`，PX4 有 35 submodules；这些 identity 不能覆盖 PX4
  lock/toolchain/board/RC profile。现有 Wave 4A build evidence 记录 current entrypoint 在先前
  boundary exit 2 停止，未有 colcon artifact；本线程未把 boundary 事后 PASS 当作 H1 PASS。
- 独立判定：**AGREE — P1 OPEN**；`BBF-AUD-013` 的 remote required CI/immutable runner
  执行状态为 **INSUFFICIENT_EVIDENCE**，没有被本线程或既有报告复跑。
- 影响：无法以 approved snapshot 重建 current control candidate，H1 不能从离线 gate 或
  后续 boundary PASS 借用结论。
- 修复：经 maintainer 批准后，将 PX4 source/submodule/toolchain/board/RC profile 与
  Offboard exact commit 写入 immutable locks/receipts，修正包直接依赖，随后在新的 `/tmp`
  从该 snapshot 完整 build/test。
- 验收命令：offline restore/lock schema/profile-generator verifier；
  `Scripts/test/test_dds_only.sh --workspace-root ... --output-root /tmp/<unique>` 的 build/test/
  test-result 均 0 且保存 hash。
- 是否阻塞 H0-H6：H0、H1、H2、H3、H4、H5、H6 是。

## Finding XVAL-007 — 感知与其余历史 P1 仍不可升级

- Finding ID：`XVAL-007`（`BBF-CUR-009`；`BBF-AUD-015,016..024`）
- 严重级别：P0（`AUD-008..009` 启用视觉时）/ P1（其余）
- 历史结论：vision frame/time/reset/quality/device health、formal SITL、endpoint/atomicity、
  rollback、法律/分发和设备稳定身份均未达原验收。
- 当前文件和行号：`src/vision_to_dds/src/vision_to_dds.cpp:75-83,126-162,260-345`；
  MAVROS residual path 见 `src/px4_bringup/launch/include/px4.launch.py:11-44` 和
  `config/mavros_params.yaml:4`；profile forbid 规则见 `config/profiles/dds_only_launch.yaml:3-39,188-193`。
- 当前证据：没有新的 vision fault suite、node integration、formal SITL、rollback rehearsal、
  legal/distribution approval 或 live graph evidence。profile 禁止 MAVROS/Agent/serial 是
  静态隔离，不能证明误启动时的实际控制权。
- 独立判定：`AUD-015,021` 为 **AGREE — STILL_OPEN**；`AUD-016..019,022..024` 为
  **AGREE — STILL_OPEN**；`AUD-020` 为 **INSUFFICIENT_EVIDENCE**（本线程未做法律/分发
  审查）。不得将 mock/synthetic 或 profile scan 解释成 SITL/硬件。
- 影响：感知错误、未审查双链、formal SITL/回滚及 release 条件仍没有实证。
- 修复：先完成 vision zero-publish fault matrix；H0-H2 通过后才做隔离 fake-transport H3；
  之后准备并批准 SITL preflight，formal SITL 与任何硬件步骤仍须独立执行/证据。
- 验收命令：frame/time/reset/dropout/nonfinite publisher-suppression tests；H3 bounded fake
  graph test；H4 approved SITL preflight parser/identity checks；相关 approval/rollback receipts。
- 是否阻塞 H0-H6：启用视觉的 P0 阻塞 H0-H6；其余 P1 至少阻塞 H1-H6 与其对应 release/promotion。

## 历史 P0/P1 完整交叉矩阵

| 基线 finding | 独立结果 | 依据 / 不得作出的推论 |
|---|---|---|
| `AUD-001..004`, `CUR-001` | **AGREE: OPEN** | XVAL-001；live writer 未接 gate。 |
| `AUD-005`, `CUR-002` | **AGREE: OPEN** | XVAL-002；auto-arm/TEXT_RC/ACK 未闭合。 |
| `AUD-006..007`, `CUR-004A` | **AGREE: OPEN** | XVAL-003；live state machine 未在 fault matrix 受测。 |
| `AUD-008..009`, `CUR-009` | **AGREE: OPEN** | XVAL-007；视觉 health 仍无完整闭环。 |
| `AUD-010` | **AGREE: symptom isolated; P1 not closed** | boundary PASS 仅来自 `COLCON_IGNORE`。 |
| `AUD-011`, `CUR-004` | **AGREE: OPEN** | canonical source/path/receipt 未确定。 |
| `CUR-003` | **AGREE: P0 OPEN; DISAGREE with “fixed”** | XVAL-004 direct open/write 仍在。 |
| `CUR-005` | **AGREE: OPEN** | XVAL-005 sanitizer parser test FAIL。 |
| `AUD-012`, `CUR-006` | **AGREE: OPEN** | exact checkout 不等于 governed PX4/toolchain/profile。 |
| `CUR-007` | **AGREE: OPEN** | root lock 和 final Offboard SHA 不同。 |
| `CUR-008` | **AGREE: OPEN** | 无 current successful H1 build receipt。 |
| `AUD-013` | **INSUFFICIENT_EVIDENCE** | 未执行 immutable CI/remote required-status 核验。 |
| `AUD-014` | **AGREE: OPEN** | gate tests PASS 但未测 live FSM。 |
| `AUD-015` | **AGREE: OPEN / formal SITL NOT-RUN** | 没有 formal SITL execution evidence。 |
| `AUD-016..019` | **AGREE: OPEN** | default/endpoint/ACK/atomicity/live authority 无闭环证据。 |
| `AUD-020` | **INSUFFICIENT_EVIDENCE** | 法律/分发批准不在本线程范围。 |
| `AUD-021` | **AGREE: OPEN** | 无实际 rollback rehearsal receipt。 |
| `AUD-022..024` | **AGREE: OPEN** | perception/device/precision profile 证据未完成。 |

## 最短剩余关键路径

1. 让正式 Offboard writer 实际使用同一个 fail-closed gate，去除默认 auto-arm/TEXT_RC，
   加入 correlated ACK、fresh RC/kill、restart 与 stale-input 闭环；以 production adapter 测试证明。
2. 取得 serial canonical origin/SHA/path/disposition；保持 `COLCON_IGNORE`，直至 fake backend
   的 authority/interlock/watchdog 和统一协议 sanitizer/fault matrix 全通过。
3. 将 Offboard、PX4/submodules/toolchain/board/RC profile 及 active source 纳入批准的 exact
   lock/receipt；不放宽 package profile。
4. 在新 `/tmp` 从锁定 snapshot 完成 H1 build/test receipt，再执行完整 H2 fault suite。
5. 仅在 H0-H2 都 GO 后进行隔离 fake-transport H3；完成 H4 SITL 前置审查。H5 需要用户
   单独硬件授权和实际台架证据；其后仍需两人拆桨/急停确认与用户再次明确授权才可重新评估 H6。
