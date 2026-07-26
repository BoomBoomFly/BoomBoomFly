# PX4、DDS 与 Offboard 接口契约审查

> 审查角色：Agent C
> 审查日期：2026-07-26（Asia/Shanghai）
> 根仓库：`/home/c/BoomBoomFly`
> 根分支：`agent/follow-latest-offboard`
> 根 HEAD：`3ce28094e14ed720987c5fc6d1172e377f09b1cc`
> 审查方式：当前 checkout 的只读静态检查；未启动 ROS、PX4、Agent、Offboard、视觉或任何硬件节点
> production 结论：**禁止启用**

## 1. 范围、基线与证据边界

开始审查前已完整读取以下强制材料：

- `README.md`
- `docs/handoff.md`
- `docs/CONTROL_AUTHORITY_MATRIX.md`
- `docs/adr/0001-dds-only-control-authority.md`
- `docs/evidence/OFFBOARD_PX4_MSGS_COMPAT_20260724.md`
- `docs/evidence/PX4_PARAMS_20260724T203458+0800.json`
- `workspace.lock.repos`
- `workspace.repos`
- `workspace.excluded_packages`
- `Scripts/README.md`
- `.gitignore`

未发现仓库内 `AGENTS.md`。`docs/adr/` 现有 1 个文件，`docs/evidence/` 现有 2 个文件，均已纳入。参数 JSON 是 2026-07-24 的 **历史、调整前快照**；文档明确说明维护者随后调整了 TELEM2/MAVLink/DDS 参数，因此本报告不把该 JSON 当作当前飞控配置。

本轮没有联网，没有取得或启动 PX4-Autopilot 源码/SITL，没有访问串口，没有运行 Agent，没有发布 `/fmu/in/*`，没有构建或刷写 firmware。已有实机 discovery 和 payload 仅作为带日期的历史证据；本轮未动态复验。

## 2. 当前锁定契约

| 组件 | manifest 锁定 | 当前 checkout | 结论 |
|---|---|---|---|
| `px4_msgs` | `392e831c1f659429ca83902e66820d7094591410` | 同 SHA；exact tag `v1.16.2`；clean detached HEAD | 已验证 |
| Micro XRCE-DDS Agent | `57d086216d01ec43121845d385894a25987f8a2c` | 同 SHA；exact tag `v2.4.2`；clean detached HEAD | 已验证 |
| `offboard_cpp` | `cded3dc5b6906420db3767abd82b2df7ba6ea9f0` | 同 SHA；`DDS` 分支；clean | 已验证 |
| `vision_to_dds` | `0c3a00137f3c90a4051ac1bc1029ec56beb669b6` | 同 SHA；clean detached HEAD | 已验证 |
| PX4-Autopilot | 未进入 lock | 当前仓库没有 checkout | 未验证；阻塞 firmware profile |

检查命令：

```bash
git -C src/{offboard_cpp,px4_msgs,Micro-XRCE-DDS-Agent,vision_to_dds} rev-parse HEAD
git -C src/{offboard_cpp,px4_msgs,Micro-XRCE-DDS-Agent,vision_to_dds} status --short --branch
git -C src/Micro-XRCE-DDS-Agent describe --tags --exact-match HEAD
git -C src/px4_msgs describe --tags --exact-match HEAD
```

实际结果：四个受查 checkout 均与 lock 一致；Agent 为 `v2.4.2`，消息集为 `v1.16.2`。

## 3. 已实现、部分实现与未验证能力

| 能力 | 状态 | 源码/证据 |
|---|---|---|
| `vehicle_status_v1` 精确 topic | 已实现 | `src/offboard_cpp/include/topics.hpp:7`；`src/offboard_cpp/src/node.cpp:44-48` |
| 版本 topic 回归测试 | 部分实现 | `test/test_topic_contract.cpp:16-40` 只检查常量和源文件文本，不验证生成 firmware 或真实 PX4 graph |
| RC normalized `[-1,1]` 语义 | 已实现 | `input.cpp:105-162`；`test_rc_input.cpp:107-142` |
| RC `signal_lost`、`channel_count`、finite/range、ROS 接收时 freshness | 已实现 | `input.cpp:23-35,63-124` |
| `/fmu/out/rc_channels` firmware 导出 | 完全缺失 | 仓库无 `dds_topics.yaml`、PX4-Autopilot checkout、patch、`.px4` artifact |
| VehicleCommand ACK | 完全缺失 | 源码无 `VehicleCommandAck` 订阅或结果处理 |
| VehicleStatus 首帧及 freshness | 完全缺失 | `State_Data_t` 只缓存消息，无接收标志或时间 |
| Offboard setpoint 预热门 | 部分/偶然实现 | FSM 每 20 ms 一律发布，但没有“有效 setpoint 连续 >=1 s”门或计数器 |
| DDS 输出 QoS | 部分实现 | Offboard 统一 best-effort/volatile；历史 PX4 输出 discovery 成功，本轮未复验 |
| DDS 输入 QoS | 未验证 | Offboard 同样使用 best-effort；历史证据没有证明 PX4 输入 reader 实际收包 |
| DDS domain、client key、Agent 参数统一源 | 完全缺失 | 仅历史命令中有串口和波特率；无项目级 profile/config |
| 外部视觉时间与 frame 契约 | 部分实现 | `vision_to_dds.cpp:262-338`；无转换/时间同步测试或 PX4 EKF 验收 |
| 精降接口 | 默认安全关闭 | `enable_precland=false` 时不创建 publisher；定制 firmware/profile 和验收均缺失 |
| 多机 namespace | 明确不支持 | ADR 禁止；旧 swarm launch 仍存在但无 Agent/client/domain 契约 |

