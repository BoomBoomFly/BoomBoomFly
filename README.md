# BoomBoomFly

BoomBoomFly 是室内无人机项目的顶层编排仓库。PX4、Micro-XRCE-DDS-Agent 与 ROS 2
工作区各自独立管理和构建。

```text
BoomBoomFly/
├── px4/
│   ├── upstream/
│   │   ├── PX4-Autopilot/          # PX4 独立仓库与构建目录
│   │   └── Micro-XRCE-DDS-Agent/   # DDS Agent 独立仓库与构建目录
│   └── px4_ws/                     # ROS 2 colcon 工作区
│       └── src/
│           ├── boomboom/           # 自研 ROS 2 仓库
│           └── external/           # 可由 colcon 管理的第三方 ROS 2 包
├── Scripts/
│   ├── workspace/                  # 仓库与 ROS 2 工作区管理
│   └── simulation/                 # PX4 SITL 仿真入口
├── manifests/                      # vcstool 多仓库清单
└── docs/                           # 硬件、验证和通信契约文档
```

顶层仓库不提交各嵌套仓库的源码或构建产物。使用 `manifests/` 和 vcstool 恢复、锁定
各仓库版本；`px4/px4_ws/src/boomboom/` 中的项目包仍保持独立 Git 历史与远端。

目标仓库职责、`ti` 五包结构和单一控制权边界见[工作区架构](docs/工作区架构.md)。
`embedded_systems` 已作为独立嵌套仓库保留，用于嵌入式驱动、小车和后续硬件扩展；`perception`
也已建立独立仓库，用于任务级目标感知。当前迁移不会把 BehaviorTree.CPP 或第三方规划器变成核心依赖。

## 基本操作

```bash
cd /home/aa/BoomBoomFly

# 恢复核心仓库（需要 vcstool）
./Scripts/workspace/pull_repos.sh

# 同时恢复可选 RealSense 源码依赖
./Scripts/workspace/pull_repos.sh --with-perception-deps

# 仅构建 ROS 2 工作区；可指定一个包及其依赖
./Scripts/workspace/build.sh
./Scripts/workspace/build.sh offboard_cpp

# 只重建自研 boomboom ROS 2 包，不扫描 upstream 或 external
cd px4/px4_ws
source /opt/ros/humble/setup.bash
colcon build --base-paths src/boomboom --symlink-install
source install/setup.bash
cd ../..

# 在当前 shell 加载 ROS 2 与已构建工作区
source Scripts/workspace/setup_env.sh

# 构建并运行 PX4 SITL（20.04 默认 Gazebo Classic，22.04 默认 gz_x500）
bash Scripts/simulation/build_px4_sitl.sh
bash Scripts/simulation/run_px4_sitl.sh
```

PX4-Autopilot 和 Micro-XRCE-DDS-Agent 不由 colcon 构建：分别在
`px4/upstream/PX4-Autopilot/` 与 `px4/upstream/Micro-XRCE-DDS-Agent/` 中按其上游
说明独立构建和运行。`Scripts/README.md` 说明各工程级脚本的范围。

`./Scripts/workspace/repo_status.sh` 可查看受管理仓库的分支、提交和脏状态；
`./Scripts/workspace/update_repos.sh` 只会在工作树干净时更新。ROS 2 构建产物位于
`px4/px4_ws/build/`、`px4/px4_ws/install/` 和 `px4/px4_ws/log/`，可使用
`./Scripts/workspace/clean.sh` 删除。

## 飞行与感知边界

- D435i 提供 RGB、深度和原始 IMU，但不是 T265 的即插即用替代品，也不原生产生位姿。
- 在相机—IMU 标定、视觉里程计接入和 PX4 EKF2 验证完成前，不得把 D435i 用作自主起飞、
  悬停或降落的定位来源。
- 每个生产 `/fmu/in/*` 控制话题只能有一个写入方；回放必须使用隔离的
  `ROS_DOMAIN_ID`，且不得接入生产飞控。
- 自动解锁和飞行不属于本仓库脚本的授权范围。飞行前须由操作员完成 Kill、遥控器、QGC
  起飞前检查、机体和桨叶检查。

当前实现、验证证据和停止条件见 [交接文档](docs/handoff.md)；长期接口和安全边界见
[工作区架构](docs/工作区架构.md)，任何实机操作只按
[第一阶段实机门禁清单](docs/第一阶段实机门禁清单.md)推进。

## 第一阶段 SITL 状态

Humble `gz_x500` 已验证真实 RC 解锁沿触发的 Offboard 正常闭环：1.5 m 起飞、约 60 s
悬停、返回本地归航点、降落和解除解锁。`/offboard/cancel_mission` 也已在 HOVER 中完成
SITL 验证，记录了 `CANCELLED`、降落 ACK 和新的 `landed = true` 样本。

受控 Micro XRCE-DDS Agent 重连后，`TimesyncStatus` 恢复为 DDS source；这只说明重连后的
恢复，不能替代自然时间跳变的根因分析，也不能外推到 Foxy、Jetson 或实机。

## 当前边界

`common`、`communication`、`offboard_cpp`、`px4_vision_bridge`、`px4_bringup`、`ti`、`perception`
和 `embedded_systems` 保持各自独立的 Git 历史与远端。只有嵌套仓库形成真实提交并完成验证后，
顶层清单才锁定新的 SHA。

## 可复现性检查

核心清单使用精确提交而不是浮动分支。恢复脚本会递归初始化自研仓库所声明的
Git 子模块。构建或飞行验证前运行：

```bash
cd /home/aa/BoomBoomFly
./Scripts/workspace/pull_repos.sh
./Scripts/workspace/verify_repos.py
./Scripts/workspace/verify_architecture.py

# 使用可选感知源码依赖时
./Scripts/workspace/pull_repos.sh --with-perception-deps
./Scripts/workspace/verify_repos.py --with-perception-deps
```

`verify_repos.py` 会检查清单是否全部为 40 位提交、远端 URL、现场 HEAD、脏工作树、
自研仓库子模块，以及是否存在未被清单管理的 ROS 包。任何检查失败都表示当前
源码树不能被称为可复现基线。Humble 环境还必须提供各包声明的系统依赖；构建 `boomboom`
前应先构建并加载工作区中的 `px4_msgs`。
