# 文档治理与清理候选

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

## 治理结论

```text
CURRENT AUTHORITATIVE DOCUMENT SET: PARTIALLY CONSISTENT
DATED AUDITS: RETAIN AS HISTORICAL EVIDENCE
WAVE 3B: LATEST HISTORICAL BASELINE, PARTIALLY STALE
HANDOFF: PARTIALLY STALE
ACTIVE PLANNING: PARTIALLY STALE / MIXED WITH HISTORY
SITL HUMAN-READABLE CATALOG: INCONSISTENT WITH MACHINE CATALOG
DIRECT DELETE CANDIDATES: NONE
EVIDENCE/RECEIPT DELETE CANDIDATES: NONE
```

`governance/DOCUMENT_AUTHORITY.md:61-75` 要求保留 dated audit、原始 evidence、
receipts、schema 和参数快照，并通过 correction/supersession 解释。故本轮不提出
可无人工确认直接删除的文件。

## 分类

| 分类 | 文件族 | 说明 |
|---|---|---|
| 当前权威 | ADR-0001、control matrix、architecture、document/release/review policy、source profiles、evidence/verification schemas、machine scenario catalog | 规范/机器事实；实现状态文字部分需更新 |
| 当前参考 | B/C interface freeze、runbooks、verification prose、planning | 仍有用，但不能证明当前执行状态 |
| 最新历史基线 | `audits/2026-07-27-wave3b/**` | 阶段身份准确；当前 workspace/PX4/serial 动态事实部分过时 |
| 历史归档 | `audits/2026-07-26/**`、Wave 3A | 保留完整谱系，不删除 |
| 历史证据 | dated evidence、参数 snapshot、receipts、patches | 不可变；不得当 current |
| 临时导航 | `handoff.md` | 只应是短导航，当前部分过时 |
| Proposed/草案 | ADR-0002、CODEOWNERS proposal、acceptance drafts/templates | 不得当 Accepted/执行证据 |

## 清理候选

| 文件 | 分类 | 被什么取代 | 建议动作 | 风险 | 需人工确认 |
|---|---|---|---|---|---|
| `docs/handoff.md` | 临时、部分过期 | 本审查 00/03/05 | 更新为短导航；Wave 3B正文转 dated archive link | 丢交接上下文 | 是 |
| `planning/NEXT_PARALLEL_TASKS.md` | 重复、部分过期 | 本审查 07/08 | active改为Wave4；旧分工逻辑归档 | 丢ownership/安全边界 | 是 |
| `planning/BACKLOG.md` | 状态过期、定义仍有用 | findings+next plan | 逐 Task ID reconcile，不批量完成/删除 | 丢audit映射 | 是 |
| `planning/MILESTONES.md` | 部分过期 | 当前gate/plan | 更新状态，保留promotion规则 | 误删安全门 | 是 |
| `planning/DEPENDENCY_GRAPH.md` | 部分过期 | Wave3B+Wave4 plan | 更新节点状态，不删除依赖图 | 误并行修改 | 是 |
| `audits/2026-07-26/08_ROADMAP.md` | 被取代、历史 | 后续planning/Wave3 | 逻辑归档，禁止删除 | 丢历史关键路径 | 否 |
| `audits/2026-07-26/10_NEXT_CODEX_TASKS.md` | 被取代、历史 | 后续planning | 逻辑归档，禁止删除 | 丢初始验收标准 | 否 |
| `13_WAVE2_READINESS.md`、`16_NEXT_WORK_ASSIGNMENT.md`、`22_SITL_IMPLEMENTATION_HANDOFF.md` | 历史 handoff | Wave3A/B/current plan | 逻辑归档，禁止删除 | 丢阶段谱系 | 否 |
| `runbooks/SITL_SCENARIO_CATALOG.md` | 当前参考但失配 | machine catalog+Wave3B F2 | 更新24→25并标025 synthetic；不归档 | 操作入口错误 | 是 |
| `verification/FAULT_SCENARIOS.md` | 当前参考但失配 | machine catalog/025 | 补025与25-count | 安全场景遗漏 | 是 |
| `verification/SITL_STATIC_VALIDATION.md` | 当前参考但失配 | current tests/catalog | 更新测试布局/数量 | 误读离线覆盖 | 是 |
| `evidence/environment/current_environment.json` | 名称误导的历史snapshot | 新dated capture+current pointer | 先新增替代/迁移引用；现文件保留 | verifier依赖固定路径 | 是 |
| `runbooks/BENCH_ACCEPTANCE_DRAFT.md` | 旧草案/重叠 | prop-off runbook+未来正式acceptance | 逐项合并停止条件后归档 | 漏安全停止条件 | 是 |
| `CONTROL_AUTHORITY_MATRIX.md` 与 `architecture/CONTROL_AUTHORITY.md` | 表面重复 | ADR+runtime mapping | 不删除；减少重复状态并互链 | 层级不同，误合并 | 是 |

## 必须修正但不应删除的冲突

1. Machine catalog 已为 12 normal + 25 fault；三份人工文档仍写 24 fault。
2. `handoff.md` 仍写历史 branch/serial_driver_ros2，当前为 master、deleted gitlink、
   untracked dirty communication。
3. `current_environment.json` 绑定 Wave1/2026-07-26，却以 current 命名。
4. ADR-0002 仍 Proposed，但 Wave 3B 已冻结/单测实现；需正式 architecture decision。
5. architecture/matrix 将 graph/owner/ACK/PRESTREAM 全写 PLANNED；应拆分为
   library `IMPLEMENTED/UNIT_TESTED`、live integration `BLOCKED`、SITL `BLOCKED`。

## 推荐结构

```text
docs/
├── architecture/
├── decisions/
├── interfaces/
├── operations/
│   └── runbooks/
├── safety/
├── audits/
│   ├── current/
│   └── archive/YYYY-MM-DD-wave*/
├── evidence/
├── plans/
│   ├── current/
│   └── archive/
└── handoff.md
```

先建立逻辑索引和稳定链接，再迁移物理路径；任何移动/删除必须先复核 link、
evidence index、supersedes/correction 和验证脚本。
