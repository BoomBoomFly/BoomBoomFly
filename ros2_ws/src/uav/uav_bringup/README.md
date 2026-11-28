# uav_bringup

ROS 2 Humble 启动与配置编排包。统一入口为 `launch/uav.launch.py`，部署参数集中在
`config/uav.yaml`。入口逐个提取节点所属分区，不能把整份集中配置作为 ROS 参数文件传给节点。

## 启动

默认只启动 `uav_control`。请先核对 `config/uav.yaml` 中的 `uav_control.backend`（`mavros` 或 `dds`）及 `read_only` 开关；默认不会启动自动任务、MAVROS、相机、OpenVINS 或视觉里程计桥接。

```bash
ros2 launch uav_bringup uav.launch.py

# 启动相机和 OpenVINS；DDS 后端会自动启动 imu_bridge，uav_bridge 输出保持关闭
ros2 launch uav_bringup uav.launch.py start_control:=false \
  start_camera:=true start_openvins:=true

# 启动 odom_bridge 进程；只有配置 uav_bridge.enabled:=true 才会回传视觉里程计
ros2 launch uav_bringup uav.launch.py start_control:=false \
  start_camera:=true start_openvins:=true start_bridge:=true

# 使用自定义集中配置
ros2 launch uav_bringup uav.launch.py config_file:=/path/to/uav.yaml \
  start_control:=false start_camera:=true start_openvins:=true start_bridge:=true
```

`start_control`、`start_mission`、`start_mavros`、`start_camera`、`start_openvins` 和
`start_bridge` 分别控制进程是否启动。控制后端唯一来源是 `uav_control.backend`（`dds` 或 `mavros`）。
MAVROS 后端下，OpenVINS 直接使用 `/mavros/imu/data_raw`；DDS 后端下，启动 OpenVINS 会同时启动 `imu_bridge`。
`uav_bridge.enabled` 默认 `false`，与控制后端 `read_only: true` 相互独立。

## 相机与 OpenVINS

默认 D435i 双目使用 `848x480x30`，与 `config/openvins/d435i/` 中的相机标定一致；安装时
该标定目录会随 `config/` 一并安装到 `uav_bringup` share 下。相机驱动保留原始
848×480 图像，OpenVINS 配置负责内部降采样。

```bash
ros2 launch uav_bringup uav.launch.py start_control:=false \
  start_camera:=true start_openvins:=true openvins_config_file:=/path/to/estimator_config.yaml
```

OpenVINS 使用 `run_subscribe_msckf` 接口：`config_path`、`verbosity`、`use_stereo`、`max_cameras`、`save_total_state` 与 `imu0_rostopic`。

## 离线诊断工具

VIO 实时检查、录包与离线分析脚本位于仓库根目录 `tools/vio/`（`check_vio.py`、`record_vio.py`、`analyze_vio_bag.py`），在加载工作区 overlay 后直接以 `python3 tools/vio/<脚本>` 运行。

## 集中配置分区

`config/uav.yaml` 包含 `camera`、`uav_control`、`uav_bridge` 和 `uav_mission`。
OpenVINS 相机、IMU 标定和估计器配置位于本包 `config/openvins/d435i/`。
