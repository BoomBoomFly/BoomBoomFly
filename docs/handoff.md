---
title: BoomBoomFly 当前交接
status: source-fixes-pushed-sitl-pending
updated: 2026-09-08
---

# BoomBoomFly 当前交接

本文是当前完成度、阻塞项和下一步的唯一入口。项目采用科研原型/工程验证模式，优先保证功能正确和便于调试。

## 文档入口

| 文档 | 用途 |
|---|---|
| [工作区架构](工作区架构.md) | 模块职责、依赖、接口、配置归属与控制权契约 |
| [代码审查与清理记录](代码审查与清理记录.md) | 当前源码修复、实际验证结果及清理依据 |
| [D435i 调试记录](D435i调试记录.md) | 2026-09-07 相机采集、RSUSB 配置和标定限制 |
| [第一阶段实机门禁清单](第一阶段实机门禁清单.md) | SITL 后的目标机与实机操作验收 |
| [参考框架采用与演进路线](参考框架采用与演进路线.md) | 外部框架采用边界及阶段验收标准 |
| [零基础开源项目阅读与学习路线](零基础开源项目阅读与学习路线.md) | 新人知识背景；不是部署说明或运行授权 |

## 当前结论（2026-09-08）

源码已恢复，gateway、视觉桥、bringup 和 TI 修复已提交并推送到各自现有默认分支；新 gateway SITL 仍未通过。
本次重新审查只更新文档，未改变这些代码或 manifest，也未启动相机、Agent、PX4 或飞行动作。

- `verify_architecture.py` 通过。
- `verify_repos.py --with-perception-deps` 在嵌套仓库推送并更新 manifest 后通过；当前 manifest 已锁定四个新提交。
- 顶层仍有未提交改动，尚未形成顶层发布提交。
- 恢复脚本 4 项本地 Git 回归、视觉配置 7 项 Python 检查及通信边界脚本通过。
- 完整核心闭包已在 `/tmp/boomboom-publish` 编译通过；纯 CTest 通过。需要 Fast DDS 网络/ROS 图的测试受
  当前运行环境接口权限限制，未取得完整运行时证据；不能使用旧 build/install 或历史测试数字代替。

## 当前实现

| 模块 | 实际状态 |
|---|---|
| common | 消息、ExecuteFlight Action 和 ROS-free C99 core 源码齐全 |
| offboard_cpp | 单一 gateway；已有 Land 发布反馈、ACK/超时、握手取消转 HOLD、同步预流等修复；包级验证待完成 |
| px4_vision_bridge | DDS/MAVROS 互斥；时间差、姿态协方差、输入去重和 TF 年龄检查已修改；真实动态融合待验证 |
| px4_bringup | 所有自研 launch 的统一入口；读取功能包配置，只保留 TI H 任务配置，不再维护重复 mission/vision 配置 |
| ti | navigation、H 节点和 D FSM 三个包；H 仍使用 Action adapter，D 无运行节点；H 状态时间改用单调时钟 |
| communication | 版本、会话、序列号等语义契约，无传输实现 |
| perception / embedded_systems | 仓库存在；真实目标观测与设备命令/回执闭环尚未建立 |

PX4 与 px4_msgs 基线为 v1.16.2，Agent 为 v2.4.2。目标部署为 Jetson Orin Nano、Ubuntu 22.04、ROS 2 Humble。
硬件 PDF 中 OrangePi 描述与目标基线的冲突仍见架构文档，尚未认定实际装机配置。

## 数据流和验证边界

```text
D435i → ROS 图像/IMU：2026-09-07 采集通过，本轮未重采
图像/IMU → VIO → /vision/odometry：未接入；OpenVINS 只有学习参考，无源码/launch/标定配置
/vision/odometry → bridge → PX4 EKF2：实现存在，当前动态融合未验证
H → navigation → ExecuteFlight → gateway → PX4：源码接线存在，当前完整运行链未验证
任务 → 设备 → 回执：尚未形成真实硬件闭环
```

D435i RSUSB 采集不等于定位，SDK 的 IMU 标定缺失提示仍有效。VIO 接入须确认 ENU 世界、
FLU 机体原点、速度参考点、时间和 reset，不能只把相机/IMU frame 改名为 base_link。

## 停止条件

1. 当前修复尚缺完整核心构建、包级回归、新 gateway ROS 图/Action/PX4 ACK/SITL 证据。
2. 真实 VIO、相机—IMU及相机—机体标定、动态/reset/延迟和 EKF2 融合未完成。
3. H 的真实感知、设备、地面站保存显示、场地到 NED 标定和飞行时限未验证；D 仍仅为 FSM 原型。
4. 顶层和四个嵌套仓库有未提交修改，尚未形成当前修复的可复现发布。
5. 解锁、Kill、人工接管、无桨联调和受控飞行仍按[实机门禁](第一阶段实机门禁清单.md)由现场操作员确认。

## 下一步

1. 在隔离目录构建当前核心依赖闭包及 D 包，完成 gateway、视觉桥和 H fake Action 回归，记录失败与通过项。
2. 审核嵌套仓库修改，验证并形成可取得提交后再更新 manifest，最后检查顶层发布状态。
3. 开展未解锁 SITL 的 ROS 图、单 writer、Action/ACK 和故障分支验证，再逐步推进目标机与实机门禁。
4. 接通真实 VIO 和标定；H/gateway 基线稳定后再明确 D 的动态能力，不提前引入规划器或行为树。

历史验证摘要保留在[代码审查与清理记录](代码审查与清理记录.md)，不覆盖当前源码修改。
