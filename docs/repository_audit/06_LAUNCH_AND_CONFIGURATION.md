# 启动链、参数、配置与运行时一致性

## 实际静态启动依赖图

```text
目标架构（尚无获准 orchestration）

PX4 v1.16.2 / future isolated SITL
  -> one Micro XRCE-DDS Agent
  -> /fmu/out/* and /fmu/in/*
  -> offboard_control_node (唯一 control writer，当前 checkout NO-GO)
     -> exactly one mission/authority owner（production 实现缺失）
  -> optional vision_to_dds_node（没有批准的项目 launch）
  -> isolated sensor/serial nodes（均不在 production launch）
  -> visualization/logging
```

`config/profiles/dds_only_launch.yaml:172-195` 只 allowlist
`offboard_control.launch.py` 的一个 node，且 `production_enabled=false`。

## [P1-LAUNCH-001] Forbidden 旧 bringup 仍可被手工启动并组合硬件/MAVROS/控制

- 严重度：P1
- 状态：已确认
- 领域：Launch / MAVLink / Sensor / Serial / Offboard
- 位置：
  - `src/px4_bringup/launch/start_all_2025TI.launch.py:7-48`
  - `src/px4_bringup/launch/include/px4_fly.launch.py:7-54`
  - `src/px4_bringup/launch/include/px4.launch.py:9-48`
  - `src/px4_bringup/launch/serial_and_image_2025TI.launch.py:7-55`
  - `config/profiles/dds_only_packages.yaml:17-30`
- 证据：
  - `start_all` 按 timer 组合 `px4_fly`、serial/CV/YOLO 与旧 offboard executable。
  - `px4_fly` 启动 RealSense、vision_to_mavros、MAVROS。
  - `px4.launch.py` 默认 MAVROS FCU `/dev/ttyACM0:57600`。
  - production profile 明确将 `px4_bringup`、MAVROS/vision_to_mavros/serial/CV 禁止。
  - 旧 `2025_Ti_main_node` 已不在当前 offboard CMake executable 列表中，入口还会部分失败。
- 影响：
  - 人工按旧命令可能打开真实设备、创建第二控制路径或混用 DDS/MAVLink。
  - timer 延迟不是 readiness/lifecycle/failsafe，部分节点失败时组合状态不可控。
- 根因：
  - archive 源码保留用于历史/审计，但文件名和 ROS launch 可执行性仍像当前入口。
- 建议：
  - 保留历史但加强机械隔离/README banner；launch guard 持续禁止 production 引用。
  - 不删除，除非 Git 历史和维护者确认已迁移全部证据。
- 前置条件：
  - 统一入口文档与 archive policy。
- 是否涉及硬件：
  - 需要后续现场验证

## 参数与 namespace 交叉验证

- `offboard_control.launch.py:31-49` 正确把 `use_sim_time` 与安装后的
  `ctrl_param.yaml` 传入 node；但该 YAML 默认 `enable_arm=true`，因此入口本身
  不具备安全默认值。
- `animal_testing.launch.py:20-64` 默认 `use_sim_time=true` 且
  `auto_start_animal_testing=true`，会自动启动 mission publisher；仅允许隔离 SITL。
- `offboard_demo.launch.py:31-75` demo 默认不自动启动，但 control writer 总会启动；
  “demo false”不构成控制安全门。
- `offboard_swarm_control.launch.py:28-72` 创建三个 namespace writer，却没有对应
  PX4 client key、Agent、domain、port、vehicle identity 契约；ADR 明确禁止。
- serial code 默认 `/dev/ttyUSB0`，YAML 为 `/dev/ttyS1`；launch 会加载 YAML，
  直接 `ros2 run` 则使用代码默认，行为不一致。
- vision 参数只从 node 内默认读取，没有受管 launch/profile 传递 frame、clock、
  device identity 或 estimator 参数。

## 启动顺序与生命周期

- Approved target graph 没有 lifecycle manager/readiness handshake。
- archive 使用固定 3/5/8/12/15/25 秒 TimerAction；没有确认 Agent、PX4 topic、
  sensor health 或 writer census。
- 未发现 production respawn/restart policy；archive MAVROS 支持参数化 respawn，
  但它是 forbidden。
- SITL 与实机通过 `use_sim_time` 变量部分区分，未通过强类型 profile/transport
  隔离；手工错误组合仍可能发生。

完整清单与两张图见 `evidence/launch_inventory.txt`。
