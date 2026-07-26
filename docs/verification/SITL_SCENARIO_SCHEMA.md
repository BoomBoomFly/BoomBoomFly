# SITL 场景机器可读契约

> Schema version：`1.0.0`
>
> 本轮能力：`UNIT_TESTED`（仅指离线 schema/fixture 工具）
>
> 正式 PX4 SITL 结果：`UNVERIFIED`

本文冻结 BoomBoomFly Level 1 场景、事件和离线结果的结构接口。schema 校验通过只证明输入符合静态契约，不证明 ROS graph、PX4、DDS Agent、topic payload 或安全行为已经运行或通过。合成事件必须保留 synthetic/mock identity，不能关闭 PX4 contract gate。

## 1. 规范文件

| 文件 | 作用 |
|---|---|
| `schemas/scenario.schema.json` | 单个正常或故障场景 |
| `schemas/event.schema.json` | JSONL 中的一条观测事件 |
| `schemas/result.schema.json` | 离线 validator/assertion 结果 |

三份 schema 使用 JSON Schema 2020-12 表达可交换结构。Python 工具不依赖第三方 JSON Schema 实现，而是执行同版本的 fail-closed 结构和跨字段检查。结构 schema 和工具的 `schema_version` 必须同时升级。

## 2. 场景顶层

每个场景必须包含：

```text
schema_version, scenario_id, title, status
requirement_ids, audit_ids, milestone, profile
preconditions, forbidden_conditions, participants, source_identity
initial_state, stimuli, expected_events, forbidden_events, timeouts
cleanup, evidence, dependencies, limitations, assertions
```

故障场景还必须包含 `fault_injection`。核心字段拒绝未知属性；需演进的项目专属数据只能放入 `extensions` 对象，并仍接受禁止设备/动作扫描。

`scenario_id` 固定为 `SITL-NORMAL-NNN` 或 `SITL-FAULT-NNN`。场景状态只能是本工作线允许的五种离线状态：`PLANNED`、`STATICALLY_VERIFIED`、`UNIT_TESTED`、`BLOCKED`、`UNVERIFIED`。`BLOCKED` 必须至少给出一个 blocker。

`dependencies` 允许：

```text
BLOCKED_BY_T00  BLOCKED_BY_T01  BLOCKED_BY_T02  BLOCKED_BY_T03
BLOCKED_BY_T04  BLOCKED_BY_T05  BLOCKED_BY_T06  BLOCKED_BY_T08
SAFETY_DECISION_REQUIRED
```

## 3. 时间、计数与顺序

所有相对时间必须是带单位的字符串：

```text
250ms
2s
1.5min
```

允许单位为 `ns`、`us`、`ms`、`s`、`min`；不允许裸数、负数或含糊等待字段。计数统一表示为：

```json
{"min": 1, "max": 1}
```

离线工具额外检查 `min <= max`。禁止事件必须固定为 `{"min": 0, "max": 0}`。

每个 stimulus 必须含 `stimulus_id`、`at`、`action`、`source`、`target`、`payload_class`、`correlation_id`。每个 expected/forbidden event 必须含：

```text
event_id, event_type, source, target, earliest, deadline, count,
order_after, order_before, correlation_id
```

顺序用 event ID 引用，不使用文件行号。引用必须存在，且事件不能引用自己。

## 4. Profile、identity 与 endpoint

本版本的 profile 固定到离线描述的隔离 SITL：

```json
{
  "profile_id": "PX4_DDS_SITL_BASELINE",
  "environment": "SITL",
  "transport": "UDP",
  "ros_domain_isolated": true,
  "namespace": "/"
}
```

`source_identity.bindings` 为每个 source 声明 `identity_kind`、预期 identity 和 `mock` 标志。mock binding 不得声称 authoritative PX4 identity。

`assertions.endpoint_contracts` 同时冻结：

- exact topic；
- exact message type；
- publisher/subscriber 方向；
- reliability、durability、history、depth；
- publisher 基数；
- required source binding。

`assertions.participant_cardinality` 固定 participant 基数。`assertions.state_transitions` 用 `from`、`to`、`trigger` 和带单位 deadline 表示 bounded 状态转换。

## 5. 故障注入扩展

`fault_injection` 必须明确：

```text
injection_point, at, duration, expected_fault_code, detection_deadline
expected_state, forbidden_states, automatic_recovery
reset_conditions, cleanup, unimplemented_dependencies
```

具体飞行安全动作未获批准时，场景必须保留 `SAFETY_DECISION_REQUIRED`，不能由 schema 作者选择 Land、Position 或停止输出。

## 6. Cleanup 与 evidence

`cleanup` 包含 bounded `deadline`、动作列表以及必须消失的 participant。列表中的 participant 必须在场景中声明。

`evidence.acceptance_level` 区分 `OFFLINE_SPEC` 与未来 `FORMAL_SITL`。当前 fixture 和离线 validator 结果仅属于前者。`required_artifacts` 描述未来运行必须保存的 identity、timeline 和原始记录；schema 不替代 T08 evidence contract。

## 7. 离线使用

```bash
python3 tools/sitl_acceptance/validate_scenario.py \
  --scenario docs/verification/scenarios/normal/SITL-NORMAL-001.json

python3 tools/sitl_acceptance/validate_event.py \
  --input test/sitl_acceptance/fixtures/valid/timeline.jsonl \
  --format jsonl
```

可选 `--output PATH` 写入稳定排序 JSON summary。退出码 `0` 表示相应离线输入通过，`2` 表示结构或语义拒绝，`3` 表示读取/JSON 解析失败。工具不访问网络、ROS graph 或设备，不启动服务。

## 8. 版本与变更规则

- 添加必需字段、改变语义或收紧枚举：升级 schema version，并迁移 catalog。
- 只增加 namespaced extension：保持核心版本，但必须记录 extension owner。
- validator 与 JSON Schema 结论冲突：fail-closed，场景不得进入正式执行。
- blocker、topic/type/QoS/source identity 未冻结：场景保持 `BLOCKED` 或 `UNVERIFIED`。
- 离线工具通过：最多证明规范/fixture 的静态或单元验证状态，不提升系统验收等级。
