# BoomBoomFly 统一发现登记册

> 去重基线：六个分域报告共 64 个原始发现，经主协调按同一根因/验收门合并为 44 个唯一发现。
> 统计：P0=9，P1=15，P2=19，P3=1。
> production 建议：**禁止启用**。

## 统一表

| ID | 等级 | 模块 | 问题 | 证据 | 风险 | 建议 | 验收标准 | 工作量 | 依赖 | 阻塞 production |
|---|---|---|---|---|---|---|---|---|---|---|
| BBF-AUD-001 | P0 | 控制权 | 无运行时 graph guard，可重复启动 PX4 control writer | `BBF-SAFE-001`; `offboard_cpp/src/node.cpp:37-42`; launch files | 多 setpoint/mode/command writer 竞争 | 启动前+持续 graph guard，绑定 profile/identity | 三个 PX4 输入恰好一个批准 writer；重复/重连立即锁存 | L | AUD-010,018 | 是 |
| BBF-AUD-002 | P0 | 控制权 | mission owner 无 owner/lease/sequence/原子仲裁 | `BBF-SAFE-002`; `BBF-DDS-008`; `node.cpp:64-75` | 旧 owner/并发 owner 可夺权或混合命令 | 正式 arbiter + command envelope | 非当前/过期/乱序/重复 lease 消息发布到 PX4 的计数为 0 | L | AUD-001,017 | 是 |
| BBF-AUD-003 | P0 | Offboard | 启动/重连无 readiness 与显式 PRESTREAM，立即发布控制流/切模 | `BBF-SAFE-003`; `BBF-DDS-004`; `CtrlFSM.cpp:54-102,326-340,614-681` | 默认/陈旧 setpoint 预装，重连后危险恢复 | WAIT_INPUTS→PRESTREAM→MODE_PENDING→ACTIVE | ready 前 0 控制发布；连续≥1s 且≥20 有效样本后才请求模式 | L | AUD-004,006 | 是 |
| BBF-AUD-004 | P0 | PX4 command | 无 VehicleCommand ACK 事务；VehicleStatus 无 freshness | `BBF-SAFE-004`; `BBF-DDS-001,003`; `node.cpp:28-84`; `CtrlFSM.cpp:405-741` | PX4 拒绝/丢包时仍可能错误迁移 | ACK pending/result/timeout/correlation + fresh status 二次确认 | ACCEPTED 前不迁移；所有拒绝码和超时 fail-closed | M | AUD-003,006,015 | 是 |
| BBF-AUD-005 | P0 | RC/kill | production 无条件 `TEXT_RC`，无 RC 可绕过，kill 无独立锁存路径 | `BBF-SAFE-005`; `BBF-DDS-002,011`; `CMakeLists.txt:33-35`; `CtrlFSM.cpp:131-170` | 可绕过物理互锁并请求 arm/mode | production 移除 mock；fresh RC 强制门；kill 边沿/去抖/锁存 | 无 RC/失效/参数注入时 0 arm/mode；mock 不在 production 二进制 | M | AUD-012,019 | 是 |
| BBF-AUD-006 | P0 | 数据有效性 | Odom/landed 未初始化、首帧逻辑错误，setpoint/视觉数值校验不全 | `BBF-SAFE-006`; `BBF-DDS-003`; `input.hpp:90-106`; `input.cpp:218-245` | 未定义值或 NaN/Inf 进入控制条件/设定点 | 全成员初始化；统一 typed validity/freshness wrapper | sanitizer 通过；首帧不差分；异常值不产生 PX4 发布 | M | AUD-003,009 | 是 |
| BBF-AUD-007 | P0 | 故障处理 | RC/DDS/odom/status/battery loss 策略不统一，landing 中故障可取消降落 | `BBF-SAFE-007`; `CtrlFSM.cpp:235-318,520-575` | 故障时撤销安全动作或继续任务 | fault lattice、优先级、deadline、锁存、人工复位 | 每类故障/每飞行阶段有确定动作并经注入测试 | XL | AUD-004,005,014 | 是 |
| BBF-AUD-008 | P0 | 外部视觉 | ENU/NED/FLU/FRD 与 TF/frame 契约未证明 | `BBF-INT-001`; `BBF-DDS-010`; `vision_to_dds.cpp:24-31,275-338` | 错轴/姿态注入 EKF2 可导致估计与控制发散 | 坐标 ADR、纯函数、金样与 covariance 测试 | 轴向/90°/180°/四元数金样全通过；frame 不匹配不发布 | L | AUD-022 | 是（启用视觉时） |
| BBF-AUD-009 | P0 | 时间/视觉健康 | ROS/camera/TF/PX4 boot time 混用，quality/reset/freshness 固定或缺失 | `BBF-INT-002`; `BBF-DDS-007,010`; `vision_to_dds.cpp:307-338` | 陈旧/未来/重置测量被标为有效 | 统一时钟域、delay/reset/quality/freeze 门 | zero/backward/future/freeze/reset/non-finite 输入均 0 发布 | L | AUD-008,022 | 是（启用视觉时） |
| BBF-AUD-010 | P1 | 构建/launch 边界 | excluded/MAVROS/旧 bringup/mock 包仍被默认发现，旧 launch 可争用串口 | `BBF-DEP-001`; `BBF-BUILD-001`; `BBF-SAFE-009`; `BBF-INT-006` | 误构建/误启动禁止 writer 或占用 TELEM2 | DDS-only allowlist、权威 build/profile launcher、禁止项负向测试 | 权威入口只发现批准包；禁止节点/tty action 使测试失败 | M | AUD-025 | 是 |
| BBF-AUD-011 | P1 | 可复现性 | 四个 lock checkout 的有效 dirty 文件树无 patch/receipt | `BBF-DEP-002`; `01` 表 2.1 | 空白恢复无法得到当前实际能力 | 逐仓固化 base/diff/hash/用途/重放顺序 | 新目录重放后 content hash 一致；无需改现有 checkout | M | 无 | 是 |
| BBF-AUD-012 | P1 | PX4 firmware | 无 PX4 source/submodule/toolchain lock、`rc_channels` profile、SITL/FMUV3 artifact | `BBF-DEP-003`; `BBF-DDS-005`; `find` 无 `dds_topics.yaml`/`.px4` | RC 权威输入不存在，安全闭环无法成立 | 锁 v1.16.2 最小 patch，静态生成、SITL、FMUv3 build | PX4 唯一 publisher/真实 payload；patch/log/resource/artifact SHA 完整 | L | AUD-011,028,033 | 是 |
| BBF-AUD-013 | P1 | CI/分支治理 | 根仓库 workflow=0，master 未保护，无 ruleset/required checks | `BBF-BUILD-002`; `BBF-GOV-002`; `gh api` 只读结果 | 未测试提交可直接进入默认分支 | 固定依赖的 required CI + 管理员保护规则 | build/test/lint/manifest 失败阻止合并；规则可 API 复核 | M | AUD-010,032 | 是 |
| BBF-AUD-014 | P1 | 安全测试 | 关键 FSM、故障恢复、authority 没有行为/故障注入测试 | `BBF-BUILD-003`; `BBF-SAFE-010`; 当前 9 gtest 仅 RC/topic | P0 回归可在 9/9 继续通过时进入主线 | 可注入 clock/transport 的纯 FSM + 表驱动故障测试 | ACK/owner/RC/DDS/odom/status/battery/restart/NaN 场景闭合 | L | AUD-003..007 | 是 |
| BBF-AUD-015 | P1 | SITL/DDS | 无项目级 PX4 DDS SITL 正常/故障入口 | `BBF-BUILD-004`; repo 无受管 SITL acceptance | mock/静态测试不能证明 PX4 实际契约 | 固定 SITL/Agent/profile/source identity 的测试框架 | PX4 publisher/type/QoS/payload 可证明；故障场景有 bounded timeout | XL | AUD-012,014,018 | 是 |
| BBF-AUD-016 | P1 | Topic/QoS | QoS 未按方向集中；多数 topic 字面量分散；源码字符串测试不证明真实端点 | `BBF-DDS-006,012`; `BBF-BUILD-006`; `node.cpp:22-35` | discovery 可见但 PX4 input 不交付，版本回归静默 | exact topic/type/version/QoS 表和端点测试 | 关键 `/fmu/in/out` 全覆盖；不兼容 QoS 启动拒绝 | M | AUD-012,015 | 是 |
| BBF-AUD-017 | P1 | Offboard input | mode 与 trajectory 不是同一 fresh/owner/sequence 事务 | `BBF-DDS-008`; `input.cpp:289-319`; `CtrlFSM.cpp:175-231` | 旧 mode+新 setpoint 或字段冲突进入 PX4 | 原子 command envelope，联合 freshness/字段合法性 | 缺一、乱序、stale、冲突、双 publisher 全部 0 PX4 发布 | M | AUD-002 | 是 |
| BBF-AUD-018 | P1 | Transport identity | domain/namespace/client key/Agent/system ID 无统一配置源 | `BBF-DDS-009`; hard-coded identity; 无 machine profile | 连接错误 PX4、测试污染真实 graph | 单一 machine-readable profile 与启动一致性校验 | identity/domain/client key 冲突均 fail-closed；swarm 明确拒绝 | M | AUD-001,010 | 是 |
| BBF-AUD-019 | P1 | 安全配置 | dev/SITL/bench/prod 共用危险默认，参数无 schema/范围/profile | `BBF-SAFE-008`; `ctrl_param.yaml:1-42` | 默认 auto arm/非法 timeout 改变安全行为 | profile schema、单位/范围、配置 hash、production 禁动态危险参数 | 非法/跨 profile 参数使启动失败；默认 production 无 auto arm | M | AUD-005 | 是 |
| BBF-AUD-020 | P1 | 许可证 | 根工程/自有包授权及依赖 notice/维护状态链不完整 | `BBF-GOV-001`; `BBF-DEP-009`; GitHub `license=null` | release/交付缺合法分发依据 | 确认 LICENSE、包 license、THIRD_PARTY_NOTICES/SBOM | 每个发布组件 license/来源/义务/维护状态机器可查 | M | 维护者/法律确认 | 是 |
| BBF-AUD-021 | P1 | 运维/回滚 | 缺 firmware/SITL/台架/实机四级 runbook、故障排查与回滚演练 | `BBF-SAFE-011`; `BBF-GOV-003` | 历史只读取证被误当控制验收；故障无法恢复 | 分级 go/no-go、物理安全、证据、rollback manifest | 台架前桌面演练；台架实际回滚成功后才考虑实机 | L | AUD-012..015,033 | 是 |
| BBF-AUD-022 | P1 | 感知 profile | 无受管 sensor→TF→DDS→EKF2 profile 和当前参数 preflight | `BBF-INT-003`; 历史参数已过期 | 错设备/frame/EKF2 设置下启动视觉 | profile schema、current read-only parameter preflight、health gate | 条件不满足时无视觉 publisher；参数证据绑定时间/firmware | L | AUD-008,009,018 | 是（启用视觉时） |
| BBF-AUD-023 | P1 | RealSense | D435/T265 角色与稳定身份未编码，T265 缺失/掉线无降级 | `BBF-INT-004`; historical inventory | 枚举变化绑定错误设备或沿用陈旧视觉 | serial/VID:PID/udev identity、缺失/重枚举降级 | T265 不可用时清缓存且无 PX4 视觉 publisher | M | AUD-022 | 是（启用视觉时） |
| BBF-AUD-024 | P1 | 精准降落 | 可选 publisher 不构成独立 firmware/profile/validity 闭环 | `BBF-INT-005`; `vision_to_dds.cpp:129-163` | stale/低置信目标被作为有效降落目标 | 独立 precision-landing profile，默认不可误启 | baseline 无 publisher；独立 SITL 验证 target freshness/covariance/quality | L | AUD-008,009,012,022 | 是（仅精降能力） |
| BBF-AUD-025 | P2 | Git 元数据 | 根索引含无 `.gitmodules` 映射的 `serial_driver_ros` gitlink | `BBF-DEP-004`; `git submodule status` exit 128 | 统一仓库审计/恢复失败 | 评审后补映射或移除历史 gitlink | recursive submodule status 返回 0 且不引入历史 control path | S | AUD-010 | 否 |
| BBF-AUD-026 | P2 | checkout 策略 | 文档称 detached lock 恢复，但多项当前在分支上 | `BBF-DEP-005`; `01` checkout 表 | “当前树”与“恢复树”策略含混 | 明确 lock=detached、development=branch 的状态机/receipt | verify 输出能区分且文档命令一致 | S | AUD-011 | 否 |
| BBF-AUD-027 | P2 | moving dependency | `../communication` 缺失且无实验 HEAD receipt | `BBF-DEP-006`; workspace verify blockers=5 | 实验结果无法绑定通信代码 | origin/HEAD/dirty/time/purpose receipt，缺失 fail-closed | 每次实验/发布有机器可验 receipt | S | AUD-018 | 否 |
| BBF-AUD-028 | P2 | 环境复现 | lock 只锁源码，不锁 ROS/system/toolchain 宽依赖 | `BBF-DEP-007`; installer scope | 空白环境构建差异被误判源码缺陷 | 固定容器/系统依赖/BOM/tool versions | 冷环境核心 build/test 可复现 | L | AUD-011 | 是（发布链） |
| BBF-AUD-029 | P2 | 恢复健壮性 | 中断重入/半成品/并发恢复未有自动化证明 | `BBF-DEP-008`; installer review | 恢复中断留下难诊断目录 | 临时目录/原子落盘/lock/中断测试 | kill/retry/并发/错误 origin 全部幂等且 fail-closed | M | AUD-011 | 否 |
| BBF-AUD-030 | P2 | launch/config 测试 | 仅语法检查，无默认安全/allowlist/graph 静态断言 | `BBF-BUILD-007` | launch 回归可加入 writer/mock/硬件 action | launch_testing/AST/YAML schema 和负向测试 | 禁止 action、危险默认、缺参数均阻止 CI | M | AUD-010,013 | 是 |
| BBF-AUD-031 | P2 | 包依赖 | package.xml/CMake 与直接源码依赖存在缺失/多余 | `BBF-BUILD-008` | 最小环境或打包时偶发失败 | 依赖扫描与最小环境 build | 直接依赖显式、无不必要 production dependency | S | AUD-013 | 否 |
| BBF-AUD-032 | P2 | 质量门 | vision lint 失败；无统一 Werror/static analysis/sanitizer | `BBF-BUILD-009`; 本轮 3/6 lint fail, 287 diagnostics | 质量/UB 回归不阻止合并 | 先修 lint，再分层加 Werror/clang-tidy/cppcheck/ASan | 核心 CI test-clean；工具版本固定 | M | AUD-013 | 否 |
| BBF-AUD-033 | P2 | 证据/artifact | build/release/evidence 无统一不可变机器可验 provenance | `BBF-BUILD-011`; `BBF-GOV-006` | 历史通过与当前 artifact 混淆，回滚不可追溯 | evidence schema、raw logs、SHA、supersession、rollback manifest | source/environment/command/result/artifact 单链可验 | M | AUD-013,021 | 是（发布/台架前） |
| BBF-AUD-034 | P2 | 可观测性 | 无结构化 safety/vision health、稳定错误码和资源上限 | `BBF-SAFE-012`; `BBF-INT-009` | 无法机器验收；长期运行/故障难定位 | fault taxonomy、diagnostics、age/owner/lease/resource metrics | 测试按错误码/事件线验收；资源有界 | M | AUD-007,009 | 否 |
| BBF-AUD-035 | P2 | RPLIDAR | model/baud/device/TF 未受管且无稳定身份 | `BBF-INT-007` | 设备误绑定和不可复现 | 保持 production 禁用；未来独立 sensor profile | 未启用时无 device action；启用需 udev/TF/掉线测试 | M | AUD-010 | 否 |
| BBF-AUD-036 | P2 | USB/VPU | USB Camera/VPU 为个人路径/枚举驱动的历史实验 | `BBF-INT-008` | 资源争用、磁盘写入和后端漂移 | 保持 excluded；如重启项目另立 profile | production 静态扫描无相关 action | S | AUD-010 | 否 |
| BBF-AUD-037 | P2 | 项目治理 | 缺 CONTRIBUTING/SECURITY/CODEOWNERS | `BBF-GOV-004` | 安全披露无渠道，高风险变更缺领域 reviewer | 新增治理文档与路径 owner | 控制/PX4/感知/运维变更要求对应 review | S | AUD-013 | 是（治理门） |
| BBF-AUD-038 | P2 | 状态文档 | handoff 单体承担历史/当前/计划且已与远端 master 漂移 | `BBF-GOV-005`; handoff base vs API master | 新代理基于旧事实工作 | 拆分机器基线、evidence index、roadmap；保留 handoff 导航 | 自动检测 HEAD/profile/日期过期 | M | AUD-033 | 否 |
| BBF-AUD-039 | P2 | 信息披露 | public evidence 含个人路径、硬件 serial、部署拓扑/邮箱 | `BBF-GOV-007`; 严格扫描未发现 token/private key | 定向攻击、设备跟踪与社会工程 | 发布前脱敏策略；凭据扫描持续化 | public evidence 不含无必要唯一标识；secret scan required | S | AUD-013 | 否；阻塞公开 evidence |
| BBF-AUD-040 | P2 | 架构文档 | 缺数据流、节点、部署、时间域和故障传播图 | `BBF-GOV-008` | writer/transport/frame/ownership 易混淆 | 从 ADR/profile 自动或半自动生成图 | 图与 topic/profile schema 链接，CI 检查引用 | M | AUD-018,022 | 否 |
| BBF-AUD-041 | P2 | 过期入口 | 恢复说明含非权威 clone URL、空占位和历史脚本 | `BBF-GOV-009` | clone 错远端或误用旧入口 | 标记 canonical URL/支持状态；占位 fail-closed | 文档命令 dry-run 与仓库 identity 门通过 | S | AUD-010 | 否 |
| BBF-AUD-042 | P2 | 任务治理 | Issues 被关闭，无 milestone/DoD/依赖与 owner | `BBF-GOV-010`; GitHub API `has_issues=false` | 高优先级依赖漏做/错误并行 | 启用或选择等价 tracker，建立 milestone/DoD | 每个 P0/P1 有 owner、依赖、测试、证据和关闭条件 | S | AUD-013 | 否 |
| BBF-AUD-043 | P2 | 文档质量 | 链接、命令、URL 与时效无自动检查 | `BBF-GOV-011` | 漂移不阻止合并 | link checker、command dry-run、URL/HEAD freshness CI | 故意破坏链接/命令/identity 时 CI 失败 | S | AUD-013,041 | 否 |
| BBF-AUD-044 | P3 | C++ 工具链 | 核心包 C++ 标准设置不统一/兼容边界未说明 | `BBF-BUILD-010` | 跨环境行为和未来共享库漂移 | 统一标准或记录包级理由 | 固定工具链下标准可审计且 CI 一致 | S | AUD-028 | 否 |

