# FPGA 软核固件基础模块库

本目录为平台无关的裸机导航与定位 C 基础算法库，不包含特定板卡的 MMIO 地址表、硬编码物理尺寸宏或板级主循环入口。所有机器人尺寸、雷达安装偏置、速度与制动参数均通过配置结构体在运行时注入。

> 特定板卡的外设寄存器映射、固化配置及主循环入口保留在 [`../boards/`](../boards/) 对应板级工程源码中。

## 分层目录

| 目录 | 分层定位 | 包含文件与接口 |
| --- | --- | --- |
| `boot/` | RISC-V 启动汇编、通用链接脚本与裸机运行时 | `start.S`、`link.ld`、`runtime.c` |
| `common/` | 跨模块共用的基础数学内联原语 | `nav_math.h`（`abs32`、`abs64`、`ceil_div`） |
| `localization/` | 轮速与 IMU 平面 EKF 里程计（纯配置结构输入） | `odometry.h`、`odometry.c` |
| `navigation/` | 滚动局部图、足迹相交、增量 A* 规划、路径跟踪、制动安全守卫与任务调度 | `local_map.h`/`.c`、`footprint.h`/`.c`、`local_plan.h`/`.c`、`route_follow.h`/`.c`、`local_guard.h`/`.c`、`robot_navigation.h`/`.c`（通过 `robot_navigation_config_t` 传入全部车体、地图与保护配置） |

## 编译说明

直接对本目录编译或做主机语法检查时，传入以下头文件搜索路径：

```text
-Icommon -Ilocalization -Inavigation
```
