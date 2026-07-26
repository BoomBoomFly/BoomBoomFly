# Repository Cleanup Wave 2：依赖与 manifest 审查

日期：2026-07-26  
范围：`workspace.lock.repos`、`workspace.repos`、
`workspace.excluded_packages`、`config/profiles/dds_only_packages.yaml` 与
`src/serial_driver_ros` gitlink。  
操作边界：本报告不修改、清理、stash 或 checkout 任何嵌套 dirty 仓库，也不执行
archive manifest 迁移。

## 结论

- `workspace.lock.repos` 有 16 个精确 SHA 条目；`workspace.repos` 有相同的 16 个
  `src/` 条目，并额外声明 moving external dependency `../communication@main`。
- DDS-only package profile 有 3 个 production package、13 个 forbidden package 和
  67 个 managed non-production package。`workspace.excluded_packages` 的 13 个有效
  条目与 `forbidden_packages` 精确一致。
- 实际 workspace discovery 还发现先前未分类的 `image_geometry` 与 `map_msgs`；
  本轮将它们加入 managed non-production，而没有扩大 production allowlist。
- `serial_driver` 的 forbidden path 从不存在的 `src/serial_driver_ros2` 校正为
  当前 mode `160000` 路径 `src/serial_driver_ros`；其 forbidden 状态不变。
- 默认精确恢复仍会拉取 Navigation2、SLAM、RealSense、RPLIDAR 和视觉支持源码。
  它们不进入 production package allowlist，但恢复范围仍大于 production 最小源码集。
- `px4_bringup` 继续作为 build-excluded provenance 保留；本轮不删除、不迁移。
- `src/serial_driver_ros` 的处置结论是
  **`REQUIRES_MAINTAINER_DECISION`**。本轮不得删除该 gitlink。

## `src/serial_driver_ros` 证据

| 检查项 | 结果 |
|---|---|
| 根索引类型 | mode `160000` gitlink，object `87f3907f0b3b906d474a8d1e1dc9677ab0c4298f` |
| `HEAD:` object type | `git cat-file -t HEAD:src/serial_driver_ros` 返回 128；根 object database 无法解析该 object |
| `.gitmodules` | 根 tree 中不存在 |
| 当前 manifests | `workspace.lock.repos` 和 `workspace.repos` 均未声明该路径 |
| DDS-only package boundary | `serial_driver` 是 forbidden package；不在 production allowlist |
| 根级当前引用 | 除 gitlink 自身、排除/profile 和历史审计外，没有当前 build、launch、test 或 production 入口引用该路径 |
| 嵌套仓库 | origin 为 `https://github.com/BoomBoomFly/serial_driver_ros.git`，HEAD 与 gitlink object 相同 |
| 嵌套 dirty 状态 | 6 个 tracked 修改和新增 include/source/test 内容；必须保留 |
| 候选替代来源 | `workspace.repos` 声明 `../communication@main`，但该 checkout 本身 dirty，串口 ROS 2 目录当前是 untracked 内容 |

删除条件没有全部满足。尽管该 gitlink 不在 manifest、无 `.gitmodules` 映射、被
DDS-only boundary 禁止且没有根级活动入口，但 `../communication` 中的替代实现
目前不是可由其已记录 HEAD 重建的 tracked source；同时 gitlink checkout 含有必须
保留的本地修改。维护者应先决定这些本地变更的归属并把替代来源固化为可审计
commit，然后才能在后续变更中移除 gitlink。

后续决策的最小前置证据：

1. 为 `src/serial_driver_ros` dirty 变更生成受批准 receipt，或把其变更迁入明确的
   maintained repository 并完成 review。
2. 将 `../communication` 的替代实现提交到其上游，并记录 origin、commit、dirty
   状态和用途；不能以当前 untracked 目录作为替代完成证据。
3. 重新运行 manifest、package allowlist、build/launch/test/production 引用扫描。
4. 由维护者明确批准删除根索引中的 mode `160000` 条目；删除不得顺带清理嵌套
   checkout。

## Manifest 与 profile 分类

以下分类按 source repository 的默认恢复意义给出。package profile 本身仍以
`production_packages`、`forbidden_packages` 和 `managed_nonproduction_packages`
为权威边界。

