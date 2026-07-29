# G2 干净 boot RC/DDS/Agent 长稳态证据

Session：`20260729T195311+0800_g2_clean_boot_soak`

日期：2026-07-29（Asia/Shanghai）

范围：用户明确批准的 G2 拆桨只读 RC/timesync soak。未发布任何 `/fmu/in/*`，未写 PX4
参数，未 Arm、未发送 VehicleCommand、未启动电机，也未进入 G3–G5。

## 干净 boot 身份

首次检查发现旧 boot 仍包含 18:11–18:32 的 UART RX DMA descriptor 故障，因此在启动 Agent
前 fail-closed。用户实际重启后重新确认：

```text
boot_started=2026-07-29 19:20:20
boot_id=3268e759-5043-48a8-92ae-44afb959ae95
kernel_error_matches_before_soak=0
```

本次 boot 与旧 boot 的 ID 不同。启动前无 Agent、offboard、vision、mission_bridge 或开发语言
服务进程，`/dev/ttyTHS0` 无 owner，内存和 DMA 水位通过 guard。

## Agent 身份与构建

重启清除了先前 `/tmp` Agent。锁定源码为 clean
`57d086216d01ec43121845d385894a25987f8a2c`。默认 superbuild 暴露两个可复现性问题：上游已删除
移动引用 `2.12.x`；固定到 Fast-DDS `v2.12.2` 后又需要 CMake 3.20，而现场为 3.16.3。
没有降低依赖的最低 CMake、升级系统或使用移动分支。

最终使用 Agent 自带的受支持系统依赖模式构建：

```text
UAGENT_SUPERBUILD=OFF
UAGENT_USE_SYSTEM_FASTDDS=ON
UAGENT_USE_SYSTEM_FASTCDR=ON
UAGENT_USE_SYSTEM_LOGGER=ON
UAGENT_P2P_PROFILE=OFF
UAGENT_BUILD_TESTS=OFF
```

依赖为 ROS Foxy FastRTPS `2.1.4`、FastCDR `1.0.13`、spdlog `1.5.0`；GCC `9.4.0`、
CMake `3.16.3`。生成 Agent SHA-256：

`4cbc5038cb74391a8ecec3ed6cd94e588530cae937b5498d6796bf2c68433995`

guard 的实际启动 preflight 为 PASS：显式 Domain 0、921600 baud、唯一串口、精确 Agent SHA、
MemAvailable 2,364,844 KiB、DMA free-above-high 461,000 KiB，且无被禁止开发进程。PX4 client
session 建立后，RC/timesync publisher 均恰好为 1；offboard control mode、trajectory setpoint、
vehicle command、visual odometry 的 ROS publisher 均为 0。

## 620 秒结果

只读节点订阅 `/fmu/out/rc_channels` 和 `/fmu/out/timesync_status`，每 5 秒检查 ROS 图和水位：

```text
duration=620.011 s
RC:       27507 samples, 44.363891 Hz, max gap 0.057031 s
timesync:   614 samples,  0.989646 Hz, max gap 1.032912 s
RC channel_count={18}
RC/timesync nonincreasing timestamps=0/0
graph samples=125
input writer violations=0
output publisher-count violations=0
minimum MemAvailable=2266704 KiB
minimum DMA free-above-high=271228 KiB
status=PASS
```

本窗口遥控保持在线，因此 `signal_lost=false`；之前的刷写/RC session 已单独验证
`true → false → true` 的真实丢失/恢复语义。最低 DMA headroom 仅比 256 MiB 门限高约 8.8 MiB，
虽然本次 PASS，后续生产运行仍必须保留 guard 和禁用开发语言服务。

## 内核与释放状态

soak 结束后，本次 boot 中以下内核匹配总数为 0：

- `page allocation failure`
- `tegra_uart_start_rx_dma`
- `serial-tegra ... Not able to get desc for Rx`

最终再次确认 RC/timesync publisher 各 1，四个关键 `/fmu/in/*` publisher 各 0。随后以 Ctrl-C
停止 Agent；Agent、监测器和控制节点均为 0，`/dev/ttyTHS0` 无 owner。运行时 bundle 已保存，
其 SHA-256 为 `5294b364f5574fa4a985e024bea8e4aac107fddf55d4942a17868930798e2d55`。

## 准入结论

G2 **PASS**。该结论只覆盖指定固件下的真实 RC/DDS/唯一 Agent、内存/DMA 门禁和干净 boot
长稳态连续性，不授权 G3 视觉/EKF、任何 `/fmu/in/*` writer、参数写入、Offboard、Arm、Land、
Disarm、Kill 或电机动作。

G3、G4 未执行，G5 仍禁止，因此整体仍为 **NO-GO / 不允许装桨飞行**。
