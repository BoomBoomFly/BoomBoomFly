---
title: BoomBoomFly 当前交接
status: h-fake-runtime-validated-gateway-sitl-unvalidated
updated: 2026-08-13
---

# BoomBoomFly 当前交接

这是当前工作的唯一状态入口。长期不变量见[工作区架构](工作区架构.md)，参考项目采用决策与阶段路线见
[参考框架采用与演进路线](参考框架采用与演进路线.md)，实机操作只按
[第一阶段实机门禁清单](第一阶段实机门禁清单.md)推进。当前用户确认的要求优先于本文。

## 当前结论

目标工作区架构已落到代码、接口、launch、测试和文档层；八个自研嵌套仓库的变更已分别通过 PR
合并到默认分支，并由核心 manifest 锁定精确 merge commit。H 任务已完成不连接 PX4 的 fake Action
纵向闭环，但新 gateway 和 D 任务链仍未完成运行时闭环。本轮没有启动 SITL、DDS Agent、QGC
或任何飞行动作。

旧 `TI` 路径已迁移为 `px4/px4_ws/src/boomboom/ti`，原独立 Git 历史、远端和用户已有删除记录均保留。

自有框架路线已冻结为“稳定能力接口 + 单一飞行执行器 + 可替换 navigation backend + 任务应用”。
Aerostack2、BehaviorTree.CPP、EGO-Planner 和 GCOPTER 当前都不加入核心依赖；PX4 ROS 2 Interface
Library 只保留为 direct-Offboard 基线完成后的隔离 A/B 候选。

## 当前实现

| 范围 | 当前状态 |
|---|---|
| `common` | 保留 ROS-free C99 core；新增 `LocalPose`、`FlightState`、目标观测、设备命令/回执和 `ExecuteFlight` Action。 |
| `offboard_cpp` | 新默认 `offboard_gateway_node` 提供 `/offboard/execute_flight` 与 `/boomboom/flight_state`；legacy mission 仅作兼容回放。两者共享 PX4 I/O 边界，但不可同时运行。 |
| `px4_vision_bridge` | DDS/MAVROS backend 互斥；hardware MAVROS 默认要求已标定机体 TF。 |
| `px4_bringup` | SITL/hardware 默认 `start_gateway=true`、`start_mission=false`；launch guard 拒绝双控制 writer。 |
| `communication` | 已定义 Ground/UAV/Car 的版本、session、sequence、幂等和断连语义；未选择传输或线格式。 |
| `ti` | 已建立 `mission_core`、`navigation`、H、D、任务 bringup 五包及模板；H 已接通外部 START/取消、覆盖路径、串行 Action 结果和观测统计，D 仍是接口模板；无 `px4_msgs` 或 `/fmu/in/*`。 |
| `perception` | 独立仓库和初始 README 已纳入工作区；动物、小车和降落标志感知实现尚未建立和验证。 |
| `embedded_systems` | 现有驱动已统一整理到 `drivers/`，固件、小车、载荷和共享代码占位已建立；设备命令/回执集成尚未建立和验证。 |
| manifests | 核心 manifest 已锁定 `common`、`communication`、`embedded_systems`、`offboard_cpp`、`px4_vision_bridge`、`px4_bringup`、`perception` 和 `ti` 的已合并精确提交。 |

PX4 与 `px4_msgs` 基线为 v1.16.2，Micro XRCE-DDS Agent 为 v2.4.2；PX4 v1.16 状态话题使用
`/fmu/out/vehicle_status_v1`。

目标机 Jetson Orin Nano 已由用户确认升级为 Ubuntu 22.04 / ROS 2 Humble。该升级解除旧 ROS 2 版本约束，
但升级后的目标机工作区构建、依赖、DDS、VIO 和无桨地面联调仍须重新验证。

## 当前架构离线证据

- 九个目标包已在空的标准 `px4/px4_ws/build|install|log` 完成一次性依赖顺序构建：
  `px4_msgs`、common、mission_core、navigation、H、D、gateway、vision bridge 和 bringup。
- 55 个包级 CTest 条目及 `px4_bringup` 7 个 pytest 全部通过；其中包含 `px4_msgs` 29 个生成代码
  lint 条目和 H 的 9 个测试。聚合 `colcon test` 仍有包间固定长等待，包级测试结果已经分别核实。
- common、communication 合约检查和 `Scripts/workspace/verify_architecture.py` 通过。
- gateway、TI 总入口、SITL bringup、hardware bringup 四组 launch 参数解析通过。
- 架构检查确认：TI 不依赖 `px4_msgs`，H/D 互不依赖且都经 navigation 使用飞行 Action，
  `offboard_cpp` 不依赖 TI，三个 PX4 控制输入只出现在 `offboard_cpp` 生产代码。
