# Wave 4A — H5/H6 安全检查表与人工审批包

审查日期：2026-07-27  
审查范围：仅书面 H5 台架硬件与 H6 拆桨实机准备规程；不构成设备访问、控制、刷写、参数写入、解锁、模式切换或起飞授权。  
证据截点：`docs/current_audit/`（2026-07-27T22:15+08:00）及本 Wave 4A 已有
`04-build-evidence.md`。  
本线程硬件访问：**NO**。本线程 formal SITL：**NO**。

## 当前决定（fail-closed）

```text
H0: NO-GO
H1: NO-GO — 本轮构建入口在严格 package-boundary 前置校验 exit 2 停止；未启动 colcon
H2: NO-GO — 只有局部离线/standalone 证据，关键完整故障测试未完成
H3: NOT-RUN
H4: NOT-RUN；SITL 前置条件也未完成
H5: NOT-RUN / BLOCKED — 未取得本次硬件范围的独立人工批准，且 H0–H4 不满足
H6 READINESS: NOT READY

HARDWARE ACCESSED: NO
FORMAL SITL RUN: NO
PROPELLERS INSTALLED: NOT VERIFIED（本线程未接触或观察机体）
```

本文件是将来由人填写的 **审批输入和检查表**，不是审批本身；空白、`TBD`、历史
记录、mock、SITL 前置检查或静态测试都不是人工批准，亦不能把 H5 写成 `GO`。任何
身份、固件、参数、profile、transport、现场布置或人员变化均使相关人工确认失效并
退回相应前置门。

## 证据依据与当前阻塞登记

下表是 H5/H6 相关的最小阻塞集。文件和行号为已复核审查报告所记录的当前代码定位；
它们不是对尚未执行硬件步骤的替代证据。后续修改代码后，必须重新静态复核并更新本表，
不得沿用本快照声称 `FIXED`。

