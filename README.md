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
3. `vision_to_dds` 已强制生产 frame 契约，但 T265 实测外参尚未提供和验收。
4. 普通垂直 flight sequence 已通过 Domain 231 隔离回放，尚无实机控制闭环证据。
5. 真实 RC publisher、类型、18 通道变化和 `signal_lost` 已拆桨验证；生产通道号、阈值和物理
   边沿仍须按最终 YAML 逐项验收。
6. 指定 SHA 固件已刷写；DDS 约 50 秒冻结已定位为 Jetson 低内存下 UART RX DMA 分配失败。
   生产 Agent 门禁和干净重启后的 620 秒只读 soak 已通过，G2 PASS；G3 视觉/EKF 尚未执行。
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

普通垂直 `flight sequence` 固定使用 task id `3`。同一 `/fmu/in/*` 控制话题只能存在
一个 ROS 2 writer；测试回放固定在 `ROS_DOMAIN_ID=231`，不进入生产 launch。

## 源码组成

根仓库不直接保存 `src/`。所有功能包由
[`Scripts/installation/uav_px4_dds_install.sh`](Scripts/installation/uav_px4_dds_install.sh)
根据 `workspace.lock.repos` 拉取。

默认 active profile：

- `px4_msgs`：精确提交
- `Micro-XRCE-DDS-Agent`：精确提交
- `offboard_cpp`：经过权威构建的精确提交
- `vision_to_dds`：BoomBoomFly 组织仓的精确提交
- `communication`：包含 `mission_bridge` 的精确提交

`communication/mission_bridge` 解码带 session/seq 的地面链路 START，并只发布任务与故障
话题；它不应发布 `/fmu/in/*` 或伪造 RC。其串口驱动位于
`src/communication/Serial/serial_driver_ros`，由 `communication` 的 Git
子模块提交固定；`serial-ros2` 仅作为 quarantine 来源记录。

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

## 构建与测试

```bash
bash Scripts/build/build_dds_only.sh
```

权威入口先执行根仓集成门禁，再只选择以下包进行 `colcon build`：

- `px4_msgs`
- `offboard_cpp`
- `vision_to_dds`
- `mission_bridge`

三个项目包 `offboard_cpp`、`vision_to_dds`、`mission_bridge` 还会执行
`colcon test`；接口依赖 `px4_msgs` 只构建。构建和测试成功不表示可以
启动电机或装桨飞行。

## 最短实机推进顺序

1. G0 源码/构建和 G1 隔离回放 evidence 已完成。
2. G2 固件、真实 RC 契约和干净重启后的拆桨 DDS/Agent 长稳态 soak 已完成。
3. 下一步须另行批准 G3；先测量 T265 外参，再逐步验证位置分量和 EKF 实际融合。
4. 拆桨逐项验证 RC/Offboard/T265/Agent/ACK/kill/低电/围栏失效结果（G4）。
5. 只有 G0–G4 全 PASS 后重新请求当次装桨、Arm、0.5 m 悬停授权；本轮禁止 G5。

当前准入和未来操作卡见 [FLIGHT_STAGE_READINESS.md](FLIGHT_STAGE_READINESS.md)、
[PROPS_OFF_FLIGHT_STAGE_TEST.md](PROPS_OFF_FLIGHT_STAGE_TEST.md) 与
[FIRST_HOVER_TEST_CARD.md](FIRST_HOVER_TEST_CARD.md)。

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
