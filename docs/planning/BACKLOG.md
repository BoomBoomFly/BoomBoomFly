# BoomBoomFly P0/P1 执行 Backlog

> 文档状态：`PLANNED`
>
> 调度事实基线：Repository Cleanup Wave 2 起始
> `master@0a7f90dad0942843c989a9bed6333a88f9b31ca5`；执行分支
> `agent/repository-cleanup-wave2`。旧审计中的 branch/HEAD 只属于
> `HISTORICAL_EVIDENCE`。
>
> 来源：`docs/audits/2026-07-26/07_FINDINGS_REGISTER.md` 的 44 个统一发现。
> 本文件完整拆分其中 9 个 P0 与 15 个 P1，共 24 项；不创建或代表真实 GitHub
> Issue/Milestone。审计报告中的旧分支和旧 HEAD 仅是 `HISTORICAL_EVIDENCE`。
>
> 全局边界：production 为 `BLOCKED`；只允许 PX4 uXRCE-DDS，MAVROS 不是
> production fallback；所有 P0 关闭前不得进入拆桨台架；任何实机控制均需另行授权。
> T00、T01、T08 的脚本、schema、receipt、package allowlist 和 evidence 基础设施
> 由各自工作线拥有，本规划只记录依赖，不授权交叉修改。

## 状态与估算

- 允许状态：`IMPLEMENTED`、`PARTIALLY_IMPLEMENTED`、`STATICALLY_VERIFIED`、
  `UNIT_TESTED`、`SITL_VERIFIED`、`BENCH_VERIFIED`、`FLIGHT_VERIFIED`、
  `HISTORICAL_EVIDENCE`、`PLANNED`、`BLOCKED`、`UNVERIFIED`。
- 估算：S（不超过约 3 人日）、M（约 3–7 人日）、L（约 1–3 周）、
  XL（跨工作线、超过约 3 周）。估算不包含等待评审、硬件授权和采购时间。
- 关闭规则：任务状态只有满足
  [Definition of Done](DEFINITION_OF_DONE.md) 后才可从验证状态推进；文档完成不等于
  运行验证完成。

## P0 Backlog

### BBF-TASK-001 — 运行时控制 writer 唯一性

- **Task ID：** `BBF-TASK-001`
- **对应 Audit ID：** `BBF-AUD-001`
- **标题：** 为 PX4 控制输入建立启动前与持续 graph guard
- **优先级：** P0
- **模块：** 控制权 / ROS graph / production profile
- **目标：** 对单机根 namespace 的 trajectory、mode、VehicleCommand writer 实施
  唯一性和身份门禁；重复、消失或重连时 fail-closed。
- **允许修改范围：** 经评审的新 authority/guard 组件、批准的 profile launcher、
  graph 测试与只读诊断；接口冻结后对 `offboard_cpp` 的最小适配。
- **禁止修改范围：** 启用 swarm；把 MAVROS、demo、animal 或 mock 纳入 production；
  访问硬件、写参数、刷固件。
- **前置条件：** T01 的 DDS-only package/launch 边界可用；transport identity
  profile 接口冻结；控制权 ADR 评审通过。
- **依赖任务：** `BBF-TASK-010`、`BBF-TASK-018`
- **可并行任务：** `BBF-TASK-002` 的协议设计、`BBF-TASK-004` 的 ACK 单元设计
- **实施步骤：** 定义批准节点/端点基数；实现启动前检查；持续监听 graph epoch；
  冲突时撤销 authority 并锁存；输出稳定事件码。
- **必须测试：** 双 writer、writer 消失/重连、错误 namespace/domain/client key、
  禁止节点混入、graph discovery 短暂变化。
- **验收标准：** 三个 `/fmu/in/*` 控制端点各只有一个批准 writer；任何基数或
  identity 冲突都阻止 ACTIVE，恢复必须人工重新授权。
- **evidence：** graph 快照、事件时间线、测试命令/退出码、root/依赖 SHA 与配置 hash；
  格式服从 T08 权威 schema。
- **风险：** ROS graph discovery 非瞬时一致；一次性快照会造成假阴性。
- **估算：** L
- **建议负责人角色：** Control Maintainer；Safety Reviewer 独立验收
- **状态：** `PLANNED`

### BBF-TASK-002 — mission owner/lease 仲裁

- **Task ID：** `BBF-TASK-002`
- **对应 Audit ID：** `BBF-AUD-002`
- **标题：** 建立唯一 mission owner、lease、sequence 与原子命令 envelope
- **优先级：** P0
- **模块：** 控制权 / mission arbitration
- **目标：** 只有当前有效 lease 的原子 mode+setpoint 事务可进入 Offboard。
- **允许修改范围：** 新 arbiter/authority 接口与实现、消息/协议 schema、Offboard
  消费接口和纯软件测试。
- **禁止修改范围：** 直接使用 demo/animal 作为 production owner；启用多机；
  绕过 graph guard；硬件运行。
- **前置条件：** authority 协议 ADR 通过；与 `BBF-TASK-017` 共同冻结 envelope；
  T01 边界可用。
- **依赖任务：** `BBF-TASK-001`；与 `BBF-TASK-017` 共同冻结 envelope 是接口协作，
  `BBF-TASK-017` 消费本任务结果
- **可并行任务：** `BBF-TASK-003` 的 readiness 状态建模、`BBF-TASK-014` 的测试夹具
- **实施步骤：** 定义 owner/lease/session epoch；加入单调 sequence/deadline；
  原子组合 mode+setpoint；实现授予、撤销、超时和人工重新授权。
- **必须测试：** 双 owner、owner crash/restart、旧 lease 重连、乱序/重复/过期命令、
  arbiter 重启、网络分区恢复。
- **验收标准：** 非当前 lease、旧 epoch、乱序、重复、过期或字段不完整的事务到达
  PX4 publisher 的计数为 0；重启后默认无 owner。
- **evidence：** 协议版本、测试向量、拒绝事件、消息计数、root/依赖 SHA。
- **风险：** lease 超时过短导致误撤权，过长导致旧 owner 残留。
- **估算：** L
- **建议负责人角色：** Control Maintainer；Architecture Reviewer 与 Safety Reviewer
- **状态：** `PLANNED`

### BBF-TASK-003 — 安全启动与 PRESTREAM

- **Task ID：** `BBF-TASK-003`
- **对应 Audit ID：** `BBF-AUD-003`
- **标题：** 实现 WAIT_INPUTS→PRESTREAM→MODE_PENDING→ACTIVE
- **优先级：** P0
- **模块：** Offboard activation / FSM
- **目标：** 启动、Agent/PX4 重连和时钟 epoch 变化后保持无控制输出，完成可审计的
  有效 setpoint 预热后才请求 Offboard。
