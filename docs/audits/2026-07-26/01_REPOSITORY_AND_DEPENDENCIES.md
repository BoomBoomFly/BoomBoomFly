# 01 — 仓库结构与依赖可复现性审查

## 1. 审查基线与边界

审查时间：2026-07-26（Asia/Shanghai）

| 项目 | 当前事实 |
|---|---|
| 仓库根目录 | `/home/c/BoomBoomFly` |
| `origin` | `https://github.com/BoomBoomFly/BoomBoomFly.git`（fetch/push） |
| 分支 | `agent/follow-latest-offboard` |
| HEAD | `3ce28094e14ed720987c5fc6d1172e377f09b1cc` |
| 根工作树基线 | `git status --short` 无输出；根仓库 clean |
| 网络核验 | 未执行；未 fetch、clone、pull 或访问远端 |
| 构建/测试 | 未构建、未测试 |
| 硬件 | 未访问、未启动任何节点或 launch |

根仓库 clean 不能解释为整个工作区 clean：`src/` 中大部分依赖是被根
`.gitignore` 忽略的独立 Git 仓库，另有未受 manifest 管理的源码目录。必须以逐仓库
审计结果为准。

开始前已读取用户要求的全部基线：

- `README.md`
- `docs/handoff.md`
- `docs/CONTROL_AUTHORITY_MATRIX.md`
- `docs/adr/0001-dds-only-control-authority.md`
- `docs/evidence/OFFBOARD_PX4_MSGS_COMPAT_20260724.md`
- `docs/evidence/PX4_PARAMS_20260724T203458+0800.json`（仅用于确认其为历史参数快照；
  不将其作为当前依赖或飞控状态）
- `workspace.lock.repos`
- `workspace.repos`
- `workspace.excluded_packages`
- `Scripts/README.md`
- `.gitignore`

上述必读路径均存在。仓库内未发现适用于本目录的 `AGENTS.md`。

## 2. 仓库与 manifest 交叉核验

### 2.1 精确 lock

`workspace.lock.repos:1-63` 声明 15 个 Git 仓库，所有 `version` 均为 40 位
commit SHA。只读命令：

```bash
bash Scripts/installation/uav_px4_dds_install.sh \
  --verify-only \
  --skip-package-check
```

实际结果：

```text
Summary: planned=15 cloned=0 updated=0 verified=15 blockers=4
exit status: 1
```

15 个路径均存在，实际 origin（允许 `.git`/末尾斜杠等价归一化）和 HEAD 均与 lock
一致。非零退出来自四个保留的 dirty checkout，说明该检查在已知 dirty 状态下确实
fail-closed。

| 路径 | lock / 当前 HEAD | origin | HEAD 状态 | 工作树 |
|---|---|---|---|---|
| `src/px4_msgs` | `392e831c…` | 匹配 | detached | clean |
| `src/Micro-XRCE-DDS-Agent` | `57d08621…` | 匹配 | detached | clean |
| `src/gazebo_ros_pkgs` | `b6f7bf12…` | 匹配 | `foxy` | clean |
| `src/imu_tools` | `d28555e4…` | 匹配 | `foxy` | clean |
| `src/librealsense` | `c94410a4…` | 匹配 | detached | dirty：3347 个 mode change |
| `src/navigation2` | `ca482808…` | 匹配 | `foxy-devel` | clean |
| `src/navigation_msgs` | `fe880e99…` | 匹配 | `foxy` | dirty：删除 `map_msgs` 13 个文件 |
| `src/offboard_cpp` | `cded3dc5…` | 匹配 | `DDS` | clean |
| `src/realsense-ros` | `8abb4657…` | 匹配 | detached | dirty：98 个 mode change，另有未跟踪 launch |
| `src/rplidar_ros` | `24cc9b6d…` | 匹配 | `ros2` | clean |
| `src/rtabmap` | `0070de4a…` | 匹配 | `foxy-devel` | clean |
| `src/rtabmap_ros` | `b341e2a7…` | 匹配 | `foxy-devel` | clean |
| `src/slam_toolbox` | `4786e90c…` | 匹配 | `foxy-devel` | clean |
| `src/vision_opencv` | `72152d9d…` | 匹配 | `foxy` | dirty：删除 `image_geometry` 17 个文件 |
| `src/vision_to_dds` | `0c3a0013…` | 匹配 | detached | clean |

