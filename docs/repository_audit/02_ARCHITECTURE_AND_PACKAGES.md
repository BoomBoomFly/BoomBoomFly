# 目录架构、包清单与构建系统

## 架构结论

生产边界由 `config/profiles/dds_only_packages.yaml:12-16` 明确收敛到：

```text
px4_msgs
  <- offboard_cpp
  <- vision_to_dds
```

线程 B 的 `colcon graph` 只读枚举未发现这三个包之间的循环。主线程运行
`verify_package_boundary.py`，在 75 个可发现包中权威发现 3 个 production 包，
exit 0。完整 package/依赖清单见 evidence。

这不等于构建通过：本轮未 build，且当前 production checkout 与 lock 不一致。

## [P2-BUILD-001] vision_to_dds 未声明直接使用的 builtin_interfaces

- 严重度：P2
- 状态：已确认
- 领域：Build / Code
- 位置：
  - `src/vision_to_dds/include/vision_to_dds/vision_to_dds.hpp:7,30`
  - `src/vision_to_dds/src/vision_to_dds.cpp:18-21`
  - `src/vision_to_dds/package.xml:10-18`
  - `src/vision_to_dds/CMakeLists.txt:18-39`
- 证据：
  - 头文件/API 直接使用 `builtin_interfaces::msg::Time`。
  - `package.xml` 没有 `<depend>builtin_interfaces</depend>`。
  - CMake 没有 `find_package(builtin_interfaces REQUIRED)` 或 target dependency。
- 影响：
  - 在被上游传递依赖“碰巧”覆盖的环境可编译，但隔离构建/依赖解析不稳定。
- 根因：
  - 依赖依赖项的传递 include，而不是声明直接依赖。
- 建议：
  - 在锁定的 vision candidate 中显式声明 package/CMake 依赖，并做 isolated build。
- 前置条件：
  - 先确定要修复 `0c3a001…` 还是锁定的 `b366db7…`。
- 是否涉及硬件：
  - 否

## [P3-BUILD-001] offboard_cpp 声明未使用的接口生成/action 依赖

- 严重度：P3
- 状态：已确认
- 领域：Build / Docs
- 位置：
  - `src/offboard_cpp/CMakeLists.txt:22-24`
  - `src/offboard_cpp/package.xml:13-18`
- 证据：
  - CMake 查找 `rosidl_default_generators` 和 `action_msgs`。
  - package 声明 `rosidl_interface_packages` group。
  - 当前包没有 `.msg/.srv/.action` 生成调用，静态源码未见 `action_msgs` 使用。
- 影响：
  - 扩大不必要依赖面，掩盖真实 package contract。
- 根因：
  - 模板/历史接口声明残留。
- 建议：
  - 在 approved candidate 上删除未使用依赖，或补充确有计划的接口与测试；不要在当前漂移 checkout 直接改。
- 前置条件：
  - 维护者确认没有下游依赖该错误的 export。
- 是否涉及硬件：
  - 否

## 包边界说明

- `px4_bringup`、`offboard_py`、`mavlink`、`vision_to_mavros`、serial 与 CV
  包仍在磁盘，但 production profile 明确 forbidden。
- `Scripts/build/build_dds_only.sh:127-135` 使用 `--paths`/
  `--packages-select` 收窄构建，而不是信任整个 `src/`。
- `src/communication/Serial/serial_driver_ros/COLCON_IGNORE:1-3` 将串口包隔离。
- ROS 1 残留在上游仓库的 `.ros1_unported`，有 `AMENT_IGNORE/COLCON_IGNORE`；
  旧 MAVROS 流程仍存在于 archive package，不能视为 production。

## Foxy 兼容性

- 权威基线声明 Ubuntu 20.04/ROS 2 Foxy。
- 当前 production 源码使用 C++17（Offboard）和 C++14（vision），均可由 Foxy
  toolchain 支持；但必须在目标 native ARM64 环境重建。
- 历史 WSL H1 结果绑定另一组 nested SHA，不能替代本轮 build。
