# BoomBoomFly Wave 3A 临时交接

> 更新日期：2026-07-27
>
> 用途：当前窗口导航；不替代 ADR、规范、planning 或 evidence。
>
> production：`BLOCKED`

## 打开工作区

不要依赖个人主目录或固定 checkout 路径。在仓库内动态解析根目录：

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"
git status --short --branch
git rev-parse HEAD
```

保留所有既有 dirty checkout；不要 reset、clean、强制 checkout 或覆盖本地改动。

## 当前 Wave 3A 导航

- root 基线：`agent/wave3a-software-gates` 从
  `f34f5e647846cf20bbe8003b52c21035831b4fe1` 开始；接手时仍须重新读取实际
  branch、HEAD 和 dirty state。
- A1 alignment：已完成只读报告，但 PX4-Autopilot source/submodule/toolchain
  identity 缺失，保持 `BLOCKED`。
- B1：`src/offboard_cpp` 中只有 test-only ACK/freshness/PRESTREAM contract
  oracle；12 tests 通过，production FSM integration 未实施。
- C1/D1/G1：schema/semantic、CI design、dependency profile 的 synthetic/offline
  tests 通过；分别不代表 runtime guard、executable CI 或 manifest migration。
- H：只有 preliminary OS inventory；H0 identity 和 H2 bench 未完成。
- canonical 结果和 blockers：
  [Wave 3A audit](audits/2026-07-27-wave3a/)。

## 当前不变量

- 软件基线：Ubuntu 20.04、ROS 2 Foxy、PX4 v1.16.2。
- production transport：PX4 uXRCE-DDS-only；MAVROS 不是 fallback。
- production 当前禁用。
- SITL orchestration 尚未获准，不能声称 `SITL_VERIFIED`。
- 台架、硬件访问、firmware 刷写和飞行均未授权。

## 从这里继续

- 权威层级：[Document Authority](governance/DOCUMENT_AUTHORITY.md)
- 架构决策：[ADR-0001](adr/0001-dds-only-control-authority.md)
- 当前规范：[控制权矩阵](CONTROL_AUTHORITY_MATRIX.md) 与
  [architecture](architecture/)
- 构建和测试：[Scripts README](../Scripts/README.md)
- 验证 runbook：[分级验证门](runbooks/VALIDATION_LEVELS.md) 与
  [SITL 验收](runbooks/SITL_ACCEPTANCE.md)
- canonical planning：[下一批并行任务](planning/NEXT_PARALLEL_TASKS.md)
- Wave 3A validation：[canonical validation ledger](audits/2026-07-27-wave3a/10_CANONICAL_VALIDATION.md)
- Wave 3A summary：[summary](audits/2026-07-27-wave3a/11_WAVE3A_SUMMARY.md)
- evidence：[索引](evidence/index.yaml) 与 [schema](evidence/SCHEMA.md)
- 本日期审计的勘误：[CORRECTIONS](audits/2026-07-26/CORRECTIONS.md)

具体 branch、HEAD、dependency 状态、blocker 和任务进度应在接手时从 Git、
machine-readable profile、planning 与对应 evidence 重新获取，不在本文件复制。

```text
PRODUCTION: BLOCKED
HARDWARE ACCESS: NOT AUTHORIZED
FIRMWARE FLASH: NOT AUTHORIZED
FLIGHT: NOT AUTHORIZED
```
