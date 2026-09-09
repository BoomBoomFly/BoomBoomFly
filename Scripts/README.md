# 脚本

脚本按职责分组，所有命令均从仓库根目录执行。

```text
Scripts/
├── workspace/   # 仓库拉取、更新、状态、构建、清理和环境加载
└── simulation/  # PX4 SITL 构建与运行入口
```

## 工作区管理

```bash
# 导入缺失仓库，并更新核心清单中的分支仓库（需要 Git、Python 3 和 PyYAML）
python3 -B Scripts/workspace/sync_repos.py pull

# 同时导入可选感知源码依赖
python3 -B Scripts/workspace/sync_repos.py pull --with-perception-deps

# 校验核心仓库，或同时校验感知依赖
./Scripts/workspace/verify_repos.py
./Scripts/workspace/verify_repos.py --with-perception-deps

# 校验 common/TI/offboard_cpp 的依赖和控制权边界
./Scripts/workspace/verify_architecture.py

# 查看受管理仓库的分支、提交和脏状态
./Scripts/workspace/repo_status.sh

# 更新分支仓库（要求干净）；固定提交仓库仅 fetch
python3 -B Scripts/workspace/sync_repos.py update

# 推送 boomboom 下所有仓库当前分支的已提交改动
./Scripts/workspace/push_repos.sh

# 默认构建 px4_bringup 及其核心依赖，或指定一个包及其依赖
./Scripts/workspace/build.sh
./Scripts/workspace/build.sh offboard_cpp

# 查看 clangd 编译数据库摘要，或查询指定源码的真实编译命令
./Scripts/workspace/read_compile_commands.py
./Scripts/workspace/read_compile_commands.py \
  px4/px4_ws/src/boomboom/offboard_cpp/src/gateway/gateway_executor.cpp

# 在当前 shell 加载 ROS 2 和已构建的工作区
source Scripts/workspace/setup_env.sh

# 记录 realtime/monotonic/boottime，检查校时跳变与 suspend/resume
python3 Scripts/workspace/monitor_clocks.py --duration-sec 180 \
  --output /tmp/boomboom-clocks.csv

# 删除 ROS 2 工作区构建产物
./Scripts/workspace/clean.sh
```

`manifests/boomboom.repos` 使用分支名：自研仓库跟随各自的 `main`、`master` 或 `DDS`，
`px4_msgs` 跟随 `release/1.16`。`sync_repos.py pull` 导入缺失仓库后同步这些分支；
`sync_repos.py update` 同步清单中已存在的仓库。统一入口直接调用 Git，
无需安装 vcstool。每次同步都会 fetch 并快进到远端分支最新提交。
旧清单产生的 detached HEAD 在可快进时自动切回指定分支；本地修改、分叉或额外提交会报错，
不会自动 stash、reset 或强制覆盖。非空非仓库目录和符号链接也不会被删除。
`verify_repos.py` 离线检查分支及本地已 fetch 的远端引用；要检查最新状态，先运行同步脚本。

工作区脚本管理 `px4/px4_ws/` 和 `px4/upstream/`。PX4 和
Micro-XRCE-DDS-Agent 不属于 colcon 源码树，按各自上游说明独立构建和运行。
`sync_repos.py update` 不覆盖未提交修改；固定版本仓库只执行 `fetch`，本地修改或构建产物不会阻塞更新。

自研 `perception` 和 `embedded_systems` 由核心 `manifests/boomboom.repos` 恢复。
`manifests/perception_deps.repos` 只保存 RealSense SDK 和 ROS 封装等可选第三方感知依赖的精确版本；
只有需要从源码恢复这些依赖时才使用 `--with-perception-deps`。旧参数 `--with-perception` 仍作为兼容别名。
无参数 `build.sh` 使用 colcon 的 `--packages-up-to px4_bringup`，不会顺带构建当前源码树中的可选
RealSense、MAVROS、RTAB-Map 或 IMU 工具；需要其中某包时显式传入包名。

Jetson 上执行 `./Scripts/workspace/build.sh realsense2_camera` 或 `librealsense2` 时，
脚本通过 `realsense_jetson.meta` 为 SDK 启用 `FORCE_RSUSB_BACKEND=ON`，使相机 IMU 不依赖
Jetson 内核的 HID Sensor Hub。桌面机和无参数核心构建保持原有选择。
D435i 故障记录与启动命令见 [D435i 调试记录](../docs/D435i调试记录.md)。

`read_compile_commands.py` 默认读取 `px4/px4_ws/build/compile_commands.json`，输出 JSON 摘要；
传入源码路径或文件名时输出匹配的编译记录。使用 `--database` 可以读取其他数据库，例如
`px4/upstream/PX4-Autopilot/build/px4_sitl_default/compile_commands.json`。

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

`push_repos.sh` 仅推送 `px4/px4_ws/src/boomboom/` 下各仓库的当前分支到其跟踪分支，
不自动提交，不使用强制推送，不包含主仓库或第三方依赖。存在未提交修改、detached HEAD
或缺少跟踪分支时停止；多个仓库依次推送，若中途失败，先前成功的推送不会回滚。
