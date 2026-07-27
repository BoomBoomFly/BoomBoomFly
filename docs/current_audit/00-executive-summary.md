# 当前状态复核执行摘要

Audit date: 2026-07-27T22:15:13+08:00  
Hostname: orinnano  
User: c  
Workspace: `/home/c/px4_ws`  
Repository: `/home/c/px4_ws/BoomBoomFly`  
Branch: `master`  
HEAD: `0ed9d148bfbfd22253142172bbfe93c51106fdfa`  
PX4 target version: v1.16.2  
ROS distribution: Foxy  
Hardware accessed: NO  
SITL run: NO  
Files modified outside docs/current_audit: YES — colcon logs; nested Git index metadata refreshed by status; root FETCH_HEAD changed concurrently/unattributed; no source/config/existing-doc change

## 最终结论

Wave 3B 的“软件阶段已提交、总门未全过、formal SITL 未运行、该阶段未访问硬件”
仍是可靠历史基线；它不再完整描述当前工作区。当前 root HEAD 仍为历史 final，但：

- 分支已为 `master`；
- tracked `src/serial_driver_ros` gitlink checkout 已缺失；
- 新增未跟踪、dirty 的 `src/communication`，内部又嵌套 serial repo；
- 新增 exact `external/PX4-Autopilot@v1.16.2`，使“PX4 source absent”过时；
- live Offboard 仍绕过已单测 runtime gate，默认 auto-arm/`TEXT_RC` 仍在；
- 新 serial 节点把 `/cmd_vel` 直接写串口且无 authority/watchdog/interlock；
- package boundary 当前 exit 2，H1 没有执行。

```text
DOCS BASELINE: INCONSISTENT

H0: NO-GO
H1: NOT-RUN

HARDWARE ACCESSED: NO
FORMAL SITL RUN: NO
SOURCE FILES MODIFIED: NO
REPORT FILES CREATED: YES
```

历史全局“从未访问真实硬件”是 `CONTRADICTED`：2026-07-24 参数快照、真实串口
DDS output-only session、Wave 3A OS/udev/USB inventory 均为历史硬件接触证据。
准确说法是“Wave 3B 和本轮没有访问硬件”。

## 1. 文档谱系

| 文档 | 阶段 | Commit | 原门禁结论 | 当前有效性 | 替代文档 |
|---|---|---|---|---|---|
| `audits/2026-07-26/00..10` | 初始审计 | `3ce28094...` 等 | 9 P0/15 P1；production blocked | 历史 finding 基线 | Wave1/2/3 + 本审查 |
| `audits/2026-07-26/11..16` | Wave1 | 至 `11058dc...` | 局部整改，未全清零 | 历史 | cleanup/Wave3 |
| `audits/2026-07-26/20..22` | Wave2 SITL spec | dated commits | offline规格，formal SITL blocked | 场景历史；24-count过时 | machine catalog+Wave3B F2 |
| `audits/2026-07-26/30..32` | cleanup | `f34f5e6...` 周边 | cleanup/static pass | 历史 | Wave3A/B |
| `audits/2026-07-27-wave3a/**` | Wave3A | root `afb4fdce...`; Offboard `c744757a...` | oracle/unit-tested；build blocked | 被后续阶段取代 | Wave3B |
| `wave3b/20..28` | Wave3B | root final `0ed9d148...`; Offboard `976d6217...` | software gates not all pass；NO-GO | 最新历史基线，动态状态部分 stale | 本审查 |
| `handoff.md` | Wave3B navigation | root final | 仅关闭软件 blockers | 部分 stale | 本审查 00/03/05 |
| ADR/architecture/runbooks/schemas | 持续规范 | 多数不自带当前SHA | DDS-only、fail-closed、逐级promotion | 规范有效；不能作执行证据 | dated audit负责状态 |

147/147 个审查前 docs 文件均 tracked；82/82 Markdown 已全文读取，65 个结构化
工件已清点。逐文件 metadata/分类见 `01-doc-inventory.md`，声明状态见
`02-doc-claims-register.md`。

