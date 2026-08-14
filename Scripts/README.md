# 脚本

脚本按职责分组，所有命令均从仓库根目录执行。

```text
Scripts/
├── workspace/   # 仓库拉取、更新、状态、构建、清理和环境加载
└── simulation/  # PX4 SITL 构建与运行入口
```

## 工作区管理

```bash
# 导入核心仓库（需要 vcstool）
./Scripts/workspace/pull_repos.sh

# 同时导入可选感知源码依赖
./Scripts/workspace/pull_repos.sh --with-perception-deps

# 校验核心仓库，或同时校验感知依赖
./Scripts/workspace/verify_repos.py
./Scripts/workspace/verify_repos.py --with-perception-deps

# 校验 common/TI/offboard_cpp 的依赖和控制权边界
./Scripts/workspace/verify_architecture.py

# 查看受管理仓库的分支、提交和脏状态
./Scripts/workspace/repo_status.sh

# 仅在所有受管理仓库干净时更新
./Scripts/workspace/update_repos.sh

# 默认构建 px4_bringup 及其核心依赖，或指定一个包及其依赖
./Scripts/workspace/build.sh
./Scripts/workspace/build.sh offboard_cpp

# 在当前 shell 加载 ROS 2 和已构建的工作区
source Scripts/workspace/setup_env.sh

# 记录 realtime/monotonic/boottime，检查校时跳变与 suspend/resume
python3 Scripts/workspace/monitor_clocks.py --duration-sec 180 \
  --output /tmp/boomboom-clocks.csv

# 删除 ROS 2 工作区构建产物
./Scripts/workspace/clean.sh
```

工作区脚本管理 `px4/px4_ws/` 和 `px4/upstream/`。PX4 和
Micro-XRCE-DDS-Agent 不属于 colcon 源码树，按各自上游说明独立构建和运行。
`update_repos.sh` 不覆盖未提交修改；上游仓库按清单固定版本，只执行 `fetch`。

自研 `perception` 和 `embedded_systems` 由核心 `manifests/boomboom.repos` 恢复。
`manifests/perception_deps.repos` 只保存 RealSense SDK 和 ROS 封装等可选第三方感知依赖的精确版本；
只有需要从源码恢复这些依赖时才使用 `--with-perception-deps`。旧参数 `--with-perception` 仍作为兼容别名。
无参数 `build.sh` 使用 colcon 的 `--packages-up-to px4_bringup`，不会顺带构建当前源码树中的可选
RealSense、MAVROS、RTAB-Map 或 IMU 工具；需要其中某包时显式传入包名。

`verify_architecture.py` 不连接 PX4，也不运行节点；它检查公共接口只由 `common` 提供、`ti` 不依赖
`px4_msgs` 或 `/fmu/in/*`、H/D 任务不互相依赖，且已接入飞行的 H 任务通过
`boomboom_navigation` 使用 Action，
以及三个 PX4 控制输入只在 `offboard_cpp` 生产代码中出现。

`monitor_clocks.py` 只采样 Linux 三类时钟并写入 CSV，不查询或修改 systemd/NTP。检测到
实时时钟跳变时返回 2；带 `--require-suspend` 但未观察到休眠/恢复时返回 3。

## 仿真

仿真脚本放在 `Scripts/simulation/`，与 ROS 2 工作区脚本分开维护：

```bash
bash Scripts/simulation/build_px4_sitl.sh
bash Scripts/simulation/run_px4_sitl.sh
bash Scripts/simulation/clean_px4_sitl.sh
```

Ubuntu 20.04 默认使用 Gazebo Classic，Ubuntu 22.04 默认使用 `gz_x500`；也可以把 PX4
仿真目标作为 `run_px4_sitl.sh` 的参数。详细说明见
`Scripts/simulation/README.md`。
