# 普通垂直起飞/悬停/降落实机准入

审计时间：2026-07-29（Asia/Shanghai）
总判定：**BLOCKED — 不允许装桨起飞。**

本轮目标是形成准入证据，不是试飞。初始审计为只读；后续按用户授权修改了
`src/vision_to_dds` 的 production launch、T265 health topic、测试和说明，并完成本地构建。
测试隔离在 `ROS_DOMAIN_ID=231`。没有修改 PX4 参数或固件，没有启动 Agent、production
vision writer 或 Offboard，没有向实机 Domain 0 发送 `/fmu/in/*`，也没有
Arm、Disarm、Land、Kill 或电机动作。

## 三个必须明确的答案

1. **PX4 目前没有实际接受外部视觉定位。** 最近的完整参数快照中
   `EKF2_EV_CTRL=0`，外部视觉位置、速度和航向均不融合；当前也没有 live T265、
   visual odometry writer 或 estimator fusion 证据。仅看到历史 `/fmu/out/vehicle_odometry`
   不能证明 EV 被 EKF 接受。
2. **真实 RC publisher 缺失的直接根因已经定位。** PX4 v1.16.2 精确源码的
   `dds_topics.yaml` 没有 `/fmu/out/rc_channels`，尽管 `RcChannels.msg` 存在且与
   `px4_msgs` 一致。必须修改清单、重建 `px4_fmu-v3_default`、建立可回滚产物，并在
   另一次明确授权的拆桨窗口刷写和复测；重启 Agent 或伪造 RC 都不能解决。
3. **真实 `odom_frame -> base_link` 变换尚不明确。** 动态
   `odom_frame -> t265_pose_frame` 有历史频率/stamp 证据，但
   `t265_pose_frame -> base_link` 的平移和旋转均未测量；五动作坐标符号和重连恢复也未
   验证。禁止假设零平移或单位旋转。

因此三个完成标准均未满足，最终结论必须保持“不允许装桨起飞”。

## 设备、代码与证据身份

| 项目 | 期望基线 | 当前可验证状态 |
|---|---|---|
| Jetson/OS/ROS | Orin Nano / Ubuntu 20.04.6 / Foxy | 与设备基线一致 |
| PX4 飞控 | v1.16.2 / Pixhawk 2.4.8 / FMUv3 | 历史 `ver all` 一致 |
| PX4 源码 | v1.16.2 stable | `54f0455...`, clean, tag `v1.16.2` |
| 根仓库 | `a7a7a72` | `a7a7a72fa64...`；保留现有未跟踪 `src/` |
| offboard_cpp/DDS | 用户给定 `c6da371` | 当前 `976d621`；给定 SHA 本地不可解析，身份 **BLOCKED** |
| vision_to_dds/master | 用户给定 `42a0688` | 实际路径 `src/vision_to_dds`，修改前 `72bd682` + 本轮本地安全修改；给定 SHA 本地不可解析，来源身份仍 **BLOCKED** |
| Micro-XRCE-DDS Agent | v2.4.2 | 历史证据如此；当前 PATH 无命令且无纳管启动件，**BLOCKED** |
| evidence index | 应索引当前 receipt | 当前无条目且记录 root HEAD 不一致，证据治理 **BLOCKED** |

`workspace.lock.repos` 对相关仓库使用 branch 而不是不可变 SHA，不能证明用户声明的两个组件
基线已被复现。不得通过 checkout/reset 覆盖当前工作区；应在后续单独进行来源校验和 receipt
固化。

## 分级准入表

