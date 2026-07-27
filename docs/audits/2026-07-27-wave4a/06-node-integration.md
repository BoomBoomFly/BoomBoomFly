# Wave 4A — 无硬件节点级集成审查

审查时间：2026-07-27（Wave 4A Thread E）  
范围：只读审查 Offboard、vision 与 bringup 的节点/launch/配置/测试入口；执行两组
明确为纯软件的静态或 contract 单元测试。  
基线：已完整读取 `docs/current_audit/00,02,03,04,05,07,08,09`，并读取本 Wave
的 `03-serial-safety.md` 和 `04-build-evidence.md`。根基线为
`master@0ed9d148bfbfd22253142172bbfe93c51106fdfa`，Offboard 为
`976d6217d73a28b72e64300e2dd04bcbeeee30d7`。  
安全边界：**未运行** `ros2 launch`、`ros2 run`、DDS Agent、MAVROS、PX4/SITL、
任何 `/fmu/in/*` 发布或真实驱动；未打开 `/dev/tty*`，未访问硬件。

## 结论

```text
H0: NO-GO
H1: NO-GO（本 Wave 的 H1 构建入口在 package-boundary 前置检查退出；未启动 colcon）
H2: NO-GO（仅局部纯软件测试；不是完整目标单元矩阵）
H3: NOT-RUN
H4: NOT-RUN
H5: NOT-RUN
H6 READINESS: NOT READY

HARDWARE ACCESSED: NO
FORMAL SITL RUN: NO
NODE/ROS GRAPH STARTED: NO
```

本线程不能也没有尝试“无硬件节点级集成”：其明确前置 H0/H1/H2 全部 GO 尚未满足；
当前没有经静态 guard 批准的 fake-transport、隔离 DDS domain、bounded
`launch_test` 入口。任何把下述 pure contract/静态检查写为“节点已启动”、
“PX4 已消费”或 H3 GO 的说法均不成立。

## 本轮可证明范围

| 检查 | 结果 | 能证明什么 | 不能证明什么 |
|---|---:|---|---|
| `test/launch_guard` Python unittest | 11/11 PASS | guard 的 fixture 能拒绝 Agent、MAVROS、设备、重复 writer 和动态 launch，并要求未知 launch review | 不会启动节点；没有验证正式 launch 的运行时 graph、QoS 或退出 |
| `src/offboard_cpp/test/test_offboard_gate_contract.py` | 12/12 PASS | test-only oracle 在 missing/stale/future frame、ACK 拒绝/超时、旧 epoch、authority reject 时保持 synthetic `publish_count=0` | 文件自述“不创建 ROS nodes、不发布 real topics”；不能约束 live `CtrlFSM` |
| 当前源码/配置/launch 静态读取 | 完成 | 可定位 publisher、subscription、QoS、launch 和 shutdown 设计 | 不能取得 ROS graph、实际 QoS match、节点退出或重启的执行证据 |

测试命令均以 `PYTHONPYCACHEPREFIX=/tmp/boomboomfly_wave4a_node_integration_pycache`
运行；除 `/tmp` 缓存和测试临时夹具外没有写入。本轮没有运行 C++ ament/gtest：当前
H1 构建未成功，且本线程不得创建 ROS graph。

## 静态控制/节点图谱

