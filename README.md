# BoomBoomFly

BoomBoomFly 是面向无人机伴随计算机的 ROS 2 工作区。受管基线为
Ubuntu 20.04、ROS 2 Foxy 与 PX4 v1.16.2。

production 控制链只允许 PX4 uXRCE-DDS；MAVROS、历史串口链和旧 bringup
不是 production fallback。production 当前禁用。

## 权威入口

- 构建：[DDS-only 构建入口](Scripts/build/build_dds_only.sh)
- 测试：[DDS-only 测试入口](Scripts/test/test_dds_only.sh) 与
  [离线测试目录](test/)
- 验证层级与 runbook：[分级验证门](docs/runbooks/VALIDATION_LEVELS.md)、
  [SITL 验收](docs/runbooks/SITL_ACCEPTANCE.md)
- 当前规范：[控制权矩阵](docs/CONTROL_AUTHORITY_MATRIX.md) 与
  [architecture](docs/architecture/)
- 当前验证边界：[分级验证门](docs/runbooks/VALIDATION_LEVELS.md)、
  [控制权矩阵](docs/CONTROL_AUTHORITY_MATRIX.md) 与
  [视觉里程计契约](docs/architecture/VISION_ODOMETRY_CONTRACT.md)
- evidence：[evidence 索引](docs/evidence/index.yaml) 与
  [schema 说明](docs/evidence/SCHEMA.md)
依赖恢复、验证器和脚本目录说明见 [Scripts README](Scripts/README.md)。

## 安全边界

除非另有明确授权：

- 不访问真实飞控、串口、相机、雷达或其他硬件；
- 不启动 Micro XRCE-DDS Agent、MAVROS、Offboard、视觉节点或 hardware launch；
- 不写 PX4 参数、不刷 firmware、不 arm、不切 mode；
- 不发布 `/fmu/in/*`、vehicle command 或 trajectory setpoint；
- 不把 mock、离线测试或历史 evidence 提升为 SITL、台架、飞行或 production 证据。

```text
PRODUCTION: BLOCKED
HARDWARE ACCESS: NOT AUTHORIZED
FIRMWARE FLASH: NOT AUTHORIZED
FLIGHT: NOT AUTHORIZED
```
