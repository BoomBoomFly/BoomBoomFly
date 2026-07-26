# BoomBoomFly 下一阶段工程路线图

> 基线：`agent/follow-latest-offboard@3ce28094e14ed720987c5fc6d1172e377f09b1cc`
> 规划日期：2026-07-26
> 总原则：production 保持禁用；先建立可复现基线和安全控制闭环，再逐级进入 SITL、拆桨台架与有限实机验证。

## 关键路径

```text
阶段 0 可复现基线
  -> 阶段 1 PX4 DDS firmware profile（只构建，不刷写）
  -> 阶段 2 Offboard 安全闭环 + SITL 故障注入
  -> 阶段 3 感知/状态估计闭环
  -> 阶段 4 拆桨台架
  -> 有限实机控制试验（另行授权）
```

阶段 0 的 DDS-only 包边界、PX4 工具链锁定和证据模板是所有后续阶段的共同前置。阶段 1 与阶段 2 的纯接口设计/单元测试可部分并行，但阶段 2 的 PX4 SITL 验收依赖阶段 1。阶段 3 不得早于控制权、时间域和 profile 门禁冻结；阶段 4 必须等待所有 P0 关闭。

## 阶段 0：基线冻结与可复现性

### 目标

把“15 个 Git 对象已锁定”提升为“从空白环境可恢复当前有效文件树、工具链、构建入口和证据链”。

### 前置条件

- 保留四个既有 dirty checkout，不执行 reset/clean。
- 确认哪些 dirty 差异属于必要适配，哪些只是文件 mode 或历史删除。
- production 继续禁用。

### 任务

1. 建立根级 DDS-only 包 allowlist；用 `COLCON_IGNORE`、`colcon.meta/defaults` 或受控脚本阻止 MAVROS、旧 bringup、mock、serial 和实验包被默认发现。
2. 为 `librealsense`、`navigation_msgs`、`realsense-ros`、`vision_opencv` 生成经维护者确认的 patch/派生仓库/内容散列和用途说明。
3. 修复 `src/serial_driver_ros` 无 `.gitmodules` 映射的历史 gitlink。
4. 锁定 PX4-Autopilot `v1.16.2@54f0455f...`、递归 submodule、OS/架构、编译器、CMake、Ninja、Python 与 ROS 依赖。
5. 为 moving `../communication` 定义实验 receipt：origin、HEAD、dirty hash、时间、用途和批准人；缺失时 fail-closed。
6. 建立统一 evidence 模板，字段至少含根/依赖 SHA、命令、环境、起止时间、原始退出码、artifact hash 和未验证项。
7. 建立最小 CI：manifest 审计、DDS-only 包发现、语法、核心三包隔离 build/test、lint、secret scan。

### 输出物

- DDS-only 包 allowlist 与受控构建入口。
- `workspace.lock.repos` 配套环境/toolchain lock。
- 四个 dirty checkout 的可重建 receipt。
- PX4 source/submodule/toolchain 清单。
- evidence 模板与首个 CI workflow。

### 验收标准

- 新目录 dry-run 与 restore 两次结果一致；第二次运行幂等。
- 默认 `colcon list` 不发现禁止包，或权威入口在发现时非零退出。
- 15 个 lock checkout、四个差异 receipt 和 moving dependency receipt 均可机器校验。
- `git submodule status --recursive` 不再因根 gitlink 元数据退出 128。
- CI 失败会阻止合并；依赖 ref、工具镜像或工具链均非 moving latest。

### 风险

- 对 dirty checkout 的错误归类可能丢失 Jetson/ROS Foxy 必要适配。
- 一次性构建全工作区会把历史第三方问题混入主线。

### 回滚策略

- 不触碰现有 checkout；先在隔离工作区重放 patch。
- allowlist 以新增受控入口落地，保留原脚本供对照但标记非权威。
- CI 先作为可观察检查，稳定后再设置 required。

### 阻塞关系

阻塞阶段 1–4。PX4 source/toolchain 锁定直接阻塞阶段 1；包边界与 CI 直接阻塞阶段 2。

## 阶段 1：PX4 DDS firmware profile

### 目标

