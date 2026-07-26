# 下一批分阶段并行任务建议

> 文档状态：`PLANNED`
>
> 本文件只建议后续工作，不直接执行、不创建真实 Issue/PR/Milestone。当前 production
> 为 `BLOCKED`；任何硬件、firmware flash、参数写入、arm、mode 或 `/fmu/in/*`
> 实机发送都不在这些建议的默认授权内。

## 调度前提

- Wave 0 的 T00（baseline）、T01（DDS-only boundary）、T08（evidence schema）已有独立
  owner；A–F 不得修改其 scripts、schema、receipt、package allowlist 或 evidence
  基础设施。
- 同一文件同一时间只允许一个 owner。接口 schema 先评审冻结，其他工作线再消费。
- A–F 的设计和失败测试可提前；任何运行 promotion 必须等待
  [依赖图](DEPENDENCY_GRAPH.md) 的硬依赖。
- 所有输出先保持 `PLANNED`、`PARTIALLY_IMPLEMENTED`、`UNIT_TESTED` 或
  `UNVERIFIED`；只有实际满足对应层级证据才可使用更强状态。

## 工作线 A：PX4 firmware profile

- **对应任务：** `BBF-TASK-012`，并支持 `016`、`018`
- **前置条件：** T00 锁定 PX4 v1.16.2 source/submodule/toolchain；T08 schema 可用；
  `px4_msgs`/PX4 `RcChannels` 字段一致。
- **是否可以立即开始：** `BLOCKED`；可立即做只读字段对照和最小 patch 设计，不能做
  可验收构建，直到 T00/T08 完成。
- **与其他工作线的冲突文件：** PX4 `dds_topics.yaml`、firmware patch、transport
  profile 与 endpoint manifest；A 是这些文件唯一 writer。不得修改 T00/T08 资产。
- **建议并行度：** 2；一人做生成/endpoint，一人做可复现 build/resource 记录；
  patch 最终合并由单一 PX4 Maintainer。
- **禁止并行的任务：** 同时维护两个不同 `rc_channels` patch；在 endpoint 未冻结时由
  B/F 各自复制 topic/QoS 常量；precision landing patch 与 baseline patch 混合。
- **预计输出：** 最小 PX4 patch、生成物检查、SITL RC payload、FMUv3 build log、
  resource margin、`.px4` SHA-256。
- **验收门：** `/fmu/out/rc_channels` 恰有一个 PX4 publisher，type/QoS 正确且是真实
  PX4 payload；baseline 无精降 topic；artifact provenance 完整。
- **是否允许修改功能包：** 允许修改经批准的隔离 PX4 firmware profile；不修改 ROS 2
  功能包。
- **是否需要硬件授权：** 否；本工作线不刷写、不访问串口。

## 工作线 B：Offboard ACK/freshness/PRESTREAM

- **对应任务：** `BBF-TASK-003`、`004`、`006`
- **前置条件：** T01 受控 build 入口；ACK endpoint/epoch 语义评审；与 C 冻结
  Offboard input/authority 边界。
- **是否可以立即开始：** 是，可立即开始纯单元失败测试、缓存初始化和 typed freshness；
  SITL 验收等待 A/F。
- **与其他工作线的冲突文件：** `offboard_cpp` 的 node/FSM/input/topic/config/test；
  B 是这些核心事务文件的临时唯一 owner。C 只能先做独立 arbiter/schema，不同时修改
  同一 Offboard 文件。
- **建议并行度：** 2；freshness/validity 与 ACK transaction 可并行，FSM/PRESTREAM
  汇合串行。
- **禁止并行的任务：** ACK、PRESTREAM、owner/lease 三组人员同时改同一 FSM；
  在 freshness wrapper 未冻结时实施 fault lattice；用 mock ACK 关闭 SITL 门。
- **预计输出：** initialized typed cache、ACK pending/result/correlation、fresh status、
  WAIT_INPUTS/PRESTREAM/MODE_PENDING、单元与 sanitizer 测试。
- **验收门：** readiness 前 PX4 控制发布为 0；至少 1 秒且至少 20 有效样本后请求 mode；
  ACCEPTED + fresh status 才迁移；所有拒绝/超时 fail-closed。
- **是否允许修改功能包：** 是，需明确授权修改 `src/offboard_cpp`；本 BBF-DOC-WAVE
  没有该授权。
