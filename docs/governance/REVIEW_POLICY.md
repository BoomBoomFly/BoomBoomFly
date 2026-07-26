# Review Policy

## 目的与当前状态

本策略定义代码、配置、firmware、runbook 和 evidence 的最低审查门。当前远端
required checks 和 CODEOWNERS enforcement 状态均为 `BLOCKED`；在技术门建立前，
以下要求作为人工合并门执行。

本策略不授予 production enable、硬件操作或实机控制权限。production 当前为
`BLOCKED`。

## 风险分级

| 等级 | 定义 | 最低独立批准 |
|---|---|---:|
| P0 | 可导致错误控制权、arm/mode/setpoint、失效安全门、错误状态估计或不可恢复硬件风险 | 3 |
| P1 | 阻塞集成、SITL、发布、台架或供应链可追溯性 | 2 |
| P2 | 工程质量、文档、可维护性；不直接改变已批准安全边界 | 1 |
| P3 | 长期改进、无当前安全或发布影响 | 1 |

作者不能批准自己的 PR。P0 至少包括对应领域 reviewer、控制/安全 reviewer 和
release/运维 reviewer；涉及 PX4 firmware 时 PX4 reviewer 必须在其中。P1 至少
包括对应领域 reviewer 和一个独立的 release、控制或 PX4 reviewer。人数不足时
状态为 `BLOCKED`，不能用风险接受替代缺失 reviewer。

角色占位采用：

- `@CONTROL-MAINTAINER`
- `@PX4-MAINTAINER`
- `@PERCEPTION-MAINTAINER`
- `@RELEASE-MAINTAINER`

这些是职责类别，不是真实账号。实际 CODEOWNERS 启用前必须由维护者映射到真实
GitHub 用户/team。

## 通用审查门

每个 PR 必须让 reviewer 能回答：

1. source、dependency、toolchain 和 profile identity 是否精确；
2. 变更是否符合 accepted ADR 和控制权矩阵；
3. 是否扩大硬件、设备、网络、secret 或 production 权限；
4. 正常、异常、重启和回滚路径是否有测试；
5. 测试证据是否来自被测 source，而不是 mock 或旧 checkout；
6. 状态是否使用批准枚举，是否把历史、计划或草案冒充当前验证；
7. known limitations、停止条件和未验证项是否明确；
8. 是否修改了已发布 evidence 或泄露敏感信息。

reviewer 必须查看实际 diff 和测试原始结果。只看 PR 摘要、截图或绿色状态不构成
领域审查。

## 控制代码

以下变更至少为 P0：PX4 input writer、VehicleCommand、arming/mode、setpoint、
RC/kill、ACK、PRESTREAM、freshness、fault lattice、owner/lease、graph guard、
mission command envelope 和安全参数。

必须由控制 reviewer 批准；涉及 PX4 endpoint/failsafe 时还需要 PX4 reviewer。
测试至少覆盖：

- 首帧前和无有效 authority 时 PX4 控制发布计数为 0；
- 所有 ACK result、timeout、迟到、重复、错误 target/command；
- RC/DDS/odom/status/battery/owner loss 和组合故障；
- 启动、Agent restart、PX4 reboot、clock jump 和旧 owner 重连；
- NaN/Inf、越界、乱序、stale 和重复 writer；
- 恢复需要明确人工重新授权。

安全评审未决定危险故障应该 Land、Position 或停止输出时，行为状态为 `BLOCKED`，
不得由实现者自行选择。

## PX4 firmware profile

firmware profile 变更至少为 P1；改变控制/安全 topic、failsafe 或刷写对象时为 P0。
必须由 PX4 reviewer 和 release reviewer 批准；影响 control contract 时还需要
控制 reviewer。

审查包必须包含：

- 精确 PX4 release/commit、递归 submodule、toolchain；
- 最小、可正反应用的 patch；
- `px4_msgs` 对齐、topic/type/version/QoS 对照；
- 静态生成与 PX4 source SITL 结果；
- 目标 board build、资源余量和 artifact SHA-256；
- baseline/目标 profile 差异和 rollback manifest。

Agent 配置不能证明 firmware topic 存在，mock publisher 不能作为 firmware 验收。
未刷写时必须明确标记硬件结果为 `UNVERIFIED`。

## 感知坐标与时间

坐标轴、TF、外参、timestamp、reset、quality、covariance 或 EKF2 输入变更至少为
P0（启用对应视觉 profile 时）。必须由 perception reviewer 和 control reviewer
批准；改变 PX4 message/profile 时还需要 PX4 reviewer。

必须提供数学规范和金样测试，覆盖 ENU/NED、FLU/FRD、轴向基向量、90/180 度、
quaternion、covariance、NaN/Inf、frame mismatch、stale/future/backward/freeze
和 sensor reset。任何前置条件不满足时，PX4 视觉 publisher 必须不存在或发布计数
为 0。硬件未授权时只能声明到 `UNIT_TESTED` 或适用的 `SITL_VERIFIED`。

## Runbook

SITL runbook 变更至少需要 control 与 release reviewer；拆桨台架或有限实机
runbook 至少需要 control、PX4 和 release reviewer。更改人员角色、go/no-go、
立即停止条件、kill、回滚或人工确认属于 P0 文档变更。

reviewer 必须验证：

- 允许/禁止操作、前置条件和角色没有歧义；
- 上一级 evidence 是下一级入口，而不是计划或历史记录；
- 桌面演练不被标成实际台架或飞行通过；
- 任一缺失 hash、参数快照、观察员、停止能力或 rollback 项都形成 no-go；
- 实机控制仍要求独立授权。

