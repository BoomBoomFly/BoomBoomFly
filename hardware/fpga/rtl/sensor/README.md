# FPGA 传感器基础模块

本目录汇总与具体底盘无关的 IMU SPI 采集、激光雷达串口解析与跨域快照封装模块。

## 模块列表

| 子目录 | 文件 | 说明 |
| --- | --- | --- |
| `imu/` | `imu660rc_spi_reader.sv` | LSM6DSV16X / IMU660RC 四线 SPI 采集主控与状态读取 |
| `imu/` | `imu963ra_spi.v` | LSM6DSR / IMU963RA 四线 SPI 配置与六轴采集 |
| `imu/` | `imu_snapshot_cdc.v` | IMU 六轴寄存器跨时钟域快照握手封装 |
| `lidar/` | `n10_receiver.sv` | N10 激光雷达串口接收封装（`n10_receiver`、`n10_uart_rx`） |
| `lidar/` | `n10_packet_parser.sv` | N10 58 字节 16 点数据帧校验与角度/距离输出（输出有效角度 `< 36000`，单位 0.01°） |
| `lidar/` | `d500_uart.v` | 乐动 D500（STL-19P）47 字节串口帧接收与 CRC-8 校验 |

## 使用边界

- 所有输出角度与加速度/角速度均为传感器芯片原始坐标与原始单位，需由上层结合安装外参、零偏与采样时钟不确定度进行标定转换。
- 运动执行前的实时近障保护应配合 `navigation/front_obstacle_guard.sv` 使用。
