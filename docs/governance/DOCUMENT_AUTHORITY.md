# Document Authority

## 目的

本文规定 BoomBoomFly 文档分别回答什么问题，以及历史、当前和计划如何区分。
它不改变 accepted ADR，也不把本轮文档工作提升为运行验证。

本文起草所依据的 checkout 是
`master@5a0e6edd4930474506a1046d414425893ebd800f`。该 identity 只说明本轮文档
核对基线；后续 checkout 必须重新记录自己的 branch、HEAD 和工作树。

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

ADR 自身可以使用 `Proposed`、`Accepted`、`Deprecated`、`Superseded` 表示决策
生命周期；这不等于能力实现或测试状态。

## 文档类型与权威范围

| 文档类型 | 权威回答 | 不回答 |
|---|---|---|
| ADR | 为什么选择某架构、边界及后果 | 当前进程、当前参数或某次测试是否通过 |
| Control authority matrix | 谁允许写哪些控制/视觉 topic、profile 基数与禁止组件 | 运行时是否已强制、publisher 当前数量 |
| Machine-readable profile | 某受管运行/构建 profile 的精确配置和 allowlist | 决策理由、某次运行事实 |
| Evidence/receipt | 某 source/profile/time 下实际执行了什么及结果 | 普遍架构规则、未来计划 |
| Handoff | 当前导航、最近状态入口和下一步指针 | 长期决策或不可变事实数据库 |
| Roadmap/planning | 未完成工作、顺序、依赖和目标 | 已实现或已验证事实 |
| Audit | 某 checkout、某时间点的审查发现 | 当前 checkout 的自动真相 |
| Runbook | 经批准操作应如何逐步执行及何时停止/回滚 | 操作是否已执行或通过 |

## 约束优先级

不存在对所有问题都适用的单一文档排名；先按问题类型选择权威来源：

1. 架构与禁止边界：accepted ADR。
2. 控制 writer/owner：control authority matrix，但不得违反 ADR。
3. 实际运行配置：批准的 machine-readable profile，但不得违反 ADR/matrix。
4. 某次验证事实：对应 evidence/receipt，且必须匹配 source/profile/artifact。
5. 操作方法：当前批准 runbook，且必须消费上述配置和证据门。
6. 当前导航：handoff，只链接权威材料并标记 freshness。
7. 未来工作：roadmap/planning。
8. 历史审查：audit，作为线索和风险记录。

法律、许可证、生产启用和硬件授权需要维护者及适用责任人的显式决策；任何文档
类型都不能自行推定这些权限。

## 冲突处理

发现冲突时：

1. 停止提升状态；安全相关冲突默认标 `BLOCKED`。
2. 记录双方文件、精确段落、checkout HEAD、更新时间和冲突类别。
3. 按“权威范围”确认谁应回答该问题，而不是简单选择更新时间较新的文件。
4. profile 违反 ADR/matrix 时，不运行 profile；通过 ADR 变更或修复 profile 解决。
5. runbook 违反 profile/安全边界时，停止操作并修订 runbook。
6. evidence 与描述不符时，保留原 evidence，创建更正/superseding record；不得覆盖。
7. handoff、roadmap 或 audit 与当前 checkout 不符时，标为历史/过期并修订导航；
   不据此改写 ADR。
8. 安全动作有 Land、Position、停止输出等争议时，提交安全评审，不由文档作者
   选择行为。

冲突关闭必须链接到审查记录或 ADR/profile/evidence 的具体修正，并说明未验证项。

## 当前、历史与计划

### 当前事实

当前事实必须绑定：

- canonical repository、branch、完整 HEAD 和工作树；
- dependency/profile/artifact identity（适用时）；
- 采集时间、方法和有效范围；
- 明确的状态枚举。

若上述 identity 改变，事实不会自动延续。运行态、参数和硬件枚举尤其不能仅凭旧
handoff 继承。

### 历史事实

审查报告、旧 HEAD、旧参数快照、过去 DDS session 和旧硬件盘点都标
`HISTORICAL_EVIDENCE`。它们可以证明“在某时发生过”，不能证明当前仍成立。
历史文件不得为了显得当前而覆写；通过索引或 supersession 关联新记录。

### 计划

roadmap、backlog、草案 runbook、future node 和未执行测试都标 `PLANNED`、
`BLOCKED` 或 `UNVERIFIED`。计划中的 control-authority node 不得写成已实现。
台架/有限实机 runbook 草案不能写成 `BENCH_VERIFIED` 或 `FLIGHT_VERIFIED`。

## 文档元数据建议

新建状态敏感文档建议包含：

```text
Document owner role:
Authority type:
Applies to repository/branch/HEAD:
Updated at:
Capability status:
Supersedes:
Superseded by:
Evidence references:
Known limitations:
```

禁止把个人主目录或真实硬件唯一标识用作 identity。owner 使用角色；public
evidence 使用匿名设备 ID。

## 维护规则

- ADR 变更必须有决策 review 和 supersession 关系。
- Matrix 变更必须与 ADR、topic inventory 和 profile 同步审查。
- Machine-readable profile 是运行配置唯一输入；Markdown 示例不得成为隐式配置。
- Evidence 一次验证一个 identity，不原地追加不同 source 的新结论。
- Handoff 保持短小，只做导航并标记链接 freshness。
- Roadmap/backlog 的 `completed` 必须链接验收 evidence，不能只链接实现 PR。
- Audit 保留原始基线；后续变化写勘误或新报告。
- Runbook 每次使用前核对版本、角色、go/no-go、停止和 rollback 条件。
- 本地相对链接和 Mermaid 应进入文档质量门；外链未检查时标 `UNVERIFIED`。

## 当前已知权威结论

- production：`BLOCKED`。
- production transport：PX4 uXRCE-DDS-only。
- MAVROS production fallback：禁止。
- DDS transport 设备：只允许 DDS owner 独占，不与 MAVLink 复用。
- namespace：当前单机根 namespace；多机为 `PLANNED`。
- `/fmu/out/rc_channels` firmware profile：`BLOCKED`。
- graph guard、owner/lease、VehicleCommand ACK、PRESTREAM、fault lattice：
  `PLANNED`。
- baseline precision landing：不默认启用。
- 拆桨台架：`UNVERIFIED`，所有 P0 关闭前不得进入。
- 有限实机控制：`BLOCKED`，必须另行授权。