## P0 详细说明

### BBF-AUD-001 — 控制 writer 唯一性没有运行时强制

- 触发条件：重复启动 `offboard_control_node`、旧 launch/namespace 混入、Agent/节点重连。
- 实际结果：源码未检查 publisher 数量或身份；ADR 只是规则。
- 预期结果：profile 中 PX4 trajectory/mode/command 各有且仅有一个批准 writer。
- 修复与验收：持续 graph guard，不只启动时快照；发现额外 writer 时撤销 authority、锁存且禁止自动恢复。工作量 L。

### BBF-AUD-002 — mission owner 无 lease/仲裁

- 触发条件：demo/animal/未来 mission 并发、owner crash/restart、旧消息重放或网络分区恢复。
- 实际结果：三个 `/offboard/*` topic 没有 owner ID、lease、sequence、deadline 或原子配对。
- 预期结果：仅当前 arbiter lease 可驱动 Offboard。
- 修复与验收：command envelope + heartbeat/sequence；非当前、乱序、重复、过期消息全部 0 PX4 发布。工作量 L。

### BBF-AUD-003 — 启动、重连和 Offboard 预热协议缺失

- 触发条件：Offboard 先于 PX4/Agent 启动、RC 快速切换、Agent/PX4 重启、内部命令过早到达。
- 实际结果：50 Hz FSM 启动即发布默认控制流并可请求 ALTCTL/POSCTL；连续发布只是偶然，不是 readiness 门。
- 预期结果：所有权威反馈和 authority ready 后才 PRESTREAM。
- 修复与验收：显式阶段；任一 freshness 中断清零；连续≥1 秒且≥20 个有效样本后才发 mode request。工作量 L。

