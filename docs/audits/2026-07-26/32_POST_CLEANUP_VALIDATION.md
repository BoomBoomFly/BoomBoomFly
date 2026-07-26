# Repository Cleanup Wave 2：Post-cleanup Validation

日期：2026-07-26
状态：`FINAL_WITH_ENVIRONMENT_BLOCKERS`

本文件是最终验证 ledger。命令均由协调线程在 Wave 2 最终工作树上以静态或离线
方式执行；没有启动 ROS/PX4、Agent、launch、SITL 或硬件。环境依赖或受保护 dirty
状态导致的非零退出与 cleanup regression 分开记录。

状态枚举：

- `PASS`：命令按验收预期返回；
- `FAIL`：本轮新增回归或未解释测试失败；
- `BLOCKED`：前置依赖、已知受保护 dirty 状态或环境缺失阻止；
- `NOT_APPLICABLE`：本轮明确不授权/不适用；
- `NOT_RUN`：未执行，并说明原因。

## 1. Worker 局部预验证

这些结果只覆盖执行时的局部工作树，协调线程仍需最终重跑。

| 命令/检查 | exit | 状态 | 摘要 |
|---|---:|---|---|
| parse `config/profiles/dds_only_packages.yaml` and compare excluded/forbidden | 0 | `PASS` at dependency-review time | JSON syntax 可解析；13 个 forbidden 与 excluded 精确一致 |
| manifest set/URL/exact-SHA comparison | 0 | `PASS` | lock=16、moving=17，共同 URL 一致，lock 全为 40 位 SHA |
| `python3 -m unittest discover -s test/package_boundary -p 'test_*.py' -v` | 0 | `PASS` | 9/9 tests；此后 profile inventory 有追加，最终必须重跑 |
| `bash -n Scripts/installation/uav_px4_dds_install.sh` | 0 | `PASS` | shell syntax |
| `git diff --check -- workspace.excluded_packages docs/audits/2026-07-26/21_WAVE2_DEPENDENCY_MANIFEST_REVIEW.md` | 0 | `PASS` | 局部 dependency diff |

## 2. 最终基础验证

| 命令 | exit | 状态 | 摘要 |
|---|---:|---|---|
| `git diff --check` | 0 | `PASS` | Wave 2 diff 无 whitespace error |
| `git status --short --branch` | 0 | `PASS` | branch 为 `agent/repository-cleanup-wave2`；Wave 2 文件与起始 dirty `src/serial_driver_ros` 均被完整识别 |
| `git diff --stat` | 0 | `PASS` | 与 changelog 文件组核对；untracked 新文件另由 status/name inventory 核对 |
| `git diff --name-status` | 0 | `PASS` | 删除、修改项与 31 一致；新增项由 status 核对 |
| `git log --oneline --decorate -10` | 0 | `PASS` | 起始 identity 为 `0a7f90d`；最终 commit identity 以本地 log 为准 |

## 3. 清理不变量

| 命令 | exit | 状态 | 摘要/分类 |
|---|---:|---|---|
| `python3 -m unittest discover -s test/repository_cleanup -p 'test_*.py' -v` | 0 | `PASS` | 3/3；删除路径、current authority 旧引用/个人路径和历史 roots |
| 旧入口/个人路径 `rg` 扫描 | 0 | `PASS` | 命中仅位于 cleanup 测试、Wave 2 changelog/audit 和 immutable historical audit/evidence；current authority 无命中 |
| 空文件扫描 + tracked inventory | 0 | `PASS` | 根仓库 tracked 空文件为 0；42 个结果全部位于受保护 nested dependencies，属于上游 package marker、ignore marker 或占位文件，未修改 |
| current Markdown relative-link checker | 0 | `PASS` | 15 个 current 文件、45 条相对链接、0 broken |
| `git ls-files -s \| awk '$1==160000 {print}'` | 0 | `BLOCKED` | 保留 `src/serial_driver_ros@87f3907…`；`REQUIRES_MAINTAINER_DECISION` |
| `git submodule status --recursive` | 128 | `BLOCKED` | 根无 `.gitmodules`，serial gitlink 无 mapping；已知 blocker，未尝试修复 dirty checkout |

## 4. Python、schema 与离线 suites

| suite / 命令 | exit | 状态 | 摘要 |
|---|---:|---|---|
| `python3 -m compileall Scripts tools test` | 0 | `PASS` | Python compile 完成；bytecode 由 `.gitignore` 处理 |
| `python3 -m unittest discover -s test -p 'test_*.py'` | 1 | `BLOCKED` | canonical discovery 实际运行 78 tests：1 failure + 8 errors；1 个 PATH/ninja sandbox 问题，8 个错误均因环境 `jsonschema==3.2.0` 不提供 `Draft202012Validator` |
| DDS-only package boundary | 0 | `PASS` | unit 9/9；真实 discovery 79 packages、classified 83、production 精确为 3 |
| launch safety | 1 | `BLOCKED` | 11 tests 中非 schema 路径通过，5 errors 均由缺少 Draft 2020-12 validator 引起；未降低 schema |
| environment validator | 0 | `PASS` | sanitized POSIX PATH 下 unit 16/16；read-only JSON summary PASS，`hardware_accessed=false`、Agent 未执行；原 PATH capture probe 因不可执行 WindowsApps `ninja` 被环境阻塞 |
| evidence/schema/index | 0 | `PASS` | evidence unit 14/14；index validator PASS |
| release/rollback manifest validators | 0 | `PASS` | 两个 template 均通过；正负向 policy 由 evidence unit suite 覆盖 |
| workspace receipt validator | 1 | `BLOCKED` | 8 tests 中 5 通过、3 errors；CLI 同因 `jsonschema==3.2.0` 缺 Draft 2020-12 validator |
| SITL scenario/event/timeline assertions | 0 | `PASS` | 纯离线 unit 17/17；不构成 SITL 执行证据 |
| SITL catalog integrity | 0 | `PASS` | 36 entries（12 normal、24 fault），ID/文件一一对应，全部仍为 `BLOCKED` |
| JSON/YAML parse validation | 0 | `PASS` | root tracked 64 JSON + 6 YAML；唯一 parse failure 是故意 malformed 的负向 fixture |
| Markdown relative links | 0 | `PASS` | current docs 0 broken；历史缺失引用由 `CORRECTIONS.md` 分类 |

