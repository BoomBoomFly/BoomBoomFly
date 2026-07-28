# BoomBoomFly

BoomBoomFly 是面向室内无人机实机验证的 ROS 2 / PX4 DDS 工作区。当前目标是
使用 T265 提供室内视觉定位，通过 DDS Offboard 完成起飞、悬停和降落。

## 硬件与软件基线

- 机载计算机：NVIDIA Jetson Orin Nano，Ubuntu 20.04.6，ROS 2 Foxy
- 飞控：Pixhawk 2.4.8，`PX4_FMU_V3` / V30，STM32F42x rev.5
- 固件：PX4 v1.16.2 stable，NuttX 11.0.0
- DDS：TELEM2，921600 baud，Domain ID 0
- 定位：Intel RealSense T265
- 深度相机：Intel RealSense D435，暂不参与 PX4 定位

现场采集结果见：

- [机载技术验证](docs/evidence/sessions/20260728T174752+0800_onboard_validation/ONBOARD_VALIDATION.md)
- [PX4 参数审计](docs/evidence/sessions/20260728T213311+0800_px4_parameter_audit/PX4_PARAMETER_AUDIT.md)

## 当前状态

已经确认：

- Pixhawk、PX4、NuttX 和 MCU 身份
- uXRCE-DDS Agent 可通过 `/dev/ttyTHS0` 与飞控通信
- T265 位姿约 199 Hz，ROS 2 数据流稳定
- `offboard_cpp`、`vision_to_dds` 和 DDS 工作区能够在机载环境构建
- `vision_to_dds` 已包含时间戳、质量和数据冻结检查

尚未达到装桨起飞条件：

1. `EKF2_EV_CTRL=0`，PX4 尚未融合外部视觉。
2. T265 到机体坐标系的外参尚未测量和验证。
3. `vision_to_dds` 默认帧名与实机 T265 帧名尚未统一。
4. `offboard_cpp` 只转发外部 setpoint，没有生成起飞、悬停和降落轨迹的节点。
5. 当前 launch 没有提供安全门所需的 RC、kill、控制状态和人工触发输入。
6. 最新记录中 `/fmu/out/rc_channels` 没有 publisher。
7. Offboard 丢失、RC 丢失、视觉丢失和低电量动作尚未完成拆桨验证。
8. 电机序号、旋向、传感器校准和首次室内运动包线没有形成实机证据。

当前仅适合继续代码集成、视觉融合和拆桨台架。完成上述项目后，再进入装桨
低高度短时悬停。

## DDS 数据链

```text
T265
  -> vision_to_dds
  -> /fmu/in/vehicle_visual_odometry
  -> PX4 EKF2

flight sequence
  -> /offboard/cmd
  -> /offboard/cmd_mode
  -> offboard_cpp
  -> /fmu/in/offboard_control_mode
  -> /fmu/in/trajectory_setpoint
  -> /fmu/in/vehicle_command
  -> PX4
```

`flight sequence` 尚未在当前工作区实现。同一 `/fmu/in/*` 控制话题只能存在
一个 ROS 2 writer。

## 源码组成

根仓库不直接保存 `src/`。所有功能包由
[`Scripts/installation/uav_px4_dds_install.sh`](Scripts/installation/uav_px4_dds_install.sh)
根据 `workspace.lock.repos` 拉取。

默认 active profile：

- `px4_msgs`：精确提交
- `Micro-XRCE-DDS-Agent`：精确提交
- `offboard_cpp`：跟随 `DDS`
- `vision_to_dds`：跟随 `master`
- `communication`：跟随 `main`

`communication` 用于后续机载计算机与单片机通信，不属于 PX4 控制链，不应
发布 `/fmu/*` 或 `/offboard/*` 控制话题。

`px4_bringup` 只保留在 archive profile。RealSense 相关仓库位于
optional-perception profile。

## 恢复工作区

在 Ubuntu 20.04 / ROS 2 Foxy 环境中执行：

```bash
git clone https://github.com/BoomBoomFly/BoomBoomFly.git
cd BoomBoomFly

bash Scripts/installation/uav_px4_dds_install.sh \
  --with-optional perception \
  --update \
  --require-colcon
```

只检查当前 checkout：

```bash
bash Scripts/installation/uav_px4_dds_install.sh \
  --with-optional perception \
  --verify-only \
  --require-colcon
```

## 构建

```bash
bash Scripts/build/build_dds_only.sh
```

构建入口只选择：

- `px4_msgs`
- `offboard_cpp`
- `vision_to_dds`

构建成功只表示代码可以编译，不表示可以启动电机或装桨飞行。

## 最短实机推进顺序

1. 统一 T265 TF 帧并测量相机到机体外参。
2. 启用 PX4 外部视觉融合，确认 local position 持续有效。
3. 实现最小 flight-sequence 节点：起飞、定点悬停、下降、着陆确认和停桨。
4. 补齐并验证 RC、kill、控制状态、command ACK 和失效回退。
5. 拆桨检查电机序号、旋向、飞控模式切换和完整起降状态机。
6. 设置保守的高度、速度、围栏和最长飞行时间。
7. 装桨执行低高度、短时间的首次室内悬停。

## 仓库结构

```text
Scripts/
  build/                 DDS-only 构建入口
  evidence/              evidence 格式检查
  installation/          依赖恢复与环境检查
config/profiles/         功能包和 launch 清单
docs/evidence/           实机记录、环境快照和依赖回执
tools/authority/         Offboard 控制状态运行工具
workspace.lock.repos     唯一源码清单
workspace.excluded_packages
                         不进入 DDS-only 构建的包名
```

脚本说明见 [Scripts/README.md](Scripts/README.md)。
