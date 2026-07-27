# 命令与执行证据

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

## 安全边界

本轮没有执行 `ros2 launch`、`ros2 run`、PX4/SITL make、DDS Agent、MAVROS、
串口读写、RealSense/RPLIDAR 启动、`/fmu/in/*` 发布、参数写入、arm/mode/takeoff、
firmware build/flash、Git fetch/pull/checkout/merge/reset/commit/push 或安装命令。

设备证据仅使用用户明确允许的 `ls -l` 列举设备节点名称；没有打开设备。观察到
`ttyS0..3`、`ttyTHS0/1/3/4`；没有匹配的 `ttyUSB*`、`ttyACM*` 或
`/dev/serial/by-id/` 条目。

## 环境与 Git 命令

| 命令/类别 | 结果摘要 | 写入 |
|---|---|---|
| `pwd`, `hostname`, `whoami`, `uname -a`, `date --iso-8601=seconds` | workspace、host、user、时间已记录 | 无 |
| root `git status --short --branch` | `master@0ed9d148`; deleted gitlink + untracked communication | 无 |
| `git rev-parse`, `git branch`, `git remote`, `git log` | root、nested、PX4 identity 账本 | 无 |
| `find ... -name .git`, `git worktree list` | 59 worktrees；无额外 linked worktree | 无 |
| `git merge-base --is-ancestor`, `git cat-file -e` | 历史 root/Offboard commit 关系已复核 | 无 |
| `git submodule status --recursive`（PX4） | 35 个递归子模块均初始化、无 `+/-/U` | 无 |
| `git ls-files docs` 与 `find docs` | 审查前 147/147 文件全部 tracked | `/tmp` 仅排序清单 |

## 文档命令

| 命令/类别 | 结果摘要 |
|---|---|
| `find docs -type f -printf '%P\n' | sort` | 完整 147 文件清单 |
| 关键字 `grep -nHE` | 输出约 133k tokens；用于定位 commit/gate/hardware/SITL 声明 |
| 全量 Markdown 分段读取 | 82/82 完整读取 |
| JSON/YAML/schema/receipt 清点 | 65/65 读取状态、identity、scope、引用关系 |
| `git log -1 -- <doc>` | 逐文件最后提交与时间写入 `01-doc-inventory.md` |

## 当前 PX4/px4_msgs 证据

| 检查 | 结果 |
|---|---|
| PX4 root identity | `v1.16.2@54f0455ffcd755534539a7cf33a09a20bf71d29d`，origin canonical，clean/detached/shallow |
| PX4 submodules | 35 个 recursive submodule 全部 initialized/clean |
| `px4_msgs` identity | `v1.16.2@392e831c1f659429ca83902e66820d7094591410`，clean/detached |
| 全消息逐文件 `cmp` | 226/226 完全一致；0 missing，0 mismatch |
| `dds_topics.yaml` | 存在；ACK/status/timesync 与控制输入存在；`rc_channels` 不存在 |
| ARM toolchain lookup | `arm-none-eabi-gcc/g++` 均未发现 |
| governance lookup | PX4 checkout 不在 `workspace*.repos`，lock template 仍未解析 |

## 当前低风险软件验证

| 命令 | Exit | 结果与边界 |
|---|---:|---|
| `python3 Scripts/test/verify_package_boundary.py --workspace-root ... --log-base /tmp/...` | 2 | `serial_driver` expected `src/serial_driver_ros`, found `src/communication/Serial/serial_driver_ros` |
| `PYTHONPYCACHEPREFIX=/tmp/... python3 -m unittest discover -s test -p 'test_*.py' -v` | 0 | root 152/152 PASS；offline/static/synthetic |
| Offboard 同类 Python discovery | 0 | 12/12 PASS；contract oracle only |
| `/usr/bin/g++ -std=c++17 ... offboard_runtime_gate.cpp test_offboard_runtime_gate.cpp -o /tmp/...` | 0 | standalone compile PASS |
| `/tmp/boomboomfly_current_audit_offboard_runtime_test` | 0 | pure-software runtime gate PASS |

没有执行 colcon build/test、ament gtest、节点级测试或 formal SITL。上述通过不能证明
live ROS node 使用 runtime gate；源码扫描确认只有测试实例化
`OffboardRuntimeGate`。

## `colcon list` 非预期日志副作用

一个只读 ROS 清点线程在 `/home/c/px4_ws` 首次执行了未带 `--log-base` 的：

```text
colcon list
```

命令退出 0，但 colcon 产生/更新时间一致的非源码日志：

```text
/home/c/px4_ws/log/COLCON_IGNORE
  size=0
  mtime=2026-07-27T22:05:18.344477984+08:00

/home/c/px4_ws/log/list_2026-07-27_22-05-18/logger_all.log
  size=359167
  mtime=2026-07-27T22:05:19.096494611+08:00
```

文件系统不提供 birth time，故不能严格证明 `COLCON_IGNORE` 是新建还是更新；logger
目录名与本次 invocation 一致。依照本轮“禁止删除”约束，未删除它们。此后所有
colcon discovery 均指定 `/tmp` log base。主仓库状态未因此增加源码/config/doc
变化，但最终不能声称“`docs/current_audit` 外绝对零文件写入”。

## Git 元数据变化与并发状态

跨仓库 `git status` 清点会 refresh index metadata；本轮观察到 `src/communication/.git/index` 与其 nested serial `.git/index` 的 mtime 在清点时更新。工作树内容/状态未改变。

此外，最终检查发现 root `.git/FETCH_HEAD` 的 mtime 为 `2026-07-27T22:29:01+08:00`，内容为当前 `origin/master at 0ed9d148...`。审查 Agent 没有发出 fetch/pull/remote-update 命令；没有 reflog commit/ref 变化，最终 root HEAD/status 与初始一致。该 metadata 改动无法归因，最合理解释是审查期间存在外部/并发 fetch。报告不使用它来声称远端实时状态，并将其作为 concurrent workspace change 披露。

## 未执行项

- H1 完整 DDS-only build：未执行；
- ROS gtest/ament/launch_test 全套：未执行；
- 无硬件节点级测试：未执行；
- formal SITL：未执行；
- 网络远端实时核验：未执行；ahead/behind 仅基于本地 refs。