- **是否需要硬件授权：** 否；单元/SITL 阶段禁止硬件。

## 工作线 C：owner/lease/graph guard

- **对应任务：** `BBF-TASK-001`、`002`、`017`、`018`
- **前置条件：** T01 package/launch 边界；authority ADR 和 command envelope 评审；
  与 B 冻结 Offboard consumer 接口。
- **是否可以立即开始：** 是，可立即进行协议、schema、graph-test 设计；Offboard 集成
  必须等待接口冻结。
- **与其他工作线的冲突文件：** 新 authority package、production launcher、command
  envelope 和 Offboard consumer adapter；C 拥有前 3 类，B 拥有核心 FSM。
- **建议并行度：** 3；协议、持续 graph guard、owner/lease fault tests 分开开发，
  consumer integration 串行。
- **禁止并行的任务：** 两套 competing envelope；一次性 graph snapshot 冒充持续 guard；
  C 与 B 同时改同一 Offboard input 文件；启用 swarm。
- **预计输出：** authority ADR/schema、arbiter、lease/sequence/deadline、graph guard、
  active-owner diagnostics、双 writer/owner/reconnect tests。
- **验收门：** 非当前/过期/乱序 lease 到 PX4 发布计数为 0；任何 writer/identity 基数
  冲突阻止 ACTIVE；恢复需人工授权。
- **是否允许修改功能包：** 是，可新增经评审 authority 包并对 Offboard 做最小接口适配；
  需单独功能开发授权。
- **是否需要硬件授权：** 否；只做软件/SITL。

## 工作线 D：CI 和质量门

- **对应任务：** `BBF-TASK-013`，支持所有任务 DoD
- **前置条件：** T00 固定工具链；T01 权威 package 入口；T08 evidence artifact 字段。
- **是否可以立即开始：** `BLOCKED` 于前三项接口；可立即设计 job graph 和负向 fixtures，
  但不得抢改 T01/T08 文件。
- **与其他工作线的冲突文件：** `.github/workflows/**`、CI config/scripts、quality
  baselines；D 独占这些文件，消费而不修改 T00/T01/T08 输出。
- **建议并行度：** 3；manifest/boundary、build/test、lint/docs/security jobs 可并行。
- **禁止并行的任务：** 多人同时改同一 workflow；用 moving latest；为绿色放宽 lint/
  tests；未经授权修改远端 branch rules。
- **预计输出：** fixed-environment CI、core build/test、lint/static/sanitizer、docs/link/
  secret/license checks、原始 artifact retention。
- **验收门：** 故意破坏 manifest/topic/allowlist/test/link/secret fixture 均非零；
  required setting 由管理员只读 API 复核。
- **是否允许修改功能包：** 默认不允许；修复被 CI 暴露的功能包问题需单独任务/owner。
- **是否需要硬件授权：** 否；runner 不得直连硬件。

## 工作线 E：视觉坐标和时间契约

- **对应任务：** `BBF-TASK-008`、`009`、`022`、`023`；`024` 延后
- **前置条件：** T01 边界；C 的 profile/authority 接口；上游 frame/安装外参由维护者
  确认。
- **是否可以立即开始：** 是，可立即开始 ADR、纯函数和离线金样；EKF2/current-device
  验收为 `BLOCKED`，需要后续只读授权。
- **与其他工作线的冲突文件：** `vision_to_dds` source/tests、frame/time ADR、
  sensor profile；E 独占这些文件。普通视觉完成前不创建精降实现分支。
- **建议并行度：** 2；坐标数学与时间/health 测试并行，publisher/profile 集成串行。
- **禁止并行的任务：** 未冻结 frame 就开发 device profile；普通视觉与 precision
  landing 同时改 publisher；把历史参数或设备 serial 当 current。
- **预计输出：** frame/time ADR、纯函数金样、reset/quality/freshness gate、
  perception profile、sensor missing/re-enumeration tests。
- **验收门：** frame mismatch、zero/backward/future/freeze/reset/NaN 输入发布计数为 0；
  普通视觉 SITL/EKF2 通过后才建议 TASK-024。
- **是否允许修改功能包：** 是，需明确授权修改 `src/vision_to_dds`；本 BBF-DOC-WAVE
  没有该授权。
- **是否需要硬件授权：** 离线/SITL 不需要；当前相机、设备 identity、PX4 参数和真实
  EKF2 验收需要单独只读/硬件授权。