## 4. Findings

### BBF-DDS-001 — VehicleCommand 未等待 ACK

- **级别：P0**
- **分类：PX4 command / 状态机**
- **证据：**
  - `src/offboard_cpp/src/node.cpp:28-84`：创建多个反馈订阅，但没有 `VehicleCommandAck`。
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:405-417`：命令直接发布。
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:427-478,486-512,614-741`：arm、land、mode 仅观察 `VehicleStatus`/landed 或超时。
  - `src/px4_msgs/msg/VehicleCommandAck.msg:5-35`：锁定消息定义提供 `command`、`result`、结果码及 target 字段。
- **检查命令：**

  ```bash
  grep -RInE "VehicleCommandAck|vehicle_command_ack" \
    src/offboard_cpp src/vision_to_dds
  ```

- **实际结果：**0 个源码匹配；DENIED、FAILED、TEMPORARILY_REJECTED、UNSUPPORTED、CANCELLED 和 IN_PROGRESS 均未处理。
- **预期结果：**每个 arm/mode/land 命令有可关联的 pending 状态；仅 ACCEPTED 且后续状态一致时迁移，拒绝或超时进入安全状态。
- **现象：**PX4 拒绝命令时，ROS 端不能区分拒绝、丢包和状态尚未更新；部分流程会按 3 秒超时重试，部分以观察到的状态判成功。
- **影响：**可能错误判断 arm、mode 或 land 事务，重复发送命令，或在状态反馈陈旧时进入错误 FSM 分支。
- **触发条件：**preflight 拒绝、mode 不可用、命令丢包、ACK 乱序/迟到、PX4/Agent 重连或 target identity 不一致。
- **建议修复：**订阅 `/fmu/out/vehicle_command_ack`；用 command、target、发送序号/时间窗关联事务；建立 ACK pending 状态与分类结果处理；ACK 后仍需 fresh `VehicleStatus` 二次确认。
- **验收标准：**
  - ACCEPTED 前不得完成状态迁移；
  - DENIED、FAILED、TEMPORARILY_REJECTED、UNSUPPORTED、CANCELLED 均保持/回到安全状态；
  - IN_PROGRESS 有独立超时；
  - ACK 丢失、迟到、重复、错误 command、错误 target 的测试全部 fail-closed；
  - SITL 证据来自 PX4 publisher，不使用 mock ACK。
- **依赖项：**BBF-DDS-003、BBF-DDS-006、PX4 SITL profile。
- **预计工作量：M**
- **是否阻塞 production：是**

### BBF-DDS-002 — RC “硬依赖”可被绕过且 production 二进制无条件启用 mock override