| Finding ID | 严重级别 | 历史结论 | 当前文件和行号 | 当前证据 / 状态 | 影响 | 修复与验收命令 | 阻塞门 |
|---|---|---|---|---|---|---|---|
| BBF-CUR-001（AUD-001..004） | P0 | Wave 3B 明确：离线 gate 通过，但 live publisher 未接入 | `src/offboard_cpp/src/node.cpp:20,28-35,87-90`; `src/lib/CtrlFSM.cpp:326-340,405-417` | `STILL_OPEN`：三个 `/fmu/in/*` writer 由 live 节点/FSM 直接发布，缺少 live ACK observer/gate | 未完成 PRESTREAM、freshness、owner、重启或拒绝情形可能仍发送控制流 | 所有 writer 收敛到同一 fail-closed gate；以 fake transport 覆盖 ready 前、ACK reject/timeout、restart、duplicate writer 均为零发布；运行获批准的完整 H2/H3 测试 | H0–H6 |
| BBF-CUR-002（AUD-005） | P0 | production `TEXT_RC`、auto-arm 与 RC 安全门未闭合 | `src/offboard_cpp/CMakeLists.txt:33-35`; `config/ctrl_param.yaml:12-16`; `src/lib/CtrlFSM.cpp:152-170,405-477` | `STILL_OPEN`：默认 auto-arm、无条件 `TEXT_RC`、无 live ACK；无 fresh RC 路径可跳过 RC 检查 | 可产生非预期 ARM/MODE 请求，人工急停前已有危险状态变化 | production 默认 auto-arm=false，移除 mock；fresh RC、kill latch、authority、ACK 均为硬门；无 RC/stale/lost/restart/reject 时 ARM/MODE 发布计数为 0 | H0–H6 |
| BBF-CUR-003/004/005 | P0/P1 | serial canonical source 未决，先前要求 fail-closed | `src/communication/Serial/serial_driver_ros/src/serial_main.cpp:13-25,29-39`; `script/send_demo.py:9-20`; `config/profiles/dds_only_packages.yaml:28`; `Scripts/test/verify_package_boundary.py:206-217` | `REGRESSED/STILL_OPEN`：任意 `/cmd_vel` 可直写串口；无 owner/watchdog/interlock；实际路径与严格 profile 不符；ROS/STM32 帧协议不一致且 odd length 可越界 | 第二执行链、误启动执行输出和不可重现 build；任何台架串口连接都不可接受 | 维护者确定唯一 origin/SHA/path/disposition；未批准时 production discovery/launch=0；协议统一后以 fake backend 做 CRC/短帧/奇数长度/断线/超时/ASan 测试。`python3 Scripts/test/verify_package_boundary.py --workspace-root /home/c/px4_ws/BoomBoomFly --log-base /tmp/<unique>` 必须 exit 0 | H0–H6 |
| BBF-CUR-006/007 | P1 | PX4 source 可读但 governance、toolchain、RC profile 和 Offboard root lock 未闭合 | `workspace.lock.repos:12-15`; `workspace.lock.repos:1-19`（没有 PX4 条目）；PX4 `src/modules/uxrce_dds_client/dds_topics.yaml:41,56,68,71,112,130,145` | `STILL_OPEN`：Offboard `976d…` 与 root lock `cded3…` 不同；PX4 v1.16.2/35 submodules/226 message 对比虽已确认，但 checkout shallow、未入 immutable lock、ARM toolchain 与 `rc_channels` endpoint 未闭合 | 无法精确重建或证明 RC/firmware/profile 与测试候选一致 | 维护者批准 immutable source/submodule/toolchain/board/RC profile，更新 exact receipt/lock；离线 restore、消息/生成器 hash 检查和获批准的纯软件目标 build 均通过 | H0、H1、H4–H6 |
| BBF-CUR-008 | P1 | H1 曾为 NOT-RUN，不能借旧 build 提升 | `Scripts/build/build_dds_only.sh:84-100`; `Scripts/test/test_dds_only.sh:76-116` | `STILL_OPEN`：Wave 4A 新鲜 `/tmp` 入口实际在 boundary exit 2 停止，未生成编译、install 或 test artifact | 当前候选没有可追溯的 H1 成功证据 | 在 H0 不再 NO-GO、source/lock/boundary 关闭后：`Scripts/test/test_dds_only.sh --workspace-root /home/c/px4_ws/BoomBoomFly --output-root /tmp/<unique>`；build、test、test-result 均 exit 0，并保存 identity/log/hash | H1–H6 |
| BBF-AUD-008..009 / CUR-009；H2/H3/H4 缺口 | P0/P1 | vision health、完整 fault suite、node integration 与 formal SITL 均未完成 | `src/vision_to_dds/vision_to_dds.cpp:75-83,126-162,260-345`；`docs/current_audit/05-gate-assessment.md` 的 H2–H4 结论 | `STILL_OPEN` / `NO-GO` / `NOT-RUN`：frame/time/reset/quality/device health 未闭合；未执行完整 current unit、无硬件节点级和 formal SITL | 感知/时钟/重启/断线异常可污染控制或估计；没有逐级实证不得进入硬件 | 以纯软件 fake clock/transport 完成 H2；以隔离 domain/fake transport 完成 H3；H4 仅在 H0–H3 GO 后形成并人工批准正式 SITL 方案。异常输入必须 fail-closed、零执行发布 | H0、H2–H6 |

补充证据：`04-build-evidence.md` 记录 H1 入口仅写 `/tmp`，未启动 `colcon build/test`，且
明确未访问硬件；`current_audit/05-gate-assessment.md` 记录 H5/H6 均 `NOT-RUN`。这些
结论优先于旧 runbook 中不同编号的 H0–H4 表述；本文件采用用户本轮 H5=台架、H6=拆桨
实机的门禁定义。

## H5 — 台架硬件：进入条件、审批卡与退出条件

### H5 进入条件（必须全为真）

以下每一项都需在**同一现场 session**由具名人员复核并记录。任何一项否、未知、过期或
无法无歧义验证，结果均为 `H5: NOT-RUN / BLOCKED`。

### A. 软件与可追溯性

- [ ] H0、H1、H2、H3 全部为 `GO`，对应原始 receipts、完整命令、日志和工件可复核。
- [ ] H4 已完成正式 SITL 前置审查；正式 SITL 是否已执行及其单独结论已记录，绝不以
  synthetic/mock 代替。
- [ ] 当前无 open P0；每项适用 P1 已关闭或以经独立审查的技术隔离消除硬件影响。
- [ ] root、Offboard、PX4、px4_msgs、Agent、所有 active package、firmware artifact、
  toolchain、profile/config 和参数快照均为 exact identity；无未知 dirty change、路径
  漂移、unapproved serial source、unapproved writer 或 lock mismatch。
- [ ] 权威执行链唯一：DDS-only 的批准 writer/cardinality 已验证；MAVROS、第二 Agent、
  历史 bringup 和 serial 执行器 writer 均不在范围、不占用同一 transport，且不会形成
  fallback 或第二控制链。