### BBF-AUD-004 — VehicleCommand ACK 与 fresh 状态闭环缺失

- 触发条件：preflight 拒绝、mode 不支持、ACK 丢失/迟到/乱序、PX4 reboot、陈旧 VehicleStatus。
- 实际结果：没有 ACK subscription/result 处理，迁移只依赖无 freshness 的状态或超时。
- 预期结果：ACK 事务与 PX4 状态一致性共同决定迁移。
- 修复与验收：处理 ACCEPTED/IN_PROGRESS/所有拒绝码；错误 target/command、超时和重复 ACK fail-closed；SITL source 必须是 PX4。工作量 M。

### BBF-AUD-005 — RC authority/mock/kill 安全门不闭合

- 触发条件：RC 从未收到、`TEXT_RC` 参数写入、误启动 mock、signal loss、kill 开关抖动。
- 实际结果：生产目标无条件编译 mock override；自动起飞在无 RC 时跳过检查；历史 kill 参数不是当前实现证据。
- 预期结果：fresh physical RC 是任何 arm/Offboard 的强制条件，kill 独立最高优先级锁存。
- 修复与验收：production 二进制无 mock；所有无效 RC 场景 arm/mode 发布为 0；kill 边沿/去抖/人工复位测试通过。工作量 M。

### BBF-AUD-006 — 未初始化值和异常数值可进入控制链