结论是“Git 对象锁定完整，但当前文件树未被完整锁定”。四个 dirty checkout 不是被
自动判定为错误；保留它们符合现有交接要求。问题在于其中的有效差异没有可复现的
patch/派生仓库/内容散列与用途分类。

### 2.2 维护 manifest 与 moving dependency

`workspace.repos:1-65` 有 16 个维护条目：15 个 `src/` 条目加
`../communication@main`。只读命令：

```bash
bash Scripts/installation/uav_px4_dds_install.sh \
  --manifest workspace.repos \
  --allow-moving-refs \
  --verify-only \
  --skip-package-check
```

实际结果：

```text
Summary: planned=16 cloned=0 updated=0 verified=15 blockers=5
exit status: 1
```

第五个 blocker 是 `/home/c/communication` 缺失。`README.md:27` 和
`Scripts/README.md:81-83` 明确把它作为不进入 lock 的 moving dependency，并要求每次
实验/发布另记实际 HEAD；当前仓库没有机器可读的实验 HEAD receipt/schema。

### 2.3 实际嵌套仓库、未受管目录和 ROS 包发现

除 15 个 lock 仓库外，`src/` 还保留下列源码：

| 实际路径 | 类型 | manifest 状态 | ROS 包发现 |
|---|---|---|---|
| `src/mavlink` | 独立 Git，dirty | 未受管、明确排除 | `mavlink` |
| `src/mavros` | 独立 Git，dirty | 未受管、明确排除 | `libmavconn`、`mavros`、`mavros_extras`、`mavros_msgs` |
| `src/offboard_py` | 独立 Git | 未受管、明确排除 | `offboard_py` |
| `src/px4_bringup` | 独立 Git | 未受管、明确排除 | `px4_bringup` |
| `src/ros2_foxy_vision_to_mavros` | 独立 Git，dirty | 未受管、明确排除 | `vision_to_mavros` |
| `src/serial-ros2` | 独立 Git | 未受管、明确排除 | `serial` |
| `src/serial_driver_ros2` | 独立 Git，dirty | 未受管、明确排除 | `serial_driver` |
| `src/cv_yolo_paddle_pkg` | 非 Git 源目录 | 未受管、明确排除 | `cv_yolo_paddle_pkg` |
| `src/opencv_cpp` | 非 Git 源目录 | 未受管、明确排除 | `opencv_cpp` |
| `src/serial_driver_ros` | 根索引 gitlink，空目录 | 不在 manifest、明确排除 | 无；gitlink 元数据损坏 |

`colcon list --base-paths src` 返回 0，没有报告重复包名，但发现了上表 12 个明确排除的
包。`workspace.excluded_packages` 的 13 个包中，只有
`src/mavros/test_mavros/COLCON_IGNORE` 实际被发现边界排除；其余 12 个均可被默认
colcon crawl 发现。当前 `src/` 下共有 81 个 `package.xml`。

注意：虽然用户把 `colcon list` 列为允许命令，该环境的 colcon 仍自动写入了忽略的
日志目录：

```text
log/list_2026-07-26_15-54-25/logger_all.log
log/latest
log/latest_list
log/COLCON_IGNORE
```

未删除或覆盖这些文件，因为并发代理也产生了其他 `log/list_*`、`log/graph_*`
记录，无法安全区分所有权。没有 tracked/source 文件因此改变；后续未再次运行
colcon。

### 2.4 submodule 与 gitlink

15 个 lock 仓库当前均无根级 `.gitmodules`。根仓库自身却在索引中保留：

```text
160000 87f3907f0b3b906d474a8d1e1dc9677ab0c4298f 0 src/serial_driver_ros
```

根 HEAD 不含 `.gitmodules`。实际执行：

```bash
git submodule status --recursive
```

结果为退出状态 128：

```text
fatal: no submodule mapping found in .gitmodules for path 'src/serial_driver_ros'
```

因此当前根仓库不能完成统一 submodule 状态审计。该路径属于历史 serial 排除项，不是
DDS production 依赖，但它是一个真实的仓库完整性/空白恢复缺陷。

## 3. 恢复脚本评价

`Scripts/installation/uav_px4_dds_install.sh` 的已验证优点：

