# BoomBoomFly

BoomBoomFly 是 Ubuntu 20.04 / ROS 2 Foxy / PX4 的无人机伴随计算机工作区。
当前受管飞控路径仅允许 PX4 uXRCE-DDS；MAVROS 不属于 production 基线。

## 当前状态

- 工作区：`/home/c/BoomBoomFly`
- Offboard：基线 `BoomBoomFly/offboard_cpp:DDS@8925f8ae...`，本地兼容修复未提交
- 实机：PX4 v1.16.2、PX4_FMU_V3、Generic Quad X
- P0-03：`SOFTWARE FIXED / HARDWARE BLOCKED / FAIL-CLOSED`
- 构建：`px4_msgs`、`offboard_cpp` 通过；RC gtest 7/7 通过
- 阻塞：缺少独立 DDS transport，默认 firmware 未导出 `rc_channels`
- production：禁用

完整的当前状态、实机证据、验证结果和下一步只维护在
[窗口交接](docs/handoff.md)。

## 源码清单

- `workspace.lock.repos`：15 项精确 SHA，用于可复现恢复。
- `workspace.repos`：维护分支意图；Offboard 跟随 `DDS`。
- `communication` 是独立 moving dependency，不进入精确 lock。

## 恢复与审计

安装脚本只管理源码仓库，不安装 ROS、系统包、udev 规则或 PX4 firmware，
也不启动 Agent、ROS 节点或硬件链路。

### 只读审计现有工作区

先检查全部 lock 条目，不执行 clone、fetch、checkout 或 submodule 更新：

```bash
bash Scripts/installation/uav_px4_dds_install.sh \
  --verify-only \
  --skip-package-check
```

`--verify-only` 会遍历整个 manifest，检查路径、Git 仓库、origin、dirty 状态和
HEAD。发现任何 blocker 时仍完成其余条目，最后返回状态码 1，且不修改仓库。

当前工作区的预期结果是：

```text
Summary: planned=15 cloned=0 updated=0 verified=15 blockers=5
exit status: 1
```

`verified=15` 表示全部 HEAD/origin 与 lock 匹配；`blockers=5` 表示其中五个仓库
保留了本地修改，两者并不冲突：

- `src/librealsense`
- `src/navigation_msgs`
- `src/offboard_cpp`
- `src/realsense-ros`
- `src/vision_opencv`

### 恢复精确 lock

建议恢复到新的 `src` 目录。先 dry-run，确认后再执行恢复：

```bash
bash Scripts/installation/uav_px4_dds_install.sh \
  --src-dir /path/to/new_ros2_ws/src \
  --dry-run \
  --skip-package-check

bash Scripts/installation/uav_px4_dds_install.sh \
  --src-dir /path/to/new_ros2_ws/src
```

默认使用 `workspace.lock.repos`，恢复出的依赖为 detached HEAD。已有 dirty 仓库、
origin 不匹配和错误 HEAD 都会 fail-closed；只有已确认干净的仓库才可配合
`--update` 切换到 manifest ref。脚本从不执行 `git pull` 或 `reset`。

### 审计维护清单

`workspace.repos` 包含 tag/branch 以及外部 moving dependency `../communication`，
必须显式允许 moving refs：

```bash
bash Scripts/installation/uav_px4_dds_install.sh \
  --manifest workspace.repos \
  --allow-moving-refs \
  --dry-run \
  --skip-package-check
```

dry-run 同样会完整汇总 blocker 并以非零状态退出；它只打印计划，不创建目录、
不 fetch，也不改变 Git ref。完整参数见脚本的 `--help` 和
[Scripts 说明](Scripts/README.md)。

`build/`、`install/`、`log/` 是可再生输出，不作为源码或验证证据保存。

## 文档

- [窗口交接](docs/handoff.md)
- [控制权矩阵](docs/CONTROL_AUTHORITY_MATRIX.md)
- [ADR-0001：DDS-only 控制权](docs/adr/0001-dds-only-control-authority.md)
- [兼容性证据](docs/evidence/OFFBOARD_PX4_MSGS_COMPAT_20260724.md)
- [实机参数快照](docs/evidence/PX4_PARAMS_20260724T203458+0800.json)

未经明确授权，不写飞控参数、不刷固件、不 arm、不切 mode、不发送控制命令，
也不启动 Agent、Offboard 或视觉注入链路。
