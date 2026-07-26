# 下一轮 Codex 任务包

> 基线：`agent/follow-latest-offboard@3ce28094e14ed720987c5fc6d1172e377f09b1cc`
> 默认安全边界：除任务另有明确授权，不访问硬件、不启动 Agent/控制节点、不写 PX4 参数、不刷 firmware、不 arm、不发送 `/fmu/in/*`。所有 build/test 使用 `/tmp` 隔离目录。
> 并行原则：同一依赖链不得并行修改同一文件；`T00/T01/T08` 可先并行，`T02` 在 T00/T08 后，`T03/T04/T05` 的设计可并行但集成按依赖顺序，感知任务在 T04 的 profile 框架后进入集成。

## T00 — 固化 dirty checkout 与环境基线

任务 ID: `BBF-NEXT-T00`
优先级: P1
目标: 把四个受管 dirty checkout 和核心工具链变成可从空白环境恢复的机器可验基线。
允许修改范围: `workspace*.repos` 的配套 schema、`Scripts/installation/`、新增 `docs/evidence/` 模板/receipt、必要的 patch 清单。
禁止修改范围: 四个 dirty checkout 的实际文件树；任何 reset/clean/checkout；PX4 参数、固件和硬件。
前置条件: 维护者确认四个 checkout 差异的业务用途；从当前树只读导出差异。
实施步骤:

1. 分类 mode-only、删除、未跟踪和源码修改。
2. 为每个仓库记录 base SHA、origin、patch/content hash、用途、适用平台和重放顺序。
3. 补充 OS/ROS/compiler/CMake/Python/tool 版本 schema。
4. 在新的 `/tmp` 源目录重放并执行两次 verify-only。

必须运行的测试: `bash -n`；manifest parser 负向测试；空白 dry-run；两次隔离恢复/校验；`git diff --check`。
验收标准: 任何 checkout 的有效文件树都能由 lock+receipt 重建；第二次运行无变更；origin/HEAD/dirty hash 不匹配时非零退出。
输出文档: `docs/evidence/WORKSPACE_BASELINE_<date>.md` 与机器可读 receipt。
风险: 错误固化历史污染；必须由维护者逐仓确认。
建议并行度: 2（工具链 schema 与 dirty 差异分类可并行；最终 receipt 串行汇合）。

## T01 — 建立 DDS-only 包发现与 launch 边界

任务 ID: `BBF-NEXT-T01`
优先级: P1
目标: 让默认受管构建/launch 无法发现或启动 MAVROS、旧 bringup、mock、serial 和实验包。
允许修改范围: 根级 colcon 配置、权威 build script、根级 profile/allowlist、对应测试和文档。
禁止修改范围: 第三方包源码；删除历史目录；启动任何 launch。
前置条件: 使用 `workspace.excluded_packages` 作为输入但核对实际包名/路径。
实施步骤:

1. 生成唯一 DDS-only package allowlist。
2. 让权威 `colcon list/build/test` 只使用 allowlist；发现禁止包时 fail-closed。
3. 增加 launch AST/static scan，拒绝 MAVROS、旧 PX4 writer、mock 和硬件自动启动。
4. 标记非权威历史入口并从 production profile 技术隔离。

必须运行的测试: 隔离 `colcon list/graph`；禁止包负向测试；launch Python compile/AST；核心三包隔离 build。
验收标准: 权威入口只发现批准包；人为加入禁止包/launch action 时测试失败；不修改历史目录。
输出文档: `docs/evidence/DDS_ONLY_PACKAGE_BOUNDARY_<date>.md`。
风险: 过度忽略可能隐藏必要依赖；allowlist 必须与 package dependency graph 交叉验证。
建议并行度: 2（包边界与 launch 静态测试可并行）。

## T02 — PX4 v1.16.2 `rc_channels` firmware profile

