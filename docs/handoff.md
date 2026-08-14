---
title: BoomBoomFly 当前交接
status: offline-validated-gateway-sitl-unvalidated
updated: 2026-08-14
---

# BoomBoomFly 当前交接

这是当前工作的唯一状态入口。长期不变量见[工作区架构](工作区架构.md)，参考项目采用决策与阶段路线见
[参考框架采用与演进路线](参考框架采用与演进路线.md)，实机操作只按
[第一阶段实机门禁清单](第一阶段实机门禁清单.md)推进。当前用户确认的要求优先于本文。

## 当前结论

本轮发布已按嵌套仓库优先、顶层仓库最后的顺序完成合并。`common`、`communication`、
`embedded_systems`、`offboard_cpp`、`px4_bringup`、`px4_vision_bridge` 和 `ti` 的精确 merge commit 已写入
核心 manifest；对应远端与本地工作分支均已删除。`perception` 保持干净且无需发布。当前改动删除无消费者
代码和空运行入口，复用现有 ROS/native 能力，并通过隔离构建与离线测试。H 任务继续保有不连接 PX4 的
fake Action 纵向闭环；新 gateway 和 D 任务链仍未完成运行时闭环。本轮没有启动 SITL、DDS Agent、QGC
或任何飞行动作。

旧 `TI` 路径已迁移为 `px4/px4_ws/src/boomboom/ti`，原独立 Git 历史、远端和用户已有删除记录均保留。
年份目录使用 `ti_2025/ti_2026`，ROS 包名和节点入口仍保持 `boomboom_task_h/boomboom_task_d`，避免目录整理
改变运行接口。

自有框架路线已冻结为“稳定能力接口 + 单一飞行执行器 + 可替换 navigation backend + 任务应用”。
Aerostack2、BehaviorTree.CPP、EGO-Planner 和 GCOPTER 当前都不加入核心依赖；PX4 ROS 2 Interface
Library 只保留为 direct-Offboard 基线完成后的隔离 A/B 候选。

## 当前实现

| 范围 | 当前状态 |
|---|---|
| `common` | 保留 ROS-free C99 core；新增 `LocalPose`、`FlightState`、目标观测、设备命令/回执和 `ExecuteFlight` Action。 |
| `offboard_cpp` | 唯一 gateway 提供 Action 与状态；旧版 mission 节点、执行器和兼容接口已删除。 |
| `px4_vision_bridge` | DDS/MAVROS backend 互斥；两条路径复用已有 `tf2::Quaternion`，hardware MAVROS 默认要求已标定机体 TF。 |
| `px4_bringup` | SITL/hardware 只提供 `start_gateway` 控制写入方；TI 入口当前只启动 H。无参数 `build.sh` 只构建该核心依赖闭包。 |
| `communication` | 已定义 Ground/UAV/Car 的版本、session、sequence、幂等和断连语义；未选择传输或线格式。 |
| `ti` | 删除无必要的公共生命周期包、H 的重复 FSM 层和任务模板。H 协调器直接管理状态/结果并接通 fake Action；D 只保留 ROS-free FSM，不提供空节点；无 `px4_msgs` 或 `/fmu/in/*`。 |
| `perception` | 独立仓库和初始 README 已纳入工作区；动物、小车和降落标志感知实现尚未建立和验证。 |
| `embedded_systems` | 删除未绑定目标板卡、无构建消费者的旧平台驱动；目标硬件确定后优先采用 Linux `gpiolib`/`libgpiod`、`i2c-dev`、`leds-gpio`。 |
| manifests | 锁定本轮八个自研嵌套仓库的精确已合并 commit；`perception` 沿用未变基线。 |

PX4 与 `px4_msgs` 基线为 v1.16.2，Micro XRCE-DDS Agent 为 v2.4.2；PX4 v1.16 状态话题使用
`/fmu/out/vehicle_status_v1`。

目标机 Jetson Orin Nano 已由用户确认升级为 Ubuntu 22.04 / ROS 2 Humble。该升级解除旧 ROS 2 版本约束，
但升级后的目标机工作区构建、依赖、DDS、VIO 和无桨地面联调仍须重新验证。

## 当前架构离线证据

- 删除旧版闭包后的 8 个 ROS 包已在 `/tmp` 全新隔离目录构建通过，48 个测试全部通过，未写入现有
  `px4/px4_ws/build|install|log`。
- `offboard_gateway.launch.py`、`sitl.launch.py`、`hardware.launch.py` 和 `ti_task.launch.py` 的
  `--show-args` 全部通过；临时安装树只包含现行运行入口。
