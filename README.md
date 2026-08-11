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

## 基本操作

```bash
cd /home/aa/BoomBoomFly

# 恢复核心仓库（需要 vcstool）
./Scripts/workspace/pull_repos.sh

# 同时恢复 RealSense、IMU filter 和 RTAB-Map 源码依赖
./Scripts/workspace/pull_repos.sh --with-perception

# 仅构建 ROS 2 工作区；可指定一个包及其依赖
./Scripts/workspace/build.sh
./Scripts/workspace/build.sh offboard_cpp

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
- 每个生产 `/fmu/in/*` 控制话题只能有一个 writer；回放必须使用隔离的
  `ROS_DOMAIN_ID`，且不得接入生产飞控。
- 自动解锁和飞行不属于本仓库脚本的授权范围。飞行前须由操作员完成 Kill、遥控器、QGC
  preflight、机体和桨叶检查。

第一阶段的实现范围、验证门和现场限制见
[第一阶段实施计划](docs/第一阶段实施计划.md)。

## 当前边界

`common`、`offboard_cpp`、`px4_vision_bridge` 和 `px4_bringup` 保持各自独立的 Git 历史与
远端；`communication` 也保留独立仓库，但第一阶段不是 ROS 2 运行包。视觉 bridge 的 Git
远端仍为原 `vision_to_dds` 仓库，以保留历史。

## 可复现性检查

核心 manifests 使用精确提交而不是浮动分支。恢复脚本会递归初始化自研仓库所声明的
Git submodule。构建或飞行验证前运行：

```bash
cd /home/aa/BoomBoomFly
./Scripts/workspace/pull_repos.sh
./Scripts/workspace/verify_repos.py

# 使用可选感知源码依赖时
./Scripts/workspace/pull_repos.sh --with-perception
./Scripts/workspace/verify_repos.py --with-perception
```

`verify_repos.py` 会检查 manifest 是否全部为 40 位提交、远端 URL、现场 HEAD、脏工作树、
自研仓库 submodule，以及是否存在未被 manifest 管理的 ROS 包。任何检查失败都表示当前
源码树不能被称为可复现基线。Humble 环境还必须提供各包声明的系统依赖；当前基线首次
