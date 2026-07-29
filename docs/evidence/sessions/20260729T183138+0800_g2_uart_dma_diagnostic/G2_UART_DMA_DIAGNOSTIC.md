# G2 Jetson UART RX DMA 冻结诊断

时间：2026-07-29（Asia/Shanghai）
范围：用户明确批准的拆桨 G2 只读诊断。未写 PX4 参数、未再次刷写、未发布 `/fmu/in/*`、
未 Arm、未启动电机，也未进入 G3–G5。

## 结论

此前约 49–50 秒的 XRCE 数据冻结由 Jetson 内存压力下的 UART RX DMA descriptor 分配失败
直接触发，不是 `rc_channels` 类型、publisher 数量、RC 接收机或 ROS QoS 故障。

内核在两次冻结时均记录：

```text
page allocation failure: order:0, mode:0x800(GFP_NOWAIT)
tegra_dma_prep_slave_sg
tegra_uart_start_rx_dma
serial-tegra 3100000.serial: Not able to get desc for Rx
```

`3100000.serial` 对应 `/dev/ttyTHS0`。错误时间为 18:26:05 和 18:32:30，与 XRCE 的 RC 和
timesync 同时停止一致。两次均是 `kmalloc-256` 无空闲对象：

- 18:26:05：DMA free 50,100 kB，低于 min 78,060 kB；
- 18:32:30：DMA free 65,544 kB，低于 min 78,060 kB。

## 内存压力来源

故障状态下机器只有 3.2 GiB RAM：

```text
used=2.7 GiB
free=79 MiB
available=368 MiB
swap_used=2.3 GiB
```

主要可回收开发进程为 VS Code Pylance、cpptools 和 extension host。Pylance 首次约 443 MiB，
被 extension host 自动重启后增长到约 839 MiB；cpptools 约 295 MiB。仅终止语言服务会被
自动拉起，因此对照测试中临时 `SIGSTOP` extension host，并终止其 Pylance/cpptools 子进程。
这是可逆的测试操作；测试后已执行 `SIGCONT` 恢复 extension host。

对照前内存达到：

```text
free=965 MiB
available=1.3 GiB
```

## 120 秒对照结果

在唯一 Agent、`/dev/ttyTHS0` 921600 baud、Domain 0 且无 offboard/vision/mission_bridge 的
条件下连续只读监测 120 秒：

```text
rc_count=5332
timesync_count=119
rc_max_gap=0.054270 s
timesync_max_gap=1.028537 s
channel_count=18
rssi=41
signal_lost=false（本窗口遥控保持在线）
```

测试期间新增 `page allocation failure` 为 0，新增
`serial-tegra ... Not able to get desc for Rx` 为 0。该对照跨过此前约 50 秒故障点并稳定达到
120 秒，支持“低 DMA 内存导致 UART RX 停止”的根因判断。

## USB/NSH 结果

两次使用 PX4 `Tools/mavlink_shell.py /dev/ttyACM0`，分别在高内存压力和释放内存后执行，均未
收到 MAVLink heartbeat，因此未取得 `uxrce_dds_client status`。USB 设备仍枚举为
`26ac:0011 / PX4 FMU v2.x`。没有为获取 shell 而修改 MAVLink 参数或发送飞行命令。

## 当前准入判断

G2 保持 **FAIL/BLOCKED**。真实 RC 契约和低压力下 120 秒 DDS 连续性已经通过，但开发环境恢复
后 Pylance/extension host 可再次吃掉 DMA zone 余量。必须先建立可复现的生产运行约束：飞行
窗口禁止运行这些开发语言服务，并在启动 Agent 前执行内存水位检查。随后需要一次干净 Jetson
启动下的较长拆桨 soak 复测，期间内核 UART/DMA 错误必须为 0。

诊断结束后 Agent、USB shell、offboard、vision、mission_bridge 均为 0；`/dev/ttyTHS0` 和
`/dev/ttyACM0` 均无 owner。
