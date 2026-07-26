# Repository Cleanup Wave 2 审计

日期：2026-07-26
性质：静态仓库清理；不授权运行节点、SITL 或硬件。
事实截止：本报告起草时的 `agent/repository-cleanup-wave2` 工作树；最终文件清单和
验证结果分别以
[`31_CLEANUP_CHANGELOG.md`](31_CLEANUP_CHANGELOG.md) 和
[`32_POST_CLEANUP_VALIDATION.md`](32_POST_CLEANUP_VALIDATION.md) 的协调线程终稿
为准。

## 1. 基线 identity

| 字段 | Wave 2 起始事实 |
|---|---|
| root HEAD | `0a7f90dad0942843c989a9bed6333a88f9b31ca5` |
| 起始 branch | `master...origin/master` |
| 执行 branch | `agent/repository-cleanup-wave2` |
| origin | `https://github.com/BoomBoomFly/BoomBoomFly.git` |
| root 起始 status | 唯一条目：` m src/serial_driver_ros` |
| mode `160000` | `src/serial_driver_ros` → `87f3907f0b3b906d474a8d1e1dc9677ab0c4298f` |
| `.gitmodules` | 不存在 |
| 网络/硬件 | 未 fetch/pull；未访问硬件；未启动节点/launch |

起始 tracked empty files：

- `Scripts/installation/car_install.sh`
- `Scripts/simulation/uav_sim.sh`
- `Simulator/gazebo_simulator/README.md`
- `Simulator/realsense_gazebo_plugin/README.md`

其他删除候选并非空文件：

- `Scripts/build/m1_build.sh` 是 287 行旧 T265 + D435 + MAVROS 构建入口；
- `Simulator/README.md` 是占位说明；
- `Simulator/` 下其余两个 README 是空占位。

## 2. 受保护的起始 dirty 状态

| 路径 | HEAD/origin | 起始 dirty 摘要 | 本轮处置 |
|---|---|---|---|
| `src/mavlink` | `22b62f8…` / `mavlink-gbp-release` | 2 个 untracked `__pycache__` 目录 | 保留，不清理 |
| `src/mavros` | `48b53cc…` / `mavlink/mavros` | 26 个 tracked modified，属于旧本地补丁 | 保留，不修改/reset/clean |
| `src/serial_driver_ros` | `87f3907…` / `BoomBoomFly/serial_driver_ros` | 6 个 tracked modified + 3 个 untracked entries | 保留，`REQUIRES_MAINTAINER_DECISION` |
| `../communication` | `df256c1…` / `wanone111/communication` | 3 tracked deleted + 1 modified + 4 untracked entries | 保留；不把 untracked ROS 2 serial 目录当可复现替代 |

创建执行分支后，根工作树仍只通过 dirty gitlink 反映
`src/serial_driver_ros`；嵌套仓库必须逐一审计，不能把根 status 当作整个 workspace
clean。

## 3. 删除候选与决定

| 候选 | 引用/内容判断 | 决定 |
|---|---|---|
| `Scripts/build/m1_build.sh` | 旧 T265 + D435 + MAVROS 构建路线，引用已不存在的旧 patch；不是 DDS-only 入口 | 删除 |
| `Scripts/installation/car_install.sh` | tracked empty，无实现 | 删除 |
| `Scripts/simulation/uav_sim.sh` | tracked empty，无实现 | 删除 |
| `Simulator/README.md` | 仅占位说明，无 orchestration | 删除 |
| `Simulator/gazebo_simulator/README.md` | tracked empty | 删除 |
| `Simulator/realsense_gazebo_plugin/README.md` | tracked empty | 删除 |
| `src/serial_driver_ros` gitlink | manifest/profile/引用层面是 orphan，但包含受保护 dirty 变更，且替代来源未固化 | 保留；维护者决策 |
| `src/px4_bringup` provenance | forbidden/excluded 的历史 MAVROS bringup，但保留精确来源有审计价值 | 本轮保留；只提出 archive migration |
| dated audits/evidence/receipts/schemas/历史参数快照 | 不可变审计与原始 evidence | 保留，不批量重写 |

实际删除的 tracked 文件是：

```text
Scripts/build/m1_build.sh
Scripts/installation/car_install.sh
Scripts/simulation/uav_sim.sh
Simulator/README.md
Simulator/gazebo_simulator/README.md
Simulator/realsense_gazebo_plugin/README.md
```

未来仿真入口只应进入正式 SITL orchestration、runbook、scenario 和 test 目录；不恢复
空 `Simulator/` 或旧 shell 入口。

## 4. Manifest 与 package boundary

### 4.1 一致性事实

- `workspace.lock.repos`：16 个条目，全部是 40 位 exact SHA。
- `workspace.repos`：相同的 16 个 `src/` 条目，另有 moving
  `../communication@main`。
- 两份 manifest 的共同路径 origin URL 一致。
- `config/profiles/dds_only_packages.yaml`：3 production、13 forbidden、67 managed
  non-production packages。
- `workspace.excluded_packages` 的 13 个有效条目与 forbidden set 精确一致；本轮只把
  旧 “T265 + D435 baseline” 头注释改成 authoritative DDS-only boundary。
- profile 同时把 forbidden `serial_driver` 的实际路径修正为
  `src/serial_driver_ros`，并补分类 `image_geometry`、`map_msgs`，防止完整 package
  discovery 把它们报告为 unknown。

### 4.2 Source 分类

