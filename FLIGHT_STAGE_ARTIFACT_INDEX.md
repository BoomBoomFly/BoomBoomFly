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
| 本轮四仓代码 | `workspace.lock.repos` 与本轮 evidence session | 以本轮完成后的精确 SHA、dirty 状态和构建日志为准；禁止移动分支进入 production receipt |

本索引不表示固件已刷写，也不表示 `/fmu/out/rc_channels` 已在实机验证。目标固件和原固件回滚
产物必须同时可读且哈希匹配，才可请求 G2 的当次拆桨刷写批准。

