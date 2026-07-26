# BBF-SITL-SPEC-WAVE 实现交接

> 文档状态：`PLANNED`
>
> 本轮最强运行结论：`UNVERIFIED`
>
> PX4 SITL、ROS、Agent、硬件和远端操作：未授权

本交接按依赖顺序说明如何把离线规范接入未来正式 SITL。任何阶段只消费上游权威
输出，不复制或修改 T00、T01、T08 文件；接口或 identity 不一致时回到提供者修复。

## 阶段 1：消费 T00/T01/T08 输出

| 项目 | 要求 |
|---|---|
| required input | T00 workspace/dirty/toolchain baseline；T01 DDS-only package/launch boundary；T08 evidence/release/rollback schema |
| 预期文件 | 由各工作线发布的 machine-readable receipt、allowlist/profile 入口和 evidence schema；精确路径以其 handoff 为准 |
| 接口版本 | 各工作线冻结的非 moving 版本；场景侧 schema `1.0.0` |
| 可以开始的条件 | 三个 owner 均给出版本、hash、validator 和变更策略；同一 root/lock identity 可关联 |
| 禁止提前执行内容 | 不自建替代 receipt/allowlist/evidence schema；不启动 SITL、ROS、Agent；不改 scripts/workflows/evidence |
| 验收命令 | 运行各 owner 提供的只读/离线 validator，再运行本项目 catalog validator |
| 输出 artifact | identity adapter 设计、字段 mapping、未解析 dependency 清单 |
| 失败处理 | 保持场景 `BLOCKED`，记录 `BLOCKED_BY_T00`、`BLOCKED_BY_T01` 或 `BLOCKED_BY_T08`；不放宽 schema |

## 阶段 2：消费 T02 firmware endpoint manifest

| 项目 | 要求 |
|---|---|
| required input | PX4 v1.16.2 source/submodule/toolchain identity；只增加 `rc_channels` 的 firmware profile；endpoint manifest |
| 预期文件 | T02 权威 patch/manifest、generator 结果、SITL/FMuv3 artifact identity 和 raw evidence 路径 |
| 接口版本 | endpoint manifest 冻结版本；消息契约与锁定 `px4_msgs` 一致 |
| 可以开始的条件 | `/fmu/out/rc_channels` topic/type/QoS、PX4 writer identity、baseline topic regression 均有机器可读声明 |
| 禁止提前执行内容 | 不用 mock/手工 publisher代替 PX4；不加入 precision landing；不刷写；不访问设备 |
| 验收命令 | 对 manifest 做 schema/hash 校验；将 endpoint 字段与 scenario topic assertions 静态比对 |
| 输出 artifact | resolved endpoint-contract mapping；`BLOCKED_BY_T02` 可关闭候选清单 |
| 失败处理 | 保留 T02 blocker；不删除 RC 场景，不降低 source identity 要求 |

## 阶段 3：消费 T03 ACK/freshness/PRESTREAM 接口

| 项目 | 要求 |
|---|---|
| required input | ACK transaction/correlation、typed freshness/epoch、WAIT_INPUTS/PRESTREAM/MODE_PENDING 事件接口 |
| 预期文件 | T03 协议说明、事件码表、状态迁移表、配置单位/范围和单元测试结果 |
| 接口版本 | T03 冻结 event/FSM contract；scenario schema `1.0.0` |
| 可以开始的条件 | 所有 ACK result、fresh status、至少 1 s/20 samples PRESTREAM 语义和 bounded deadline 可机器观察 |
| 禁止提前执行内容 | 不以固定 sleep 推断 readiness；不把 unit ACK fixture 当 PX4 ACK；不改 Offboard 包 |
| 验收命令 | 用 synthetic JSONL 对每条状态边、拒绝码、timeout、correlation 执行离线 assertion |
| 输出 artifact | event adapter、normal/ACK fault 场景的 resolved assertion map |
| 失败处理 | 保持 `BLOCKED_BY_T03`；事件歧义返回 T03 owner，不能靠日志文本猜测 |

## 阶段 4：消费 T04 owner/lease/graph guard