任务 ID: `BBF-NEXT-T02`
优先级: P1
目标: 生成只增加 `/fmu/out/rc_channels` 的可追溯 PX4 DDS profile，完成静态生成、SITL 和 FMUv3 build；不刷写。
允许修改范围: 新增锁定 PX4 source/patch/toolchain/evidence；独立 profile 配置和测试。
禁止修改范围: 当前飞控参数；任何 firmware flash；`landing_target_pose` baseline；真实串口/硬件。
前置条件: T00 完成 PX4 source/submodule/toolchain lock；T08 evidence schema 完成。
实施步骤:

1. 对齐 PX4/px4_msgs `RcChannels` 定义。
2. 最小修改 `dds_topics.yaml` publication。
3. 静态检查生成 DataWriter/type/QoS。
4. 隔离 SITL + UDP Agent 验证唯一 PX4 publisher 和真实 payload。
5. 构建 `px4_fmu-v3_default`，记录资源余量与 SHA-256。

必须运行的测试: patch clean apply/reverse；PX4 generator；SITL DDS topic/type/QoS/payload；baseline topic regression；FMUv3 build。
验收标准: mock publisher 不能通过验收；artifact 可追溯到 source/submodule/toolchain；不产生刷写或硬件访问。
输出文档: `docs/evidence/PX4_V116_RC_CHANNELS_PROFILE_<date>.md`、patch、raw log、artifact hash。
风险: FMUv3 flash/RAM 余量；消息版本漂移。
建议并行度: 2（静态生成与 evidence 模板准备并行；SITL/FMUV3 在生成通过后串行）。

## T03 — VehicleCommand ACK、反馈 freshness 与 Offboard 预热

任务 ID: `BBF-NEXT-T03`
优先级: P0
目标: 所有 arm/mode/land 事务仅在有效预热、ACK 接受和 fresh 状态一致后迁移。
允许修改范围: `src/offboard_cpp` 的节点/FSM/input/topic constants、配置和测试。
禁止修改范围: mock 作为 production 验收；硬件/参数/firmware；mission owner 协议（由 T04）。
前置条件: T01 确保受控构建；先写失败测试。SITL 部分依赖 T02。
实施步骤:

1. 订阅精确 ACK topic并实现 pending/result/correlation/timeout。
2. 给 VehicleStatus/Odom/Battery/LandDetected 加首帧、receive time、epoch 和 freshness。
3. 初始化全部缓存成员并修复 odometry 首帧逻辑。
4. 实现 WAIT_INPUTS/PRESTREAM/MODE_PENDING；PRESTREAM 中断清零。
5. 仅 ACK ACCEPTED + fresh status 一致时完成迁移。

必须运行的测试: 所有 ACK result；丢失/迟到/重复/错误 target；首帧/stale/reboot/clock rollback；至少 1s/20 sample 预热；ASan/UBSan 单测；T02 后 SITL。
验收标准: ready 前所有 PX4 控制发布计数为 0；拒绝/超时锁存安全；无未初始化/NaN/Inf 路径。
输出文档: `docs/evidence/OFFBOARD_COMMAND_TRANSACTION_<date>.md`。
风险: 状态与 ACK 到达乱序；必须定义关联时间窗和 PX4 reboot epoch。
建议并行度: 2（freshness wrapper 与 ACK 测试可并行；FSM 集成串行）。

## T04 — owner/lease 与运行时 graph guard

任务 ID: `BBF-NEXT-T04`
优先级: P0
目标: 运行时强制唯一 control writer、vision writer、Agent 和 mission owner，并防止旧 owner 重连夺权。
允许修改范围: 新 control-authority/arbiter 包、Offboard 输入接口、production profile launcher、graph/lease 测试。
禁止修改范围: 启用 swarm；直接复用旧 demo/animal 作为 production owner；硬件运行。
前置条件: T01 包/launch 边界；控制权协议 ADR 评审。与 T03 接口先冻结后并行开发。
实施步骤:

1. 定义 command envelope：owner ID、lease ID、sequence、deadline、mode+setpoint 原子字段。
2. Offboard 只接受 arbiter 输出。
3. 启动前和持续检查 publisher/node/profile/identity 基数。
4. owner loss、重复 owner、旧 owner 重连和 graph 变化时撤销 lease并锁存。
5. 结构化输出 active owner/lease 与拒绝原因。

必须运行的测试: 双 writer、双 owner、owner crash/restart、旧 lease、乱序/重复、namespace/domain/client key 冲突、禁止节点混入。
验收标准: 非当前 lease 消息不抵达 PX4 publisher；任何基数冲突阻止 ACTIVE；恢复必须人工重新授权。
输出文档: ADR、协议 schema、`docs/evidence/CONTROL_AUTHORITY_RUNTIME_<date>.md`。
风险: ROS graph discovery 短暂性；guard 不能仅依赖一次快照。
建议并行度: 3（协议、graph guard、故障测试可并行，集成串行）。

## T05 — RC/kill/fault lattice 与安全参数 schema

任务 ID: `BBF-NEXT-T05`
优先级: P0
目标: 移除 production mock 绕过，统一 RC/DDS/odom/status/battery 故障优先级、锁存、降级和人工恢复。
允许修改范围: Offboard production target、FSM/fault evaluator、配置 schema、诊断和测试。
禁止修改范围: 修改 PX4 参数；把 kill 映射历史快照当当前事实；自动恢复到 ACTIVE。
前置条件: T03 freshness/ACK；T04 authority；RC SITL 集成依赖 T02。
实施步骤:

1. production target 移除 `TEXT_RC` 和 mock 参数。
2. 所有 arm/Offboard 入口要求 fresh authoritative RC。
3. 定义 fault priority/state/action/deadline；着陆中故障不得无条件取消 landing。
4. 实现 kill 去抖、边沿、最高优先级锁存和人工复位协议。
5. 集中安全参数，定义单位、范围、profile 和配置 hash。

必须运行的测试: 无 RC/丢 RC/stale/signal_lost；DDS/odom/status/battery loss；kill bounce/edge；非法参数；各飞行状态 fault injection。
验收标准: production 二进制无 mock 符号；任何关键缺失禁止 arm；故障在 deadline 内进入预定义状态并稳定输出错误码。
输出文档: safety parameter schema、fault table、`docs/evidence/FAULT_LATTICE_<date>.md`。
风险: 错误降级动作可能比保持 PX4 failsafe 更危险；逐状态评审。
建议并行度: 2（schema/诊断与 fault 测试并行；FSM 合并串行）。

## T06 — 根级 required CI 与质量门

任务 ID: `BBF-NEXT-T06`
优先级: P1
目标: 让 manifest、build、test、lint 和安全静态回归在合并前自动阻断。
允许修改范围: `.github/workflows/`、CI scripts/config、lint/static-analysis 配置。
禁止修改范围: 放宽测试以获得绿色；使用 moving latest dependency；创建/修改远端保护规则（除非另行授权）。
前置条件: T01 权威包入口；T00 工具链/依赖固定。
实施步骤:

1. 添加 manifest/dirty/包边界 job。
2. 添加核心三包隔离 build/test。
3. 修复并强制 vision lint；加入 shell/python/xml/yaml/launch 检查。
4. 分层加入 warnings-as-errors、clang-tidy/cppcheck、ASan/UBSan。
5. 上传原始日志、test results、SBOM/lock receipt 与 hash。

必须运行的测试: 本地 runner 等价命令；故意破坏 topic/allowlist/lint 的负向 CI；缓存冷启动。
验收标准: 任一 required job 失败返回非零；依赖固定；artifact 可追溯。远端 branch protection 由仓库管理员另行配置。
输出文档: `docs/evidence/CI_BASELINE_<date>.md`。
风险: Foxy/aarch64 与 hosted runner 差异；必要时用锁定容器或 self-hosted runner，禁止未经评审直连硬件。
建议并行度: 3（manifest、build/test、static-analysis jobs 可并行）。