## 工作线 F：SITL 验收框架

- **对应任务：** `BBF-TASK-014`、`015`、`016`
- **前置条件：** A 的 firmware profile；B/C 的测试接口；D 的 CI；transport identity
  固定。
- **是否可以立即开始：** 可立即建立无运行副作用的 orchestration schema、场景清单和
  event parser；正式运行验收为 `BLOCKED`，等待 A–D。
- **与其他工作线的冲突文件：** SITL orchestration、scenario definitions、event
  assertions、CI SITL job；F 独占这些文件，endpoint manifest 由 A 产出、F 只消费。
- **建议并行度：** 3；正常场景、故障场景、evidence parser 可并行，基础 orchestration
  和最终集成串行。
- **禁止并行的任务：** 在 A profile 前用 mock 替代 PX4；在 B/C 接口变化时冻结
  assertions；用长固定 sleep 掩盖 race；接触真实串口。
- **预计输出：** 固定 PX4/Agent/domain profile、正常/故障 scenario、source identity
  assertions、bounded event timeline、CI integration。
- **验收门：** 每场景独立可重复；PX4 publisher/reader 可证明；RC/DDS/owner/status/
  battery loss、ACK result、restart、double-writer、time jump、mock 混入全部闭合。
- **是否允许修改功能包：** 默认只修改测试/orchestration；为测试 hook 改功能包需与
  B/C owner 协调并单独 review。
- **是否需要硬件授权：** 否；SITL 必须使用隔离 UDP/domain，不访问 `/dev`。

## 建议波次与人员安排

| 波次 | 主工作线 | 建议总并行度 | 进入条件 | 退出门 |
|---|---|---:|---|---|
| Wave 0 | T00、T01、T08 | 3 | 文件 ownership 已确认 | M0 baseline review |
| Wave 1 | A 的静态设计、B 单元、C 协议、D CI 设计、E 金样、F 场景 schema | 6 个工作线，每线不超过上述并行度 | 不交叉修改 T00/T01/T08 | 接口冻结 review |
| Wave 2 | A build/SITL、B/C 集成、D jobs、E publisher health、F orchestration | 受冲突文件限制动态降至 4–5 | Wave 1 schema 通过 | M1 + M2 unit gates |
| Wave 3 | F 正常/故障 SITL；E 普通视觉 SITL | 3 | A–D 依赖通过 | M3/M4 `SITL_VERIFIED` |
| Wave 4 | Level 2 runbook 最终化与授权准备 | 2（operator + reviewer） | 全部 P0 和适用 P1 关闭 | M5 go/no-go |

Wave 1 的“6 个工作线”是组织建议，不表示当前工具并发槽或同一仓库允许 6 个 Agent
同时写文件；实际调度必须服从平台并发上限和文件 ownership。

## 下一批最小可启动包

在不等待硬件的前提下，建议下一批按以下顺序立项：

1. B1：typed validity/freshness 与未初始化失败测试。
2. C1：authority/envelope ADR 和 graph guard 测试设计。
3. E1：frame/time 纯函数金样与异常输入无发布断言。
4. A0：只读 `RcChannels` 字段对照和最小 patch review（不构建 promotion）。
5. D0/F0：CI job/scenario schema，仅消费 T00/T01/T08 接口。

其中 B1、C1、E1 可以立即并行；A0、D0、F0 的正式落地受 T00/T01/T08 输出阻塞。

## 统一 no-go

- 任一任务试图修改不属于自己的冲突文件。
- source/profile/artifact identity 未固定或工作树含未解释 dirty release source。
- 把历史 PX4 参数、历史 DDS session、mock publisher、文档草案或桌面演练声明为 current
  运行通过。
- 本轮 BBF-DOC-WAVE 尝试启动任何 Agent、Offboard、vision、SITL 或硬件 launch。
  后续获批任务只可按批准的隔离 SITL profile 启动 UDP Agent、PX4 SITL、DUT 和可选
  vision DUT；MAVROS、旧 bringup、hardware launch 和真实设备链始终禁止进入 SITL。
- 尝试访问真实串口、刷 firmware、写真实参数、arm/切换真实飞行器 mode 或向真实 PX4
  发送 `/fmu/in/*`。
- 任一 P0 未关闭却申请拆桨台架，或没有单独授权却申请有限实机。
