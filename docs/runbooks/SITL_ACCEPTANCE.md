# PX4 DDS SITL 验收

> 文档状态：`IMPLEMENTED`
>
> 验收状态：`BLOCKED`
>
> 最近结果：`UNVERIFIED`
>
> 硬件：禁止使用

本 runbook 规定 Level 1 的验收边界。当前仓库没有已批准的项目级 PX4 DDS SITL orchestration，`rc_channels` firmware profile 和关键 Offboard 安全闭环也未完成，因此本文不能直接启动验收，不能声称 `SITL_VERIFIED`。

## 1. 目标与范围

目标是在完全隔离的 PX4 v1.16.2 SITL 中验证：

- 单 PX4 uXRCE-DDS client 与单 Micro XRCE-DDS Agent；
- `/fmu/in/*`、`/fmu/out/*` 的 exact topic、type、版本、QoS 和 source identity；
- `/offboard_control_node` 的唯一控制 writer 和单一 mission owner；
- authoritative `/fmu/out/rc_channels` 来自 PX4，不是 mock；
- readiness、PRESTREAM、VehicleCommand ACK、fresh feedback、owner/lease、graph guard；
- 正常状态迁移和批准 fault lattice 的故障注入；
- 可重复 evidence 和清理/回滚。

本级不证明真实 UART、执行器、电池、RC 链路、台架或飞行安全。

## 2. 允许与禁止

允许：锁定 PX4 SITL binary、UDP Agent、隔离 ROS domain、测试专用 mission owner、只读 graph 检查、受控故障注入、日志/rosbag/equivalent recorder。mock 只可用于明确标为 unit fixture 的负向测试，不得提供 PX4 contract 的通过证据。

禁止：

- 访问 `/dev/ttyTHS0`、`/dev/ttyACM*`、`/dev/ttyUSB*`；
- 启动 MAVROS、旧 `px4_bringup`、任何真实硬件 Offboard/视觉入口或 hardware launch；只允许受管 SITL orchestration 创建被测 DUT；
- 使用真实 PX4、相机、雷达、VPU 或执行器；
- 刷写 firmware、修改真实参数、arm 真实飞行器；
- 把 mock publisher、rosbag replay 或手工 topic publisher 当作 PX4 source evidence；
- baseline 启用 precision landing 或 swarm namespace；
- 在项目级 orchestration 尚为 `BLOCKED` 时手工拼接命令后宣称验收通过。

## 3. 前置条件

全部勾选后才可把本 runbook 从 `BLOCKED` 提交为待执行：

- [ ] Level 0 已按同一 root HEAD/lock/profile 通过，状态为 `STATICALLY_VERIFIED` 且 required unit tests 为 `UNIT_TESTED`。
- [ ] PX4 v1.16.2 source SHA、递归 submodule、toolchain、SITL binary SHA-256 已锁定。
- [ ] `rc_channels` profile 已静态生成，baseline 未加入 `landing_target_pose`。
- [ ] Micro XRCE-DDS Agent v2.4.2 binary identity 已记录。
- [ ] DDS-only package/launch 边界已技术强制；MAVROS 和历史入口不可进入测试图。
- [ ] graph guard、owner/lease、ACK/freshness、PRESTREAM 和 fault lattice 已实现并通过单元测试。
- [ ] exact topic/type/version/QoS 表和 transport identity profile 已评审。
- [ ] evidence schema、raw log 和 rollback manifest 入口已由对应工作线提供。
- [ ] 安全 reviewer 已批准每种故障的预期动作和 deadline；未批准项保持 `BLOCKED`。

## 4. 人员角色

| 角色 | 职责 |
|---|---|
| test operator | 只运行受管 orchestration 和批准场景，不临时改变 profile |
| control reviewer | 核对状态机、writer、ACK、freshness 和故障结果 |
| evidence recorder | 在运行前锁定 identity，保留原始输出、退出码和时间线 |
| safety reviewer | 批准故障动作/deadline；不得由实现者单独代签 |

