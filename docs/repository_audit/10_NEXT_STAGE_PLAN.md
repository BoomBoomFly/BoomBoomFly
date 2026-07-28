# 下一阶段任务计划

所有命令均为未来验收建议，不是本轮已执行记录。任何 Phase 2+ 动态命令必须先生成
exact command card 并获得相应授权。

## Phase 0：仓库冻结与基线确认

### P0-T01 冻结根与 nested Git 身份

- 优先级：P0
- 前置条件：独占审查窗口；禁止 fetch/checkout/reset/clean
- 涉及目录：根、`src/*/.git`、`workspace*.repos`、`.gitmodules`
- 验收命令：`git status --short --branch`；对 ledger 中每个 repo 执行
  `git -C <path> rev-parse HEAD`、`git -C <path> status --porcelain=v1 -uall`
- 预期输出：root/nested identity 与批准 ledger 完全一致；dirty receipt 全部可解释
- 风险：误操作可覆盖用户变更；必须只读
- 是否需要硬件：否
- 是否可以并行：否，作为所有任务的共同快照
- 建议负责线程：A

### P0-T02 决定 Offboard/vision canonical checkout

- 优先级：P0
- 前置条件：P0-T01；维护者确认 `722e05a…`/`b366db7…` 审批
- 涉及目录：`src/offboard_cpp`、`src/vision_to_dds`、`workspace.lock.repos`
- 验收命令：`git -C <path> rev-parse HEAD` 与 manifest exact SHA 比较；运行
  `python3 Scripts/test/verify_h0_production.py --workspace-root <isolated-root>`
- 预期输出：两个 HEAD 与 lock 相等；H0 JSON status PASS
- 风险：当前两个 checkout 虽 clean 但可能是用户刻意保留；不得擅自切换
- 是否需要硬件：否
- 是否可以并行：否
- 建议负责线程：A+C+E

### P0-T03 固定 PX4 v1.16.2/px4_msgs/firmware topic 契约

- 优先级：P0
- 前置条件：批准的 PX4 source/firmware artifact
- 涉及目录：`src/px4_msgs`、future PX4 lock、`docs/evidence/`
- 验收命令：比较 PX4 `dds_topics.yaml`、generated message hash、
  `git -C src/px4_msgs rev-parse HEAD`；静态断言 `vehicle_status_v1` 和 `rc_channels`
- 预期输出：board/firmware SHA、px4_msgs SHA、topic list、generator/toolchain hash 一一绑定
- 风险：若 `rc_channels` 缺失必须 NO-GO，不能用 mock 放宽
- 是否需要硬件：否
- 是否可以并行：可与 P0-T04 并行
- 建议负责线程：C

### P0-T04 冻结 DDS/MAVLink 权威与硬件禁区

- 优先级：P0
- 前置条件：ADR-0001
- 涉及目录：`config/profiles/`、`docs/architecture/`、`docs/runbooks/`
- 验收命令：`python3 Scripts/test/launch_guard/check_launch_safety.py ...`；
  `python3 Scripts/test/verify_serial_quarantine.py ...`
- 预期输出：DDS-only；MAVROS/old bringup/serial hardware writer production 引用为 0
- 风险：错误 allowlist 会放行真实设备入口
- 是否需要硬件：否
- 是否可以并行：是
- 建议负责线程：C+D+F

## Phase 1：纯软件构建门

### P1-T01 修复当前静态 P0/P1

- 优先级：P0
- 前置条件：Phase 0 全部通过；只修改 approved candidate
- 涉及目录：`src/offboard_cpp`、`src/vision_to_dds`
- 验收命令：H0 verifier；Offboard gate/RC/topic tests；vision frame/time/fault tests
- 预期输出：拒绝、stale、restart、clock fault、无 RC 时 `/fmu/in/*` publish count 均为 0
- 风险：安全门错误可能改变飞控动作；只做纯软件测试
- 是否需要硬件：否
- 是否可以并行：Offboard 与 vision 可分 repo 并行，接口冻结后合并
- 建议负责线程：C+E

### P1-T02 Clean isolated build

- 优先级：P1
- 前置条件：P1-T01；exact source/OS/toolchain lock
- 涉及目录：production 三包、`Scripts/build/`
- 验收命令：`bash Scripts/build/build_dds_only.sh --workspace-root <frozen-root> --output-root /tmp/<id>`
- 预期输出：3/3 packages build；所有输出仅 `/tmp`；无 source-tree artifact
- 风险：资源耗尽/环境漂移；先固定并发与磁盘预算
- 是否需要硬件：否
- 是否可以并行：否
- 建议负责线程：B+G

### P1-T03 Lint、unit、sanitizer 与 dependency checks

- 优先级：P1
- 前置条件：P1-T02
- 涉及目录：production packages、`test/`、`.github/`
- 验收命令：`bash Scripts/test/test_dds_only.sh ...`；独立 ASan/UBSan build；
  package boundary、evidence、receipt tests
- 预期输出：0 errors/failures/skips（skip 必须有审批）；sanitizer 0 finding；
  package boundary 3/3
