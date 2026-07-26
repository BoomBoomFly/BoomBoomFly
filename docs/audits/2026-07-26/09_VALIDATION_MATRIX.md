# BoomBoomFly 验证矩阵

> 基线：`agent/follow-latest-offboard@3ce28094e14ed720987c5fc6d1172e377f09b1cc`
> 记号：`✓` 本轮或可追溯证据已验证；`△` 部分/仅历史或 mock；`✗` 已知缺失/失败；`—` 未执行或尚不适用。
> 本轮没有启动 ROS/PX4/Agent/硬件。凡涉及 SITL、台架和实机的结果，除明确标注历史证据外均为未验证。

| 能力 | 静态检查 | 单元测试 | 集成测试 | SITL | 台架 | 实机 | 当前状态 | 缺失证据 |
|---|---|---|---|---|---|---|---|---|
| 工作区恢复 | ✓ lock/脚本 | △ `bash -n` | △ 当前树 verify-only | — | — | — | 15/15 HEAD/origin 匹配；4 dirty blocker；非空白恢复闭环 | 空白环境两次恢复、dirty patch receipt、系统/toolchain lock、幂等/中断测试 |
| DDS-only 包边界 | ✗ 排除包仍被发现 | — | ✗ 默认 `colcon list` 发现 12 个禁止包 | — | — | — | 文档 allowlist 已定义，未技术强制 | 根级 allowlist、CI 负向测试、production launch package allowlist |
| 核心三包构建 | ✓ 语法/manifest | ✓ Offboard 9/9 | ✓ `/tmp` 隔离构建 3/3 | — | — | — | build 通过；vision lint 3/6 executable 失败 | clean lint、固定工具链、CI required check |
| PX4 DDS session | △ 配置只见历史证据 | — | △ 2026-07-25 历史只读 session | ✗ 无项目入口 | — | △ 历史实机只读 | Agent v2.4.2 历史 session/payload 已证明；本轮未复验 | 当前 domain/client key/参数、可重放 SITL、台架只读取证 |
| `vehicle_status_v1` | ✓ 精确常量 | △ 源文件字符串测试 | △ 历史真实 discovery | ✗ | — | △ 历史实机输出 | topic 修复已实现，未验证 freshness/epoch | PX4 publisher/type/QoS 回归、stale/reboot 测试 |
| `rc_channels` | ✓ parser 契约 | ✓ 7 个 RC case | ✗ firmware 无 topic | ✗ | — | ✗ 历史实机缺失 | parser 已支持 normalized 数据；权威 topic 完全缺失 | PX4 patch、生成 DataWriter、SITL 真实 payload、FMUv3 artifact |
| `battery_status` | △ 消息可编译 | ✗ 无 freshness/low battery 测试 | △ 历史真实 payload | ✗ | — | △ 历史实机只读 | 只证明曾收到约 16V payload | freshness、断线、阈值、低电量故障策略及 PX4 source 证据 |
| RC safety interlock | ✗ TEXT_RC/无 RC 绕过 | △ parser case | ✗ 无系统门禁 | ✗ | — | — | 不满足 fail-closed；production blocker | production 无 mock 符号、无 RC/失效/kill 故障注入、firmware topic |
| Offboard activation | ✗ 无显式 PRESTREAM | ✗ FSM 未测 | ✗ | ✗ | — | — | 启动即发送控制流；无 readiness/预热计数 | WAIT/PRESTREAM/MODE_PENDING 测试、PX4 SITL activation evidence |
| VehicleCommand ACK | ✗ 无订阅/处理 | ✗ | ✗ | ✗ | — | — | 完全缺失，P0 | 所有 ACK result、关联、超时、重试、fresh status 二次确认 |
| trajectory writer 唯一性 | △ ADR/矩阵 | ✗ | ✗ 无 graph guard | ✗ | — | — | 规则已冻结，运行时未强制 | 单/双 writer graph 测试、持续 guard、identity/profile 冲突测试 |
| mission owner/lease | △ ADR | ✗ | ✗ | ✗ | — | — | 完全缺少 owner/lease/sequence | arbiter、lease expiry、旧 owner 重连、乱序/重复测试 |
| DDS loss | △ 文档要求 | ✗ | ✗ | ✗ | — | — | 无统一 loss detector/fault state | Agent/PX4 disconnect、reconnect、epoch reset 和人工恢复测试 |
| RC loss | △ parser fail-closed | ✓ `signal_lost`/stale | ✗ FSM/landing 故障行为 | ✗ | — | — | parser 部分实现；系统降级不闭合 | takeoff/active/landing 各状态 fault injection |
| odometry loss | △ age 检查不完整 | ✗ 首帧/未初始化 | ✗ | ✗ | — | — | 存在未初始化与首帧逻辑缺陷 | 首帧、stale、jump、clock rollback、reconnect 测试 |
| vehicle status loss | ✗ 无 receive/freshness | ✗ | ✗ | ✗ | — | — | 陈旧状态可参与迁移 | first-frame、stale、PX4 reboot、ACK+state 一致性测试 |
| NaN/Inf 与输入范围 | △ RC 已检查 | △ 仅 RC | ✗ trajectory/vision 未闭合 | ✗ | — | — | 控制与视觉链仍可接收异常数值 | 全消息 finite/range/schema、fuzz/sanitizer、拒绝发布断言 |
| visual odometry | △ 实现存在 | ✗ 无功能测试 | ✗ 无受管 profile | ✗ | — | — | 坐标、frame、时间、quality/reset 未证明；默认应禁用 | 数学金样、TF/freshness、EKF2 innovation、传感器断线降级 |
| T265 缺失降级 | △ 历史“未发现” | ✗ | ✗ | — | — | — | 设备角色/稳定身份/降级未实现 | serial/udev、掉线/重枚举、健康状态、禁止旧测量 |
| precision landing | △ 默认关闭 | ✗ | ✗ | ✗ | — | — | 可选 publisher 不是已验收能力 | 独立 firmware/profile、目标 validity/freshness/covariance、SITL |
| QoS 契约 | △ 源码可见 | ✗ | △ 历史只证明输出 discovery | ✗ | — | △ 历史输出 | 输入/输出/视觉 QoS 未集中，输入交付未证明 | exact topic/type/QoS 端点表、不兼容负向测试、PX4 reader 证据 |
| timestamp/epoch | ✗ 多时间域直填 | ✗ | ✗ | ✗ | — | — | 无 ROS/camera/PX4 boot time 策略 | time ADR、zero/backward/future/reset 测试、SITL 延迟统计 |
| transport/profile identity | ✗ 无统一配置源 | ✗ | △ 历史单机命令 | ✗ | — | △ 历史单 client | domain/client key/system ID/namespace 分散 | machine-readable profile、双 Agent/错误 PX4/域冲突测试 |
| firmware profile | ✗ 无 PX4 source/patch | — | ✗ 无生成物 | ✗ | — | — | 完全缺失 | source/submodule/toolchain、static generation、SITL、FMUv3 hash |
| 安全参数 schema | ✗ 默认 auto arm | ✗ | ✗ | ✗ | — | — | profile 未分层，范围/单位未统一校验 | schema、配置 hash、非法值负向测试、dev/SITL/bench/prod 分离 |
| launch 静态安全 | △ Python 语法通过 | ✗ | ✗ 无 allowlist/graph assertions | — | — | — | 历史 launch 可启动禁止组件 | launch_testing、profile allowlist、禁止节点/设备负向测试 |
| CI/合并门 | ✗ 根 workflow=0 | — | — | — | — | — | GitHub master 未保护、无 ruleset/required check | Actions、branch protection、required checks、artifact retention |
| evidence 可追溯性 | △ 有两份历史 evidence | — | — | — | — | △ 历史 | 有 SHA/命令线索，但格式不统一且当前/历史易混 | schema、raw logs、exit codes、environment/artifact hashes、索引 |
| 拆桨台架 | △ 仅文档要求 | — | — | — | ✗ | — | 无 runbook/验收记录 | 物理安全、双人确认、故障注入、停止条件、回滚演练 |
| rollback | △ 文档提及 | — | — | — | ✗ | — | firmware/参数/软件回滚未打包、未演练 | 已知良好 artifact、前后参数快照、恢复步骤与台架演练 |
| 有限实机控制 | — | — | — | — | — | ✗ | production 禁用；本轮明确未执行 | 所有 P0/P1 关闭、逐级证据、独立风险评估与明确授权 |

