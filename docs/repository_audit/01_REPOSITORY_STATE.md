# Git、仓库边界与工作区完整性

## 基线

根仓库为 Git 工作树，`master@df01b9280c0e79a05ad1e4cec727e7427c9251ca`，
upstream 为 `origin/master`，本地 ref 相等，工作树干净。未执行 fetch，因此不能
把本地 `origin/master` 解释为远端实时状态。

```text
BoomBoomFly (root, clean)
  `-- src/communication (gitlink, clean, update=none)
        `-- Serial/serial_driver_ros (nested independent repo, clean, quarantine)

src/Micro-XRCE-DDS-Agent, offboard_cpp, px4_msgs, vision_to_dds, optional repos
  `-- independent checkouts governed by workspace.lock.repos
      (not root submodules)
```

完整 ledger 见 `evidence/git_state.txt`。

## [P1-GIT-001] 两个 production checkout 与 exact lock 不一致

- 严重度：P1
- 状态：已确认
- 领域：Git / Build / PX4
- 位置：
  - `workspace.lock.repos:13-20`
  - `docs/repository_audit/evidence/git_state.txt` 的 exact-lock comparison
  - `src/offboard_cpp/.git`（Git identity）
  - `src/vision_to_dds/.git`（Git identity）
- 证据：
  - `git -C src/offboard_cpp rev-parse HEAD` → `976d6217…`，锁为 `722e05af…`。
  - `git -C src/vision_to_dds rev-parse HEAD` → `0c3a0013…`，锁为 `b366db72…`。
  - 当前 Offboard checkout 缺少 `src/safety_gate_adapter.cpp`；静态 H0 exit 2。
  - 审查时读取的旧候选记录绑定 `722e05a…`/`b366db7…`；旧报告随后按用户授权删除，
    当前 exact lock comparison 仍证明 checkout 不匹配。
- 影响：
  - 当前源码不等于测试候选；历史 build/test/安全结论不适用于当前 checkout。
  - 对当前目录直接运行构建或 launch 会使用未批准代码。
- 根因：
  - 根仓库只锁路径，不通过 gitlink 强制这两个独立 checkout 的 HEAD。
- 建议：
  - Phase 0 只读冻结差异并由维护者选择 approved source；任何 checkout 动作另行授权。
  - 选择后在隔离目录重跑 H0/H1，禁止复用历史产物。
- 前置条件：
  - 确认 `722e05a…` 与 `b366db7…` 的审批、远端可恢复性及 native ARM64 目标。
- 是否涉及硬件：
  - 否

## [P1-GIT-002] Optional 源码工作树存在大规模 dirty 状态

- 严重度：P1
- 状态：已确认
- 领域：Git / Build / Sensor
- 位置：
  - `src/librealsense/`
  - `src/mavlink/`
  - `src/navigation_msgs/map_msgs/`
  - `src/realsense-ros/`
  - `src/ros2_foxy_vision_to_mavros/launch/t265_tf_to_mavros_launch.py:38`
  - `src/vision_opencv/image_geometry/`
- 证据：
  - `librealsense` 3347 个 mode-only 变更；`mavlink` 233 个 mode-only + 8 untracked。
  - `navigation_msgs` 删除 13 个 `map_msgs` 文件。
  - `realsense-ros` 98 个 mode 变更 + 1 untracked。
  - `vision_opencv` 删除 17 个 `image_geometry` 文件。
  - `vision_to_mavros` 将 `output_rate` 从 30 改为 100。
  - 对应 perception/navigation dirty checkout 有 receipt，但当前树仍不是 clean upstream。
- 影响：
  - Optional perception/navigation 构建结果依赖本地 patch/mode 状态；误清理会丢失用户数据。
  - mode 漂移会产生巨大无意义 diff，并干扰审计与打包。
- 根因：
  - 已知裁剪/receipt 管理与文件系统执行位漂移并存；个别 legacy 修改来源未在本轮确认。
- 建议：
  - 保持不动；用 receipt 验证器核对 patch hash，再决定 clean clone、patch 重放或保留。
  - 构建 optional profile 时必须记录 dirty patch hash。
- 前置条件：
  - 维护者确认这些 dirty checkout 是否仍是受保护基线。
- 是否涉及硬件：
  - 否

## [P3-REPO-001] 独立源码树内保留生成目录和缓存

- 严重度：P3
- 状态：已确认
- 领域：Git / Build
- 位置：
  - `src/offboard_py/build/`
  - `src/serial-ros2/build/`
  - `src/rtabmap/build/`
  - `src/ros2_foxy_vision_to_mavros/log/`
  - 多个 `__pycache__/`
- 证据：
  - 只读 `find` 在源码树中发现上述目录。
  - 本审查没有把内容作为源码证据。
- 影响：
  - `colcon`/静态搜索容易误收生成文件，路径还暴露旧主机环境。
- 根因：
  - 历史本地构建产物未与 source checkout 物理隔离。
- 建议：
  - 仅列为清理候选；先确认各独立仓库 ignore 与用户是否需要产物，后续用可恢复方式处理。
- 前置条件：
  - 人工确认、receipt/工作树状态备份。
- 是否涉及硬件：
  - 否

## 无法确认

- 所有 remote 的实时可用性和远端分支偏离：本轮禁止网络/fetch。
- `mavlink` 的 8 个 untracked 文件是否用户数据：未展开内容，禁止删除。
- dirty mode 漂移的产生者：可能是挂载/权限行为，不能仅靠 Git 静态状态归因。