## T07 — PX4 DDS SITL 验收与故障注入框架

任务 ID: `BBF-NEXT-T07`
优先级: P1
目标: 建立项目级、可复放且能区分 PX4 publisher 与 mock 的 SITL 验收入口。
允许修改范围: SITL scripts/launch、测试 orchestration、rosbag/log assertions、CI job。
禁止修改范围: 真实硬件串口；用 mock 替代 PX4 contract 验收；刷写。
前置条件: T02 firmware profile；T03–T05 的测试接口；T06 CI 基线。
实施步骤:

1. 固定 PX4 SITL、Agent、domain/namespace/client key。
2. 验证 session、topic/type/QoS/source identity。
3. 正常场景覆盖预热、ACK、状态迁移。
4. 故障场景覆盖 loss/restart/reject/double-writer/time jump。
5. 输出机器可判定 event timeline。

必须运行的测试: `vehicle_status_v1`、rc/battery/odom/ACK；RC/DDS/owner/status loss；ACK result；PX4/Agent 重启；mock 混入拒绝。
验收标准: 每个场景独立、可重复、超时明确；PX4 source identity 可证明；失败阻止 CI。
输出文档: `docs/evidence/SITL_DDS_ACCEPTANCE_<date>.md` 和原始 artifacts。
风险: 测试时序不稳定；使用事件条件和 bounded timeout，不能用长固定 sleep。
建议并行度: 3（正常、故障、证据解析可并行，基础 orchestration 先完成）。

## T08 — 统一证据、发布与回滚 schema

任务 ID: `BBF-NEXT-T08`
优先级: P2
目标: 统一 firmware/build/SITL/台架证据和回滚包格式，避免历史声明冒充当前事实。
允许修改范围: `docs/evidence/` 模板、机器可读 schema、验证脚本、索引。
禁止修改范围: 覆盖现有 evidence；删除 handoff；伪造未运行结果。
前置条件: 无，可与 T00/T01 并行。
实施步骤:

1. 定义 evidence metadata schema。
2. 区分 current、historical、superseded、unverified。
3. 加入命令、exit code、环境、root/dependency SHA、artifact hash、原始日志链接。
4. 定义 firmware/参数/software rollback manifest。
5. 对现有两份 evidence 做非破坏索引。

必须运行的测试: schema validation；缺字段/错误 hash/旧 HEAD 负向测试；链接检查。
验收标准: 任一验收可追溯到同一源码、环境和 artifact；历史参数不可被标为 current。
输出文档: `docs/evidence/SCHEMA.md`、schema 与索引。
风险: handoff 与 evidence 重复维护；权威字段必须唯一。
建议并行度: 2（schema 与现有证据索引并行）。

## T09 — 外部视觉坐标与时间契约

任务 ID: `BBF-NEXT-T09`
优先级: P0（启用视觉 profile 前）
目标: 证明 ENU/NED、FLU/FRD 转换、timestamp、reset、quality 和 freshness 正确，异常输入不发布 PX4 视觉消息。
允许修改范围: `src/vision_to_dds`、共享坐标/时间库、测试、ADR。
禁止修改范围: 启动真实相机/PX4；写 EKF2 参数；启用 precision landing。
前置条件: T01 受控包边界；T04 profile/authority 接口冻结。
实施步骤:

1. 写坐标/时间 ADR 和字段级契约。
2. 将转换抽为纯函数并添加金样/性质测试。
3. 校验 frame、quaternion、covariance、finite、timestamp、delay、reset。
4. 对 freeze/future/backward/sensor reset fail-closed。
5. 增加结构化 vision health。

必须运行的测试: 轴向与 90/180 度金样；四元数归一；covariance；NaN/Inf；TF freeze；clock jump；reset counter；无发布断言。
验收标准: 所有异常输入 publish count=0；输出 frame 与数学规范一致；测试不依赖真实硬件。
输出文档: ADR、`docs/evidence/VISION_FRAME_TIME_CONTRACT_<date>.md`。
风险: 现有输入 frame 假设不清；先冻结上游契约再改实现。
建议并行度: 2（数学与时间测试并行）。