- **允许修改范围：** `offboard_cpp` FSM、时钟/输入 wrapper、配置和单元/SITL 测试。
- **禁止修改范围：** 缩短为未经评审的固定 sleep；以持续发布默认零值冒充 PRESTREAM；
  硬件、firmware、参数。
- **前置条件：** `BBF-TASK-006` 输入有效性；`BBF-TASK-004` ACK 接口设计；
  T01 受控构建入口。
- **依赖任务：** `BBF-TASK-004`、`BBF-TASK-006`
- **可并行任务：** `BBF-TASK-002` 协议实现、`BBF-TASK-012` firmware 静态生成
- **实施步骤：** 增加无输出初态；汇总 readiness；记录连续样本数/时长；中断清零；
  mode request 进入 pending；重连撤销旧事务。
- **必须测试：** 缺任一反馈、少于 1 秒、少于 20 样本、预热中断、节点/Agent/PX4
  重启、ROS clock zero/backward。
- **验收标准：** readiness 前 `/fmu/in/*` 控制发布为 0；连续至少 1 秒且至少 20
  个有效样本后才允许 mode request；任何 epoch 变化重新预热。
- **evidence：** 状态/样本时间线、发布计数、边界测试、SITL recorder。
- **风险：** readiness 定义遗漏关键输入，或把 topic 存在误当数据新鲜。
- **估算：** L
- **建议负责人角色：** Control Maintainer；Safety Reviewer
- **状态：** `PLANNED`

### BBF-TASK-004 — VehicleCommand ACK 与 fresh status

- **Task ID：** `BBF-TASK-004`
- **对应 Audit ID：** `BBF-AUD-004`
- **标题：** 建立 VehicleCommand 事务和 VehicleStatus freshness 闭环
- **优先级：** P0
- **模块：** PX4 command / telemetry freshness
- **目标：** arm、mode、land 只在正确 ACK 和新鲜状态一致时完成迁移。
- **允许修改范围：** `offboard_cpp` ACK subscription、pending/correlation、状态缓存、
  timeout/retry 策略及测试。
- **禁止修改范围：** 把 mock ACK 作为 SITL/台架证据；无限重试；硬件控制。
- **前置条件：** exact ACK topic/type/QoS 契约；统一 epoch/freshness 基础；T01 边界。
- **依赖任务：** `BBF-TASK-006`；`BBF-TASK-003` 和 `BBF-TASK-015` 消费本任务结果
- **可并行任务：** `BBF-TASK-002`、`BBF-TASK-012` 的静态工作
- **实施步骤：** 创建 pending 事务；关联 command/target/epoch/time window；分类全部
  result；处理 IN_PROGRESS；以 fresh VehicleStatus 二次确认；拒绝旧/错 ACK。
- **必须测试：** ACCEPTED、IN_PROGRESS、DENIED、FAILED、UNSUPPORTED、
  TEMPORARILY_REJECTED、CANCELLED、丢失/迟到/重复/错误 target/重启前 ACK。
- **验收标准：** ACCEPTED 且 fresh 状态一致前不得迁移；其余结果和超时均进入或保持
  锁存安全态；SITL 证据来源为 PX4。
- **evidence：** ACK/状态事件线、correlation 字段、退出码、PX4 source identity。
- **风险：** ACK 与状态乱序、重试命令歧义和 PX4 reboot 跨 epoch 污染。
- **估算：** M
- **建议负责人角色：** Control Maintainer；PX4 Maintainer 复核契约
- **状态：** `PLANNED`

### BBF-TASK-005 — RC authority、mock 隔离与 kill

- **Task ID：** `BBF-TASK-005`
- **对应 Audit ID：** `BBF-AUD-005`
- **标题：** 关闭 RC 绕过并建立独立 kill 锁存路径
- **优先级：** P0
- **模块：** RC safety interlock / kill
- **目标：** production 二进制无 mock override；fresh authoritative RC 是 arm/Offboard
  强制门；kill 为独立最高优先级、去抖且需人工复位的安全输入。
- **允许修改范围：** Offboard production/test target 分离、RC/kill evaluator、配置与测试。
- **禁止修改范围：** 把历史参数快照当当前映射；修改 PX4 参数；用 mock 作为
  SITL/bench 验收；自行决定飞行中降级动作。
- **前置条件：** `BBF-TASK-012` 提供 PX4 `rc_channels`；当前 RC mapping 经另行授权
  只读确认；kill 动作和 deadline 的安全评审输入已冻结。
- **依赖任务：** `BBF-TASK-003`、`BBF-TASK-012`；`BBF-TASK-019` 和
  `BBF-TASK-007` 消费本任务结果
- **可并行任务：** `BBF-TASK-004` 的单元实现、`BBF-TASK-014` 测试矩阵设计
- **实施步骤：** 分离 production/test 编译；所有入口强制 RC ready；按 function 或
  已验映射识别开关；实现 kill 去抖/边沿/锁存/人工复位。
- **必须测试：** 无首帧、signal_lost、stale、数组/映射错误、NaN/Inf、参数注入、
  kill bounce/持续/释放/重启。
- **验收标准：** production 二进制不含 `TEXT_RC`/mock 参数；所有 RC 无效场景 arm/mode
  发布计数为 0；kill 响应满足经批准 deadline。
- **evidence：** binary/symbol 检查、PX4 publisher identity、RC/kill 事件时间线。
- **风险：** kill 的期望动作尚需逐飞行阶段安全评审，不能由实现者单独选择。
- **估算：** M
- **建议负责人角色：** Control Maintainer；Safety Reviewer；PX4 Maintainer
- **状态：** `PLANNED`

### BBF-TASK-006 — 输入初始化与数据有效性

- **Task ID：** `BBF-TASK-006`
- **对应 Audit ID：** `BBF-AUD-006`
- **标题：** 统一首帧、finite、range、freshness 与 epoch 校验
- **优先级：** P0
- **模块：** 输入数据 / 控制安全
- **目标：** 消除 Odom/LandDetected 未初始化读取和首帧错误，拒绝异常控制/视觉数值。
- **允许修改范围：** typed validity wrapper、缓存初始化、纯函数校验、单元/fuzz/
  sanitizer 测试。
