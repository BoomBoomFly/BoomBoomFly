# 工作区脚本

脚本根据自身位置定位项目，可以从任意目录执行。

| 脚本 | 用途 |
| --- | --- |
| `sync_ros_packages.sh [仓库…]` | 克隆或快进同步自写独立仓库 |
| `push_git.sh 仓库 "提交说明"` | 暂存、提交并推送指定仓库 |
| `setup_ros_environment.bash [工作区]` | 加载 Humble 与指定工作区 overlay |
| `test_scripts.py` | 用临时仓库和本地 bare 远程验证脚本 |

## 同步

```bash
./Scripts/sync_ros_packages.sh
# 只同步指定范围：
./Scripts/sync_ros_packages.sh uav_control uav_bringup
./Scripts/sync_ros_packages.sh swarm_ws ugv_ws
```

仓库路径统一从 `manifests/default.xml` 读取。默认先同步三个工作区，再同步八个自写包，共十一个独立仓库：`uav_ws/src/` 下的 `uav_control`、`uav_vio_bridge`、
`uav_bringup`、`uav_mission`，以及项目根目录下的 `swarm_ws`、`ugv_ws`。
共享接口包 `uav_interfaces` 随 `uav_control` 克隆。UGV 功能包包括 `fpga_gateway`、`car_bringup`、`car_navigation`、`car_mission`，保持原 ROS 包名。

已有仓库沿用当前分支 upstream，执行 `git pull --ff-only`；首次克隆使用
`https://github.com/BoomBoomFly/<仓库>.git`。遇错即停止，已完成的同步不回滚。
已有非 Git 目录会保留并报错。脚本不切分支、不重置、不处理冲突，也不更新第三方或 PX4。

## 按仓库提交推送

```bash
./Scripts/push_git.sh main "更新主项目脚本"
./Scripts/push_git.sh uav_ws "更新 UAV 工作区及仿真"
./Scripts/push_git.sh uav_control "更新控制节点"
./Scripts/push_git.sh uav_vio_bridge "更新位姿桥接"
./Scripts/push_git.sh uav_bringup "更新启动编排"
./Scripts/push_git.sh uav_mission "更新任务"
./Scripts/push_git.sh swarm_ws "更新集群源码与仿真"
./Scripts/push_git.sh ugv_ws "更新地面车工作区说明"
./Scripts/push_git.sh fpga_gateway "更新网关"
./Scripts/push_git.sh car_bringup "更新车辆启动"
./Scripts/push_git.sh car_navigation "更新导航"
./Scripts/push_git.sh car_mission "更新任务"
```

`main` 表示主仓库范围，不限定分支名。执行前查看对应仓库 `git status`：
脚本自动暂存所选仓库内全部未忽略的新增、修改和删除，并包括原有暂存内容。

`uav_ws` 范围管理其 README、`.gitignore` 和 `sim/`；主仓库明确排除：

- 独立工作区 `uav_ws/`、`swarm_ws/`、`ugv_ws/`（包括其中嵌套仓库）。
- `uav_ws/src/thirdparty/`、`uav_ws/upstream/`。
- `uav_ws/build/`、`uav_ws/install/`、`uav_ws/log/`、主仓库 `log/`。
- `references/`、`reference/`、`docker/kalibr/source/`。

排除路径已有暂存改动时，脚本停止并保留暂存内容。没有新改动时跳过提交，
仍推送已有提交到 `origin` 同名分支。不自动 pull、force push 或推送标签；
推送失败保留本地提交。以后增加独立仓库需更新 manifest 及对应父工作区的 `.gitignore`、推送排除列表。

UAV 仿真文件迁移后，`uav_bringup` 的构建需要同时具备 `uav_ws/src/` 和
`uav_ws/sim/`。包仓库的同步不会获取 `uav_ws` 仓库管理的 `sim` 文件。

## 加载环境与首次构建

```bash
source Scripts/setup_ros_environment.bash          # 默认 uav_ws
source Scripts/setup_ros_environment.bash ugv_ws
source Scripts/setup_ros_environment.bash swarm_ws
```

环境脚本要求已有 `/opt/ros/humble/setup.bash` 和选中工作区的
`install/local_setup.bash`；不自动构建、切换目录或启动节点。
多个 overlay 连续加载会叠加，独立验证时使用新终端。

首次构建尚无 overlay 时，直接加载系统 ROS：

```bash
source /opt/ros/humble/setup.bash
cd /home/aa/BoomBoomFly/uav_ws
colcon build --base-paths src/uav_control/uav_interfaces src --symlink-install \
  --packages-select mavros_msgs uav_interfaces uav_control uav_mission uav_vio_bridge uav_bringup
source install/local_setup.bash
```

UGV 从 `ugv_ws` 执行 `colcon build --base-paths src`。
集群工作区目前只有预留说明，没有可构建的 ROS 包。
仿真入口和验证边界见 [UAV](https://github.com/BoomBoomFly/uav_ws/blob/main/sim/README.md)、
[UGV](https://github.com/BoomBoomFly/ugv_ws/blob/main/sim/README.md)、[集群](https://github.com/BoomBoomFly/swarm_ws/blob/main/sim/README.md)。

## 离线检查

```bash
python3 Scripts/test_scripts.py
```

检查覆盖语法、十一个独立仓库的推送和范围隔离、首次克隆、快进同步、
越界暂存拒绝及工作区环境选择。测试仅操作临时目录和本地 bare 远程，
不连接 GitHub、不提交或推送实际项目、不验证飞控或车辆功能。

## repo 获取

repo 在现有顶层目录初始化及版本锁定流程见 [manifest 说明](../manifests/README.md)。`/home/aa/BoomBoomFly` 直接作为 repo 客户端顶层，首次初始化使用 `--use-local-gitdirs` 复用现有 Git 目录。同步脚本和 repo 读取同一清单，不要同时运行。
