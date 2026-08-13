# 仿真

本目录提供 PX4 SITL 的构建、运行和定向清理入口，使用以下工程路径：

```text
PX4:      px4/upstream/PX4-Autopilot
ROS 2:    px4/px4_ws
```

## 基本操作

```bash
# 只构建 PX4 SITL
bash Scripts/simulation/build_px4_sitl.sh

# Ubuntu 20.04 默认运行 Gazebo Classic；Ubuntu 22.04 默认运行 gz_x500
bash Scripts/simulation/run_px4_sitl.sh

# 也可显式指定 PX4 仿真目标
bash Scripts/simulation/run_px4_sitl.sh gz_x500_vision
bash Scripts/simulation/run_px4_sitl.sh gazebo-classic

# 只删除 build/px4_sitl_default，不清理 colcon 工作区或其他 PX4 target
bash Scripts/simulation/clean_px4_sitl.sh
```

在 PX4 已运行后，另开终端启动第一阶段 ROS 链路：

```bash
cd px4/px4_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch px4_bringup sitl.launch.py
```

该启动文件默认启动唯一的 UDP 8888 Micro XRCE-DDS Agent、视觉桥接节点和任务节点。
若该代理已由其他终端管理，先用 `ss -lunp | rg ':8888'` 核对后，改用
`start_agent:=false`；不得启动第二个代理或第二个生产任务写入方。

脚本不安装系统依赖。Ubuntu 20.04 和 22.04 分别使用 PX4 v1.16 官方推荐的
Gazebo Classic 与新 Gazebo 默认目标；其他系统必须显式传入仿真目标。
`HEADLESS=1`、`PX4_GZ_WORLD` 等 PX4 环境变量会原样传递给 `make`。
