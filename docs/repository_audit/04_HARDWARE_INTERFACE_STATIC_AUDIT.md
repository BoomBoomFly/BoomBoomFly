# 传感器、串口与硬件接口静态审查

本章只做源码/配置检查。没有运行 `lsusb`、设备枚举、串口打开、相机、雷达、
Agent 或任何 hardware launch。

## [P1-SER-001] ROS 串口与 STM32 协议不一致，接收路径存在奇数长度越界

- 严重度：P1
- 状态：已确认
- 领域：Serial / Sensor / Code
- 位置：
  - `src/communication/Serial/serial_driver_ros/src/serial_driver.cpp:35-60,63-104`
  - `src/communication/Serial/serial_driver_ros/include/serial_driver/protocol_defs.hpp:9-19`
  - `src/communication/Serial/Serial_32/src/Serial.c:110-219`
  - `src/communication/Serial/serial_driver_ros/COLCON_IGNORE:1-3`
- 证据：
  - ROS 发送帧为 `0x0F 0xF0 LEN DATA additive_checksum`，无 tail。
  - STM32 parser 要求 `0x0F 0xF0 LEN DATA CRC16_LOW CRC16_HIGH 0xFF`。
  - ROS 接收循环 `j += 2` 并读取 `frame[j+1]`，未拒绝 odd `len`。
  - quarantine 验证器 exit 0，当前 colcon discovery 与 production 引用均为 0。
- 影响：
  - 若人工移除隔离并运行，两端不能可靠互通；奇数长度帧可导致越界读。
  - ROS node 订阅 `/cmd_vel` 后立即写串口，没有 authority/watchdog/interlock。
- 根因：
  - ROS 与 MCU 分别演化为不同帧协议，未共享 machine-readable schema/golden vector。
- 建议：
  - 保持 quarantine；统一 CRC、tail、字节序和最大长度。
  - 在 host 端增加粘包/拆包/奇数长度/CRC/tail/fuzz/ASan 测试。
  - 引入 authority、sequence、timeout、zero-command on loss 和设备身份门。
- 前置条件：
  - 维护者确认串口所驱动的实际执行对象与安全停止语义。
- 是否涉及硬件：
  - 需要后续现场验证

## [P2-HW-001] 设备路径与身份选择依赖不稳定默认值

- 严重度：P2
- 状态：已确认
- 领域：Sensor / Serial / Launch
- 位置：
  - `src/communication/Serial/serial_driver_ros/src/serial_main.cpp:13-25`
  - `src/communication/Serial/serial_driver_ros/config/serial_config.yaml:3-4`
  - `src/px4_bringup/launch/include/px4.launch.py:23-30`
  - `config/profiles/dds_only_launch.yaml:8-13`
  - `docs/architecture/DEPLOYMENT_TOPOLOGY.md:77-79`
- 证据：
  - serial code 默认 `/dev/ttyUSB0:115200`，YAML 又是 `/dev/ttyS1:115200`。
  - archive MAVROS 默认 `/dev/ttyACM0:57600`。
  - 目标 DDS 文档使用 `/dev/ttyTHS0:921600`，并明确当前 runtime owner/参数未验证。
  - RPLIDAR 上游 model launch 普遍使用 `/dev/ttyUSB0`；未见项目级按序列号选择 profile。
- 影响：
  - USB 枚举顺序变化可能绑定错误设备；serial/DDS/MAVLink 可能争用端口。
- 根因：
  - 上游默认、历史配置与目标拓扑并存，缺少项目级 stable identity 层。
- 建议：
  - 使用 `/dev/serial/by-id` 或受管 udev symlink，并绑定 VID:PID+serial。
  - 每个 profile 声明唯一 owner、baud、permissions、reconnect 上限和 stop 行为。
- 前置条件：
  - 现场只读设备清单需单独人工批准；本轮不得探测。
- 是否涉及硬件：
  - 需要后续现场验证

## RealSense

- `librealsense` 与 `realsense-ros` 是 optional perception source，HEAD 与 lock 匹配，
  但工作树有大量 receipt-governed mode drift。
- 当前权威 launch allowlist 不含 RealSense；`px4_bringup/px4_fly.launch.py:8-17`
  的 T265 入口属于 forbidden archive。
- `vision_to_dds` 默认 frame 是 `/camera_odom_frame` 与 `/camera_link`，未绑定
  相机 serial、具体型号、USB topology 或分辨率/带宽 profile。
- 多设备选择、断线重连、USB 带宽和实际 frame rate：**待现场验证**。

## RPLIDAR

- 仅发现上游 `rplidar_ros` 及型号 launch；没有项目级批准 bringup 将其接入
  production graph。
- frame、model baud 和 `/dev/ttyUSB0` 默认值必须由单设备 profile 固定。
- 与串口节点共享 USB serial namespace 的冲突：**待现场验证**。

## STM32

- `Serial_32` 具有 CRC16/MODBUS、长度、tail、buffer overflow 检查和 host parser tests。
- `communication/README.md:76-80` 明确缺完整 CubeMX/HAL/启动文件/链接脚本，真实
  firmware build 与上板均未验证。
- UART 引脚文档自身指出历史注释与常见 STM32F103 映射不一致，必须以原理图/CubeMX 为准。

## ESP8266、网络与 udev

- 权威 production 源码中未找到 ESP8266 集成入口；状态为 **无法确认/未集成**。
- 没有批准的网络控制 endpoint；未探测 IP/端口。
- 上游仓库含 udev 示例，但未发现项目级、按序列号固定且带最小权限的统一 udev policy。
- `dialout`/udev 权限只应在 Phase 3 由人工批准验证，不应由安装脚本自动放宽。