一人可承担 operator/recorder，但 control 或 safety reviewer 必须独立。

## 5. 设备、软件、firmware、参数和 transport

| 项目 | Level 1 要求 |
|---|---|
| 设备状态 | 无真实硬件；工作目录和 ROS domain 与其他 graph 隔离；测试有 bounded timeout |
| OS/ROS | Ubuntu 20.04、ROS 2 Foxy；RMW 实现和版本进入记录 |
| Agent | Micro XRCE-DDS Agent v2.4.2；binary SHA-256/来源进入记录 |
| PX4 | v1.16.2 锁定 source 和 `rc_channels` SITL profile；binary SHA-256 进入记录 |
| project | 根 remote/branch/HEAD/status、lock hash、被测依赖 HEAD/dirty receipt 完整 |
| 参数快照 | 由本次 SITL instance 导出并 hash；2026-07-24 实机参数只可标 `HISTORICAL_EVIDENCE` |
| transport | 单 SITL PX4、单 UDP Agent、单 client identity、单 ROS domain、根 namespace `/` |
| mission | 一个测试 owner；demo 与 animal 互斥；正式 arbiter 存在时只允许其授权输出 |
| vision | 默认关闭；如单独测试视觉，必须满足独立 profile 且不能改变 baseline 结论 |

## 6. 执行前只读记录命令

以下命令只记录源码身份，不启动系统：

```bash
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git rev-parse HEAD
git status --short
git rev-parse HEAD:workspace.lock.repos
```

SITL binary、Agent binary、profile 和参数文件的路径必须由受管 orchestration 输出，不接受操作者临时猜测。记录其 SHA-256：

```bash
sha256sum "$BBF_SITL_BINARY"
sha256sum "$BBF_AGENT_BINARY"
sha256sum "$BBF_SITL_PROFILE"
sha256sum "$BBF_SITL_PARAMETER_SNAPSHOT"
```

上述变量必须由 orchestration 写入本次运行环境并回显解析后的绝对目标；不得使用用户 home 路径作为持久 evidence。变量缺失即 `no-go`。

## 7. 启动顺序

项目级启动命令当前为 `BLOCKED`，由后续 SITL 框架提供。批准版本必须实现以下顺序和失败清理：

1. 创建独立临时目录、ROS domain 和 evidence run ID。
2. 校验没有真实设备参数、serial Agent、MAVROS 或非 allowlist package/action。
3. 启动单一 PX4 SITL，等待确定的 readiness 事件，不用无界 sleep。
4. 启动单一 UDP Agent，验证 client/profile identity。
5. 启动 observer/recorder；先检查 `/fmu/out/*`，此时不得有 ROS 侧控制 writer。
6. 启动 graph guard 和被测 Offboard；在反馈/authority ready 前断言 `/fmu/in/*` 控制发布计数为 0。
7. 启动唯一 test mission owner；按批准 test case 推进 PRESTREAM、ACK 和状态迁移。
8. 每个场景独立清理，下一场景不得继承 lease、PX4 epoch、参数或消息缓存。

任一步失败都跳到第 11 节清理，不继续后续场景。

## 8. Graph、topic 与 QoS 检查命令

仅在隔离 SITL graph 已由批准 orchestration 启动后执行：

```bash
ros2 node list
ros2 topic list -t
ros2 topic info -v /fmu/out/vehicle_status_v1
ros2 topic info -v /fmu/out/rc_channels
ros2 topic info -v /fmu/out/battery_status
ros2 topic info -v /fmu/out/vehicle_odometry
ros2 topic info -v /fmu/out/vehicle_land_detected
ros2 topic info -v /fmu/out/vehicle_command_ack
ros2 topic info -v /fmu/in/trajectory_setpoint
ros2 topic info -v /fmu/in/offboard_control_mode
ros2 topic info -v /fmu/in/vehicle_command
ros2 topic info -v /fmu/in/vehicle_visual_odometry
ros2 topic info -v /offboard/cmd
ros2 topic info -v /offboard/cmd_mode
ros2 topic info -v /offboard/takeoff_land
```

