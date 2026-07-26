# Release Policy

## 当前状态

BoomBoomFly 当前没有可声明的 production release，production 状态为 `BLOCKED`。
本策略定义 promotion 所需条件，不表示这些条件已经实现或通过。required CI、
branch protection、许可证链和完整 release evidence 当前均为 `BLOCKED`。

## Release 基本原则

release 必须由同一个可验证 source identity 构建、测试和提升。以下任一条件成立
时禁止 release：

- 根仓库或任一纳入 release 的依赖 checkout 为 dirty；
- root HEAD、dependency、submodule、toolchain 或 profile 不精确；
- 使用未经批准的 moving ref 或 `latest`；
- artifact 未计算 SHA-256，或测试对象与待发布 artifact 不是同一对象；
- firmware profile、rollback manifest 或 known limitations 缺失；
- 许可证/第三方义务未经维护者及法律确认；
- 适用 P0/P1 未关闭，或 reviewer/测试/evidence 门未通过；
- 使用历史参数快照代表当前配置；
- production enable 决策缺失。

dirty checkout 可以用于本地调查，但其输出不得被 promotion。不得通过忽略 dirty
状态、复制二进制或只记录 commit SHA 来绕过此门。

## Release source identity

每个 release manifest 至少记录：

- canonical repository、branch/tag 和完整 root commit SHA；
- commit/tag 的签名状态（如项目启用签名策略）；
- 根工作树状态和 submodule/gitlink 状态；
- 适用 ADR、control authority matrix 和 machine-readable profile 版本/hash；
- release task、review approvals、构建时间和构建者角色；
- 是否来自受保护默认分支及 required checks 结果。

审查报告中的旧 branch/HEAD 只能作为 `HISTORICAL_EVIDENCE`。release identity
必须在构建开始和 artifact promotion 前各核验一次。

## Dependency identity

依赖清单必须记录每个组件的 canonical origin、精确 commit、tag（如有）、dirty
状态、patch/receipt、递归 submodule 和许可证。moving dependency 若无法固定到
精确内容 identity，不得进入 production release。

`workspace.lock.repos` 只证明其中记录的源码 commit；它不单独证明 dirty 文件树、
OS package、ROS dependency、PX4 source、toolchain 或 artifact。相关 identity
必须由 release manifest 补齐。

## Toolchain identity

至少记录：

- OS、architecture、ROS distribution 和 RMW；
- compiler/linker、CMake、Ninja/Make、Python、colcon；
- 容器 image digest 或等价的 system package BOM；
- PX4 cross-toolchain、generator 和 Micro XRCE-DDS Agent identity；
- 构建参数、环境差异和可复现性限制。

只记录工具名称或宽版本范围不够。无法冻结的输入必须列为 known limitation，并由
release reviewer 判断是否阻塞；安全关键工具无法精确时默认 `BLOCKED`。

## Artifact 与 provenance

每个交付 artifact 均需：

- 唯一名称、类型、目标平台和 profile；
- SHA-256、大小、生成命令、退出码和原始日志引用；
- source/dependency/toolchain manifest hash；
- 对应 build/test/SITL evidence；
- SBOM、许可证/NOTICE 处置和敏感信息扫描结果；
- retention、访问权限和 supersession 状态。

不得重新打包后沿用旧 hash 或旧测试结论。artifact 发生任何字节变化，都必须创建
新 identity 并重新执行适用门。

## PX4 firmware profile

firmware release manifest 还必须包含：

- PX4 release/commit、递归 submodule、board target 和最小 profile patch；
- DDS topic/type/version/QoS 清单；
- baseline 明确不默认启用 precision landing；
- 静态生成、PX4 source SITL、目标 board build 和资源余量；
- `.px4` artifact SHA-256 与 firmware provenance；
- 已知良好 firmware、参数兼容范围和刷写/恢复前置条件。

“build 完成”不等于“刷写完成”或“台架通过”。未获得硬件授权时硬件状态必须为
`UNVERIFIED`。

## Rollback manifest

release 之前必须提供可独立解析的 rollback manifest，至少包含：

- 上一已批准 software、dependency、profile 和 firmware artifact identity；
- 当前与目标参数快照的适用时间、firmware identity 和差异；
- transport、domain、namespace、client key 和单一设备 owner 的恢复配置；
- rollback 触发条件、执行角色、停止条件和人工确认；
- artifact 完整性检查、恢复后的 graph/health 验证；
- rollback 失败时的安全停留状态和升级路径。

历史参数只能用于比较，不能作为当前 rollback 输入。桌面演练可标
`STATICALLY_VERIFIED`；只有拆桨台架实际成功才可标 `BENCH_VERIFIED`。

## Known limitations

release notes 必须列出：

- 明确的 `BLOCKED`、`UNVERIFIED` 和 profile 外能力；
- 当前单机根 namespace 限制；
- production DDS-only、MAVROS 非 fallback、transport 独占要求；
- precision landing 是否禁用；
- 已验证级别及其 evidence；
- 过期条件，例如 dependency、firmware、参数、硬件或 profile 改变。

不能使用含糊的进度措辞；只能使用本文列出的状态枚举。

## Promotion gates

| Gate | 最低条件 | 允许的最强状态 |
|---|---|---|
| Source candidate | clean、exact identity、review plan | `STATICALLY_VERIFIED` |
| Build candidate | 固定工具链 build/test、artifact hash | `UNIT_TESTED` |
| SITL candidate | PX4 source identity、正常/故障矩阵、evidence | `SITL_VERIFIED` |
| Bench candidate | 所有 P0、适用 P1 关闭；runbook 和授权齐全 | 进入台架，不等于通过 |
| Bench accepted | 拆桨台架及 rollback 实际完成 | `BENCH_VERIFIED` |
| Limited flight candidate | bench accepted、独立风险评估与实机授权 | 进入有限实机，不等于通过 |
| Flight accepted | 批准包线内实际验收及 evidence | `FLIGHT_VERIFIED` |

任何 gate 失败都回到最近的已批准状态，不得自动越级。

## Production enable 决策

production enable 不是 build、merge、release 或 `FLIGHT_VERIFIED` 的自动结果。
它至少需要：

- 所有适用 P0/P1 关闭；
- control、PX4、release 责任人批准；启用视觉时增加 perception 责任人；
- 独立安全 review 无未解决 P0/P1；
- release manifest、rollback、known limitations 和当前参数证据完成；
- 仓库维护者记录批准范围、profile、artifact、有效期和撤销条件；
- 硬件/飞行操作另有明确授权。

默认分支、远端设置、release 创建和 production enable 只能由具备明确权限的维护者
执行。普通文档或代码 PR 不授权上述动作。

## 发布后

- artifact 和 evidence 不可原地替换；修复创建新版本并声明 supersession；
- 发现 P0 安全问题时冻结 promotion，评估撤回、回滚和负责任披露；
- dependency、firmware、参数、profile 或硬件 identity 变化会使相关验证过期；
- 定期检查 release 可重建性、secret/PII、许可证和 rollback 可用性。