- `set -Eeuo pipefail`（第 2 行）；
- 拒绝危险 manifest 路径和重复目标（第 262-285 行）；
- 默认拒绝 moving ref（第 282-284 行）；
- 对已有仓库检查 origin、dirty、HEAD（第 432-470 行）；
- `--verify-only` 遍历全部 manifest 后按 blocker 非零退出（第 546-560 行）；
- 不执行 `git pull` 或 reset；
- `bash -n Scripts/installation/uav_px4_dds_install.sh` 返回 0。

限制：

- 它只证明 manifest 中的仓库，不拒绝未受管仓库或 excluded ROS 包；
- 默认 package check 仅检查 4 个必需包，发现 forbidden 包也成功（第 492-543 行）；
- `--verify-only` 不核验 submodule commit/dirty/初始化完整性；
- 新仓库采用逐项 `mkdir/init/fetch/checkout`，没有事务、恢复 receipt 或半成品恢复测试；
- 它明确不锁定/安装 ROS、系统包、udev、PX4 firmware 或工具链，因此只能恢复“源码
  仓库子集”，不能从空白环境恢复可构建、可验收的完整工程。

真实 clone/fetch/update、空白目录恢复和故障中断重入均因本轮禁网/禁写边界未执行，
相关结论标为静态检查或未验证。

## 4. 发现

### BBF-DEP-001 — 明确排除的控制与历史包仍被默认 colcon 发现

- **级别：** P1
- **分类：** 根仓库 / 包发现边界 / 集成可复现性
- **证据：**
  - `workspace.excluded_packages:1-17` 声明 13 个排除包；
  - `Scripts/README.md:105-122` 声明这些源码仅作历史参考，不恢复或构建；
  - `Scripts/installation/uav_px4_dds_install.sh:492-543` 只检查 4 个 required package，
    不检查 forbidden/unmanaged package；
  - `Scripts/README.md:138-143` 给出的通用 `colcon build --symlink-install` 没有
    `--packages-skip`；
  - `find src -name COLCON_IGNORE -print` 仅在 `test_mavros` 等非根排除位置发现标记；
  - `colcon list --base-paths src` 实际发现 12 个排除包：`offboard_py`、
    `cv_yolo_paddle_pkg`、`opencv_cpp`、`mavlink`、`libmavconn`、`mavros`、
    `mavros_extras`、`mavros_msgs`、`vision_to_mavros`、`px4_bringup`、`serial`、
    `serial_driver`。
- **现象：** manifest 声称的 DDS-only 源码边界没有在物理工作区或 colcon discovery
  层强制执行；`verify-only` 仍报告 15 个 lock 条目 verified。
- **实际结果：** 默认 colcon crawl 返回 0 并包含 MAVROS、旧 bringup 和旧 serial 包。
- **预期结果：** DDS-only baseline 的默认 discovery 只包含允许包；任何 forbidden
  包出现时验证必须非零退出。
- **影响：** 本机全量构建集合与空白 lock 恢复集合不同；旧控制链可能被意外构建或
  后续 launch 引用，破坏 DDS-only 架构边界。
- **触发条件：** 在当前根目录执行未带严格 allowlist/skip 的 `colcon list/build`。
- **建议修复：** 在不删除历史源码的前提下，将归档源码移出 active `src/`，或为每个
  排除根增加可审计的发现屏障；把安装脚本 package check 改为 managed allowlist +
  forbidden denylist，release/CI 强制 `--require-colcon`。
- **验收标准：**
  - 13 个 excluded package 均不能被 production workspace 的 `colcon list` 发现；
  - 任一 excluded/unmanaged package 注入 active `src/` 后检查非零退出；
  - DDS-only 全量 build plan 不含 MAVROS、旧 bringup、mock/旧 serial；
  - 空白恢复与当前受管工作区包名集合完全一致。
- **依赖项：** 控制权 profile/CI 设计；处置历史源码前需维护者确认保留位置。
- **预计工作量：** M
- **是否阻塞 production：** 是

### BBF-DEP-002 — 四个受管 dirty checkout 的有效文件树未进入可复现基线

