# BoomBoomFly

BoomBoomFly 是面向室内无人机的 ROS 2 / PX4 DDS 工作区。当前目标是通过
DDS Offboard 完成起飞、悬停和降落，并由 T265 视觉里程计提供室内定位。

当前技术基线：

- Ubuntu 20.04
- ROS 2 Foxy
- PX4 v1.16.2
- Pixhawk 2.4.8 / PX4 FMUv3 / STM32F42x
- NuttX 11.0.0
- PX4 uXRCE-DDS：TELEM2、921600 baud、Domain ID 0
- `px4_msgs`、`offboard_cpp`、`vision_to_dds`

`src/communication` 是独立子模块，用于后续伴随计算机与单片机通信。它不
属于 PX4 DDS 控制链，不得发布 `/fmu/*` 或控制 `/offboard/*` 话题。
`px4_bringup` 保留在 archive profile，用于开发参考，不是默认控制入口。

## 当前实机状态

2026-07-28 的参数与只读硬件检查结果：

| 项目 | 当前结果 |
|---|---|
| 飞控 | Pixhawk 2.4.8；`PX4_FMU_V3` / V30；STM32F42x rev.5 |
| 固件 | PX4 1.16.2 stable；Git `54f0455ffcd755534539a7cf33a09a20bf71d29d` |
| 飞控 OS | NuttX 11.0.0；Git `886acbbdb4f061e5c0ce1a76afbcfa7cb7df9849` |
| 构建 | 2026-04-22 14:06:56；default；GCC 9.3.1 |
| 机架身份 | Generic Quadcopter；System ID 1 |
| DDS | uXRCE-DDS 配置到 TELEM2，921600 baud |
| T265 | 位姿约 199 Hz，`odom_frame -> t265_pose_frame` |
| D435 | 深度和彩色约 30 Hz，不参与当前 PX4 定位链 |
| PX4 外部视觉融合 | `EKF2_EV_CTRL=0`，尚未启用 |
| T265 机体外参 | 尚未测量并验证 |
| Offboard 丢失回退 | 依赖有效 Position 状态，室内条件尚未闭合 |
| 首次室内运动包线 | 围栏、速度、高度和最长时长尚未收敛 |

当前可以继续进行 SITL、视觉验证和拆桨台架。完成外部视觉融合、外参、故障
回退和有限运动包线验证后，再进入装桨有限飞行。

详细数据见 [PX4 参数审计](docs/evidence/sessions/20260728T213311+0800_px4_parameter_audit/PX4_PARAMETER_AUDIT.md)
和 [机载技术验证](docs/evidence/sessions/20260728T174752+0800_onboard_validation/ONBOARD_VALIDATION.md)。

## DDS 控制链

```text
T265
  -> vision_to_dds
  -> /fmu/in/vehicle_visual_odometry
  -> PX4 EKF2

offboard_cpp
  -> /fmu/in/offboard_control_mode
  -> /fmu/in/trajectory_setpoint
  -> /fmu/in/vehicle_command
  -> PX4
```

同一 PX4 输入话题只能有一个 writer。不要同时启动旧 bringup、demo writer
或第二个 `offboard_control_node` / `vision_to_dds_node`。

## 根清单与更新策略

仓库根目录只保留一个清单：`workspace.lock.repos`。

- `offboard_cpp` 始终跟随 `DDS`
- `vision_to_dds` 始终跟随 `master`
- `px4_bringup` 始终跟随 `DDS`
- 第三方依赖保持精确 SHA
- `communication` 子模块独立跟随 `main`

恢复并更新 DDS 主链与视觉依赖：

```bash
bash Scripts/installation/uav_px4_dds_install.sh \
  --with-optional perception \
  --update \
  --skip-package-check
```

只核对现有 checkout：

```bash
bash Scripts/installation/uav_px4_dds_install.sh \
  --with-optional perception \
  --verify-only \
  --skip-package-check
```

`communication` 默认由同一安装脚本拉取并更新。仅单独维护子模块时可执行：

```bash
git submodule sync -- src/communication
git submodule update --init --remote --checkout src/communication
```

## 最短验证路径

```bash
python3 test/dependency_profiles/validate_dependency_profiles.py \
  --manifest-root .

python3 Scripts/test/verify_h0_production.py \
  --workspace-root .

python3 Scripts/test/verify_package_boundary.py \
  --workspace-root .

python3 -m unittest discover -s test -p 'test_*.py' -v

bash Scripts/test/test_dds_only.sh
```

按顺序推进：

1. [T265 视觉启动](docs/runbooks/T265_VISION_STARTUP.md)
2. [SITL 验收](docs/runbooks/SITL_ACCEPTANCE.md)
3. [拆桨台架](docs/runbooks/BENCH_ACCEPTANCE_DRAFT.md)
4. [有限实机](docs/runbooks/LIMITED_FLIGHT_ACCEPTANCE_DRAFT.md)

## 关键技术文档

- [系统总览](docs/architecture/SYSTEM_OVERVIEW.md)
- [部署拓扑](docs/architecture/DEPLOYMENT_TOPOLOGY.md)
- [节点清单](docs/architecture/NODE_INVENTORY.md)
- [数据流](docs/architecture/DATA_FLOW.md)
- [故障传播](docs/architecture/FAULT_PROPAGATION.md)
- [视觉里程计契约](docs/architecture/VISION_ODOMETRY_CONTRACT.md)
- [依赖 profile](docs/dependencies/SOURCE_PROFILES.md)
- [脚本说明](Scripts/README.md)

## 仓库结构

```text
Scripts/                 构建、依赖恢复和静态验证
config/                  DDS-only package/launch profile
docs/                    架构、运行手册、场景和技术证据
test/                    离线回归测试
tools/                   DDS 控制链与 SITL 验证工具
src/communication        伴随计算机与单片机通信子模块
workspace.lock.repos     唯一根仓库清单
workspace.excluded_packages
                         DDS-only 禁止包列表
```
