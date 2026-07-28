# 文档、过时文件与清理结果

## [P2-DOC-001] 旧报告、handoff 与当前 master/checkout 不一致（已清理）

- 严重度：P2
- 状态：已确认，已清理
- 领域：Docs / Git
- 位置：
  - 删除前的 `docs/handoff.md`
  - 删除前的 `docs/audits/**`
  - 删除前的 `docs/current_audit/**`
  - `README.md:9-25`
  - `docs/repository_audit/00_EXECUTIVE_SUMMARY.md`
- 证据：
  - 旧 handoff 和日期化报告绑定旧 branch/HEAD；当前根基线为
    `master@df01b9280c0e79a05ad1e4cec727e7427c9251ca`。
  - 当前 checkout 的 exact-lock comparison 与旧候选身份不一致。
  - 用户明确授权不保留历史性报告和历史 evidence。
  - 删除后 README、ADR、architecture、governance、测试约束和当前报告均改指向
    `docs/repository_audit/**`。
- 影响：
  - 清除误把旧 GO/旧 SHA 当成当前事实的入口。
  - 被删内容仍可从 Git 历史恢复；源码、配置和机器验证契约未删除。
- 根因：
  - 多轮审查以 `current`/Wave 命名留在工作树，且没有自动 freshness 门。
- 建议：
  - 后续审查只维护一个当前入口；新报告生成时在同一变更中替换旧入口。
  - dated evidence 只有在仍被验证器、schema、receipt 或安全门消费时才保留。
- 前置条件：
  - 提交前运行引用检查、evidence validator 和 repository cleanup tests。
- 是否涉及硬件：
  - 否

## 已执行删除

| 文件 | 判断 | 证据 | 风险 | 建议动作 |
|---|---|---|---|---|
| `docs/audits/**` | 过时报告 | 绑定旧 SHA，已由统一审查取代 | 工作树内历史链消失 | 已删除；Git 可恢复 |
| `docs/current_audit/**` | 重复/过时报告 | 目录名暗示 current，但绑定旧 checkout | 旧入口误导 | 已删除；Git 可恢复 |
| `docs/handoff.md` | 失效入口 | branch/HEAD 与当前不一致 | 旧 GO 被误用 | 已删除；入口迁至 README/当前审查 |
| `docs/evidence/*20260724*`、`*2026-07-26*` | 历史证据/旧基线 | 仅历史索引或无活跃消费方 | 丢失工作树内旧快照 | 已删除；索引已清空，Git 可恢复 |
| `docs/planning/BACKLOG.md`、`DEPENDENCY_GRAPH.md`、`MILESTONES.md` | 旧 Wave 规划 | 无入站引用，仍指向已删 handoff/audit | 丢失旧任务映射 | 已删除；当前计划为 `10_NEXT_STAGE_PLAN.md` |

本次共删除 86 个受 Git 管理的旧报告、handoff、dated evidence 和 planning 文件。
未删除源码、配置、ADR、architecture、authority schema、dependency profile、receipt、
环境/供应链 validator 输入、runbook、verification 场景或其他清理候选。

## 保留项及理由

| 路径 | 结论 | 证据 |
|---|---|---|
| `docs/adr/**` | 保留 | Accepted/Proposed 决策仍被架构与控制权规范引用 |
| `docs/architecture/**` | 保留并待刷新基线 | 含唯一 topic、writer、部署、故障与节点契约 |
| `docs/authority/**` | 保留 | schema 被 authority tests 与运行时代码消费 |
| `docs/dependencies/SOURCE_PROFILES.md` | 保留 | `Scripts/README.md` 当前引用 |
| `docs/evidence/schemas/**`、templates、environment、receipts | 保留 | 被 CI、验证脚本和单元测试直接消费 |
| `docs/runbooks/**` | 保留 | 当前分级安全门；文档存在不授予硬件权限 |
| `docs/verification/**` | 保留 | scenario catalog、schema 和 fixtures 是测试权威输入 |

## 仍需后续修正但不可删除

- `docs/architecture/*.md` 的静态基线仍指向旧 HEAD，应在 Phase 0 重新核验后刷新。
- `docs/runbooks/SITL_ACCEPTANCE.md` 的示例路径使用不存在的 `timeline.jsonl`；实际 fixture
  是 `synthetic_timeline.jsonl`，应单独修正并验证。
- `docs/runbooks/PROP_OFF_BENCH_SAFETY.md` 状态为 Proposed，却包含易被误读为授权的
  `AUTHORIZED` 表述；在独立人工授权来源确认前不得执行硬件步骤。
