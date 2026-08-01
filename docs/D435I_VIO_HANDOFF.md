# D435i VIO → PX4 交接

更新：2026-08-01

## 当前状态

- 当前任务入口：`px4_bringup/hover_d435i_0_5m.launch.py`。
- 启动参数保持 `auto_arm=false`：不会自动解锁或起飞；遥控器手动解锁后才允许申请 Offboard。
- MicroXRCE Agent 与 PX4 DDS 已建立连接。
- 当前视觉链路未就绪：`/camera/infra1/image_rect_raw`、`/d435i_vio/imu`、`/d435i_vio/odometry`、`/vision/quality`、`/fmu/in/vehicle_visual_odometry` 均为 `0 Hz`，因此 Offboard readiness 为 `odom=0`，QGC 的 `No offboard signal` 是预期保护行为。
- D435i 已枚举为 USB 3.x（5000M），但 RealSense 驱动尚未发布数据流。

## 已生效修改

- 视觉桥将启动期 `QUALITY_LOW` 视为 warmup：停止发布但不锁存；质量恢复后需两帧健康 TF 才恢复 PX4 `VehicleOdometry`。
- 时间回退、时间戳跳变、重复 writer、输入超时等严重故障仍保持锁存。
- D435i launch 显式关闭该型号不支持的 `pose`、`fisheye1`、`fisheye2` 流。
- 视觉桥单元测试已通过（8/8）。

涉及文件：

- `src/vision_to_dds/src/vision_contract.cpp`
- `src/vision_to_dds/include/vision_to_dds/vision_contract.hpp`
- `src/vision_to_dds/test/test_vision_contract.cpp`
- `src/vision_to_dds/launch/d435i_vio_to_px4.launch.py`

## 自启动

- 保留 `/etc/systemd/system/ros2_offboard.service`，当前为 `disabled`、`inactive`。
- 已移除 crontab 中指向不存在 `startup.sh` 的 `@reboot` 项。
- 后续如需自启动，应修改该 systemd 服务为当前工作空间和唯一 launch 入口，避免旧的 `start_all.launch.py` 重复启动节点。

## 下一步

1. 确保机体上锁、桨叶安全。
2. 对 D435i 执行硬件重置或重新供电；确认 USB 3.x 枚举。
3. 重启唯一任务实例。
4. 确认以下话题均有数据：红外图像、IMU、VIO odometry、`/vision/quality`、`/fmu/in/vehicle_visual_odometry`。
5. 确认 `/offboard/readiness` 中 `odom=1` 后，再由操作员遥控器手动解锁。

## 安全边界

本记录不构成解锁、Offboard 或飞行授权。进行飞行前必须由操作员独立完成 Kill、遥控器、QGC preflight、机体与桨叶检查。
