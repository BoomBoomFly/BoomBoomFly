# 控制权、安全与故障处理审查

## 1. 审查基线与边界

- 审查时间：2026-07-26（Asia/Shanghai）
- 根仓库：`/home/c/BoomBoomFly`
- 根仓库分支：`agent/follow-latest-offboard`
- 根仓库 HEAD：`3ce28094e14ed720987c5fc6d1172e377f09b1cc`
- 根仓库 origin：`https://github.com/BoomBoomFly/BoomBoomFly.git`
- 受管 Offboard 仓库：`src/offboard_cpp`
- Offboard HEAD：`cded3dc5b6906420db3767abd82b2df7ba6ea9f0`
- Offboard origin：`https://github.com/BoomBoomFly/offboard_cpp.git`
- 审查方式：源码、配置、launch、测试、manifest、ADR、证据及 Git 状态的只读交叉检查。
- 未执行：构建、测试、ROS/PX4/Agent/硬件节点启动、topic/service 调用、串口访问、参数读写、固件操作和网络访问。

开始审查时根仓库仅有未跟踪的 `docs/audits/`；`src/offboard_cpp` 为干净 checkout。本文把根仓库治理问题与受管外部依赖 `offboard_cpp` 的源码问题分别标注。`docs/evidence/PX4_PARAMS_20260724T203458+0800.json` 是历史参数快照；根据 `docs/evidence/OFFBOARD_PX4_MSGS_COMPAT_20260724.md:161-164`，它不是 2026-07-25 参数调整后的当前飞控配置，本文不据此断言当前参数状态。

## 2. 当前实现状态

| 能力 | 状态 | 源码/证据 |
|---|---|---|
| DDS-only 控制权规则 | 文档已冻结，运行时未强制 | `docs/adr/0001-dds-only-control-authority.md:92-108` |
| trajectory/mode/vehicle command 单一实现出口 | 部分实现 | `src/offboard_cpp/src/node.cpp:28-35` 集中发布，但可启动多个节点实例且无 graph guard |
| mission owner 唯一性 | 未实现 | demo/animal 均可发布相同内部命令；消息无 owner/lease |
| RC 帧校验 | 已实现 | `src/offboard_cpp/src/lib/input.cpp:23-35,63-213` |
| RC safety interlock 可用性 | 未闭环 | 历史只读硬件证据显示 `/fmu/out/rc_channels` 缺失；起飞分支允许无 RC 时继续 |
| VehicleCommand ACK | 完全缺失 | 无 ACK 订阅、pending 状态或 result 分类 |
| odometry/command freshness | 部分实现 | 有 receive-time timeout，但首帧、负时间、finite 和 mode 配对不完整 |
| vehicle status freshness | 完全缺失 | `State_Data_t` 只缓存消息 |
| 低电量处理 | 部分实现 | 有低电量降落状态；缺失/陈旧电池数据不 fail-closed |
| kill/emergency stop | 完全缺失 | 源码无独立 kill/emergency 输入或锁存安全态 |
| 故障注入测试 | 完全缺失 | 现有测试仅 RC 解析与 topic 常量 |
| production profile | 文档声明禁用，无可执行入口 | `docs/CONTROL_AUTHORITY_MATRIX.md:94-124`、launch 源码 |

## 3. 发现

### BBF-SAFE-001

- **级别：P0**
- **分类：控制写入唯一性 / graph guard**
- **归属：根仓库运行约束 + 受管依赖 `offboard_cpp`**
- **证据：**
  - `src/offboard_cpp/src/node.cpp:28-35`：每个 `offboard_node` 实例都直接创建 trajectory、OffboardControlMode 和 VehicleCommand 发布者。
  - `src/offboard_cpp/launch/offboard_control.launch.py:38-53`：可直接启动控制 writer，无 profile 或排他检查。
  - `src/offboard_cpp/launch/offboard_swarm_control.launch.py:28-72`：一次启动三个 writer 实例，但没有将实例绑定到 PX4 system/client identity 的契约。
  - `docs/adr/0001-dds-only-control-authority.md:108,160-165`：文档明确承认当前没有运行时强制。
