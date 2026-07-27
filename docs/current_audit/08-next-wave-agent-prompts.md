# 下一波 Agent 可直接使用的任务提示

Audit date: 2026-07-27T22:15:13+08:00  
Hostname: orinnano  
User: c  
Workspace: `/home/c/px4_ws`  
Repository: `/home/c/px4_ws/BoomBoomFly`  
Branch: `master`  
HEAD: `0ed9d148bfbfd22253142172bbfe93c51106fdfa`  
PX4 target version: v1.16.2  
ROS distribution: Foxy  
Hardware accessed: NO  
SITL run: NO  
Files modified outside docs/current_audit: YES — colcon logs; nested Git index metadata refreshed by status; root FETCH_HEAD changed concurrently/unattributed; no source/config/existing-doc change

以下 prompts 必须由未来协调 Agent 赋予互斥写入路径。默认禁止硬件、正式 SITL、
install、flash、参数写入、arm/mode/takeoff、Git destructive 操作和 push。

## Prompt W4A-01 — Offboard live safety integration

```text
你负责 W4A-01，唯一写入范围为 src/offboard_cpp 的 live node/FSM/gate adapter
与对应 tests。先读取 docs/current_audit/04、05、07 和 Wave3B 22/authority freeze。
将所有 /fmu/in/trajectory_setpoint、offboard_control_mode、vehicle_command 发布收敛
到一个 fail-closed gate：authority identity/lease/epoch、VehicleCommandAck correlation、
fresh VehicleStatus、monotonic clock、restart reset、PRESTREAM>=1s 且>=20样本。
ready 前与任何 reject/restart/duplicate writer 下 publish count 必须为0。不得修改
PX4 source、serial、vision、门禁阈值；不得启动 ROS/PX4/Agent/SITL/硬件。先写失败
测试，再实现。输出精确 diff、测试命令、结果、残余风险；不要宣称 mock 是 SITL。
```

## Prompt W4A-02 — RC/kill/auto-arm closure

```text
你负责 W4A-02，唯一写入范围为 Offboard RC/input/FSM/config/tests；与 W4A-01
共享文件必须由协调者串行。移除 production TEXT_RC，production 默认 auto-arm=false，
fresh physical RC 和独立 kill latch 为 arm/mode 硬门；RC never-received/stale/lost、
mock injection、kill bounce、restart/recovery 全部要求 ARM/MODE publish=0，恢复不自动
ACTIVE。不得决定危险故障的 Land/Position 行为，需 Safety Reviewer 批准。禁止硬件、
PX4参数、SITL和降低标准。输出测试矩阵与验收结果。
```

## Prompt W4A-03 — Serial source decision and quarantine

```text
你负责 W4A-03。先只读保全 root 的 deleted src/serial_driver_ros 和 untracked dirty
src/communication；不得删除、移动、clean、reset、stage 或覆盖它们。解析
workspace.repos、dds_only_packages profile、实际两个 Git identity 与 /cmd_vel→serial
执行路径。先提交 maintainer decision proposal：唯一 canonical origin/SHA/path/package
及旧路径 disposition。未获书面决定不得改 source，只能增强 fail-closed validator/tests。
目标是未知 serial 在 production discovery/launch 中为0，package boundary原因准确。
若获批实现协议，必须统一 ROS/STM32 CRC/tail/length schema并做golden/odd/partial/ASan/
disconnect tests；只能使用模拟backend，禁止打开/dev。
```

## Prompt W4A-04 — PX4 provenance and RC endpoint

```text
你负责 W4A-04，默认只读 external/PX4-Autopilot。验证
v1.16.2@54f0455f、35 recursive submodules、px4_msgs@392e831c 的226/226消息一致性、
dds_topics.yaml和generator身份。由PX4/Release maintainer批准后，创建非模板的
source/submodule/toolchain/board lock proposal。单独评审 /fmu/out/rc_channels 最小
profile；baseline差异必须精确且可逆。禁止修改当前PX4 checkout、联网自动更新、
build/flash/参数/hardware/SITL。若ARM/toolchain/board缺失，诚实BLOCKED。
```

## Prompt W4A-05 — Vision fail-closed health

```text
你负责 W4A-05，唯一写入 src/vision_to_dds、perception schema/profile和纯软件tests。
建立明确 ENU/NED/FLU/FRD/frame契约、时间域/epoch/reset/quality/max-age、finite/
covariance/device health 门。任何 frame mismatch、zero/backward/future/freeze、
dropout、NaN/Inf 均不得向PX4发布。precision landing保持baseline disabled并作为
独立能力。不得启动RealSense、读取当前PX4参数或运行SITL。以轴向、90/180度、
四元数/covariance金样和publisher suppression测试验收。
```

## Prompt W4B — Reproducible H1 build

```text
你负责 Wave4B，仅当协调者确认 H0 不为 NO-GO 后开始。先对齐 approved root locks、
Offboard final、PX4/serial disposition，修复 production 三包直接依赖与 package
boundary；不得扩大allowlist或引入MAVROS/serial/archive包。所有colcon输出必须在
/tmp唯一目录，先清理继承AMENT/CMAKE环境并source Foxy。运行
Scripts/test/test_dds_only.sh --output-root /tmp/<unique>，保存root/nested HEAD、
命令、exit、logs、artifact hashes。禁止ROS launch、设备、SITL。任何前置失败即
停止，H1不得借历史build提升。
```

## Prompt W4C — Complete unit/fault suite

```text
你负责 Wave4C，在H1 PASS后建立完整H2证据。覆盖live FSM/transport/publisher、
ACK所有结果、owner/lease/duplicate writer、RC/kill、DDS/PX4/Agent restart、
odom/status/battery/setpoint loss、clock jump、NaN/Inf；另按已批准来源覆盖serial
CRC/odd/partial/disconnect和vision frame/time/dropout。必须使用fake clock/transport，
不得把mock当PX4/SITL证据。执行所有相关Python、gtest、standalone和negative suites，
任何未执行项使H2非GO。
```

## Prompt W4D/W4E — Node integration and SITL readiness

```text
仅在H0/H1/H2 GO后执行。W4D使用隔离DDS domain和fake transport做无设备ROS node
integration，静态guard必须证明不启动Agent/MAVROS/serial/camera/lidar且不连接真实
/fmu/in graph；bounded timeout和cleanup必需。H3证据只说明node integration。
W4E只准备formal SITL proposal：锁定PX4 source/toolchain/profile/domain/ports，映射
37个scenario并确保真实PX4 source identity。未获单独人工授权不得启动SITL/Agent。
synthetic结果不得升级为formal SITL。
```

## 协调规则

- Offboard live files：W4A-01 与 W4A-02 串行；
- serial、PX4、vision 可并行，各自单一 writer；
- manifests/profile/CI 由 Wave4B 单一 owner，等待 W4A 决策；
- 每条线只返回 commit/diff/test evidence，不自行 merge/push；
- 任一 P0 或来源不明状态出现，H0 保持 NO-GO。
