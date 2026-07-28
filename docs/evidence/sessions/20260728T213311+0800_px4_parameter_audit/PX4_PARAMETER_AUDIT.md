# PX4 参数快照审计（2026-07-28）

## 1. 结论

本次收到一份 QGroundControl 导出的 PX4 参数快照、一张固件信息截图和
一份飞控 NSH `ver all` 输出。参数与截图按原样保存；终端输出仅对设备唯一
标识 PX4GUID 脱敏。三个材料均计算 SHA-256。

当前状态：`BLOCKED`

参数快照补齐了固件版本、机架类型、System ID 和 uXRCE-DDS 串口配置，
但仍不能支持室内 DDS/Offboard 实机飞行。首要阻塞是
`EKF2_EV_CTRL=0`：PX4 当前没有融合外部视觉位置、速度、高度或航向。

本次工作仅整理用户提供的只读材料，没有连接飞控、写 PX4 参数、刷写固件、
启动 Offboard、解锁或发送 `/fmu/in/*`。

## 2. 原始材料

| 材料 | 仓库路径 | 字节数 | SHA-256 |
|---|---|---:|---|
| QGroundControl 参数快照 | `raw/px4_2026-07-28.params` | 33,686 | `f669480ed8fd3f8066a6ab3132667a4be5a13dce956f7f23139efeff409222ce` |
| 固件信息截图 | `raw/vehicle_firmware_info.png` | 11,546 | `22dc1d3525abd49b645930a165924fd2c496582ecc60f2bb7a54f19df3bf2d04` |
| NSH `ver all`（PX4GUID 脱敏） | `raw/ver_all_redacted.txt` | 526 | `3d81548ea832115d79c790b457d4bbaf3b74fb8600651a46a7617aaee4adbff6` |

参数文件包含 974 个参数名，未发现重复参数名。文件头记录：

- Stack：PX4 Pro
- Vehicle：Quadrotor
- Version：1.16.2
- Git Revision：`54f0455ffc000000`

截图记录：

- System ID：1
- Airframe：Quadrotor X
- Vehicle：Generic Quadcopter
- Firmware：1.16.2
- Custom firmware：0.0.0

现场补充的硬件与 `ver all` 身份：

- 飞控板：Pixhawk 2.4.8
- HW arch：`PX4_FMU_V3`
- HW type/version/revision：`V30` / `0x9000E` / `0x000`
- MCU：STM32F42x rev. 5
- PX4：Release 1.16.2（17826559），branch `stable`
- PX4 Git：`54f0455ffcd755534539a7cf33a09a20bf71d29d`
- OS：NuttX 11.0.0（184549631）
- NuttX Git：`886acbbdb4f061e5c0ce1a76afbcfa7cb7df9849`
- 构建时间：2026-04-22 14:06:56
- 构建 variant：`default`
- 工具链：GNU GCC 9.3.1 20200408

`HW arch: PX4_FMU_V3` 已确认运行固件的 FMUv3 架构，与现场报告的
Pixhawk 2.4.8 一致。它不等同于固件二进制 SHA-256，仍不能单独证明当前
飞控二进制与后续 SITL、台架或重建产物逐字节一致。

## 3. 已补齐的信息

| 项目 | 快照值 | 当前判断 |
|---|---:|---|
| 机架 | `SYS_AUTOSTART=4001`、`CA_AIRFRAME=0` | Generic Quadcopter，多旋翼 |
| HITL | `SYS_HITL=0` | 非 HITL 参数配置 |
| System ID | `MAV_SYS_ID=1` | 已知 |
| DDS 接口 | `UXRCE_DDS_CFG=102` | uXRCE-DDS 配置到 TELEM2 |
| TELEM2 波特率 | `SER_TEL2_BAUD=921600` | 已知 |
| DDS Domain ID | `UXRCE_DDS_DOM_ID=0` | 已知 |
| DDS Client Key | `UXRCE_DDS_KEY=1` | 已知 |
| DDS 时间同步 | `UXRCE_DDS_SYNCT=1` | 启用 |

上述参数只证明保存的配置值，不证明串口接线、Agent 连接、topic 可见性、
消息版本兼容性或运行时数据质量。

## 4. 实机飞行阻塞点

### 4.1 外部视觉没有进入 PX4 EKF

- `EKF2_EV_CTRL=0`
- `EKF2_EV_POS_X/Y/Z=0`
- `EKF2_EV_QMIN=0`

`EKF2_EV_CTRL=0` 表示外部视觉位置、速度、高度和航向融合位均未启用。
即使伴随计算机能读取 T265，当前参数也不能证明 PX4 拥有室内
Position/Offboard 悬停所需的位置估计。

在改动任何参数前，还必须确定 T265 到机体坐标系的平移和旋转外参、
消息坐标系、时间戳来源、更新率以及跟踪质量降级行为。

### 4.2 Offboard 丢失回退依赖有效位置估计