- **级别：** P1
- **分类：** 外部依赖仓库 / 本地修改溯源
- **证据：**
  - `README.md:47-60` 和 `docs/handoff.md:42-56` 记录四个既有 dirty checkout；
  - `workspace.lock.repos:20-23,28-31,36-39,56-59` 仅锁定上游 commit；
  - `git -C src/librealsense diff --summary`：3347 个 `100644 => 100755` mode change；
  - `git -C src/navigation_msgs diff --shortstat`：删除 `map_msgs` 13 文件/152 行；
  - `git -C src/realsense-ros status --short`：98 个 mode change，未跟踪
    `realsense2_camera/launch/rs_t265_launch.py`；
  - `git -C src/vision_opencv diff --shortstat`：删除 `image_geometry` 17 文件/3411 行；
  - lock `--verify-only` 实际为 `verified=15 blockers=4`、退出 1。
- **现象：** HEAD 精确匹配不等于当前文件树可复现。部分差异像文件权限污染，部分是
  ROS 包裁剪，另有一个可能承载集成功能的未跟踪 T265 launch；仓库内没有各差异的
  patch/hash、来源、维护者、用途和丢弃策略。
- **实际结果：** 新环境按 lock 恢复会重新出现 `map_msgs`、`image_geometry`，且不会
  得到本地 T265 launch；当前 workspace package/launch 集合随之变化。
- **预期结果：** 当前所依赖的每个有效差异都有可追溯派生提交或 patch+SHA，纯权限
  噪声与功能差异分离；干净恢复得到同一文件树和包发现结果。
- **影响：** 传感器、视觉依赖和 ROS 包闭包无法从空白环境复现，现有构建证据不能
  自动代表 lock 的干净恢复结果。
- **触发条件：** 新机恢复、CI checkout、开发者误把 `verified=15` 当作完整文件树证明。
- **建议修复：** 保持现有 checkout 不动，先为四仓库生成只读差异分类/内容散列；
  将真正需要的差异发布到受管 fork/commit 或版本化 patch；将文件模式异常单独归因；
  再由维护者决定历史裁剪的可复现方式。
- **验收标准：**
  - 四仓库每个差异都有“保留/舍弃/权限噪声”分类和负责人；
  - 功能差异可由锁定资产无交互重放且 hash 一致；
  - 干净恢复和当前目标基线的 `colcon list`、launch 文件及关键内容 hash 一致；
  - 正式 verify 不再依赖未解释的 dirty checkout。
- **依赖项：** BBF-DEP-001；感知 owner 对 T265 launch 的权威性判定。
- **预计工作量：** L
- **是否阻塞 production：** 是

### BBF-DEP-003 — PX4 firmware source、递归 submodule 与交叉工具链不在锁中

- **级别：** P1
- **分类：** 根仓库 / 固件依赖 / 空白恢复
- **证据：**
  - `workspace.lock.repos:1-63` 的 15 项不含 PX4-Autopilot；
  - `git ls-files` 不含 PX4 source/toolchain/container lock；
  - `docs/handoff.md:110-112` 明确缺 `.px4` artifact SHA、原构建目录 clean/patch/
    submodule 证据；
  - `docs/handoff.md:230-240` 把
    `PX4-Autopilot v1.16.2@54f0455ffcd755534539a7cf33a09a20bf71d29d`、递归
    submodule、工具链和 artifact SHA 列为下一步；
  - `docs/handoff.md:247-249` 明确当前本机缺 PX4 source、交叉编译器和 SITL 工具。
- **现象：** companion 侧消息/Agent 已锁定，但生产所需定制 `rc_channels` firmware
  的源码闭包与工具链完全不受当前 manifest 管理。
- **实际结果：** `uav_px4_dds_install.sh` 可恢复 15 个 companion 仓库，却不能从空白
  环境重建或静态验证目标 PX4 firmware profile。
- **预期结果：** PX4 commit、递归 submodule、patch/profile、生成器与编译器版本均有
  机器可读锁和可审计 artifact receipt。
- **影响：** 无法证明 `.px4` artifact 对应审查过的 DDS topic 契约；`rc_channels`
  firmware profile 和 FMUv3 构建闭环被阻断。
- **触发条件：** 固件 profile 开发、SITL、FMUv3 release build 或灾难恢复。
- **建议修复：** 在隔离的固件工作流中锁定 PX4 commit/递归 submodule/toolchain，
  保存最小 `dds_topics.yaml` patch、生成物检查、build log、flash/RAM 余量和 `.px4`
  SHA-256；本阶段不刷写。