## T10 — 感知设备 profile 与缺失降级

任务 ID: `BBF-NEXT-T10`
优先级: P1
目标: 用稳定身份绑定 D435/T265，并在 T265 缺失/掉线时明确禁用视觉注入；隔离旧硬件入口。
允许修改范围: 新 sensor profile、udev 建议文件、受管 launch、health diagnostics、离线/虚拟设备测试。
禁止修改范围: 运行相机/雷达/VPU；写系统 udev；删除旧源码；启动旧 MAVROS/serial launch。
前置条件: T01 launch 隔离；T09 frame/time contract。
实施步骤:

1. 编码 D435/T265 角色、serial/VID:PID、USB/带宽要求。
2. 建立 frame/TF 参数映射和启动前检查。
3. 实现缺失、断线、重枚举降级及旧数据清除。
4. profile 禁止旧 MAVROS、ttyTHS0、RPLIDAR/USB/VPU 非主线入口。
5. 独立设计 precision landing profile，但默认不创建 publisher。

必须运行的测试: 设备缺失/错误 serial/双设备/重枚举；frame 不匹配；health loss；禁止 launch action 静态测试。
验收标准: T265 不可用时无 `/fmu/in/vehicle_visual_odometry` publisher；错误设备不被自动替代；旧 launch 无法进入 production profile。
输出文档: `docs/evidence/SENSOR_PROFILE_<date>.md`、设备/TF 图。
风险: 当前 T265 不在历史枚举中，动态行为先标未验证；后续硬件验证需另行授权。
建议并行度: 2（profile schema 与降级测试并行）。

## T11 — SITL 到拆桨台架的 runbook 与回滚演练

任务 ID: `BBF-NEXT-T11`
优先级: P1
目标: 建立 firmware/SITL/拆桨台架/有限实机四级验收、停止条件和回滚表。
允许修改范围: 运维 runbook、checklist、证据模板；仅离线演练。
禁止修改范围: 本任务内刷写、参数写入、arm、模式切换、setpoint、硬件 launch。
前置条件: T08 schema；T02/T03/T04/T05/T07 全部验收后才能实际进入台架。
实施步骤:

1. 定义角色、物理隔离、桨叶/执行器状态、双人确认。
2. 定义 transport 只读预检、publisher/owner graph 检查。
3. 定义 fault injection、deadline、停止条件和人工复位。
4. 定义 firmware/参数/software 前后快照与 rollback。
5. 只做桌面演练；实际台架另行授权。

必须运行的测试: runbook dry-run；checklist schema；缺少 hash/参数/观察员/回滚项时拒绝；证据链接检查。
验收标准: 每级门有明确 go/no-go；失败不会自动升级；回滚步骤可在无硬件桌面演练中完整解析。
输出文档: `docs/runbooks/BENCH_ACCEPTANCE.md`（或经维护者批准路径）及 evidence 模板。
风险: 纸面 runbook 不能替代真实台架演练；报告必须持续标“未验证”。
建议并行度: 2（安全 checklist 与回滚 manifest 可并行）。

## 依赖关系总览

```text
T00 ─┬─> T02 ───────────────┬─> T07 ─> T11
     └─> T06                │
T01 ─┬─> T03 ─> T05 ───────┤
     ├─> T04 ─> T05 ───────┤
     └─> T06                │
T08 ─┬─> T02                │
     └──────────────────────┘
T04 ─> T09 ─> T10
T06 作为 T02–T10 的持续合并门
```

允许第一批并行：`T00`、`T01`、`T08`。
允许第二批并行：`T02` 的静态工作、`T03` 的纯单元设计、`T04` 协议设计、`T06` CI。
禁止错误并行：T07 不得早于 T02/T03/T04/T05；T10 不得早于 T09；实际 T11 台架不得早于全部 P0/P1 关闭。