- **级别：P0**
- **分类：RC safety interlock**
- **证据：**
  - `src/offboard_cpp/CMakeLists.txt:33-35`：全局、无条件 `add_compile_definitions(TEXT_RC)`。
  - `src/offboard_cpp/src/node.cpp:15-18`：production 节点声明 `mock_rc_mode`、`mock_rc_gear`。
  - `src/offboard_cpp/src/lib/input.cpp:143-158`：收到真实 RC 后，mode/gear 被两个 ROS 参数覆盖。
  - `src/offboard_cpp/text/mock_rc_control.py:18-70`：脚本可发布伪 `/fmu/out/rc_channels` 并调用节点参数服务。
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:131-170`：自动起飞仅在 `rc_is_received()` 为真时检查 RC；RC 完全缺失时跳过检查。
  - `src/offboard_cpp/config/ctrl_param.yaml:12-16`：自动起飞和自动 arm 默认都为 true。
- **检查命令：**

  ```bash
  grep -RInE "TEXT_RC|mock_rc_mode|mock_rc_gear|rc_is_received" \
    src/offboard_cpp
  nl -ba src/offboard_cpp/src/lib/CtrlFSM.cpp | sed -n '131,170p'
  ```

- **实际结果：**真实 PX4 RC 帧只提供 freshness/有效性载体，最终模式权威来自可写 ROS 参数；无 RC 时，上层 `/offboard/takeoff_land=1` 仍可进入切模和 arm 流程。
- **预期结果：**production 构建不得包含 mock override；RC 首帧、有效性、freshness 和明确物理开关状态应是进入任何控制/arm 流程的强制前置条件。
- **现象：**文档声明 `/fmu/out/rc_channels` 是硬依赖，但源码对自动起飞并非 fail-closed，且 production 目标带有测试宏。
- **影响：**ROS graph 内任意可调用参数服务/发布内部起飞话题的进程可能绕过物理 RC 权威，形成非预期切模或 arm 请求。
- **触发条件：**误启动 mock、参数被设置、真实 RC 缺失但出现起飞命令、测试与 production 构建混用。
- **建议修复：**把 mock 编译为独立测试 target/profile，production target 编译期禁止；所有 arm/Offboard/takeoff 入口统一要求 fresh authoritative RC；生产启动时发现 mock publisher 或 mock 参数支持即退出。
- **验收标准：**
  - production 二进制符号/编译命令不含 `TEXT_RC`；
  - RC 从未收到、signal_lost、stale、通道无效、开关不满足时，起飞/arm/mode 命令发布计数为 0；
  - mock 只能在独立 ROS domain/namespace 的测试 target 中运行；
  - 加入“伪参数 + 真 RC”“无 RC + 起飞命令”故障注入测试。
- **依赖项：**定制 `rc_channels` firmware、graph guard/profile 隔离。
- **预计工作量：M**
- **是否阻塞 production：是**

### BBF-DDS-003 — VehicleStatus 无 freshness；Odom 首帧状态未初始化

- **级别：P0**
- **分类：反馈 freshness / 未初始化状态**
- **证据：**
  - `src/offboard_cpp/include/lib/input.hpp:90-106`：`pos_jump` 无初始化；`State_Data_t` 无 `has_received`/`rcv_stamp`。
  - `src/offboard_cpp/src/lib/input.cpp:218-245`：构造时 `rcv_stamp=now()`；feed 先再次覆盖时间，再用 `rcv_stamp==0` 判断首帧，因此通常永远不是首帧；随后读取未初始化的 `p`。
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:351-355`：`odom_is_received()` 不检查 `recv_new_msg`，并读取可能未初始化的 `pos_jump`。
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:443-458,633-648,685-741`：arm/mode 成功判断直接使用无 freshness 的 `current_state`。
- **检查命令：**

  ```bash
  grep -RInE "recv_new_msg|pos_jump|State_Data_t|current_state|rcv_stamp" \
    src/offboard_cpp/include src/offboard_cpp/src
  ```

- **实际结果：**无状态首帧/超时门；Odom 在首帧前和首帧处理时存在未初始化读取路径。
- **预期结果：**所有 PX4 权威反馈具有 `has_received`、ROS receive timestamp、合法性与统一 freshness；首帧不做前后差分；时钟回退/clock type 不同 fail-closed。
- **现象：**启动、DDS 断线或 Agent 重启后，FSM 可能使用默认/陈旧状态；首个 odometry 的 jump 判定不确定。
- **影响：**可能错误发送 ALTCTL/POSCTL/Offboard/arm 相关命令，或错误确认命令完成。
- **触发条件：**节点先于 Agent/PX4 启动、首帧 odometry、DDS 中断、PX4 重启、ROS time 跳变。
- **建议修复：**为 Odom、VehicleStatus、Battery、LandDetected 和内部命令建立统一 typed freshness wrapper；显式初始化全部成员；PX4 reboot/时间回退清空事务和 setpoint。
- **验收标准：**
  - 首帧前任何 VehicleCommand 发布计数为 0；
  - 首个 odometry 不读取前一位置；
  - stale status/odom、PX4 timestamp 回退、Agent 重连均进入安全状态；
  - sanitizer/单元测试覆盖未初始化路径。
- **依赖项：**BBF-DDS-001、统一时钟策略。
- **预计工作量：M**
- **是否阻塞 production：是**

### BBF-DDS-004 — 无可审计的 Offboard 预热门，且启动即发布控制流和切模命令

- **级别：P0**
- **分类：Offboard activation**
- **证据：**
  - `src/offboard_cpp/src/node.cpp:86-91`：FSM 50 Hz 无条件运行。
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:54-69,326-340`：每 tick 都发布 `TrajectorySetpoint` 和 `OffboardControlMode`，包括 POSITION/无有效反馈阶段。
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:76-102`：POSITION 状态会主动请求 ALTCTL/POSCTL。
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:123-128,161-166,614-681`：进入 Offboard 的请求没有有效 setpoint 连续时长/计数器。
- **检查命令：**

  ```bash
  nl -ba src/offboard_cpp/src/lib/CtrlFSM.cpp | sed -n '50,170p'
  nl -ba src/offboard_cpp/src/lib/CtrlFSM.cpp | sed -n '326,340p'
  nl -ba src/offboard_cpp/src/lib/CtrlFSM.cpp | sed -n '614,681p'
  ```

