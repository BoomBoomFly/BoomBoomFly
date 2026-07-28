# BoomBoomFly Milestones

> 文档状态：`PLANNED`
>
> 当前调度入口为 [`docs/handoff.md`](../handoff.md) 和
> [Wave 4B open findings](../audits/2026-07-27-wave4b-wsl/07-open-findings.md)。
> 本文件不绑定活动 branch/HEAD；精确 source identity 必须从当次 handoff/receipt
> 重新验证。旧审计中的 branch/HEAD 只属于 `HISTORICAL_EVIDENCE`。这些是仓库内
> 规划，不是已创建的 GitHub Milestone，也不代表阶段已经通过。

## 共同 promotion 规则

1. production 始终为 `BLOCKED`，直到 M0–M6 的适用安全门全部关闭并由有权角色批准。
2. 任何里程碑的文档、模板或桌面演练完成，只能支持 `STATICALLY_VERIFIED`；
   不得升级为 `SITL_VERIFIED`、`BENCH_VERIFIED` 或 `FLIGHT_VERIFIED`。
3. 任何失败、缺证、身份不匹配、dirty release source 或未关闭 P0 都是 no-go。
4. 下一级必须引用同一 source/dependency/toolchain/profile/artifact identity；身份变化使
   前一级运行证据失效，必须重跑受影响门。
5. M5 前所有 P0 必须关闭。M6 需要单独的实机授权，路线图本身不授予该权限。

## M0：可复现基线

- **目标状态：** `STATICALLY_VERIFIED`
- **入口条件：** 当前 checkout identity 已记录；保留既有 dirty checkout；T00/T01/T08
  文件所有权明确；不执行 reset/clean。
- **范围：** `BBF-TASK-010`、`011`、`013`、`025`–`029` 的基础部分，以及
  T08 evidence schema；为 `BBF-TASK-020` 建立维护者决策门。
- **完成条件：**
  - DDS-only package/launch 边界技术强制，禁止路径负向测试通过；
  - lock+receipt 可在隔离目录重建有效文件树，第二次执行幂等；
  - OS/ROS/toolchain/dependency identity 可机器核验；
  - evidence schema 可区分 current、historical、superseded、unverified；
  - archive/default/optional/moving source profile 互斥且可机器验证；
  - moving dependency 有 exact-HEAD/dirty/approval receipt；
  - CODEOWNERS 和 remote required checks 只在真实 owner/管理员批准后启用；
  - CI 骨架执行无硬件静态/build/test 门，远端 required 设置由管理员另行确认。
- **阻塞项：** archive/source profile 尚未实施；`src/serial_driver_ros` 为
  `REQUIRES_MAINTAINER_DECISION`；`src/communication` dirty/untracked 来源未固化；
  CODEOWNERS 无有效 owner；required checks 未获管理员授权。未知许可证决定不阻塞
  离线开发，但继续阻塞 release。
- **禁止提前执行：** PX4 firmware patch 集成、SITL promotion、任何 hardware、
  firmware flash、参数写入或 production enable。
- **验收责任：** Release Maintainer 主验；Control/PX4/Perception Maintainer 复核各自
  依赖；独立 Reviewer 验证无越界修改。

## M1：PX4 DDS firmware profile

- **目标状态：** `SITL_VERIFIED`（firmware profile）；FMUv3 仅 build artifact，
  不等于实机固件验证。
- **入口条件：** M0 的 PX4 source/submodule/toolchain identity 与 T08 schema通过；
  `px4_msgs`/PX4 `RcChannels` 字段一致；baseline topic 集冻结。
- **范围：** `BBF-TASK-012`、`016` 的 firmware 端、`018` 的 transport identity 基础。
- **完成条件：**
  - 最小 patch 只增加 `/fmu/out/rc_channels`，baseline 不含
    `/fmu/in/landing_target_pose`；
  - 生成物包含正确 DataWriter/topic/type/QoS；
  - 隔离 PX4 DDS SITL 中恰有一个 PX4 publisher 且产生真实 payload；
  - baseline outputs 无回归；
  - `px4_fmu-v3_default` 构建、资源余量、完整日志和 `.px4` SHA-256 可追溯。
