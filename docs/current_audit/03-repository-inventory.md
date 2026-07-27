# 当前仓库清单与提交漂移

Audit date: 2026-07-27T22:15:13+08:00  
Hostname: orinnano  
User: c  
Workspace: `/home/c/px4_ws`  
Repository: `/home/c/px4_ws/BoomBoomFly`  
Branch: `master`  
HEAD: `0ed9d148bfbfd22253142172bbfe93c51106fdfa`  
PX4 target version: v1.16.2  
ROS distribution: Foxy  
Hardware accessed: NO  
SITL run: NO  
Files modified outside docs/current_audit: YES — colcon logs; nested Git index metadata refreshed by status; root FETCH_HEAD changed concurrently/unattributed; no source/config/existing-doc change

## 结论

`/home/c/px4_ws` 不是 Git 仓库。共发现 59 个 Git worktree：BoomBoomFly 树内
23 个，`external/PX4-Autopilot` 根仓库及递归子模块 36 个。没有额外 linked
worktree。

根 HEAD 与 Wave 3B final 相同，但分支从历史
`agent/wave3b-integration-gates` 变为 `master`，历史工作分支本地 ref 已不存在。
根工作树不干净：

```text
## master...origin/master
 D src/serial_driver_ros
?? src/communication/
```

## 主要仓库

| 路径 | 分支 | HEAD | 文档记录 HEAD | 漂移状态 | 工作区状态 |
|---|---|---|---|---|---|
| `BoomBoomFly` | `master` | `0ed9d148bfbfd22253142172bbfe93c51106fdfa` | Wave 3B final 同值；文档分支为 `agent/wave3b-integration-gates` | HEAD 相同、分支已变 | dirty：删除 gitlink、未跟踪 communication |
| `BoomBoomFly/src/offboard_cpp` | `agent/wave3b-offboard-integration` | `976d6217d73a28b72e64300e2dd04bcbeeee30d7` | Wave 3B final 同值；root lock 为 `cded3dc5b6906420db3767abd82b2df7ba6ea9f0` | final 相同；比 lock 后代 2 commits | clean；无 upstream |
| `BoomBoomFly/src/px4_msgs` | detached | `392e831c1f659429ca83902e66820d7094591410` | 同值、tag `v1.16.2` | 相同 | clean |
| `external/PX4-Autopilot` | detached | `54f0455ffcd755534539a7cf33a09a20bf71d29d` | Wave 3B 仅称其为未验证候选且源码缺失 | 新增可验证 checkout；未纳入治理 lock | clean、shallow、35 个递归子模块均初始化/clean |
| `BoomBoomFly/src/communication` | `main` | `df256c180dbd4167f879b697e38d547521f1f8e2` | Wave 3B 称 communication absent | 新增、路径/origin 与 manifest 不一致 | dirty：3 deleted、1 untracked nested repo |
| `BoomBoomFly/src/communication/Serial/serial_driver_ros` | `master` | `87f3907f0b3b906d474a8d1e1dc9677ab0c4298f` | 旧根 gitlink 指向同一 SHA | 新路径；未被 root/profile 跟踪 | clean |
| `BoomBoomFly/src/serial_driver_ros` | — | — | gitlink `87f3907f...` | checkout 已缺失 | root 记录 deleted |
| `BoomBoomFly/src/serial_driver_ros2` | — | — | `main@8614989c...`，历史 protected dirty | 当前路径缺失 | `NOT_VERIFIED`，不得推断迁移完成 |

## BoomBoomFly 树内完整仓库账本