| 组件 | 静态输入/输出 | QoS/配置 | H3 含义 |
|---|---|---|---|
| `offboard_node` | 订阅 `fmu/out/*`、`offboard/cmd*`、`offboard/takeoff_land`；发布 `fmu/in/trajectory_setpoint`、`fmu/in/offboard_control_mode`、`fmu/in/vehicle_command` | `node.cpp:22-35` 对三个 PX4 写端使用 `KeepLast(1)+best_effort+volatile`；无隔离 domain/remap | 是直接真实 PX4 topic 名称，不能作为 fake-transport 入口执行 |
| `offboard_demo`/`animal_testing` | 发布 `offboard/cmd*`、`offboard/takeoff_land`，可驱动正式 node | `offboard_demo.cpp:10-15`、`animal_testing.cpp:10-15` | 不是安全 test fake；已有 launch 只能在完整控制链被关闭后重新评审 |
| `vision_to_dds_node` | 默认可发布 `/fmu/in/vehicle_visual_odometry`；参数可启用 `/fmu/in/landing_target_pose` | `vision_to_dds.cpp:79-84,130-163,307-345` | 直接控制输入，且当前没有 H3 fake/missing-input/restart test |
| `px4_bringup` 历史 launch | MAVROS、serial、RealSense/vision、`ros2 run` 串联 | `px4.launch.py:10-47`、`px4_fly.launch.py:8-53`、`start_all_2025TI.launch.py:8-48` | 明确不符合本任务“无硬件、无 Agent/MAVROS”边界 |

`config/profiles/dds_only_launch.yaml:38-40` 明确将 `/fmu/in/` 作为 forbidden topic
pattern，`:172-184` 只把 `offboard_control.launch.py` 放入**静态 allowlist**，同时写明
production disabled、该文件不获运行授权。该 profile 没有提供 H3 fake domain 或
transport substitute。

## 发现

### BBF-W4A-NODE-001 — 正式 Offboard 节点不是受测 runtime gate/fake transport 的使用者

- Finding ID：BBF-W4A-NODE-001（映射历史 `BBF-CUR-001`、`BBF-CUR-004A`）
- 严重级别：P0
- 历史结论：Wave 3B runtime gate 仅有 offline/standalone 覆盖；current audit 判
  live node 直接发布，H0 NO-GO、H3 NOT-RUN。
- 当前文件和行号：`src/offboard_cpp/src/node.cpp:20,28-35,87-91` 创建 FSM、三个
  `/fmu/in/*` publisher 并每 20 ms 调 `FSM()`；`src/offboard_cpp/src/lib/CtrlFSM.cpp:339-340`
  无条件发布 setpoint/mode，`:405-417` 直接发布 `VehicleCommand`。受测 gate 是独立
  `src/lib/offboard_runtime_gate.cpp:42-260`，而 `node.cpp` 没有实例化或调用它。
- 当前证据：本轮源码扫描只找到 standalone `OffboardRuntimeGate` 测试与 test-only
  Python oracle；未找到 production fake transport、`VehicleCommandAck` subscription、
  runtime gate adapter 或 node-level publisher spy。
- 状态：**STILL_OPEN**。
- 影响：在无输入、陈旧输入、ACK reject/timeout、PX4/Agent/节点重启时，纯 gate 的
  `publish_count=0` 不能约束真实 publisher；静态源码反而显示状态机路径可周期写入。
- 修复：先由 H0 线程把唯一 writer、gate、authority/epoch、ACK、freshness、PRESTREAM
  和 restart reset 接到 production transport；随后为该 transport 注入 fake clock/
  fake publisher，并测试每个拒绝路径 `fmu/in` write-count=0。
- 验收命令：**仅 H0/H1/H2 GO 且隔离方案获批后**，在唯一 `ROS_DOMAIN_ID`、无 Agent/
  PX4/设备的 bounded `launch_test` 中启动 fake transport；断言启动前、无输入、stale
  input、ACK reject/timeout、duplicate writer、PX4/Agent 模拟重启和 node restart 时
  三个 `/fmu/in/*` write-count 都为 0。
- 是否阻塞 H0-H6：H0 是；H1/H2 是（实现/测试路径不一致）；H3 是；H4-H6 是。

### BBF-W4A-NODE-002 — 当前 launch 入口不满足隔离、设备禁止和唯一 writer 的 H3 条件

- Finding ID：BBF-W4A-NODE-002（映射历史 `BBF-CUR-003`、`BBF-CUR-010`）
- 严重级别：P1（与 NODE-001 的 P0 共同使 H3 不可进入）
- 历史结论：current audit 要求 H0/H1/H2 GO 后才可运行 fake transport graph；历史
  bringup 需保持隔离。
