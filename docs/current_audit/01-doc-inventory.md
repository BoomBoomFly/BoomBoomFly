# 文档全量清单

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

## 清点范围与读法

审查开始时 `docs/` 共 147 个文件，全部被 Git 跟踪：82 个 Markdown，65 个
JSON/YAML/patch 等结构化工件。全部 Markdown 已完整读取；结构化工件按 schema、
identity、状态字段和引用关系清点。

“阶段/角色”是内容分类，不按 mtime 推断权威性。“报告结论”仅摘录原文；当前有效性
由本轮 Git、代码和低风险软件验证决定。非报告工件的 baseline/final、H0–H4、
硬件/SITL 字段记作 `N/A`，而不是猜测。

## 权威报告谱系

| 文档族 | 阶段 | 主要提交/身份 | 原结论 | 当前有效性 |
|---|---|---|---|---|
| `audits/2026-07-26/00..10` | 初始全仓审计 | root `3ce28094...` 等历史身份 | 44 个去重 finding；production 禁用 | 历史基线，已被 Wave1/2/3 报告推进 |
| `audits/2026-07-26/11..16` | Wave 1 | root `5a0e6edd...`→`b4aba4a0...` | 文档、边界、治理第一轮落地，仍 blocked | 历史归档价值 |
| `audits/2026-07-26/20..22` | Wave 2 SITL 规格 | schema/offline only | 仅规格和 synthetic，不是 formal SITL | 作为测试规格仍有效 |
| `audits/2026-07-26/30..32` | repository cleanup | root `0a7f90da...` 周边 | 清理与静态验证完成 | 历史变更记录 |
| `audits/2026-07-27-wave3a/*` | Wave 3A | root `f34f5e64...`→`afb4fdce...`; Offboard `c744757a...` | 软件 oracle/unit-tested；DDS build 被串口路径阻塞 | 被 Wave 3B 阶段报告部分取代 |
| `audits/2026-07-27-wave3b/20..28` | Wave 3B | root final `0ed9d148...`; Offboard final `976d6217...` | 软件实现提交；总门未全过；formal SITL/hardware 未进入 | 最新阶段基线；若描述当前工作区则部分过时 |
| `handoff.md`、`planning/NEXT_PARALLEL_TASKS.md` | Wave 3B handoff | 同上 | 仅允许关闭软件 blocker | 历史 handoff，需由本审查取代为当前导航 |
| architecture/ADR/runbooks/interfaces | 持续性规范 | 多数不绑定当前 HEAD | DDS-only、逐级 promotion、fail-closed | 规范仍有效，不是执行证据 |

## 全文件清单

字段说明：`身份/门禁` 对非报告写 `N/A`；`有效性` 采用 `CURRENT_REFERENCE`、
`HISTORICAL`、`PARTIALLY_STALE`、`SUPERSEDED` 或 `CURRENT_ARTIFACT`。