| 项目 | 要求 |
|---|---|
| required input | owner/lease/sequence/epoch envelope；持续 graph guard；publisher/source identity diagnostics |
| 预期文件 | T04 protocol schema、node/endpoint allowlist、稳定拒绝码、单元/graph 测试结果 |
| 接口版本 | T04 冻结 authority contract |
| 可以开始的条件 | duplicate/lost/reconnected owner 和 writer、错误 domain/client key 均产生有界、稳定事件 |
| 禁止提前执行内容 | 不以单次 graph snapshot 证明持续唯一性；不启用 demo/animal production owner；不改 authority 包 |
| 验收命令 | 离线重放 owner loss、duplicate owner/writer、identity 冲突 timeline |
| 输出 artifact | authority/source/cardinality assertion adapter；`BLOCKED_BY_T04` 关闭候选 |
| 失败处理 | 任一 identity 或 cardinality 不可证明即 fail-closed；保留 blocker |

## 阶段 5：消费 T05 fault code 和恢复策略

| 项目 | 要求 |
|---|---|
| required input | Safety Reviewer 批准的 fault code、priority、状态×故障动作、deadline、latch、reset/health window |
| 预期文件 | T05 fault taxonomy、安全参数 schema、批准记录和测试 mapping |
| 接口版本 | T05 冻结 fault contract；每次修订必须显式版本化 |
| 可以开始的条件 | 每个适用场景有唯一批准的允许/禁止状态和恢复规则；争议项已由有权角色决定 |
| 禁止提前执行内容 | 实现者不得自行选择 Land、Position、PX4 failsafe 或停止输出；不得自动恢复 ACTIVE |
| 验收命令 | catalog dependency 检查；对批准事件向量运行 timeline assertion 和 result reporter |
| 输出 artifact | resolved fault scenario set、safety mapping、剩余 `SAFETY_DECISION_REQUIRED` |
| 失败处理 | 未批准格点保持 `BLOCKED_BY_T05` 与 `SAFETY_DECISION_REQUIRED`，不运行该场景 |

## 阶段 6：接入 T06 CI

| 项目 | 要求 |
|---|---|
| required input | 固定环境、DDS-only required jobs、artifact retention 和隔离 SITL job contract |
| 预期文件 | T06 权威 workflow/runner config、job interface 和日志 artifact 规则 |
| 接口版本 | T06 固定 runner/toolchain/profile 版本 |
| 可以开始的条件 | 本地等价命令可运行；负向 fixture 非零；runner 明确禁止真实设备 |
| 禁止提前执行内容 | 不修改 `.github/**`；不用 moving latest；不为绿色跳过 required 场景 |
| 验收命令 | compileall、所有 CLI `--help`、catalog validator、unittest、禁止内容扫描和 T06 本地等价入口 |
| 输出 artifact | CI adapter、JSON summaries、test logs、scenario/result mapping |
| 失败处理 | required job 失败即 `BLOCKED_BY_T06`；保留原始失败日志，禁止 warning-as-success |

## 阶段 7：正式运行隔离 PX4 SITL

| 项目 | 要求 |
|---|---|
| required input | 阶段 1–6 全绿；受管 orchestration；固定 PX4/Agent/domain/client/profile identity；批准场景集合 |
| 预期文件 | orchestration manifest、每次 run identity、JSONL timeline、raw logs、T08 evidence/rollback bundle |
| 接口版本 | scenario/event/result `1.0.0`；所有上游接口版本逐项记录 |
| 可以开始的条件 | 独立 test/control/safety/release reviewer 放行；无未解决规范或实现 P0/P1；获得明确 SITL 运行授权 |
| 禁止提前执行内容 | 不接触真实串口/硬件；不启动 MAVROS/旧 bringup；不把 mock 关掉 PX4 contract 门；不自动晋升台架 |
| 验收命令 | 只运行受管 orchestration 提供的 bounded 命令；随后执行 parse/assert/report 并验证 cleanup |
| 输出 artifact | 每场景 JSON result、完整 event timeline、source/topic/type/QoS/cardinality 证据、cleanup/rollback 结果 |
| 失败处理 | 停止当前隔离 run、保留 evidence、确认无 participant 残留；结果保持失败/阻塞并回到最早失效接口阶段 |

## 当前交接结论

本轮交付冻结的是离线接口和 synthetic fixture 的判定行为，不是 PX4 SITL
orchestration，也不是任何运行通过记录。正式实现最早从阶段 1 的接口消费开始。
