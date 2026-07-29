# 普通飞行阶段参数、代码、固件、工具链与回滚索引

更新时间：2026-07-29（Asia/Shanghai）。本索引区分“工作区直接校验”和“用户声明但当前路径不可见”；
后者不能用于自动刷写或准入。

| 类别 | 身份/路径 | 当前校验结果 |
|---|---|---|
| 历史完整参数 | `docs/evidence/sessions/20260728T213311+0800_px4_parameter_audit/raw/px4_2026-07-28.params` | 33,686 bytes；SHA-256 `f669480ed8fd3f8066a6ab3132667a4be5a13dce956f7f23139efeff409222ce`；历史值，写参前必须重导出 |
| 历史运行固件身份 | 同 session 的 `raw/ver_all_redacted.txt` | PX4 v1.16.2，FMUv3，PX4 `54f0455ffcd755534539a7cf33a09a20bf71d29d`；不是二进制身份 |
| 修改后 PX4 源码 | `/home/c/px4_ws/external/PX4-Autopilot` | branch `flight/rc-channels-dds-v1.16.2`，HEAD `706b7caa5b157405c65c7847a9d8d0dfffc3defb`，clean；`d863d5d0d0` 添加 DDS RC topic，后续提交修复 FMUv3 编译 |
| 待授权目标固件 | `/home/c/px4_ws/external/PX4-Autopilot/build/px4_fmu-v3_default/px4_fmu-v3_default.px4` | 1,900,443 bytes；SHA-256 `e67291b15f982bb5028af8d7598e3236884045cd8f2b7ad7a81f75a16cff5fed`；**未刷写** |
| 同构建 BIN | `/home/c/px4_ws/external/PX4-Autopilot/build/px4_fmu-v3_default/px4_fmu-v3_default.bin` | 2,052,073 bytes；SHA-256 `a280d9999829a5132524b352c69ba107bc3c6bd9140125bb54dd119f35e86065` |
| PX4 工具链 | 当前工作区命令输出 | `arm-none-eabi-gcc 9.2.1 20191025`；CMake `3.16.3`；Ninja `1.11.1.git.kitware.jobserver-1` |
| 原固件回滚产物 | 用户声明已保存并校验；当前工作区未发现路径 | **外部证据待绑定**。刷写批准前必须给出可读路径、大小和 SHA-256，并再次校验；不得以目标固件或历史截图代替 |
| 根集成构建提交 | `292cdc1717ae57db2f68b695e1c8a66c6d66c16c` | 权威四包 clean build/test 使用的根集成基线；后续根提交仅修复回放器固定数组和防 pycache 污染 |
| `px4_msgs` | `src/px4_msgs` | `392e831c1f659429ca83902e66820d7094591410`，clean/detached |
| `offboard_cpp` | `src/offboard_cpp` | `e24bb3facfcf4126ad7b3d216a768a040758e895`，clean，DDS ahead 1 |
| `vision_to_dds` | `src/vision_to_dds` | `470cf59cf8fbcddd17b12e9d31f084e87f5f2fac`，clean，master ahead 1 |
| `communication` | `src/communication` | `e6d6126acd16050216e5f091e61d58a96ef3ed65`，clean，main ahead 1 |
| 本轮软件 evidence | `docs/evidence/sessions/20260729T162319+0800_vertical_flight_stage` | 四包 build PASS；50 tests 0 failure；Domain 231 回放运行时与 Domain 0 拒绝均有日志/哈希 |

本索引不表示固件已刷写，也不表示 `/fmu/out/rc_channels` 已在实机验证。目标固件和原固件回滚
产物必须同时可读且哈希匹配，才可请求 G2 的当次拆桨刷写批准。
