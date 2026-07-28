# 参与 BoomBoomFly 开发

本文定义 BoomBoomFly 的贡献门。它不授予硬件操作、飞控控制、发布或
production enable 权限。

## 当前边界

- 当前 production 状态：`BLOCKED`。
- production 控制链只允许 PX4 uXRCE-DDS；MAVROS 不是 fallback。
- 当前只支持单机根 namespace；多机能力为 `PLANNED`。
- 未经单独授权，不得访问真实硬件、写 PX4 参数、刷写 firmware、arm、切换模式
  或发送 `/fmu/in/*`。
- 2026-07-24 参数快照和 2026-07-25 DDS session 都属于
  `HISTORICAL_EVIDENCE`，不能代表当前配置或当前验证状态。

能力和验证结论只能使用以下状态：

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

## 开始贡献前

1. 阅读 `README.md`、`docs/repository_audit/00_EXECUTIVE_SUMMARY.md`、适用 ADR、
   控制权矩阵和对应 runbook。
2. 记录根仓库 branch、HEAD 和工作树；依赖仓库还要记录 origin、HEAD 和 dirty
   状态。
3. 先确认变更范围、风险级别、文件 owner 和依赖任务。不得覆盖他人的 dirty
   checkout 或并行修改同一文件。
4. 对控制、firmware、感知、硬件、发布或 evidence 变更，先按
   `docs/governance/REVIEW_POLICY.md` 确定 reviewer 和验收门。

## 分支与提交

默认分支不得直接修改或直接 push。所有变更通过短生命周期分支和 PR 进入：

```text
feature/<task-id>-<short-name>
fix/<task-id>-<short-name>
docs/<task-id>-<short-name>
test/<task-id>-<short-name>
chore/<task-id>-<short-name>
security/<private-id>-<short-name>
```

安全漏洞未公开前，不在分支名中暴露漏洞细节。一个 commit 应表达一个可审查的
意图；不要把功能、格式化、依赖更新和生成物混入同一 commit。commit message
建议使用：

```text
<type>(<scope>): <imperative summary>
```

每个 commit 必须可构建或明确标记为不影响构建的文档/测试提交。修复过程中不得
使用 force push 隐藏已进入共享审查的安全相关历史；必要的历史整理由维护者确认。

## PR 必填内容

PR 描述必须包含：

- Task ID、对应 Audit ID、目标和不在范围内的内容；
- source identity：根 HEAD、相关依赖 HEAD/lock、适用 profile；
- 风险级别、控制权/transport/坐标/时间/硬件影响；
- 修改文件和明确未修改的安全边界；
- 实际运行的命令、退出码和结果；
- 未运行的测试及原因，使用 `BLOCKED` 或 `UNVERIFIED`；
- go/no-go、停止条件、回滚方法和 known limitations；
- evidence 路径；涉及 artifact 时包含 SHA-256；
- 是否需要硬件授权、production enable 决策或后续人工确认。

不能把“代码已写”“runbook 已写”或“桌面演练”描述成
`SITL_VERIFIED`、`BENCH_VERIFIED` 或 `FLIGHT_VERIFIED`。

## 必须运行的检查

按变更风险选择测试；适用项不能静默跳过。

| 变更 | 最低检查 |
|---|---|
| 纯文档 | `git diff --check`、本地 Markdown 链接、Mermaid 语法、敏感信息扫描 |
| manifest/恢复 | parser 与负向测试、只读 identity/lock 校验、隔离 dry-run |
| shell/Python/launch | 语法、lint、静态 launch/profile 负向检查 |
| ROS 2 包 | 隔离 build、单元测试、test result、适用 lint/static analysis |
| 控制/authority | 状态表单元测试、异常输入、故障注入、重复 writer/owner 负向测试 |
| topic/QoS/firmware profile | 静态契约、生成物检查、真实 PX4 publisher 的 SITL 验收 |
| 感知坐标/时间 | 数学金样、NaN/Inf、frame/time/reset/freeze 负向测试 |
| release | release policy 的 source/dependency/toolchain/artifact/rollback 全门 |

测试必须绑定到被审查的 source identity。在未建立 required CI 前，PR 中列出的检查
是人工门，状态为 `PLANNED` 的 CI 不能写成已强制执行。

## 生成物与仓库卫生

不得提交：

```text
build/
install/
log/
临时目录或编辑器缓存
未经批准的二进制或 firmware artifact
原始未脱敏硬件日志
token、secret、private key 或个人凭据
```

不得以 reset、clean 或强制 checkout 处理未知 dirty 文件。先确定 owner，再使用
隔离目录验证。依赖、artifact 和 evidence 的来源必须可重建，不得使用未经锁定的
`latest` 作为 release 输入。

## 硬件相关修改

硬件相关 PR 必须说明设备角色、稳定身份策略、最小权限、供电/串口所有权、失败
行为和回滚。公开内容不得包含真实硬件唯一标识、个人主目录、账户名或不必要的
部署拓扑。

真实设备枚举、设备节点访问、参数读取、节点启动和台架动作分别需要任务明确授权。
有代码 review 不等于有硬件授权。拆桨台架和有限实机必须使用对应 runbook，并由
规定人员逐门确认。

## PX4 firmware 变更

firmware profile PR 至少提供：

- 精确 PX4 release、commit、递归 submodule 和 toolchain identity；
- 最小 patch 及其适用 profile；baseline 不默认加入 precision landing；
- PX4/`px4_msgs` 消息定义、topic、方向和 QoS 对照；
- 静态生成、PX4 DDS SITL 和目标 board build 的独立结果；
- flash/RAM 余量、artifact SHA-256、known limitations 和 rollback manifest；
- 明确说明是否执行过刷写。没有硬件授权时必须写 `UNVERIFIED`。

不能仅凭 Agent 配置声明 firmware 已导出 topic，也不能用 mock publisher 作为 PX4
firmware contract 的验收证据。

## Evidence 与脱敏

evidence 必须是一次验证事实，不得被用来替代架构决策或当前配置。使用项目已批准
的 schema；schema 尚未覆盖的字段至少包括 source、dependency、toolchain、
profile、命令、退出码、时间、结果、限制、artifact hash 和验收角色。禁止覆盖
已发布 evidence；后续结果创建新记录并通过 supersession 关联。

公开前必须移除：

- token、secret、private key、cookie 和认证 header；
- 个人邮箱、账户名、主目录、内网地址；
- 真实硬件序列号、设备唯一 ID 和不必要的端口拓扑；
- 未经批准的原始飞行数据、位置和影像。

角色占位符（例如 `@CONTROL-MAINTAINER`）不是实际账号，不得误作已启用的
CODEOWNERS。当前提议与启用门见
[`docs/governance/CODEOWNERS_PROPOSAL.md`](docs/governance/CODEOWNERS_PROPOSAL.md)；
仓库当前没有有效 CODEOWNERS enforcement。

## 许可证

项目许可证选择和第三方分发义务目前为 `BLOCKED`，需要维护者及法律确认。贡献者
不得自行添加或推定根 LICENSE；在决策完成前，不得把仓库内容描述为已获某一许可
证授权发布。