- **实际结果：**节点运行后会偶然形成连续发布，但没有证明消息有效、feedback ready、连续时间足够；在启动不到要求时长时也可直接发 mode command。
- **预期结果：**只在所有安全输入有效后进入 PRESTREAM；连续发布明确安全的 setpoint/control mode 达规定时间和最小样本数，随后才请求 Offboard，并等待 ACK + fresh status。
- **现象：**“一直发布”代替了显式 activation protocol；默认构造/零值 setpoint 在未就绪阶段也进入 `/fmu/in/*`。
- **影响：**无法证明满足 PX4 Offboard 激活契约；启动顺序和定时差异可能导致拒绝、重试或非预期 setpoint 被预装。
- **触发条件：**节点与 PX4/Agent 同时启动、RC 快速切换、内部起飞命令过早到达、ROS time 未稳定。
- **建议修复：**引入 `WAIT_FEEDBACK -> PRESTREAM -> MODE_PENDING -> ACTIVE`；记录有效样本数、连续时长、publish deadline 和中断原因；非控制状态不发送有效 control mode/setpoint。
- **验收标准：**
  - PRESTREAM 前 `/fmu/in/trajectory_setpoint`、`offboard_control_mode` 和 `vehicle_command` 均无控制发布；
  - 连续 >=1 s 且 >=20 个有效样本后才允许 mode request；
  - 任一 RC/odom/status/DDS freshness 中断清零预热；
  - PX4 SITL recorder 证明 publisher 和 payload 来自被测节点，非 mock。
- **依赖项：**BBF-DDS-001、BBF-DDS-003、SITL DDS profile。
- **预计工作量：L**
- **是否阻塞 production：是**

### BBF-DDS-005 — `rc_channels` firmware profile 及可追溯 artifact 完全缺失

- **级别：P1**
- **分类：PX4 v1.16.2 firmware / DDS topic generation**
- **证据：**
  - `workspace.lock.repos` 锁定 `px4_msgs`，但没有 PX4-Autopilot。
  - 仓库搜索无 `dds_topics.yaml`、无 `.px4` artifact。
  - `docs/evidence/OFFBOARD_PX4_MSGS_COMPAT_20260724.md:179-191` 的历史实机证据记录 `/fmu/out/rc_channels` 不存在；这不是本轮动态复验。
  - `src/offboard_cpp/src/node.cpp:50-54` 把该 topic 当运行依赖。
- **检查命令：**

  ```bash
  find . -path '*/dds_topics.yaml' -o -name '*.px4'
  grep -n "PX4-Autopilot" workspace.lock.repos
  ```

- **实际结果：**均无结果；不存在源码 patch、生成物检查、SITL PX4 publisher payload、FMUv3 构建日志或 artifact SHA-256。
- **预期结果：**锁定 PX4 `v1.16.2@54f0455f...` 及递归 submodule/toolchain，在 profile 中仅增加所需 topic，保存 patch、生成物、SITL、FMUv3 资源余量和 artifact hash。
- **现象：**Agent 配置不能补出 firmware 未生成的 topic，当前 RC safety interlock 无权威数据源。
- **影响：**Offboard 安全闭环无法在 SITL、台架或实机成立。
- **触发条件：**任何现有/default PX4 v1.16.2 firmware 启动 Offboard。
- **建议修复：**按路线阶段独立准备 PX4 source/toolchain；先静态生成和 SITL，再 FMUv3 构建；本阶段不刷写。
- **验收标准：**
  - 生成物包含 `RcChannels` DataWriter；
  - SITL `/fmu/out/rc_channels` 恰有一个 PX4 publisher，类型/QoS 正确并有真实 PX4 payload；
  - patch、submodule SHA、toolchain、日志、flash/RAM 余量、`.px4` SHA-256 全部留证；
  - baseline 不加入 `landing_target_pose`。
