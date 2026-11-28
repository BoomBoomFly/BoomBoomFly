# BoomBoomFly

无人机、地面车辆、六足机器人及空地协同研发仓库（ROS 2 Humble + FPGA/MCU）。
仓库采用 **单一自研 Monorepo + `vcstool` 外部依赖清单** 结构：所有自研 ROS 2 功能包、仿真配置与硬件工程均在本仓库统一版本控制；OpenVINS、MAVROS、PX4 等上游源码通过清单按需拉取，不直接提交进主仓历史。

## 目录结构

```text
BoomBoomFly/
├── ros2_ws/                        # 统一 ROS 2 Humble 工作区
│   ├── src/
│   │   ├── interfaces/             # 纯消息/服务接口包：uav_interfaces, ugv_interfaces
│   │   ├── uav/                    # uav_bridge, uav_control, uav_mission, uav_bringup
│   │   ├── ugv/                    # ugv_bridge, car/(car_bringup, car_navigation, car_vision), legged/
│   │   ├── swarm/                  # swarm_cooperation（跨平台对齐、地图融合与协同调度）
│   │   └── thirdparty/             # .gitignore 忽略；由 vcs import 拉取外部依赖
│   └── sim/                        # 仿真配置与启动入口（uav/, ugv/, swarm/）
├── hardware/
│   ├── fpga/                       # 高云 FPGA 板级工程（boards/）及可复用参考库（rtl/, fw/）
│   └── mcu/                        # 下位机 MCU 固件（boards/ 板级工程 + libs/ 通用库）
├── repos/                          # vcstool 外部依赖清单（uav_thirdparty.repos）
└── docs/                           # 架构设计、参考仓库分工与验证记录
```

各子系统详细说明：
- [ROS 2 工作区说明](ros2_ws/README.md)
- [FPGA 工程说明](hardware/fpga/README.md)
- [MCU 工程与算法库说明](hardware/mcu/README.md)
- [外部依赖清单说明](repos/README.md)
- [参考仓库与借鉴分工](docs/参考仓库与借鉴分工.md) · [任务与控制架构现状及讨论记录](docs/任务与控制架构现状及讨论记录.md)

## 快速开始与按平台增量构建

### 1. 拉取仓库与外部依赖

```bash
git clone https://github.com/BoomBoomFly/BoomBoomFly.git ~/BoomBoomFly
cd ~/BoomBoomFly

# 如需构建 UAV OpenVINS / MAVROS / PX4 DDS 依赖：
mkdir -p ros2_ws/src/thirdparty
vcs import ros2_ws/src/thirdparty < repos/uav_thirdparty.repos
```

### 2. 按目标边缘平台选择构建

统一工作区使用 `--packages-up-to` 只编译目标入口及其依赖链，避免在资源受限板卡上全量编译：

```bash
source /opt/ros/humble/setup.bash
cd ~/BoomBoomFly/ros2_ws

# OrangePi（无人机 UAV 全套）
colcon build --symlink-install --packages-up-to uav_bringup

# Jetson（BX72 小车全套）
colcon build --symlink-install --executor sequential --packages-up-to car_bringup

# 无 TensorRT 的开发机（跳过 vision_node C++ 编译，保留接口与 Python 节点）
colcon build --symlink-install --packages-up-to car_bringup --cmake-args -DBUILD_TENSORRT_VISION=OFF

# 树莓派（ACG720 六足桥接端）
colcon build --symlink-install --packages-up-to legged_bridge

# 协同主机（小车 + 六足协同建图与调度）
colcon build --symlink-install --executor sequential --packages-up-to swarm_cooperation
```

构建完成后，在新终端加载环境：

```bash
source /opt/ros/humble/setup.bash
source ~/BoomBoomFly/ros2_ws/install/local_setup.bash
```

## 开发、多端部署与子仓导出工作流

- **主机开发、边缘端部署**：日常在主机/笔记本修改并提交；现场联调可用 `rsync` 快速同步到 Jetson / OrangePi / 树莓派测试，稳定后再在主机一次性提交，边缘端只执行 `git pull --ff-only`。
- **保持主仓历史整洁**：功能开发与调参建议在特性分支完成，合并回 `main` 时使用 GitHub **Squash and merge**，并严禁将 `.bag`/`.db3`/`.mcap`/`.ulg` 录包、模型权重或 FPGA 综合产物提交进仓。
- **独立子仓导出（可选）**：如后续需将某个目录单独导出到独立 GitHub 仓库且不污染主仓历史，可使用 `git subtree split --prefix=<目录> -b <临时分支>` 后推送到目标仓库。

## UAV 技术路线与 SITL 状态

- **定位链路**：D435i 双目红外 + 飞控 IMU → OpenVINS → `uav_bridge` (`odom_bridge` / `imu_bridge`) → MAVROS 或 PX4 DDS → PX4。
- **控制链路**：`uav_mission` → `uav_interfaces` (`VehicleState` / `FlightCommand`) → `uav_control` → MAVROS 或 PX4 DDS。
- **SITL 记录**：PX4 v1.17.0 / Gazebo Sim 8.14.0 起飞-悬停-降落验证见 [UAV SITL 验证记录](ros2_ws/sim/uav/PX4_SITL_起飞悬停降落验证.md)。
