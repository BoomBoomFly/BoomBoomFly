# PX4 DDS SITL 故障注入场景

> 文档状态：`STATICALLY_VERIFIED`
>
> 场景状态：24 个正式候选为 `BLOCKED`；1 个 synthetic 场景为 `UNIT_TESTED`
>
> 验证范围：`OFFLINE_SPEC_ONLY`

本文索引 `docs/verification/scenarios/faults/` 下的机器可读故障场景。场景文件冻结未来正式隔离 SITL 所需的注入点、时间、持续时间、检测 deadline、故障码、状态约束、source identity、topic/type/QoS、publisher 基数、reset 和 cleanup 契约。本轮没有运行 PX4 SITL；schema 校验或合成 fixture 通过不构成 PX4 contract 通过。

## 统一约束

- 每次注入都有明确的 `at`、`duration` 与 `detection_deadline`，时间值必须带单位。
- 故障事件必须在 monotonic timeline 中按 `correlation_id` 闭合；顺序按事件 ID 判断，不按固定行号判断。
- `fault_injection.expected_fault_code` 是供 T05 消费的冻结候选；T05 未实现前场景保持 `BLOCKED`。
- `automatic_recovery` 全部为 `false`。输入或 transport 恢复不等于 authority 恢复；必须满足场景的 reset 条件。
- 凡涉及飞行阶段动作选择，均依赖 `SAFETY_DECISION_REQUIRED`。本文不在 Land、Position、PX4 failsafe 或停止输出之间作安全决策。
- mock 只可作为 `SITL-FAULT-022` 的污染源负向输入，且不得关闭任何 PX4 contract 门。
- source identity、topic/type/QoS 和 publisher 基数必须同时满足；topic discovery 不能独自证明 payload 来自目标 PX4。
- cleanup deadline 为有界值，结束时所列 managed participant 必须全部不存在。

## 场景索引