- **禁止修改范围：** 用默认零值表示已收到；放宽 NaN/Inf；访问硬件。
- **前置条件：** 时钟 epoch 策略评审；消息字段契约冻结。
- **依赖任务：** 无硬依赖；其输出被 `BBF-TASK-003`、`004`、`007` 使用
- **可并行任务：** `BBF-TASK-002`、`BBF-TASK-012`
- **实施步骤：** 值初始化全部成员；先判首帧再差分；统一 receive time/epoch；
  校验 finite/range/quaternion/字段组合；异常时清缓存并输出稳定故障码。
- **必须测试：** 无首帧、首帧、NaN/Inf、非法 quaternion、超范围 jump、负 age、
  clock reset、fuzz、ASan/UBSan。
- **验收标准：** sanitizer 无未初始化读取；首帧不差分；任一异常输入到 PX4 的发布
  计数为 0；无有效 odom/landed 不可推进控制状态。
- **evidence：** sanitizer 原始日志、表驱动用例、发布计数与代码覆盖。
- **风险：** 阈值选择若无单位和 frame 契约可能制造误拒绝。
- **估算：** M
- **建议负责人角色：** Control Maintainer；Perception Maintainer 复核视觉字段
- **状态：** `PLANNED`

### BBF-TASK-007 — fault lattice 与恢复

- **Task ID：** `BBF-TASK-007`
- **对应 Audit ID：** `BBF-AUD-007`
- **标题：** 建立故障优先级、deadline、锁存与人工恢复模型
- **优先级：** P0
- **模块：** Safety FSM / fault handling
- **目标：** 对 RC、DDS、odom、status、battery、owner 和组合故障给出经安全评审的
  确定行为；禁止未经授权自动恢复。
- **允许修改范围：** fault evaluator、状态/事件 taxonomy、安全参数、单元/SITL 测试。
- **禁止修改范围：** 实现者自行决定危险故障应 Land、Position 或停止输出；修改 PX4
  failsafe 参数；硬件试验。
- **前置条件：** `BBF-TASK-004` freshness/ACK、`005` RC/kill、`014` 测试框架；
  PX4 failsafe 设计评审。
- **依赖任务：** `BBF-TASK-004`、`BBF-TASK-005`、`BBF-TASK-014`
- **可并行任务：** 仅 fault table 安全分析可与依赖实现并行；FSM 集成不得并行
- **实施步骤：** 列出状态×故障矩阵；由安全评审批准动作；实现优先级/deadline/
  latch；恢复要求健康窗口和人工授权；结构化诊断。
- **必须测试：** 每个单故障、关键组合故障、起飞/ACTIVE/landing 阶段、恢复和重复故障。
- **验收标准：** 每个格有唯一批准动作和 deadline；landing 不会因分散分支被无条件
  取消；恢复绝不自动回到 ACTIVE；SITL 结果匹配同一状态表。
- **evidence：** 已批准 fault table、事件线、deadline 测量、失败注入日志。
- **风险：** 错误降级可能比 PX4 原生 failsafe 更危险，是全项目最高集成风险之一。
- **估算：** XL
- **建议负责人角色：** Safety Reviewer（责任人）；Control 与 PX4 Maintainer 联审
- **状态：** `BLOCKED`

### BBF-TASK-008 — 外部视觉坐标契约

- **Task ID：** `BBF-TASK-008`
- **对应 Audit ID：** `BBF-AUD-008`
- **标题：** 冻结 ENU/NED、FLU/FRD、TF/frame 数学契约
- **优先级：** P0（启用视觉 profile 前）
- **模块：** Perception / frame transform
- **目标：** 输入 frame 到 PX4 `VehicleOdometry` 的位置、姿态和 covariance 转换具有
  唯一规范和金样证明。
- **允许修改范围：** 坐标 ADR、纯转换函数、`vision_to_dds` 适配与离线测试。
- **禁止修改范围：** 启动真实相机/PX4；写 EKF2 参数；启用 precision landing。
- **前置条件：** 上游 frame 和安装外参契约由维护者确认；T01 包边界。
- **依赖任务：** 无本地 backlog 完成依赖；T01 是外部工作线前置，
  `BBF-TASK-022` 消费本任务结果
- **可并行任务：** `BBF-TASK-009` 时间/健康契约、`BBF-TASK-013` CI 设计
- **实施步骤：** 写字段级数学规范；抽出纯函数；覆盖基向量、90/180 度和 quaternion；
  验证 covariance 同构变换；frame 不符时不创建/撤销 publisher。
- **必须测试：** 单位轴、90/180 度、已知 quaternion、covariance、frame mismatch、
  NaN/Inf 和性质测试。
- **验收标准：** 全部金样通过；输出枚举与数学一致；frame 不匹配时 PX4 视觉发布为 0。
- **evidence：** ADR 版本、金样数据、测试日志与 frame tree。
- **风险：** 坐标错误可直接导致估计和控制发散。
- **估算：** L
- **建议负责人角色：** Perception Maintainer；PX4 Maintainer 与 Safety Reviewer
- **状态：** `PLANNED`

### BBF-TASK-009 — 视觉时间、reset 与健康

- **Task ID：** `BBF-TASK-009`
- **对应 Audit ID：** `BBF-AUD-009`
- **标题：** 统一 ROS/camera/TF/PX4 时间域和视觉健康门
- **优先级：** P0（启用视觉 profile 前）
- **模块：** Perception / timestamp / health
- **目标：** 明确 sample/publish time、epoch、delay、reset、quality、freshness；
  异常时间或健康输入不得发布到 PX4。
- **允许修改范围：** 时间 ADR、共享校验函数、视觉 health/diagnostics 和离线/SITL 测试。
- **禁止修改范围：** 用固定 quality/reset 冒充健康；硬件访问；写 PX4 参数。
- **前置条件：** `BBF-TASK-008` frame 契约；PX4 boot time 语义评审。
- **依赖任务：** `BBF-TASK-008`；`BBF-TASK-022` 消费本任务结果
- **可并行任务：** `BBF-TASK-008` 纯数学实现、`BBF-TASK-013`
- **实施步骤：** 定义时钟域与转换；检测 zero/backward/future/freeze；管理 sensor/PX4
  epoch 和 reset counter；从真实状态推导 quality/covariance；失效撤销发布许可。
- **必须测试：** zero/backward/future、freeze、sensor/PX4 reset、延迟超限、NaN/Inf、
  sim-time 未启动。
- **验收标准：** 所有异常输入 publish count=0；reset counter 和 health 变化可观测；
  SITL 记录 sample delay 与 PX4 消费证据。
- **evidence：** 时间 ADR、故障注入事件线、delay 分布、PX4 source/consumer identity。
- **风险：** 时钟域映射错误会造成陈旧数据被错误排序或融合。
- **估算：** L
- **建议负责人角色：** Perception Maintainer；PX4 Maintainer
- **状态：** `PLANNED`

