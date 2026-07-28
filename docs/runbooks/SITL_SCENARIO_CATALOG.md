# PX4 DDS SITL 场景目录

> 文档状态：`STATICALLY_VERIFIED` 的目标；实际状态以本轮离线检查结果为准
>
> 动态 PX4 SITL：`UNVERIFIED`
>
> 正式运行：未授权

本目录是 [`SITL_ACCEPTANCE.md`](SITL_ACCEPTANCE.md) 的机器可读场景导航，不是运行
证据。权威清单位于
[`../verification/scenarios/catalog.json`](../verification/scenarios/catalog.json)；
场景 schema、event schema 和结果 schema 的版本均为 `1.0.0`。

## 场景集合

| 集合 | ID 范围 | 数量 | 说明 |
|---|---|---:|---|
| normal | `SITL-NORMAL-001`–`SITL-NORMAL-012` | 12 | session、topic、PX4 feedback、readiness、PRESTREAM、ACK、mode、cleanup |
| fault | `SITL-FAULT-001`–`SITL-FAULT-025` | 25 | 24 个正式候选，以及 1 个 `OFFLINE_SYNTHETIC` Wave 3B 拒绝矩阵 |

`SITL-FAULT-025` 的 `UNIT_TESTED` 仅指内存 synthetic fixture；它没有运行 PX4、
Agent、ROS graph 或 formal SITL，不能作为 H4 或硬件证据。

场景不得因依赖未实现而从 catalog 删除。此类条目保留为 `BLOCKED`，并列出
`BLOCKED_BY_T00`–`BLOCKED_BY_T06`、`BLOCKED_BY_T08` 或
`SAFETY_DECISION_REQUIRED`。

## 加载与判定规则

1. 只从 catalog 的相对路径加载场景；路径必须位于 `scenarios/normal` 或
   `scenarios/faults`。
2. ID 在整个 catalog 内唯一，且必须与文件内容及文件名一致。
3. 先校验 schema，再解析 JSONL timeline，最后执行 deadline、order、count、
   source identity、publisher cardinality、state transition 和 cleanup 断言。
4. 不使用固定行号决定顺序；使用 monotonic timestamp、correlation ID 和显式
   `order_after`/`order_before`。
5. 不以长固定 sleep 作为 assertion；所有等待均由带单位的 bounded timeout 限制。
6. 任一 warning、未知 dependency、未闭合 correlation、cleanup 缺失或非法输入都失败。

## 状态解释

- `UNIT_TESTED` 只表示标准库离线工具和 synthetic fixture 的确定性测试通过。
- `STATICALLY_VERIFIED` 只表示 schema、catalog 或文档契约通过静态检查。
- `BLOCKED` 表示场景已定义但正式执行依赖未满足。
- `UNVERIFIED` 表示没有足够证据。
- 本轮不得使用更强的运行状态，也不得从 validator 退出码推断 PX4 SITL 已通过。

## requirement / audit 映射

每个场景必须同时携带 `requirement_ids` 和 `audit_ids`。result schema 不复制这两组
ID；它用 `scenario_id` 回链 catalog 和冻结场景。T08 evidence bundle 还必须绑定
catalog、场景文件和结果文件的 digest，防止映射在结果生成后漂移。由此形成
requirement/audit → scenario → assertion → result → evidence bundle 的单链。当前主要映射为：

| 场景域 | 主要 Audit ID |
|---|---|
| source / writer / owner | `BBF-AUD-001`, `BBF-AUD-002`, `BBF-AUD-018` |
| PRESTREAM / ACK / freshness | `BBF-AUD-003`, `BBF-AUD-004`, `BBF-AUD-006` |
| RC / firmware endpoint | `BBF-AUD-005`, `BBF-AUD-012`, `BBF-AUD-016` |
| fault lattice | `BBF-AUD-007`, `BBF-AUD-014`, `BBF-AUD-015` |
| vision frame / time | `BBF-AUD-008`, `BBF-AUD-009` |

正式 evidence 格式由 T08 所有者提供；本目录不修改或复制该 schema。
