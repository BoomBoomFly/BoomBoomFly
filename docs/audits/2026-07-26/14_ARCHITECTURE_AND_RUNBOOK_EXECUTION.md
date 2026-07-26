# BBF-DOC-WAVE 架构与运行手册执行记录

> 报告状态：`IMPLEMENTED`
>
> 动态系统验证：`UNVERIFIED`
>
> production：`BLOCKED`

## 1. 当前仓库身份

| 字段 | 当前 checkout |
|---|---|
| Repository | `https://github.com/BoomBoomFly/BoomBoomFly.git` |
| Branch | `master` |
| HEAD before | `5a0e6edd4930474506a1046d414425893ebd800f` |
| Audit start time | `2026-07-26T17:29:50+08:00` |
| Working tree at start | `src/serial_driver_ros` 已有 dirty gitlink；本任务未触碰 |

旧审计中的分支、HEAD、主机路径和设备状态均只作为 `HISTORICAL_EVIDENCE`。本报告的静态结论以表中 checkout 为准。

## 2. Agent 分工与文件所有权

| Agent | 独占范围 | 工作类型 | 结果 |
|---|---|---|---|
| A — architecture | `docs/architecture/SYSTEM_OVERVIEW.md`、`DEPLOYMENT_TOPOLOGY.md`、`NODE_INVENTORY.md` | 文档写入 + 只读源码核对 | `IMPLEMENTED` |
| B — control/data flow | `docs/architecture/DATA_FLOW.md`、`CONTROL_AUTHORITY.md`、`FAULT_PROPAGATION.md` | 文档写入 + 只读 topic/FSM 核对 | `IMPLEMENTED` |
| C — runbooks | `docs/runbooks/*.md` 本轮四文件 | 文档写入；未执行 runbook | `IMPLEMENTED`；运行 `UNVERIFIED` |
| D — governance | 根治理建议稿与 `docs/governance/*.md` | 文档写入 | `IMPLEMENTED` |
| E — backlog | `docs/planning/*.md` 本轮五文件 | 文档写入；未创建远端 issue | `IMPLEMENTED` |
| main coordinator | 本报告及 `15_*`、`16_*` | 汇总、检查、修复文档问题 | `IMPLEMENTED` |
| independent reviewer | 全部本轮文档 | 只读独立审查 | 最终结论见 `15_*` |

任何 Agent 都未获得 `src/**`、manifest、脚本、workflow、evidence schema/receipt 或远端资源的写权限。T00、T01、T08 负责范围未分配给本任务。

## 3. 新增文件

### 架构

- `docs/architecture/SYSTEM_OVERVIEW.md`
- `docs/architecture/DEPLOYMENT_TOPOLOGY.md`
- `docs/architecture/NODE_INVENTORY.md`
- `docs/architecture/DATA_FLOW.md`
- `docs/architecture/CONTROL_AUTHORITY.md`
- `docs/architecture/FAULT_PROPAGATION.md`

### Runbook

- `docs/runbooks/VALIDATION_LEVELS.md`
- `docs/runbooks/SITL_ACCEPTANCE.md`
- `docs/runbooks/BENCH_ACCEPTANCE_DRAFT.md`
- `docs/runbooks/LIMITED_FLIGHT_ACCEPTANCE_DRAFT.md`

### 治理

- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODEOWNERS.draft`
- `docs/governance/REVIEW_POLICY.md`
- `docs/governance/RELEASE_POLICY.md`
- `docs/governance/DOCUMENT_AUTHORITY.md`

### Planning 与审计

- `docs/planning/BACKLOG.md`
- `docs/planning/MILESTONES.md`
- `docs/planning/DEPENDENCY_GRAPH.md`
- `docs/planning/DEFINITION_OF_DONE.md`
- `docs/planning/NEXT_PARALLEL_TASKS.md`
- `docs/audits/2026-07-26/14_ARCHITECTURE_AND_RUNBOOK_EXECUTION.md`
- `docs/audits/2026-07-26/15_DOCUMENT_CONSISTENCY_REVIEW.md`
- `docs/audits/2026-07-26/16_NEXT_WORK_ASSIGNMENT.md`

## 4. 架构文档完成情况

- Companion、PX4 flight controller、ROS 2、Micro XRCE-DDS Agent、RealSense、QGroundControl、开发主机和部署边界：`STATICALLY_VERIFIED`。
- Ubuntu 20.04、ROS 2 Foxy、PX4 v1.16.2 的当前设备状态：仅 `HISTORICAL_EVIDENCE`；本轮未动态核验。
- production 唯一候选 transport 为 PX4 uXRCE-DDS；MAVROS fallback：`BLOCKED`。
- `/dev/ttyTHS0` 仅允许单 DDS Agent 独占；运行时 owner guard：`PLANNED`。
- `/offboard_control_node` 是三个 PX4 控制输入的唯一允许 writer；运行时唯一性 guard：`PLANNED`。
- `/vision_to_dds_node` 是外部视觉输入的唯一允许 writer；坐标/时间/健康闭环：`BLOCKED`。
- 正式 mission arbiter/control-authority node：`PLANNED`，未描述为当前实现。
- 根 namespace 单机限制：`IMPLEMENTED`（架构决策）；多机：`BLOCKED`。
- topic/type/QoS/freshness/缺失行为与九类故障传播均已文档化；端到端 QoS、SITL 与 fault injection：`UNVERIFIED`。

## 5. Runbook 完成情况

| Level | 文档 | 文档状态 | 实际验收状态 |
|---|---|---|---|
| 0 静态/单元 | `VALIDATION_LEVELS.md` | `IMPLEMENTED` | 本轮 `UNVERIFIED` |
| 1 PX4 DDS SITL | `SITL_ACCEPTANCE.md` | `IMPLEMENTED` | `BLOCKED` / `UNVERIFIED` |
| 2 拆桨台架 | `BENCH_ACCEPTANCE_DRAFT.md` | `IMPLEMENTED` 的草案 | `UNVERIFIED` / `BLOCKED` |
| 3 有限实机 | `LIMITED_FLIGHT_ACCEPTANCE_DRAFT.md` | `IMPLEMENTED` 的草案 | `UNVERIFIED` / `BLOCKED` |

每级均包含权限边界、前置条件、角色、设备、软件/firmware/参数/transport identity、命令、预期、go/no-go、立即停止、evidence、rollback 和晋级门。Level 2/3 没有被描述为真实通过。本轮未执行 SITL、台架或实机。

## 6. 治理文档完成情况

- 贡献、分支、commit/PR、测试、生成物和硬件/PX4 变更规则：`IMPLEMENTED`。
- 安全披露、飞控安全、命令注入、设备权限、secret、firmware provenance 和公开 evidence 脱敏：`IMPLEMENTED`。
- 安全联系人未知，保留 `待维护者填写`；未虚构邮箱。
- `CODEOWNERS.draft` 仅使用角色占位，不能直接启用：`IMPLEMENTED`。
- P0/P1 reviewer、release identity、artifact SHA-256、rollback、production enable 权限和文档权威冲突处理：`IMPLEMENTED`。
- LICENSE 选择：`BLOCKED`，等待权利人/维护者/法律确认；本任务未选择许可证。

## 7. Backlog 完成情况

统一登记册的 44 个发现已作为规划输入；其中全部 9 个 P0 和 15 个 P1 均建立本地可执行 backlog。未创建 GitHub Issue、Milestone、Release 或 PR。M0–M6、依赖图、Definition of Done、责任角色、可并行和禁止并行关系均已记录。

## 8. 未决策事项

- 各飞行阶段发生 RC、DDS、odometry、status、battery、owner 或 vision loss 时，选择 Land、Position、保持 PX4 failsafe 或停止 ROS 输出的策略与 deadline：`BLOCKED`，需跨域安全评审。
- kill source、mapping、去抖、锁存、释放与重启后语义：`BLOCKED`。
- QGroundControl 独立监控链路：`UNVERIFIED`。
- Level 2 最低能量门和 Level 3 数值包线/法规/场地：`BLOCKED`。
- 根 LICENSE、安全联系人和真实 CODEOWNERS 账号：`BLOCKED` 或 `UNVERIFIED`。

## 9. 未验证事项

- 当前 PX4 参数、firmware artifact、DDS domain/client key/system identity；
- ROS 到 PX4 输入 QoS 和实际消费；
- `/fmu/out/rc_channels` firmware profile；
- graph guard、owner/lease、VehicleCommand ACK、PRESTREAM、fault lattice；
- 外部视觉坐标、时钟、quality/reset、EKF2 消费；
- SITL、拆桨台架、回滚实操和有限实机。

以上均保持 `UNVERIFIED`、`PLANNED` 或 `BLOCKED`，未从文档存在推断为通过。

## 10. 安全边界遵守

- Source packages modified: no
- PX4 firmware modified or built: no
- T00/T01/T08 files modified: no
- Hardware or `/dev` accessed: no
- Agent/MAVROS/Offboard/vision/sensor launch: no
- `/fmu/in/*` sent, arm or mode changed: no
- Remote modified, issue/release/PR created, or push: no
- Existing audit/evidence overwritten or deleted: no
