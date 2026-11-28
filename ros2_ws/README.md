# ROS 2 统一工作区（`ros2_ws`）

ROS 2 Humble 统一工作区，在一个 `colcon` 工作区内管理无人机、地面车辆、六足机器人、协同调度与共享接口包，消除多层 workspace overlay 依赖。

## 目录与功能包

| 路径 | 功能包 / 内容 | 说明 |
| --- | --- | --- |
| `src/interfaces/uav_interfaces` | `uav_interfaces` | 无人机状态与飞行命令接口（`VehicleState`、`FlightCommand`） |
| `src/interfaces/ugv_interfaces` | `ugv_interfaces` | 地面车共享服务接口（`MissionStart.srv`） |
| `src/uav/uav_bridge` | `uav_bridge` | OpenVINS 里程计安全门控与 IMU 桥接（`odom_bridge`、`imu_bridge`） |
| `src/uav/uav_control` | `uav_control` | PX4 DDS 与 MAVROS 统一控制节点 `uav_control_node` |
| `src/uav/uav_mission` | `uav_mission` | 非阻塞起飞、悬停与降落状态机 `mission_node` |
| `src/uav/uav_bringup` | `uav_bringup` | UAV 统一启动入口 `uav.launch.py` 与集中配置 `uav.yaml` |
| `src/ugv/ugv_bridge` | `ugv_bridge` | BX72 FPGA 遥测、命令、视频与 HTTP 网关 |
| `src/ugv/car/car_bringup` | `car_bringup` | BX72 小车统一启动与建图入口 |
| `src/ugv/car/car_navigation` | `car_navigation` | 全局 SLAM、Nav2 MPPI 配置与 `robot_mission` |
| `src/ugv/car/car_vision` | `car_vision` | TensorRT 目标检测（含自包含 ByteTrack 子集）与视觉伺服 |
| `src/ugv/legged/legged_bridge` | `legged_bridge` | ACG720 UDP/HTTP/ROS 接入与相机标定元数据 |
| `src/ugv/legged/legged_bringup` | `legged_bringup` | ACG720 雷达里程计与建图启动 |
| `src/swarm/swarm_cooperation` | `swarm_cooperation` | 小车与 ACG720 AprilGrid 对齐、地图融合与协同 HTTP 控制台 |
| `src/thirdparty/` | 外部依赖源码 | 由 `.gitignore` 排除，通过 [外部依赖清单](../repos/README.md) 拉取 |
| `sim/uav/` · `sim/swarm/` | 仿真入口与记录 | PX4 SITL 启动入口、历史测试记录与集群仿真预留目录 |

## 常用构建与启动命令

```bash
source /opt/ros/humble/setup.bash
cd ~/BoomBoomFly/ros2_ws

# 1. UAV（无人机）
colcon build --symlink-install --packages-up-to uav_bringup
source ../tools/setup_ros_env.bash
ros2 launch uav_bringup uav.launch.py

# 2. BX72 小车（Jetson）
colcon build --symlink-install --executor sequential --packages-up-to car_bringup
source ../tools/setup_ros_env.bash
ros2 launch car_bringup car_bringup.launch.py

# 3. ACG720 六足（树莓派桥接 / 计算端建图）
colcon build --symlink-install --packages-up-to legged_bridge
ros2 run legged_bridge acg720_bridge
# 计算端：colcon build --symlink-install --packages-up-to legged_bringup
ros2 launch legged_bringup acg720_mapping.launch.py

# 4. 异构协同建图
colcon build --symlink-install --executor sequential --packages-up-to swarm_cooperation
ros2 launch swarm_cooperation cooperative_mapping.launch.py
```

各模块详细参数与设计边界：
- UAV：[uav_control](src/uav/uav_control/README.md) · [uav_mission](src/uav/uav_mission/README.md) · [uav_bridge](src/uav/uav_bridge/README.md) · [uav_bringup](src/uav/uav_bringup/README.md) · [UAV 仿真](sim/uav/README.md)
- UGV：[car_bringup](src/ugv/car/car_bringup/README.md) · [car_navigation](src/ugv/car/car_navigation/README.md) · [ugv_bridge](src/ugv/ugv_bridge/README.md) · [legged](src/ugv/legged/README.md)
- 协同：[swarm_cooperation](src/swarm/swarm_cooperation/README.md) · [集群仿真](sim/swarm/README.md)
