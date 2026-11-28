# MCU

本目录存放下位机 MCU 固件工程与平台无关通用库，采用 **`boards/`（板级工程）与 `libs/`（芯片无关通用库）分离** 的结构，与 `hardware/fpga/` 保持一致的组织方式。

## 目录结构

```text
hardware/mcu/
├── .gitignore          # 排除 MCU 编译产物与 IDE 临时文件
├── README.md
├── boards/             # 具体板级完整工程（按 <芯片或板卡>_<用途>/ 划分，可独立编译烧录）
└── libs/               # 芯片无关的纯 C/C++ 模块库（不直接包含厂商 HAL 头文件）
    ├── algorithms/     # 纯算法库：control/{pid,ladrc,lqr,smc}/、estimation/ekf_2d/、filter/、examples/
    ├── protocol/       # 通信帧编解码、CRC 与上下位机指令格式
    ├── drivers/        # 通过总线接口注入的外设器件驱动
    └── utils/          # 环形缓冲区等嵌入式通用工具
```

详细规范见：
- [板级工程规范](boards/README.md)
- [通用基础库规范](libs/README.md)
- [算法库说明](libs/algorithms/README.md)