- **依赖项：**PX4 源码/工具链冻结。
- **预计工作量：L**
- **是否阻塞 production：是**

### BBF-DDS-006 — QoS 未按方向集中定义，PX4 输入交付未验证

- **级别：P1**
- **分类：DDS QoS**
- **证据：**
  - `src/offboard_cpp/src/node.cpp:22-35`：同一 best-effort/volatile depth=1 profile 同时用于 PX4 输入 publishers 和输出 subscriptions。
  - `src/vision_to_dds/src/vision_to_dds.cpp:83-84,161-162`：PX4 输入 publishers 使用整数 depth 的默认 QoS，和 Offboard 不一致。
  - `test/test_topic_contract.cpp` 不检查 QoS。
  - 历史 evidence 只证明若干 PX4 输出被 ROS 解码，没有证明 ROS 输入被 PX4 reader 接收。
- **检查命令：**

  ```bash
  grep -RInE "QoS|best_effort|reliable|durability" \
    src/offboard_cpp src/vision_to_dds
  ```

- **实际结果：**没有方向化 QoS 常量、生成 firmware endpoint 对照或 QoS 回归测试。
- **预期结果：**输出 subscription、控制 input publisher、视觉 input publisher 分开定义并与 v1.16.2 生成 endpoint 的 offered/requested QoS 逐项匹配。
- **现象：**不同节点对同一 PX4 输入方向使用不同 QoS；兼容性依赖中间件默认值。
- **影响：**可能出现 discovery 可见但输入不交付，或未来 RMW/生成配置变化导致静默回归。
- **触发条件：**RMW/QoS 默认变化、firmware profile 重生成、SITL/实机环境差异。
- **建议修复：**集中 `px4_qos.hpp`/配置；建立 type/topic/QoS 静态表和 SITL endpoint 断言。
- **验收标准：**所有关键 `/fmu/in/*`、`/fmu/out/*` 均有 exact topic/type/QoS 测试；SITL 证明 PX4 实际消费输入；QoS 不兼容注入时启动门拒绝。
- **依赖项：**BBF-DDS-005。
- **预计工作量：M**
- **是否阻塞 production：是**

### BBF-DDS-007 — ROS time、TF sample time 与 PX4 boot time 没有统一策略

- **级别：P1**
- **分类：timestamp / timesync**
- **证据：**
  - `src/px4_msgs/msg/{VehicleCommand,OffboardControlMode,TrajectorySetpoint,VehicleOdometry}.msg` 均注明 microseconds/system time。
  - `CtrlFSM.cpp:68-69,382,415,589` 直接使用 `node_->now()/1000`。
  - `vision_to_dds.cpp:307-310` 的 `timestamp` 来自 ROS now，`timestamp_sample` 来自 TF header。
  - launch 允许 `use_sim_time`，但没有 zero time、跳变、epoch/boot-domain 转换或 monotonicity 门。
- **检查命令：**

  ```bash
  grep -RInE "timestamp|timestamp_sample|use_sim_time|Timesync|timesync" \
    src/offboard_cpp src/vision_to_dds
  ```

- **实际结果：**只做单位换算，没有显式时钟域契约或验证。
- **预期结果：**每个字段明确来源、单位、epoch、单调性、最大延迟和 PX4 重启处理；视觉 sample time 与 publish time 的关系可测试。
- **现象：**仿真时钟未启动、TF 旧帧、ROS 时间回退或 PX4 重启时仍可能生成时间戳。
- **影响：**PX4/EKF2 可能拒绝、延迟融合或错误排序视觉与控制消息。
- **触发条件：**`use_sim_time=true`、bag replay、NTP/clock jump、TF freeze、PX4 reboot。
- **建议修复：**形成 timestamp ADR 和共享转换/校验库；对 zero/backward/future/stale timestamp fail-closed。
- **验收标准：**单元测试覆盖各时钟域和跳变；SITL 检查 PX4 接收时间与 sample delay；视觉 EKF innovation 证据包含延迟统计。
- **依赖项：**视觉 profile、SITL。
- **预计工作量：M**
- **是否阻塞 production：是**

### BBF-DDS-008 — 上层 setpoint 与 OffboardControlMode 未作为同一新鲜事务验证