- gateway 单测覆盖非法/NaN goal、单 goal、RC 启动门、取消转 HOLD、定位或 heading 失效、原地 Land、
  Land 不可取消和新落地样本门禁。
- H 网格覆盖测试确认执行路径只经过四邻接自由格，并覆盖单洞、窄条、不连通和确定性场景。
- H 节点现提供 `/boomboom/task_h/start`、`/boomboom/task_h/cancel` 和
  `/boomboom/task_h/state`；`auto_start` 仍默认关闭，任务层只经 navigation adapter 请求飞行能力。
- H fake 成功场景以 3 个连续禁飞格跑通 60 个自由格、119 个连续 GOTO 航点及
  `TAKEOFF -> GOTO* -> RETURN_HOME -> LAND -> COMPLETE`，逐段确认 0.5 m 四邻接和不穿越禁飞格；
  节点级 reject、abort、timeout、巡航取消、Land 取消拒绝和假观测统计场景也通过。
- fake H ROS 图检查未发现 `/fmu/in/*` publisher；`verify_architecture.py` 和 `git diff --check` 通过。

以上证明 H 任务层到 fake Action server 的开发机 Humble 运行时闭环，不是新 gateway 的 SITL、真实感知、
Jetson 或实机证据。

## 仍有效的 legacy 运行证据

以下证据属于显式 legacy `offboard_mission_node` 或视觉 bridge，不会自动转移到新 Action gateway：

- Humble `gz_x500` 已以真实 RC 解锁沿完成 Offboard、1.5 m 起飞、约 60 s 悬停、本地 home 返回、Land
  和解除解锁；程序未发送 ARM、DISARM 或 Kill。
- 外部 ARM 不触发任务；人工切出 Offboard、mission 退出或 PX4 failsafe 后，legacy mission 不重抢控制权。
- legacy HOVER 取消已完成返回、Land ACK、新 `landed = true` 样本和解除解锁。
- Offboard ACK target 关联、拒绝、timeout 计时和 Land 新样本保护已有回归；accepted ACK 后始终不进入
  Offboard 的原生运行时分支仍未复现。
- 合成静止 Odometry 的 DDS EKF2 融合和合成静止 TF 的 MAVROS 链路已在未解锁 SITL 通过；这不是
  真实 VIO、动态外参、速度融合、目标 Jetson/Humble 或飞行证据。
- WSL 周期 realtime 后跳已归因到 `systemd-timesyncd` 的 32 s NTP 校时；临时停止后的 host 与原样 A/B
  稳定，但持久 mask 和 Windows suspend/resume 仍未验证。

## 停止条件

- 新 `/offboard/execute_flight` 的 ROS 图、Action 时序、QoS、PX4 ACK 和故障分支尚未运行 SITL。
- H 当前只验证 fake flight/perception：没有真实动物识别、地面站显示保存、激光设备、场地坐标标定、
  真实飞行时限或新 gateway/PX4 证据，不得称为 H 赛题或飞行闭环。
- D wrapper 已声明 Action、订阅和设备 publisher，但尚未把 FSM 接到外部 START、Action 结果、目标观测
  和设备回执，不得称为 D 赛题闭环。
- 八个自研嵌套仓库已合并并回到干净默认分支；核心 manifest 已纳管 `communication` 和 `ti`。
  完整 `verify_repos.py` 仍被上游 `Micro-XRCE-DDS-Agent` 中既有未跟踪目录
  `build-system-fastdds/` 阻塞；本轮未删除或忽略该用户/上游构建状态。
- 真实 VIO 动态、延迟、reset、相机到机体外参，以及升级后的 Jetson Orin Nano Ubuntu 22.04/Humble
  构建和无桨地面联调均未完成。
- 所有实机解锁、Kill、人工接管、系留和受控飞行步骤都必须停在现场操作员逐项批准之前。

任一停止条件未解除，均不得把开发机 Humble 离线或 legacy SITL 结果外推为新 gateway、TI、目标
Jetson/Humble 或实机通过。

## 下一步顺序

1. 在未解锁 SITL 中核对新 gateway 的 ROS 图、单 writer、状态、Action 接受/取消和错误分支；进入 RC
   解锁阶段前必须另行取得操作员确认。
2. 再用模拟目标和设备回执冻结 D 任务的 `FollowTarget`、动态降落和轨迹接口；在接口、
   地图和实时预算明确前不引入 GCOPTER、EGO-Planner 或 BehaviorTree.CPP。
3. 处理开发机持久授时策略、真实 VIO，并在升级后的 Jetson Orin Nano Ubuntu 22.04/Humble 上完成构建、
   DDS 和无桨联调，再进入实机门禁。BehaviorTree.ROS2 的 ROS 版本条件已满足，但仍只在任务复杂度达到
   引入门槛后评估，不进入当前 H 闭环。