- **验收标准：**
  - 机器可读清单固定 PX4 HEAD 与全部递归 submodule HEAD；
  - 固定 OS/架构、CMake/Ninja/Python 和 `arm-none-eabi-*`/容器 digest；
  - 空白隔离环境两次构建得到已解释的可重复 artifact hash；
  - patch 只增加批准的 DDS publication，静态生成、SITL 后才允许 FMUv3 构建；
  - 所有流程不依赖当前飞控参数快照。
- **依赖项：** PX4 DDS contract 审查结论；BBF-DEP-007。
- **预计工作量：** XL
- **是否阻塞 production：** 是

### BBF-DEP-004 — 根仓库含无 `.gitmodules` 映射的历史 gitlink

- **级别：** P2
- **分类：** 根仓库 / Git 嵌套关系
- **证据：**
  - 根索引：`src/serial_driver_ros` 为 mode `160000`、object
    `87f3907f0b3b906d474a8d1e1dc9677ab0c4298f`；
  - 根 HEAD 不存在 `.gitmodules`；
  - `workspace.excluded_packages:16-17` 把 `serial`/`serial_driver` 明确排除；
  - `git submodule status --recursive` 实际退出 128：
    `no submodule mapping found in .gitmodules for path 'src/serial_driver_ros'`。
- **现象：** 历史 serial gitlink 留在根 Git tree，但没有 URL/path mapping；当前目录为空。
- **实际结果：** 统一 submodule 状态命令失败，空白 checkout 无法解释或初始化该对象。
- **预期结果：** 根 Git tree 不含已排除的悬空 gitlink；若确需 submodule，则必须有
  完整 `.gitmodules`、origin、commit 和生命周期说明。
- **影响：** 仓库健康检查和灾难恢复产生歧义；未来加入 PX4 submodule 后可能掩盖真正
  的 submodule blocker。
- **触发条件：** `git submodule status/update --recursive`、新机 checkout 或审计脚本。
- **建议修复：** 经维护者确认后，在后续实施轮从根索引清理这个已排除 gitlink并记录
  历史来源；不要在本轮删除本地目录。
- **验收标准：**
  - `git submodule status --recursive` 返回 0；
  - 根 tree 的所有 mode-160000 条目均有有效 `.gitmodules` 映射；
  - excluded serial 不进入 active source/package discovery。
- **依赖项：** BBF-DEP-001；历史源码保留决策。
- **预计工作量：** S
- **是否阻塞 production：** 否（前提是 serial 持续被严格排除）

### BBF-DEP-005 — detached HEAD 策略与当前受管 checkout 状态不一致

- **级别：** P2
- **分类：** 外部依赖仓库 / Git 策略
- **证据：**
  - `README.md:76-78`、`Scripts/README.md:27-30` 声明精确恢复为 detached HEAD；
  - 安装脚本输出固定显示 `Checkout: detached HEAD`
    （`uav_px4_dds_install.sh:293-297`）；
  - 脚本在已有 HEAD 匹配时直接成功，不检查 symbolic ref
    （`uav_px4_dds_install.sh:449-462`）；
  - 实测 15 个 lock checkout 中 10 个仍在本地分支，只有 5 个 detached。
- **现象：** 内容 SHA 正确，但状态策略没有被 verify-only 强制，输出文字会使操作者
  误以为当前全部 detached。
- **实际结果：** `gazebo_ros_pkgs`、`imu_tools`、`navigation2`、`navigation_msgs`、
  `offboard_cpp`、`rplidar_ros`、`rtabmap`、`rtabmap_ros`、`slam_toolbox`、
  `vision_opencv` 均在分支。
- **预期结果：** 要么验证部署 checkout 必须 detached，要么文档明确“新恢复 detached，
  已有 checkout 只验证 commit”，并在 receipt 中记录差异。
- **影响：** 开发者可能在受管依赖分支上意外提交/移动 HEAD；后续 verify 才会发现，
  不符合统一部署状态承诺。
- **触发条件：** 在现有工作区继续开发、运行依赖更新或把脚本输出作为部署证明。
- **建议修复：** 将策略拆为 developer checkout 与 immutable deployment checkout；
  verify 输出实际 branch/detached 状态，release profile 对非 detached 设 blocker。
- **验收标准：**
  - 每个 lock 项的 branch/detached 状态进入机器可读 receipt；
  - release/CI 恢复的 15 项全部 detached；
  - 开发 checkout 若允许分支，文档和命令输出不再宣称其 detached。