- 触发条件：首帧 odometry、节点先于 telemetry、NaN/Inf setpoint、clock jump、非法 quaternion。
- 实际结果：成员未初始化，feed 先覆盖 timestamp 再判断首帧；RC 之外的数值验证不完整。
- 预期结果：所有输入有首帧、finite/range/schema/freshness 状态。
- 修复与验收：显式初始化；首帧不差分；ASan/UBSan/fuzz 与异常消息测试全部不产生 PX4 输出。工作量 M。

### BBF-AUD-007 — 故障优先级、降级和恢复不一致

- 触发条件：飞行/着陆中 RC、DDS、odom、status、battery 或 owner 丢失。
- 实际结果：不同状态处理分散；着陆时丢 RC/odom 可取消 landing；battery stale 无策略。
- 预期结果：按飞行状态、PX4 failsafe 能力和故障严重度选择确定动作，默认不自动恢复。
- 修复与验收：fault lattice + bounded deadline + fault-latched；对每状态/故障组合做 SITL 注入并证明人工复位。工作量 XL。

### BBF-AUD-008 — 外部视觉坐标/frame 契约未证明

- 触发条件：RealSense frame 与默认 TF 不同、参数旋转错误、姿态/covariance 未同构变换。
- 实际结果：输出标记 FRD，但实现和上游 frame 没有数学/测试闭环。
- 预期结果：输入 frame 到 PX4 `VehicleOdometry` 字段的转换有唯一规范。
- 修复与验收：纯函数金样覆盖轴向、90/180 度、四元数和 covariance；frame 不匹配时无 publisher。工作量 L。

