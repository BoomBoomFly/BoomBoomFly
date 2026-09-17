# BoomBoomFly

室内无 GPS 无人机科研原型，使用 ROS 2 Humble、PX4 和 MAVROS。
本仓库管理工作区说明与辅助脚本；自写包
[`uav_control`](https://github.com/BoomBoomFly/uav_control)、
[`uav_vio_bridge`](https://github.com/BoomBoomFly/uav_vio_bridge) 和
[`uav_bringup`](https://github.com/BoomBoomFly/uav_bringup) 分别独立管理。

## 技术路线与接口隔离

- 定位链路：D435i 左右红外图像 + 飞控 IMU → OpenVINS → uav_vio_bridge → MAVROS / MAVLink
  → PX4 external vision。
- 控制链路：ROS 2 C++ 任务 → MAVROS setpoint → PX4 内部位置/速度控制器。

定位数据接入与任务控制保持独立。飞控通信集中在接口文件中，后续任务逻辑
不直接依赖具体 topic/service。当前使用 MAVROS；DDS 接口仅预留，尚未实现
通信或加入构建。以后迁移控制通道时须保持单一控制来源。

当前发送给 MAVROS 的位置使用本地 ENU，由 MAVROS 完成 ENU/NED 转换。
`uav_vio_bridge` 将 OpenVINS 的 `PoseWithCovarianceStamped` 原样转发到
MAVROS `/mavros/vision_pose/pose_cov`，不修改时间戳或坐标。
OpenVINS 接入前仍需检查实际 topic、frame、timestamp 和坐标约定。
EGO-Swarm、DDS 迁移和完整任务框架属于后续工作。

## 当前状态

以下环境与 SITL 状态来自已确认的开发记录，不代表每次文档更新都重新验证：

| 项目 | 状态 |
| --- | --- |
| 开发环境 | Ubuntu 22.04.5、ROS 2 Humble、Gazebo Harmonic（gz sim 8.14.0） |
| MAVROS | ros2 分支源码编译成功，包含 mavlink、mavros_msgs、libmavconn、mavros、mavros_extras；GeographicLib egm96-5 已安装 |
| PX4 | v1.17.0，关键 submodule 已初始化，`make px4_sitl gz_x500` 已实际启动成功 |
| uav_control | C++17 / rclcpp / ament_cmake；实现 state 订阅和 YAML 目标的约 20 Hz 位置 setpoint 发布，包编译通过 |
| ROS 通信检查 | 先前独立测试收到 0 条消息，原因尚未确认；不能认定控制包与 MAVROS/PX4 已联通 |
| 飞行控制 | OFFBOARD 切换、ARM、起飞/悬停及完整状态机尚未实现 |
| 定位 | 最小 `uav_vio_bridge` 已实现，独立编译及 run/launch 启动通过；消息转发测试超时，OpenVINS → PX4 链路尚未验证 |
| 启动编排 | `uav_bringup` 第一版已编译，两个 launch 启动及正常退出已验证；仅启动桥接节点，不代表 VIO 链路跑通 |
| 实机 | 飞控尚未到货，H743 串口、固件、MAVLink 参数和 IMU 均未验证 |

## 目录与 Git 归属

```text
BoomBoomFly/
├── Scripts/                     # 同步、推送和环境加载
├── ros_ws/
│   ├── src/
│   │   ├── uav_control/         # 自写独立 Git 仓库
│   │   ├── uav_vio_bridge/      # OpenVINS 位姿桥接，独立 Git 仓库
│   │   ├── uav_bringup/         # 启动与 YAML 配置编排，独立 Git 仓库
│   │   └── thirdparty/          # MAVROS、MAVLink、OpenVINS 等本地源码
│   ├── upstream/PX4-Autopilot/  # PX4 源码
│   ├── build/
│   ├── install/
│   └── log/
├── references/                  # 本地参考仓库
└── docker/kalibr/source/        # 本地第三方源码
```

父仓库忽略第三方、参考仓库、构建产物与三个自写独立仓库目录。
三个包的源码在各自仓库中提交，不是 Git submodule。
克隆主仓库后，三个包均可用同步脚本获取。
其他自写包不会因整个 `ros_ws/src` 被忽略而丢失。

## 同步与编译

```bash
cd /home/aa/BoomBoomFly
./Scripts/sync_ros_packages.sh
source Scripts/setup_ros_environment.bash
cd ros_ws
CMAKE_BUILD_PARALLEL_LEVEL=2 MAKEFLAGS="-j2" colcon build \
  --packages-select uav_control --symlink-install
source install/local_setup.bash
ros2 launch uav_control setpoint.launch.py
```

以上针对当前已有依赖和 install 的开发环境。同步脚本依次克隆或快进更新
`uav_control`、`uav_vio_bridge`、`uav_bringup`，不安装 ROS、不准备第三方、不编译 PX4。
新机器需要先准备上述依赖；环境脚本要求工作区已生成 `install/local_setup.bash`。

获取或更新自写包，然后仅编译 VIO 桥接包：

```bash
cd /home/aa/BoomBoomFly
./Scripts/sync_ros_packages.sh
source /opt/ros/humble/setup.bash
cd ros_ws
colcon build --base-paths src/uav_vio_bridge --packages-select uav_vio_bridge --symlink-install
source install/setup.bash
ros2 launch uav_vio_bridge uav_vio_bridge.launch.py
```

已有独立仓库可执行 `git -C ros_ws/src/uav_vio_bridge pull --ff-only`。
桥接包参数、验证命令与证据边界见其 [README](https://github.com/BoomBoomFly/uav_vio_bridge#readme)。
推送脚本支持 `uav_vio_bridge` 范围，见下方示例。

## 最小 VIO 启动编排

在 `ros_ws` 下编译并启动：

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select uav_vio_bridge uav_bringup
source install/setup.bash
ros2 launch uav_bringup uav.launch.py
```

也可单独执行 `ros2 launch uav_bringup vio.launch.py`；两个入口分别运行。
当前结构为 `uav.launch.py → vio.launch.py → uav_vio_bridge_node`。
参数集中在 `uav_bringup/config/uav_vio_bridge.yaml`，沿用桥接包现有话题。
尚未编排 OpenVINS、MAVROS、D435i 或 uav_control。
详细配置和验证边界见 [uav_bringup README](https://github.com/BoomBoomFly/uav_bringup#readme)。

## SITL 与 MAVROS

终端一启动 PX4：

```bash
cd /home/aa/BoomBoomFly/ros_ws/upstream/PX4-Autopilot
make px4_sitl gz_x500
```

终端二加载环境并连接 MAVROS：

```bash
cd /home/aa/BoomBoomFly
source Scripts/setup_ros_environment.bash
ros2 launch mavros px4.launch \
  fcu_url:="udp://127.0.0.1:14540@127.0.0.1:14580"
```

该地址对应已确认的 PX4 Onboard MAVLink local/listen 14580、remote 14540。
预期 `/mavros/state` 显示 `connected: true`；此处提供待执行的联通步骤，
不代表该连接已通过验证。控制包验证命令见同步后的
`ros_ws/src/uav_control/README.md`。发布位置 setpoint 本身不会自动解锁或切换模式。

## 提交与推送

```bash
# 四个独立范围，按需执行；会暂存并提交所选范围内全部未忽略改动。
./Scripts/push_git.sh uav_control "更新控制接口"
./Scripts/push_git.sh uav_vio_bridge "更新位姿桥接"
./Scripts/push_git.sh uav_bringup "更新启动编排"
./Scripts/push_git.sh main "更新工作区脚本与文档"
```

执行前检查对应仓库的 `git status`。`main` 是主仓库范围名，不是固定分支名。
脚本不自动拉取或强制推送；推送失败会保留本地提交。
详细范围、保护规则与离线检查见 [Scripts/README.md](Scripts/README.md)。