- **阻塞项：** 缺 PX4 source/submodule/toolchain；FMUv3 资源门未批准；T08 schema 未就绪。
- **禁止提前执行：** firmware flash、访问串口、修改当前 PX4 参数、将 mock payload
  当作验收、启用精降 topic。
- **验收责任：** PX4 Maintainer 主验；Release Maintainer 核 provenance；
  Control Maintainer 核 RC 消息契约。

## M2：Offboard 安全闭环

- **目标状态：** `UNIT_TESTED`；依赖 M1 的集成部分在 M3 才能达到 `SITL_VERIFIED`。
- **入口条件：** M0 的受控 build/profile；authority/envelope/time/fault 设计经过评审；
  M1 的接口可用于集成或以清晰 stub 只做纯单元开发。
- **范围：** `BBF-TASK-001`–`007`、`014`、`017`、`019`。
- **完成条件：**
  - graph guard 和 owner/lease 在运行时 fail-closed；
  - readiness/PRESTREAM、ACK+fresh status、统一 validity/freshness/epoch 完成；
  - production target 无 RC mock，RC/kill 强制门闭合；
  - fault lattice 每个适用状态×故障格经 Safety Reviewer 批准；
  - 所有状态边、ACK result、loss/restart/NaN 场景有表驱动单元测试；
  - production 仍保持 `BLOCKED`。
- **阻塞项：** `BBF-TASK-007` 危险降级动作未获安全评审；M1 无 RC 权威 source；
  接口冲突未冻结。
- **禁止提前执行：** 把纯单元结果声明为 PX4 交付验证；启动硬件；在未评审 fault
  action 前实现 Land/Position/停止输出选择；自动恢复 ACTIVE。
- **验收责任：** Control Maintainer 主验；Safety Reviewer 对 fault/action 有否决权；
  PX4 Maintainer 复核命令/反馈契约。

## M3：SITL 验收

- **目标状态：** `SITL_VERIFIED`
- **入口条件：** M1 firmware profile 完成；M2 单元与接口门通过；CI 可运行隔离 SITL；
  transport identity 固定。
- **范围：** `BBF-TASK-015`、`016` 的运行端，以及 M2 全部正常/故障场景。
- **完成条件：**
  - PX4/Agent/domain/source/profile identity 固定且可证明；
  - topic/type/version/QoS 和 PX4 input consumption 验证；
  - 正常 PRESTREAM、ACK、状态迁移闭合；
  - RC/DDS/owner/odom/status/battery loss、ACK reject、PX4/Agent restart、
    double-writer、time jump、mock 混入全部按 bounded timeout fail-closed；
  - 每场景独立可重放并产生机器可判定 event timeline；
  - 所有适用 P0 关闭，没有未解决的文档/代码级 P0/P1。
- **阻塞项：** M1/M2 任一未完成；flaky 无界等待；source identity 无法证明。
- **禁止提前执行：** 拆桨台架、实机串口、firmware flash、把 mock publisher 当 PX4。
- **验收责任：** Integration/Test Maintainer 主验；PX4、Control、Safety Reviewer 共同签字；
  Release Maintainer 验证 evidence 链。

## M4：感知状态估计

- **目标状态：** `SITL_VERIFIED`（普通视觉 profile）；真实传感器和实机 EKF2 仍可保持
  `UNVERIFIED`，直到另行授权。
- **入口条件：** M2 authority/profile/freshness 框架完成；M3 的隔离 SITL 能承载视觉；
  上游 frame/设备角色已确认。
- **范围：** `BBF-TASK-008`、`009`、`022`、`023`；`024` 仅在普通视觉稳定后作为可选专项。
- **完成条件：**
  - 坐标、frame、quaternion、covariance 金样通过；
  - sample/publish time、epoch、reset、quality/freshness 经过故障测试；
  - sensor→TF→DDS→EKF2 profile 任何 preflight 失败时无视觉 publisher；
  - T265 缺失/掉线/重枚举清旧数据并撤销 authority；
  - 普通视觉 SITL/EKF2 证据可追溯；
  - precision landing 默认关闭，baseline publisher 不存在。