### BBF-AUD-009 — 时间、reset、quality 与视觉 freshness 未闭合

- 触发条件：TF freeze、相机重启、ROS time zero/backward/future、PX4 reboot、NaN/Inf。
- 实际结果：ROS now 与 TF stamp 直接填入 PX4 字段，quality/reset 固定，时钟域不明。
- 预期结果：sample/publish time、epoch、最大 delay、reset/quality 有明确来源与门。
- 修复与验收：时间 ADR；所有异常时间/健康场景 publish count=0；SITL/EKF2 delay/innovation 证据。工作量 L。

## P1 详细说明

### BBF-AUD-010 — DDS-only 包/launch 边界未技术强制

- 触发条件：裸 `colcon build`、误用旧 launch 或硬件入口。
- 实际结果：12 个明确排除包仍被发现；旧 MAVROS/serial launch 可争用 `/dev/ttyTHS0`。
- 修复与验收：权威 allowlist + launch 静态负向测试；禁止包/action 出现即非零退出。工作量 M。

### BBF-AUD-011 — dirty checkout 无可重建 receipt

- 触发条件：新主机/新工作区恢复、checkout 损坏或维护者交接。
- 实际结果：HEAD/origin 匹配，但 mode/deletion/untracked 差异不在 lock。
- 修复与验收：保持现有树不动，在隔离目录重放 patch/content receipt 后 hash 一致。工作量 M。

