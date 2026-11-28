# FPGA RTL 基础模块库

本目录为平台无关的通用 RTL 基础模块库，按功能域划分，不包含具体开发板顶层、引脚/时序约束、器件绑定 IP 核或板卡专用通信协议栈。

> 各板卡完整工程、引脚/时序约束（`.cst`/`.sdc`）、高云 IP 核（`.ipc`/`.vo`/`.mod`、`pll_init.v`）及板级业务顶层保留在 [`../boards/`](../boards/) 中。

## 功能域划分

| 目录 | 功能定位 | 模块清单 |
| --- | --- | --- |
| `common/` | 通用时序、串口、存储与异步缓冲原语 | `clock/us_timebase.sv`（`clock_contract`、`us_phase`、`deadline_age`）、`clock/rx_pll_phase_scan.v`、`uart/`（`uart_rx_core.sv`、`uart_rx.sv`、`uart_tx.sv`、`packet_uart_tx.sv`）、`mem/sync_ram.sv`（`sync_ram`）、`fifo/async_fifo.sv`（`async_fifo`） |
| `ethernet/` | 以太网 PHY 接口与 UDP 协议栈 | `phy/`（`gmii_to_rgmii.v`、`rgmii_to_gmii.v`、`mdio_bit_shift.v`、`phy_reg_config.v`）、`udp/`（`crc32_d8.v`、`ip_checksum.v`、`eth_udp_tx_gmii.v`、`eth_udp_tx_dual_gmii.v`、`eth_udp_rx_gmii.v`） |
| `sensor/` | 传感器采集、包解析与跨域快照 | `imu/`（`imu660rc_spi_reader.sv`、`imu963ra_spi.v`、`imu_snapshot_cdc.v`）、`lidar/`（`n10_receiver.sv`、`n10_packet_parser.sv`、`d500_uart.v`）、[传感器说明](sensor/README.md) |
| `video/` | 相机配置与图像采集 | `i2c/`（`i2c_bit_shift.v`、`i2c_control.v`）、`ov5640_dvp/`（`ov5640_camera_init.v`、`ov5640_init_table_rgb.v`、`DVP_Capture.v`、`camera_line_align.v`）、`ov5647_csi2/`（`ov5647_camera_init.v`、`ov5647_init_table_raw10.v`） |
| `motion/` | 电机闭环与六足步态生成 | `motor/motor_control.sv`（编码器解码、PID/速度闭环与 PWM 驱动）、`hexapod/`（`hexapod_gait.v`、`gait_offsets.hex`） |
| `navigation/` | 硬件避障守卫、雷达降维、命令仲裁与里程计数学 | `lidar_bin_reduce.sv`、`front_obstacle_guard.sv`、`command_arbiter.sv`、`fusion_math.sv` |
| `softcore/` | 第三方 RV32 软核 | `vendor/gorv32_fp/`（`riscv_fp_core.v`、[内核说明](softcore/vendor/gorv32_fp/README.md)） |