- **现象：** 静态扫描确认 managed control path 的 PX4 输入发布集中在 `offboard_node`，但源码中没有 publisher 数量检查、ROS graph guard 或启动时 fail-closed 门；同一节点可被重复启动。
- **影响：** 同一目标 PX4 上可能出现多个 trajectory/mode/command writer，造成设定点竞争、模式命令竞争或错误飞行器被控制。
- **触发条件：** 重复 launch、同 namespace 重启残留、运维误启动，或多机 namespace/transport 映射错误。
- **检查命令：**
  - `grep -RInE "create_publisher|/fmu/in/|fmu/in/" --exclude-dir=.git src/offboard_cpp src/vision_to_dds`
  - `grep -RInE "get_publishers_info_by_topic|count_publishers|get_node_graph_interface|GraphEvent" --exclude-dir=.git src/offboard_cpp src/vision_to_dds`
- **实际结果：** 找到直接 PX4 输入 writer；未找到 graph guard API 使用。
- **预期结果：** production 启动前和运行中应确认每机恰好一个控制 writer，重复、消失或 namespace 不匹配均锁止控制输出。
- **建议修复：** 在正式 production launcher 和控制节点中实现启动前/持续 graph guard；多机配置显式绑定 namespace、DDS domain、client key、system id，并在冲突时进入不可自动恢复的安全态。
- **验收标准：**
  - 重复启动任一 writer 时两个实例都不得发送控制消息，或仅唯一获授权实例可发送；
  - writer 消失、重复和重连均产生结构化故障并保持 fail-closed；
  - 单机和三机 namespace/system/client-key 映射有自动化静态及 SITL 测试；
  - production graph 验收证明每机 trajectory/mode/command writer 均为 1。
- **依赖项：** BBF-SAFE-002、production profile、PX4 DDS namespace/client identity 契约。
- **预计工作量：L**
- **是否阻塞 production：是**

### BBF-SAFE-002

- **级别：P0**
- **分类：mission owner / lease / 仲裁**
- **归属：根仓库架构 + 受管依赖 `offboard_cpp`**
- **证据：**
  - `src/offboard_cpp/src/node.cpp:56-78`：内部命令 topic 直接进入 FSM。
  - `src/offboard_cpp/src/examples/offboard_demo.cpp:10-15` 与 `src/offboard_cpp/src/examples/animal_testing.cpp:10-15`：两个候选 owner 发布相同三个命令 topic。
  - `src/offboard_cpp/src/lib/input.cpp:291-319`：命令缓存只有 payload 和本机接收时间，没有 owner、lease、sequence 或会话 epoch。
  - `docs/CONTROL_AUTHORITY_MATRIX.md:36-49,138-140`：要求一个 mission owner，但注明尚未实现。
- **现象：** 任意能发布 `/offboard/cmd`、`/offboard/cmd_mode`、`/offboard/takeoff_land` 的节点都可驱动 FSM；没有授权、租约、序号、原子配对或旧 owner 隔离。
- **影响：** 并发 owner、重启后的旧消息/旧 owner、网络分区后重连均可能夺取或混合控制权。
- **触发条件：** demo 与 animal 同时运行、正式 owner 与示例节点并存、owner 崩溃重启或 DDS 重连。
- **检查命令：**
  - `grep -RInE "owner_id|lease|sequence|heartbeat|authority" --exclude-dir=.git src/offboard_cpp src/vision_to_dds`
  - `grep -RInE "offboard/cmd|offboard/takeoff_land" src/offboard_cpp/src src/offboard_cpp/launch`
- **实际结果：** 未找到 owner/lease 协议实现；找到至少两个内部命令发布者。
- **预期结果：** 所有 mission 命令必须经唯一 arbiter，以 owner ID、单调序号、租约和会话 epoch 验证；owner 丢失/切换必须清空旧命令并安全降级。
- **建议修复：** 引入 `control_authority_node` 或等效 arbiter，定义原子 command envelope；`offboard_node` 只接受 arbiter 输出，并拒绝非当前租约、重复、乱序和过期消息。
- **验收标准：**
  - 两个 owner 同时请求时最多一个获租约；
  - owner 超时在限定时间内撤销控制并清空 setpoint；
  - 旧 owner 重连、sequence 回退、lease 过期、命令/模式不同步均 fail-closed；
  - arbiter 重启后默认无 owner，不自动恢复先前控制状态。
- **依赖项：** BBF-SAFE-001；内部命令接口设计。
- **预计工作量：XL**
- **是否阻塞 production：是**

### BBF-SAFE-003