## P1 Backlog

### BBF-TASK-010 — DDS-only 包/launch 边界

- **Task ID：** `BBF-TASK-010`
- **对应 Audit ID：** `BBF-AUD-010`
- **标题：** 技术强制 DDS-only package 与 launch allowlist
- **优先级：** P1
- **模块：** Workspace / build / launch
- **目标：** 权威入口不发现或启动 MAVROS、旧 bringup、mock、serial 和实验包。
- **允许修改范围：** 仅 T01 所有者批准的根级 allowlist、受控 build/profile launcher
  与静态负向测试。
- **禁止修改范围：** 本 BBF-DOC-WAVE 修改 T01 文件；删除历史目录；修改第三方包；
  启动 launch。
- **前置条件：** T01 文件所有权和 package 名称表冻结。
- **依赖任务：** 根 gitlink 元数据问题按 P2 `BBF-AUD-025` 另行追踪，不纳入本 P0/P1 backlog
- **可并行任务：** `BBF-TASK-011`、证据 schema 工作线 T08
- **实施步骤：** 由 T01 生成唯一 allowlist；约束 list/build/test；静态扫描禁止 action；
  建立负向 fixture。
- **必须测试：** colcon list/graph、禁止包注入、launch AST、核心包隔离 build。
- **验收标准：** 权威入口只发现批准包；禁止节点或 `/dev/ttyTHS0` 非 DDS action
  出现时非零失败。
- **evidence：** T01 生成的边界报告与测试日志；本文件不复制 receipt。
- **风险：** allowlist 过窄会隐藏必要依赖，过宽会恢复禁止路径。
- **估算：** M
- **建议负责人角色：** Release Maintainer（T01 owner）；Control Maintainer 复核
- **状态：** `PLANNED`

### BBF-TASK-011 — dirty checkout 可重建 receipt

- **Task ID：** `BBF-TASK-011`
- **对应 Audit ID：** `BBF-AUD-011`
- **标题：** 固化四个 lock checkout 的有效 dirty 文件树
- **优先级：** P1
- **模块：** Reproducibility / dependency provenance
- **目标：** 从 lock+receipt 在新目录重建当前有效差异，不改现有 checkout。
- **允许修改范围：** 仅 T00 所有者批准的 workspace/toolchain receipt、安装验证与隔离重放。
- **禁止修改范围：** 本 BBF-DOC-WAVE 修改 T00 文件；reset/clean/checkout 现有 dirty 树；
  擅自判断业务差异。
- **前置条件：** 维护者逐仓确认差异用途；T00 独占相关文件。
- **依赖任务：** 无
- **可并行任务：** `BBF-TASK-010`、T08 schema
- **实施步骤：** 分类差异；记录 base/origin/hash/用途；隔离重放；两次 verify-only。
- **必须测试：** patch/content hash、clean apply、幂等恢复、错误 origin/HEAD/dirty 负向测试。
- **验收标准：** 新目录重放后 content hash 一致；现有 dirty checkout 无变化。
- **evidence：** T00 权威 receipt；本规划只保存任务关系。
- **风险：** 把历史污染固化为必要适配。
- **估算：** M
- **建议负责人角色：** Release Maintainer（T00 owner）；相关依赖 Maintainer 签字
- **状态：** `PLANNED`

### BBF-TASK-012 — PX4 `rc_channels` firmware profile

- **Task ID：** `BBF-TASK-012`
- **对应 Audit ID：** `BBF-AUD-012`
- **标题：** 构建可追溯 PX4 v1.16.2 `rc_channels` DDS profile
- **优先级：** P1
- **模块：** PX4 firmware / DDS generation
- **目标：** 以最小 patch 增加 `/fmu/out/rc_channels`，完成静态生成、SITL 与 FMUv3
  构建留证；不刷写。
- **允许修改范围：** 隔离的锁定 PX4 source/patch/toolchain/profile、生成测试与 artifact。
- **禁止修改范围：** 刷写；硬件/串口；修改当前参数；baseline 加入
  `landing_target_pose`；改 T00/T08 schema/receipt。
- **前置条件：** T00 source/submodule/toolchain identity；T08 evidence schema；
  `px4_msgs` 字段一致性确认。
- **依赖任务：** `BBF-TASK-011`、P2 环境与 evidence 工作线
- **可并行任务：** `BBF-TASK-003`/`004` 的纯单元工作、`BBF-TASK-013`
- **实施步骤：** 锁 source/submodule；最小改 publications；检查生成 DataWriter/type/QoS；
  UDP SITL 验证真实 PX4 payload；构建 FMUv3 并 hash。
- **必须测试：** patch apply/reverse、generator、baseline topic 回归、SITL
  type/QoS/source/payload、FMUv3 build 与资源门。
- **验收标准：** `rc_channels` 恰有一个 PX4 publisher；mock 不能通过；artifact 可追溯
  到 source/submodule/toolchain；无硬件访问。
- **evidence：** patch、submodule 清单、raw logs、资源余量、`.px4` SHA-256，服从 T08。
- **风险：** FMUv3 flash/RAM 余量和 PX4/px4_msgs 版本漂移。
- **估算：** L
- **建议负责人角色：** PX4 Maintainer；Release Maintainer 复核 provenance
- **状态：** `BLOCKED`

### BBF-TASK-013 — required CI 与默认分支门

- **Task ID：** `BBF-TASK-013`
- **对应 Audit ID：** `BBF-AUD-013`
- **标题：** 建立固定依赖的 required CI 和分支保护建议
- **优先级：** P1
- **模块：** CI / governance
- **目标：** manifest、build、test、lint、docs/security 失败可阻止合并。
- **允许修改范围：** 后续授权的 CI workflow、质量配置和管理员 ruleset 操作说明。
- **禁止修改范围：** 本 BBF-DOC-WAVE 修改 `.github/workflows`；放宽测试；使用
  moving latest；未经授权修改远端保护设置。
- **前置条件：** T00 工具链固定；T01 权威包入口；review policy 生效。
- **依赖任务：** `BBF-TASK-010`；P2 质量发现 `BBF-AUD-032` 另行追踪，
  不伪装为本 backlog 的 Task ID
- **可并行任务：** `BBF-TASK-012` 静态生成、`BBF-TASK-008`/`009` 离线测试
- **实施步骤：** 定义 jobs；固定环境；加入负向 fixture；保存 artifacts；管理员单独
  启用 required checks。
- **必须测试：** 故意破坏 manifest/topic/allowlist/lint/link；冷缓存；本地等价命令。
- **验收标准：** 任一 required job 失败非零；依赖与 artifact 可追溯；分支保护可由
  只读 API 复核。