### BBF-AUD-012 — PX4 `rc_channels` firmware profile 缺失

- 触发条件：任何现有 PX4 v1.16.2 default firmware 启动 Offboard。
- 实际结果：仓库无 PX4 source、patch、生成物、SITL 或 `.px4` artifact；历史实机 topic 缺失。
- 修复与验收：锁定 source/submodule/toolchain，最小 patch，SITL 真实 PX4 publisher，FMUv3 build/hash；不刷写。工作量 L。

### BBF-AUD-013 — 无 CI/required checks/分支保护

- 触发条件：直接 push/merge 未验证提交。
- 实际结果：GitHub API 确认 master unprotected、workflow=0、ruleset=[]。
- 修复与验收：固定依赖 CI；管理员启用保护；故意破坏 build/test/lint/manifest 时合并被阻止。工作量 M。

### BBF-AUD-014 — 安全 FSM 与故障注入测试缺失

- 触发条件：控制状态机修改、重连、拒绝命令、owner/telemetry loss。
- 实际结果：9 个 gtest 只覆盖 RC parser 和 topic 文本契约。
- 修复与验收：抽离纯 FSM/clock/transport；完整状态表与 fault injection required CI。工作量 L。

### BBF-AUD-015 — 项目级 PX4 DDS SITL 缺失