- **阻塞项：** 当前硬件/参数状态未知；安装外参未确认；M2 authority 未完成。
- **禁止提前执行：** 写 EKF2 参数、启动真实相机、把历史设备枚举/参数当 current、
  在普通视觉未闭环时启用 precision landing。
- **验收责任：** Perception Maintainer 主验；PX4 Maintainer 核 EKF2/DDS 契约；
  Safety Reviewer 核 fail-closed。

## M5：拆桨台架

- **目标状态：** `BENCH_VERIFIED`
- **入口条件：** 所有 P0 关闭；适用 P1 关闭；M3 通过，带视觉场景还需 M4；
  Level 2 runbook、当前 firmware/参数/transport identity、回滚包与双人授权齐全。
- **范围：** `BBF-TASK-021` 的真实拆桨台架执行；仅按获批 test card。
- **完成条件：**
  - 桨叶拆除、机体固定、供电隔离、急停/RC/kill、观察员和双人确认留证；
  - `/dev/ttyTHS0` 只由 DDS transport 独占，QGC 仅按获批独立链路监控；
  - 逐项验证 graph/authority、ACK、RC/DDS/odom/status/battery loss 和重启；
  - 所有 stop condition 在批准 deadline 内触发；
  - firmware/参数/software rollback 在台架实际演练成功；
  - 无未解决的台架级 P0/P1。
- **阻塞项：** 任一 P0 未关闭；实机授权、当前参数快照、已知良好 artifact 或观察员缺失；
  runbook 仍只是草案。
- **禁止提前执行：** 安装桨叶、离地、超出 test card、自动升级到 M6、把桌面演练标为
  `BENCH_VERIFIED`。
- **验收责任：** Safety Reviewer 是 go/no-go authority；Flight Operator 执行；
  Observer 独立喊停；PX4/Control Maintainer 在场；Release Maintainer 核 evidence。

## M6：有限实机

- **目标状态：** `FLIGHT_VERIFIED`（仅批准包线和 profile，不等于 production）
- **入口条件：** M5 `BENCH_VERIFIED`；单独实机风险评估、地点/法规/保险/人员和最小包线
  授权；当前天气、硬件、firmware、参数、transport 与 M5 一致。
- **范围：** 仅批准的有限飞行 test card；production enable 是独立决策。
- **完成条件：**
  - 在限高、限时、限距、隔离区域与明确停止条件内完成；
  - 每个 planned maneuver 和 abort/recovery 都有观察与证据；
  - 结果绑定 source/dependency/toolchain/firmware/parameter/profile identity；
  - 事故/异常完成复盘，未通过项回退到 M5 或更早；
  - production enable 由授权治理角色另行书面决定。
- **阻塞项：** 无实机授权；M5 身份变化；任何 unresolved P0/P1；环境或人员不满足。
- **禁止提前执行：** 未授权 arm/mode/setpoint、扩展包线、夜间/人口密集区测试、
  自动转入 production。
- **验收责任：** 授权 Flight Test Director 是 go/no-go authority；Safety Pilot 和
  Observer 均有独立停止权；领域 Maintainer 与 Release Maintainer 共同签字。

## 里程碑状态汇总

| Milestone | 当前状态 | 允许的最强声明 |
|---|---|---|
| M0 | `PARTIALLY_IMPLEMENTED` | 旧入口和当前文档已进入清理；G 的 release hygiene 门未完成 |
| M1 | `BLOCKED` | 规划已定义，未取得可追溯 firmware profile |
| M2 | `BLOCKED` | P0 控制闭环未实现 |
| M3 | `BLOCKED` | schema/parser 可离线推进；正式 PX4 DDS SITL 等待 A–D |
| M4 | `BLOCKED` | E 等待 C authority/profile 接口冻结 |
| M5 | `BLOCKED` | 拆桨台架未授权；软件门与正式 SITL 未关闭 |
| M6 | `BLOCKED` | 飞行未授权；M5 未通过 |

```text
PRODUCTION: BLOCKED
HARDWARE ACCESS: NOT AUTHORIZED
FIRMWARE FLASH: NOT AUTHORIZED
FLIGHT: NOT AUTHORIZED
```
