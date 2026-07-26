# Definition of Done 与验收责任

> 文档状态：`PLANNED`
>
> 本文件定义 backlog 和 milestone 的关闭门。它不能把实现、静态检查或桌面演练
> 自动提升为 SITL、台架或实机通过。若与 ADR、控制权矩阵或机器可读运行 profile
> 冲突，按 `docs/governance/DOCUMENT_AUTHORITY.md` 的冲突流程处理。

## 1. 通用 Definition of Done

任一 P0/P1 任务只有同时满足以下项目才能关闭：

- Task ID、Audit ID、目标、修改范围、依赖和 owner 已登记。
- 当前 root HEAD、受影响 dependency HEAD、toolchain/profile/config identity 已记录。
- 实现没有越过任务允许范围；不存在未解释的 dirty source 或生成物提交。
- 每条验收标准至少有一个 requirement-test mapping；正向和关键负向用例均通过。
- 运行了与风险相称的必需测试，保存原始命令、时间、退出码和日志。
- `git diff --check`、适用 build/test/lint/static/docs/secret 检查通过。
- 没有把 mock source 冒充 PX4、真实传感器或 production 权威 source。
- evidence 符合 T08 权威 schema，source、environment、command、result、artifact 和
  limitations 可形成单链；旧证据只标 `HISTORICAL_EVIDENCE`。
- 回滚影响已分析；涉及 artifact/config/profile 的变更有已知良好目标和回退步骤。
- 所需 reviewer 按 review policy 批准，且验收者不是唯一实现者。
- 文档中的能力状态使用规定枚举；没有“计划/草案冒充验证”。
- 所有 reviewer P0/P1 已关闭；接受风险必须由有权角色记录范围、理由和失效日期，
  不能用风险接受绕过安全门进入台架或实机。

## 2. 分级 DoD

| 最强可声明状态 | 必须具备 | 明确不足以满足 |
|---|---|---|
| `IMPLEMENTED` | 代码/配置存在，范围审查完成 | 文档计划、未合并 patch |
| `PARTIALLY_IMPLEMENTED` | 可定位的部分能力和剩余缺口 | 无精确剩余清单的模糊完成声明 |
| `STATICALLY_VERIFIED` | syntax/schema/interface/graph 静态断言通过 | 编译成功、文档存在 |
| `UNIT_TESTED` | 隔离、确定性单元测试覆盖验收边界 | mock 单元结果冒充 PX4 |
| `SITL_VERIFIED` | 固定 PX4 source/profile/Agent 的真实 SITL 正常与故障证据 | mock publisher、历史实机 output-only |
| `BENCH_VERIFIED` | 获批拆桨台架按 runbook 实际执行并签字，rollback 实际成功 | 台架草案、桌面演练 |
| `FLIGHT_VERIFIED` | 单独授权的有限实机 test card 实际完成 | bench、SITL 或 production 声明 |
| `HISTORICAL_EVIDENCE` | 带日期和 identity 的既有事实，明确非 current | 当前参数/profile 断言 |
| `PLANNED` | 有 owner、依赖、步骤和验收门 | 实现或验证结论 |
| `BLOCKED` | 阻塞条件和解除责任明确 | 仅因任务困难 |
| `UNVERIFIED` | 未运行或无法证明 | 默认推定通过 |

状态只可向右侧更强证据推进；source/profile/artifact identity 改变后，受影响运行结论
必须回退为 `UNVERIFIED`，保留旧 bundle 为 `HISTORICAL_EVIDENCE`。

## 3. 优先级特定 DoD

### P0

- 至少三名独立 reviewer，其中必须有一个独立 Safety Reviewer；控制/PX4/感知领域
  变更还需对应 Maintainer，并满足 [Review Policy](../governance/REVIEW_POLICY.md) 的
  角色组合。
- 所有危险路径有正向、负向、边界、loss/restart/invalid-input 测试。
- 需要运行验证的 P0 必须达到相应 milestone 的 `SITL_VERIFIED`，不得仅以单元测试关闭
  production blocker。
- Safety Reviewer 必须确认 fail-closed、deadline、latch 和恢复条件。
- 任何 P0 未关闭时 M5、M6 和 production 都为 `BLOCKED`。

### P1

- 至少两名 reviewer；其中一名为对应领域 Maintainer，涉及 release/evidence/hardware
  promotion 时另一名为 Release 或 Safety Reviewer。
- 接口、identity、profile、CI 或 runbook 任务必须有故意破坏的负向测试。
- 对适用 production profile 的 P1，未达到其声明的运行级别不得关闭 production blocker。