基于精确 PX4 v1.16.2 生成只增加 `/fmu/out/rc_channels` 的可追溯 DDS firmware profile，并完成静态生成、SITL 与 FMUv3 构建；本阶段不刷写。

### 前置条件

- 阶段 0 的 PX4 source、递归 submodule 和交叉工具链已锁。
- `px4_msgs@392e831c...` 的 `RcChannels.msg` 与 PX4 源码消息定义逐字段一致。
- evidence 模板和隔离构建目录已建立。

### 任务

1. 以最小 patch 修改 `dds_topics.yaml` publications，仅加入 `rc_channels`；baseline 不加入精降 topic。
2. 静态生成并检查 DataWriter、topic 名称、消息版本、type hash 与 QoS。
3. 在隔离 PX4 SITL + UDP Agent 中检查 `/fmu/out/rc_channels` 唯一 PX4 publisher 和真实 payload，禁止 mock 作为验收来源。
4. 回归 `vehicle_status_v1`、battery、odometry、landed 与 command ACK。
5. 构建 `px4_fmu-v3_default`，保存 flash/RAM 余量、完整日志和 `.px4` SHA-256。
6. 形成 transport profile schema：ROS domain、namespace、client key、Agent 参数、system/component identity。

### 输出物

- PX4 source patch、submodule 清单、工具链清单。
- 静态生成物检查记录。
- SITL DDS 原始 transcript/rosbag 或等价证据。
- FMUv3 构建日志、资源余量和 artifact SHA-256。
- transport profile 与回滚表；不包含任何刷写结果。

### 验收标准

- `/fmu/out/rc_channels` type/QoS/topic 与锁定 `px4_msgs` 一致，且恰有一个 PX4 publisher。
- SITL payload 来自 PX4 publisher，包含有效 `channel_count`、`signal_lost` 和 normalized channels。
- 所有 baseline 输出 topic 无回归。
- 同一 source/submodule/toolchain 可重复得到同 SHA 或解释确定性差异。
- FMUv3 构建成功且资源余量满足预先批准门槛。

### 风险

- FMUv3 资源紧张；消息生成改动可能扩大 flash/RAM。
- PX4/px4_msgs 消息版本不一致会产生静默接口偏差。

### 回滚策略

- patch 独立保存且可反向应用；保留未修改官方 v1.16.2 build 对照。
- 不刷写，硬件状态不改变。

### 阻塞关系

依赖阶段 0；阻塞阶段 2 的 RC/SITL 闭环与阶段 4 台架。

## 阶段 2：Offboard 安全闭环

### 目标

实现可运行时强制的单一控制权、事务化命令、统一 freshness、明确预热/故障状态和故障注入测试。

### 前置条件

- DDS-only build/profile 可执行强制。
- 阶段 1 的 SITL firmware profile 可用。
- 安全需求—测试映射评审通过。

### 任务

1. production target 移除 `TEXT_RC`；RC 从未收到、丢失、陈旧或开关无效时禁止 arm/Offboard。
2. 引入 `control_authority_node` 或等效 arbiter，包含 owner、lease、sequence、heartbeat、原子 mode+setpoint envelope。
3. 实现启动前和持续 graph guard：控制 writer、视觉 writer、mission owner、Agent 均满足 profile 基数。
4. 订阅 `VehicleCommandAck`，实现 pending、result 分类、超时、有限重试及 fresh VehicleStatus 二次确认。
5. 建立 `BOOT -> WAIT_INPUTS -> STANDBY -> PRESTREAM -> MODE_PENDING -> ACTIVE -> FAULT_LATCHED`。
6. 所有反馈使用统一首帧、receive-time、PX4 epoch、finite/range/freshness wrapper；修复未初始化成员。
7. 定义 RC、DDS、odometry、vehicle status、battery、owner loss 的优先级、降级动作、锁存与人工恢复。
8. 建立故障注入：ACK 各 result、重复 writer/owner、RC/DDS/odom/status/battery loss、PX4/Agent 重启、时钟回退、NaN/Inf。
9. 增加结构化 safety diagnostics 和稳定错误码。

### 输出物