| 分类 | repositories |
|---|---|
| production required | `px4_msgs`、`offboard_cpp`、`vision_to_dds` |
| production transport runtime support | `Micro-XRCE-DDS-Agent`；不是 production ROS package allowlist 的扩张 |
| build/test only | `gazebo_ros_pkgs` |
| optional perception/navigation | `imu_tools`、`librealsense`、`navigation2`、`navigation_msgs`、`realsense-ros`、`rplidar_ros`、`rtabmap`、`rtabmap_ros`、`slam_toolbox`、`vision_opencv` |
| archived provenance | `px4_bringup` |
| moving external dependency | `../communication@main` |
| orphan/unreferenced | `src/serial_driver_ros` gitlink；保留待决策 |

默认 exact lock 仍恢复 optional perception/navigation source，虽然它们不进入
production package allowlist。后续应做显式 source profile 拆分，而不是盲目删除
上游源码。

### 4.3 `px4_bringup` archive 建议

本轮没有执行迁移。最小后续方案是：

1. 新建 exact-SHA `workspace.archive.repos`，只保存
   `px4_bringup@0fbdcbf6ee53d6927de75af1d98f22cf5bd4f917`。
2. 从 active lock/moving intent manifests 移除该路径，但继续保留 package
   forbidden/excluded。
3. installer 增加显式、默认不启用的 archive manifest 参数；archive moving ref 和
   active/archive duplicate 必须 fail closed。
4. 更新 manifest/profile/receipt validators、负向 tests 和当前文档。

完整设计见
[`21_WAVE2_DEPENDENCY_MANIFEST_REVIEW.md`](21_WAVE2_DEPENDENCY_MANIFEST_REVIEW.md)。

## 5. 异常 gitlink

`src/serial_driver_ros` 的证据：

- 根索引是 mode `160000`，但根无 `.gitmodules`；
- `git cat-file -t HEAD:src/serial_driver_ros` 返回 128，根 object database 无法解析
  该 object；
- 不在 `workspace.lock.repos` 或 `workspace.repos`；
- package `serial_driver` 是 forbidden，不在 production allowlist；
- 没有当前 root build、launch、test 或 production 活动入口引用；
- nested checkout 的 HEAD 与 gitlink hash 一致，但含 6 tracked modified 和 3
  untracked entries；
- `../communication` 虽是候选替代来源，其 checkout 也 dirty，ROS 2 serial
  替代目录当前未跟踪，不能由记录的 HEAD 重建。

结论：

```text
src/serial_driver_ros: REQUIRES_MAINTAINER_DECISION
```

维护者必须先决定 dirty 变更归属、生成/批准 receipt 或迁入明确仓库，并把
`../communication` 替代实现固化为可审计 commit；之后才能批准删除 gitlink。

## 6. 文档漂移

| 漂移 | Wave 2 处置 |
|---|---|
| 根 README 复制主机路径、临时 branch/commit/device/blocker | 改成稳定的项目、版本、uXRCE-DDS-only、安全边界和 canonical 入口 |
| `Scripts/README.md` 仍说明旧 MAVROS build、空 car/simulation 脚本和旧 clone URL | 改写为当前 build/evidence/installation/test/SITL 入口 |
| handoff 含个人绝对路径和易漂移当前状态 | 改为动态 `git rev-parse --show-toplevel` 与临时导航语义 |
| 文档权威边界不够清楚 | `DOCUMENT_AUTHORITY.md` 区分 ADR、architecture/matrix、handoff、planning、dated audit/evidence 和 corrections/supersedes |
| 历史感知审计引用不存在 ADR 和参数快照路径 | 新增 `CORRECTIONS.md`；原日期化审计不回写 |
| 根 `CODEOWNERS.draft` 使用占位角色且包含不存在/外部 checkout 路径 | 已迁移为 `docs/governance/CODEOWNERS_PROPOSAL.md`，保持 **DO NOT ENABLE**；有效 CODEOWNERS 仍需真实 owner 决策 |

起草时对 current README、Scripts README、handoff、governance 和 planning 的扫描未发现
个人固定 workspace 路径或旧删除入口。历史审计中仍可能出现旧路径，属于
`HISTORICAL_EVIDENCE`，应由 corrections/supersedes 解释，不能直接改写。

## 7. 风险与维护者决策

| 项目 | 状态 | 所需决策/动作 |
|---|---|---|
| serial gitlink 与 dirty patch | `REQUIRES_MAINTAINER_DECISION` | 确定归属、receipt/迁移，然后决定 gitlink 删除 |
| `../communication` moving dirty source | `BLOCKED` for related release | 固化 exact commit/content/用途/批准 receipt |
| `px4_bringup` 默认恢复 | `PLANNED` | 批准 archive manifest 迁移和 validator/test 方案 |
| optional perception/navigation 默认恢复 | `PLANNED` | 批准 source profile 拆分，不降低 package allowlist |
| CODEOWNERS | `BLOCKED` | 提供真实 GitHub user/team；不得启用占位 owner |
| CI required checks | `BLOCKED` | 固定 CI job graph后由管理员另行授权 ruleset |
| release/rollback | `BLOCKED` | 完成 source/dependency/toolchain/profile/artifact 与 rollback evidence |
| formal SITL | `BLOCKED` | A/B/C/D 软件门通过后才运行 |
| 拆桨台架/实机/刷写/飞行 | `BLOCKED` / 未授权 | 另行明确硬件与安全授权 |

## 8. 审计结论

旧 MAVROS/空占位入口已从 active tree 删除，当前入口和文档权威边界已朝
uXRCE-DDS-only 基线收敛。不可变 audits/evidence 被保留，错误历史引用通过勘误而非
篡改处理。依赖边界仍有三个 release hygiene 缺口：异常 dirty gitlink、moving
dependency receipt、archive/optional source profile。它们不应通过删除 dirty 内容或
放宽检查规避。

```text
PRODUCTION: BLOCKED
HARDWARE ACCESS: NOT AUTHORIZED
FIRMWARE FLASH: NOT AUTHORIZED
FLIGHT: NOT AUTHORIZED
```