预期：

- 三个 PX4 控制输入各有且仅有 `/offboard_control_node` 一个批准 writer；
- 视觉输入最多一个 `/vision_to_dds_node` writer，默认 baseline 为 0；
- 三个 `/offboard/*` 命令 topic 来自同一当前 lease owner；
- `/fmu/out/*` 的 authoritative publisher 能追溯到本次 PX4 SITL；
- `/fmu/out/rc_channels` 存在、type/QoS 匹配，并有来自 PX4 的有效 payload；
- graph 不含 MAVROS、旧 bringup、mock feedback、demo/animal 并发或多个 Agent；
- root namespace 以外的 swarm endpoint 为 0。

`ros2 topic info` 不能单独证明 payload source 或 PX4 reader 实际消费；必须与 orchestration 的 process identity、endpoint metadata 和 PX4-side evidence 交叉验证。

## 9. 场景矩阵

每个场景都必须有 initial state、injection、expected event、deadline、actual timeline 和 reviewer result。具体安全动作只有经过 safety review 后才能填入；不得由本文预设 Land、Position 或停止输出。

本节的人工可读矩阵由机器可读 catalog 细化。正式执行器必须读取
[`../verification/scenarios/catalog.json`](../verification/scenarios/catalog.json)，
按 catalog 中的相对路径加载场景，并使用 schema version `1.0.0` 校验。人工表格与
catalog 冲突、场景未登记、schema 校验失败或 dependency 未解析时均为 `no-go`。
完整索引见 [SITL 场景目录](SITL_SCENARIO_CATALOG.md)。

### 9.1 正常场景

| ID | 场景 | 预期结果 |
|---|---|---|
| SITL-N01 | telemetry readiness | 所有必需 PX4 输出首帧、freshness、epoch 和 QoS 合格前，控制输出计数为 0 |
| SITL-N02 | PRESTREAM | 连续不少于 1 s 且不少于 20 个有效样本后才允许 mode request；中断清零 |
| SITL-N03 | VehicleCommand accepted | 只有匹配的 `ACCEPTED` ACK 加 fresh VehicleStatus 一致后才迁移 |
| SITL-N04 | mission transaction | mode+trajectory 同 owner/lease/sequence/time window 且字段合法才到达 PX4 input |
| SITL-N05 | controlled completion | 只验证批准 test case；最终清除 lease 和旧 setpoint，不自动恢复 ACTIVE |

### 9.2 故障场景

| ID | 注入 | 不可妥协断言 | 安全动作状态 |
|---|---|---|---|
| SITL-F01 | duplicate control writer | graph guard 拒绝 ACTIVE，非批准 writer 数据到 PX4 的计数为 0 | `PLANNED`，待评审 deadline |
| SITL-F02 | duplicate/expired/old mission owner | lease 撤销；乱序、重复、过期命令计数为 0 | `PLANNED` |
| SITL-F03 | ACK denied/failed/unsupported/temporary reject | 不宣称事务成功，不进入目标状态 | `PLANNED` |
| SITL-F04 | ACK lost/late/duplicate/wrong target | correlation 拒绝，bounded timeout 后锁存 | `PLANNED` |
| SITL-F05 | RC never received/loss/stale/signal_lost | arm/mode request 计数为 0；mock 不可满足验收 | `PLANNED` |
| SITL-F06 | DDS loss / Agent restart | epoch/lease/预热清零，不自动恢复旧控制 | 具体飞行阶段动作 `BLOCKED` |
| SITL-F07 | odometry loss/jump/NaN/Inf | 无效输入不得产生新 PX4 setpoint | 具体动作 `BLOCKED` |
| SITL-F08 | VehicleStatus stale / PX4 reboot | 旧 ACK/status/lease 全部失效，不自动恢复 | 具体动作 `BLOCKED` |
| SITL-F09 | battery never received/stale/invalid | 不继续未批准任务，不误报 low-battery 已处理 | 具体动作 `BLOCKED` |
| SITL-F10 | mission owner loss | lease 超时且旧 setpoint 清空；恢复需人工重新授权 | 具体动作 `BLOCKED` |
| SITL-F11 | vision loss/freeze/reset/time jump | stale/future/backward/non-finite 视觉 publish count 为 0 | 具体动作 `BLOCKED` |
| SITL-F12 | kill edge/bounce | 去抖、最高优先级、锁存和人工复位符合批准契约 | `PLANNED` |