| 相对路径 | 类型 | Git | 最后提交 | 提交时间 | 标题/用途 | 阶段/角色 | 身份/门禁/硬件/SITL | 阻塞/后续 | 当前有效性 |
|---|---|---|---|---|---|---|---|---|---|
| `CONTROL_AUTHORITY_MATRIX.md` | MD | tracked | `3ce2809` | 2026-07-25T22:20:58+08:00 | 控制权与发布者矩阵 | reference | N/A | — | CURRENT_REFERENCE |
| `adr/0001-dds-only-control-authority.md` | MD | tracked | `3ce2809` | 2026-07-25T22:20:58+08:00 | ADR-0001：DDS-only 控制权与视觉权威路径 | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `adr/0002-authority-command-envelope.md` | MD | tracked | `afb4fdc` | 2026-07-27T16:07:03+08:00 | ADR-0002：控制权 command envelope 与 fail-closed consumer 边界 | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `architecture/CONTROL_AUTHORITY.md` | MD | tracked | `656ebce` | 2026-07-26T18:10:48+08:00 | BoomBoomFly 控制权运行契约 | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `architecture/DATA_FLOW.md` | MD | tracked | `656ebce` | 2026-07-26T18:10:48+08:00 | BoomBoomFly 数据流与 topic 契约 | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `architecture/DEPLOYMENT_TOPOLOGY.md` | MD | tracked | `656ebce` | 2026-07-26T18:10:48+08:00 | BoomBoomFly 部署拓扑 | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `architecture/FAULT_PROPAGATION.md` | MD | tracked | `656ebce` | 2026-07-26T18:10:48+08:00 | BoomBoomFly 故障传播与安全评审边界 | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `architecture/NODE_INVENTORY.md` | MD | tracked | `656ebce` | 2026-07-26T18:10:48+08:00 | BoomBoomFly 节点与进程清单 | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `architecture/SYSTEM_OVERVIEW.md` | MD | tracked | `656ebce` | 2026-07-26T18:10:48+08:00 | BoomBoomFly 系统架构总览 | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `audits/2026-07-26/00_EXECUTIVE_SUMMARY.md` | MD | tracked | `1e385c2` | 2026-07-26T16:55:18+08:00 | BoomBoomFly 工程审查执行摘要 | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/01_REPOSITORY_AND_DEPENDENCIES.md` | MD | tracked | `1e385c2` | 2026-07-26T16:55:18+08:00 | 01 — 仓库结构与依赖可复现性审查 | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/02_BUILD_TEST_AND_CI.md` | MD | tracked | `531c9b0` | 2026-07-26T16:40:47+08:00 | 02 — 构建系统、测试与 CI 审查 | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/03_PX4_DDS_OFFBOARD_CONTRACT.md` | MD | tracked | `531c9b0` | 2026-07-26T16:40:47+08:00 | PX4、DDS 与 Offboard 接口契约审查 | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/04_SAFETY_AND_CONTROL_AUTHORITY.md` | MD | tracked | `531c9b0` | 2026-07-26T16:40:47+08:00 | 控制权、安全与故障处理审查 | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/05_PERCEPTION_AND_INTEGRATION.md` | MD | tracked | `531c9b0` | 2026-07-26T16:40:47+08:00 | 05 感知、硬件接口与系统集成审查 | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/06_DOCUMENTATION_AND_GOVERNANCE.md` | MD | tracked | `1e385c2` | 2026-07-26T16:55:18+08:00 | 文档、运维、安全与项目治理审查 | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/07_FINDINGS_REGISTER.md` | MD | tracked | `531c9b0` | 2026-07-26T16:40:47+08:00 | BoomBoomFly 统一发现登记册 | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/08_ROADMAP.md` | MD | tracked | `531c9b0` | 2026-07-26T16:40:47+08:00 | BoomBoomFly 下一阶段工程路线图 | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/09_VALIDATION_MATRIX.md` | MD | tracked | `531c9b0` | 2026-07-26T16:40:47+08:00 | BoomBoomFly 验证矩阵 | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/10_NEXT_CODEX_TASKS.md` | MD | tracked | `531c9b0` | 2026-07-26T16:40:47+08:00 | 下一轮 Codex 任务包 | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/11_WAVE1_EXECUTION.md` | MD | tracked | `11058dc` | 2026-07-26T22:01:01+08:00 | BoomBoomFly Wave 1 execution | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/12_WAVE1_VALIDATION.md` | MD | tracked | `11058dc` | 2026-07-26T22:01:01+08:00 | BoomBoomFly Wave 1 validation | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/13_WAVE2_READINESS.md` | MD | tracked | `11058dc` | 2026-07-26T22:01:01+08:00 | BoomBoomFly Wave 2 readiness | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/14_ARCHITECTURE_AND_RUNBOOK_EXECUTION.md` | MD | tracked | `8b1db51` | 2026-07-26T18:10:48+08:00 | BBF-DOC-WAVE 架构与运行手册执行记录 | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/15_DOCUMENT_CONSISTENCY_REVIEW.md` | MD | tracked | `8b1db51` | 2026-07-26T18:10:48+08:00 | BBF-DOC-WAVE 文档一致性审查 | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/16_NEXT_WORK_ASSIGNMENT.md` | MD | tracked | `8b1db51` | 2026-07-26T18:10:48+08:00 | BBF-DOC-WAVE 下一阶段工作安排建议 | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/20_SITL_SPEC_EXECUTION.md` | MD | tracked | `42d458d` | 2026-07-26T21:09:36+08:00 | BBF-SITL-SPEC-WAVE 执行记录 | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/21_SITL_SCENARIO_REGISTER.md` | MD | tracked | `42d458d` | 2026-07-26T21:09:36+08:00 | BBF-SITL-SPEC-WAVE 场景登记册 | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/21_WAVE2_DEPENDENCY_MANIFEST_REVIEW.md` | MD | tracked | `f34f5e6` | 2026-07-26T22:58:48+08:00 | Repository Cleanup Wave 2：依赖与 manifest 审查 | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/22_SITL_IMPLEMENTATION_HANDOFF.md` | MD | tracked | `42d458d` | 2026-07-26T21:09:36+08:00 | BBF-SITL-SPEC-WAVE 实现交接 | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/30_REPOSITORY_CLEANUP_AUDIT.md` | MD | tracked | `f34f5e6` | 2026-07-26T22:58:48+08:00 | Repository Cleanup Wave 2 审计 | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/31_CLEANUP_CHANGELOG.md` | MD | tracked | `f34f5e6` | 2026-07-26T22:58:48+08:00 | Repository Cleanup Wave 2 Changelog | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/32_POST_CLEANUP_VALIDATION.md` | MD | tracked | `f34f5e6` | 2026-07-26T22:58:48+08:00 | Repository Cleanup Wave 2：Post-cleanup Validation | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-26/CORRECTIONS.md` | MD | tracked | `1264e1e` | 2026-07-26T22:57:44+08:00 | 2026-07-26 Audit Corrections | 2026-07-26 audit/Wave1/Wave2 | 历史提交；门禁见原报告；不能代表当前；SITL 多为 synthetic/not-run | 由 Wave 3A/3B 与本审查取代当前状态 | HISTORICAL |
| `audits/2026-07-27-wave3a/00_BASELINE_OWNERSHIP.md` | MD | tracked | `afb4fdc` | 2026-07-27T16:07:03+08:00 | Wave 3A baseline and ownership | Wave 3A report | root f34f5e64→afb4fdce；H0/H1 blocked；HW NO；SITL NO | 被 Wave 3B 阶段推进 | SUPERSEDED |
| `audits/2026-07-27-wave3a/10_CANONICAL_VALIDATION.md` | MD | tracked | `afb4fdc` | 2026-07-27T16:07:03+08:00 | Wave 3A canonical validation ledger | Wave 3A report | root f34f5e64→afb4fdce；H0/H1 blocked；HW NO；SITL NO | 被 Wave 3B 阶段推进 | SUPERSEDED |
| `audits/2026-07-27-wave3a/11_WAVE3A_SUMMARY.md` | MD | tracked | `afb4fdc` | 2026-07-27T16:07:03+08:00 | Wave 3A summary and handoff | Wave 3A report | root f34f5e64→afb4fdce；H0/H1 blocked；HW NO；SITL NO | 被 Wave 3B 阶段推进 | SUPERSEDED |
| `audits/2026-07-27-wave3a/A1_PX4_RC_CHANNELS_ALIGNMENT.md` | MD | tracked | `afb4fdc` | 2026-07-27T16:07:03+08:00 | Wave 3A A1 — PX4 v1.16.2 `RcChannels` source/message/profile alignment | Wave 3A report | root f34f5e64→afb4fdce；H0/H1 blocked；HW NO；SITL NO | 被 Wave 3B 阶段推进 | SUPERSEDED |
| `audits/2026-07-27-wave3a/C1_AUTHORITY_CONTRACT.md` | MD | tracked | `afb4fdc` | 2026-07-27T16:07:03+08:00 | Wave 3A C1 — Authority envelope contract | Wave 3A report | root f34f5e64→afb4fdce；H0/H1 blocked；HW NO；SITL NO | 被 Wave 3B 阶段推进 | SUPERSEDED |
| `audits/2026-07-27-wave3a/D1_CI_DESIGN.md` | MD | tracked | `afb4fdc` | 2026-07-27T16:07:03+08:00 | Wave 3A D1 — locked offline CI gate design | Wave 3A report | root f34f5e64→afb4fdce；H0/H1 blocked；HW NO；SITL NO | 被 Wave 3B 阶段推进 | SUPERSEDED |
| `audits/2026-07-27-wave3a/G1_DEPENDENCY_PROFILE_DESIGN.md` | MD | tracked | `afb4fdc` | 2026-07-27T16:07:03+08:00 | Wave 3A G1 — archive and optional dependency source-profile design | Wave 3A report | root f34f5e64→afb4fdce；H0/H1 blocked；HW NO；SITL NO | 被 Wave 3B 阶段推进 | SUPERSEDED |
| `audits/2026-07-27-wave3a/H_HARDWARE_INVENTORY.md` | MD | tracked | `afb4fdc` | 2026-07-27T16:07:03+08:00 | Wave 3A H — Preliminary hardware inventory | Wave 3A report | root f34f5e64→afb4fdce；H0/H1 blocked；HW NO；SITL NO | 被 Wave 3B 阶段推进 | SUPERSEDED |
| `audits/2026-07-27-wave3b/20_BASELINE_AND_OWNERSHIP.md` | MD | tracked | `0ed9d14` | 2026-07-27T17:18:33+08:00 | Wave 3B baseline and ownership | Wave 3B report | root 0ed9d148／Offboard 976d6217；H0/H1 not run；HW NO；SITL NO | PX4/toolchain、Offboard lock、live gate、serial、CI lock | PARTIALLY_STALE |
| `audits/2026-07-27-wave3b/21_PX4_PROVENANCE.md` | MD | tracked | `d45c474` | 2026-07-27T17:16:45+08:00 | Wave 3B A2 — PX4 exact source and toolchain provenance | Wave 3B report | root 0ed9d148／Offboard 976d6217；H0/H1 not run；HW NO；SITL NO | PX4/toolchain、Offboard lock、live gate、serial、CI lock | PARTIALLY_STALE |
| `audits/2026-07-27-wave3b/22_BC_RUNTIME_INTEGRATION.md` | MD | tracked | `0ed9d14` | 2026-07-27T17:18:33+08:00 | Wave 3B B2/C2 runtime integration | Wave 3B report | root 0ed9d148／Offboard 976d6217；H0/H1 not run；HW NO；SITL NO | PX4/toolchain、Offboard lock、live gate、serial、CI lock | PARTIALLY_STALE |
| `audits/2026-07-27-wave3b/23_CI_IMPLEMENTATION.md` | MD | tracked | `0ed9d14` | 2026-07-27T17:18:33+08:00 | Wave 3B D2 — local offline CI implementation | Wave 3B report | root 0ed9d148／Offboard 976d6217；H0/H1 not run；HW NO；SITL NO | PX4/toolchain、Offboard lock、live gate、serial、CI lock | PARTIALLY_STALE |
| `audits/2026-07-27-wave3b/24_MANIFEST_MIGRATION_AND_SERIAL_DECISION.md` | MD | tracked | `0ed9d14` | 2026-07-27T17:18:33+08:00 | Wave 3B G2 — manifest migration and serial decision | Wave 3B report | root 0ed9d148／Offboard 976d6217；H0/H1 not run；HW NO；SITL NO | PX4/toolchain、Offboard lock、live gate、serial、CI lock | PARTIALLY_STALE |
| `audits/2026-07-27-wave3b/25_OFFLINE_ACCEPTANCE.md` | MD | tracked | `0ed9d14` | 2026-07-27T17:18:33+08:00 | Wave 3B F2 — offline acceptance integration | Wave 3B report | root 0ed9d148／Offboard 976d6217；H0/H1 not run；HW NO；SITL NO | PX4/toolchain、Offboard lock、live gate、serial、CI lock | PARTIALLY_STALE |
| `audits/2026-07-27-wave3b/26_PROP_OFF_BENCH_READINESS.md` | MD | tracked | `0ed9d14` | 2026-07-27T17:18:33+08:00 | Wave 3B prop-off bench readiness | Wave 3B report | root 0ed9d148／Offboard 976d6217；H0/H1 not run；HW NO；SITL NO | PX4/toolchain、Offboard lock、live gate、serial、CI lock | PARTIALLY_STALE |
| `audits/2026-07-27-wave3b/27_WAVE3B_VALIDATION.md` | MD | tracked | `0ed9d14` | 2026-07-27T17:18:33+08:00 | Wave 3B canonical validation ledger | Wave 3B report | root 0ed9d148／Offboard 976d6217；H0/H1 not run；HW NO；SITL NO | PX4/toolchain、Offboard lock、live gate、serial、CI lock | PARTIALLY_STALE |
| `audits/2026-07-27-wave3b/28_WAVE3B_SUMMARY.md` | MD | tracked | `0ed9d14` | 2026-07-27T17:18:33+08:00 | Wave 3B summary and gate decision | Wave 3B report | root 0ed9d148／Offboard 976d6217；H0/H1 not run；HW NO；SITL NO | PX4/toolchain、Offboard lock、live gate、serial、CI lock | PARTIALLY_STALE |
| `authority/WAVE3B_BC_INTERFACE_FREEZE.md` | MD | tracked | `0ed9d14` | 2026-07-27T17:18:33+08:00 | Wave 3B B/C runtime interface freeze | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `authority/schemas/authority-envelope.schema.json` | JSON | tracked | `afb4fdc` | 2026-07-27T16:07:03+08:00 | authority-envelope.schema.json | schema | N/A | 由 validator/测试消费 | CURRENT_ARTIFACT |
| `dependencies/SOURCE_PROFILES.md` | MD | tracked | `727abb3` | 2026-07-27T17:16:46+08:00 | Dependency source profiles | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `evidence/DDS_ONLY_LAUNCH_BOUNDARY_2026-07-26.md` | MD | tracked | `a78dd64` | 2026-07-26T20:16:13+08:00 | DDS-only launch boundary | dated evidence | 历史专项证据；按文内 scope，不代表本轮硬件/SITL | 需绑定当前 workspace/source | HISTORICAL |
| `evidence/DDS_ONLY_PACKAGE_BOUNDARY_2026-07-26.md` | MD | tracked | `b13a081` | 2026-07-26T20:06:07+08:00 | DDS-only package boundary — 2026-07-26 | dated evidence | 历史专项证据；按文内 scope，不代表本轮硬件/SITL | 需绑定当前 workspace/source | HISTORICAL |
| `evidence/EVIDENCE_SCHEMA_20260726.md` | MD | tracked | `16a1367` | 2026-07-26T17:44:09+08:00 | Evidence schema remediation — 2026-07-26 | reference | N/A | — | CURRENT_REFERENCE |
| `evidence/OFFBOARD_PX4_MSGS_COMPAT_20260724.md` | MD | tracked | `1e385c2` | 2026-07-26T16:55:18+08:00 | Offboard / px4_msgs v1.16.2 compatibility evidence | dated evidence | 历史专项证据；按文内 scope，不代表本轮硬件/SITL | 需绑定当前 workspace/source | HISTORICAL |
| `evidence/PX4_PARAMS_20260724T203458+0800.json` | JSON | tracked | `3b296de` | 2026-07-24T23:00:48+08:00 | PX4_PARAMS_20260724T203458+0800.json | historical hardware evidence | 历史硬件参数快照；非本轮；SITL NO | 不得当 current 参数 | HISTORICAL |
| `evidence/RELEASE_TEMPLATE.yaml` | YAML | tracked | `16a1367` | 2026-07-26T17:44:09+08:00 | RELEASE_TEMPLATE.yaml | reference | N/A | — | CURRENT_REFERENCE |
| `evidence/ROLLBACK_TEMPLATE.yaml` | YAML | tracked | `80452c1` | 2026-07-26T20:56:21+08:00 | ROLLBACK_TEMPLATE.yaml | reference | N/A | — | CURRENT_REFERENCE |
| `evidence/SCHEMA.md` | MD | tracked | `80452c1` | 2026-07-26T20:56:21+08:00 | BoomBoomFly evidence, release, and rollback schema | reference | N/A | — | CURRENT_REFERENCE |
| `evidence/TOOLCHAIN_BASELINE_20260726.md` | MD | tracked | `97b10c9` | 2026-07-26T20:00:18+08:00 | BoomBoomFly toolchain baseline — 2026-07-26 | reference | N/A | — | CURRENT_REFERENCE |
| `evidence/WORKSPACE_BASELINE_2026-07-26.md` | MD | tracked | `73e3634` | 2026-07-26T20:00:30+08:00 | BoomBoomFly preserved checkout baseline receipt | reference | N/A | — | CURRENT_REFERENCE |
| `evidence/environment/current_environment.json` | JSON | tracked | `97b10c9` | 2026-07-26T20:00:18+08:00 | current_environment.json | environment evidence | 采集于 Wave 1；记录 PX4 source absent | 当前 external/PX4-Autopilot 已存在 | PARTIALLY_STALE |
| `evidence/environment/px4_source_toolchain_lock.template.json` | JSON | tracked | `97b10c9` | 2026-07-26T20:00:18+08:00 | px4_source_toolchain_lock.template.json | reference | N/A | — | CURRENT_REFERENCE |
| `evidence/index.yaml` | YAML | tracked | `16a1367` | 2026-07-26T17:44:09+08:00 | index.yaml | reference | N/A | — | CURRENT_REFERENCE |
| `evidence/receipts/APPROVALS.md` | MD | tracked | `3a29c46` | 2026-07-26T21:29:35+08:00 | Workspace receipt approvals | dependency receipt/artifact | receipt 自身多为 unverified；HW/SITL N/A | 审批/当前树复核 | CURRENT_ARTIFACT |
| `evidence/receipts/approvals/trusted_maintainers.json` | JSON | tracked | `3a29c46` | 2026-07-26T21:29:35+08:00 | trusted_maintainers.json | dependency receipt/artifact | receipt 自身多为 unverified；HW/SITL N/A | 审批/当前树复核 | CURRENT_ARTIFACT |
| `evidence/receipts/librealsense.json` | JSON | tracked | `73e3634` | 2026-07-26T20:00:30+08:00 | librealsense.json | dependency receipt/artifact | receipt 自身多为 unverified；HW/SITL N/A | 审批/当前树复核 | CURRENT_ARTIFACT |
| `evidence/receipts/navigation_msgs.json` | JSON | tracked | `73e3634` | 2026-07-26T20:00:30+08:00 | navigation_msgs.json | dependency receipt/artifact | receipt 自身多为 unverified；HW/SITL N/A | 审批/当前树复核 | CURRENT_ARTIFACT |
| `evidence/receipts/patches/librealsense.patch.b64` | B64 | tracked | `73e3634` | 2026-07-26T20:00:30+08:00 | librealsense.patch.b64 | dependency receipt/artifact | receipt 自身多为 unverified；HW/SITL N/A | 审批/当前树复核 | CURRENT_ARTIFACT |
| `evidence/receipts/patches/navigation_msgs.patch.b64` | B64 | tracked | `73e3634` | 2026-07-26T20:00:30+08:00 | navigation_msgs.patch.b64 | dependency receipt/artifact | receipt 自身多为 unverified；HW/SITL N/A | 审批/当前树复核 | CURRENT_ARTIFACT |
| `evidence/receipts/patches/realsense_ros.patch.b64` | B64 | tracked | `73e3634` | 2026-07-26T20:00:30+08:00 | realsense_ros.patch.b64 | dependency receipt/artifact | receipt 自身多为 unverified；HW/SITL N/A | 审批/当前树复核 | CURRENT_ARTIFACT |
| `evidence/receipts/patches/vision_opencv.patch.b64` | B64 | tracked | `73e3634` | 2026-07-26T20:00:30+08:00 | vision_opencv.patch.b64 | dependency receipt/artifact | receipt 自身多为 unverified；HW/SITL N/A | 审批/当前树复核 | CURRENT_ARTIFACT |
| `evidence/receipts/realsense_ros.json` | JSON | tracked | `73e3634` | 2026-07-26T20:00:30+08:00 | realsense_ros.json | dependency receipt/artifact | receipt 自身多为 unverified；HW/SITL N/A | 审批/当前树复核 | CURRENT_ARTIFACT |
| `evidence/receipts/vision_opencv.json` | JSON | tracked | `73e3634` | 2026-07-26T20:00:30+08:00 | vision_opencv.json | dependency receipt/artifact | receipt 自身多为 unverified；HW/SITL N/A | 审批/当前树复核 | CURRENT_ARTIFACT |
| `evidence/schemas/environment.schema.json` | JSON | tracked | `97b10c9` | 2026-07-26T20:00:18+08:00 | environment.schema.json | schema | N/A | 由 validator/测试消费 | CURRENT_ARTIFACT |
| `evidence/schemas/evidence.schema.json` | JSON | tracked | `16a1367` | 2026-07-26T17:44:09+08:00 | evidence.schema.json | schema | N/A | 由 validator/测试消费 | CURRENT_ARTIFACT |
| `evidence/schemas/evidence_index.schema.json` | JSON | tracked | `16a1367` | 2026-07-26T17:44:09+08:00 | evidence_index.schema.json | schema | N/A | 由 validator/测试消费 | CURRENT_ARTIFACT |
| `evidence/schemas/px4_source_toolchain_lock.schema.json` | JSON | tracked | `97b10c9` | 2026-07-26T20:00:18+08:00 | px4_source_toolchain_lock.schema.json | schema | N/A | 由 validator/测试消费 | CURRENT_ARTIFACT |
| `evidence/schemas/release.schema.json` | JSON | tracked | `16a1367` | 2026-07-26T17:44:09+08:00 | release.schema.json | schema | N/A | 由 validator/测试消费 | CURRENT_ARTIFACT |
| `evidence/schemas/rollback.schema.json` | JSON | tracked | `80452c1` | 2026-07-26T20:56:21+08:00 | rollback.schema.json | schema | N/A | 由 validator/测试消费 | CURRENT_ARTIFACT |
| `evidence/schemas/workspace_receipt.schema.json` | JSON | tracked | `3a29c46` | 2026-07-26T21:29:35+08:00 | workspace_receipt.schema.json | schema | N/A | 由 validator/测试消费 | CURRENT_ARTIFACT |
| `evidence/schemas/workspace_receipt_approval.schema.json` | JSON | tracked | `3a29c46` | 2026-07-26T21:29:35+08:00 | workspace_receipt_approval.schema.json | schema | N/A | 由 validator/测试消费 | CURRENT_ARTIFACT |
| `governance/CODEOWNERS_PROPOSAL.md` | MD | tracked | `ce15729` | 2026-07-26T22:57:58+08:00 | CODEOWNERS Proposal | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `governance/DOCUMENT_AUTHORITY.md` | MD | tracked | `1264e1e` | 2026-07-26T22:57:44+08:00 | Document Authority | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `governance/RELEASE_POLICY.md` | MD | tracked | `7b978b1` | 2026-07-26T18:10:48+08:00 | Release Policy | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `governance/REVIEW_POLICY.md` | MD | tracked | `ce15729` | 2026-07-26T22:57:58+08:00 | Review Policy | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `handoff.md` | MD | tracked | `2892041` | 2026-07-27T17:16:47+08:00 | BoomBoomFly Wave 3B handoff | Wave 3B handoff/plan | root final 0ed9d148；NO-GO；HW NO；SITL NO | 当前 PX4/communication/serial 漂移未记录 | PARTIALLY_STALE |
| `planning/BACKLOG.md` | MD | tracked | `f34f5e6` | 2026-07-26T22:58:48+08:00 | BoomBoomFly P0/P1 执行 Backlog | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `planning/DEFINITION_OF_DONE.md` | MD | tracked | `f44cb48` | 2026-07-26T18:10:48+08:00 | Definition of Done 与验收责任 | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `planning/DEPENDENCY_GRAPH.md` | MD | tracked | `f34f5e6` | 2026-07-26T22:58:48+08:00 | BoomBoomFly 工作线依赖图 | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `planning/MILESTONES.md` | MD | tracked | `f34f5e6` | 2026-07-26T22:58:48+08:00 | BoomBoomFly Milestones | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `planning/NEXT_PARALLEL_TASKS.md` | MD | tracked | `2892041` | 2026-07-27T17:16:47+08:00 | 下一波并行任务 | Wave 3B handoff/plan | root final 0ed9d148；NO-GO；HW NO；SITL NO | 当前 PX4/communication/serial 漂移未记录 | PARTIALLY_STALE |
| `runbooks/BENCH_ACCEPTANCE_DRAFT.md` | MD | tracked | `be23e78` | 2026-07-26T18:10:48+08:00 | 拆桨台架验收草案 | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `runbooks/LIMITED_FLIGHT_ACCEPTANCE_DRAFT.md` | MD | tracked | `be23e78` | 2026-07-26T18:10:48+08:00 | 有限实机控制验收草案 | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `runbooks/PROP_OFF_BENCH_SAFETY.md` | MD | tracked | `afb4fdc` | 2026-07-27T16:07:03+08:00 | Prop-off bench safety runbook | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `runbooks/SITL_ACCEPTANCE.md` | MD | tracked | `5f54d0d` | 2026-07-26T21:09:36+08:00 | PX4 DDS SITL 验收 | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `runbooks/SITL_SCENARIO_CATALOG.md` | MD | tracked | `5f54d0d` | 2026-07-26T21:09:36+08:00 | PX4 DDS SITL 场景目录 | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `runbooks/VALIDATION_LEVELS.md` | MD | tracked | `be23e78` | 2026-07-26T18:10:48+08:00 | BoomBoomFly 分级验证门 | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `verification/EVENT_TIMELINE.md` | MD | tracked | `e9b37de` | 2026-07-26T21:09:36+08:00 | SITL event timeline and offline assertions | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `verification/FAULT_SCENARIOS.md` | MD | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | PX4 DDS SITL 故障注入场景 | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `verification/NORMAL_SCENARIOS.md` | MD | tracked | `222fc26` | 2026-07-26T21:09:36+08:00 | SITL 正常流程场景 | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `verification/SITL_SCENARIO_SCHEMA.md` | MD | tracked | `7e29d7c` | 2026-07-26T21:09:36+08:00 | SITL 场景机器可读契约 | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `verification/SITL_STATIC_VALIDATION.md` | MD | tracked | `16cb11a` | 2026-07-26T21:09:36+08:00 | SITL static validation | normative/reference | 规范，不是执行证据；HW/SITL N/A | 实施状态另见 dated audit | CURRENT_REFERENCE |
| `verification/scenarios/catalog.json` | JSON | tracked | `d4588d8` | 2026-07-27T17:16:47+08:00 | catalog.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-001.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-001.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-002.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-002.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-003.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-003.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-004.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-004.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-005.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-005.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-006.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-006.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-007.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-007.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-008.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-008.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-009.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-009.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-010.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-010.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-011.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-011.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-012.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-012.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-013.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-013.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-014.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-014.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-015.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-015.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-016.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-016.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-017.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-017.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-018.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-018.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-019.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-019.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-020.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-020.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-021.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-021.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-022.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-022.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-023.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-023.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-024.json` | JSON | tracked | `675a68e` | 2026-07-26T21:09:36+08:00 | SITL-FAULT-024.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/faults/SITL-FAULT-025.json` | JSON | tracked | `d4588d8` | 2026-07-27T17:16:47+08:00 | SITL-FAULT-025.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/normal/SITL-NORMAL-001.json` | JSON | tracked | `222fc26` | 2026-07-26T21:09:36+08:00 | SITL-NORMAL-001.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/normal/SITL-NORMAL-002.json` | JSON | tracked | `222fc26` | 2026-07-26T21:09:36+08:00 | SITL-NORMAL-002.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/normal/SITL-NORMAL-003.json` | JSON | tracked | `222fc26` | 2026-07-26T21:09:36+08:00 | SITL-NORMAL-003.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/normal/SITL-NORMAL-004.json` | JSON | tracked | `222fc26` | 2026-07-26T21:09:36+08:00 | SITL-NORMAL-004.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/normal/SITL-NORMAL-005.json` | JSON | tracked | `222fc26` | 2026-07-26T21:09:36+08:00 | SITL-NORMAL-005.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/normal/SITL-NORMAL-006.json` | JSON | tracked | `222fc26` | 2026-07-26T21:09:36+08:00 | SITL-NORMAL-006.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/normal/SITL-NORMAL-007.json` | JSON | tracked | `222fc26` | 2026-07-26T21:09:36+08:00 | SITL-NORMAL-007.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/normal/SITL-NORMAL-008.json` | JSON | tracked | `222fc26` | 2026-07-26T21:09:36+08:00 | SITL-NORMAL-008.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/normal/SITL-NORMAL-009.json` | JSON | tracked | `222fc26` | 2026-07-26T21:09:36+08:00 | SITL-NORMAL-009.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/normal/SITL-NORMAL-010.json` | JSON | tracked | `222fc26` | 2026-07-26T21:09:36+08:00 | SITL-NORMAL-010.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/normal/SITL-NORMAL-011.json` | JSON | tracked | `222fc26` | 2026-07-26T21:09:36+08:00 | SITL-NORMAL-011.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/scenarios/normal/SITL-NORMAL-012.json` | JSON | tracked | `222fc26` | 2026-07-26T21:09:36+08:00 | SITL-NORMAL-012.json | offline SITL-spec fixture | OFFLINE_SYNTHETIC；formal SITL false；HW NO | 不得提升为 formal SITL | CURRENT_ARTIFACT |
| `verification/schemas/event.schema.json` | JSON | tracked | `7e29d7c` | 2026-07-26T21:09:36+08:00 | event.schema.json | schema | N/A | 由 validator/测试消费 | CURRENT_ARTIFACT |
| `verification/schemas/result.schema.json` | JSON | tracked | `7e29d7c` | 2026-07-26T21:09:36+08:00 | result.schema.json | schema | N/A | 由 validator/测试消费 | CURRENT_ARTIFACT |
| `verification/schemas/scenario.schema.json` | JSON | tracked | `7e29d7c` | 2026-07-26T21:09:36+08:00 | scenario.schema.json | schema | N/A | 由 validator/测试消费 | CURRENT_ARTIFACT |
