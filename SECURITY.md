# BoomBoomFly 安全策略

## 支持状态

BoomBoomFly 当前 production 状态为 `BLOCKED`，没有已声明的 production release
或受支持版本。仓库中的控制、SITL、台架和实机能力必须分别使用规定状态标记；
历史日志不能证明当前系统安全。

## 报告安全问题

安全联系地址：**待维护者填写**

正式私下报告渠道建立前，报告流程状态为 `BLOCKED`。请不要在 public issue、PR、
讨论区、commit message 或公开 evidence 中披露可利用细节、凭据、真实硬件唯一
标识或可复现攻击步骤。维护者应尽快提供一个组织控制、可审计且有替补人的私下
渠道。

报告建议包含：

- 受影响组件、版本、commit 或 artifact SHA-256；
- 影响、攻击前置条件和最小复现；
- 是否可能导致 arm、mode、setpoint、writer 竞争或安全门绕过；
- 是否涉及真实硬件、设备权限、firmware 或公开 evidence；
- 已采取的临时缓解措施；
- 报告者希望使用的联系和署名方式。

不要附带真实 token、完整 private key 或未脱敏硬件日志。需要传输敏感材料时，先
与维护者约定受控渠道。

## 安全问题范围

以下问题应按安全事件处理：

- 未授权 arm、mode、VehicleCommand、setpoint 或 `/fmu/in/*` 发布；
- graph guard、owner/lease、RC/kill、freshness、ACK、PRESTREAM 或 fault gate
  绕过；
- MAVROS/旧 launch 混入 DDS-only production graph，或 transport 被多个进程争用；
- ROS 参数、launch、shell、配置、日志解析或构建流程中的命令注入；
- 串口、USB、udev、设备组或容器映射权限过宽；
- token、secret、private key、CI credential 或 release signing material 泄露；
- firmware 来源、submodule、toolchain、artifact hash 或刷写对象不可证明；
- 感知坐标、时间、reset、quality 或 freshness 缺陷可能向 PX4 注入错误状态；
- public evidence 泄露硬件唯一标识、账户、个人路径、位置、影像或部署拓扑；
- rollback、release manifest 或验证结论被伪造、替换或与错误 source identity 绑定。

一般功能缺陷可以按贡献流程报告；当无法判断是否影响飞行安全时，默认按安全问题
私下报告。

## 飞控与设备安全

安全问题调查不自动授权硬件操作。未经明确授权，不得：

- 访问真实飞控、串口、USB 设备或传感器；
- 启动 Agent、MAVROS、Offboard、vision 或硬件 launch；
- 写 PX4 参数、刷写 firmware、arm、切换模式或发送 `/fmu/in/*`；
- 复用 DDS 专用 transport 运行 MAVLink；
- 在未拆桨、无观察员或无停止能力时复现控制问题。

如复现确实需要硬件，必须先完成风险评估、角色分工、停止条件、证据脱敏和回滚
检查，并使用已批准的分级 runbook。安全报告本身不是实机授权。

设备访问遵循最小权限：

- 不使用全员可写设备规则；
- 不以 root 运行整个控制栈来规避权限问题；
- transport 设备只有一个经批准 owner；
- 容器只映射任务所需设备；
- 日志不得记录不必要的设备唯一 ID。

## 命令注入与供应链

所有外部输入——包括分支名、manifest ref、路径、ROS 参数、launch 参数、日志字段
和 artifact 名——都应视为不可信。脚本必须避免字符串拼接执行，使用参数数组、
allowlist、显式路径和 fail-closed 校验。不得通过扩大 shell、设备或 CI 权限来
掩盖输入校验缺失。

firmware 和 release artifact 必须绑定精确 source、递归 submodule、toolchain、
profile 和 SHA-256。来源不明、hash 不符、使用 moving `latest`、dirty checkout
构建或缺 rollback manifest 时，promotion 状态必须为 `BLOCKED`。

## Token、secret 与处置

- secret 只能存放在批准的 secret manager 或受控 CI secret 中；
- 不得写入源码、Markdown、配置示例、日志、bag、截图或 evidence；
- 日志输出和错误消息必须对 credential、header 和 URL credential 脱敏；
- 怀疑泄露时先撤销/轮换，再保存脱敏证据并检查受影响范围；
- 删除当前文件不能清除 Git 历史，历史清理和通知由维护者按事件流程决定。

本仓库内出现的角色占位符不是 credential，也不代表真实人员账号。

## Public evidence 与隐私

公开 evidence 只保留完成审查所需的最小信息。必须移除个人邮箱、账户名、个人绝对
路径、真实硬件序列号、设备唯一 ID、内网信息、精确位置和未经授权的图像。需要
保留原始材料时，将其放入访问受控、具备保留期限和完整性校验的位置；public tree
只发布脱敏摘要及受控材料的非敏感引用。

历史 PX4 参数快照必须明确标为 `HISTORICAL_EVIDENCE`，不得发布为当前配置。桌面
演练、草案 runbook 或 mock 测试不得写成 `BENCH_VERIFIED` 或
`FLIGHT_VERIFIED`。

## 负责任披露

维护者在收到报告后应：

1. 确认收到并限制知情范围；
2. 分级影响，冻结可能扩大风险的 release 或硬件活动；
3. 在隔离环境复现，记录 source identity 和所有安全边界；
4. 开发修复与回归测试，并安排独立 reviewer；
5. 在需要时轮换 secret、撤回 artifact 或发布操作缓解；
6. 与报告者协调披露时间、致谢和公开细节；
7. 发布脱敏 advisory，明确受影响版本、修复、回滚和未验证项。

响应时限、支持版本、CVE/CNA 流程和安全联系地址均为 `PLANNED`，由维护者填写。
在这些机制建立前，不得声称项目已有完整的漏洞响应 SLA。