任一 `BLOCKED` 动作未获安全批准时，不运行对应场景，也不能完成 Level 1。

## 10. go、no-go 与立即停止

### go

- 全部前置条件有可追溯 evidence；
- 正常和 required 故障场景至少连续两次独立运行结果一致；
- source、binary、profile、参数、domain 和 process identity 完整；
- 无 mock source、未知 publisher、跨 domain 污染或残留进程；
- control 和 safety reviewer 均无未解决 P0/P1；
- rollback/cleanup 完成并被 recorder 确认。

通过后状态可记为 `SITL_VERIFIED`，但只适用于该精确身份组合。

### no-go

- 任一前置为 `BLOCKED`/`UNVERIFIED`；
- 任一 required test fail、skip、flaky 或超时；
- endpoint type/QoS/source/数量与契约不符；
- PX4 输入消费仅由 ROS discovery 推断；
- 参数/profile/firmware/HEAD 与运行记录不一致；
- evidence 缺 raw log、退出码、timeline 或 reviewer；
- 需要人工解释日志才能把失败改成通过。

### 立即停止

- orchestration 尝试打开真实串口/USB/硬件；
- 发现 MAVROS、serial Agent、未知 PX4/Agent 或重复 writer；
- ROS domain 与预分配隔离值不一致；
- 测试失去 bounded timeout、日志或 source identity；
- 故障行为偏离批准状态表；
- 任一 reviewer 发出 stop。

## 11. 清理与 rollback

1. 使用 orchestration 的 bounded shutdown；保存每个进程退出码。
2. 确认 PX4 SITL、Agent、Offboard、mission、vision、recorder 和故障注入器均退出。
3. 在同一测试 domain 检查无残留节点/endpoint；检查不能切换到真实 domain。
4. 还原临时 profile/参数文件；不修改 source checkout，不删除失败 evidence。
5. 记录失败时的最后状态、active lease、PX4 epoch、ACK pending 和 fault event。
6. 若 cleanup 不完整，标记 run `BLOCKED` 并隔离该测试 domain/临时目录，不开始新 run。

## 12. evidence 要求

- root/lock/dependency/PX4 source/submodule/toolchain/Agent SHA；
- SITL/Agent/profile/parameter/config SHA-256；
- domain、namespace、client key、process PID/command line 和启动顺序；
- topic/type/QoS/source inventory；
- PX4-origin `rc_channels` 及 baseline topic payload；
- 每个场景的原始日志、事件 timeline、退出码、重复次数和 deadline；
- no-go/stop/cleanup/rollback 结果；
- operator、control reviewer、safety reviewer、recorder 的结论；
- 明确列出 `UNVERIFIED`、not applicable 和未执行场景。

## 13. 下一等级入口

进入拆桨台架前必须同时满足：

1. 本级针对精确候选版本为 `SITL_VERIFIED`；
2. 所有 P0 关闭，适用 P1（firmware、profile、CI、SITL、安全测试、runbook、rollback）关闭；
3. `BENCH_ACCEPTANCE_DRAFT.md` 经维护者、安全 reviewer 和 test director 批准为受控版本；
4. 台架 firmware/参数/software/transport rollback 包已桌面演练；
5. 已获得硬件、刷写、参数和任何 control action 的单独书面授权。

任一条件缺失，Level 2 保持 `BLOCKED`。

## 14. 机器可读场景与离线验证