- **依赖项：** 发布 profile 定义。
- **预计工作量：** S
- **是否阻塞 production：** 否（精确 HEAD 已匹配，但 release 前应完成）

### BBF-DEP-006 — moving communication 依赖缺失且没有实验 HEAD receipt 机制

- **级别：** P2
- **分类：** 外部 moving dependency / 实验溯源
- **证据：**
  - `workspace.lock.repos:1-2` 明确省略 `../communication`；
  - `workspace.repos:62-65` 固定路径/origin，但 ref 为 `main`；
  - `Scripts/README.md:81-83` 要求每次实验或发布单独记录实际 HEAD；
  - `--manifest workspace.repos --allow-moving-refs --verify-only` 实际报告
    `/home/c/communication` missing，汇总 `blockers=5`、退出 1；
  - 根受管文件中没有 communication experiment receipt/schema。
- **现象：** moving 选择是明确决策，但“如何记录实际 HEAD”只存在文字要求；当前本机
  连该 checkout 都不存在。
- **实际结果：** 依赖它的 MCU/串口集成不能在当前 workspace 验证，也不能重放某次实验。
- **预期结果：** 每次纳入实验的 moving dependency 有 origin、HEAD、dirty、时间和调用
  工程 HEAD 的不可变 receipt；缺失时相关 profile fail-closed。
- **影响：** 将来串口/MCU 实验无法精确回放，主仓库 lock 无法说明实际参与代码。
- **触发条件：** 启用 communication 的集成 profile 或引用其源码。
- **建议修复：** 保留 moving 主线意图，但增加实验锁快照/receipt 生成与验证；缺失
  checkout 时非 communication profile 可明确标为 not-applicable，而相关 profile 必须失败。
- **验收标准：**
  - receipt 含 root HEAD、communication origin/HEAD/dirty/timestamp；
  - 同一 receipt 可恢复精确实验 checkout；
  - 未提供 receipt 时 communication 集成测试和 release 拒绝运行。
- **依赖项：** communication 接口/profile 定义。
- **预计工作量：** M
- **是否阻塞 production：** 否（ADR 当前禁止其进入飞控控制链）

### BBF-DEP-007 — 空白恢复只锁源码，不锁 ROS/system/toolchain 依赖

- **级别：** P2
- **分类：** 根仓库 / 环境可复现性
- **证据：**
  - `README.md:29-32` 和 `Scripts/README.md:27-30` 明确安装脚本不安装 ROS、系统包、
    udev 或 firmware；
  - `Scripts/README.md:136-144` 仅要求环境预先具备 Ubuntu 20.04、ROS 2 Foxy，并运行
    `rosdep check`/colcon；
  - 根 `git ls-files` 不含 rosdep lock、apt snapshot、Python lock、Dockerfile/container
    digest 或 toolchain lock；
  - `uav_px4_dds_install.sh:508-527` 在 colcon 不存在/失败时默认只警告并可继续成功；
  - `docs/evidence/OFFBOARD_PX4_MSGS_COMPAT_20260724.md:174-176` 只记录使用“system ROS 2
    Foxy Fast DDS/Fast CDR/spdlog”，没有精确软件包版本。
- **现象：** 精确 Git lock 被表述为可复现恢复，但构建所需的系统依赖解析仍受当前 apt/
  rosdep 环境影响。
- **实际结果：** 本轮只能证明 15 个源码 HEAD；从空白 Ubuntu 恢复到相同可构建二进制
  未验证，也没有足够锁信息执行。
- **预期结果：** 源码 lock 与 OS/arch、ROS repo snapshot、apt/rosdep resolution、
  Python/CMake/compiler 版本共同形成环境锁。
- **影响：** 相同源码可能因系统依赖漂移出现不同编译、QoS/runtime ABI 或不可构建结果。
- **触发条件：** 新主机、CI runner、系统升级、灾难恢复。
- **建议修复：** 增加机器可读环境 inventory 和可重建环境（固定仓库 snapshot 或
  container digest），保存 rosdep resolution；把 release 恢复设置为
  `--require-colcon` 并校验工具版本。
- **验收标准：**
  - 环境锁包含 OS/arch、ROS distro/repository snapshot、apt 包版本、Python/CMake/
    compiler/colcon 版本；
  - 两个空白隔离环境恢复相同源码和依赖版本；
  - 核心包 build/test 结果及关键二进制 hash/ABI receipt 可比较；
  - 缺工具或 package discovery 失败时 release 恢复非零退出。