## 4. 变更类型的必需测试

| 变更类型 | 最低测试 | 追加验收 |
|---|---|---|
| PX4 firmware profile | patch apply/reverse、generator、baseline regression、FMUv3 build | PX4 DDS SITL publisher/type/QoS/payload、artifact SHA-256 |
| Offboard control/FSM | build、unit、ASan/UBSan、表驱动 fault tests | PX4 DDS SITL ACK/loss/restart/authority |
| Authority/graph/profile | schema、双 owner/writer、lease/identity 负向测试 | 持续 graph 变化与人工重新授权 |
| DDS endpoint/QoS | static manifest/version check | PX4 publisher/reader 的 SITL 交付 |
| Vision frame/time | 数学金样、property、NaN/Inf、clock/reset/freeze | SITL/EKF2 consumption；真实 sensor 另行授权 |
| CI/build boundary | 本地等价命令、禁止包/action 和 broken test 负向 fixture | required check/branch rule 由管理员只读复核 |
| Runbook | Markdown/link/schema、桌面 dry-run、缺字段负向测试 | 台架/实机状态只能由实际获批执行产生 |
| Release/evidence | schema/hash/link/provenance 验证 | rollback manifest；台架前实际 rollback 门 |

## 5. 验收角色

| 角色 | 主要责任 | 不可替代的批准 |
|---|---|---|
| Task Owner | 实现、测试、风险与证据完整性 | 不能独自关闭自己实现的 P0/P1 |
| Control Maintainer | Offboard、authority、RC/kill、fault 接口 | 控制代码和 PX4 input writer |
| PX4 Maintainer | firmware、message/topic/QoS、Agent/vehicle identity | PX4 profile 与 artifact |
| Perception Maintainer | frame/time/TF/device/EKF2/precision landing | 视觉 publisher enable |
| Test/Quality Maintainer | 测试架构、CI repeatability、负向 fixture | required test 充分性 |
| Release Maintainer | source/dependency/toolchain/artifact/evidence/rollback identity | milestone promotion package |
| Safety Reviewer | hazard、fault action、deadline、stop/recovery | M2 fault table、M5/M6 go/no-go |
| Flight Test Director | 获批 test card、人员与现场总控 | M6 每次 test 的 go/no-go |
| Safety Pilot / Observer | 人工接管与独立停止 | M5/M6 任一人均可 no-go/stop |
| Maintainer/Legal Approver | 根许可证和分发义务 | `BBF-TASK-020` |

真实账号和人员映射必须由维护者填写；角色名不是 GitHub 用户名，也不构成授权。

## 6. Task closure checklist

```text
[ ] 当前 root/dependency/toolchain/profile/artifact identity 已记录
[ ] 允许/禁止范围检查完成，无其他工作线文件冲突
[ ] 所有依赖任务达到要求状态
[ ] requirement-test mapping 完整
[ ] 正向、负向、loss/restart/invalid-input 测试通过
[ ] 原始命令、退出码、日志和 hash 已保存
[ ] rollback impact 和已知良好目标明确
[ ] 文档状态枚举准确，历史/current/计划不混淆
[ ] 所需领域 reviewer 已批准
[ ] 独立 Safety/Release Reviewer（按适用）已批准
[ ] Reviewer P0/P1 为 0
```

任一复选项为空时，任务保持 `PLANNED`、`PARTIALLY_IMPLEMENTED`、`BLOCKED` 或
`UNVERIFIED`，不得标记为更强的验证状态。

## 7. Milestone promotion responsibility

| Promotion | 推荐提出者 | 必须批准 | 最低状态 |
|---|---|---|---|
| M0 → M1 | Release Maintainer | T00/T01/T08 owner + independent Reviewer | `STATICALLY_VERIFIED` |
| M1 → M2/M3 | PX4 Maintainer | Release + Control Maintainer | firmware `SITL_VERIFIED` |
| M2 → M3 | Control Maintainer | Safety + PX4 Maintainer | control `UNIT_TESTED` |
| M3 → M4/M5 | Integration Maintainer | Safety + Release + relevant domains | `SITL_VERIFIED` |
| M4 → vision-enabled M5 | Perception Maintainer | PX4 + Safety Reviewer | vision `SITL_VERIFIED` |
| M5 → M6 | Flight Test Director | Safety + Release + domain maintainers + explicit authority | `BENCH_VERIFIED` |
| M6 → production decision | Project authority | Safety、Release、领域 owner 按治理政策批准 | `FLIGHT_VERIFIED` 仍非自动 production |
