# UAV 仿真

这里保存 SITL 启动入口和 [2026-09-19 历史验证](PX4_SITL_起飞悬停降落验证.md)。
PX4/Gazebo、Agent 或 MAVROS 需单独准备，本地当前树不包含 PX4 源码和当时的 SITL 日志。

## 当前入口

[sitl_flight.launch.py](sitl_flight.launch.py) 复用统一 `uav_bringup/launch/uav.launch.py`，
只传入 `config_file` 并设置 `start_mission=true`。它不启动 PX4、Gazebo、Agent 或 MAVROS。
在 `ros2_ws` 根目录加载已编译的 overlay 后按文件路径启动：

```bash
# 先准备仿真与通信，并加载匹配的控制/任务/bringup overlay
ros2 launch "$PWD/sim/uav/sitl_flight.launch.py" \
  config_file:=/absolute/path/to/uav_sitl.yaml
```

配置副本来自 [uav.yaml](../../src/uav/uav_bringup/config/uav.yaml)：
MAVROS 仿真显式设 `uav_control.backend=mavros`，DDS 仿真显式设 `dds`；
仿真与控制核对后再将选中后端的 `read_only` 设为 `false`。该入口会启动自动任务，不用于只读检查。

同次试验只运行一个控制后端和一个任务目标来源；各节点需要同一版本的 `uav_interfaces`。
历史 MAVROS 连接为 `udp://:14540@127.0.0.1:14580`、PX4 `gz_x500`，
不代表当前端口、固件和参数已确认。SITL 通过不证明 VIO、真实飞控或自由飞行通过。