- common、communication 合约检查和 `Scripts/workspace/verify_architecture.py` 通过。
- 现行 launch 不再暴露 D 的空运行入口。
- 架构检查确认：TI 不依赖 `px4_msgs`，H/D 互不依赖，已接入飞行的 H 经 navigation 使用 Action，
  `offboard_cpp` 不依赖 TI，三个 PX4 控制输入只出现在 `offboard_cpp` 生产代码。
- gateway 单测覆盖非法/NaN goal、单 goal、RC 启动门、取消转 HOLD、定位或 heading 失效、原地 Land、
  Land 不可取消和新落地样本门禁。
- H 网格覆盖测试确认执行路径只经过四邻接自由格，并覆盖单洞、窄条、不连通和确定性场景。
- H 节点现提供 `/boomboom/task_h/start`、`/boomboom/task_h/cancel` 和
  `/boomboom/task_h/state`；`auto_start` 仍默认关闭，任务层只经 navigation adapter 请求飞行能力。
- H fake 成功场景以 3 个连续禁飞格跑通 60 个自由格、119 个连续 GOTO 航点及
  `TAKEOFF -> GOTO* -> RETURN_HOME -> LAND -> COMPLETE`，逐段确认 0.5 m 四邻接和不穿越禁飞格；
  节点级 reject、abort、timeout、巡航取消、Land 取消拒绝和假观测统计场景也通过。
- fake H ROS 图检查未发现 `/fmu/in/*` publisher；所有本轮改动仓库的 `git diff --check` 通过。

以上证明 H 任务层到 fake Action server 的开发机 Humble 运行时闭环，不是新 gateway 的 SITL、真实感知、
Jetson 或实机证据。

## 仍有效的视觉链路证据

- 合成静止 Odometry 的 DDS EKF2 融合和合成静止 TF 的 MAVROS 链路已在未解锁 SITL 通过；这不是
  真实 VIO、动态外参、速度融合、目标 Jetson/Humble 或飞行证据。
- WSL 周期 realtime 后跳已归因到 `systemd-timesyncd` 的 32 s NTP 校时；临时停止后的 host 与原样 A/B
  稳定，但持久 mask 和 Windows suspend/resume 仍未验证。

## 停止条件

- 新 `/offboard/execute_flight` 的 ROS 图、Action 时序、QoS、PX4 ACK 和故障分支尚未运行 SITL。
- H 当前只验证 fake flight/perception：没有真实动物识别、地面站显示保存、激光设备、场地坐标标定、
  真实飞行时限或新 gateway/PX4 证据，不得称为 H 赛题或飞行闭环。
- D 只有 ROS-free FSM；外部 START、Action、感知、设备回执和节点均未实现，不得称为 D 赛题闭环。
- 本轮八个 PR 和核心 manifest 已形成新的可复现发布；上游
  `Micro-XRCE-DDS-Agent/build-system-fastdds/` 仍是用户拥有的未跟踪目录，因此全量 `verify_repos.py` 仍会
  报告该项，但本轮未删除、忽略或纳入提交。
- 真实 VIO 动态、延迟、reset、相机到机体外参，以及升级后的 Jetson Orin Nano Ubuntu 22.04/Humble
  构建和无桨地面联调均未完成。
- 所有实机解锁、Kill、人工接管、系留和受控飞行步骤都必须停在现场操作员逐项批准之前。

任一停止条件未解除，均不得把开发机 Humble 离线或历史 SITL 结果外推为新 gateway、TI、目标
Jetson/Humble 或实机通过。

## 下一步顺序

1. 在未解锁 SITL 中核对新 gateway 的 ROS 图、单 writer、状态、Action 接受/取消和错误分支；进入 RC
   解锁阶段前必须另行取得操作员确认。
2. 再用模拟目标和设备回执冻结 D 任务的 `FollowTarget`、动态降落和轨迹接口；在接口、
   地图和实时预算明确前不引入 GCOPTER、EGO-Planner 或 BehaviorTree.CPP。
3. 处理开发机持久授时策略、真实 VIO，并在升级后的 Jetson Orin Nano Ubuntu 22.04/Humble 上完成构建、
   DDS 和无桨联调，再进入实机门禁。BehaviorTree.ROS2 的 ROS 版本条件已满足，但仍只在任务复杂度达到
   引入门槛后评估，不进入当前 H 闭环。
4. 若要求全量 `verify_repos.py` 无告警，再单独审计并处理上游
   `Micro-XRCE-DDS-Agent/build-system-fastdds/`；不得把该上游目录混入自研仓库发布。