| 相对路径 | 分支/HEAD | Upstream | 当前状态 |
|---|---|---|---|
| `.` | `master@0ed9d148` | `origin/master` | dirty：1 deleted gitlink、1 untracked dir |
| `src/Micro-XRCE-DDS-Agent` | detached `57d08621` | — | clean |
| `src/communication` | `main@df256c18` | `origin/main` | dirty：3 deleted、1 untracked dir |
| `src/communication/Serial/serial_driver_ros` | `master@87f3907f` | `origin/master` | clean |
| `src/gazebo_ros_pkgs` | `foxy@b6f7bf12` | `origin/foxy` | clean |
| `src/imu_tools` | `foxy@d28555e4` | `origin/foxy` | clean |
| `src/librealsense` | detached `c94410a4` | — | dirty：3347 mode-only |
| `src/mavlink` | detached `22b62f8d` | — | dirty：233 mode-only、2 `__pycache__` |
| `src/navigation2` | `foxy-devel@ca482808` | `origin/foxy-devel` | clean |
| `src/navigation_msgs` | `foxy@fe880e99` | `origin/foxy` | dirty：13 deleted |
| `src/offboard_cpp` | `agent/wave3b-offboard-integration@976d6217` | — | clean |
| `src/offboard_py` | `master@38887f08` | `origin/master` | clean |
| `src/px4_bringup` | `DDS@0fbdcbf6` | `origin/DDS` | clean |
| `src/px4_msgs` | detached `392e831c` | — | clean |
| `src/realsense-ros` | detached `8abb4657` | — | dirty：98 modified、1 untracked |
| `src/ros2_foxy_vision_to_mavros` | `main@3d395fdc` | `origin/main` | dirty：1 modified |
| `src/rplidar_ros` | `ros2@24cc9b6d` | `origin/ros2` | clean |
| `src/rtabmap` | `foxy-devel@0070de4a` | `origin/foxy-devel` | clean |
| `src/rtabmap_ros` | `foxy-devel@b341e2a7` | `origin/foxy-devel` | clean |
| `src/serial-ros2` | `master@ae46504a` | `origin/master` | clean |
| `src/slam_toolbox` | `foxy-devel@4786e90c` | `origin/foxy-devel` | clean |
| `src/vision_opencv` | `foxy@72152d9d` | `origin/foxy` | dirty：17 deleted |
| `src/vision_to_dds` | detached `0c3a0013` | — | clean |

有 upstream 的仓库仅按本地 remote-tracking refs 计算均为 ahead/behind `0/0`；
本轮未 fetch，不能解释为实时远端状态。BoomBoomFly 树内仓库均非 shallow。

## 历史提交关系

| 仓库 | 文档提交 | 与当前 HEAD 的关系 |
|---|---|---|
| Root | `afb4fdcecb22596056432492d1ad284919b065cd` | ancestor，落后 7 commits |
| Root | `0ed9d148bfbfd22253142172bbfe93c51106fdfa` | equal |
| Offboard | `c744757a2df467807af240e34188869af65c603e` | ancestor，落后 1 commit |
| Offboard | `976d6217d73a28b72e64300e2dd04bcbeeee30d7` | equal |
| Offboard root lock | `cded3dc5b6906420db3767abd82b2df7ba6ea9f0` | ancestor，落后 2 commits |
| px4_msgs | `392e831c1f659429ca83902e66820d7094591410` | equal |
| PX4-Autopilot intended candidate | `54f0455ffcd755534539a7cf33a09a20bf71d29d` | current exact HEAD/tag `v1.16.2` |

## PX4 source evidence

- origin：`https://github.com/PX4/PX4-Autopilot.git`
- root：detached、clean、shallow；
- `v1.16.2^{commit}` 与 HEAD 同为 `54f0455f...`；
- 35 个递归子模块均已初始化，`git submodule status --recursive` 无
  `-`、`+` 或 `U` 前缀；
- PX4 源码与 `px4_msgs@392e831c...` 的 226/226 个 `.msg` 文件逐文件完全一致；
- `dds_topics.yaml` 存在，但未包含 `/fmu/out/rc_channels`；
- checkout 未进入 `workspace*.repos` 或非模板 source/toolchain lock；
- `arm-none-eabi-gcc/g++` 未在 PATH 中发现。

因此历史“源码不存在”被当前事实取代，但“已批准、可重复恢复的
source/submodule/toolchain/board lock”仍未关闭。

## 路径与来源冲突

`workspace.repos` 仍声明 sibling `../communication`，当前实际却是 root 内未跟踪
`src/communication`；两者路径和 origin 均不一致。当前根包边界精确期望
`src/serial_driver_ros`，实际 `colcon` 发现
`src/communication/Serial/serial_driver_ros`。这是当前 H0/H1 阻塞项，不得通过
放宽 validator 消除。