- **级别：P0**
- **分类：启动、重启与 DDS 重连安全态**
- **归属：受管依赖 `offboard_cpp`**
- **证据：**
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:33-47`：FSM 构造后直接处于 `POSITION`，没有 `INIT/WAIT_FOR_FEEDBACK/FAULT_LATCHED`。
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:50-89`：首次 timer tick 即读取反馈缓存，并在 odometry 无效时请求 ALTCTL。
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:326-340`：每个 tick 无条件发布 trajectory 和 OffboardControlMode。
  - `src/offboard_cpp/src/node.cpp:86-91`：启动后 20 ms 定时执行 FSM。
- **现象：** 节点启动或重启没有等待 RC、vehicle status、odometry、battery 和 graph authority 全部建立；会立刻发送 PX4 输入和可能的模式命令。
- **影响：** DDS/Agent 或节点重启后可能用默认/陈旧缓存发送 setpoint，或在飞行中主动切换模式，无法证明重加入是安全的。
- **触发条件：** Offboard 节点启动、进程重启、ROS time 跳变、DDS session 重建。
- **检查命令：** `nl -ba src/offboard_cpp/src/lib/CtrlFSM.cpp | sed -n '33,102p'`
- **实际结果：** 初始状态为 `POSITION`，无安全初始化态；输出发布不受 authority/feedback-ready 门控制。
- **预期结果：** 启动和重连均进入无控制输出的锁存初始化态，只有完整、连续、新鲜且相互一致的反馈与控制权前置条件通过后才能进入 active。
- **建议修复：** 增加显式 `BOOT/WAIT_INPUTS/STANDBY/ACTIVE/FAULT_LATCHED`；记录每个输入首帧与 epoch；对 DDS/clock 重置执行 lease 失效和人工重新授权。
- **验收标准：**
  - 缺任一必需反馈时无 `/fmu/in/*` 控制输出；
  - 节点、Agent、PX4 任一重启后不自动 arm、切模式或恢复旧 setpoint；
  - 连续健康窗口和显式重新授权后才能激活；
  - 覆盖节点重启、Agent 重启、PX4 boot-time 回退和 ROS clock jump 的测试。
- **依赖项：** BBF-SAFE-001、002、004。
- **预计工作量：L**
- **是否阻塞 production：是**

### BBF-SAFE-004

- **级别：P0**
- **分类：VehicleCommand ACK / vehicle status freshness**
- **归属：受管依赖 `offboard_cpp`**
- **证据：**
  - `src/offboard_cpp/src/node.cpp:34-35,37-84`：创建 VehicleCommand publisher，但订阅列表没有 VehicleCommandAck。
  - `src/offboard_cpp/src/lib/input.cpp:279-287`：VehicleStatus 只覆盖缓存，无 receive timestamp/首帧标志。
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:405-417`：命令发布后没有 command/target/result 关联。
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:427-478,614-681`：以缓存的 arming/nav state 推断成功，超时后仅返回 false；未处理 DENIED、FAILED、TEMPORARILY_REJECTED。
- **现象：** arm、land、进入/退出模式均没有 ACK pending 状态；VehicleStatus 也没有 freshness，因此旧状态可能被当作当前命令结果。
- **影响：** PX4 拒绝、未收到或延迟处理命令时，ROS 侧无法准确区分成功、拒绝和超时，状态迁移可能基于陈旧反馈。
- **触发条件：** preflight 拒绝、RC/参数限制、链路丢包、PX4 忙、旧 VehicleStatus 缓存。
- **检查命令：** `grep -RInE "VehicleCommandAck|vehicle_command_ack" --exclude-dir=.git src/offboard_cpp`
- **实际结果：** 无匹配；源码仅使用 VehicleCommand 和 VehicleStatus。
- **预期结果：** 每个安全相关命令应建立可关联的 pending 状态，只有 ACCEPTED 和随后新鲜状态确认后迁移，其余 result/超时均 fail-closed。
- **建议修复：** 订阅精确版本的 ACK topic；实现 command-result 分类、超时、有限重试和 correlation；为 VehicleStatus 增加首帧、receive-time、PX4 timestamp/epoch 校验。
- **验收标准：**
  - 仅 `ACCEPTED` 且新鲜状态满足目标时迁移；
  - `DENIED`、`FAILED`、`UNSUPPORTED`、`TEMPORARILY_REJECTED` 与 ACK 超时均保持或进入安全态；
  - 旧 ACK、错误 command/target/source 和 PX4 重启前 ACK 被拒绝；
  - 单元测试与 PX4 SITL publisher 故障注入覆盖所有结果码。
- **依赖项：** 精确 `px4_msgs`/PX4 v1.16.2 ACK topic 契约；BBF-SAFE-003。
- **预计工作量：L**
- **是否阻塞 production：是**

### BBF-SAFE-005

- **级别：P0**
- **分类：RC interlock / kill switch**
- **归属：受管依赖 `offboard_cpp` + 待建 PX4 firmware profile**
- **证据：**
  - `src/offboard_cpp/src/lib/input.cpp:23-35,63-125`：RC 首帧、signal_lost、channel_count、finite/range 和 freshness 已实现。
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:131-170`：自动起飞只有“收到新鲜 RC 时”才验证开关和摇杆；没有 RC 时跳过该安全门。
  - `src/offboard_cpp/CMakeLists.txt:33-35` 与 `src/offboard_cpp/src/lib/input.cpp:143-158`：所有构建无条件启用 `TEXT_RC`，运行时参数可覆盖物理 mode/gear。
  - `docs/evidence/OFFBOARD_PX4_MSGS_COMPAT_20260724.md:186-192`：历史只读硬件验收中 `/fmu/out/rc_channels` 缺失。
  - 源码关键字扫描未找到独立 kill/emergency stop 路径。
- **现象：** RC parser 本身已 fail-closed，但系统级 interlock 可被“无 RC 时跳过”和生产构建中的 mock switch 破坏；没有独立、锁存、最高优先级 kill 路径。历史参数 JSON 中有 `RC_MAP_KILL_SW` 键，但该快照不是当前配置，不能作为实现或验收证据。
- **影响：** 内部起飞命令可能在 RC safety input 缺失时继续走向 Offboard/arm；参数写入可替代物理模式开关；紧急情况下 ROS 控制链没有确定的立即停止机制。
- **触发条件：** custom firmware 尚未导出 rc_channels、RC/DDS 丢失、误用 mock 参数、需要紧急停止。
- **检查命令：**
  - `grep -RInE "TEXT_RC|mock_rc|kill|emergency" src/offboard_cpp/CMakeLists.txt src/offboard_cpp/src src/offboard_cpp/include`
  - `grep -n "/fmu/out/rc_channels" docs/evidence/OFFBOARD_PX4_MSGS_COMPAT_20260724.md`
- **实际结果：** 找到无条件 mock 编译和 RC 可选式起飞校验；未找到 kill 实现；历史硬件图缺少 rc_channels。
- **预期结果：** production 中 RC interlock 是硬前置条件，mock 完全不可编译/不可配置；kill 独立于 mission owner 且一旦触发保持锁存安全态。
- **建议修复：** production target 移除 `TEXT_RC`；RC 缺失/失效一律禁止 arm/Offboard；实现经明确契约验证的 kill input、去抖、边沿和人工复位；先完成仅构建不刷写的 PX4 DDS firmware profile。
- **验收标准：**
  - production 二进制不含 `mock_rc_*` 参数或 mock publisher；
  - 无首帧、signal_lost、stale、越界、NaN/Inf、RC topic 缺失均拒绝 arm/Offboard；
  - kill 抖动、持续触发、释放、重启后均符合锁存策略；
  - SITL 与拆桨台架证明 kill/RC loss 的限定响应时间；
  - 验收输入来自 PX4 publisher，不是 mock publisher。
- **依赖项：** PX4 DDS firmware profile；当前参数快照；拆桨台架计划。
- **预计工作量：L**
- **是否阻塞 production：是**

### BBF-SAFE-006

- **级别：P0**
- **分类：未初始化值 / NaN/Inf / 输入有效性**
- **归属：受管依赖 `offboard_cpp`**
- **证据：**
  - `src/offboard_cpp/include/lib/input.hpp:79-96`：`p/v/w/pos_jump` 没有成员初始化。
  - `src/offboard_cpp/src/lib/input.cpp:218-245`：构造时未初始化这些字段；feed 先把 `rcv_stamp` 设为 now，再用 `rcv_stamp == 0` 判断首帧，因此首帧仍对未初始化 `p` 做差。
  - `src/offboard_cpp/include/lib/input.hpp:159-175`：`Takeoff_Land_Data_t::landed` 未初始化。
  - `src/offboard_cpp/src/lib/input.cpp:296-319`：外部 trajectory/mode 直接复制，无 finite、范围或互斥模式校验。
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:351-376`：odom/command/battery freshness 未检查 has-received、负 age 或 clock reset。
- **现象：** 控制条件读取未初始化状态；首次 odometry 的 jump 检查逻辑恒不能进入首帧分支；外部 setpoint 可把 NaN/Inf 或不一致 mode 送入控制链。
- **影响：** 未定义行为可能随机拒绝或接受 odometry/landed 状态；异常数值可能形成危险 setpoint，或在重启/clock jump 后误判新鲜。
- **触发条件：** 首次 timer tick、首帧 odometry、首帧 land detected 之前、恶意/损坏的上层命令、时间回退。
- **检查命令：**
  - `nl -ba src/offboard_cpp/src/lib/input.cpp | sed -n '216,353p'`
  - `nl -ba src/offboard_cpp/include/lib/input.hpp | sed -n '79,175p'`
- **实际结果：** 发现未初始化成员和错误首帧判断；只有 RC 输入具备完整的 has-received/finite/range/非负 age 组合校验。
- **预期结果：** 所有控制相关缓存显式初始化，并采用统一 envelope 校验首帧、freshness、clock epoch、finite、frame、范围和字段组合。
- **建议修复：** 值初始化全部成员；先判断 `recv_new_msg` 再比较；验证 odometry quaternion/position/velocity 与 trajectory/mode；无效输入清空缓存并进入锁存安全态。
- **验收标准：**
  - sanitizer/UBSan 下首帧和无首帧路径无未初始化读取；
  - NaN/Inf、非单位四元数、超范围跳变、负 age、clock reset 均被拒绝；
  - setpoint 与 control mode 的有效字段组合有表驱动测试；
  - 无有效 odometry/land status 时不可 arm、takeoff 或宣告 landed。
- **依赖项：** 统一 freshness/epoch 组件；BBF-SAFE-003。
- **预计工作量：M**
- **是否阻塞 production：是**

### BBF-SAFE-007

- **级别：P0**
- **分类：故障降级 / 低电量 / 着陆恢复**
- **归属：受管依赖 `offboard_cpp`**
- **证据：**
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:207-224`：OFFBOARD 的 RC/odom loss 返回 POSITION 或 AUTO_HOVER，但不验证目标模式 ACK/新鲜状态。
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:264-280`：AUTO_LAND 中 RC/odom loss 会取消着陆并退出 Offboard。
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:285-337`：低电量只在 battery 被认为“已收到”时处理；陈旧/缺失数据无故障动作。
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:374-376`：battery freshness 只有 age 比较，构造时 stamp=now，且无首帧标志。
- **现象：** 各输入丢失的策略不统一；着陆期间丢 RC/odom 会取消着陆；电池遥测缺失或陈旧不会进入低电量安全策略。DDS loss 和 vehicle-status stale 没有独立状态。
- **影响：** 最需要安全降级时可能撤销降落、切换到未经确认的模式，或在失去电池健康信息后继续执行任务。
- **触发条件：** AUTO_LAND 时 RC/odom loss、DDS/Agent 断线、battery topic 停止、VehicleStatus stale。
- **检查命令：** `nl -ba src/offboard_cpp/src/lib/CtrlFSM.cpp | sed -n '175,377p'`
- **实际结果：** FSM 中存在分散且不一致的恢复分支，无统一 fault priority、锁存和恢复条件。
- **预期结果：** 有显式故障优先级表；RC、DDS、odom、status、battery loss 均映射到经安全分析批准的动作，恢复必须重新授权而非自动回到 active。
- **建议修复：** 把故障评估与任务状态解耦；建立 fault lattice/priority、锁存、超时和恢复门；对“保持 PX4 failsafe”“请求 land”“停止 Offboard 输出”等动作给出前置条件和 ACK。
- **验收标准：**
  - 每类单故障和组合故障有确定、可测试的状态迁移；
  - AUTO_LAND 中传感器丢失不会未经批准地取消安全动作；
  - battery/status 从未收到、stale、invalid 均 fail-closed；
  - 故障恢复需要新鲜输入、健康窗口和显式 operator re-arm；
  - SITL 故障注入与拆桨台架结果符合同一状态表。
- **依赖项：** BBF-SAFE-003、004、005；PX4 failsafe 参数基线。
- **预计工作量：XL**
- **是否阻塞 production：是**

### BBF-SAFE-008

- **级别：P1**
- **分类：安全参数边界与配置 profile**
- **归属：受管依赖 `offboard_cpp`**
- **证据：**
  - `src/offboard_cpp/config/ctrl_param.yaml:3-29`：超时、自动 arm、低电压、odom jump 和 RC 索引集中在单一通用 YAML。
  - `src/offboard_cpp/config/ctrl_param.yaml:13-16`：默认启用自动起降和自动 arm。
  - `src/offboard_cpp/src/lib/param.cpp:28-46`：读取参数后没有范围、有限性或跨参数约束检查。
  - `src/offboard_cpp/src/lib/param.cpp:64-88`：动态参数回调默认成功，未知参数也成功返回。
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:328-335,460-465`：`0.15`、`warning >= 2`、3 秒等安全阈值散落在源码。
- **现象：** development/SITL/bench/production 共用默认自动 arm 配置；安全参数没有 schema、单位、适用机型、合法范围和启动时 fail-closed 验证。
- **影响：** 错误负超时、过大起飞高度、错误电池规格或 RC 映射可改变安全行为，且节点仍正常启动。
- **触发条件：** YAML 编辑、参数覆盖、机型/电池变化、动态参数调用。
- **检查命令：** `nl -ba src/offboard_cpp/src/lib/param.cpp; nl -ba src/offboard_cpp/config/ctrl_param.yaml`
- **实际结果：** 参数可读取但无语义校验；默认 `enable_arm: true`。
- **预期结果：** production profile 默认 disarmed；所有安全参数有类型、范围、单位、来源、机型约束和不可动态修改策略。
- **建议修复：** 定义 profile-specific schema；启动时全量验证并输出配置 hash；生产禁用危险动态参数；将所有安全阈值集中管理并关联安全依据。
- **验收标准：**
  - 非 finite、负 timeout、无效 RC index、非法高度/速度/电池阈值使启动失败；
  - production 默认 `enable_arm=false`，需显式受控授权；
  - 未知参数和飞行中修改安全参数被拒绝；
  - profile/config hash 进入每次 SITL、台架和实机证据。
- **依赖项：** production profile 定义；机型、电池和 PX4 failsafe 参数基线。
- **预计工作量：M**
- **是否阻塞 production：是**

### BBF-SAFE-009

- **级别：P1**
- **分类：launch/profile 隔离**
- **归属：根仓库运维 + 受管依赖 `offboard_cpp`**
- **证据：**
  - `src/offboard_cpp/launch/offboard_control.launch.py:38-53`：直接启动真实控制 writer，默认 `use_sim_time=false`。
  - `src/offboard_cpp/launch/animal_testing.launch.py:20-29,43-64`：默认 `use_sim_time=true`，但 `auto_start_animal_testing=true`，三秒后启动 mission owner。
  - `src/offboard_cpp/launch/offboard_demo.launch.py:37-50`：无论 demo 是否启用都启动控制 writer。
  - `docs/CONTROL_AUTHORITY_MATRIX.md:94-124`：定义了 offline/sensor/read-only/SITL/bench/production 规则，但当前是文档规则。
- **现象：** profile 名称和允许节点矩阵没有被可执行 launcher 强制；历史 launch 可绕过 production 禁用声明。
- **影响：** 操作者可能把示例/SITL launch 用于硬件环境，意外创建控制 publisher 或 mission owner。
- **触发条件：** 直接运行包内 launch、错误 `use_sim_time`、launch 被上层 include。
- **检查命令：** `grep -RInE "Node\\(|auto_start|use_sim_time|offboard_node" src/offboard_cpp/launch`
- **实际结果：** launch 直接创建 writer；无 `profile`、hardware-control gate、graph guard 或 explicit acknowledgment。
- **预期结果：** 唯一受支持入口按 profile allowlist 启动节点；offline/read-only 永不创建 `/fmu/in/*` publisher；production 在安全门未完成前不可选择。
- **建议修复：** 将现有 launch 标为 test-only 并由根仓库统一 profile launcher 封装；对 profile、sim time、transport identity 和 authority 做启动时断言。
- **验收标准：**
  - 静态测试证明 read-only/profile 不包含任何控制 writer；
  - 示例 launch 无法在 production profile 中加载；
  - 未显式选择 profile 时默认 offline；
  - production gate 未满足时 launch 在创建节点前失败。
- **依赖项：** BBF-SAFE-001、002、008。
- **预计工作量：L**
- **是否阻塞 production：是**

### BBF-SAFE-010

- **级别：P1**
- **分类：安全测试 / 故障注入**
- **归属：受管依赖 `offboard_cpp` + 根仓库 CI**
- **证据：**
  - `src/offboard_cpp/CMakeLists.txt:69-89`：只注册 `test_rc_input` 与 `test_topic_contract`。
  - `src/offboard_cpp/test/test_rc_input.cpp:46-135`：覆盖 RC 解析和 freshness。
  - `src/offboard_cpp/test/test_topic_contract.cpp:16-35`：只检查 VehicleStatus topic 字面契约。
  - 没有 FSM、ACK、owner、graph、重启、battery、odometry、DDS loss 或组合故障测试。
- **现象：** 当前 9 个 gtest case 的历史通过证据只证明 RC parser 和一个 topic contract；关键控制状态机没有自动化安全测试。
- **影响：** 控制权竞争、错误状态迁移、故障恢复和危险默认值可在无回归信号的情况下进入主线。
- **触发条件：** FSM、参数、消息或 launch 的任意变更。
- **检查命令:** `grep -RInE "TEST\\(|TEST_F\\(|ament_add_gtest|add_test" src/offboard_cpp/test src/offboard_cpp/CMakeLists.txt`
- **实际结果：** 2 个测试可执行文件、9 个 case；均不覆盖上述安全闭环。
- **预期结果：** 关键状态迁移具有确定性单元测试，并有真实 PX4 publisher 的 SITL 故障注入、launch graph 与台架分层验收。
- **建议修复：** 抽离可注入 clock/transport 的纯 FSM；建立状态转移表驱动测试；增加 RC/DDS/odom/status/battery loss、ACK result、重启、重复 owner 和 NaN/Inf 测试。
- **验收标准：**
  - 每个 production 状态和故障边均有正/负测试；
  - 覆盖所有 VehicleCommand ACK result 与 timeout；
  - SITL 使用 PX4 publisher 而非 mock publisher；
  - 任一安全测试失败可阻止合并和 release。
- **依赖项：** BBF-SAFE-002 至 009 的接口设计；CI required checks。
- **预计工作量：XL**
- **是否阻塞 production：是**

### BBF-SAFE-011

- **级别：P1**
- **分类：拆桨台架 / production 验收**
- **归属：根仓库运维与安全治理**
- **证据：**
  - `docs/CONTROL_AUTHORITY_MATRIX.md:126-166` 给出静态/runtime 建议，但没有可执行的拆桨台架步骤、观察点、停止条件或签字记录。
  - `docs/evidence/OFFBOARD_PX4_MSGS_COMPAT_20260724.md:154-206` 仅记录历史 output-only transport 验证，并明确未启动 Offboard、未 arm、未发送控制输入。
  - `docs/evidence/` 当前只有兼容性记录与历史参数 JSON，没有拆桨台架验收记录。
- **现象：** 没有从 SITL 到拆桨台架的安全验收方案；现有硬件证据只证明历史 DDS transport/输出 topic，不证明控制闭环、failsafe 或停止能力。
- **影响：** 即使代码修复，也没有可追溯证据证明真实 PX4/RC/DDS/电机输出链在故障下按预期停止。
- **触发条件：** 尝试从 SITL 直接进入有限实机控制测试。
- **检查命令：**
  - `find docs/evidence -maxdepth 2 -type f -print`
  - `grep -RInE "拆桨|prop.*off|bench|故障注入|kill" README.md docs Scripts/README.md`
- **实际结果：** 未发现包含前置条件、逐步动作、遥测证据、停止条件、回滚和批准人的完整台架验收包。
- **预期结果：** 有四级验收门：静态/单元、SITL、拆桨台架、有限实机；上一层完整通过才可进入下一层。
- **建议修复：** 编写并演练拆桨台架 runbook，明确物理安全、transport 只读预检、参数快照、故障注入、日志、回滚和双人确认。
- **验收标准：**
  - 台架前确认拆桨、区域隔离、物理 kill、供电限制和串口独占；
  - 逐项验证 duplicate writer、RC/DDS/odom/status/battery loss、ACK reject/timeout 和重启；
  - 每项保存根/依赖/PX4 SHA、配置 hash、命令、完整日志、结果和签字；
  - 任一项失败即禁止进入实机阶段并按 runbook 回滚。
- **依赖项：** BBF-SAFE-001 至 010；firmware artifact；当前 PX4 参数快照。
- **预计工作量：L**
- **是否阻塞 production：是**

### BBF-SAFE-012

- **级别：P2**
- **分类：安全可观测性与故障审计**
- **归属：受管依赖 `offboard_cpp` + 根仓库证据规范**
- **证据：**
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:76-337`：故障主要以自由文本日志和函数内 static 标志处理。
  - `src/offboard_cpp/src/lib/input.cpp:37-54`：RC 拒绝只有字符串 reason，无稳定错误码、状态 topic 或计数器。
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:285`：低电量状态名为 `WANRING`，缺乏正式 fault taxonomy。
- **现象：** 没有结构化 health/fault 输出、稳定错误码、进入/退出时间、故障来源、active owner/lease 或最后新鲜消息 age 指标。
- **影响：** SITL/台架无法机器判定安全验收，现场故障难以关联到输入丢失、命令拒绝或控制权变化。
- **触发条件：** 任一 fail-closed、降级、恢复或重复 owner 事件。
- **检查命令：** `grep -RInE "diagnostic|DiagnosticStatus|fault_code|error_code|health" src/offboard_cpp/src src/offboard_cpp/include`
- **实际结果：** 未找到结构化诊断接口。
- **预期结果：** 发布只读、结构化且稳定版本的 safety status，日志含事件 ID、epoch、owner、状态迁移原因和输入 age。
- **建议修复：** 定义 safety event taxonomy 与 diagnostic message；测试按错误码而非日志字符串验收；证据记录完整事件序列。
- **验收标准：**
  - 每个 P0/P1 故障路径产生稳定唯一事件码；
  - 状态迁移包含 from/to/reason/time/epoch；
  - 诊断不得成为控制输入或绕过 arbiter；
  - SITL/台架脚本能自动断言预期事件与最大响应时间。
- **依赖项：** 统一 FSM/fault model；证据模板。
- **预计工作量：M**
- **是否阻塞 production：否；但应在台架验收前完成**

## 4. Production 阻塞项

production 当前必须保持禁用。独立安全审查识别出以下阻塞链：

1. `BBF-SAFE-001`：无 writer graph guard。
2. `BBF-SAFE-002`：无 owner/lease/arbiter。
3. `BBF-SAFE-003`：启动/重启不是无输出安全态。
4. `BBF-SAFE-004`：无 VehicleCommand ACK，VehicleStatus 无 freshness。
5. `BBF-SAFE-005`：RC interlock 可跳过、mock 编入生产、无 kill。
6. `BBF-SAFE-006`：未初始化状态与控制输入有效性不完整。
7. `BBF-SAFE-007`：故障降级、着陆和电池丢失策略不闭合。
8. `BBF-SAFE-008`：安全参数无 profile/schema/range gate。
9. `BBF-SAFE-009`：launch 未强制 profile 隔离。
10. `BBF-SAFE-010`：无关键 FSM/故障注入质量门。
11. `BBF-SAFE-011`：无拆桨台架验收与证据。

## 5. 最短安全关键路径

1. 先修复未初始化读取并建立统一 input validity/freshness/epoch 基础件。
2. 将 FSM 改为默认无输出的初始化/锁存故障态；接入 VehicleCommand ACK 和新鲜 VehicleStatus。
3. 实现唯一 arbiter、owner/lease/sequence 与持续 graph guard。
4. 移除 production mock RC，固定 RC/kill 硬前置与 PX4 DDS firmware profile。
5. 用表驱动单元测试和 PX4 SITL publisher 覆盖全部故障边。
6. 建立 production profile gate，再执行拆桨台架验收；全部通过前不得进入实机控制。

## 6. 验证限制

- 本轮没有启动 ROS graph，因此“运行中确有几个 publisher”和实际 graph guard 行为均为**未验证**；结论来自可启动路径和源码缺少排他机制。
- 没有启动 PX4 SITL，因此 ACK result、mode/arm 拒绝、DDS loss 与 failsafe 运行结果均为**未验证**。
- 没有访问硬件或当前飞控参数，因此 RC kill 映射、PX4 failsafe 参数和当前 firmware topic profile 均为**未验证**。
- 没有运行构建或测试；历史 `9 gtest cases, 0 failures` 仅作为 2026-07-25 证据引用，不冒充本轮结果。
- `../communication` 在本地不存在；无法审查该 moving dependency 是否有额外控制 writer。它不改变当前 managed source 已缺少 runtime authority guard 的结论，但完整 workspace 恢复后必须补扫。

## 7. 本报告实际使用的检查命令

```bash
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git rev-parse HEAD
git status --short
git -C src/offboard_cpp rev-parse HEAD
git -C src/offboard_cpp status --short
git -C src/offboard_cpp remote -v
find docs/adr docs/evidence src/offboard_cpp/test -type f
grep -RInE 'create_publisher|/fmu/in/|offboard/cmd|VehicleCommand|TrajectorySetpoint' ...
grep -RInE 'owner_id|lease|sequence|heartbeat|authority|VehicleCommandAck|kill|emergency' ...
grep -RInE 'TEST\(|TEST_F\(|ament_add_gtest|add_test' src/offboard_cpp/test src/offboard_cpp/CMakeLists.txt
nl -ba <上述源码、launch、配置与证据文件> | sed -n '<审查范围>p'
```

## 8. 数量统计

| P0 | P1 | P2 | P3 | 合计 |
|---:|---:|---:|---:|---:|
| 7 | 4 | 1 | 0 | 12 |