- 触发条件：接口/firmware/QoS/FSM 变更。
- 实际结果：没有受管 SITL 入口，无法证明 PX4 实际消费/发布。
- 修复与验收：固定 SITL/Agent/profile；正常与故障场景可重复，PX4 source identity 和 payload 可证明。工作量 XL。

### BBF-AUD-016 — topic/type/version/QoS 契约不完整

- 触发条件：RMW 默认、PX4 generator、消息版本或 topic 重命名变化。
- 实际结果：同一 QoS 用于不同方向，vision 使用不同默认；测试只匹配源文本。
- 修复与验收：集中端点表，静态+SITL exact assertion；不兼容 QoS 时启动拒绝。工作量 M。

### BBF-AUD-017 — mode 与 trajectory 非原子事务

- 触发条件：单 topic 丢包、owner 启动顺序、旧 mode+新 setpoint、字段冲突。
- 实际结果：分别缓存，仅 trajectory freshness 可触发迁移。
- 修复与验收：同 lease/sequence/time window 的原子 envelope；缺一或冲突时 0 PX4 发布。工作量 M。

### BBF-AUD-018 — Transport/vehicle identity 配置分散

- 触发条件：多 Agent、多 PX4、共享主机、domain/namespace 变化。
- 实际结果：无 machine profile，system/component hard-coded，swarm launch 无 transport 契约。
- 修复与验收：统一 domain/client key/namespace/Agent/vehicle identity；冲突测试 fail-closed。工作量 M。

