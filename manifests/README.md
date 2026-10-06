# 多仓库清单

`/home/aa/BoomBoomFly` 同时是主 Git 仓库和 repo 客户端顶层，不再额外建立外层目录。
`default.xml` 描述三个工作区及八个功能包，共 11 个子仓库；主仓库由普通 Git 单独管理。
同步与推送脚本也从该清单获取子仓库路径。

## 现有工作区初始化

已安装支持 `--use-local-gitdirs` 的官方 repo 工具，并配置 GitHub 私有仓库访问权限后：

```bash
cd /home/aa/BoomBoomFly
repo init -u https://github.com/BoomBoomFly/BoomBoomFly.git -b main \
  -m manifests/default.xml --use-local-gitdirs
repo sync
```

该模式复用各子仓库原有 `.git/`，repo 元数据保存到顶层 `.repo/`，由主仓库忽略。
清单路径直接使用 `uav_ws/`、`ugv_ws/`、`swarm_ws/`，不会生成第二层 `BoomBoomFly/`。
`--use-local-gitdirs` 必须在首次初始化客户端时使用；不要对已采用其他存储模式的客户端直接切换此选项。
执行同步前检查各仓库工作状态，不使用 force-sync、reset 或 clean 覆盖本地工作。

## 新机器获取

先克隆主仓库到需要的顶层，再在其中初始化 repo：

```bash
git clone https://github.com/BoomBoomFly/BoomBoomFly.git ~/BoomBoomFly
cd ~/BoomBoomFly
repo init -u https://github.com/BoomBoomFly/BoomBoomFly.git -b main \
  -m manifests/default.xml --use-local-gitdirs
repo sync
```

只获取 UAV 时使用 `repo init` 的 `-g uav`；UGV 为 `-g ugv`；集群为 `-g swarm`。
主仓库不在 repo 的项目列表中，使用 `git pull --ff-only` 单独更新；repo sync 获取的清单来自远端主仓库，不能自动更新顶层文档和脚本。

## 开发与推送

子仓库独立提交，使用常规 Git 或 `Scripts/push_git.sh`，不依赖 Gerrit。
已有 main 分支继续用于开发；新获取的项目可能处于 detached HEAD，开始修改前建立分支：

```bash
repo start feature-navigation car_navigation
./Scripts/push_git.sh car_navigation "更新导航"
```

推送脚本拒绝 detached HEAD，并推送到同名远程分支。清单跟随 main，开发分支合并到 main 后才能进入默认同步版本。

## 验证版本

开发清单跟随 main，同一清单在不同时间可能获取不同提交。验证通过后，在顶层执行：

```bash
repo manifest -r -o manifests/validated.xml
git rev-parse HEAD
```

锁定清单固定 11 个子仓库提交，主仓库提交需另行记录。只有实际完成目标验证后才作为验证版本发布；生成文件本身不代表测试通过。

## 上游与同步边界

当前清单只包含自写仓库。PX4、MAVROS、MAVLink、OpenVINS 及参考仓库未纳入默认同步，上游保留原有 submodule 管理。
集群尚无可构建功能包，先由工作区管理预留说明。

`sync_ros_packages.sh` 从同一清单读取路径，并沿各仓库当前分支 upstream 快进；
repo 使用清单 revision 同步。两个同步入口不要同时运行。