- `COM_OF_LOSS_T=1.0`
- `COM_OBL_RC_ACT=0`

当前配置在 Offboard 丢失约 1 秒后选择 Position 模式。室内 GPS 不可靠且
外部视觉融合关闭时，不能假设 Position 模式可用。必须先用只读状态确认
本地位置有效，再决定适合室内环境的回退动作。

### 4.3 安全相关断路器处于禁用检查/动作的取值

- `CBRK_IO_SAFETY=22027`
- `CBRK_SUPPLY_CHK=894281`
- `CBRK_USB_CHK=197848`
- `CBRK_FLIGHTTERM=121212`

这些值分别涉及 IO Safety、供电有效性检查、USB 连接检查和部分
Flight Termination 行为。已知飞控板为 Pixhawk 2.4.8，但仍必须结合实际
接线、IO 配置和人工急停设计逐项确认；当前快照没有给出这些取值的硬件依据。

### 4.4 室内飞行包线没有被参数限制

- `GF_MAX_HOR_DIST=0`
- `GF_MAX_VER_DIST=0`
- `GF_ACTION=2`
- `MPC_XY_VEL_MAX=12 m/s`
- `MPC_Z_VEL_MAX_UP=3 m/s`
- `MPC_TKO_SPEED=1.5 m/s`
- `MIS_TAKEOFF_ALT=2.5 m`

水平和垂直距离围栏为 0，表示相应距离限制未启用。速度、起飞速度和任务
起飞高度也不能直接作为首次室内飞行的最小运动包线。

### 4.5 人工接管和链路丢失动作尚未闭环

- `RC_MAP_OFFB_SW=6`
- `RC_MAP_KILL_SW=8`
- `RC_MAP_ARM_SW=0`
- `COM_RC_OVERRIDE=1`
- `COM_RC_LOSS_T=0.5`
- `NAV_RCL_ACT=2`
- `COM_RCL_EXCEPT=0`
- `COM_DL_LOSS_T=10`
- `NAV_DLL_ACT=0`

Offboard 和 Kill 已映射到 RC 通道，但 `COM_RC_OVERRIDE=1` 只包含自动模式
摇杆覆盖，不包含 Offboard 覆盖。RC 丢失动作是 Return；地面站链路丢失动作
未启用。Return 在室内的行为依赖有效位置、Home 点和高度，不能默认视为安全。

### 4.6 电池与解锁条件偏宽

- `COM_LOW_BAT_ACT=0`
- `COM_ARM_WO_GPS=1`
- `BAT1_CAPACITY=-1`
- `BAT1_N_CELLS=4`

低电量动作当前仅为警告，GPS 检查失败不会阻止解锁。`BAT1_CAPACITY=-1`
也没有提供可用容量。首次室内运行前需要用实际电池遥测确认电压、电流、
剩余电量和低电量动作，而不能只依赖参数文件。

### 4.7 固件架构已确认，DDS 运行证据仍不完整

- 飞控板为 Pixhawk 2.4.8，运行架构已由 `ver all` 确认为
  `PX4_FMU_V3`，MCU 为 STM32F42x rev. 5。
- 完整 PX4 Git 已确认是
  `54f0455ffcd755534539a7cf33a09a20bf71d29d`，但仍缺少运行中固件
  二进制 SHA-256，不能唯一绑定完整构建产物。
- 参数未证明 `/fmu/out/rc_channels` 已由当前固件发布。
- 参数未证明 uXRCE-DDS Agent 已连接或 topic 数据持续更新。
- 参数未证明 T265 数据已进入 PX4 estimator。

## 5. 实机前技术检查

1. 导出或重建 `PX4_FMU_V3` 固件并记录可复现的二进制 SHA-256。
2. 证明 T265 位姿经正确坐标变换和时间同步进入 PX4，并由 estimator 接受。
3. 只读证明 DDS Agent、关键输入输出 topic、频率、时间戳和消息版本正常。
4. 明确 Offboard 丢失、RC 丢失、定位丢失和低电量的室内动作。
5. 解释或修正四个安全相关断路器，并留下变更前后参数快照。
6. 给出首次室内高度、水平范围、速度、加速度、偏航速率和最长时长。
7. 完成正式 PX4 DDS SITL 和拆桨台架，保存原始日志及哈希。

## 6. 参考

- [PX4 v1.16 参数参考](https://docs.px4.io/v1.16/en/advanced_config/parameter_reference)
- [PX4 v1.16 外部位置估计](https://docs.px4.io/v1.16/en/ros/external_position_estimation)
- [PX4 v1.16 uXRCE-DDS](https://docs.px4.io/v1.16/en/middleware/uxrce_dds)
- [PX4 v1.16 安全配置](https://docs.px4.io/v1.16/en/config/safety)
- [PX4 v1.16 机架参考](https://docs.px4.io/v1.16/en/airframes/airframe_reference)
