# Wave 3A C1 — Authority envelope contract

- 日期：2026-07-27
- 工作线：C1
- 状态：`UNIT_TESTED`（协议 oracle 与 synthetic fixtures）；runtime integration
  `BLOCKED`
- 基线：root `f34f5e647846cf20bbe8003b52c21035831b4fe1`，
  branch `agent/wave3a-software-gates`
- 权威决策候选：[ADR-0002](../../adr/0002-authority-command-envelope.md)
- Schema：[authority-envelope.schema.json](../../authority/schemas/authority-envelope.schema.json)

## 范围与写入边界

C1 新增独立 ADR、Draft 2020-12 schema、标准库语义 oracle 和 synthetic fixtures。
没有修改 `src/offboard_cpp` FSM、node、input、topic、config 或 B1 tests；没有启动
ROS、Agent、PX4、节点或 SITL；没有访问硬件或发布真实 `/fmu/in/*`。

`tools/authority/validate_envelope.py` 是 contract oracle，不是 production runtime
guard。synthetic counter 不可作为 SITL、台架、硬件或 production evidence。

## 冻结字段

| 类别 | 字段/规则 |
|---|---|
| owner identity | `owner.principal_id` + 每次进程重启变化的 `owner.instance_id` |
| lease | exact `lease_id`、lifecycle、monotonic issue/expiry；只有 `ACTIVE` 可消费 |
| ordering | source epoch 内 `sequence` 严格递增；duplicate/out-of-order 均拒绝 |
| freshness | monotonic created/deadline；expired、future、越过 lease expiry 均拒绝 |
| epoch | exact `source_epoch` + exact `graph_epoch` |
| correlation | source epoch 内唯一 `command.correlation_id` |
| atomic command | `command.kind` 与 `command.payload` 同一个 envelope |
| recovery | identity/cardinality fault 锁存；人工恢复只回 `READY` 并撤销旧 lease |

## B/C consumer boundary 冻结

C1 validator 输出 `accepted`、stable `event_code`、`latch_state`、
`consumer_state` 和 envelope/correlation identity。

B1/future consumer 只有 C1 accept 且自身 ACK、fresh VehicleStatus、PRESTREAM
（至少 1 秒且至少 20 个连续有效样本）及其他 readiness gate 全满足时，才允许
增加 synthetic/future runtime PX4 publish count。

- C1 任一 reject/latch：publish count = 0；
- C1 accept 但 B1 gate 未完成：publish count = 0；
- 人工 recovery：只回 `READY`，旧 lease 撤销，不自动 `ACTIVE`；
- production adapter：本波不实现，后续由单一 integration owner 串行实现。

## Fail-closed coverage

表驱动 fixtures 覆盖：

- non-current owner、旧 owner instance、非当前 lease；
- 非 ACTIVE 与 expired lease；
- duplicate/out-of-order sequence；
- expired deadline、future created time、deadline 超出 lease；
- correlation replay；
- duplicate writer、duplicate owner；
- source reconnect、旧 source epoch、graph epoch 变化；
- latch 在 cardinality 恢复后仍保持；
- 未经人工授权的 recovery 被拒绝；
- 人工 recovery 不进入 ACTIVE；
- 所有 reject case synthetic PX4 publish count 为 0。

## Schema/toolchain 状态

schema 固定 Draft 2020-12，不提供降级版本。validator CLI 在
`Draft202012Validator` 不可用时明确以 exit 2 报环境阻塞。unittest 会将该单项标为
skip 并保留“schema was not downgraded”原因，标准库 semantic tests 仍可执行。

本 checkout 实测 Python `jsonschema 4.19.2` 且
`Draft202012Validator=True`，与任务提示的已知 `3.2.0` 环境不同；实际状态优先，
差异应进入协调线程 post-validation ledger。

## 离线验证结果

| 命令 | 结果 |
|---|---|
| `python3 tools/authority/validate_envelope.py --help` | `PASS`，exit 0 |
| `python3 tools/authority/validate_envelope.py --schema docs/authority/schemas/authority-envelope.schema.json --context test/authority/fixtures/valid/context.json test/authority/fixtures/valid/envelope.json` | `PASS`，exit 0，`AUTH_ACCEPTED` |
| `python3 -m unittest discover -s test/authority -p 'test_*.py' -v` | `PASS`，19 tests，0 failures/errors/skips |
| `python3 -m compileall -q tools/authority test/authority` | `PASS`，exit 0；生成的 cache 已移除 |
| C1 文件尾随空白检查 | `PASS`，无匹配 |

以上全为纯离线/static/synthetic 验证，不提升为 SITL 或台架 evidence。

## 结论

- Authority protocol/schema/synthetic semantics：`UNIT_TESTED` 候选；
- ADR 状态：`Proposed`，仍需 Architecture/Control Maintainer 与 Safety Reviewer；
- production arbiter/graph guard/Offboard adapter：`BLOCKED`；
- formal SITL：`BLOCKED`；
- prop-off bench：`BLOCKED`；
- production：`BLOCKED`。
