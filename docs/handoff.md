# BoomBoomFly 临时交接

> 更新日期：2026-07-26
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