- 当前文件和行号：`offboard_control.launch.py:31-53` 无 domain 隔离或 topic fake
  remap，直接启动 `offboard_node`；`offboard_swarm_control.launch.py:29-73` 同时启动
  三个 writer。`px4_bringup/launch/include/px4.launch.py:10-47` 引入 MAVROS，配置
  `mavros_params.yaml:4` 为 `/dev/ttyTHS0:921600`；`px4_fly.launch.py:8-53` 引入
  RealSense、vision-to-MAVROS 和 MAVROS；`start_all_2025TI.launch.py:35-42` 包含
  `ros2 run`。
- 当前证据：`dds_only_launch.yaml:2-40` 把 Agent、设备、MAVROS/serial/camera 和
  `/fmu/in/` 设为拒绝项；`:181-184` 明确 static allowlist 不是运行授权且
  production disabled。本轮 launch guard fixture suite 11/11 PASS，但它只是 guard
  的自测；没有批准或启动任何当前 launch。
- 状态：**STILL_OPEN**。
- 影响：直接运行任一现有入口可能连接真实 DDS domain、设备或多 writer；没有可安全
  替代它们的 H3 launch/test profile。
- 修复：新增专用、单 writer、默认拒绝的 H3 test-only profile：固定隔离 domain、只
  连接 fake transport/publisher spy、禁止所有 device/Agent/MAVROS/PX4 executable，设
  bounded timeout 和强制 cleanup；由静态 guard 将其精确 allowlist。
- 验收命令：先对新入口运行 `Scripts/test/launch_guard/check_launch_safety.py`；只有
  H0-H2 GO 后，使用独立 DDS domain 运行其 bounded `launch_test`，保存 graph、QoS、
  writer-count、退出和 restart 日志。不得连接 `/fmu/in` 的真实 graph。
- 是否阻塞 H0-H6：H0 是（现有控制入口不安全）；H1/H2 是（需要闭环验证）；H3 是；
  H4-H6 是。

### BBF-W4A-NODE-003 — 视觉节点存在直接 PX4 输入输出，但无 node-level 缺失/陈旧/退出证据

- Finding ID：BBF-W4A-NODE-003（映射历史 `BBF-CUR-009`）
- 严重级别：P1
- 历史结论：视觉 frame/time/reset/quality/dropout health gate 未闭合，production
  disabled；异常输入应当 zero publish。
- 当前文件和行号：`src/vision_to_dds/src/vision_to_dds.cpp:79-84` 创建默认
  `/fmu/in/vehicle_visual_odometry` publisher；`:130-163` 可由参数创建
  `/fmu/in/landing_target_pose`；`:307-345` 在 transform 成功路径直接发布，且写死
  `reset_counter=0`、`quality=1`；`:353-359` 只有普通 `spin` 后 shutdown。
- 当前证据：当前目录没有 `src/vision_to_dds/test/`；没有 fake TF/transport、dropout、
  stale timestamp、node shutdown 或 restart 的节点级测试入口。本轮未启动该节点。
- 状态：**STILL_OPEN**。
- 影响：不能以“没有输入时应不发布”的设计推断替代实际 node 证据；视觉若被启用可形成
  与 Offboard 并列的 `/fmu/in/*` writer。
- 修复：先完成视觉 H0 fail-closed health gate 和纯函数矩阵，再用 fake TF、fake clock
  和 publisher spy 建立隔离 node test；baseline 持续不创建 precision landing writer。
- 验收命令：在获批 H3 fake graph 中表驱动注入 no-first-frame、dropout、stale/future/
  backward time、reset、NaN/Inf、frame/quality mismatch 和 restart；每项 PX4 writer
  count=0，并验证 node 停止后没有重连/残留 publisher。
- 是否阻塞 H0-H6：H0（启用视觉 profile 时）是；H1 否；H2 是；H3-H6 是。