| 等级 | 准入内容 | 当前状态 | 主要证据/阻塞 |
|---|---|---|---|
| H0 | 默认无生产 writer | **PASS（当前快照 + 单测）** | no-daemon ROS 图无节点、无 `/fmu/*`；vision 默认 false 不创建 writer，offboard profile 为 `production_enabled:false`。一旦启用 production 即须重新判定 |
| H1 | DDS 输出完整 | **BLOCKED** | 当前无 Agent；历史 `rc_channels` 为 0 publisher；Agent 二进制/启动件和完整运行 QoS receipt 未纳管 |
| H2 | T265 TF/外参正确 | **BLOCKED** | vision frame、转换、health/reconnect 软件契约已通过单测；但静态外参未测、五动作/live 拔插未做且当前无 live T265 |
| H3 | EKF 接受视觉定位 | **BLOCKED** | `EKF2_EV_CTRL=0`；无 estimator aid/fusion 接受证据 |
| H4 | 拆桨失效测试 | **BLOCKED** | DDS/TF/EKF 前置不成立；Position/Return/Warning/无围栏/高速度和 breaker 风险尚未整改验证 |
| H5 | 低高度装桨悬停 | **BLOCKED** | 只有 H0–H4 全部 PASS、独立飞前审查和当次明确授权后才可进入 |

准入严格单向：`H0 → H1 → H2 → H3 → H4 → H5`。历史证据不能越级，任何上游等级失效，
所有下游等级自动 BLOCKED。

## 各级出口条件

### H0 — 默认无生产 writer

- 默认 profile 不创建或不启动任何 `/fmu/in/*` writer。
- 当前 `vision_to_dds` 默认 `enable_vision_dds=false`，不创建
  `/fmu/in/vehicle_visual_odometry`；production 必须显式双确认且提供实测外参。
- 当前 offboard node 会创建 trajectory/mode/command writer，并在启动后持续发 setpoint/mode；
  `OffboardRuntimeGate` 只存在于测试，未接入生产节点。
- 当前构建全局启用 `TEXT_RC`，会覆盖真实 mode/gear 字段；不能作为生产安全输入。

vision H0 writer 门已有图级单测；offboard 仍须保持未启动。任何 production enable 都必须重新
检查 graph 和 single-writer 条件，且不可依赖 mock RC。

### H1 — DDS 输出完整

- 唯一、已纳管且校验过的 Agent v2.4.2 独占 `/dev/ttyTHS0`，921600 baud，Domain 0。
- 新实机窗口记录所有 `/fmu/out/*` publisher、类型、端点 QoS、频率、PX4 stamp、冻结。
- 六个重点 topic 均有预期 publisher；`vehicle_command_ack` 不通过主动发命令制造样本。
- `rc_channels` 必须来自真实 PX4/RC 链路，拆桨拨杆/摇杆可验证，绝不允许 mock。
- 固件构建、刷写和回滚分别得到明确批准并形成 receipt。

### H2 — T265 TF/外参正确

- 当前 live T265 topic 和 TF 达到稳定频率，stamp 严格递增，无冻结。
- 完成相机到机体的实测外参表，发布唯一静态
  `t265_pose_frame -> base_link`，组成
  `odom_frame -> t265_pose_frame -> base_link`。
- 静止、前移、右移、抬高、顺时针偏航五动作的符号和量级全部通过。
- 拔插/重连后 source epoch、stamp、TF 和输出自动恢复；无旧变换污染。
- 最终语义固定为 `world_frame_id=odom_frame`、`body_frame_id=base_link`，并证明
  ROS FLU/上正到 PX4 所声明 frame 的转换正确。

### H3 — EKF 接受视觉定位

- 只有 H2 PASS 后，才提出一次独立、可回滚的参数修改授权。
- 根据已验证的信号选择 `EKF2_EV_CTRL`，不启用未提供/未验证的速度或航向；delay 和 lever arm
  必须测量/拟合，不能猜。
- 拆桨下确认 `estimator_status_flags` 的 EV control/fault 位、对应 estimator aid source 的
  `fusion_enabled`、`fused`、创新检验和 `time_last_fuse` 持续更新。
- `/fmu/out/vehicle_local_position` 有效、连续，reset counter 和 estimator 状态无异常；冻结或
  断流按设计拒绝陈旧视觉并恢复。

### H4 — 拆桨失效测试