## 2. 仓库清单

| 路径 | 分支 | HEAD | 文档记录 HEAD | 漂移状态 | 工作区状态 |
|---|---|---|---|---|---|
| `BoomBoomFly` | master | `0ed9d148...` | Wave3B final同值，旧工作分支 | HEAD同、branch变 | dirty：deleted gitlink + untracked communication |
| `src/offboard_cpp` | agent/wave3b-offboard-integration | `976d6217...` | 同值；root lock `cded3dc5...` | current比lock后代2 | clean、无upstream |
| `src/px4_msgs` | detached | `392e831c...` | 同值/tag v1.16.2 | 相同 | clean |
| `external/PX4-Autopilot` | detached | `54f0455f...` | 旧文档称候选/absent | 新增exact source | clean、shallow、35 submodules clean |
| `src/communication` | main | `df256c18...` | 旧文档称目标 absent | 新增且manifest路径/origin冲突 | dirty |
| nested serial | master | `87f3907f...` | 旧gitlink同SHA | 新路径、未跟踪 | clean |
| `src/serial_driver_ros2` | — | — | `8614989c...` protected dirty | 当前缺失 | NOT_VERIFIED |

详细 23 个 BoomBoomFly repos 与 PX4 recursive ledger 见
`03-repository-inventory.md`。

## 3. 历史问题复核

| Finding ID | 历史状态 | 当前状态 | 证据 | 是否阻塞 |
|---|---|---|---|---|
| AUD-001..004 | P0 open | STILL_OPEN | live node/FSM直接publish，无ACK、无live gate | H0 |
| AUD-005 | P0 open | STILL_OPEN | `TEXT_RC`、auto-arm=true、无RC时检查可跳过 | H0 |
| AUD-006..007 | P0 open | STILL_OPEN | 初始化/fault lattice/live recovery未闭合 | H0 |
| AUD-008..009 | P0 open | STILL_OPEN | vision frame/time/reset/quality health gate缺失 | H0（启用视觉） |
| AUD-010..011 | P1 open | REGRESSED | 新serial路径使boundary exit2；communication无receipt | H0/H1 |
| AUD-012 | P1 open | STILL_OPEN | exact PX4已出现；governed lock/toolchain/RC endpoint仍缺 | H0/H1/SITL |
| AUD-013..019 | P1 open | STILL_OPEN | CI execution、live tests、formal SITL、QoS/atomicity/identity/defaults未达原验收 | H0/H1/SITL |
| AUD-020 | P1 open | NOT_VERIFIED | 法律/分发批准不在本轮 | release |
| AUD-021 | P1 open | STILL_OPEN | runbook存在，演练/实际rollback未完成 | promotion |
| AUD-022..024 | P1 open | STILL_OPEN | perception/RealSense/precision profiles未闭合 | perception/hardware |

按原关闭标准，历史 P0 9/9、P1 15/15 均未完整关闭；其中多项有显著
offline/static 缓解，但不能标 `FIXED`。

## 4. 新发现

| Finding ID | 严重级别 | 子系统 | 问题 | 证据 | 建议 |
|---|---|---|---|---|---|
| CUR-001 | P0 | Offboard | live publisher绕过runtime gate | `node.cpp:28-35`; `CtrlFSM.cpp:339-340,405-416` | 所有publish单点gate |
| CUR-002 | P0 | RC/arm | 默认auto-arm+mock，无live ACK | CMake/YAML/FSM | production fail-closed |
| CUR-003 | P0 | serial actuator | `/cmd_vel`直接串口写，无授权/超时互锁 | new serial main/demo | quarantine并做canonical决定 |
| CUR-004 | P1 | workspace | serial/communication来源、路径、manifest冲突 | Git+profile+exit2 | exact decision/receipt |
| CUR-005 | P1 | serial protocol | additive checksum vs CRC16+tail；odd len越界 | ROS/STM32源码 | 单一schema+ASan/fault tests |
| CUR-006 | P1 | PX4 | exact source未受治理，toolchain/RC endpoint缺 | external repo/DDS YAML | approved lock/profile |
| CUR-007 | P1 | reproducibility | Offboard final未入root lock | `workspace.lock.repos` | publish/approve/update lock |
| CUR-008 | P1 | build | boundary exit2、依赖闭包不完整、H1未跑 | validator/manifests | 修H0后isolated H1 |
| CUR-009 | P1 | perception | frame/time/device health未闭合 | vision/RealSense源码 | pure tests+zero-publish gate |
| CUR-010 | P2 | hardware config | hard-coded device/frame、重连/最小权限不足 | configs/launches | profile/by-id/bounded reconnect |

