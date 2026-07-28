# Document Authority

## 目的

本文规定 BoomBoomFly 文档分别回答什么问题，以及决策、当前规范、临时交接、
计划和不可变历史记录之间的权威边界。文档类型不能自行授予 production、硬件、
刷写或飞行权限。

## 状态词汇

能力、测试和验证状态只能使用：

```text
IMPLEMENTED
PARTIALLY_IMPLEMENTED
STATICALLY_VERIFIED
UNIT_TESTED
SITL_VERIFIED
BENCH_VERIFIED
FLIGHT_VERIFIED
HISTORICAL_EVIDENCE
PLANNED
BLOCKED
UNVERIFIED
```

ADR 可使用 `Proposed`、`Accepted`、`Deprecated`、`Superseded` 表示决策生命
周期；这不等于能力实现或验证状态。

## 文档类型与权威范围

| 文档类型 | 权威范围 | 边界 |
|---|---|---|
| Accepted ADR | 架构决策、理由、禁止边界与后果 | 不证明当前实现或运行状态 |
| Architecture / control matrix | 当前系统规范、writer/owner、数据流、部署和故障边界 | 不得违反 Accepted ADR；不证明运行时已强制 |
| Machine-readable profile | 受管 build/runtime 的精确配置与 allowlist | 不替代决策理由或执行 evidence |
| Handoff | 临时交接、导航和 freshness 提示 | 不是长期事实库，不覆盖 ADR、规范或 evidence |
| Planning | 待办、顺序、依赖、owner 和验收门 | 计划不等于实现或通过 |
| Runbook | 经批准操作的步骤、go/no-go、停止与回滚 | 文档存在不表示步骤已执行 |
| Dated audit | 绑定日期与 checkout 的审查发现 | 不自动代表当前 tree |
| Dated evidence / receipt | 绑定 source/profile/artifact/time 的实际记录 | 不自动推广为普遍规则或当前状态 |
| Correction / supersedes record | 修正历史引用、解释限制或以新记录替代旧结论 | 若原件仍在工作树则不得静默改写；获准删除后由 Git 历史恢复 |

## 权威层级

应先按问题类型选取权威来源，再处理冲突：

1. 架构决策由 Accepted ADR 决定。
2. 当前系统规范由 architecture 文档和 control matrix 决定，但不得违反 ADR。
3. 精确运行或构建配置由获批 machine-readable profile 决定，但不得违反 ADR
   或当前规范。
4. 操作方法由当前获批 runbook 决定，并必须消费上述配置与门禁。
5. 某次执行事实只由匹配 source/profile/artifact identity 的 evidence/receipt
   证明。
6. handoff 只提供临时导航；planning 只描述未来工作。
7. dated audit/evidence 在工作树存在期间不原地改写；由 correction/superseding
   record 解释，或在被完整取代且无活跃引用时经维护者批准删除。

法律、许可证、production enable 和硬件授权仍需维护者及适用责任人的显式决策。

## 历史勘误与 supersession

当前权威文档直接修正，并通过 Git commit 保留变更记录。已被当前统一报告完整
取代、且没有活跃消费方的旧报告或 dated evidence 可以从工作树删除；Git 历史是其
恢复路径。

发现错误或后续变化时：

1. 修正当前权威文档，并记录依据和日期。
2. 删除旧材料前检查源码、脚本、测试、CI、schema、索引和文档的入站引用。
3. 仍被构建、依赖或发布验证器消费的 machine-readable evidence、receipt、schema、
   template 和 scenario 不属于旧报告，不得仅因日期较早而删除。
4. evidence 的 supersession 与索引更新必须符合
   [evidence schema](../evidence/SCHEMA.md) 和机器可读索引。
5. 文档修正或旧材料删除不把未执行项目提升为通过。

## 冲突处理

1. 停止状态提升；安全相关冲突默认标为 `BLOCKED`。
2. 记录冲突文件、段落、checkout HEAD、时间和问题类型。
3. 按本文的权威范围确定应回答该问题的来源。
4. profile 违反 ADR/matrix 时不得运行；runbook 违反 profile 或安全边界时停止。
5. evidence 与描述不符时先停止状态提升，再修正索引或创建替代记录。
6. handoff、planning 或 audit 过期时更新当前入口；若已被完整取代且无活跃引用，可删除旧文件。

## 当前、历史与计划

当前事实必须绑定 canonical repository、完整 HEAD、工作树、适用 dependency、
profile/artifact identity、采集时间和方法。identity 改变后不得默认继承旧结论。

dated audit、旧参数快照、过去 session 和旧硬件盘点均为
`HISTORICAL_EVIDENCE`。它们能证明某时发生过，不能证明现在仍成立。

planning、draft runbook 和未执行测试只能标为 `PLANNED`、`BLOCKED` 或
`UNVERIFIED`。mock、parser 或静态检查不得提升为 SITL、台架、飞行或 production
证据。

## 维护规则

- ADR 变更必须经过 decision review，并维护 supersession 关系。
- Matrix 与 architecture 变更必须和 ADR、topic inventory、profile 同步审查。
- Machine-readable profile 是配置唯一输入；Markdown 示例不是隐式配置。
- Evidence 一次只绑定一个 identity，不在原记录中追加不同 source 的结论。
- Handoff 保持短小，只做导航并提示重新获取动态状态。
- Planning 的完成状态必须链接对应验收 evidence。
- Audit 必须绑定基线；被统一报告取代且无活跃引用的旧报告可由维护者批准删除。
- Runbook 使用前必须核对版本、角色、go/no-go、停止和 rollback 条件。
- 本地相对链接、schema、索引和 Mermaid 应进入文档质量门。

## 当前已知权威结论

- production：`BLOCKED`。
- production transport：PX4 uXRCE-DDS-only。
- MAVROS production fallback：禁止。
- 当前单机根 namespace；多机为 `PLANNED`。
- `/fmu/out/rc_channels` firmware profile：`BLOCKED`。
- graph guard、owner/lease、VehicleCommand ACK、PRESTREAM 和 fault lattice：
  `PLANNED`。
- baseline precision landing：不默认启用。
- SITL：`BLOCKED`。
- 拆桨台架、hardware access、firmware flash 和 flight：未授权。
