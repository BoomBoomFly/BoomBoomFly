# Wave 4A — 构建与仓库治理证据

审查时间：2026-07-27（Wave 4A Thread C）  
工作区：`/home/c/px4_ws/BoomBoomFly`  
审查范围：静态身份/来源/锁定复核，以及仅在 `/tmp` 的 DDS-only 纯软件构建入口。  
安全边界：未运行 `ros2 launch`、`ros2 run`、PX4/SITL、MicroXRCEAgent、MAVROS、任何 `/fmu/in/*` 发布、串口/相机/LiDAR 或硬件探测命令；未安装软件、未改动源代码/配置/锁文件。

## 结论

```text
H0: NO-GO
H1: NO-GO — 构建入口实际执行，但在 package-boundary 前置校验以 exit 2 停止；
               colcon build/test 未启动，故不存在当前提交的成功构建证据。
HARDWARE ACCESSED: NO
FORMAL SITL RUN: NO
```

本报告不把历史 standalone/offline 测试、已有 PX4 checkout、或仅创建的 `/tmp` 目录写成 H1 通过。H0 仍为 NO-GO，因此即使后续获得一次编译成功，也不能单独升级 H1 或推进 H2–H6。

## 当前身份与可恢复性账本

| 组件 | 当前身份 | 来源/状态 | 锁定复核 | 结论 |
|---|---|---|---|---|
| 根仓库 | `master@0ed9d148bfbfd22253142172bbfe93c51106fdfa` | dirty：删除 `src/serial_driver_ros` gitlink；未跟踪 `src/communication/`；无 unmerged index 条目 | N/A | 非干净、关键路径漂移 |
| Offboard | `agent/wave3b-offboard-integration@976d6217d73a28b72e64300e2dd04bcbeeee30d7` | `https://github.com/BoomBoomFly/offboard_cpp.git`；clean、非 shallow、无 upstream tracking ref | `workspace.lock.repos:12-15` 锁定的是祖先 `cded3dc5b6906420db3767abd82b2df7ba6ea9f0` | **不匹配** |
| px4_msgs | detached `v1.16.2@392e831c1f659429ca83902e66820d7094591410` | `https://github.com/PX4/px4_msgs.git`；clean、非 shallow | `workspace.lock.repos:4-7` 完全匹配 | 身份已知 |
| Micro-XRCE-DDS-Agent | detached `57d086216d01ec43121845d385894a25987f8a2c` | `https://github.com/eProsima/Micro-XRCE-DDS-Agent.git`；clean、非 shallow | `workspace.lock.repos:8-11` 完全匹配 | 身份已知；本轮未运行 |
| vision_to_dds | detached `0c3a00137f3c90a4051ac1bc1029ec56beb669b6` | `https://github.com/wanone111/vision_to_dds.git`；clean、非 shallow | `workspace.lock.repos:16-19` 完全匹配 | 身份已知，但其安全问题不因本项关闭 |
| PX4-Autopilot | detached `v1.16.2@54f0455ffcd755534539a7cf33a09a20bf71d29d` | `https://github.com/PX4/PX4-Autopilot.git`；clean、**shallow**；35 个递归 submodule 已初始化；`git fsck --connectivity-only` 通过 | 不在 `workspace.lock.repos` 或受批准的 source/submodule/toolchain/board lock 中 | 身份可读但**未治理** |
| communication | `main@df256c180dbd4167f879b697e38d547521f1f8e2` | `https://github.com/BoomBoomFly/communication.git`；dirty：三个删除项、一个嵌套未跟踪 repo | `workspace.repos:21-24` 声明 sibling `../communication` 和 moving `main`，实际为 root 内路径 | **来源/路径未决** |
| serial_driver_ros | `master@87f3907f0b3b906d474a8d1e1dc9677ab0c4298f` | `https://github.com/BoomBoomFly/serial_driver_ros.git`；位于 `src/communication/Serial/serial_driver_ros` | 根 index 仍记录删除的 `src/serial_driver_ros` gitlink；DDS profile `:28` 仍要求旧路径 | **不受治理** |

锁文件 SHA-256：`workspace.lock.repos` `365e8ecb681ee98b9c8511c7fc565362a0abc446371d893a3b8f4e87d23d2235`；`workspace.repos` `19d75a993a6e69a9f0af9c6dc609a2c67447a7694a13fea9681588dff0f1f06b`；DDS profile `5db74886c901eec86118f338dd67c126a8fab9c1ccb205ca3566f851e51f6786`。