- [ ] 自动解锁默认关闭；live gate 证明 lease/ACK/status/RC/kill/PRESTREAM/freshness/
  restart/timeout 全部 fail-closed，恢复不得自动进入 ACTIVE。

### B. 单独人工范围批准（尚未获得）

本次需要用户/指定安全负责人对**精确范围**作书面批准，至少包含：飞行器/飞控、时间窗、
场地、允许的连接方式、允许的只读检查、是否允许上电、是否允许启动哪个批准节点、是否
允许 disarmed observation、是否允许任何 armed/actuator 步骤，以及每项失效时间。批准
必须逐项列出，不得从本文件、先前权限、设备已连接或软件通过推断。

```text
H5 SESSION ID:
AIRFRAME / FLIGHT CONTROLLER:
EXACT SOURCE + LOCK + FIRMWARE + PARAMETER + PROFILE IDENTITIES:
APPROVED DATE/TIME WINDOW AND LOCATION:
ALLOWED HARDWARE ACCESS SCOPE:
EXPLICITLY PROHIBITED ACTIONS:
APPROVED OBSERVER-ONLY COMMAND LIST VERSION / HASH:
APPROVED CONTROL/ACTION COMMAND LIST VERSION / HASH (if any):
HUMAN OPERATOR:
SAFETY OFFICER:
OBSERVER:
EVIDENCE RECORDER:
PHYSICAL POWER-CUTOFF OPERATOR:
APPROVER NAME / ROLE / SIGNATURE / TIME:
H5 DECISION FOR THIS SESSION: GO / NO-GO
```

未获得上述具体、有效、可追溯的人工填写与签字时，不能把该模板填写为 `GO`，更不能执行
任何硬件动作。

### C. 物理与隔离门

- [ ] 至少两名不同人员进行 challenge-response；Human Operator 与 Observer/Safety
  Officer 不得为同一人。两人均逐电机/逐桨位目视确认**全部螺旋桨已拆除**并签字。
- [ ] 机体固定、人员警戒区/电池危险区/执行器净空已设置；无松散物体、线束或人员进入。
- [ ] 物理急停/动力隔离可立即触达；其操作员已确认方法、职责和口令。逻辑/伴随计算机
  供电与 propulsion power 可隔离，串口线可物理断开。
- [ ] 串口隔离已确认：未经本次明确批准，不连接任何执行器串口；批准 DDS transport 时，
  仅一个经批准 owner 可占用指定端口。MAVROS、第二 Agent、QGC、历史 serial 或未知
  进程不得争用该端口。
- [ ] 网络隔离已确认：使用批准的隔离 ROS domain/网络边界；不得接入未知 DDS participant、
  远程控制源或桥接；没有外部网络/无线链路可变更控制权。
- [ ] RC、独立 kill、人工接管、状态/故障显示、消防/电池隔离和紧急通信均可用；本次
  profile 所依赖的硬件 health 有当次只读证据。

### D. H5 分步审批与命令清单控制

这是一张命令**审批清单格式**，不提供、也不授权执行命令。每条未来命令必须有唯一 ID、
不可变脚本/hash、预期状态、最大持续时间、前置条件、允许角色、abort 触发和人工签字。
没有相应行的命令一律禁止；不得用 shell history、临场修改或“相似命令”替代。

| Step | 允许目的 | 必填前置条件 | 命令/脚本审批字段 | 双人确认与退出 | 当前状态 |
|---|---|---|---|---|---|
| H5-0 | 断电/无连接的现场布置检查 | A–C 全部完成，机体确认 disarmed | `CMD-ID / hash / read-only proof / max duration` | Operator 复诵、Observer 确认；任一差异停止 | NOT APPROVED |
| H5-1 | 受批准的只读 identity/health 采集 | H5-0 通过；工具已证明不会写设备或打开未批准端口 | `CMD-ID / exact binary / fields retained / log path` | Recorder 记录；identity 不符即退出至断电安全态 | NOT APPROVED |
| H5-2 | disarmed-only 的观察/graph 检查 | H5-1 identity 一致；全 `/fmu/in/*` pre-readiness 发布计数为 0 | `CMD-ID / profile hash / writer allowlist / timeout` | Operator+Observer 复核唯一 writer；发现未知 writer 即中止 | NOT APPROVED |
| H5-3 | armed/actuator 或 fault 测试（若另行需要） | H5-2 实际通过；单独 on-site card 给出能量、通道、时长、失联动作和物理 abort | `CMD-ID / exact scope / max output / duration / human-only action` | 不能由 Codex/脚本自动 arm/mode/abort；每个 case 单独批准 | NOT APPROVED |
| H5-4 | 结束、断能、封存证据 | 前一步停止或完成；人员仍在岗 | `CMD-ID / shutdown order / evidence manifest` | 确认 disarmed、动力隔离、串口/网络释放；异常则设备隔离 | NOT APPROVED |

