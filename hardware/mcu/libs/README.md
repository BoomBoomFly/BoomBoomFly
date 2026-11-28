# MCU 通用基础库（`libs/`）

本目录存放与具体 MCU 芯片和 HAL 解耦的纯 C/C++ 基础模块，供 `../boards/` 下各个板级工程复用。

## 目录划分

| 目录 | 定位 | 内容说明 |
| --- | --- | --- |
| `algorithms/` | 通用算法库 | 控制（PID、LADRC、LQR、SMC）、状态估计（2D EKF）与信号滤波（见 [algorithms/README.md](algorithms/README.md)） |
| `protocol/` | 通信协议与校验 | 帧编解码、CRC 校验、心跳包与上下位机指令格式定义 |
| `drivers/` | 外设器件驱动 | IMU、电机/电调、编码器、ToF 等与总线解耦的器件驱动 |
| `utils/` | 嵌入式基础工具 | 环形缓冲区、定点数、通用工具辅助（预留） |

## 约束

- **禁止直接依赖芯片厂商 HAL**：`libs/` 内部不要直接 `#include` 特定芯片的 HAL/SDK 头文件；SPI、I2C、UART、CAN、延时等底层操作应通过结构体或函数指针由板级 `bsp/` 注入。