- 风险：历史 14,598 计数不可作为固定阈值，应以 test inventory/hash 为准
- 是否需要硬件：否
- 是否可以并行：lint/unit/static 可以并行；sanitizer build 隔离
- 建议负责线程：E+G

### P1-T04 CI required-gate 设计

- 优先级：P2
- 前置条件：本地 Phase 1 通过
- 涉及目录：`.github/workflows/`、`test/ci_design/`
- 验收命令：workflow contract tests；GitHub required check readback
- 预期输出：PR/push 自动门；immutable actions；无硬件/网络控制端点；branch protection 生效
- 风险：误触发资源消耗或把手工证据 job 当 required
- 是否需要硬件：否
- 是否可以并行：是
- 建议负责线程：G

## Phase 2：SITL 集成门

### P2-T01 建立 exact SITL command card

- 优先级：P1
- 前置条件：Phase 1 全部 GO
- 涉及目录：new SITL profile、`docs/runbooks/SITL_ACCEPTANCE.md`、`tools/sitl_acceptance/`
- 验收命令：静态 validator 检查 command card、domain、端口、进程 allowlist 与 `/dev` 禁止项
- 预期输出：仅 PX4 SITL、单 Agent、单 writer；不含 `/dev/tty*`、MAVROS 或硬件 driver
- 风险：错误 transport 可能连接实机；必须用虚拟/UDP loopback 和独立 domain
- 是否需要硬件：否
- 是否可以并行：规格与 observer 可并行，实现串行
- 建议负责线程：C+F+G

### P2-T02 执行 formal SITL 场景

- 优先级：P1
- 前置条件：P2-T01 审批；进程/端口前置检查通过
- 涉及目录：PX4 SITL、Agent、Offboard、scenario catalog
- 验收命令：只执行已批准 command card；随后 timeline validator 与 writer census
- 预期输出：topic/QoS匹配；prestream/ACK/arm/mode/failsafe/restart/timeout 场景全部通过；
  teardown 后禁止进程为 0
- 风险：自动化若误连设备；command card 必须断言无设备路径
- 是否需要硬件：否
- 是否可以并行：场景可分批，不能共享同一 domain/port
- 建议负责线程：C+F+G

## Phase 3：单设备台架验证

### P3-T01 逐设备、人工批准台架

- 优先级：P1
- 前置条件：Phase 2 GO；两人复核；拆桨/执行器隔离；exact session approval
- 涉及目录：RealSense、RPLIDAR、serial、PX4 transport 各自独立 profile
- 验收命令：`<APPROVED_DEVICE_SPECIFIC_COMMAND_CARD>`，每次只启一个设备；
  结束后执行批准的日志/hash/进程/端口 owner 采集
- 预期输出：设备 identity、权限、baud/USB profile、重连/超时、资源占用与停止行为满足卡片
- 风险：物理动作、USB/串口争用、权限错误；首测禁止多子系统同时上电
- 是否需要硬件：是，必须人工明确批准
- 是否可以并行：否；不同设备也按顺序首次验证
- 建议负责线程：D，安全观察员 C/F

### P3-T02 拆桨飞控只读→有限 writer promotion

- 优先级：P0
- 前置条件：P3-T01 各单设备通过；回滚卡；kill/RC/ACK/failsafe 证据
- 涉及目录：PX4/Agent/Offboard approved profile
- 验收命令：先只读 command card；writer 阶段使用另一次明确批准的 exact card
- 预期输出：单 port owner、单 writer、无意外 arm/mode、拒绝路径 writer count 0、kill 可用
- 风险：飞控/执行器动作；任何 identity/参数不符立即 NO-GO
- 是否需要硬件：是，拆桨或安全台架
- 是否可以并行：否
- 建议负责线程：C+D+F

## Phase 4：完整系统集成

### P4-T01 GO/NO-GO 集成与回滚演练

- 优先级：P0
- 前置条件：Phase 0–3 全部 GO；变更冻结；场地/人员批准
- 涉及目录：全系统 approved profiles、release/rollback evidence
- 验收命令：`<APPROVED_FULL_SYSTEM_COMMAND_CARD>`；实时 writer/port/health
  observer；结束后 evidence validator 与 artifact SHA 检查
- 预期输出：
  - GO：identity 全匹配、单 control/vision owner、全部 freshness/ACK/kill/failsafe 通过
  - NO-GO：任何 duplicate writer、stale/clock reset、device identity drift、port conflict、
    rejected ACK、unexpected arm/mode 或日志缺失
- 风险：完整系统物理风险最高；必须有立即停止和恢复到冻结版本的回滚方案
- 是否需要硬件：是，单独授权
- 是否可以并行：否
- 建议负责线程：主协调代理 + C/D/F/G + 两名现场人员

## Promotion 规则

- 任一 Phase 失败，后续 Phase 不得开始。
- 历史 PASS 只有在 root/nested/toolchain/artifact hash 全匹配时才能复用。
- 任何 hardware access、firmware flash、parameter write、arm/mode/setpoint 都需要
  独立、精确、当次授权；“继续完成任务”不扩大授权范围。