- 控制权协议/ADR、profile schema、graph guard。
- 安全 FSM 与 VehicleCommand 事务实现。
- 单元测试、组件测试和 SITL 故障注入测试集。
- 控制权唯一性和 fault event 证据。

### 验收标准

- 非当前 lease、乱序/重复/过期命令均不得到达 `/fmu/in/*`。
- 所有反馈 ready 前控制消息发布计数为 0。
- 连续不少于 1 秒且不少于 20 个有效 setpoint 后才请求 Offboard。
- ACK 为 ACCEPTED 且 fresh 状态一致后才迁移；拒绝和超时进入锁存安全态。
- 任一关键输入 stale、DDS loss 或 owner loss 后，在规定 deadline 内停止/降级且必须显式重新授权。
- SITL 中禁止组件、重复 publisher 和 mock 混入均 fail-closed。

### 风险

- “停止 Offboard 输出”与“请求 PX4 land/position”在不同故障下可能有相反风险，需要按飞行阶段分析。
- 自动恢复可能在重连后重新取得控制权，默认应禁用。

### 回滚策略

- 新安全 FSM 与旧实现分支隔离；production profile 只允许新入口。
- 任何测试失败立即回到 offline/SITL；不进入台架。

### 阻塞关系

依赖阶段 0/1；阻塞阶段 3 的视觉注入和阶段 4 的台架控制。

## 阶段 3：感知和状态估计

### 目标

冻结外部视觉坐标、时间、TF、设备身份与 EKF2 前置条件，形成普通视觉里程计和精降两个独立、可降级 profile。

### 前置条件

- 阶段 2 的 authority/profile/freshness 框架完成。
- D435/T265 角色由维护者确认；设备 serial/VID:PID/udev 策略确定。
- 当前 PX4 参数可通过另行授权的只读通道重新取证。

### 任务

1. 形成 ENU/NED、FLU/FRD 数学规范和金样测试，校验位置、姿态、速度、covariance。
2. 定义 camera/TF/ROS/PX4 时间域、sample/publish timestamp、最大延迟、reset counter 和时钟跳变处理。
3. 统一 frame_id/child_frame_id、TF 树和静态外参；启动前检查上游 frame。
4. 用稳定 serial/udev 绑定 D435/T265；T265 缺失/断线时禁止视觉注入并输出健康状态。
5. 校验 EKF2 外部视觉前置参数、innovation/estimator status，不允许从历史快照推断当前配置。
6. 把 precision landing 做成独立 firmware/launch/profile，增加目标 freshness、validity、covariance 和置信度门。
7. 对 TF freeze、sensor reset、NaN/Inf、延迟、掉线和设备重枚举做故障注入。

### 输出物

- 坐标与时间 ADR、TF 图、设备 inventory schema。
- `vision-odometry` 与 `precision-landing` 两套 profile。
- 转换/时间/健康单元测试、SITL/EKF2 证据。
- D435/T265 缺失降级和回滚证据。

### 验收标准

- 金样向量覆盖轴向、90/180 度旋转、四元数归一化和 covariance 变换。
- stale/future/backward/frozen/reset/non-finite 输入不产生 PX4 视觉发布。
- T265 缺失或掉线时系统进入明确降级态，不沿用旧测量。
- EKF2 innovation、delay、reset 和 estimator health 达到预设门槛。
- 精降未显式启用时 publisher 不存在；启用时使用独立 firmware/profile。

### 风险

- 坐标变换错误可能直接使状态估计和控制发散。
- 历史硬件枚举与参数快照可能已过期。

### 回滚策略

- 默认关闭所有 PX4 视觉输入；先离线 bag、再 SITL。
- EKF2 参数变更不属于本轮路线实施授权；未来必须保存前后快照和恢复值。

### 阻塞关系

依赖阶段 2；视觉能力阻塞阶段 4 中带视觉的台架/实机，但不阻塞纯 telemetry 台架。

## 阶段 4：SITL、台架与实机验收

### 目标

按静态、单元、集成、SITL、拆桨台架、有限实机六级门逐级证明控制闭环、故障响应和回滚。

### 前置条件

- 所有 P0 关闭并经独立代码审查。
- P1 的 firmware、SITL、profile、CI、台架 runbook 已完成。
- 当前 firmware artifact、参数、transport/domain 和物理安全配置可追溯。

