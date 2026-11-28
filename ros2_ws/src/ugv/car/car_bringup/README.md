# 小车统一启动

在 Jetson 已构建的 ROS 2 Humble 工作区中加载 `install/setup.bash` 后启动：

```bash
ros2 launch car_bringup car_bringup.launch.py
# 只测试航点时关闭视觉检测与伺服：
ros2 launch car_bringup car_bringup.launch.py enable_vision:=false
# 仅启动遥测、视频、建图与相机安装变换：
ros2 launch car_bringup car_mapping.launch.py
```

节点网络、速度、视频和模型设置位于 `config/bringup.yaml`。启动参数支持 `enable_vision:=false`、`enable_command:=false`、`enable_mission:=false` 或 `global_map_enabled:=false`。各节点启动不等于机器人已完成真实场地导航验证。

每次启动重新建图，启动入口将 `map_file_name` 强制设为空字符串，即使自定义配置指定旧图也不会恢复；历史地图归档仍保留。

默认使用系统安装的 Humble `slam_toolbox`（并将 `minimum_travel_distance` 设为 `0.0`，以便静止状态也能发布扫描位姿）。如需使用自定义编译的 `libkartoSlamToolbox.so` 与 `libtoolbox_common.so`，可显式传入 `slam_library_dir:=/实际库目录`。

已有建图和接收节点时，可单独启动命令桥与导航任务：`ros2 launch car_navigation mission_services.launch.py`。