H5-0 至 H5-2 即使未来获批，也不自动允许 H5-3。H5-3 的每一个 test case 都需要新卡，
不得把命令拒绝、掉线或输出异常通过重试变成通过。

### H5 立即 abort 条件与退出状态

任一现场人员均可无条件说出“停止”。触发后由 Human Operator/Safety Officer 按获批准的
物理程序进入安全状态；本文件不指定或自动执行 arm、mode、land、disarm 或 actuator 命令。

- 出现任何未预期 arm、模式切换、执行输出、串口字节发送、未知/重复 writer、MAVROS、
  第二 Agent 或控制权/namespace/domain 变化；
- ACK reject/timeout/correlation mismatch，lease/owner 丢失，PX4、Agent、节点或 transport
  重启，或 ready 前 `/fmu/in/*` 非零发布；
- RC/kill/人工接管、急停、物理断电、battery/safety switch、estimator/status/odom/vision
  health 任一不可用或与批准预期不符；
- DDS/串口/网络断线、CRC/短帧/乱序、陈旧/未来/回退 timestamp、NaN/Inf、clock jump，
  或故障恢复试图自动重新 ACTIVE；
- 机体固定、桨叶拆除、净空、供电、人员角色、日志/时钟/记录或身份任一失效；
- 任何人叫停，或实际 PX4 failsafe/输出与批准的 case card 不一致。

退出后：停止推进后续步骤，记录事件时间线和原始证据，确认 disarmed/物理动力隔离、隔离
设备并保留日志；不得自动恢复、自动重试或在同一 session 扩大范围。恢复须完成故障分析、
重新适用的前置检查和新的人工 `GO`。

### H5 完成判定

H5 仅在本次已明确批准的所有步骤实际完成、无非预期 arm/mode/output、原始证据完整、
双人结论一致且独立审查确认后，才可能记录 `H5: GO`。截至本报告，以上条件均未执行，
故结论是 **H5: NOT-RUN / BLOCKED**，不是 `GO`。

## H6 — 拆桨实机：进入/退出条件

H6 不是 H5 的自动后续步骤，也不等同自由飞行、装桨或 production。它只可在用户对一个
明确拆桨实机步骤再次单独授权后，由现场人员按批准 test card 执行。

### H6 进入条件（全部必需）

- [ ] H0、H1、H2、H3 **全部 GO**；H4 的 SITL 前置要求已满足，formal SITL 的实际执行/
  未执行结论和证据单独记录；H5 已实际 `GO`。
- [ ] 无 open P0；所有 H6 适用 P1 已关闭或被独立技术隔离；H5 后无未审查的 source、
  firmware、parameter、profile、transport 或现场配置变化。
- [ ] 两名不同人员再次逐电机/逐桨位确认机体**所有螺旋桨已拆除**，记录时间、姓名和签字；
  不得把 H5 的旧确认复用为 H6 当前确认。
- [ ] 机体固定、执行机构净空、人员警戒区、动力隔离和实体急停均已复核；Safety Officer
  可在不进入危险区的前提下实施断能。
- [ ] 自动解锁仍关闭；唯一 control owner、ACK/timeout/RC/kill/freshness/restart/fault
  fail-closed 行为有与当前精确候选一致的 H0–H5 证据。
- [ ] 串口/网络隔离和唯一 DDS transport owner 已复核；没有 MAVROS、第二 Agent、QGC
  控制路径、demo、mock 或未知节点成为第二执行链。
- [ ] 用户再次书面批准此 H6 的精确 test card：范围、命令清单 hash、最大能量/时长、允许
  通道、预期状态、每项 abort、人工控制者、急停者、观察员、记录人及失效时间全部填写。