| 分类 | 条目 | 说明 |
|---|---|---|
| production required | `src/px4_msgs`、`src/offboard_cpp`、`src/vision_to_dds` | 与 3 个 production package allowlist 一致 |
| production required（transport runtime，非 production ROS package allowlist） | `src/Micro-XRCE-DDS-Agent` | uXRCE-DDS-only transport 支持；profile 将其 ROS package 记为 managed non-production，不能因此把它加入控制 package allowlist |
| build/test only | `src/gazebo_ros_pkgs` | SITL/仿真支持，不属于 production package allowlist |
| optional perception/navigation | `src/imu_tools`、`src/librealsense`、`src/navigation2`、`src/navigation_msgs`、`src/realsense-ros`、`src/rplidar_ros`、`src/rtabmap`、`src/rtabmap_ros`、`src/slam_toolbox`、`src/vision_opencv` | 均只映射到 managed non-production packages；当前默认 lock 仍恢复这些仓库 |
| archived provenance | `src/px4_bringup` | MAVROS/旧串口 launch 来源；在 forbidden/excluded 中，禁止默认 build/launch |
| moving external dependency | `../communication@main` | 只在 `workspace.repos`；需要 `--allow-moving-refs`，且实验/发布应有 commit receipt |
| orphan/unreferenced | `src/serial_driver_ros` gitlink | 不在 manifest、无 `.gitmodules`，但因 dirty 和替代证据不足不能删除 |

`workspace.excluded_packages` 是 package-name denylist，不是 source restore manifest。
其 13 项与 profile 的 forbidden set 完全一致：
`offboard_py`、`cv_yolo_paddle_pkg`、`opencv_cpp`、`mavlink`、
`libmavconn`、`mavros`、`mavros_extras`、`mavros_msgs`、`test_mavros`、
`vision_to_mavros`、`px4_bringup`、`serial`、`serial_driver`。

## 默认恢复的 profile 拆分建议

不要直接删除导航、SLAM 或感知源码来源。后续应将 source restore 与 package build
边界分成明确 profile：

1. `workspace.lock.repos` 只保留 production required 与明确的 build/test-only
   transport/SITL 依赖；默认恢复不包含 optional perception/navigation。
2. 新增一个精确锁定的可选 manifest，例如
   `workspace.perception_navigation.lock.repos`，承载当前 10 个 optional
   perception/navigation 仓库。
3. `workspace.repos` 继续表达维护分支意图，但安装器要求显式参数才恢复可选
   profile；moving `../communication` 继续要求 `--allow-moving-refs`。
4. package boundary 不因 source profile 拆分而放宽。production allowlist 仍只有
   `px4_msgs`、`offboard_cpp`、`vision_to_dds`，optional packages 仍是 managed
   non-production。

## `px4_bringup` archive manifest 最小迁移方案（未执行）

### Manifest

1. 新建 `workspace.archive.repos`，只放
   `src/px4_bringup@0fbdcbf6ee53d6927de75af1d98f22cf5bd4f917`，保留 origin。
2. 从 `workspace.lock.repos` 和 `workspace.repos` 移除 `src/px4_bringup`。
3. `workspace.excluded_packages` 与 package profile 的 forbidden
   `px4_bringup` 项必须保留；archive 是来源保全，不是 build 或 launch 授权。

### Installer 参数

- 保持 `--manifest` 默认指向 active `workspace.lock.repos`。
- 新增显式、无默认启用的 `--archive-manifest <path>`；只有传入时才附加恢复 archive
  条目。
- archive manifest 必须只接受 40 位 commit SHA；即使同时传
  `--allow-moving-refs`，也不得允许 archive 条目使用 branch/tag。
- active 与 archive manifest 路径重复时 fail closed。默认命令因此不会恢复
  `px4_bringup`，而维护者仍可显式、detached-HEAD 恢复 provenance。

### Validator

- 增加 active lock、moving intent、archive 三类 manifest 的集合校验：URL 一致性、
  active/archive 路径互斥、archive 全为精确 SHA。
- package-boundary validator 继续要求 `px4_bringup` 位于 forbidden/excluded；
  profile 的 `source_manifests` 应加入 `workspace.archive.repos`。
- receipt validator 当前在 capture 路径中硬编码 `workspace.lock.repos`。如果未来
  archive checkout 也允许 receipt capture，应新增显式 lock-manifest 参数，并将
  receipt 的 `repository.lock_manifest` 固定为实际 archive manifest；验证端已有按
  receipt 中 manifest 路径读取的机制。现有 active receipts 不应改写。

### Tests

- 默认 installer dry-run/verify 不计划 `px4_bringup`。
- 显式 `--archive-manifest workspace.archive.repos` 时只按精确 SHA 计划 archive。
- archive moving ref、active/archive 重复路径、origin 不一致均必须 fail closed。
- package-boundary 测试继续证明 archive 包不能进入 allowlist/build graph。
- receipt 测试增加 archive lock 的 capture/verify 正向用例和路径逃逸、错误 manifest
  的负向用例；现有 receipts 保持不变。

### 文档

更新当前 README、`Scripts/README.md`、release policy、handoff 与 package-boundary
evidence，说明默认恢复不含 archive，以及显式恢复命令。日期化历史审计不回写；
计数或旧路径变化通过 `CORRECTIONS.md` / supersedes 机制说明。

## 本轮实际修改

仅把 `workspace.excluded_packages` 的旧 “T265 + D435 Offboard baseline” 头注释改成
当前权威 DDS-only package boundary，并注明它必须与 profile 的 forbidden set 精确
一致。清单有效条目未改变。
