# 普通飞行阶段参数、代码、固件、工具链与回滚索引

更新时间：2026-07-29（Asia/Shanghai）。本索引区分“工作区直接校验”和“用户声明但当前路径不可见”；
后者不能用于自动刷写或准入。

| 类别 | 身份/路径 | 当前校验结果 |
|---|---|---|
| 历史完整参数 | `docs/evidence/sessions/20260728T213311+0800_px4_parameter_audit/raw/px4_2026-07-28.params` | 33,686 bytes；SHA-256 `f669480ed8fd3f8066a6ab3132667a4be5a13dce956f7f23139efeff409222ce`；历史值，写参前必须重导出 |
| 历史运行固件身份 | 同 session 的 `raw/ver_all_redacted.txt` | PX4 v1.16.2，FMUv3，PX4 `54f0455ffcd755534539a7cf33a09a20bf71d29d`；不是二进制身份 |
| 修改后 PX4 源码 | `/home/c/px4_ws/external/PX4-Autopilot` | branch `flight/rc-channels-dds-v1.16.2`，HEAD `706b7caa5b157405c65c7847a9d8d0dfffc3defb`，clean；`d863d5d0d0` 添加 DDS RC topic，后续提交修复 FMUv3 编译 |
| 已刷写目标固件 | `/home/c/px4_ws/external/PX4-Autopilot/build/px4_fmu-v3_default/px4_fmu-v3_default.px4` | 1,900,443 bytes；SHA-256 `e67291b15f982bb5028af8d7598e3236884045cd8f2b7ad7a81f75a16cff5fed`；2026-07-29 uploader Erase/Program/Verify/Reboot PASS |
| 同构建 BIN | `/home/c/px4_ws/external/PX4-Autopilot/build/px4_fmu-v3_default/px4_fmu-v3_default.bin` | 2,052,073 bytes；SHA-256 `a280d9999829a5132524b352c69ba107bc3c6bd9140125bb54dd119f35e86065` |
| PX4 工具链 | 当前工作区命令输出 | `arm-none-eabi-gcc 9.2.1 20191025`；CMake `3.16.3`；Ninja `1.11.1.git.kitware.jobserver-1` |
| 用户提供备份 | `docs/px4_fmu-v3_default.px4`（未跟踪、未修改） | 1,900,443 bytes；SHA-256 与目标同为 `e67291b...`; 可重刷同一固件，但不能证明恢复旧行为 |
| 刷写后参数快照 | 临时完整 JSON + G2 evidence 摘要 | 974 参数；完整 JSON SHA-256 `522652317e3ddfd6d386a1b79473533619b0c45a62dd7b0ce1bf1dd5ee1f5617` |
| 根集成构建提交 | `292cdc1717ae57db2f68b695e1c8a66c6d66c16c` | 权威四包 clean build/test 使用的根集成基线；后续根提交仅修复回放器固定数组和防 pycache 污染 |
| `px4_msgs` | `src/px4_msgs` | `392e831c1f659429ca83902e66820d7094591410`，clean/detached |
| `offboard_cpp` | `src/offboard_cpp` | `e24bb3facfcf4126ad7b3d216a768a040758e895`，clean，DDS ahead 1 |
| `vision_to_dds` | `src/vision_to_dds` | `470cf59cf8fbcddd17b12e9d31f084e87f5f2fac`，clean，master ahead 1 |
| `communication` | `src/communication` | `e6d6126acd16050216e5f091e61d58a96ef3ed65`，clean，main ahead 1 |
| 本轮软件 evidence | `docs/evidence/sessions/20260729T162319+0800_vertical_flight_stage` | 四包 build PASS；50 tests 0 failure；Domain 231 回放运行时与 Domain 0 拒绝均有日志/哈希 |
| G2 刷写/实机 evidence | `docs/evidence/sessions/20260729T174904+0800_g2_flash_rc_dds` | 刷写、唯一 Agent、真实 RC publisher/类型/变化/loss PASS；XRCE 数据面约 49–50 秒后冻结，G2 FAIL/BLOCKED |
| G2 UART DMA 诊断 | `docs/evidence/sessions/20260729T183138+0800_g2_uart_dma_diagnostic` | 内核证明 Jetson 低内存时 UART RX DMA descriptor 分配失败；释放语言服务后 120 秒 RC/timesync 对照 PASS；生产内存约束待验收 |
| Agent 内存/DMA 门禁 | `docs/evidence/sessions/20260729T190953+0800_agent_memory_guard` | 根 SHA `133cf05fd49deb55b072bd061b310aaf7f7310e7`；精确 Agent SHA、唯一串口、Domain 0、内存/DMA 水位和开发进程 fail-closed；7 项单测与四包 50 tests PASS；干净重启长稳态 soak 待验收 |

固件已刷写且真实 `/fmu/out/rc_channels` 契约已验证。当前备份与目标逐字节相同，不是旧行为
回滚证据；生产内存门禁不能替代干净重启长稳态验证，G2 仍为 FAIL/BLOCKED。