### BBF-W4A-NODE-004 — 已通过的测试仅验证静态策略/合同，不验证节点启动、QoS、退出或重启

- Finding ID：BBF-W4A-NODE-004
- 严重级别：P1（证据缺口）
- 历史结论：H3 为 NOT-RUN；mock/synthetic 不得代替真实节点或硬件。
- 当前文件和行号：`src/offboard_cpp/test/test_offboard_gate_contract.py:1-5` 明确测试
  不创建 ROS node/real topic；`:77-120,123-208,211-293` 覆盖 ACK、freshness、clock、
  restart 的 contract。`test/launch_guard/test_launch_safety.py:25-137` 使用离线 AST
  分析 fixture；`src/offboard_cpp/test/test_topic_contract.cpp:16-40` 只检查一项
  VehicleStatus topic 字面契约。
- 当前证据：本轮命令实际通过 12/12 contract 与 11/11 guard tests；没有 `launch_test`
  文件、ROS graph 记录、QoS endpoint match、进程退出、重启或 `VehicleCommandAck`
  transport 注入日志。
- 状态：**INSUFFICIENT_EVIDENCE**，不得标为 FIXED。
- 影响：不能证明正式 node 的 startup ordering、参数加载、QoS 兼容性、无输入/陈旧
  输入零执行输出或退出/重启行为。
- 修复：在生产 gate 完整接线后，增加隔离 node integration suite，并明确每项测试的
  fake-only 边界及 cleanup receipt。
- 验收命令：目标包从已验证 H1 artifact 运行 bounded fake-transport `launch_test`；保存
  启动配置、图、QoS、进程退出码、重启 epoch 和 publisher spy 的零输出断言。mock 成功
  只能作为 H3 的一部分，不能作为 SITL/H5/H6 证据。
- 是否阻塞 H0-H6：H0/H1/H2 间接是；H3 是；H4-H6 是。

## H3 最短剩余关键路径

1. 先关闭 NODE-001 的 H0 P0：生产 writer 必须使用已经单测的 fail-closed gate；关闭
   default auto-arm/TEXT_RC、ACK/authority/restart/freshness 与 serial/vision P0/P1。
2. 完成 serial canonical disposition、PX4/Offboard exact lock 和 package boundary，取得
   当前提交的隔离 H1 build receipt；然后执行完整 H2 live-FSM/fault matrix。
3. 新建并静态批准 test-only H3 launch：唯一 writer、独立 DDS domain、fake transport/
   publisher spy、无 `/dev`/Agent/MAVROS/PX4/SITL、bounded timeout/cleanup。
4. 执行 H3 node tests，实际保留启动、配置、QoS、no-input/stale-input、ACK reject/
   timeout、PX4/Agent 模拟重启、node restart 与退出日志；所有拒绝场景执行 write-count
   为 0。
5. 仅在 H0-H3 全部 GO 后再评审 H4 前置。H5/H6 仍需独立硬件授权、实体安全检查和
   人工确认；本报告不授权任何硬件动作。

## 命令证据

| 命令 | 退出 | 说明 |
|---|---:|---|
| `env PYTHONPYCACHEPREFIX=/tmp/boomboomfly_wave4a_node_integration_pycache python3 -m unittest discover -s test/launch_guard -p 'test_*.py' -v` | 0 | 11/11 静态 launch-guard tests PASS；不启动 ROS |
| `env PYTHONPYCACHEPREFIX=/tmp/boomboomfly_wave4a_node_integration_pycache python3 -m unittest discover -s test -p 'test_offboard_gate_contract.py' -v`（cwd `src/offboard_cpp`） | 0 | 12/12 test-only gate contract PASS；测试注释明确不创建 ROS node/real topic |
| `find`、`grep -RInE`、`nl -ba ...` 静态源码/配置清点 | 0 | 仅只读；用于本报告文件/行号，不建立 ROS graph |

未执行：ROS 节点、launch、DDS graph、Agent、MAVROS、PX4/SITL、硬件或设备访问。