- **evidence：** CI run URL/ID、job logs、artifact hashes、ruleset 只读快照。
- **风险：** Foxy/aarch64 与 hosted runner 差异；self-hosted runner 不得直连硬件。
- **估算：** M
- **建议负责人角色：** Release Maintainer；领域 Maintainer 维护各 job
- **状态：** `PLANNED`

### BBF-TASK-014 — 安全 FSM 与故障注入测试

- **Task ID：** `BBF-TASK-014`
- **对应 Audit ID：** `BBF-AUD-014`
- **标题：** 建立可注入 clock/transport 的安全行为测试矩阵
- **优先级：** P1
- **模块：** Test architecture / control safety
- **目标：** P0 控制边和故障恢复具备表驱动单元测试与分层集成测试。
- **允许修改范围：** 测试夹具、纯 FSM 抽象、fake clock/transport、SITL fault hooks。
- **禁止修改范围：** 以 mock PX4 publisher 通过 PX4 契约验收；降低安全断言。
- **前置条件：** 已完成接口分阶段冻结；本任务先提供共享 fault-test 框架，
  `BBF-TASK-007` 再用它完成 fault lattice 验收。
- **依赖任务：** `BBF-TASK-002`、`BBF-TASK-003`、`BBF-TASK-004`、
  `BBF-TASK-017`、`BBF-TASK-019`
- **可并行任务：** 每个已冻结接口的测试先写；共享夹具合并串行
- **实施步骤：** 建状态转移表；先写失败用例；加入 fake clock/transport；覆盖组合故障；
  与 CI/SITL 分层。
- **必须测试：** ACK、owner、RC/DDS/odom/status/battery loss、restart、clock jump、
  NaN/Inf、双 writer、所有恢复边。
- **验收标准：** 每个 production 状态和故障边至少一正一负用例；失败阻止合并；
  SITL 契约场景来源为 PX4。
- **evidence：** requirement-test mapping、JUnit/原始日志、覆盖报告、故障时间线。
- **风险：** 过度依赖实现细节产生脆弱测试，或 mock 掩盖 DDS 真实行为。
- **估算：** L
- **建议负责人角色：** Test/Quality Maintainer；Safety Reviewer
- **状态：** `BLOCKED`

### BBF-TASK-015 — 项目级 PX4 DDS SITL

- **Task ID：** `BBF-TASK-015`
- **对应 Audit ID：** `BBF-AUD-015`
- **标题：** 建立正常与故障场景的可复放 PX4 DDS SITL 入口
- **优先级：** P1
- **模块：** SITL / integration
- **目标：** 证明真实 PX4 publisher/reader、topic/type/QoS/payload 与控制安全行为。
- **允许修改范围：** SITL orchestration、隔离 UDP Agent、测试 assertions、日志解析。
- **禁止修改范围：** 真实串口/硬件；刷写；mock 替代 PX4 契约证据；长时间无界 sleep。
- **前置条件：** `BBF-TASK-012` firmware profile；`BBF-TASK-014` fault hooks；
  `BBF-TASK-018` identity；CI 基线。
- **依赖任务：** `BBF-TASK-012`、`BBF-TASK-014`、`BBF-TASK-018`
- **可并行任务：** orchestration 骨架、证据解析和场景设计可并行；执行需依赖收敛
- **实施步骤：** 固定 source/profile/domain；启动隔离 SITL/Agent；验 endpoint；
  正常流程；故障注入；生成机器可判定时间线。
- **必须测试：** status_v1、RC、battery、odom、ACK；loss/reject/restart/double-writer/
  time jump/mock 混入。
- **验收标准：** 每场景独立、可重复、bounded timeout；PX4 source identity 可证明；
  任一失败阻止 promotion。
- **evidence：** orchestration manifest、raw logs/rosbag、event timeline、退出码与 hashes。
- **风险：** 时序 flaky；必须按事件条件等待并保持隔离 domain。
- **估算：** XL
- **建议负责人角色：** Integration/Test Maintainer；PX4 与 Control Maintainer 验收
- **状态：** `BLOCKED`

### BBF-TASK-016 — topic/type/version/QoS 契约

- **Task ID：** `BBF-TASK-016`
- **对应 Audit ID：** `BBF-AUD-016`
- **标题：** 集中关键 DDS endpoint 契约并验证交付
- **优先级：** P1
- **模块：** DDS interface / QoS
- **目标：** 对所有关键 `/fmu/in/*`、`/fmu/out/*` 建立 exact
  topic/type/version/direction/QoS 表与静态/SITL 断言。
- **允许修改范围：** interface manifest、生成/校验代码、Offboard/vision 最小适配、
  endpoint tests。
- **禁止修改范围：** 本任务直接改变 PX4 topic 业务范围；把 discovery 当作输入已消费；
  修改 T01 allowlist。
- **前置条件：** `BBF-TASK-012` 生成 endpoint；`BBF-TASK-015` SITL 骨架。
- **依赖任务：** `BBF-TASK-012`、`BBF-TASK-015`
- **可并行任务：** 静态 manifest 设计可与 firmware 生成并行
- **实施步骤：** 枚举端点；区分输入/输出 QoS；校验 MESSAGE_VERSION；生成节点常量；
  SITL 证明 PX4 实际发布/消费；不兼容时拒绝启动。
- **必须测试：** 每个关键端点 exact assertion、消息版本漂移、QoS 不兼容、topic rename、
  PX4 reader 消费。
- **验收标准：** 关键端点 100% 覆盖；任何 type/version/QoS 不匹配 fail-closed；
  输入消费由 PX4 证据证明。
- **evidence：** endpoint manifest hash、生成清单、ROS graph/QoS 与 PX4 消费日志。
- **风险：** RMW 显示与 XRCE 生成配置之间存在语义差异。
- **估算：** M
- **建议负责人角色：** PX4 Maintainer；Control/Perception Maintainer 联审
- **状态：** `BLOCKED`

### BBF-TASK-017 — 原子 Offboard input

- **Task ID：** `BBF-TASK-017`
- **对应 Audit ID：** `BBF-AUD-017`
- **标题：** 将 mode 与 trajectory 绑定为同 owner/sequence 的新鲜事务
- **优先级：** P1
- **模块：** Offboard command interface
- **目标：** 缺一、乱序、stale 或字段冲突时不向 PX4 发布。
- **允许修改范围：** command envelope、arbiter/Offboard 接口、字段合法性检查与测试。
- **禁止修改范围：** 保留两个无关联 topic 作为 production 权威输入；绕过 lease。
- **前置条件：** `BBF-TASK-002` owner/lease 协议；控制模式字段规则评审。
- **依赖任务：** `BBF-TASK-002`
- **可并行任务：** `BBF-TASK-003` readiness、`BBF-TASK-006` validity wrapper
- **实施步骤：** 定义原子消息；绑定 lease/sequence/deadline；校验 mode-setpoint 字段；
  拒绝不完整/冲突；迁移旧接口仅限测试隔离。