- **依赖项：** BBF-DEP-003；CI 基础设施。
- **预计工作量：** L
- **是否阻塞 production：** 是

### BBF-DEP-008 — 恢复流程缺少中断重入与半成品清理的自动化证明

- **级别：** P2
- **分类：** 根仓库 / 恢复脚本可靠性
- **证据：**
  - 新仓库流程依次执行 `mkdir`、`git init`、`remote add`、fetch、checkout、submodule
    （`uav_px4_dds_install.sh:409-430`）；
  - 15 项串行执行，没有事务/receipt（第 546-549 行）；
  - 已存在 `.git` 后直接执行未包装的 `git rev-parse HEAD`
    （第 449 行），对“init 成功但首次 fetch/checkout 失败”的无 HEAD 半成品没有专门路径；
  - `Scripts/README.md:55-65` 声明已有仓库规则，但没有中断/重入测试证据。
- **现象：** 正常已有 checkout 的 fail-closed 已实测；网络中断、磁盘满、fetch 后
  checkout 前失败和再次运行的行为没有自动化覆盖。
- **实际结果：** 因本轮禁止联网/clone，故障重入未执行；静态流程显示失败可能留下
  `.git` 半成品，下一次运行未必给出可恢复的分类诊断。
- **预期结果：** 每个步骤可幂等重入，半成品有明确状态和安全恢复指导，不依赖人工删除。
- **影响：** 空白恢复可能在第 N 个仓库失败后留下混合状态；操作者难以区分安全重试与
  需要隔离目录重建。
- **触发条件：** clone/fetch/submodule 中断或磁盘/网络故障。
- **建议修复：** 用离线 fixture/bare remotes 建立恢复脚本测试，覆盖每个中断点、无
  HEAD repo、错误 origin、dirty、错误 SHA、submodule 缺失和重复运行；输出每仓库 receipt。
- **验收标准：**
  - 所有故障点均非零、无现有 checkout 被覆盖；
  - 对脚本创建的半成品再次运行可安全完成或给出明确可执行诊断；
  - 连续运行两次得到相同 HEAD/状态，第二次无写入；
  - 测试完全离线且不访问真实 workspace。
- **依赖项：** 测试 fixture/CI。
- **预计工作量：** M
- **是否阻塞 production：** 否（但阻塞可宣称灾难恢复已验证）

### BBF-DEP-009 — 依赖许可证、维护状态和弃用信息未形成统一清单

- **级别：** P2
- **分类：** 根仓库 / 供应链治理
- **证据：**
  - `workspace.lock.repos` 每项只有 path/type/url/version，无 license、owner、
    maintenance/deprecation 字段；
  - 根仓库不存在 `LICENSE`、NOTICE、SBOM 或第三方依赖清单；
  - 多数依赖自身有 LICENSE/package license，但
    `src/vision_to_dds/package.xml:8` 仍为 `TODO: License declaration`；
  - 当前锁提交日期跨 2019-2026；这些日期只是本地 commit 元数据，不能证明上游仍维护。
- **现象：** 来源 URL 和 SHA 完整，但发布许可、维护责任、Foxy/EOL 风险、fork/patch
  策略与弃用计划没有聚合；上游当前维护状态因本轮禁网未验证。
- **实际结果：** 可以定位源码来源，不能从根仓库判断每个依赖能否分发、谁负责安全
  更新或何时替换。
- **预期结果：** 每个受管/例外依赖均有 SPDX license、来源、owner、维护状态、EOL/
  deprecation 和替代计划，且与 lock SHA 关联。
- **影响：** release 合规和长期维护决策无法自动审计；`vision_to_dds` 的 TODO license
  可能阻碍合法分发。
- **触发条件：** 对外发布、production 镜像制作、安全更新或依赖升级。
- **建议修复：** 增加第三方 inventory/SBOM，补齐自有/派生包 license，记录 ROS 2
  Foxy 和旧感知依赖的维护/替代计划；联网核验在后续获准时完成并留证。
- **验收标准：**
  - 15 个 lock 仓库、communication 和历史例外均有 SPDX/来源/owner/status；
  - 所有受管 package.xml 无 TODO license；
  - release artifact 自动生成 SBOM 并与 root HEAD/lock hash 关联；
  - 无 license 或 EOL 处置未批准时 release gate 失败。
