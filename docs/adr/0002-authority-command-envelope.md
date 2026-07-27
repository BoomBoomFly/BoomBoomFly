# ADR-0002：控制权 command envelope 与 fail-closed consumer 边界

- 状态：**Proposed**
- 决策日期：2026-07-27
- 所属任务：Wave 3A C1 / BBF-TASK-001、002、017、018
- 依赖决策：[ADR-0001](0001-dds-only-control-authority.md)
- 决策范围：上层任务 owner 到唯一 PX4 writer 之间的原子控制权 envelope、拒绝语义和恢复边界
- 不包含：`src/offboard_cpp` FSM 集成、ROS graph guard 实现、PX4 ACK/freshness/PRESTREAM 实现、SITL 或硬件验证

## 背景

ADR-0001 已决定 DDS-only、单机根 namespace 和唯一 PX4 control writer，但当前
production source 尚未实现 owner/lease、连续 graph identity、命令 correlation 或
fail-closed consumer。分离的 mode/setpoint 输入也不能证明两个 payload 来自同一
owner、lease、sequence 和时间窗口。

本 ADR 冻结 C1 的协议和 B/C consumer boundary。配套 schema、纯软件语义 oracle
与 synthetic consumer fixtures 只证明协议规则可机器检查；它们不是 production
runtime guard，也不是 SITL、台架或实机 evidence。

## 决策

### 1. 原子 envelope

每个候选命令必须是一个不可拆分的 authority envelope，并包含：

- `owner.principal_id`：经 profile 批准的逻辑 owner；
- `owner.instance_id`：该 owner 进程实例，重启后必须变化；
- `lease.lease_id` 和 `lease.lifecycle`；
- `lease.issued_monotonic_ns` 与 `lease.expires_monotonic_ns`；
- 在 source epoch 内严格递增的 `sequence`；
- `created_monotonic_ns` 与严格的 `deadline_monotonic_ns`；
- `source_epoch`：owner/transport 会话 epoch；
- `graph_epoch`：已验证 ROS graph snapshot epoch；
- `command.correlation_id`：在 source epoch 内唯一；
- `command.kind` 与一个原子的 `command.payload`。

机器定义为
[`authority-envelope.schema.json`](../authority/schemas/authority-envelope.schema.json)，
固定使用 JSON Schema Draft 2020-12。不得为了旧 `jsonschema` 环境改成较低 draft。

所有时间均来自 consumer 认可的同一 monotonic clock domain。wall clock、PX4
timestamp、ROS time 与 monotonic time 不得隐式互换。`deadline_monotonic_ns` 必须
晚于 `created_monotonic_ns`，且不晚于 lease expiry。

### 2. Lease lifecycle

schema 允许传输完整 lifecycle：

```text
GRANTED -> ACTIVE -> RENEWING -> ACTIVE
                    \-> RELINQUISHING -> REVOKED
GRANTED/ACTIVE/RENEWING -> EXPIRED
任意 graph/source identity fault -> REVOKED + FAULT_LATCHED
```

consumer 只接受 `ACTIVE`。`GRANTED` 不等于可发布；`RENEWING` 期间不接受新命令；
`RELINQUISHING`、`REVOKED` 和 `EXPIRED` 一律拒绝。lease ID 不可复用。owner
进程重启、source reconnect 或 graph epoch 变化必须使旧 lease 失效。

### 3. 单调与 freshness

- `sequence` 在每个新的 `source_epoch` 内从非负整数开始并严格递增；
- 等于最近接受值为 duplicate，小于最近接受值为 out-of-order；
- correlation ID 在 source epoch 内不可重放；
- `now >= deadline`、`now >= lease expiry` 或 deadline 越过 lease expiry 均拒绝；
- `created_monotonic_ns` 位于 consumer 当前时间之后时拒绝；
- 拒绝消息不得推进 last sequence、correlation set 或任何 PX4 publish counter。

epoch 变化不是隐式恢复。它是 identity discontinuity，必须锁存，重新完成 graph
identity、owner 授权和新 lease 后才能再次消费。

### 4. Graph 与 owner 基数

进入消费前和运行中均必须满足：

- 批准的 authority writer cardinality 恰为 1；
- 当前 owner cardinality 恰为 1；
- principal、instance、lease、source epoch 和 graph epoch 全部精确匹配；
- graph snapshot 的节点、topic、type、QoS 与获批 profile 匹配。

duplicate writer、duplicate owner、source reconnect 或 graph epoch 变化立即进入
`FAULT_LATCHED`。临时恢复为单 writer/owner 不得自动清除 latch。

### 5. 稳定拒绝事件码

consumer 必须输出稳定、可机器断言的事件码。C1 v1 冻结以下代码：

