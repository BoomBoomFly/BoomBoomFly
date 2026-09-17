# BoomBoomFly

室内无 GPS 无人机科研原型，使用 ROS 2 Humble、PX4 和 MAVROS。
本仓库管理工作区说明与辅助脚本；自写控制包
[`uav_control`](https://github.com/BoomBoomFly/uav_control) 独立管理。

## 技术路线与接口隔离

- 定位链路：D435i 左右红外图像 + 飞控 IMU → OpenVINS → MAVROS / MAVLink
  → PX4 external vision。
- 控制链路：ROS 2 C++ 任务 → MAVROS setpoint → PX4 内部位置/速度控制器。

定位数据接入与任务控制保持独立。飞控通信集中在接口文件中，后续任务逻辑
不直接依赖具体 topic/service。当前使用 MAVROS；DDS 接口仅预留，尚未实现
通信或加入构建。以后迁移控制通道时须保持单一控制来源。

当前发送给 MAVROS 的位置使用本地 ENU，由 MAVROS 完成 ENU/NED 转换。
OpenVINS 接入前需检查实际 topic、frame、timestamp 和消息类型，优先使用
配置与 remap；仅在确实需要适配时增加最小 VIO bridge。
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
| 定位 | OpenVINS → PX4 链路尚未验证，未实现额外 VIO bridge |
| 实机 | 飞控尚未到货，H743 串口、固件、MAVLink 参数和 IMU 均未验证 |

## 目录与 Git 归属

```text
BoomBoomFly/
├── Scripts/                     # 同步、推送和环境加载
├── ros_ws/
│   ├── src/
│   │   ├── uav_control/         # 自写独立 Git 仓库
│   │   └── thirdparty/          # MAVROS、MAVLink、OpenVINS 等本地源码
│   ├── upstream/PX4-Autopilot/  # PX4 源码
│   ├── build/
│   ├── install/
│   └── log/
├── references/                  # 本地参考仓库
└── docker/kalibr/source/        # 本地第三方源码
```

父仓库忽略第三方、参考仓库、构建产物与独立 `uav_control` 目录。
`uav_control` 的源码在自己的仓库中正常提交；此目录不是 Git submodule，
克隆主仓库后需用同步脚本获取。其他自写包不会因整个 `ros_ws/src` 被忽略而丢失。

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

以上针对当前已有依赖和 install 的开发环境。同步脚本仅克隆或快进更新
`uav_control`，不安装 ROS、不准备第三方、不编译 PX4。
新机器需要先准备上述依赖；环境脚本要求工作区已生成 `install/local_setup.bash`。

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
# 两个独立范围，按需执行；会暂存并提交所选范围内全部未忽略改动。
./Scripts/push_git.sh uav_control "更新控制接口"
./Scripts/push_git.sh main "更新工作区脚本与文档"
```

执行前检查对应仓库的 `git status`。`main` 是主仓库范围名，不是固定分支名。
脚本不自动拉取或强制推送；推送失败会保留本地提交。
详细范围、保护规则与离线检查见 [Scripts/README.md](Scripts/README.md)。