- **依赖项：** 项目治理/法务策略。
- **预计工作量：** M
- **是否阻塞 production：** 否（阻塞正式对外发布）

## 5. 分级统计与 production 阻塞项

| 等级 | 数量 | IDs |
|---|---:|---|
| P0 | 0 | — |
| P1 | 3 | `BBF-DEP-001`、`BBF-DEP-002`、`BBF-DEP-003` |
| P2 | 6 | `BBF-DEP-004` 至 `BBF-DEP-009` |
| P3 | 0 | — |

本模块明确的 production 阻塞项：

1. `BBF-DEP-001`：DDS-only 包发现边界未强制；
2. `BBF-DEP-002`：当前有效依赖文件树不能由 lock 重建；
3. `BBF-DEP-003`：PX4 firmware source/submodule/toolchain 未锁；
4. `BBF-DEP-007`：完整构建环境未锁，不能宣称空白恢复可复现。

## 6. 已实现、部分实现、未验证

| 能力 | 状态 | 说明 |
|---|---|---|
| 根仓库身份 | 已实现并验证 | origin、branch、HEAD、根 status 已核对 |
| 15 项源码 SHA/origin lock | 已实现并验证 | 全部 path/origin/HEAD 匹配 |
| 已有 dirty checkout fail-closed | 已实现并验证 | 完整遍历、4 blockers、退出 1 |
| unsafe manifest path/重复 target 拒绝 | 已实现（静态检查） | 脚本有明确检查 |
| moving ref 显式授权 | 已实现并验证 | 不带 allow 默认拒绝；维护 verify 显示 communication 缺失 |
| active ROS 包 allowlist | 完全缺失 | 12 个 excluded 包仍被发现 |
| 当前 dirty 文件树复现 | 完全缺失 | 无 patch/派生 SHA/receipt |
| PX4 firmware 源码闭包 | 完全缺失 | 文档也明确为下一阶段 |
| 系统/ROS/toolchain lock | 完全缺失 | 仅有平台文字要求 |
| detached deployment 状态 | 部分实现 | 新 clone/update 会 detached，已有匹配分支被接受 |
| submodule 完整性审计 | 未实现 | 根 gitlink 使 status 失败；verify-only 不检查依赖 submodule |
| 空白联网恢复 | 未验证 | 本轮禁止联网、clone、fetch |
| 重复恢复/故障注入 | 未验证 | 没有离线 fixture 证据 |
| 上游维护/弃用状态 | 未验证 | 本轮禁止联网，不以本地 commit 日期替代 |

## 7. 建议最短依赖关键路径

1. 先完成 `BBF-DEP-001`：建立 active source/package allowlist，隔离历史控制包。
2. 并行分类四个 dirty checkout；随后完成 `BBF-DEP-002` 的 patch/fork/receipt。
3. 建立环境 inventory（`BBF-DEP-007`），作为 PX4 工具链锁的前置。
4. 完成 `BBF-DEP-003` 的 PX4 source/submodule/toolchain/profile lock。
5. 用全新隔离路径执行两次恢复、包发现、构建和 hash 对比；只有此后才能宣称可复现。

## 8. 本次实际命令与限制

执行的主要只读命令包括：

```text
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git rev-parse HEAD
git status --short/--branch
git ls-files / git ls-tree / git show
git -C <repo> remote get-url origin
git -C <repo> rev-parse HEAD
git -C <repo> symbolic-ref --short -q HEAD
git -C <repo> status --porcelain/--short
git -C <repo> diff --shortstat/--summary
git submodule status --recursive
find / grep / sed / awk / nl / wc / file / stat
bash -n Scripts/installation/uav_px4_dds_install.sh
bash Scripts/installation/uav_px4_dds_install.sh --verify-only --skip-package-check
bash Scripts/installation/uav_px4_dds_install.sh \
  --manifest workspace.repos --allow-moving-refs --verify-only --skip-package-check
colcon list --base-paths src
```

没有运行 clone/fetch/submodule update、安装、构建、测试、ROS node/launch、硬件端口、
PX4 参数/固件/Git 写操作。`colcon list` 的隐式 `log/` 写入已在第 2.3 节如实披露。