| Event code | Latch | 含义 |
|---|---:|---|
| `AUTH_ACCEPTED` | 否 | C1 envelope gate 接受；尚不代表允许 PX4 publish |
| `AUTH_SCHEMA_INVALID` | 否 | envelope 不满足 schema/必要字段 |
| `AUTH_FAULT_LATCHED` | 是 | 既有 fault latch 尚未人工恢复 |
| `AUTH_DUPLICATE_WRITER` | 是 | authority writer 基数不是 1 |
| `AUTH_DUPLICATE_OWNER` | 是 | owner 基数不是 1 |
| `AUTH_GRAPH_EPOCH_CHANGED` | 是 | graph epoch 与已验证 epoch 不同 |
| `AUTH_SOURCE_EPOCH_CHANGED` | 是 | source reconnect/restart 或旧 source epoch |
| `AUTH_OWNER_NOT_CURRENT` | 否 | principal 不是当前 owner |
| `AUTH_OWNER_INSTANCE_NOT_CURRENT` | 否 | instance 不是当前 owner instance |
| `AUTH_NO_ACTIVE_LEASE` | 否 | 人工恢复后尚未发放新 lease |
| `AUTH_LEASE_NOT_CURRENT` | 否 | lease ID 不是当前 lease |
| `AUTH_LEASE_NOT_ACTIVE` | 否 | lifecycle 不是 `ACTIVE` |
| `AUTH_LEASE_EXPIRED` | 否 | lease 已过期 |
| `AUTH_SEQUENCE_DUPLICATE` | 否 | sequence 等于最近接受值 |
| `AUTH_SEQUENCE_OUT_OF_ORDER` | 否 | sequence 小于最近接受值 |
| `AUTH_CREATED_IN_FUTURE` | 否 | created time 晚于 consumer monotonic now |
| `AUTH_DEADLINE_EXPIRED` | 否 | deadline 已到或已过 |
| `AUTH_DEADLINE_OUTSIDE_LEASE` | 否 | deadline 晚于 lease expiry |
| `AUTH_CORRELATION_REPLAY` | 否 | correlation ID 已被接受过 |
| `AUTH_DOWNSTREAM_NOT_READY` | 否 | B1 ACK/freshness/PRESTREAM gate 未全部满足 |
| `AUTH_MANUAL_RECOVERY_REQUIRED` | 是 | 尝试自动恢复 latch |

实现不得把未知错误映射成 `AUTH_ACCEPTED`。新增或改变代码语义需要 schema/ADR
版本变更和 consumer contract review。

### 6. B/C consumer boundary

C1 只输出：

```text
accepted: bool
event_code: stable code
latch_state: CLEAR | FAULT_LATCHED
consumer_state: READY | ACTIVE | FAULT_LATCHED
envelope_id / correlation_id
```

B1 或未来 production consumer 只有同时满足以下条件才可增加任一
`/fmu/in/*` publish counter：

1. C1 `accepted == true` 且 latch 为 `CLEAR`；
2. B1 VehicleCommand ACK correlation/result gate 满足；
3. VehicleStatus 与所有要求反馈 fresh；
4. PRESTREAM 至少 1 秒且至少 20 个连续有效样本；
5. 其他 readiness/safety gate 全部满足。

任一 C1 reject/latch 或任一 B1 gate 未满足，synthetic 与未来 runtime PX4 publish
count 必须保持 0。`AUTH_ACCEPTED` 仅表示 authority envelope 合法，不单独授权发布、
arm、mode、takeoff 或 flight。

该边界在 Wave 3A 中不集成 `src/offboard_cpp`。C1 的
[`validate_envelope.py`](../../tools/authority/validate_envelope.py) 是离线 contract
oracle；B1 可独立实现 test-only oracle。production adapter 必须在两侧测试契约通过
后由单一 integration owner 串行实现。

### 7. Latch 与人工恢复

graph/source identity fault、duplicate writer 或 duplicate owner 进入
`FAULT_LATCHED`。自动重连、基数恢复、收到新 envelope 或时间流逝均不得清除。

人工恢复必须是独立、经认证和审计的动作，并且只能：

1. 清除 latch；
2. 回到 `READY`；
3. 撤销旧 lease 和旧 correlation/sequence 状态；
4. 要求重新验证 graph/source identity 并发放新 lease。

恢复绝不能自动进入 `ACTIVE`，也不能重放最后 setpoint。`arm`、flight mode、
takeoff 与 abort 权限仍为人工专属，不由本协议授予。

## 后果和限制

- 原子 envelope 消除分离 mode/setpoint 的跨 owner 和跨时窗组合歧义。
- 严格 sequence、deadline、correlation 和 epoch 使 replay/reconnect 默认拒绝。
- 运行时需要独立 arbiter、graph guard、profile identity 与 Offboard adapter；
  Wave 3A C1 尚未实现它们。
- 当前 Draft 2020-12 validator 可用性属于环境门。缺少支持时 schema validation
  明确 `BLOCKED`，不得降低 schema。
- synthetic publish counter 只证明 consumer contract，不是 PX4 DDS 输出 evidence。

## 验收

- Draft 2020-12 schema 自校验通过；
- valid fixture 通过，缺字段和未知字段非零；
- non-current/old/duplicate/out-of-order/expired envelope 被拒绝；
- duplicate writer/owner、source reconnect 和 graph epoch 变化锁存 fail closed；
- 所有拒绝输入的 synthetic PX4 publish count 为 0；
- downstream gate 未满足时，即使 C1 接受也不发布；
- 人工恢复只回 `READY`，不会自动进入 `ACTIVE`；
- 未启动 ROS、Agent、PX4、节点或 SITL，未发布真实 topic。

当前状态：协议和纯软件 fixtures 为 `UNIT_TESTED` 的候选；production runtime
authority guard、formal SITL、prop-off bench 和 production 均仍为 `BLOCKED`。