### BBF-AUD-019 — 安全参数无 profile/schema

- 触发条件：非法负 timeout、错误高度/电池/RC 映射、development 配置进入 production。
- 实际结果：默认 auto arm，共用 YAML，无范围/单位/启动校验。
- 修复与验收：profile-specific schema/hash；非法值或缺字段阻止启动；production 默认 auto arm=false。工作量 M。

### BBF-AUD-020 — 许可证与第三方义务链不完整

- 触发条件：公开 release、镜像、firmware 配套包或商业交付。
- 实际结果：根 GitHub license=null，自有包/组合分发依据不完整。
- 修复与验收：维护者/法律确认 LICENSE、包 license、notices、SBOM、维护/弃用状态。工作量 M。

### BBF-AUD-021 — 四级验收、故障排查和回滚 runbook 缺失

- 触发条件：从 SITL 升级台架/实机，或 firmware/参数/transport 故障。
- 实际结果：只有历史 output-only 证据，无正式 promotion/stop/rollback 流程。
- 修复与验收：静态→SITL→拆桨台架→有限实机逐级门；台架实际回滚成功才可升级。工作量 L。

### BBF-AUD-022 — 感知/EKF2 受管 profile 缺失

- 触发条件：启动 `vision_to_dds`、设备/frame/当前 EKF2 参数不满足。
- 实际结果：历史参数快照已过期，无 machine preflight。
- 修复与验收：sensor→TF→DDS→EKF2 profile；任何条件不满足时无 PX4 vision publisher。工作量 L。

### BBF-AUD-023 — T265 稳定身份和缺失降级未实现

- 触发条件：T265 缺失、掉线、USB 重枚举或 D435/T265 角色互换。
- 实际结果：历史枚举未发现 T265，项目配置未编码角色。
- 修复与验收：serial/VID:PID/udev identity；掉线清缓存并撤销 vision authority。工作量 M。

### BBF-AUD-024 — 精准降落不是独立已验收能力

- 触发条件：参数误启、目标 TF stale/低置信、baseline firmware 无 topic。
- 实际结果：默认关闭是安全正项，但启用路径缺 firmware/profile/validity/SITL。
- 修复与验收：保持 baseline 无 publisher；独立 profile 通过 target freshness/covariance/quality 与 SITL。工作量 L。

## 原始发现去重映射

- DEP：001→AUD-010；002→011；003→012；004→025；005→026；006→027；007→028；008→029；009→020。
- BUILD：001→010；002→013；003→014；004→015；005→008/009；006→016；007→030；008→031；009→032；010→044；011→033。
- DDS：001→004；002→005；003→004/006；004→003；005→012；006→016；007→009；008→002/017；009→018；010→008/009；011→005；012→016。
- SAFE：001→001；002→002；003→003；004→004；005→005；006→006；007→007；008→019；009→010；010→014；011→021；012→034。
- INT：001→008；002→009；003→022；004→023；005→024；006→010；007→035；008→036；009→034。
- GOV：001→020；002→013；003→021；004→037；005→038；006→033；007→039；008→040；009→041；010→042；011→043。