| Scenario ID | 故障 | 注入点 | Fault code | 检测 deadline | 预期状态 | 禁止状态摘要 | 自动恢复 | 主要 blocker |
|---|---|---|---|---:|---|---|---|---|
| `SITL-FAULT-001` | ACK DENIED | pending ACK result path | `ACK_DENIED` | 500 ms | `FAULT_LATCHED` | `ACTIVE` | 否 | T03, T05 |
| `SITL-FAULT-002` | ACK FAILED | pending ACK result path | `ACK_FAILED` | 500 ms | `FAULT_LATCHED` | `ACTIVE` | 否 | T03, T05 |
| `SITL-FAULT-003` | ACK UNSUPPORTED | pending ACK result path | `ACK_UNSUPPORTED` | 500 ms | `FAULT_LATCHED` | `ACTIVE` | 否 | T03, T05 |
| `SITL-FAULT-004` | ACK timeout | correlated ACK observation path | `ACK_TIMEOUT` | 750 ms | `FAULT_LATCHED` | `ACTIVE` | 否 | T03, T05 |
| `SITL-FAULT-005` | stale VehicleStatus | `/fmu/out/vehicle_status_v1` observation | `VEHICLE_STATUS_STALE` | 750 ms | `FAULT_LATCHED` | `ACTIVE`, false success | 否 | T03, T05, safety |
| `SITL-FAULT-006` | odometry loss | `/fmu/out/vehicle_odometry` observation | `ODOMETRY_LOSS` | 750 ms | `FAULT_LATCHED` | `ACTIVE`, new setpoint acceptance | 否 | T03, T05, safety |
| `SITL-FAULT-007` | RC never received | first `/fmu/out/rc_channels` sample | `RC_NEVER_RECEIVED` | 1250 ms | `FAULT_LATCHED` | `PRESTREAM`, mode/arm request | 否 | T02, T03, T05 |
| `SITL-FAULT-008` | RC `signal_lost` | PX4 SITL RC input | `RC_SIGNAL_LOST` | 500 ms | `FAULT_LATCHED` | `ACTIVE`, auto recovery | 否 | T02, T05, safety |
| `SITL-FAULT-009` | RC stale | RC delivery after valid sample | `RC_STALE` | 750 ms | `FAULT_LATCHED` | `ACTIVE`, auto recovery | 否 | T02, T03, T05, safety |
| `SITL-FAULT-010` | battery stale | `/fmu/out/battery_status` observation | `BATTERY_STALE` | 750 ms | `FAULT_LATCHED` | false handling, mission continue | 否 | T03, T05, safety |
| `SITL-FAULT-011` | DDS Agent loss | single UDP Agent session | `DDS_AGENT_LOST` | 750 ms | `FAULT_LATCHED` | old transaction replay, `ACTIVE` | 否 | T04, T05, safety |
| `SITL-FAULT-012` | DDS Agent restart | single UDP Agent lifecycle | `DDS_AGENT_RESTARTED` | 1250 ms | `FAULT_LATCHED` | old epoch/transaction, `ACTIVE` | 否 | T04, T05, safety |
| `SITL-FAULT-013` | PX4 restart | managed PX4 SITL lifecycle | `PX4_RESTARTED` | 1250 ms | `FAULT_LATCHED` | old epoch/transaction, `ACTIVE` | 否 | T03, T04, T05, safety |
| `SITL-FAULT-014` | owner loss | owner heartbeat/lease renewal | `OWNER_LOST` | 750 ms | `FAULT_LATCHED` | old owner command, auto recovery | 否 | T04, T05, safety |
| `SITL-FAULT-015` | duplicate mission owner | owner graph and lease acquisition | `DUPLICATE_MISSION_OWNER` | 500 ms | `FAULT_LATCHED` | second lease, forwarded command | 否 | T04, T05 |
| `SITL-FAULT-016` | duplicate PX4 input writer | PX4 input writer graph | `DUPLICATE_PX4_INPUT_WRITER` | 500 ms | `FAULT_LATCHED` | unauthorized input, `ACTIVE` | 否 | T04, T05 |
| `SITL-FAULT-017` | wrong ROS domain | pre-participant profile check | `ROS_DOMAIN_MISMATCH` | 500 ms | `FAULT_LATCHED` | participant creation, PX4 input | 否 | T04, T08 |
| `SITL-FAULT-018` | wrong client key | XRCE client identity handshake | `XRCE_CLIENT_KEY_MISMATCH` | 750 ms | `FAULT_LATCHED` | session authorization, `PRESTREAM` | 否 | T04, T08 |
| `SITL-FAULT-019` | timestamp rollback | odometry source timestamp | `TIMESTAMP_ROLLBACK` | 500 ms | `FAULT_LATCHED` | invalid cache/setpoint use | 否 | T03, T05, safety |
| `SITL-FAULT-020` | future timestamp | odometry source timestamp | `TIMESTAMP_FUTURE` | 500 ms | `FAULT_LATCHED` | invalid cache/setpoint use | 否 | T03, T05, safety |
| `SITL-FAULT-021` | NaN/Inf setpoint | atomic setpoint validation | `SETPOINT_NONFINITE` | 500 ms | `FAULT_LATCHED` | PX4 publication, `ACTIVE` | 否 | T03, T04, T05, safety |
| `SITL-FAULT-022` | mock publisher contamination | feedback graph/source guard | `MOCK_SOURCE_DETECTED` | 500 ms | `FAULT_LATCHED` | contract acceptance, `ACTIVE` | 否 | T02, T04, T05 |
| `SITL-FAULT-023` | vision freeze | approved transform source | `VISION_STALE` | 750 ms | `FAULT_LATCHED` | frozen vision publish, `ACTIVE` | 否 | T03, T05, safety |
| `SITL-FAULT-024` | vision frame mismatch | pre-conversion frame check | `VISION_FRAME_MISMATCH` | 500 ms | `FAULT_LATCHED` | mismatched publish, `PRESTREAM` | 否 | T05, safety |
| `SITL-FAULT-025` | Wave 3B synthetic rejection matrix | offline synthetic event stream | `WAVE3B_REJECTION_MATRIX` | 2 s | `FAIL_CLOSED` | `ACTIVE`、任何 PX4 publish | 否 | 无 formal dependency；仅 `OFFLINE_SYNTHETIC` |

## 依赖映射

| 依赖 | 本组场景等待的输入 |
|---|---|
| `BLOCKED_BY_T00` | workspace、dirty checkout、toolchain 与精确执行身份 |
| `BLOCKED_BY_T01` | DDS-only package/launch 边界与禁止入口 |
| `BLOCKED_BY_T02` | PX4 `rc_channels` endpoint/profile 和 authoritative source |
| `BLOCKED_BY_T03` | ACK、freshness、PRESTREAM、clock/epoch validity 接口 |
| `BLOCKED_BY_T04` | owner/lease、graph guard、transport/source identity guard |
| `BLOCKED_BY_T05` | 稳定 fault code、fault lattice、reset 与恢复策略 |
| `BLOCKED_BY_T06` | CI 中的离线及未来正式 SITL gate |
| `BLOCKED_BY_T08` | evidence、result、cleanup 和 rollback artifact schema |
| `SAFETY_DECISION_REQUIRED` | 分飞行阶段批准的故障后允许动作与禁止动作 |

T00/T01/T08 的输出由其他工作线拥有；本目录只消费其未来冻结接口，不修改对应文件。

## 状态统计

```text
fault scenarios: 25
PLANNED: 0
STATICALLY_VERIFIED: 0
UNIT_TESTED: 1 (SITL-FAULT-025; offline synthetic only)
BLOCKED: 24
UNVERIFIED: 0
```

文档本身可静态校验；`SITL-FAULT-025` 的离线单元测试也不提升任何正式候选状态。
正式 SITL 执行仍未授权。
