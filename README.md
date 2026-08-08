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

当前 D435i/VIO 状态、验证步骤和已知限制见
[D435i RealSense 集成记录](docs/D435I_REALSENSE_INTEGRATION.md) 与
[D435i VIO → PX4 交接](docs/D435I_VIO_HANDOFF.md)。

## 当前边界

`common`、`offboard_cpp`、`vision_to_dds` 和 `px4_bringup` 保持各自独立的 Git 历史与
远端。当前整理不包含业务代码合并或重构。
