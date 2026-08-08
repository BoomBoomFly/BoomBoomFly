# Simulation

本目录用于 PX4 SITL 仿真脚本。仿真脚本应使用以下工程路径：

```text
PX4:      px4/upstream/PX4-Autopilot
ROS 2:    px4/px4_ws
```

后续建议提供独立的 `build_px4_sitl.sh`、`run_px4_sitl.sh` 和
`clean_px4_sitl.sh`，不要从这里调用或清理 colcon 工作区。
