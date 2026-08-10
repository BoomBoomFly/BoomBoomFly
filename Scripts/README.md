# Scripts

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
./Scripts/workspace/pull_repos.sh --with-perception

# 查看受管理仓库的分支、提交和脏状态
./Scripts/workspace/repo_status.sh

# 仅在所有受管理仓库干净时更新
./Scripts/workspace/update_repos.sh

# 构建全部 ROS 2 包，或指定一个包及其依赖
./Scripts/workspace/build.sh
./Scripts/workspace/build.sh offboard_cpp

# 在当前 shell 加载 ROS 2 和已构建的工作区
source Scripts/workspace/setup_env.sh

# 删除 ROS 2 工作区构建产物
./Scripts/workspace/clean.sh
```

工作区脚本管理 `px4/px4_ws/` 和 `px4/upstream/`。PX4 和
Micro-XRCE-DDS-Agent 不属于 colcon 源码树，按各自上游说明独立构建和运行。
`update_repos.sh` 不覆盖未提交修改；上游仓库按 manifest 固定版本，只执行 fetch。

`manifests/perception.repos` 保存当前 RealSense SDK 和 ROS wrapper 源码依赖的精确版本；
只有需要从源码恢复 RealSense 感知环境时才使用 `--with-perception`。

## 仿真

仿真脚本放在 `Scripts/simulation/`，与 ROS 2 工作区脚本分开维护。目录约定见
`Scripts/simulation/README.md`。