## 当前可声称的最强结论

1. 目标仓库身份、分支和 HEAD 已确认。
2. 15 个 lock 仓库的路径、origin 与 HEAD 匹配；四个 checkout 的 dirty 状态导致 verify-only 正确非零退出。
3. `px4_msgs`、`offboard_cpp`、`vision_to_dds` 在 `/tmp` 隔离目录构建成功。
4. Offboard 当前 9/9 gtest 通过；覆盖范围限于 RC parser 和 topic 源码契约。
5. `vision_to_dds` 当前不是 test-clean：3/6 lint executable 失败。
6. 2026-07-25 的历史证据证明过一次真实 PX4 DDS 输出 session 和 payload，但不代表当前参数、当前运行状态或控制闭环。

## 明确不能声称

- 不能声称 PX4 firmware 已导出 `rc_channels`。
- 不能声称 ROS 到 PX4 的控制输入 QoS/交付已验证。
- 不能声称 VehicleCommand 被 PX4 接受或拒绝时状态机行为正确。
- 不能声称运行时只有一个控制 writer/mission owner。
- 不能声称视觉坐标、时间或 EKF2 融合正确。
- 不能声称 SITL、拆桨台架、回滚或实机控制已经通过。
- 不能把 2026-07-24 参数快照当作当前飞控配置。