- **级别：P1**
- **分类：Offboard input contract**
- **证据：**
  - `input.cpp:291-319`：两类消息分别缓存，构造时 `rcv_stamp=now()`，没有 `has_received`、sequence 或 owner。
  - `CtrlFSM.cpp:183-188`：AUTO_HOVER 进入 OFFBOARD 只检查 trajectory freshness。
  - `CtrlFSM.cpp:226-230`：随后直接复制可能未收到/陈旧的 `offboard_mode_data.msg`。
  - `CtrlFSM.cpp:357-372`：freshness 函数不检查首帧、负 age 或 clock mismatch。
- **检查命令：**

  ```bash
  nl -ba src/offboard_cpp/src/lib/input.cpp | sed -n '289,319p'
  nl -ba src/offboard_cpp/src/lib/CtrlFSM.cpp | sed -n '175,231p'
  ```

- **实际结果：**单独一帧 trajectory 可触发状态迁移；mode 与 setpoint 的字段一致性、发布者一致性和时间关联均未验证。
- **预期结果：**同一 owner/lease 下的 mode+setpoint 有 sequence、共同 freshness、合法字段组合和原子接受语义。
- **现象：**mode 全 false、mode/setpoint 控制维度冲突、旧 mode + 新 setpoint 都可能被转发。
- **影响：**PX4 可能拒绝 Offboard、选择错误控制层级或使用不完整 setpoint。
- **触发条件：**owner 启动顺序不同、其中一个 topic 丢包、多个 owner、重连。
- **建议修复：**引入命令 envelope/arbiter；至少在 Offboard 节点内要求两类首帧、同一时间窗和字段一致性。
- **验收标准：**缺 mode、缺 setpoint、模式冲突、stale、乱序、双 publisher 全部 fail-closed；不得发布到 PX4。
- **依赖项：**owner/lease、graph guard。
- **预计工作量：M**
- **是否阻塞 production：是**

### BBF-DDS-009 — domain、namespace、client key、Agent 和 vehicle identity 无统一配置源

- **级别：P1**
- **分类：transport / identity / 多机边界**
- **证据：**
  - 仓库搜索 `ROS_DOMAIN_ID|domain_id|client_key` 在项目配置中无结果。
  - `CtrlFSM.cpp:405-416` 硬编码 target/source system/component 为 `1`。
  - `docs/evidence/...:179` 只保留历史 Agent 命令 `MicroXRCEAgent serial -D /dev/ttyTHS0 -b 921600 -v 6`，未记录统一数字 domain/profile。
  - `offboard_swarm_control.launch.py:29-65` 创建 `/drone1..3`，但没有对应 PX4 namespace、Agent、client key、domain、port 或 vehicle identity。
- **检查命令：**

  ```bash
  grep -RInE "ROS_DOMAIN_ID|domain_id|client_key|MicroXRCEAgent" \
    README.md docs Scripts src/offboard_cpp src/vision_to_dds
  ```

- **实际结果：**除历史命令/说明外，没有机器可读的 transport profile。
- **预期结果：**单一 profile 明确 ROS domain、PX4 namespace、client key、Agent transport/port、system/component identity 和目标 PX4。
- **现象：**配置散落，当前只能依赖单机根 namespace 和默认 identity；旧 swarm launch 不能构成多机支持。
- **影响：**可能连接错误 PX4、测试 graph 污染真实 graph、重连身份混淆；无法安全扩展多机。
- **触发条件：**多个 PX4/Agent、共享主机、多 ROS domain、旧 launch 误启动。
- **建议修复：**新增机器可读 profile schema 与启动前一致性校验；当前明确禁止安装/运行 swarm launch。
- **验收标准：**profile 唯一生成 Agent/PX4/ROS 参数；identity 不一致时 fail-closed；双 Agent/client key/domain 冲突测试通过。
- **依赖项：**profile launcher、graph guard。
- **预计工作量：M**
- **是否阻塞 production：是**

### BBF-DDS-010 — 外部视觉/精降 DDS 契约缺少转换与时序测试

- **级别：P1**
- **分类：visual odometry / precision landing**
- **证据：**
  - `vision_to_dds.cpp:24-31,275-292`：通过若干固定角参数进行位置/四元数变换。
  - `vision_to_dds.cpp:307-338`：声明 `POSE_FRAME_FRD`，velocity unknown，固定 covariance/quality/reset_counter。
  - `vision_to_dds.cpp:129-163`：精降默认关闭，这是正确的 fail-closed 默认；开启后 topic 可由参数任意指定。
  - `vision_to_dds/CMakeLists.txt:44-53`：只有 lint，没有坐标、timestamp、TF freeze、reset 或 DDS contract 单元测试。
- **检查命令：**

  ```bash
  nl -ba src/vision_to_dds/src/vision_to_dds.cpp
  nl -ba src/vision_to_dds/CMakeLists.txt
  ```

