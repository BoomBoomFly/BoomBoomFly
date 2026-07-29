# 普通飞行阶段参数、代码、固件、工具链与回滚索引

更新时间：2026-07-29（Asia/Shanghai）。本索引区分“工作区直接校验”和“用户声明但当前路径不可见”；
后者不能用于自动刷写或准入。

| 类别 | 身份/路径 | 当前校验结果 |
|---|---|---|
| 历史完整参数 | `docs/evidence/sessions/20260728T213311+0800_px4_parameter_audit/raw/px4_2026-07-28.params` | 33,686 bytes；SHA-256 `f669480ed8fd3f8066a6ab3132667a4be5a13dce956f7f23139efeff409222ce`；历史值，写参前必须重导出 |
| 历史运行固件身份 | 同 session 的 `raw/ver_all_redacted.txt` | PX4 v1.16.2，FMUv3，PX4 `54f0455ffcd755534539a7cf33a09a20bf71d29d`；不是二进制身份 |
| 修改后 PX4 源码 | `/home/c/px4_ws/external/PX4-Autopilot` | branch `flight/rc-channels-dds-v1.16.2`，HEAD `a8f2dbdfff4792c92f576060ab947f8e588d6f8b`，clean；增加真实 RC 和 EV position/height aid-source DDS 输出 |
| 已刷写目标固件 | `/home/c/px4_ws/external/PX4-Autopilot/build/px4_fmu-v3_default/px4_fmu-v3_default.px4` | 1,901,211 bytes；SHA-256 `fa0fafe9ff25ec503498124631b2880c0255f02cd64394555fcf077a556a725b`；2026-07-29 uploader Erase/Program/Verify/Reboot PASS |
| 同构建 BIN | `/home/c/px4_ws/external/PX4-Autopilot/build/px4_fmu-v3_default/px4_fmu-v3_default.bin` | 2,053,049 bytes；SHA-256 `1a8ac7c019ab781eb334417be1c4b839334e5b4e1f9fa896120ca7e77ccb83ab` |
| PX4 工具链 | 当前工作区命令输出 | `arm-none-eabi-gcc 9.2.1 20191025`；CMake `3.16.3`；Ninja `1.11.1.git.kitware.jobserver-1` |
| 用户提供备份 | `docs/px4_fmu-v3_default.px4`（未跟踪、未修改） | 1,900,443 bytes；SHA-256 `e67291b...`；可回刷上一个已验证的 RC-only DDS 固件 |
| 刷写后参数快照 | 临时完整 JSON + G2 evidence 摘要 | 974 参数；SHA-256 `522652317...`; aid-source 固件刷写后 USB 参数列表未稳定重导出，未声称完成 diff |
| 根集成构建提交 | `292cdc1717ae57db2f68b695e1c8a66c6d66c16c` | 权威四包 clean build/test 使用的根集成基线；后续根提交仅修复回放器固定数组和防 pycache 污染 |
| `px4_msgs` | `src/px4_msgs` | `392e831c1f659429ca83902e66820d7094591410`，clean/detached |
| `offboard_cpp` | `src/offboard_cpp` | `e24bb3facfcf4126ad7b3d216a768a040758e895`，clean，DDS ahead 1 |
| `vision_to_dds` | `src/vision_to_dds` | `470cf59cf8fbcddd17b12e9d31f084e87f5f2fac`，clean，master ahead 1 |
| `communication` | `src/communication` | `e6d6126acd16050216e5f091e61d58a96ef3ed65`，clean，main ahead 1 |
| 本轮软件 evidence | `docs/evidence/sessions/20260729T162319+0800_vertical_flight_stage` | 四包 build PASS；50 tests 0 failure；Domain 231 回放运行时与 Domain 0 拒绝均有日志/哈希 |
| G2 刷写/实机 evidence | `docs/evidence/sessions/20260729T174904+0800_g2_flash_rc_dds` | 刷写、唯一 Agent、真实 RC publisher/类型/变化/loss PASS；XRCE 数据面约 49–50 秒后冻结，G2 FAIL/BLOCKED |
| G2 UART DMA 诊断 | `docs/evidence/sessions/20260729T183138+0800_g2_uart_dma_diagnostic` | 内核证明 Jetson 低内存时 UART RX DMA descriptor 分配失败；释放语言服务后 120 秒 RC/timesync 对照 PASS；生产内存约束待验收 |
| Agent 内存/DMA 门禁 | `docs/evidence/sessions/20260729T190953+0800_agent_memory_guard` | 根 SHA `133cf05fd49deb55b072bd061b310aaf7f7310e7`；精确 Agent SHA、唯一串口、Domain 0、内存/DMA 水位和开发进程 fail-closed；7 项单测与四包 50 tests PASS |
| G2 干净 boot soak | `docs/evidence/sessions/20260729T195311+0800_g2_clean_boot_soak` | Boot ID `3268e759-5043-48a8-92ae-44afb959ae95`；guard 启动 Agent SHA `4cbc5038...433995`；620.011 秒 RC/timesync、零输入 writer、内核错误 0、最终串口释放 PASS；保存运行 bundle 和构建依赖身份 |
| G3 T265 预检 | `docs/evidence/sessions/20260729T200247+0800_g3_t265_preflight` | T265 原始与 ROS odometry 约 200 Hz、严格 `odom_frame → t265_pose_frame`、断流质量 0/恢复 epoch 递增、Domain 0 零输入 writer；该 session 当时缺外参，后续已补齐 |
| T265 实测外参 | `/home/c/px4_ws/measured_extrinsics/t265_to_base_link.measured.yaml` | Pixhawk IMU 中心为 `base_link`；`t265_pose_frame → base_link` 平移 `[-0.082,-0.015,0.108] m`、单位四元数；SHA-256 `42e48f773f771af91b2b3106b9a48ede6cc60fc29b0267157ae4c2f684f54295` |
| G3 真实位置融合 | `docs/evidence/sessions/20260729T210816+0800_g3_t265_position_fusion` | Domain 0 唯一视觉 writer、位置/高度融合、零速度/航向融合、零拒绝、T265 断流退出、epoch 递增和显式 reset 恢复 PASS；该 session 当时缺 aid-source，已由下一行补证解除 |
| G3 aid-source 补证 | `docs/evidence/sessions/20260729T212815+0800_g3_aid_source_firmware` | 新固件刷写；EV position/height innovation、variance、test ratio、time_last_fuse；两段 30 秒融合、断流、epoch 防重放、显式复位恢复和最终 writer 释放全部 PASS |

真实 `/fmu/out/rc_channels`、生产内存门禁、干净 boot soak 和 G3 视觉/EKF 强制证据均通过，
G0–G3 PASS。用户备份可回刷上一个 RC-only 固件；G4 未执行，整体继续 NO-GO，禁止装桨
飞行。
