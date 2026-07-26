# BBF-SITL-SPEC-WAVE 执行记录

> 报告状态：`UNIT_TESTED`
>
> 动态 PX4 SITL：`UNVERIFIED`
>
> production：`BLOCKED`

## 1. Repository 与隔离工作区

| 字段 | 值 |
|---|---|
| Repository | `https://github.com/BoomBoomFly/BoomBoomFly.git` |
| Base SHA | `8b1db510e7248968e2911aae022047b3d82df9e0`（执行时最新 `origin/master`） |
| Required ancestor | `8b1db510e7248968e2911aae022047b3d82df9e0` |
| Ancestor check | exit 0 |
| Working branch | `agent/sitl-acceptance-spec` |
| Worktree | `/tmp/boomboomfly_sitl_spec/repository` |
| 主工作区既有状态 | `src/serial_driver_ros` dirty gitlink；未触碰、未复制、未 stash/reset/clean |

最初从调用环境 `/home/aa/px4_ws` 执行 Git identity 命令时发现该路径不是可用的
repository checkout，命令 exit 128；随后只读定位 canonical checkout
`/home/aa/px4_ws/BoomBoomFly`。第一次 sandbox 内 `git fetch origin` 因网络隔离
失败；经用户授权的网络权限重试后 exit 0。没有因失败结果继续推断远端状态。

## 2. Agent 分工与文件所有权

| Agent | 独占写入范围 | 结果 |
|---|---|---|
| A — schema | schema 文档、3 个 JSON Schema、scenario/event validator | 完成；局部检查通过 |
| B — normal scenarios | `scenarios/normal/**`, `NORMAL_SCENARIOS.md` | 12/12 完成并校验 |
| C — fault scenarios | `scenarios/faults/**`, `FAULT_SCENARIOS.md` | 24/24 完成并校验 |
| D — timeline/assertions | timeline 文档、parse/assert/report 工具 | 完成；审查发现的 event-ID bypass 已修复 |
| E — tests/review | `test/sitl_acceptance/**`, `SITL_STATIC_VALIDATION.md` | 17 tests；最终 P0=0/P1=0 |
| main coordinator | catalog/validator、runbook、3 份审计、集成修复 | 完成 |

平台最多 4 个总并发槽（含主 Agent），因此五个子 Agent 采用滚动并行：A/B/C
先启动，A 完成后启动 D，B 完成后启动 E。所有权始终互斥。

## 3. 修改文件

- `docs/verification/`：5 份规范/说明文档、3 个 schema、1 个 catalog、12 个 normal
  场景和 24 个 fault 场景。
- `tools/sitl_acceptance/`：`validate_scenario.py`、`validate_event.py`、
  `validate_catalog.py`、`parse_timeline.py`、`assert_timeline.py`、
  `report_result.py`。
- `test/sitl_acceptance/`：5 个 unittest 模块、fixture helper、3 个 valid synthetic
  fixture 和 5 个 invalid fixture。
- `docs/runbooks/SITL_ACCEPTANCE.md`：仅补机器可读场景、离线命令、blocker、traceability
  与正式运行边界。
- `docs/runbooks/SITL_SCENARIO_CATALOG.md`。
- 本报告、`21_SITL_SCENARIO_REGISTER.md`、
  `22_SITL_IMPLEMENTATION_HANDOFF.md`。

未修改 `src/**`、ROS package、PX4 firmware、manifest、T00/T01/T08 文件、workflow、
evidence/supply-chain/compliance 文件或其他禁止范围。

## 4. 实际命令与退出码

| 命令 / 检查 | 退出码 | 结果 |
|---|---:|---|
| canonical checkout identity/remote/branch/HEAD/status | 0 | repository 与既有 dirty gitlink 已记录 |
| 首次 sandbox `git fetch origin` | 128 | 网络隔离；未作为基线 |
| 授权后 `git fetch origin` | 0 | 最新远端引用取得 |
| `git rev-parse origin/master` | 0 | base 为 `8b1db510...` |
| `git merge-base --is-ancestor 8b1db510... origin/master` | 0 | required baseline present |
| `git worktree add -b agent/sitl-acceptance-spec ...` | 0 | 独立 worktree 创建 |
| 3 个 schema 的 `python3 -m json.tool` | 0 | JSON syntax PASS |
| 6 个 CLI `--help` | 0 | 全部 PASS |
| `validate_event.py` 对 valid synthetic JSONL | 0 | 6 events，PASS |
| `report_result.py` 对 valid synthetic fixture | 0 | offline-only PASS |
| `validate_catalog.py --catalog ...` | 0 | normal=12, fault=24, errors=0 |
| `python3 -m compileall tools/sitl_acceptance test/sitl_acceptance` | 0 | 全部 Python 文件编译 |
| `python3 -m unittest discover ... -v` | 0 | 17 tests，0 failures/errors |
| 禁止 literal scan | 0（有预期命中） | 仅 invalid safety fixture；9 项均被拒绝测试消费 |
| endpoint contract cross-scenario consistency scan | 0 | topic/type/direction/QoS 冲突 0 |
| `git diff --check` | 0 | PASS |

compileall 和最终 unittest 使用
`PYTHONPYCACHEPREFIX=/tmp/boomboomfly_sitl_spec_validation/pycache`。早期局部检查生成的
repo 内 pycache 已删除，最终扫描为 0。

## 5. 测试结果

- Scenario schema cases：missing ID、duplicate ID、missing deadline、timeout missing
  unit、unknown dependency、missing source、malformed forbidden event、illegal status、
  BLOCKED without blocker 全部 fail-closed。
- Timeline cases：wall/monotonic rollback、correlation mismatch、deadline、forbidden
  event、cleanup、publisher count、source identity、state transition、duplicate count
  和 event-ID source bypass 全部被拒绝。
- Safety cases：mock-as-PX4、三类设备路径、真实 serial transport、firmware programming、
  real-hardware arm 和三个禁止状态均被拒绝。
- Positive fixture 明确为 synthetic；PASS 仅是 `OFFLINE_ASSERTION_ONLY`。

## 6. 没有执行的操作

- 没有启动 PX4 SITL、Micro XRCE-DDS Agent、Offboard、MAVROS、视觉节点、ROS launch
  或任何 ROS node。
- 没有访问 `/dev`、真实串口、相机、传感器、飞控或其他硬件。
- 没有发布真实 `/fmu/in/*`，没有 arm、切 mode、改参数、build/flash firmware。
- 没有修改 ROS 2 package、PX4 source 或其他工作线文件。
- 没有创建/合并 PR，没有 push，没有修改远端设置或 `master`。

## 7. 安全边界与状态

36 个正式场景全部保持 `BLOCKED`。离线 schema/catalog/tool/tests 可分别描述为
`STATICALLY_VERIFIED` 或 `UNIT_TESTED`，但不提升任何场景的动态状态。fault 场景
`automatic_recovery=false`；安全动作争议保留 `SAFETY_DECISION_REQUIRED`。mock 或
synthetic source 永远不能关闭 PX4 source contract。

## 8. Reviewer 结论

独立 Agent E 对 schema、36 个场景、timeline/result 工具、fixtures、runbook 和审计
输出进行只读审查。发现并关闭 3 项规范级 P1：

1. event ID 可绕过 source/target/type/correlation 匹配；
2. normal/fault 对相同 endpoint 的 direction/QoS 与 evidence level 冲突；
3. result 与 requirement/audit traceability 文档承诺不一致。

修复后 catalog、unittest、compileall、help、scope、状态和禁止内容均复核通过。
最终未解决 reviewer P0=0，P1=0。