- **实际结果：**实现存在，但 ENU/NED/FLU/FRD 数学、frame_id、covariance、quality、reset、freeze 和 timestamp 没有测试；PX4 EKF 消费未验证。
- **预期结果：**每个输入 frame 到 PX4 VehicleOdometry 字段有数学规范、金样测试和 SITL/EKF 验收；精降独立 profile。
- **现象：**参数可改变旋转，但没有证明输出与 `POSE_FRAME_FRD` 语义一致；TF 仅在 stamp 递增时发布，无明确 freeze timeout/健康输出。
- **影响：**可能向 EKF 注入方向、姿态或时间错误的数据。
- **触发条件：**相机 frame 变化、T265 缺失/重启、TF freeze、参数误配、启用精降。
- **建议修复：**先建立纯函数转换与金样测试；加入 TF age/reset/quality 门；视觉和精降分别建立 firmware/profile 与 EKF 前置检查。
- **验收标准：**轴向基向量、90° rotations、已知 quaternion、timestamp delay、TF freeze/reset 测试通过；SITL 使用 PX4 subscriber 证明消费；精降默认 profile 不出现 publisher。
- **依赖项：**BBF-DDS-007、感知 profile、EKF2 前置参数证据。
- **预计工作量：L**
- **是否阻塞 production：是**

### BBF-DDS-011 — RC 物理通道映射未与 PX4 function/current parameters 建立契约

- **级别：P1**
- **分类：RC mapping**
- **证据：**
  - `RcChannels.msg:3-38` 提供 `function[]` 映射和 `FUNCTION_OFFBOARD/KILLSWITCH`。
  - `input.cpp:79-100,143-144` 仅按 YAML 原始数组索引读取 mode/gear，不读取 `function[]`，也不检查 kill function。
  - `ctrl_param.yaml:23-29` 使用 `ch_mode=8`、`ch_gear=9`。
  - 历史参数证据记录 2026-07-24 的 `RC_MAP_OFFB_SW=6`、`RC_MAP_KILL_SW=8`；该值已标记为历史，当前参数未验证。
- **检查命令：**

  ```bash
  nl -ba src/px4_msgs/msg/RcChannels.msg
  nl -ba src/offboard_cpp/config/ctrl_param.yaml
  nl -ba src/offboard_cpp/src/lib/input.cpp | sed -n '79,144p'
  ```

- **实际结果：**normalized/PWM 混用已修复，但“哪个物理开关是 Offboard/kill”的契约仍依赖手工零基索引，且没有与当前飞控参数交叉验证。
- **预期结果：**使用 `function[]` 或经过验收的显式映射；启动时与参数/profile 一致；kill 优先级和边沿/去抖有测试。
- **现象：**错误索引可能把无关通道当作授权开关；历史 snapshot 与 YAML 数字也没有可证明对应关系。
- **影响：**安全互锁可能永远不触发或由错误通道触发。
- **触发条件：**接收机通道重映射、不同遥控器、YAML 索引基准误解、参数变化。
- **建议修复：**优先按 `function[]` 解析；保留显式 fallback 时校验唯一性和当前参数证据；加入 kill 独立路径。
- **验收标准：**真实/仿真 PX4 publisher 的 function mapping 测试；任意重映射后仍识别正确；重复/缺失 function fail-closed；保存调整后只读参数快照。
- **依赖项：**BBF-DDS-005、获批后的参数只读复验。
- **预计工作量：M**
- **是否阻塞 production：是**

### BBF-DDS-012 — topic 字面量只集中管理了 VehicleStatus

- **级别：P2**
- **分类：接口维护性 / 回归测试**
- **证据：**
  - `include/topics.hpp:7` 只有 `kVehicleStatus`。
  - `node.cpp:28-81` 的其余 `/fmu/in/*`、`/fmu/out/*` 仍为散落字面量。
  - `test_topic_contract.cpp:23-40` 通过读取 C++ 源文件文本验证，未对消息版本、QoS 或生成 firmware manifest 做结构化校验。
- **检查命令：**

  ```bash
  nl -ba src/offboard_cpp/include/topics.hpp
  nl -ba src/offboard_cpp/test/test_topic_contract.cpp
  ```

