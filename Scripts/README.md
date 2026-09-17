# BoomBoomFly 工作区脚本

根据 `FPGA_GOWIN/Scripts` 的同步、推送与环境加载方式，适配当前目录。
可从任意目录执行脚本，工作区位置由脚本自身路径确定。

| 脚本 | 用途 |
| --- | --- |
| `sync_ros_packages.sh` | 首次克隆 `BoomBoomFly/uav_control` 到 `ros_ws/src/uav_control`，已有独立仓库时执行 `git pull --ff-only` |
| `push_git.sh` | 自动暂存、提交并推送指定仓库到 `origin` 同名分支 |
| `setup_ros_environment.bash` | source 系统 ROS 2 Humble 和已编译的工作区 overlay |

## 同步自写包

```bash
cd /home/aa/BoomBoomFly
./Scripts/sync_ros_packages.sh
```

当前仅同步 `uav_control`。已有非 Git 目录会报错并保留；已有仓库沿用当前
分支的 upstream，不自动切分支、重置或处理冲突。无 upstream 时需先配置。
脚本不更新 PX4、MAVROS、MAVLink、OpenVINS，也不创建尚未实现的功能包。

## 按仓库提交推送

按需选择一个范围：

```bash
./Scripts/push_git.sh uav_control "更新控制接口"
./Scripts/push_git.sh main "更新工作区脚本与文档"
```

`main` 是主项目范围名称，不限定当前分支名。`uav_control` 是独立仓库，
通过自己的远程地址单独发布。

执行前用对应仓库的 `git status` 查看改动。脚本自动提交所选范围内所有
未忽略的新增、修改和删除文件，包括已暂存内容。主仓库范围明确排除：

- `ros_ws/src/uav_control/`
- `ros_ws/src/thirdparty/` 和 `ros_ws/upstream/`
- `ros_ws/build/`、`ros_ws/install/`、`ros_ws/log/`
- `references/`、`reference/` 和 `docker/kalibr/source/`

若上述排除路径已经有暂存改动，脚本直接停止，保留暂存区供你处理。
这些排除规则仅约束本脚本，手动 `git add` 仍需留意范围。
以后增加独立包时，应同时更新范围映射和主仓库排除列表。

没有新改动时跳过提交，仍推送已有提交。不自动 pull、force push 或推送标签。
推送失败会保留本地提交，可处理网络或远端分歧后重试。

## 加载 ROS 环境与编译

```bash
cd /home/aa/BoomBoomFly
source Scripts/setup_ros_environment.bash
cd ros_ws
CMAKE_BUILD_PARALLEL_LEVEL=2 MAKEFLAGS="-j2" colcon build \
  --packages-select uav_control --symlink-install
source install/local_setup.bash
```

环境脚本要求已有 Humble 和工作区安装产物，不安装依赖、不重编译第三方，
也不启动 SITL、MAVROS 或控制节点。新工作区尚无 install 时先手动 source
系统 Humble，按项目依赖准备步骤完成首次编译。

## 离线检查

```bash
python3 Scripts/test_scripts.py
```

检查使用临时目录与本地 bare 远程，验证推送范围、非 Git 目录保护和快进同步；
不连接 GitHub，不提交或推送实际项目，不验证飞控功能。
