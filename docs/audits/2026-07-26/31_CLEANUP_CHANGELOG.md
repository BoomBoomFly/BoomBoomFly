# Repository Cleanup Wave 2 Changelog

日期：2026-07-26
状态：`FINAL_RECONCILED`

本表已按协调线程最终工作树逐项核对。推荐 rollback 是对对应逻辑 commit 执行
`git revert <commit>`；这保留审计历史，也不会 reset/clean 任何 nested dirty
checkout。

## 删除

| 文件 | 原 ownership | 原因 | build/test/runtime 影响 | rollback |
|---|---|---|---|---|
| `Scripts/build/m1_build.sh` | 旧 build tooling | 删除 T265 + D435 + MAVROS 入口及失效 patch 路线 | 防止误执行旧 build；DDS-only build 不受影响 | revert “obsolete entrypoints” commit；仅在明确恢复历史工具时使用 |
| `Scripts/installation/car_install.sh` | installation | tracked empty，无实现 | 无 build/runtime 能力损失 | revert 删除 commit；不应以空文件代替实现 |
| `Scripts/simulation/uav_sim.sh` | simulation | tracked empty，无实现 | 无 SITL 能力损失；正式 SITL 仍 `BLOCKED` | revert 删除 commit；真实实现应进入 canonical orchestration |
| `Simulator/README.md` | simulator placeholder | 占位目录，无有效 orchestration | 无 runtime 影响 | revert 删除 commit |
| `Simulator/gazebo_simulator/README.md` | simulator placeholder | tracked empty | 无 runtime 影响 | revert 删除 commit |
| `Simulator/realsense_gazebo_plugin/README.md` | simulator placeholder | tracked empty | 无 runtime 影响 | revert 删除 commit |
| `CODEOWNERS.draft` | governance | 所有 owner 是角色占位符，且含外部 checkout/不存在 firmware profile 路径；根 draft 易被误启用 | enforcement 仍 `BLOCKED`；不创建 active CODEOWNERS | revert governance commit，只恢复 draft；不得把它复制到 GitHub active path |

## 修改

| 文件 | Wave 2 owner | 修改原因 | build/test/runtime 影响 | rollback |
|---|---|---|---|---|
| `.gitignore` | cleanup coordination | 忽略 Python bytecode；移除已删除 M1/MAVROS patch 的 exception；保留 current DDS-only build entrypoint | 防止离线验证产生的 `__pycache__` 污染 status；不改变 source build graph | revert cleanup commit；若仅回滚部分，重新核对 build entrypoint tracking |
| `README.md` | authority docs | 改为稳定项目入口，移除个人路径、临时 commit/device/blocker，明确 PX4 v1.16.2/uXRCE-DDS-only/no-go | 文档导航变化；不启用 runtime | revert docs authority commit |
| `Scripts/README.md` | authority docs | 只说明 current build/evidence/installation/test/SITL，修复 clone URL 和删除入口引用 | 操作员不再被引向旧脚本；不改变脚本行为 | revert docs authority commit |
| `docs/handoff.md` | authority docs | 使用动态 repo root，移除漂移状态和个人绝对路径 | handoff 变成临时导航；不改变 runtime | revert docs authority commit |
| `docs/governance/DOCUMENT_AUTHORITY.md` | authority docs/governance | 明确 ADR、architecture/matrix、handoff、planning、dated evidence、corrections/supersedes 的权威边界 | 降低历史材料误用风险；无 build 影响 | revert governance docs commit |
| `CONTRIBUTING.md` | governance | 指向不可启用 CODEOWNERS proposal，并明确当前无 enforcement | review 文档变化；无 runtime 影响 | revert governance commit |
| `docs/governance/REVIEW_POLICY.md` | governance | 增加 planned CI job graph、workflow 安全门和 required-check blocker | 不创建 workflow、不改远端规则；无 runtime 影响 | revert governance commit |
| `config/profiles/dds_only_packages.yaml` | test/profile integrity | 修正 forbidden serial gitlink 路径，补分类 `image_geometry`/`map_msgs` | 完整 package discovery 不再把两个包视为 unknown；production allowlist 和 forbidden names 未放宽 | revert test/profile commit，并重跑 boundary tests |
| `workspace.excluded_packages` | dependency review | 将旧 T265+D435 注释改成 authoritative DDS-only forbidden boundary | 13 个有效 package 名称未变；build boundary 行为不变 | revert dependency-doc commit；不得改变有效列表 |
| `docs/planning/BACKLOG.md` | planning | 加入 G 工作线 TASK-025–029 和 A–G 当前调度状态 | planning only；不代表实现 | revert planning commit |
| `docs/planning/MILESTONES.md` | planning | 更新 Wave 2 identity、M0 release-hygiene 门和 M3–M6 blocker | promotion 规则更明确；不执行测试/硬件 | revert planning commit |
| `docs/planning/DEPENDENCY_GRAPH.md` | planning | 重排 A–G、G release gate、E/F 前置和禁止并行关系 | planning only | revert planning commit |
| `docs/planning/NEXT_PARALLEL_TASKS.md` | planning | canonical 更新 A1–G5 的 owner、唯一范围、输入/输出/验收/状态/授权 | 后续调度入口；不授权范围外写入 | revert planning commit |