## Evidence 与 release metadata

evidence schema、receipt、索引和发布 metadata 变更至少由 release reviewer 批准；
涉及控制、PX4、感知结论时还需要对应领域 reviewer。已发布 evidence 不得原地
改写；更正应创建新记录并声明 supersession。

reviewer 要求验证 schema、hash、source identity、命令/退出码、原始日志、状态和
脱敏。`HISTORICAL_EVIDENCE` 不能提升为当前 `SITL_VERIFIED`、
`BENCH_VERIFIED` 或 `FLIGHT_VERIFIED`。

## Required test 类型

| 变更域 | 必需测试类型 |
|---|---|
| 文档/治理 | Markdown 相对链接、Mermaid、style、状态枚举、敏感信息、`git diff --check` |
| manifest/供应链 | identity、lock、dirty、parser/schema、负向输入、隔离恢复 |
| build/launch | syntax、allowlist、AST/graph 负向断言、隔离 build/test |
| 控制 | 单元、状态表、fault injection、sanitizer、组件测试、SITL |
| firmware | patch、generator、endpoint contract、PX4 SITL、target build/hash |
| 感知 | 数学金样、时钟/重置、异常输入、SITL/EKF2（适用时） |
| runbook | 静态 checklist、桌面演练；台架/实机结果必须另行执行 |
| release | provenance、artifact hash、SBOM/license、rollback manifest、known limitations |

某测试因环境或授权无法执行时，PR 必须写 `BLOCKED` 或 `UNVERIFIED`，并且该测试
若属于当前 promotion gate，PR 不得提升对应能力状态。

## CI 与 required checks 实施提议

当前 tree 不存在 `.github/`，没有可执行 workflow；下列 job 均为 `PLANNED`，
required checks 和 branch protection 仍为 `BLOCKED`。本节定义落地目标，不创建
workflow，也不表示任何检查已经由 GitHub 强制。

### 提议 job graph

| 稳定 job 名 | 内容 | 前置 / 依赖 |
|---|---|---|
| `governance-static` | `git diff --check`、Markdown 相对链接、状态枚举、旧入口、tracked 空文件、secret/PII 和 CODEOWNERS pattern 检查 | 无硬件；扫描规则和允许的历史记录分类需锁定 |
| `python-unit` | `compileall` 与 `python3 -m unittest discover -s test -p 'test_*.py'` | 锁定 Python 和依赖 |
| `dds-boundary` | DDS-only package allowlist 与 launch safety 正/负向测试 | `python-unit`；保留全部危险 fixture |
| `evidence-integrity` | evidence/index/schema、release/rollback manifest 与 workspace receipt 验证器测试 | `python-unit` |
| `sitl-spec-offline` | scenario/catalog/event/timeline/schema 的纯离线测试 | `python-unit`；不得启动 PX4、Agent 或 ROS graph |
| `supply-chain-static` | manifest 解析、精确 ref、origin、excluded/profile 一致性和 moving dependency policy | `python-unit`；不得 fetch 或改 checkout |
| `dds-build-test` | Ubuntu 20.04 / ROS 2 Foxy 环境中的隔离 DDS-only build/test | `dds-boundary`、`evidence-integrity`；输出仅在临时目录 |

建议 required checks 使用上述稳定 job 名；若拆分矩阵，branch protection 只绑定
不会随矩阵值漂移的聚合 job。`dds-build-test` 未具备锁定 runner/container、
ROS dependency 和缓存完整性前必须 fail-closed，不能静默跳过。

### Workflow 落地门

创建 workflow 前必须：

1. 锁定所有第三方 action 到完整 commit SHA，记录来源和更新流程。
2. 默认 `permissions: contents: read`；单个 job 只能按必要范围增加权限。
3. pull request 检查不使用 production secret，不执行来自不可信 fork 的 privileged
   workflow，也不使用可写 self-hosted hardware runner。
4. 禁止访问 `/dev/ttyTHS0`、`/dev/ttyACM*`、相机、雷达和其他真实硬件；禁止启动
   Agent、MAVROS、Offboard、视觉节点或 hardware launch。
5. build/test 输出写入隔离临时目录；不缓存 dirty source tree、credential、
   evidence raw log 或未审查 artifact。
6. 负向 fixture 必须验证预期非零和 fail-closed；不得为全绿而删除、放宽或标
   `continue-on-error`。
7. secret/PII 扫描对 dated audit/evidence 进行“检测并分类”，不得自动重写或删除
   不可变历史 artifact。
8. 先在测试分支验证 job 名、触发器、超时、取消、日志脱敏和 fork 行为，再由有
   权限的维护者单独配置 required checks。

CI 通过也不授权 SITL、hardware access、firmware flash、arm、flight 或
production enable。

## 合并、风险接受与紧急变更

- 未解决的 P0/P1 review comment 阻止合并。
- accepted ADR 变更必须通过新 ADR 或对原 ADR 的显式 supersession，不能藏在代码
  或 runbook PR 中。
- P0/P1 风险接受必须由维护者、安全/控制责任人和适用领域 owner 共同记录范围、
  理由、补偿控制和失效日期；不能把 `BLOCKED` 改写为已验证。
- 安全紧急修复可以缩小公开细节，但不能跳过独立 review、source identity、回归
  测试和回滚准备。
- production enable 是独立决策，不随普通 PR 合并自动发生。