最终 unittest 必须证明 `test/test_unittest_discovery.py` 能发现全部预期 suite；只运行
单个子目录不能替代 canonical discovery。

## 5. DDS-only build/test

执行前已确认帮助入口：

```bash
bash Scripts/test/test_dds_only.sh --help
```

| 命令 | exit | 状态 | 摘要/分类 |
|---|---:|---|---|
| `bash Scripts/test/test_dds_only.sh` | 1 | `BLOCKED` | 隔离 build 3/3 PASS；test 阶段受沙箱禁止 `/home/aa/.ros/log`/network interface 访问，且受保护 nested `vision_to_dds` 有既存 lint failures；未修改依赖 |

该脚本成功只证明 DDS-only allowlist 的隔离 build/test，不授权启动 Agent、Offboard、
vision、SITL 或硬件。

## 6. Workspace 恢复只读审计

```bash
bash Scripts/installation/uav_px4_dds_install.sh \
  --verify-only \
  --skip-package-check
```

| 命令 | exit | 状态 | 摘要/分类 |
|---|---:|---|---|
| exact-lock verify-only | 0 | `PASS` | planned=16、verified=16、blockers=0；manifest 不含 mavlink/mavros/serial gitlink/communication，未声称验证这些路径 |
| moving manifest verify-only | 1 | `BLOCKED` | planned=17、verified=17、blockers=1；唯一 blocker 是受保护 dirty `../communication`，命令确认未改变文件或 Git refs |

不允许通过 reset、clean、checkout、删除 receipt 或忽略目录来消除 blocker。Wave 2
起始受保护 dirty 状态包括 `src/mavlink`、`src/mavros`、
`src/serial_driver_ros` 和 `../communication`；exact-lock 命令实际覆盖哪些路径，
必须根据 manifest 和输出逐项说明，不能机械声称“4 blockers”。

## 7. 分类 ledger

协调线程在最终执行后填写：

| 分类 | 数量 | 明细 |
|---|---:|---|
| PASS | 15 checks/suites | diff、cleanup invariants、links、compile、package boundary、environment、evidence、manifest、SITL static/catalog、parse、exact-lock 等 |
| expected blocker | 5 classes | orphan serial gitlink、dirty moving communication、旧 jsonschema、sandbox PATH/log/network、nested dependency lint |
| new regression | 0 | 未发现由 Wave 2 改动引入的断言失败 |
| environment missing | 2 | Draft 2020-12-capable jsonschema；可写 ROS log/允许 interface probe 的隔离 test 环境 |
| test failure | 0 new | 非零 suite 均由上述环境或受保护 nested dependency 既存 lint 分类 |
| unauthorized hardware | 4 classes | hardware access、firmware flash、flight、production 均未授权 |

## 8. 未授权运行项

| 项目 | 状态 | 原因 |
|---|---|---|
| formal PX4 DDS SITL | `BLOCKED` | A/B/C/D 软件门未完成；本轮只允许离线 parser/tests |
| Micro XRCE-DDS Agent / Offboard / vision launch | `NOT_APPLICABLE` | 本轮明确禁止启动 |
| hardware launch / serial / camera / lidar | `NOT_APPLICABLE` | 未授权，且静态 cleanup 不需要 |
| PX4 parameter write / reboot / firmware flash | `NOT_APPLICABLE` | 未授权 |
| arm / mode / `/fmu/in/*` publication | `NOT_APPLICABLE` | 未授权 |
| prop-off bench | `BLOCKED` | 软件门、正式 SITL、release/rollback 和硬件授权未完成 |
| flight | `BLOCKED` | M5 未通过且无独立飞行授权 |

## 9. 最终结论

```text
STATIC CLEANUP: PASS
OFFLINE TESTS: PASS WITH ENVIRONMENT BLOCKERS
DDS-ONLY BUILD/TEST: BUILD PASS; TEST BLOCKED
WORKSPACE VERIFY-ONLY: EXACT LOCK PASS; MOVING MANIFEST BLOCKED
NEW REGRESSIONS: 0

PRODUCTION: BLOCKED
HARDWARE ACCESS: NOT AUTHORIZED
FIRMWARE FLASH: NOT AUTHORIZED
FLIGHT: NOT AUTHORIZED
```

只要存在未解释的新 regression，不能接受 cleanup；只要 A–G 的适用 promotion 门未
完成，即使全部静态/离线测试 PASS，production 仍保持 `BLOCKED`。
