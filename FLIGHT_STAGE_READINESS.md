# 普通垂直飞行阶段准入

更新时间：2026-07-29（Asia/Shanghai）  
范围：T265 定位下的 0.5 m 垂直起飞、定高 3 秒、垂直下降、PX4 Land、落地确认和 Disarm。  
当前总判定：**NO-GO / 不允许装桨飞行**。

## 受控闭环

外层安全/指令事务与任务状态组合后的完整序列是：

`WAIT_START → PRESTREAM → OFFBOARD_ACK → ARM_ACK → TAKEOFF → HOVER_3S → HOME_DESCEND → PX4_LAND_ACK → LAND_CONFIRMED → DISARM_ACK → COMPLETE`

普通垂直任务固定编号为 `3`。`/mission/start` 类型固定为
`std_msgs/msg/UInt32`：`0` 无效、`1` 赛题任务 1、`2` 赛题任务 2、`3` 普通垂直测试。
启动事件只在当前任务、当前 session、新 seq/freshness 条件下消费一次；运行中或重复 START
不得重启或切换任务。

## 生产边界

- 权威构建只包含 `px4_msgs`、`offboard_cpp`、`vision_to_dds`、`mission_bridge`。
- 测试和回放固定 `ROS_DOMAIN_ID=231`；回放器明确拒绝 Domain 0。
- `mission_bridge` 不写 `/fmu/in/*`，不生成 RC；生产 RC 只允许真实
  `/fmu/out/rc_channels`。
- 视觉默认关闭；只有 production 和 vision 两个显式确认、实测外参有效时才允许创建视觉 writer。
- D435、精确降落、动态小车、投放和完整地面站 UI 均不在本阶段。

## 分阶段门

| 门 | 当前状态 | 进入下一门的客观条件 |
|---|---|---|
| G0 源码与构建 | **PASS（软件证据）** | 精确 SHA；四包 clean build；50 tests 全 PASS；launch、单 writer、无生产 mock 门禁 PASS |
| G1 SITL/隔离回放 | **PASS（Domain 231 软件证据）** | 60 秒历史频率无误锁；VERTICAL_TEST、ACK/超时/kill/断流/Land/Disarm 场景 PASS；回放器运行时 PASS |
| G2 拆桨 H1 | **FAIL/BLOCKED（根因已定位、门禁已补）** | 固件、真实 RC 和低压力 120 秒 DDS 对照 PASS；冻结由 Jetson 低内存导致 UART RX DMA descriptor 分配失败。生产 Agent 门禁现要求精确 SHA、唯一串口、Domain 0、MemAvailable≥1024 MiB、DMA headroom≥256 MiB 且无 VS Code/Pylance/cpptools；干净启动 soak 尚未验收 |
| G3 拆桨视觉/EKF | **BLOCKED / 未执行** | G2 PASS、实测外参 PASS；先位置分量，再逐步速度和航向，并保存 estimator 接受证据 |
| G4 拆桨失效测试 | **BLOCKED / 未执行** | G3 PASS；逐项取得授权并以 PX4 实际 mode/failsafe/Land 结果验收 |
| G5 装桨首次悬停 | **PROHIBITED / 本任务绝不执行** | 仅 G0–G4 全 PASS 后重新 go/no-go，并取得当次装桨、Arm、0.5 m 悬停明确授权 |

软件测试 PASS 不能替代刷写后 RC、T265/EKF 或拆桨失效的实机证据，也不能表述为“可以飞行”。
G0/G1 原始输出见
[`docs/evidence/sessions/20260729T162319+0800_vertical_flight_stage`](docs/evidence/sessions/20260729T162319+0800_vertical_flight_stage)。
G2 刷写和失败诊断证据见
[`docs/evidence/sessions/20260729T174904+0800_g2_flash_rc_dds`](docs/evidence/sessions/20260729T174904+0800_g2_flash_rc_dds)。
Jetson UART RX DMA 根因和 120 秒内存对照见
[`docs/evidence/sessions/20260729T183138+0800_g2_uart_dma_diagnostic`](docs/evidence/sessions/20260729T183138+0800_g2_uart_dma_diagnostic)。

## 参数纪律

本阶段未授权写 PX4 参数。任何候选修改前必须重新导出完整参数并计算 SHA-256；记录旧值、
新值、单项理由、验证方法和回滚值；一次只改一个风险组；写后重新导出并 diff。首次测试包线
为 0.5 m、上升不超过 0.3 m/s、下降不超过 0.2 m/s。无测距仪时不得假设 range aid 可用，
circuit breaker 必须逐项确认。

关联操作卡：

- [PROPS_OFF_FLIGHT_STAGE_TEST.md](PROPS_OFF_FLIGHT_STAGE_TEST.md)
- [FIRST_HOVER_TEST_CARD.md](FIRST_HOVER_TEST_CARD.md)
- [FLIGHT_STAGE_ARTIFACT_INDEX.md](FLIGHT_STAGE_ARTIFACT_INDEX.md)
