# 文档声明复核登记册

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

状态仅使用规定枚举；“当前验证状态”评价声明在本轮证据下的状态，不把文件 mtime
当成新鲜度。

| Claim ID | 文档 | 文档阶段 | 声明 | 仓库/组件 | 文档证据 | 当前验证状态 |
|---|---|---|---|---|---|---|
| C-001 | `wave3b/28_WAVE3B_SUMMARY.md` | Wave 3B | 软件阶段已完成并提交 | root | final 后的 summary/style commits；当前 HEAD 为 `0ed9d148...` | CONFIRMED |
| C-002 | `wave3b/20_BASELINE_AND_OWNERSHIP.md` | Wave 3B | root baseline 为 `afb4fdce...` | root | commit 存在，当前 HEAD 后代 7 commits | CONFIRMED |
| C-003 | `wave3b/28_WAVE3B_SUMMARY.md` | Wave 3B | root work branch 为 `agent/wave3b-integration-gates` | root | 当前分支 `master`；历史 ref 已不存在 | SUPERSEDED |
| C-004 | `handoff.md` | Wave 3B | root final 需动态解析 | root | 当前 HEAD 正是 `0ed9d148...` | CONFIRMED |
| C-005 | `wave3b/20_BASELINE_AND_OWNERSHIP.md` | Wave 3B | 当时仅 `?? src/serial_driver_ros2/` | root/serial | 当前为 deleted gitlink + untracked `src/communication` | SUPERSEDED |
| C-006 | `wave3b/24_MANIFEST...md` | Wave 3B | `../communication` absent | workspace | manifest 目标仍 absent；另有不同路径/origin的 `src/communication` | CONFIRMED |
| C-007 | `wave3b/24_MANIFEST...md` | Wave 3B | serial canonical source/path 未决定 | serial | package boundary 当前仍 exit 2，且实际路径再次漂移 | STILL_OPEN |
| C-008 | `wave3b/24_MANIFEST...md` | Wave 3B | protected `src/serial_driver_ros2@8614989...` 存在且 dirty | serial | 当前路径缺失，无法证明迁移/处置 | CONTRADICTED |
| C-009 | `wave3b/22_BC_RUNTIME_INTEGRATION.md` | Wave 3B | Offboard final `976d6217...` clean | Offboard | 当前同 SHA、clean | CONFIRMED |
| C-010 | `wave3b/24_MANIFEST...md` | Wave 3B | Offboard final 不匹配 root lock | root/Offboard | lock 仍 `cded3dc5...`，current 后代 2 commits | STILL_OPEN |
| C-011 | `wave3b/22_BC_RUNTIME_INTEGRATION.md` | Wave 3B | B/C pure-software gate PASS | authority/Offboard | 本轮 152 root + 12 nested + standalone gate PASS | CONFIRMED |
| C-012 | `wave3b/22_BC_RUNTIME_INTEGRATION.md` | Wave 3B | live ROS node/publisher 未接 gate | Offboard | gate 仅 tests 实例化；node/FSM直接 publish | STILL_OPEN |
| C-013 | `wave3b/21_PX4_PROVENANCE.md` | Wave 3B | PX4-Autopilot checkout absent | PX4 | 当前 `external/PX4-Autopilot` 存在 | FIXED |
| C-014 | `wave3b/21_PX4_PROVENANCE.md` | Wave 3B | intended v1.16.2 candidate 为 `54f0455f...` | PX4 | current tag/HEAD exact 同值 | CONFIRMED |
| C-015 | `wave3b/21_PX4_PROVENANCE.md` | Wave 3B | source/submodules/messages 无法核验 | PX4/px4_msgs | 35 submodules initialized；226/226 msg 相同 | FIXED |
| C-016 | `wave3b/21_PX4_PROVENANCE.md` | Wave 3B | approved immutable source/toolchain/board lock 缺失 | PX4 | checkout 未入 manifest；template 未解析；ARM compiler absent | STILL_OPEN |
| C-017 | 初始 findings / Wave 3B summary | 多阶段 | `rc_channels` firmware endpoint/profile 未闭合 | PX4/RC | official v1.16.2 DDS YAML 无 `rc_channels` | STILL_OPEN |
| C-018 | `wave3b/23_CI_IMPLEMENTATION.md` | Wave 3B | workflow static contract PASS | CI | workflow/tests存在；root 相关 Python suite PASS | CONFIRMED |
| C-019 | `wave3b/23_CI_IMPLEMENTATION.md` | Wave 3B | reproducible CI execution被 immutable locks 阻塞 | CI | lock 字段未被本轮新证据关闭 | STILL_OPEN |
| C-020 | `wave3b/27_WAVE3B_VALIDATION.md` | Wave 3B | package boundary/DDS wrapper在 serial conflict 前退出 | ROS build | 当前 boundary 同样 exit 2，但发现路径已变 | CONFIRMED |
| C-021 | `wave3b/27_WAVE3B_VALIDATION.md` | Wave 3B | 当前目标 DDS build 已通过 | ROS build | 文档没有此声明，本轮也未 build | NOT_APPLICABLE |
| C-022 | `wave3b/25_OFFLINE_ACCEPTANCE.md` | Wave 3B | F2 仅 OFFLINE_SYNTHETIC | SITL spec | machine catalog/timeline 明确 synthetic | CONFIRMED |
| C-023 | `wave3b/28_WAVE3B_SUMMARY.md` | Wave 3B | formal SITL 未运行 | SITL | 本轮亦未运行，未发现 formal result | CONFIRMED |
| C-024 | `verification/FAULT_SCENARIOS.md` | Wave 2 reference | fault 场景为 24 个且全部 blocked | SITL spec | catalog 已为 25 fault，第 25 为 offline unit-tested | SUPERSEDED |
| C-025 | `runbooks/SITL_SCENARIO_CATALOG.md` | Wave 2 reference | catalog 共 36 场景 | SITL spec | current catalog 12 normal + 25 fault = 37 | SUPERSEDED |
| C-026 | `wave3b/26_PROP_OFF_BENCH_READINESS.md` | Wave 3B | Wave 3B 未访问硬件 | Wave 3B | 原报告 scope 清楚，本轮无反证 | CONFIRMED |
| C-027 | 已知基线概述 | 跨历史 | 工程历史从未访问真实硬件 | workspace history | 历史参数快照、真实串口 DDS session、Wave3A USB inventory | CONTRADICTED |
| C-028 | `evidence/PX4_PARAMS...json` | 2026-07-24 | 参数快照是当前 PX4 状态 | hardware evidence | evidence index明确 historical，当前未读设备 | CONTRADICTED |
| C-029 | `wave3a/H_HARDWARE_INVENTORY.md` | Wave 3A | 当时枚举了 OS/udev/USB/设备 | hardware | 属历史采集，本轮不复用为当前连接状态 | CONFIRMED |
| C-030 | `CONTROL_AUTHORITY_MATRIX.md`/ADR-0001 | 规范 | PX4 权威控制链为 DDS-only、MAVROS禁止 | control authority | production profile/launch guard表达该规则，production disabled | CONFIRMED |
| C-031 | 同上 | 规范 | 当前不存在任何 MAVROS/serial 冲突路径 | archived chain | px4_bringup仍配置 MAVROS ttyTHS0，另有新 serial writer；靠隔离而非删除 | CONTRADICTED |
| C-032 | 初始 findings | 初始审计 | 无 runtime graph/owner/ACK/PRESTREAM live closure | Offboard | offline gate已实现，live路径仍绕过 | STILL_OPEN |
| C-033 | 初始 findings | 初始审计 | production `TEXT_RC`/auto-arm危险默认 | Offboard | 当前源码与 YAML 仍存在 | STILL_OPEN |
| C-034 | 初始 findings | 初始审计 | vision frame/time/reset/quality闭环缺失 | perception | 当前源码未达到原验收 | STILL_OPEN |
| C-035 | `dependencies/SOURCE_PROFILES.md` | Wave 3B | governed restore默认仅 active exact-SHA | dependencies | manifest/validator结构存在 | CONFIRMED |
| C-036 | `dependencies/SOURCE_PROFILES.md` | Wave 3B | 当前 workspace 可由 default lock准确恢复 | dependencies | Offboard mismatch、新 communication/PX4均在 lock 外 | CONTRADICTED |
| C-037 | `handoff.md` | Wave 3B | 只应继续关闭软件 blockers | workspace | 当前 H0 NO-GO、H1未运行，仍适用 | CONFIRMED |
| C-038 | `handoff.md` | Wave 3B | formal SITL/硬件/flight不应进入 | safety | 当前阻塞仍在，本轮未越界 | CONFIRMED |
| C-039 | architecture/status 文档 | 持续规范 | graph/authority/gate 全部仍仅 PLANNED | architecture | library/oracle 已实现并单测；live仍 open | SUPERSEDED |
| C-040 | `adr/0002-authority-command-envelope.md` | ADR | ADR 状态 Proposed | governance | 文件仍 Proposed，但接口已冻结/实现，治理状态未同步 | STILL_OPEN |
| C-041 | `wave3b/27_WAVE3B_VALIDATION.md` | Wave 3B | root Python 152 tests PASS | tests | 本轮重新执行 152/152 PASS | CONFIRMED |
| C-042 | Wave 3B test summaries | Wave 3B | 离线 tests 可证明 H2/live/SITL GO | tests | 报告明确不作此 claim；本轮完整相关 suite未执行 | NOT_APPLICABLE |
| C-043 | current environment evidence | Wave 1/3 baseline | managed PX4 source scan为 absent | environment | 扫描路径不覆盖新 `external/`，当前内容过时 | SUPERSEDED |
| C-044 | 当前代码外新增状态 | 本轮 | `src/communication` 已有治理 receipt/lock | dependencies | 未在 manifests/receipts中发现该 identity | CONTRADICTED |

## 结论

Wave 3B 的“阶段完成、软件总门未全过、正式 SITL 未运行、该阶段未访问硬件”仍是
可靠历史基线；其动态 workspace 描述已被 PX4、communication 和 serial 漂移部分
取代。文档基线整体判为 `INCONSISTENT`，而不是全盘失效。
