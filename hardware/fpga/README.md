# FPGA

本仓库存放高云（Gowin）FPGA 板级工程，以及去板卡特化的通用 RTL 基础模块库与固件基础算法库。

## 目录结构

```text
FPGA/
├── boards/                      # 各平台完整 Gowin 工程（含器件 IP、约束、MMIO 与板级顶层）
│   ├── ACG720_60K_robot/        # ACG720 60K 工程
│   └── BX72_138K_robot/         # BX72 138K 工程（含板级软核固件与构建说明）
├── rtl/                         # 平台无关的可复用 RTL 基础模块库
│   ├── common/                  # clock/（微秒时基、PLL 相位扫描）、uart/、mem/、fifo/
│   ├── ethernet/                # phy/（RGMII/GMII/MDIO）、udp/（CRC/校验和/UDP 收发）
│   ├── sensor/                  # imu/（SPI IMU）、lidar/（N10/D500 串口解析）
│   ├── video/                   # i2c/、ov5640_dvp/、ov5647_csi2/
│   ├── motion/                  # motor/（四轮闭环控制）、hexapod/（六足步态）
│   ├── navigation/              # 雷达降维、前向避障守卫、命令仲裁、里程计数学
│   └── softcore/                # vendor/gorv32_fp/（RV32 软核）
└── fw/                          # 平台无关的裸机定位与局部导航 C 基础库
    ├── boot/                    # 启动汇编、链接脚本与裸机运行时
    ├── common/                  # 基础数学内联原语（nav_math.h）
    ├── localization/            # 平面 EKF 里程计（odometry）
    └── navigation/              # 局部地图、足迹、A* 规划、路径跟踪与安全守卫（参数全部结构体注入）
```

## 说明

- **板级工程（当前验证主线）**：请使用 `boards/BX72_138K_robot/BX72_138K_robot.gprj` 或 `boards/ACG720_60K_robot/ACG720_60K_robot.gprj` 打开具体开发板工程；两个工程均直接引用各自 `boards/*/src/` 下的板级源码。
- **通用基础库（学习与解耦参考）**：[`rtl/README.md`](rtl/README.md) 与 [`fw/README.md`](fw/README.md) 保留去板卡特化的 RTL 模块与裸机算法库，供后续学习与跨平台移植参考（当前未直接挂载到上述 `.gprj`）。
- **板级详细文档**：
  - [ACG720 60K 接线、协议与构建说明](boards/ACG720_60K_robot/README.md)
  - [BX72 GoRV32 固件说明](boards/BX72_138K_robot/src/firmware/README.md)
  - [BX72 传感器说明](boards/BX72_138K_robot/src/sensor/README.md)
