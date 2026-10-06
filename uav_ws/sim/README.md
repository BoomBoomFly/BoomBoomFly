# UAV 仿真

集中存放本工程自有的 PX4 SITL 启动文件和仿真验证记录。

- `uav_bringup/launch/sitl_flight.launch.py`：启动控制与任务节点。
- [PX4 SITL 验证记录](PX4_SITL_起飞悬停降落验证.md)：环境、操作步骤和历史结果。
- PX4 源码及其内置 Gazebo 模型、世界和插件仍位于 `../upstream/PX4-Autopilot/`，由上游仓库管理。

从 `uav_ws` 构建：

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src/uav_control/uav_interfaces src --packages-select mavros_msgs uav_interfaces uav_control uav_mission uav_bringup
source install/setup.bash
```

先按验证记录启动 PX4、Gazebo、QGroundControl 与 MAVROS，再运行：

```bash
ros2 launch uav_bringup sitl_flight.launch.py
```

仿真文件由原包的 CMake 安装，ROS 包名和命令保持一致。构建需要完整的 `uav_ws/src` 与 `uav_ws/sim` 布局；单独克隆 `uav_bringup` 不包含这里的入口。SITL 结果不代表实机验证。