```text
H6 SESSION ID:
H5 EVIDENCE / INDEPENDENT REVIEW REFERENCE:
TWO-PERSON PROP-OFF CONFIRMATION (name/time/signature):
AIRFRAME FIXTURE / CLEARANCE CONFIRMATION:
PHYSICAL E-STOP / POWER-ISOLATION METHOD AND OPERATOR:
SERIAL ISOLATION / NETWORK ISOLATION CONFIRMATION:
EXACT CANDIDATE IDENTITIES (source/lock/firmware/params/profile):
TEST-CARD VERSION + HASH / APPROVED COMMAND IDS:
MAXIMUM ENERGY, OUTPUT, DURATION, AND CHANNEL SCOPE:
ABORT CONDITIONS / EXPECTED FAILSAFE / HUMAN RESPONSE:
USER'S EXPLICIT H6 AUTHORIZATION (name/time/signature):
H6 DECISION: READY / NOT READY
```

任何字段为空、任何已签条件失效、或未获用户**再次**明确批准，H6 都必须为
`NOT READY`。

### H6 角色、观察与执行纪律

| 角色 | 责任 | 独立性要求 |
|---|---|---|
| Human Operator | 仅执行批准 test card 中的人为步骤，复诵每一步并立即响应 halt | 不得由 Codex、脚本或 ROS node 取代 |
| Safety Officer / physical cutoff operator | 持有无条件停止和物理断能权，监视动力/电池/机体/急停 | 与 Operator 不同人 |
| Observer | 独立核验桨叶拆除、固定、净空、人员边界、异常声音/振动/运动 | 可无条件叫停；不得兼任 Operator |
| Evidence Recorder | 绑定 identity、批准、命令 ID、ACK/status、事件时间线、原始日志和实际结果 | 记录中断即停止，不篡改或覆盖异常 |
| Test Director（如指定） | 冻结范围，逐项发起 challenge-response，拒绝临场扩 scope | 不得用口头“继续”替代新批准 |

每一步使用 challenge-response：Test Director 读出目标/上限/abort，Operator 复诵，
Observer 确认物理条件，Safety Officer 确认断能可用，Recorder 记录时间，才可进入该
步骤。每步结束都回到已批准的安全状态并重新确认；失败后不可自行推进下一项。

### H6 abort/退出条件

H5 abort 条件在 H6 全部继承，并额外包括：任何超出 test-card 的能量、通道、时长、
机体位移、振动、温度、电流、噪声或人员/净空边界；任何不一致的 ACK、状态、控制权、
RC/kill、传感器、日志、时钟、串口/网络所有权；以及任一人叫停。触发后立即按当前获批的
人工/物理应急卡停止并隔离能源，封存证据，不再继续 H6 或进入装桨/飞行。

H6 结束后必须由两名现场人员确认 disarmed、动力隔离、桨叶仍全部拆除、串口/网络资源
释放，随后封存日志并进行独立结论复核。H6 通过不授权安装螺旋桨、H7、飞行或 production。

## 最短剩余关键路径（依赖顺序）

1. 先关闭/隔离 P0：live Offboard gate、默认 auto-arm/RC/kill/ACK、未跟踪
   `/cmd_vel`→serial 执行链；确认没有 DDS/MAVROS/serial 的双重控制。
2. 由维护者确定 serial canonical source/path/SHA/disposition，并把 Offboard、PX4、
   px4_msgs、PX4 submodules/toolchain/board/RC profile 写入批准的 immutable lock；保持
   unknown serial fail-closed。
3. 在不放宽 package boundary 的前提下使其 exit 0，修复依赖闭包；以新的 `/tmp` receipt
   完成 H1 build/test，保留完整 source identity、日志、artifact hashes。
4. 执行完整 H2 fake-transport/fault suite：ACK、owner、RC/kill、PX4/Agent/node/DDS
   restart、stale setpoint、timestamp、serial CRC/断线、vision/传感器掉线均须通过且 fail-closed。
5. 仅在 H0–H2 GO 后，执行无硬件 fake transport/node integration 取得 H3 GO；再完成 H4
   SITL 前置审查，formal SITL 是否运行须独立记录，不能由 mock 代替。
6. 向用户提交本文件的 H5 卡及精确硬件访问范围；获得单独书面批准后，才可由现场人员完成
   H5 的实际、可审计台架步骤并取得 H5 GO。
7. H5 GO 后重新完成 H6 两人拆桨/急停/隔离/净空确认，提交精确 H6 test card；只有用户
   再次明确授权并且所有 H6 条件仍有效时，H6 才可重新评估为 `READY`。

截至此审查截点，第 1–7 步均未完整完成。因此最终结论保持：

```text
H6 READINESS: NOT READY
```
