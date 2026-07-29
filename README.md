# BoomBoomFly

BoomBoomFly 是面向室内无人机任务的 ROS 2 / PX4 DDS 工作区。当前最短目标是：

1. T265 向 PX4 提供稳定的视觉位置；
2. QGroundControl/PX4 负责模式切换、解锁和人工接管；
3. ROS 2 只负责持续轨迹、任务路径以及降落请求；
4. 首次闭环只做 0.5 m 垂直起飞、悬停和降落。

## 基线

- 机载计算机：Jetson Orin Nano，Ubuntu 20.04，ROS 2 Foxy
- 飞控：Pixhawk 2.4.8，PX4 v1.16.2
- 定位：Intel RealSense T265
- DDS：TELEM2，921600 baud，`ROS_DOMAIN_ID=0`
- PX4 参数：[docs/2026.7.30.params](docs/2026.7.30.params)
- 依赖清单：[workspace.repos](workspace.repos)

`offboard_cpp`、`vision_to_dds` 和 `communication` 跟随各自远端默认分支的
最新提交；第三方依赖仍固定到精确提交。根仓库不保存 `src/`，由安装脚本恢复。

## 恢复与构建

```bash
git clone https://github.com/BoomBoomFly/BoomBoomFly.git
cd BoomBoomFly

bash Scripts/installation/uav_px4_dds_install.sh \
  --with-optional perception \
  --update \
  --require-colcon

bash Scripts/build/build_dds_only.sh
```

`--update` 只允许项目分支快进，不会丢弃本地提交或覆盖脏工作树。每次恢复后，
安装脚本会把实际使用的分支和提交记录到 `log/repository-versions.tsv`。

只检查现有工作区：

```bash
bash Scripts/installation/uav_px4_dds_install.sh \
  --with-optional perception \
  --verify-only \
  --require-colcon
```

## 数据链

```text
T265 -> vision_to_dds -> /fmu/in/vehicle_visual_odometry -> PX4 EKF2

mission START -> flight sequence -> offboard_cpp
              -> trajectory setpoint / vehicle command -> PX4
```

生产环境中，每个 `/fmu/in/*` 控制话题只能有一个 writer。回放测试固定使用
`ROS_DOMAIN_ID=231`，不得接入生产飞控。

## 下一步

先完成 `offboard_cpp` 的 QGC 控制边界和垂直轨迹闭环，再接入任务协调、目标感知、
抛投管理和地面站功能。项目仓直接跟随已审核的默认分支；只有第三方依赖版本变化时
才更新 `workspace.lock.repos` 中的精确提交，并通过统一构建入口完成工作区集成。

## 目录

```text
Scripts/build/          构建入口
Scripts/installation/   工作区恢复与环境检查
Scripts/runtime/        仍在使用的运行工具
Scripts/test/           隔离回放
config/profiles/        构建与启动包清单
docs/contracts/         通信契约
tools/authority/        控制状态检查工具
workspace.lock.repos    项目分支与第三方锁定版本清单
```

脚本用途见 [Scripts/README.md](Scripts/README.md)。