- 在固定机架/安全区、拆桨、动力隔离或安全限能条件下执行
  [PROPS_OFF_FAILSAFE_TEST.md](PROPS_OFF_FAILSAFE_TEST.md)。
- 分别验证 Offboard 丢失、RC 丢失、双丢失、低电、围栏、视觉冻结/断流、Agent 退出、串口断开、
  command ACK 拒绝/超时、kill/authority/manual activation/manual arm enable。
- 室内候选动作以 Land 为主，绝不把 Return 当作默认；每项以实际 `vehicle_status`、
  `failsafe_flags`、mode、land detection 和 ACK 证明，不能只读参数推断。
- breaker、速度和围栏风险全部经硬件前置条件、单项修改、单项回滚验证。

### H5 — 低高度装桨悬停

H5 不是本轮授权内容。未来必须在 H0–H4 全 PASS、独立 go/no-go 复核、现场安全员、有效 RC
人工接管、空旷围护区和用户对当次装桨测试的明确授权后，才能制定最低高度、最短时长的普通
垂直起飞/悬停/降落卡。D435 精确降落不在本工位范围。

## 当前失效配置风险

最近参数快照仍显示：Offboard 丢失回退 Position、RC 丢失 Return、低电仅 Warning、水平和
垂直围栏距离为 0、`MPC_XY_VEL_MAX=12 m/s`，且 IO safety、supply、USB、flight termination
circuit breaker 使用使能 magic value。它们都没有通过室内拆桨失效测试。候选值、前置条件和
逐项回滚见 [PX4_PARAMETER_CHANGE_PLAN.md](PX4_PARAMETER_CHANGE_PLAN.md)；该文档是计划，
不是写参授权。

## 变更纪律

每一次参数、源码、固件或生产配置修改前，必须保存并关联：

1. 原始完整参数文件及 SHA-256；
2. 根仓库、PX4、px4_msgs、offboard、vision 的 Git SHA 和 dirty 状态；
3. `ver all`、板型、bootloader/固件版本和当前可回刷固件 SHA-256；
4. 将要执行的精确命令、操作者和 ISO-8601 时间；
5. 逐项回滚命令/步骤、回滚产物及回滚后验收项。

缺一项就不执行。参数不得批量写；固件不得未经确认刷写；所有实机测试先拆桨。不得启动
Offboard、Arm、Disarm、Land、Kill 或发送 `/fmu/in/*`，除非用户在当次任务中逐项明确授权。

## 唯一下一步：只推进 H1

下一步最小动作是：**由用户明确授权一次“仅准备 H1 的未刷写固件构建与 receipt”任务**。
范围只能包含：归档原始参数/版本/Git/回滚固件，校验 Agent v2.4.2 来源，给
`dds_topics.yaml` 增加真实 `rc_channels` 输出，在独立修改中构建并记录 FMUv3 产物、大小、日志
和 SHA-256。到此停止；不刷写、不启动 `/fmu/in/*`、不改 EKF/T265、不开 Offboard。

该动作本身不会让 H1 PASS。之后仍需另一次明确的拆桨刷写授权和只读 DDS 复测。H1 未 PASS
前不得推进 H2；所有条件满足前，**不允许装桨起飞**。

## 交付索引

- [DDS_TOPIC_AUDIT.md](DDS_TOPIC_AUDIT.md)：Agent、串口、Domain、输出、QoS 与 RC 根因。
- [T265_EXTRINSICS_AND_TF.md](T265_EXTRINSICS_AND_TF.md)：轴定义、外参表、五动作与 TF 草案。
- [PX4_PARAMETER_CHANGE_PLAN.md](PX4_PARAMETER_CHANGE_PLAN.md)：v1.16.2 参数候选、前置、拆桨验证与回滚。
- [PROPS_OFF_FAILSAFE_TEST.md](PROPS_OFF_FAILSAFE_TEST.md)：H4 拆桨失效测试卡。