- **必须测试：** 缺 mode、缺 setpoint、旧+新混合、乱序/重复、双 publisher、模式冲突。
- **验收标准：** 所有无效组合到 PX4 publisher 的计数为 0；有效事务只消费一次。
- **evidence：** schema hash、输入/输出计数、拒绝事件与表驱动测试。
- **风险：** 接口迁移与 `BBF-TASK-002`、`003` 同文件冲突，必须先冻结接口再分支。
- **估算：** M
- **建议负责人角色：** Control Maintainer
- **状态：** `PLANNED`

### BBF-TASK-018 — transport 与 vehicle identity

- **Task ID：** `BBF-TASK-018`
- **对应 Audit ID：** `BBF-AUD-018`
- **标题：** 建立单一 machine-readable transport/vehicle profile
- **优先级：** P1
- **模块：** DDS transport / identity
- **目标：** 统一 ROS domain、根 namespace、client key、Agent transport、system/component
  identity 和目标 PX4；当前明确拒绝 swarm。
- **允许修改范围：** profile schema/实例、只读 preflight、launcher 生成与冲突测试。
- **禁止修改范围：** 复用 `/dev/ttyTHS0` 给 MAVLink；本轮读取当前硬件；启用多机。
- **前置条件：** T01 launcher 边界；T08 schema 职责边界明确。
- **依赖任务：** `BBF-TASK-010`
- **可并行任务：** `BBF-TASK-001` guard 接口、`BBF-TASK-012` firmware profile
- **实施步骤：** 定义 schema；生成 ROS/Agent/PX4 参数；启动前一致性校验；拒绝双 Agent、
  错 domain/client/identity 和 swarm namespace。
- **必须测试：** 缺字段、双 Agent/client key、domain 污染、错误 system ID、namespace 冲突。
- **验收标准：** profile 是唯一配置源；任何 identity 冲突 fail-closed；单机根 namespace
  为唯一批准配置。
- **evidence：** profile hash、生成输出、负向测试和 graph identity 快照。
- **风险：** 历史命令未记录数字 domain，不能被推断为当前配置。
- **估算：** M
- **建议负责人角色：** PX4/Release Maintainer；Control Maintainer 复核
- **状态：** `PLANNED`

### BBF-TASK-019 — 安全参数 schema

- **Task ID：** `BBF-TASK-019`
- **对应 Audit ID：** `BBF-AUD-019`
- **标题：** 分离 dev/SITL/bench/production 安全配置并校验范围
- **优先级：** P1
- **模块：** Safety configuration
- **目标：** 所有安全参数有类型、单位、范围、适用 profile、来源和配置 hash；
  production 默认禁止 auto arm 和危险动态修改。
- **允许修改范围：** 参数 schema、profile 实例、启动验证、配置 hash 与负向测试。
- **禁止修改范围：** 写 PX4 参数；沿用历史 snapshot 作为 current；动态放宽安全门。
- **前置条件：** `BBF-TASK-005` RC/kill 需求；`BBF-TASK-007` fault table。
- **依赖任务：** `BBF-TASK-005`
- **可并行任务：** `BBF-TASK-004`、`BBF-TASK-013`
- **实施步骤：** 收集参数；定义单位/范围/交叉约束；profile 分层；启动 fail-closed；
  禁止未知或飞行中危险修改；计算 hash。
- **必须测试：** 非 finite、负 timeout、非法高度/速度/电池/RC index、缺字段、跨 profile
  误用、未知动态参数。
- **验收标准：** 非法配置阻止启动；production `enable_arm=false`；证据绑定配置 hash。
- **evidence：** schema/version、实例 hash、全部负向测试和安全依据。
- **风险：** 机型/电池差异使通用阈值失效。
- **估算：** M
- **建议负责人角色：** Control Maintainer；Safety Reviewer
- **状态：** `PLANNED`

### BBF-TASK-020 — 许可证与第三方义务

- **Task ID：** `BBF-TASK-020`
- **对应 Audit ID：** `BBF-AUD-020`
- **标题：** 完成根工程、自有包和第三方分发合规链
- **优先级：** P1
- **模块：** Legal / release governance
- **目标：** 由权利人确认 LICENSE，并使包元数据、NOTICE/SBOM 和依赖维护状态可查。
- **允许修改范围：** 在维护者/法律明确选择后更新许可证正文、metadata、notices 和检查。
- **禁止修改范围：** 本任务或 Agent 自行选择许可证；伪造法律批准；修改第三方许可证。
- **前置条件：** 权利人和维护者给出书面许可证决策。
- **依赖任务：** 维护者/法律外部决策
- **可并行任务：** 依赖 inventory 与 SBOM 调研可和技术任务并行
- **实施步骤：** 盘点自有/第三方；记录来源/版本/义务/EOL；取得许可决定；对齐
  package metadata；CI 阻止 unknown 或未声明的许可证。
- **必须测试：** SPDX/license scan、SBOM 生成、package metadata 一致性、unknown 负向测试。
- **验收标准：** 每个发布组件的 license/来源/义务/维护状态机器可查；维护者批准可审计。
- **evidence：** 批准记录引用、license inventory、SBOM/NOTICE hash。
- **风险：** 法律结论不能由工程团队替代。
- **估算：** M
- **建议负责人角色：** Release Maintainer；项目权利人/法律顾问验收
- **状态：** `BLOCKED`

### BBF-TASK-021 — 四级 runbook 与回滚演练

- **Task ID：** `BBF-TASK-021`
- **对应 Audit ID：** `BBF-AUD-021`
- **标题：** 建立软件、SITL、拆桨台架、有限实机逐级 promotion
- **优先级：** P1
- **模块：** Operations / acceptance / rollback
- **目标：** 每一级有 go/no-go、stop、人工确认、evidence 和 rollback；台架/实机草案不冒充验证。
- **允许修改范围：** `docs/runbooks`、checklist、与 T08 schema 对接的模板；离线桌面演练。
- **禁止修改范围：** 本任务内刷写、arm、mode、setpoint、硬件 launch；修改 T08 schema/
  receipt；把桌面演练标为 BENCH_VERIFIED。