本节只授权离线读取 JSON/JSONL，不授权启动 PX4 SITL、Agent、ROS 节点或任何
launch。当前场景与 synthetic fixture 的最高结论是 `STATICALLY_VERIFIED` 或
`UNIT_TESTED`；它们不构成 `SITL_VERIFIED`。

### 14.1 规范入口

| 项目 | 路径 / 版本 |
|---|---|
| scenario catalog | `docs/verification/scenarios/catalog.json` |
| scenario schema | `docs/verification/schemas/scenario.schema.json`, `1.0.0` |
| event schema | `docs/verification/schemas/event.schema.json`, `1.0.0` |
| result schema | `docs/verification/schemas/result.schema.json`, `1.0.0` |
| timeline encoding | UTF-8 JSONL，每行一个完整 event object |
| requirement/audit mapping | `result.scenario_id` → catalog entry → 场景的 `requirement_ids` / `audit_ids` |

场景状态只允许 `PLANNED`、`STATICALLY_VERIFIED`、`UNIT_TESTED`、`BLOCKED` 和
`UNVERIFIED`。`BLOCKED` 场景必须列出至少一个 blocker；依赖未满足时不得通过
跳过场景来关闭验收门。

### 14.2 离线命令

从仓库根目录运行：

```bash
python3 tools/sitl_acceptance/validate_catalog.py \
  --catalog docs/verification/scenarios/catalog.json

python3 tools/sitl_acceptance/validate_scenario.py \
  --scenario docs/verification/scenarios/normal/SITL-NORMAL-001.json

python3 tools/sitl_acceptance/validate_event.py \
  --input test/sitl_acceptance/fixtures/valid/timeline.jsonl

python3 tools/sitl_acceptance/parse_timeline.py \
  --input test/sitl_acceptance/fixtures/valid/timeline.jsonl \
  --output /tmp/bbf-sitl-parsed.json

python3 tools/sitl_acceptance/assert_timeline.py \
  --scenario docs/verification/scenarios/normal/SITL-NORMAL-001.json \
  --timeline test/sitl_acceptance/fixtures/valid/timeline.jsonl
```

这些工具只验证文件结构和合成时间线断言。fixture 必须显式标为 synthetic；工具返回
0 只说明对应离线输入满足规范，不能关闭 PX4 source contract、QoS delivery 或正式
SITL 门。

### 14.3 正式 SITL 前置依赖

- `BLOCKED_BY_T00`：工作区、dirty receipt、PX4 source/submodule/toolchain identity。
- `BLOCKED_BY_T01`：DDS-only package/launch boundary。
- `BLOCKED_BY_T02`：`rc_channels` firmware endpoint manifest 与 PX4-source payload。
- `BLOCKED_BY_T03`：ACK/freshness/PRESTREAM 接口和稳定事件。
- `BLOCKED_BY_T04`：owner/lease/continuous graph guard。
- `BLOCKED_BY_T05`：经 Safety Reviewer 批准的 fault code、动作、deadline 与恢复策略。
- `BLOCKED_BY_T06`：required CI 和隔离 SITL job。
- `BLOCKED_BY_T08`：正式 evidence、release 与 rollback schema。

依赖字段用于 fail-closed 调度，不是 waiver。涉及 Land、Position、保持 PX4 failsafe
或停止输出选择而尚未批准的场景必须再列 `SAFETY_DECISION_REQUIRED`。

### 14.4 source identity 与 mock 门

正式结果必须把事件中的 source identity 绑定到本次 PX4 source、SITL binary、
profile、Agent、domain、client key 和 endpoint identity。mock、bag、手工 publisher
或 synthetic fixture 即使 topic/type/QoS 相同，也不能满足 PX4 contract；发现 mock
污染时必须产生失败结果且 PX4 contract 门保持未关闭。

本文件仍未授权正式运行。获得 T00–T06/T08 输入、冻结接口并完成独立安全评审后，
应另行批准受管 orchestration 和精确场景集合。