PX4/px4_msgs 消息复核：PX4 当前 production + versioned 消息按生成后的 basename 映射，与 `px4_msgs/msg` 的 226 个生产消息逐文件一致（0 mismatch、0 production missing）。唯一不映射项是 PX4 的历史 `msg/px4_msgs_old/msg/VehicleStatusV0.msg`，不属于当前 px4_msgs v1.16.2 的生产消息集合；不能据此声称 PX4 toolchain、board 或 DDS RC profile 已经闭合。

工具链身份：`/opt/ros/foxy/setup.bash` 存在；`colcon_core==0.21.0`；CMake `3.16.3`；G++ `9.4.0`；未发现 `arm-none-eabi-gcc` 或 `arm-none-eabi-g++`。因此 ARM firmware build/toolchain 身份仍为 `NOT_VERIFIED`，且本轮没有尝试 firmware build。

## 构建执行证据

构建入口在执行前已静态检查（`bash -n`）并确认其行为为：清空继承 AMENT/CMake/ROS 路径、只 source 明示 Foxy underlay、先执行 package-boundary，只有该校验通过才调用 `colcon build`；所有 build/install/log/test-results 路径由 `Scripts/build/build_dds_only.sh:60-100` 限制为 `/tmp`。入口不含 launch、run、Agent、PX4、MAVROS、设备节点或 `/fmu/in/*` 发布。

| 命令 | 结果 | 保留证据 |
|---|---|---|
| `bash -n Scripts/build/build_dds_only.sh Scripts/test/test_dds_only.sh` | PASS | 静态语法检查 |
| `bash Scripts/test/test_dds_only.sh --workspace-root /home/c/px4_ws/BoomBoomFly --output-root /tmp/boomboomfly_wave4a_h1_build_20260727T231500` | FAILED in prerequisite build entry | `test_dds_only.sh:76-80` 调用 build；未到 `colcon` |
| `python3 Scripts/test/verify_package_boundary.py ... --log-base /tmp/boomboomfly_wave4a_h1_build_20260727T231500/log/package-boundary-exitcheck` | **exit 2** | 原始 JSON：`{"error":"package serial_driver path mismatch: expected src/serial_driver_ros, found src/communication/Serial/serial_driver_ros","status":"FAIL"}` |

保留的隔离目录：`/tmp/boomboomfly_wave4a_h1_build_20260727T231500/`。该目录只含空 build/install/test-results 目录、boundary `COLCON_IGNORE`/colcon list 日志和 `artifacts/package-boundary-summary.json`；后者 SHA-256 为 `7bab2925f640ac8dc87f76c40ece382a61d14daee2af3116136b2b8c802b82db`，内容为同一 FAIL JSON。不存在 `package-selection.tsv`、编译对象、install artifact、test result 或 `colcon build/test` 日志，因为脚本在 `Scripts/build/build_dds_only.sh:96-100` 失败并按 `set -e` 停止。

## 发现与处置

### BBF-CUR-004 — serial canonical path/source 与 package boundary 漂移

- 严重级别：P1（与未隔离的 BBF-CUR-003 P0 联合阻塞 H0/H1）。
- 历史结论：`STILL_OPEN/REGRESSED`；不得放宽 validator 绕过 canonical disposition。
- 当前文件和行号：`config/profiles/dds_only_packages.yaml:28` 期望 `src/serial_driver_ros`；`workspace.repos:21-24` 指向另一 sibling/moving source；根 index 的 gitlink `src/serial_driver_ros` 已删除；实际包位于 `src/communication/Serial/serial_driver_ros`。
- 当前证据：本轮 authoritative boundary 实际 exit 2；上述完整 JSON 与 `/tmp` 工件已保留。
- 状态：`STILL_OPEN`。
- 影响：DDS-only 构建在 `colcon` 前停止，无法产生 H1 receipt；关键执行链来源也不可恢复。
- 修复：先由维护者书面确定唯一 origin、SHA、path 与 disposition；保留严格边界断言，随后更新 approved manifest/profile/receipt 并复跑。
- 验收命令：`python3 Scripts/test/verify_package_boundary.py --workspace-root /home/c/px4_ws/BoomBoomFly --log-base /tmp/<unique>` 必须 exit 0；随后以全新 `/tmp/<unique>` 运行 `Scripts/test/test_dds_only.sh`。
- 阻塞：H0、H1、H2、H3、H5、H6。

### BBF-CUR-007 — Offboard final 未被 root exact lock 恢复