## 5. 门禁结论

```text
H0 静态审查：NO-GO
H1 纯软件构建：NOT-RUN
H2 单元测试：NO-GO
H3 无硬件节点级测试：NOT-RUN
H4 SITL：NOT-RUN
H5 台架硬件：NOT-RUN
H6 拆桨实机：NOT-RUN
H7 受控飞行：NOT-RUN
```

H0 blockers 为 open live P0、未知 critical serial source、dirty/path boundary、
Offboard lock mismatch、PX4 governance/RC profile、dangerous defaults、vision health。
H1 没有 build，且 boundary 在 build 前 exit2。H2 仅部分通过：root Python
152/152、Offboard Python 12/12、standalone gate PASS；完整 ROS/serial/vision/live
unit suite 未运行，故不是 GO。

## 6. 文档清理候选

| 文件 | 分类 | 被什么取代 | 建议动作 | 风险 | 需人工确认 |
|---|---|---|---|---|---|
| `handoff.md` | 临时/部分过期 | 本审查00/03/05 | 更新短导航，旧正文归档链接 | 丢交接上下文 | 是 |
| `NEXT_PARALLEL_TASKS.md` | mixed active/history | 本审查07/08 | active换Wave4，旧分工归档 | 丢ownership规则 | 是 |
| `BACKLOG/MILESTONES/DEPENDENCY_GRAPH` | 部分过期 | current findings/plan | reconcile，不删除 | 丢安全/依赖映射 | 是 |
| human-readable SITL三文档 | 数量失配 | machine catalog+F2 | 更新24→25/37 | 测试遗漏 | 是 |
| `current_environment.json` | 名称误导历史snapshot | 新dated capture+pointer | 先迁引用，现文件保留 | verifier依赖 | 是 |
| dated audits/evidence/receipts | 历史证据 | 后续报告仅supersede | 逻辑归档，禁止删除 | 破坏谱系 | 否 |

直接删除候选：无。

## 7. 下一阶段计划

```text
Wave 4A：关闭 H0 静态阻塞项
Wave 4B：建立可重复 H1 构建基线
Wave 4C：单元测试和故障注入
Wave 4D：无硬件节点集成
Wave 4E：SITL 前置准备
```

首要顺序是：live gate wiring与RC/arm closure；serial quarantine/canonical decision；
PX4 provenance/RC endpoint；vision fail-closed；随后才对齐 locks/依赖并运行
isolated H1。完整任务 ownership、验收命令、回滚和并行约束见
`07-next-phase-plan.md`，可直接派发 prompts 见 `08-next-wave-agent-prompts.md`。

## 审查过程例外

一个 ROS 清点线程执行未带 `/tmp --log-base` 的 `colcon list`，在
`/home/c/px4_ws/log/` 产生/更新 2 个日志元数据项。依照“禁止删除”未清理。
源码、配置、已有 docs 均未修改；详情见 `09-command-evidence.md`。因此报告头如实写
`Files modified outside docs/current_audit: YES`，而不是虚假填写 NO。

另有两类 Git metadata 变化：跨仓库 status refresh 了 nested index metadata；root `.git/FETCH_HEAD` 在 22:29 被外部/并发更新到同一 `origin/master at 0ed9d148...`。审查 Agent 未执行 fetch，且不据此声称远端实时状态。
