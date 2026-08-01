# D435i RealSense 集成记录

更新时间：2026-08-01。本文记录当前 Jetson Orin Nano / Ubuntu 20.04 / ROS 2 Foxy
工作区中 D435i 的可复现状态，不把已退役的 T265 流程当作当前配置。

## 锁定的软件版本

| 组件 | 版本 | 精确提交 |
| --- | --- | --- |
| librealsense | v2.58.1 | `bf2778061d5dd29776e9aca8765f75852671760b` |
| realsense-ros | 4.51.1 | `2a65533ee7431bdc05fe5744798efc7f5713f866` |

这两个版本均由根目录的 `workspace.lock.repos` 锁定。librealsense 以默认
V4L2/HID 后端构建，`FORCE_RSUSB_BACKEND=OFF`；不要在该主机上改用 RSUSB
后端，因为此前该后端会枚举到设备却收不到 IMU 帧，并出现 libusb
`Resource temporarily unavailable` 控制传输警告。

## 已验证状态

- 设备为 Intel RealSense D435i（PID `0x0B3A`），USB 3.2 链路；固件为 `5.15.1`。
- `rs-enumerate-devices` 可枚举 RGB、立体深度和 BMI085 运动模块；加速度计支持
  100/200/400 Hz，陀螺仪支持 200/400 Hz。
- `realsense2_camera` 可打开加速度计 100 Hz 和陀螺仪 200 Hz。
- `/camera/imu` 已收到同时含角速度和线加速度的 `sensor_msgs/Imu` 消息，静止时
  加速度模长约为重力加速度；IMU 数据链路已恢复。

## 启动与检查

在工作区根目录执行：

```bash
source /opt/ros/foxy/setup.bash
source install/setup.bash
export LD_LIBRARY_PATH="$PWD/install/librealsense2/lib:${LD_LIBRARY_PATH:-}"

ros2 launch realsense2_camera rs_launch.py \
  enable_gyro:=true enable_accel:=true \
  unite_imu_method:=2
```

`unite_imu_method` 在该 ROS 2 Foxy 驱动版本中是整数；`2` 表示线性插值。
不能传入字符串 `linear_interpolation`。Foxy 的 `ros2 topic echo` 不支持 `--once`，
请用以下命令观察后以 `Ctrl-C` 结束：

```bash
ros2 topic echo /camera/imu
ros2 topic hz /camera/gyro/sample
ros2 topic hz /camera/accel/sample
```

`/camera/imu` 的 `orientation_covariance[0] = -1` 与零四元数表示驱动没有提供姿态
估计，这是原始 IMU 流的正常语义，并非 IMU 无数据。

## 构建方法

在同一个已恢复的工作区中执行。首次或切换后端时，只删除四个 RealSense 包的
`build/`、`install/` 和 `log/` 产物，再重新构建；不要删除整个工作区的构建结果。

```bash
source /opt/ros/foxy/setup.bash

colcon build --packages-select librealsense2 --executor sequential \
  --cmake-args -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_EXAMPLES=OFF -DBUILD_GRAPHICAL_EXAMPLES=OFF

CMAKE_PREFIX_PATH="$PWD/install/librealsense2:${CMAKE_PREFIX_PATH:-}" \
LD_LIBRARY_PATH="$PWD/install/librealsense2/lib:${LD_LIBRARY_PATH:-}" \
PKG_CONFIG_PATH="$PWD/install/librealsense2/lib/pkgconfig:${PKG_CONFIG_PATH:-}" \
colcon build --packages-select realsense2_camera_msgs realsense2_description realsense2_camera \
  --executor sequential --cmake-args -DCMAKE_BUILD_TYPE=Release
```

构建后可确认后端和链接目标：

```bash
grep '^FORCE_RSUSB_BACKEND:BOOL=' build/librealsense2/CMakeCache.txt
ldd install/realsense2_camera/lib/realsense2_camera/realsense2_camera_node | grep librealsense
rs-enumerate-devices
```

预期第一条输出为 `FORCE_RSUSB_BACKEND:BOOL=OFF`，并且节点链接到工作区中的
`librealsense2.so.2.58`。

## 当前限制与后续动作

1. 启动时仍可能出现 `IMU Calibration is not available, default intrinsic and extrinsic will be used`。
   原始 IMU 可用，但在取得可信的相机—IMU 内外参前，不能将其用于精度要求高的 VIO
   或飞控状态估计。
2. 默认深度配置曾报告 `Depth stream start failure`。这是独立于 IMU 的未解决问题；
   先用低带宽深度流复测：

   ```bash
   ros2 launch realsense2_camera rs_launch.py \
     enable_color:=false depth_module.profile:=640x480x30 \
     enable_gyro:=true enable_accel:=true unite_imu_method:=2
   ```

   若该配置稳定，再逐步开启 RGB；若仍失败，检查直连 USB 3 数据线、供电和固件。
3. D435i 不是 T265 的即插即用替代品：它不原生产生位姿话题。仓库现通过双目 VIO 与
   `vision_to_dds` 适配器产生 `/fmu/in/vehicle_visual_odometry`，并已在 USB 3.2、无桨
   台架上确认 PX4 EKF2 融合位置、高度和航向。USB 2.1 会导致 VIO 数据超时，不能用于
   此用途。动态验证、Offboard 安全演练和带桨飞行仍未完成；在获得单独飞行授权前，禁止
   依赖 D435i 进行自主起飞、悬停或降落。