- 严重级别：P1。
- 历史结论：`STILL_OPEN`。
- 当前文件和行号：`workspace.lock.repos:12-15`。
- 当前证据：live checkout 为 `976d6217...`，而 exact lock 为其祖先 `cded3dc5...`；二者均可本地读取，但 lock 不能恢复当前审查对象。
- 状态：`STILL_OPEN`。
- 影响：即使 boundary 修复，H1 receipt 仍不能声称可从 root lock 重建相同 Offboard 源。
- 修复：确认 commit 可恢复并取得维护者批准后，更新 exact lock 与相应 receipt；不使用 moving `workspace.repos` 的 `DDS` ref 代替。
- 验收命令：在无网络/干净 fixture 中按 approved lock 解析 `src/offboard_cpp`，`git rev-parse HEAD` 必须等于获批 SHA，再运行完整 H1 构建。
- 阻塞：H0、H1、H2、H3、H5、H6。

### BBF-CUR-006 — PX4 source/toolchain/profile governance 未闭合

- 严重级别：P1。
- 历史结论：exact source/message identity 已改善，但 governed source/submodule/toolchain/board lock 与 RC endpoint 仍 `STILL_OPEN`。
- 当前文件和行号：`workspace.lock.repos:1-19` 没有 PX4 entry；`workspace.repos:1-24` 没有 PX4 exact entry；PX4 `src/modules/uxrce_dds_client/dds_topics.yaml` 仍需独立的 RC endpoint/profile 审查。
- 当前证据：`v1.16.2@54f0455f...`、35 recursive submodules、`git fsck` PASS、226/226 production message mapping consistent；checkout 为 shallow；ARM compiler 不在 PATH。
- 状态：`STILL_OPEN`，不是 `FIXED`。
- 影响：无法离线、受批准地重建 PX4 firmware/profile，也不能证明 RC safety endpoint 与板卡工具链。
- 修复：由 PX4/Release maintainer 批准 immutable origin/SHA/tag/submodule manifest、toolchain digest/version、board/profile 和 RC endpoint；将其写入非模板 exact lock。禁止以当前 checkout 存在代替审批。
- 验收命令：offline source/submodule/message verifier、lock schema verifier、profile/generator hash verifier，以及获单独批准后的纯软件 target build；本任务不得 flash 或访问硬件。
- 阻塞：H0、H1、H4、H5、H6。

### BBF-CUR-008 — 当前 H1 没有成功的纯软件构建证据

- 严重级别：P1。
- 历史结论：`H1 NOT-RUN`；package boundary exit 2 是先决失败。
- 当前文件和行号：`Scripts/build/build_dds_only.sh:84-100`（只写 `/tmp` 并先运行 boundary）；`Scripts/test/test_dds_only.sh:76-116`（build 成功后才 test）。
- 当前证据：本轮新鲜 `/tmp` entrypoint 已执行，boundary exit 2；`colcon build/test` 没有启动，且没有 artifact。
- 状态：`STILL_OPEN`；本轮将 H1 gate 判为 `NO-GO`，其目标构建子步骤为 `NOT-RUN`。
- 影响：无 current-commit build/install/test receipt；H1 不得借用 Wave 3B、standalone gate 或本次失败前置检查升级。
- 修复：先关闭 BBF-CUR-003/004/006/007 及 H0 P0，修复严格 boundary 后，在新的 `/tmp` 目录重跑同一入口，并保存 package selection、完整 colcon logs、test results、artifact hashes 及所有 nested SHA。
- 验收命令：`Scripts/test/test_dds_only.sh --workspace-root /home/c/px4_ws/BoomBoomFly --output-root /tmp/<unique>`，build/test/test-result 全部 exit 0。
- 阻塞：H1、H2、H3、H5、H6。

## 最短剩余关键路径（本线程范围）

1. 维护者先决定并审批 serial/communication 的唯一 exact source/path/disposition；保持未知执行路径 fail-closed，不能改宽 boundary。
2. 将获批 serial disposition、Offboard final 与 PX4 source/submodules/toolchain/board/profile 写入不可变 lock/receipt；明确 RC endpoint。
3. 在不改变 allowlist 的前提下使 package-boundary exit 0，并修复 production package 直接依赖闭包。
4. 固定上述 source snapshot 后，在全新 `/tmp` 运行同一 DDS-only build/test 入口；只有 build、test、test-result 全部成功并有完整工件身份时，H1 才可重新评估。

本线程修改：仅新增本报告。`/tmp/boomboomfly_wave4a_h1_build_20260727T231500` 是可保留的构建证据，不是仓库源文件修改。