- **前置条件：** T08 schema；实际台架前 `BBF-TASK-001`–`020` 适用门全部通过。
- **依赖任务：** `BBF-TASK-012`–`015`；所有 P0
- **可并行任务：** runbook 草案可立即与软件开发并行；实际执行不得并行或提前
- **实施步骤：** 定义级别/角色/设备；列 preflight/go/no-go/stop；绑定证据；定义
  software/firmware/参数 rollback；先桌面演练。
- **必须测试：** 文档 dry-run、缺 hash/observer/rollback/approval 负向检查、链接/schema。
- **验收标准：** 未过上级不得升级；Level 2/3 保持 `UNVERIFIED` 直到真实授权执行；
  台架实际回滚成功才可提请有限实机。
- **evidence：** checklist 实例、签字、日志和 rollback receipt；本轮仅产生草案。
- **风险：** 纸面流程不能替代物理演练。
- **估算：** L
- **建议负责人角色：** Release/Operations Maintainer；Safety Reviewer；Flight Operator
- **状态：** `PARTIALLY_IMPLEMENTED`

### BBF-TASK-022 — 感知/EKF2 profile

- **Task ID：** `BBF-TASK-022`
- **对应 Audit ID：** `BBF-AUD-022`
- **标题：** 建立 sensor→TF→DDS→EKF2 受管 profile 与健康门
- **优先级：** P1
- **模块：** Perception integration
- **目标：** 设备、frame、time、QoS、EKF2 前置条件全部满足后才允许视觉 publisher。
- **允许修改范围：** sensor/SITL profile、只读 preflight、health gate、离线测试。
- **禁止修改范围：** 未授权读取/写入当前 PX4 参数；真实相机启动；使用历史参数
  snapshot 作为 current。
- **前置条件：** `BBF-TASK-008`/`009`；`BBF-TASK-018` identity；当前参数需另行授权取证。
- **依赖任务：** `BBF-TASK-008`、`BBF-TASK-009`、`BBF-TASK-018`
- **可并行任务：** schema/离线 profile 可与 `BBF-TASK-023` 设备降级测试设计并行
- **实施步骤：** 定义 profile；校验设备/frame/time/QoS；只读校验 EKF2 前置；
  不健康时不创建或撤销视觉 writer；输出诊断。
- **必须测试：** 缺设备/TF/time sync/EKF2 参数、错误 frame/domain、health loss/recovery。
- **验收标准：** 任一前置不满足时 `/fmu/in/vehicle_visual_odometry` publisher 为 0；
  参数证据绑定 firmware/time/profile。
- **evidence：** profile hash、preflight 输出、health 事件、参数 evidence 引用。
- **风险：** 当前参数未知，必须保持 `BLOCKED`，不得从历史值推断。
- **估算：** L
- **建议负责人角色：** Perception Maintainer；PX4 Maintainer
- **状态：** `BLOCKED`

### BBF-TASK-023 — RealSense 稳定身份与缺失降级

- **Task ID：** `BBF-TASK-023`
- **对应 Audit ID：** `BBF-AUD-023`
- **标题：** 固定 D435/T265 角色并处理缺失、掉线和重枚举
- **优先级：** P1
- **模块：** Sensor identity / degradation
- **目标：** 错设备不自动替代；T265 不可用时清除旧缓存并撤销视觉 authority。
- **允许修改范围：** 匿名化设备角色/profile、udev 建议、health/degradation 与虚拟设备测试。
- **禁止修改范围：** 在 public evidence 写真实 serial/VID:PID；安装 udev；启动真实设备；
  把历史枚举当 current。
- **前置条件：** `BBF-TASK-022` profile；真实设备身份确认需另行授权和脱敏流程。
- **依赖任务：** `BBF-TASK-022`
- **可并行任务：** 虚拟设备测试与 profile schema 可并行
- **实施步骤：** 定义角色/稳定 ID；有限等待；错误/重复设备 fail-closed；掉线清缓存；
  重枚举需重新健康窗口。
- **必须测试：** 设备缺失、错误 ID、双设备、USB2/带宽降级、拔出/重连/重枚举。
- **验收标准：** T265 不可用时无 PX4 视觉 publisher；旧数据不复用；错误设备不替代。
- **evidence：** 使用匿名设备别名的测试矩阵、health 时间线和 profile hash。
- **风险：** 真实设备当前状态 `UNVERIFIED`，硬件验证需新授权。
- **估算：** M
- **建议负责人角色：** Perception Maintainer；Security Reviewer 复核脱敏
- **状态：** `BLOCKED`

### BBF-TASK-024 — 独立精准降落 profile

- **Task ID：** `BBF-TASK-024`
- **对应 Audit ID：** `BBF-AUD-024`
- **标题：** 将 precision landing 保持默认关闭并建立专项闭环
- **优先级：** P1（仅精准降落能力）
- **模块：** Precision landing
- **目标：** baseline 无 landing target publisher；专项 profile 独立验证 firmware、frame、
  freshness、covariance、quality 与目标丢失。
- **允许修改范围：** 独立 profile/firmware topic patch、视觉 target validity、SITL 测试。
- **禁止修改范围：** baseline 默认启用；与普通视觉验收合并；在本轮启动硬件/实机。
- **前置条件：** `BBF-TASK-008`、`009`、`012`、`022` 全部通过；产品需求批准。
- **依赖任务：** `BBF-TASK-008`、`BBF-TASK-009`、`BBF-TASK-012`、`BBF-TASK-022`
- **可并行任务：** 仅需求/接口设计可并行；实现和 SITL 不得早于依赖
- **实施步骤：** 保持 baseline publisher 缺席；定义专项 firmware/profile；修复 camera
  frame 使用；实现 target age/quality/covariance 门；SITL 故障注入。
- **必须测试：** 默认无 publisher、target stale/lost/jump/NaN/Inf、frame mismatch、
  quality/covariance、PX4 实际 reader。
- **验收标准：** baseline 永不出现 publisher；专项所有异常目标 fail-closed；
  PX4 消费证据来自 SITL，不用 mock。
- **evidence：** 独立 profile/patch hash、正常与目标丢失时间线、PX4 reader 证据。
- **风险：** 精降会放大视觉坐标/时间错误；应在普通视觉闭环稳定后开展。
- **估算：** L
- **建议负责人角色：** Perception Maintainer；PX4 与 Safety Reviewer
- **状态：** `BLOCKED`

## 工作线 G：仓库依赖与 release hygiene

Wave 2 增加工作线 G，不改变 `BBF-TASK-001`–`024` 的安全验收含义。G 负责把
依赖恢复、moving source、review ownership、required checks 和 release/rollback
evidence 变成可机器验证的 release 门。