### 任务

1. SITL 正常场景：session、状态、RC、预热、ACK、起飞/悬停/降落。
2. SITL 故障场景：RC/DDS/odom/status/battery/owner loss、拒绝 ACK、时钟跳变、重启、双 writer。
3. 编写拆桨台架 runbook：区域隔离、执行器/桨叶状态、双人确认、观察员、急停、停止条件。
4. 先做 transport 只读取证，再做不 arm 的 command rejection/graph 门禁，再按审批逐门放行。
5. 保存刷写前 artifact hash、当前/目标参数快照、回滚 firmware/参数和恢复演练证据。
6. 仅当台架全部通过，另行审批最小包线、限高、限时的实机试验。

### 输出物

- SITL 正常/故障报告与原始日志。
- 拆桨台架批准单、逐项记录、故障注入和停止证据。
- firmware/参数/transport 回滚包。
- 有限实机试验风险评估与单独授权记录。

### 验收标准

- 每级失败都会阻止进入下一级。
- 控制 publisher/owner/Agent 数量符合矩阵；PX4 source 可证明。
- 所有 P0/P1 测试结果可由 CI 或证据包重放。
- 台架中每个故障都在 deadline 内进入预期安全态，并验证人工复位。
- 回滚在台架环境实际演练成功后才允许有限实机。

### 风险

- 真实执行器和飞行环境具有不可逆伤害风险。
- transport、firmware、参数与软件 profile 任一不一致都会使历史证据失效。

### 回滚策略

- 每级保持已验证的前一 profile 和 artifact。
- 任何异常立即停止当前级别；台架/实机不自动继续或自动恢复。

### 阻塞关系

依赖阶段 0–3；有限实机控制需要新的明确授权，不由本路线图自动授权。

## 时间窗口

### 未来 1 周

- 完成 DDS-only 包 allowlist 和权威隔离 build/test 入口。
- 固化四个 dirty checkout 的用途与可重建 receipt。
- 修复历史 gitlink；建立 evidence 模板。
- 锁定 PX4 source/submodule/toolchain 方案。
- 创建安全需求—测试映射；先写 ACK、RC 缺失、首帧/freshness、NaN/Inf 的失败测试。
- 修复 `vision_to_dds` 当前 lint 失败，建立 required CI 骨架。

### 未来 2～4 周

- 完成阶段 1 的 `rc_channels` 静态生成、SITL 与 FMUv3 build artifact。
- 实现 VehicleCommand ACK、统一 freshness、显式 PRESTREAM 和 production 移除 TEXT_RC。
- 实现 owner/lease 与 graph guard 的最小闭环。
- 建立 PX4 DDS SITL 正常/故障入口和 required checks。
- 冻结视觉坐标/时间 ADR 与单元测试。

### 未来 1～3 个月

- 完成完整 fault lattice、结构化诊断和安全参数 schema。
- 完成视觉状态估计 profile、EKF2 取证与 T265 缺失降级。
- 设计独立 precision-landing profile。
- 完成 SITL 全矩阵、拆桨台架 runbook、回滚演练。
- 所有门通过后，再提交有限实机试验审批。

## 暂缓事项

- 多机/swarm namespace、共享 Agent、多 client key。
- 精准降落，直到普通视觉里程计闭环稳定。
- RPLIDAR、USB Camera/VPU、YOLO 等非主线感知。
- 性能优化、架构泛化和 release packaging，除非直接服务安全证据。
- 任何 firmware 刷写、参数写入、arm、mode/setpoint 或实机控制。

## 不建议继续投入的历史路径

- MAVROS/MAVLink 作为 production fallback。
- `px4_bringup`、`vision_to_mavros`、旧 serial/MAVROS 一键 launch。
- `offboard_swarm_control.launch.py` 的现有多机路径。
- 以 `mock_rc_control.py` 或 mock PX4 publisher 作为 SITL/台架验收。
- 在当前混合 `src/` 上做“全包能编过”而不先建立 DDS-only allowlist。
- 继续扩充单一巨大 handoff 作为唯一状态数据库；应拆分机器可读基线、runbook 与证据索引。
