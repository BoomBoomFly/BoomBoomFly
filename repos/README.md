# 外部依赖清单（vcstool）

本目录使用 ROS 2 标准的 `vcstool`（`.repos`）清单管理外部第三方依赖，避免将大型上游源码直接纳入主仓库历史。

## 拉取 UAV 外部依赖

在仓库根目录执行：

```bash
mkdir -p ros2_ws/src/thirdparty
vcs import ros2_ws/src/thirdparty < repos/uav_thirdparty.repos
```

更新已有第三方源码：

```bash
vcs pull ros2_ws/src/thirdparty
```

## 说明与版本锁定

- **版本锁定**：当前 `uav_thirdparty.repos` 跟踪对应分支（`master` / `ros2` / `main`）。完成实机或 SITL 验证并准备发布稳定基线时，建议运行 `vcs export --exact ros2_ws/src/thirdparty > repos/uav_thirdparty.repos` 锁定精确的 commit hash 或 tag。
- **PX4 SITL**：如需本地编译 PX4 仿真，请将 `PX4-Autopilot` 克隆至 `ros2_ws/upstream/PX4-Autopilot`（已被 `.gitignore` 忽略）。
- **UGV ByteTrack**：经本地裁剪与修改的 ByteTrack 最小子集已自包含于 `ros2_ws/src/ugv/car/car_vision/thirdparty/bytetrack/`，随业务包一并维护，无需额外拉取。