### BBF-TASK-025 — archive manifest 与 source profile

- **Task ID：** `BBF-TASK-025`
- **工作线：** G
- **优先级：** P1
- **目标：** 将 build-excluded `px4_bringup` provenance 从默认恢复范围移入显式
  archive manifest，并把 production、build/test、optional perception/navigation、
  archive 和 moving source 分层。
- **唯一写入范围：** 后续获批任务中的 `workspace*.repos`、manifest validator 及其
  tests、对应当前文档；不得修改任何 nested checkout。
- **前置依赖：** 维护者批准
  [`21_WAVE2_DEPENDENCY_MANIFEST_REVIEW.md`](../audits/2026-07-26/21_WAVE2_DEPENDENCY_MANIFEST_REVIEW.md)
  的最小迁移方案。
- **是否可立即开始：** 是，只做 schema/参数/负向测试设计；实际迁移需维护者批准。
- **验收门：** 默认 restore 不计划 archive/optional source；显式 archive 只接受精确
  SHA；active/archive 重复、moving archive 或 URL 不一致均 fail closed；
  `px4_bringup` 仍是 forbidden package。
- **状态：** `PLANNED`
- **硬件授权：** 不需要；禁止硬件。

### BBF-TASK-026 — moving dependency receipt

- **Task ID：** `BBF-TASK-026`
- **工作线：** G
- **优先级：** P1
- **目标：** 为 `../communication` 建立 root HEAD、origin、exact HEAD、dirty
  content、时间、用途、批准人和 replay 结果的 fail-closed receipt。
- **唯一写入范围：** 后续获批的 receipt schema/validator/tests 与新 dated receipt；
  不修改、清理或提交 `../communication`。
- **前置依赖：** 维护者决定当前 dirty/untracked 串口实现的归属及签名身份。
- **是否可立即开始：** receipt schema 与负向测试可开始；签署 current receipt
  `BLOCKED` 于维护者确认。
- **验收门：** 缺 checkout、错误 origin/HEAD、未解释 dirty、缺签名或 replay hash
  不一致均阻止相关 profile/release。
- **状态：** `PARTIALLY_IMPLEMENTED`
- **硬件授权：** 不需要；不得启动串口链。

### BBF-TASK-027 — CODEOWNERS 落地

- **Task ID：** `BBF-TASK-027`
- **工作线：** G
- **优先级：** P1
- **目标：** 在真实 GitHub user/team 和路径经过维护者确认后，把不可启用的 proposal
  转成有效 `.github/CODEOWNERS`。
- **唯一写入范围：** 后续获批的 `.github/CODEOWNERS` 和 governance approval
  evidence；不虚构 owner。
- **前置依赖：** 维护者提供有效账号/team；proposal 路径检查通过。
- **是否可立即开始：** 否。
- **验收门：** GitHub 能解析所有 owner；关键路径有真实 reviewer；proposal 的
  “不可启用”警告只在批准后解除。
- **状态：** `BLOCKED`
- **硬件授权：** 不需要。

### BBF-TASK-028 — CI required checks

- **Task ID：** `BBF-TASK-028`
- **工作线：** G，与工作线 D 共同验收
- **优先级：** P1
- **目标：** 将 D 的已通过 job graph 绑定为默认分支 required checks，并保存远端
  ruleset 只读证据。
- **唯一写入范围：** GitHub ruleset/branch-protection 配置及其 evidence；workflow
  文件仍由 D 独占。
- **前置依赖：** `BBF-TASK-013` 的 jobs 在固定环境通过；仓库管理员明确授权。
- **是否可立即开始：** 否；当前只能设计 required job 名称。
- **验收门：** 任一 required job 失败阻止合并；只读 API 快照与 job 名称一致；没有
  bypass 或弱化安全负向测试。
- **状态：** `BLOCKED`
- **硬件授权：** 不需要；需要远端管理员授权。

### BBF-TASK-029 — release 与 rollback evidence

- **Task ID：** `BBF-TASK-029`
- **工作线：** G
- **优先级：** P1
- **目标：** 每个 release 候选绑定 source/dependency/toolchain/profile/artifact、
  approval、已知 blocker 和可演练 rollback。
- **唯一写入范围：** release/rollback manifest、dated evidence/index 条目和对应
  validator tests；不改历史 evidence。
- **前置依赖：** `BBF-TASK-025`、`026`、`028`；T08 schema 仍是格式权威。
- **是否可立即开始：** 负向 fixture 可开始；release promotion `BLOCKED`。
- **验收门：** 缺任一 identity/approval/rollback artifact 非零；rollback 在隔离软件
  环境可重放；台架/飞行 rollback 仍需另行授权。
- **状态：** `BLOCKED`
- **硬件授权：** 离线不需要；台架/飞行演练需要且当前未授权。

## Wave 2 调度状态

| 工作线 | 当前可启动项 | 状态 |
|---|---|---|
| A | A1 PX4 source/message/profile 只读对齐 | `PLANNED`；只读部分可立即开始 |
| B | B1 Offboard freshness/ACK 失败测试 | `PLANNED`；纯软件可立即开始 |
| C | C1 authority envelope ADR/schema | `PLANNED`；可立即开始 |
| D | D1 CI job graph/负向 fixture | `PLANNED`；可立即开始 |
| E | E1 vision frame/time/health contract | `BLOCKED` 于 C1 接口冻结 |
| F | F1 schema/parser 离线完善 | `PARTIALLY_IMPLEMENTED`；正式 SITL `BLOCKED` 于 A–D |
| G | G1 archive manifest/source profile 设计 | `PLANNED`；可立即开始，迁移需批准 |

精确 owner、写入范围、输入、输出和并行冲突以
[`NEXT_PARALLEL_TASKS.md`](NEXT_PARALLEL_TASKS.md) 为 canonical 调度表。

## 覆盖检查

| 优先级 | Audit ID 范围 | Backlog 数量 | 覆盖状态 |
|---|---|---:|---|
| P0 | `BBF-AUD-001`–`009` | 9 | `STATICALLY_VERIFIED` |
| P1 | `BBF-AUD-010`–`024` | 15 | `STATICALLY_VERIFIED` |
| Wave 2 release hygiene | `BBF-TASK-025`–`029` | 5 | `STATICALLY_PLANNED` |
| 合计 | 29 项 | 29 | mapping 完整；实现状态见各任务 |

这里的 `STATICALLY_VERIFIED` 仅表示文档映射完整，不表示任一实现、SITL、台架或
实机能力已通过。