## 新增

| 文件 | Wave 2 owner | 新增原因 | build/test/runtime 影响 | rollback |
|---|---|---|---|---|
| `docs/audits/2026-07-26/CORRECTIONS.md` | authority docs | 勘误历史审计中的错误 ADR/参数快照路径，原审计不回写 | 改善历史引用；无 runtime 影响 | revert corrections commit；不要改写原审计代替 |
| `docs/audits/2026-07-26/21_WAVE2_DEPENDENCY_MANIFEST_REVIEW.md` | dependency review | 保存 manifest 分类、serial gitlink decision 和 archive 迁移设计 | 审计/规划；未执行 manifest 迁移 | revert dependency-doc commit |
| `docs/governance/CODEOWNERS_PROPOSAL.md` | governance | 保存占位角色映射、真实 tracked 路径核对和启用门；明确 DO NOT ENABLE | 当前 enforcement 仍 `BLOCKED` | revert governance commit；不要创建 active CODEOWNERS |
| `test/repository_cleanup/test_cleanup_invariants.py` | test integrity | 守护删除路径、current authority 无旧入口/个人路径、历史 roots 保留 | 新增离线 cleanup quality gate | revert test commit；不得删除来绕过回归 |
| `test/test_unittest_discovery.py` | test integrity | 守护 repository test suite 可被 canonical unittest discovery 找到 | 新增离线质量门；不启动 runtime | revert test commit；不得为绕过失败而删除 |
| `docs/audits/2026-07-26/30_REPOSITORY_CLEANUP_AUDIT.md` | planning/audit | 汇总基线、删除/保留、manifest、gitlink、文档漂移与决策项 | 审计记录 | revert planning/audit commit |
| `docs/audits/2026-07-26/31_CLEANUP_CHANGELOG.md` | planning/audit | 文件级变更、影响和 rollback | 审计记录 | revert planning/audit commit |
| `docs/audits/2026-07-26/32_POST_CLEANUP_VALIDATION.md` | planning/audit + coordinator | 命令、退出码、blocker 和最终结论的唯一 validation ledger | 不运行命令；记录验证 | revert planning/audit commit |

## 迁移

已完成的 governance migration：

- 删除 `CODEOWNERS.draft`；
- 新增 `docs/governance/CODEOWNERS_PROPOSAL.md`；
- proposal 明确不可启用，且删除对外部 checkout 和不存在
  `/profiles/px4-firmware/**` 的虚假覆盖承诺。

尚未执行的依赖迁移：

- `px4_bringup` → `workspace.archive.repos` 只是方案；
- optional perception/navigation source profile 只是方案。

协调线程已核对：`SECURITY.md` 未修改，未创建 `.github/` 或 active CODEOWNERS；
全部 governance 变更已列入本表。

## 未归属于 Wave 2 的保留状态

以下不是清理产生的文件变更，不能被纳入 rollback：

- `src/serial_driver_ros` 起始即是 dirty gitlink；
- `src/mavlink`、`src/mavros` 和 `../communication` 的起始 dirty 内容；
- dated audits/evidence/receipts/schemas 和历史参数快照；
- 验证产生且被 `.gitignore` 忽略的 `__pycache__`/`.pyc`。

不得使用 `git reset --hard`、`git clean` 或递归删除处理上述状态。

## 建议逻辑 commit 与 rollback 粒度

| commit 主题 | 文件组 | rollback 影响 |
|---|---|---|
| `chore(cleanup): remove obsolete and empty entrypoints` | 六个删除项、相应 `.gitignore` exception | 恢复旧入口；可能重新引入误执行风险 |
| `docs: align current authority and portable repository paths` | README、Scripts README、handoff、authority、corrections | 恢复漂移文档，不影响 code |
| `chore(deps): clarify DDS-only dependency boundaries` | excluded 注释、DDS-only profile、dependency review | 恢复旧注释/分类；不得借回滚放宽 production allowlist |
| `docs(governance): relocate CODEOWNERS proposal` | draft 删除、proposal、CONTRIBUTING、REVIEW_POLICY | 只恢复 proposal/draft，不应创建无效 active CODEOWNERS |
| `test: validate repository cleanup invariants` | test discovery/cleanup tests | 删除质量门；不建议用于“修复”失败 |
| `docs(planning): assign post-cleanup parallel work` | planning + 30/31/32 | 回到旧调度；不影响实现 |

rollback 后必须重新运行该变更组的完整静态/离线验证，且任何 rollback 都不授权
hardware、firmware flash、flight 或 production。