- **实际结果：**`vehicle_status_v1` 回归已被防护；其他关键 topic 可独立漂移。
- **预期结果：**所有关键 topic/type/version/QoS 由一份机器可读契约生成或校验。
- **现象：**修复是单点字符串测试，不能提前发现 `rc_channels`、ACK、视觉或 QoS 契约变化。
- **影响：**升级 PX4/px4_msgs 或 profile 时可能再次发生运行时静默不匹配。
- **触发条件：**消息版本升级、topic rename、firmware profile 修改。
- **建议修复：**建立 interface manifest，静态比对 `px4_msgs` MESSAGE_VERSION、节点端点与 PX4 生成清单。
- **验收标准：**CI 对每个关键 endpoint 生成 exact topic/type/version/QoS 断言；旧字面量和不匹配 profile 阻止合并。
- **依赖项：**BBF-DDS-005、BBF-DDS-006。
- **预计工作量：S**
- **是否阻塞 production：否（但被相关 P1 覆盖）**

## 5. 重点检查结论

1. **PX4 v1.16.2 topic 名称：**`vehicle_status_v1` 已由当前源码和消息版本交叉验证；其余默认 firmware topic 因无 PX4-Autopilot/`dds_topics.yaml` 只能结合历史 discovery，当前静态未验证。
2. **版本化消息集中管理：**仅 VehicleStatus 已集中；其余未形成机器可读版本契约。
3. **`rc_channels` 硬依赖：**RC parser 本身首帧/失联/freshness fail-closed，但自动起飞路径可在 RC 缺失时继续，且 `TEXT_RC` 覆盖真实开关，整体不满足硬依赖。
4. **RC 完整校验：**`signal_lost`、`channel_count`、数组界、finite、range、ROS receive freshness 已实现；`timestamp_last_valid`、function mapping、kill function 未使用。
5. **normalized 与 PWM：**当前核心 parser 和测试使用 normalized；未发现核心控制路径继续做 1000..2000 转换。历史参数中的 PWM calibration 不等于消息语义混用。
6. **timestamp：**只做 ROS/TF 时间到微秒换算；boot/ROS/sim time 契约和重启处理未实现。
7. **QoS：**历史输出 payload 证明部分 PX4→ROS 链路曾工作；ROS→PX4 输入 QoS 和消费未验证。
8. **VehicleCommand ACK：**完全未实现。
9. **Offboard 预热：**有 50 Hz 连续发布，但无有效样本/持续时间/readiness 门，不能作为合格验收。
10. **domain/namespace/client key/Agent：**无统一配置源；当前仅批准单机根 namespace，多机 launch 不构成支持。
11. **firmware profile：**源码、patch、生成物、SITL PX4 publisher 证据、FMUv3 artifact/hash 均缺失。
12. **SITL 验收来源：**本轮未运行 SITL；现有 RC gtest 使用 mock message，只能证明 parser，不能证明 PX4 publisher/profile。

## 6. 分级统计与最短关键路径

| 等级 | 数量 |
|---|---:|
| P0 | 4 |
| P1 | 7 |
| P2 | 1 |
| P3 | 0 |

最短关键路径：

1. 冻结 PX4 v1.16.2 源码/submodule/toolchain，生成只增加 `rc_channels` 的 firmware profile；
2. 在隔离 SITL 中证明 topic/type/QoS/PX4 publisher payload；
3. 移除 production `TEXT_RC`，使所有控制入口真正依赖 authoritative RC；
4. 统一 feedback 首帧/freshness/PX4 reboot 处理；
5. 实现 VehicleCommand ACK 事务；
6. 实现显式 Offboard PRESTREAM 门；
7. 完成 RC/DDS/odom/status/ACK 故障注入后，才进入拆桨台架。

## 7. 本轮实际执行的命令类别

```text
git rev-parse / remote / branch / status / describe
find（基线文件、相关源码、dds_topics.yaml、firmware artifact）
wc
cat
sed
nl -ba
grep -RInE
```

环境中 `rg` 不存在，首次搜索返回 `rg: command not found`，随后改用 `grep`；这不是代码缺陷。环境缺少 bwrap，因此经用户批准后在沙箱外执行了只读命令。

## 8. 未验证项

- 当前飞控调整后的 PX4 参数、DDS domain、client key 和 TELEM2 回滚值；
- PX4 v1.16.2 官方/定制 `dds_topics.yaml` 本地源码；
- firmware 静态生成、FMUv3 build、flash/RAM 余量与 artifact SHA-256；
- ROS→PX4 input topic 的实际 QoS 匹配和 payload 消费；
- VehicleCommand ACK 正常/拒绝/超时行为；
- Offboard 激活、RC/DDS/odom/status loss；
- 外部视觉 EKF2 消费、坐标与时间延迟；
- 精降 profile；
- SITL、台架和实机控制。

上述内容均因仓库缺少相应源码/入口、环境缺少工具链，或受本轮安全边界限制而保持 **未验证**，未伪造成功结果。
