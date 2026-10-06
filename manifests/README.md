# 多仓库清单

`default.xml` 是自写仓库路径的统一来源，供 repo 和 `Scripts` 中的同步/推送入口读取。
包括主项目、三个工作区、四个 UAV 功能包和四个 UGV 功能包，共 12 个仓库。
集群目前没有可构建的功能包，先保留工作区管理，不建立空功能仓库。

## 在新目录使用 repo

安装官方 repo 工具并配置 GitHub 访问权限后：

```bash
mkdir -p ~/boomboom-client
cd ~/boomboom-client
repo init -u https://github.com/BoomBoomFly/BoomBoomFly.git -b main -m manifests/default.xml
repo sync
```

项目位于 `~/boomboom-client/BoomBoomFly/`，repo 元数据位于客户端根目录 `.repo/`。
请先在新目录验证，不在现有含未提交文件的工作目录直接初始化。
只获取 UAV 时，使用 `repo init` 的 `-g core,uav`；UGV 为 `-g core,ugv`；集群为 `-g core,swarm`。
仓库仍独立提交，GitHub 推送使用常规 Git 或 `Scripts/push_git.sh`，不依赖 Gerrit。

## 开发与验证版本

开发清单跟随 `main`；同一清单在不同时间同步，获取的提交可能不同。
验证通过后，在 repo 客户端根目录执行：

```bash
repo manifest -r -o BoomBoomFly/manifests/validated.xml
```

`validated.xml` 固定当时各仓库提交。只有实际完成目标验证后，才将其作为验证版本发布；生成锁定文件本身不代表测试通过。

## 上游边界

当前清单只包含自写仓库。PX4、MAVROS、MAVLink、OpenVINS 与参考仓库未纳入默认同步。
已有 PX4 等上游仓库保留其原有 submodule 管理。待明确依赖版本、实际使用范围后再增加可选依赖清单，避免默认下载所有参考项目。

`sync_ros_packages.sh` 可用于原有工作目录，从同一清单获取路径并沿当前分支 upstream 快进。
repo 客户端使用 `repo sync`。两个同步方式不要同时运行，也不要假定 repo 会保留任意未提交修改；切换前先检查各仓库状态。
