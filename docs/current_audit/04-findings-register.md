# 当前发现登记册

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

## 历史 P0/P1 复核摘要

| Finding ID | 历史状态 | 当前状态 | 证据 | 是否阻塞 |
|---|---|---|---|---|
| BBF-AUD-001..004 | OPEN/P0 | STILL_OPEN | live node 直接创建/publish PX4 writers；runtime gate 仅测试实例化；无 ACK subscription | H0/H1/SITL |
| BBF-AUD-005 | OPEN/P0 | STILL_OPEN | `TEXT_RC` 无条件编译；auto arm 默认 true；无 RC 时检查可跳过 | H0 |
| BBF-AUD-006 | OPEN/P0 | STILL_OPEN | 多个输入初值/first-frame 仍不闭合；FSM 启动即 50 Hz 发布 | H0 |
| BBF-AUD-007 | OPEN/P0 | STILL_OPEN | live fault lattice/锁存/人工恢复未集成 | H0/SITL |
| BBF-AUD-008..009 | OPEN/P0 | STILL_OPEN | vision frame/time/reset/quality/freshness 未形成 live health gate | H0（启用视觉时） |
| BBF-AUD-010 | OPEN/P1 | STILL_OPEN | package boundary 当前 exit 2，serial 实际路径再次漂移 | H0/H1 |
| BBF-AUD-011 | OPEN/P1 | REGRESSED | 新未跟踪 communication/serial 无 receipt；旧 protected checkout 消失 | H0/H1 |
| BBF-AUD-012 | OPEN/P1 | STILL_OPEN | exact PX4 source/message 部分已补齐；governed lock、ARM toolchain、`rc_channels` endpoint 仍缺 | H0/H1/SITL |
| BBF-AUD-013 | OPEN/P1 | STILL_OPEN | workflow static exists；immutable locks/remote required status 未闭合 | H1/release |
| BBF-AUD-014 | OPEN/P1 | STILL_OPEN | 152+12+standalone tests pass，但 live FSM 未使用安全门 | H0/H2/SITL |
| BBF-AUD-015 | OPEN/P1 | STILL_OPEN | formal PX4 DDS SITL 未运行 | SITL |
| BBF-AUD-016..019 | OPEN/P1 | STILL_OPEN | endpoint/identity/atomic input/safety profile 不完整；auto-arm default 仍危险 | H0 |
| BBF-AUD-020 | OPEN/P1 | NOT_VERIFIED | 本轮未做法律/分发批准 | release |
| BBF-AUD-021 | OPEN/P1 | STILL_OPEN | 分级 runbook、stop/rollback 模板已建立，但桌面/实际回滚演练未达到原验收标准 | 后续 promotion |
| BBF-AUD-022..024 | OPEN/P1 | STILL_OPEN | sensor/TF/EKF2、stable device、precision landing 独立 profile 未闭合 | 感知/SITL/硬件 |

## 新发现摘要

| Finding ID | 严重级别 | 子系统 | 问题 | 证据 | 建议 |
|---|---|---|---|---|---|
| BBF-CUR-001 | P0 | Offboard | 测试过的安全门没有接入 live node，节点直接发布控制/模式/命令 | `node.cpp:20,28-35,87-90`; gate 仅 tests 使用 | 单一集成 owner 将所有 PX4 publish 穿过 gate |
| BBF-CUR-002 | P0 | Offboard/RC | 默认 auto-arm + production `TEXT_RC` + 无 ACK live 闭环 | `CMakeLists.txt:33-35`; `ctrl_param.yaml:12-16`; `CtrlFSM.cpp:161-170,405-477` | production 默认禁止 arm；物理 RC/ACK/authority 强制门 |
| BBF-CUR-003 | P0 | Serial/actuator | 未跟踪节点将任意 `/cmd_vel` 直接写串口，demo 周期发非零速度 | `serial_main.cpp:13-35`; `send_demo.py:9-20` | 在决定来源前隔离/禁止构建启动；设计 interlock/watchdog |
| BBF-CUR-004 | P1 | Workspace | 旧 gitlink 删除、新 communication/serial 路径未跟踪且来源冲突 | root status；manifest/profile 与实际路径 | maintainer 决定 canonical exact source/path/receipt |
| BBF-CUR-005 | P1 | Serial | ROS additive checksum/no tail 与 STM32 CRC16+tail 不兼容，odd length 可越界 | 两端协议源码 | 单一 schema + 金样/错误注入/ASan |
| BBF-CUR-006 | P1 | PX4 provenance | exact source 现已存在但未治理，ARM/board/toolchain lock 与 RC endpoint 仍缺 | external PX4、lock template、DDS YAML | 建立 approved lock，不修改当前 checkout |
| BBF-CUR-007 | P1 | Reproducibility | Offboard final 未进入 root exact lock | current HEAD 与 `workspace.lock.repos` | 发布/批准 exact commit 后更新 lock |
| BBF-CUR-008 | P1 | ROS build | package boundary exit 2，依赖声明仍不完整，H1 未运行 | validator output、package/CMake | 先关闭 H0，再 isolated build |
| BBF-CUR-009 | P1 | Perception | frame/time/reset/quality/掉线 health gate 仍不闭合 | `vision_to_dds.cpp`; RealSense launch defaults | 纯函数转换、timestamp/epoch/device health 门 |
| BBF-CUR-010 | P2 | Hardware config | tty/USB/frame/model 多处硬编码，设备稳定身份和重连策略不足 | serial/bringup/RPLIDAR/RealSense configs | 分 profile、by-id、bounded reconnect、production disabled |
| BBF-CUR-011 | P2 | Documentation | `current_environment.json` 和 handoff 的“PX4 absent/communication absent”已过时 | 当前新增 repos | 用 dated current audit supersede，不改历史记录 |
| BBF-CUR-012 | P2 | Audit reproducibility | 审查期间 root `FETCH_HEAD` 被无法归因的并发动作更新 | mtime/content；无 Agent fetch command或reflog变化 | 后续审查使用独占/快照工作区 |

### [P0] Live Offboard 发布路径绕过 Wave 3B runtime gate

- Finding ID：BBF-CUR-001（映射 BBF-AUD-001..004、017）
- 文档来源：`audits/2026-07-27-wave3b/22_BC_RUNTIME_INTEGRATION.md`
- 文档原结论：纯软件 gate PASS，但明确声明 live ROS publisher integration 未完成
- 当前仓库：`src/offboard_cpp`
- 当前分支：`agent/wave3b-offboard-integration`
- 当前 HEAD：`976d6217d73a28b72e64300e2dd04bcbeeee30d7`
- 文件：`src/node.cpp`；`src/lib/CtrlFSM.cpp`；`CMakeLists.txt`
- 行号：`node.cpp:20,28-35,87-90`；`CtrlFSM.cpp:326-340,405-417`；`CMakeLists.txt:43-77,113-120`
- 当前证据：node 创建三个 `/fmu/in/*` publisher 并每 20 ms 调 FSM；FSM 直接 publish；全仓除测试外没有 `OffboardRuntimeGate` 实例或 ACK observer
- 验证状态：STILL_OPEN
- 影响：authority、ACK、freshness、PRESTREAM、restart 测试通过也不约束实际控制发布
- 触发条件：启动 offboard node、PX4/Agent 重连、陈旧/缺失输入、重复 writer
- 建议：由单一 writer 将 live subscription、authority adapter、ACK/status/timesync 与所有 publish 统一接入 gate
- 验收方法：ready 前三个 PX4 输入 publish count 为 0；所有拒绝/重连场景仍为 0；只有完整 gate 后允许发布
- 是否阻塞 H0：是
- 是否阻塞 H1：是（目标 build 即使成功也不可 promotion）
- 是否阻塞后续硬件阶段：是

### [P0] 默认自动解锁和 mock RC 仍在 production 代码路径

- Finding ID：BBF-CUR-002（映射 BBF-AUD-005、019）
- 文档来源：`audits/2026-07-26/07_FINDINGS_REGISTER.md`
- 文档原结论：production mock/auto-arm/kill 安全门不闭合
- 当前仓库：`src/offboard_cpp`
- 当前分支：`agent/wave3b-offboard-integration`
- 当前 HEAD：`976d6217d73a28b72e64300e2dd04bcbeeee30d7`
- 文件：`CMakeLists.txt`；`config/ctrl_param.yaml`；`src/lib/CtrlFSM.cpp`
- 行号：`CMakeLists.txt:33-35`；`ctrl_param.yaml:12-16`；`CtrlFSM.cpp:152-170,405-477`
- 当前证据：无条件定义 `TEXT_RC`；auto arm 默认 true；起飞路径在 RC 从未 fresh 时可跳过 RC 检查并直接发 ARM command；live node 无 ACK subscription
- 验证状态：STILL_OPEN
- 影响：错误 topic/参数或缺 RC 场景可能触发模式切换和解锁请求
- 触发条件：收到 `/offboard/takeoff_land=1`、odom/landed 条件满足、RC 缺失或 mock 参数影响
- 建议：production 编译移除 mock；auto-arm 默认 false；fresh physical RC、kill latch、accepted ACK、authority 全部强制
- 验收方法：无 RC、stale RC、mock、invalid params、ACK reject/timeout 下 ARM/MODE publish count 均为 0
- 是否阻塞 H0：是
- 是否阻塞 H1：否（编译本身），但阻塞 promotion
- 是否阻塞后续硬件阶段：是

### [P0] 未跟踪 serial 节点可把任意 cmd_vel 直接写入执行串口

- Finding ID：BBF-CUR-003
- 文档来源：Wave 3B 未记录该路径；`24_MANIFEST_MIGRATION_AND_SERIAL_DECISION.md` 记录旧 serial conflict
- 文档原结论：serial canonical source/path 必须维护者决定，production 应隔离
- 当前仓库：`src/communication/Serial/serial_driver_ros`
- 当前分支：`master`
- 当前 HEAD：`87f3907f0b3b906d474a8d1e1dc9677ab0c4298f`
- 文件：`src/serial_main.cpp`；`script/send_demo.py`
- 行号：`serial_main.cpp:13-25,29-39`；`send_demo.py:9-20`
- 当前证据：节点构造即打开参数串口；任何 `/cmd_vel` 回调将线/角速度编码后写串口；无 enable、owner/lease、watchdog、零速 timeout、interlock 或范围检查；demo 每 0.5 s 发布非零速度
- 验证状态：REGRESSED
- 影响：若误启动并连接执行控制器，ROS topic 可直接导致执行器动作
- 触发条件：运行未跟踪 `serial_cmd_sender`，设备存在并向 `/cmd_vel` 发布
- 建议：当前保持 package/launch fail-closed；确定设备用途前不得纳入 build；后续需显式安全 profile、物理/软件 interlock、watchdog、range/finite validation
- 验收方法：未授权 profile 下包不可发现/启动；授权测试中无 enable/lease 或 timeout 时只允许零/无输出；协议 golden tests 通过
- 是否阻塞 H0：是
- 是否阻塞 H1：是
- 是否阻塞后续硬件阶段：是

### [P0] 启动即发布与输入初始化/有效性边界仍不安全

- Finding ID：BBF-CUR-004A（映射 BBF-AUD-003、006）
- 文档来源：`audits/2026-07-26/07_FINDINGS_REGISTER.md`
- 文档原结论：缺 readiness/PRESTREAM，未初始化/异常值可进入控制链
- 当前仓库：`src/offboard_cpp`
- 当前分支：`agent/wave3b-offboard-integration`
- 当前 HEAD：`976d6217d73a28b72e64300e2dd04bcbeeee30d7`
- 文件：`src/lib/CtrlFSM.cpp`；`include/lib/input.hpp`；`src/lib/input.cpp`
- 行号：`CtrlFSM.cpp:50-69,326-340`；`input.hpp:80-106,159-169`；`input.cpp:281-318`
- 当前证据：FSM 无 WAIT/PRESTREAM 状态且每周期 publish；VehicleStatus 不记录接收 freshness；多个数据成员/landed 缺显式初始化；tested gate 不在该路径
- 验证状态：STILL_OPEN
- 影响：节点先于 telemetry、restart、NaN/Inf/clock jump 时可发布默认或陈旧控制流
- 触发条件：节点启动、输入缺失/断流、PX4/Agent restart
- 建议：typed validity wrapper + finite/range/epoch checks；live WAIT→PRESTREAM→ACTIVE；restart 清空全部状态
- 验收方法：ASan/UBSan 与异常/首帧/断流测试；ready 前真实 publisher count 0
- 是否阻塞 H0：是
- 是否阻塞 H1：否（编译本身），但阻塞 promotion
- 是否阻塞后续硬件阶段：是

### [P1] Serial canonical path/source 与 package boundary 再次漂移

- Finding ID：BBF-CUR-004
- 文档来源：Wave 3B `24_MANIFEST_MIGRATION_AND_SERIAL_DECISION.md`
- 文档原结论：旧 gitlink与 protected `serial_driver_ros2` 冲突，维护者决定前 fail-closed
- 当前仓库：root + `src/communication`
- 当前分支：`master` / `main`
- 当前 HEAD：`0ed9d148...` / `df256c180...`
- 文件：root index；`workspace.repos`；`config/profiles/dds_only_packages.yaml`
- 行号：profile serial entry `:28`；boundary exact compare `Scripts/test/verify_package_boundary.py:206-217`
- 当前证据：旧两路径当前都缺失；实际包位于未跟踪 nested path；package boundary 复现 exit 2
- 验证状态：REGRESSED
- 影响：来源不可追溯，权威 DDS-only wrapper 在 build 前停止
- 触发条件：package discovery、restore、H1 build
- 建议：维护者选择 canonical origin/path/SHA/package contract，并生成 receipt；不放宽路径检查
- 验收方法：clean restore 精确发现唯一 serial disposition；package boundary exit 0
- 是否阻塞 H0：是
- 是否阻塞 H1：是
- 是否阻塞后续硬件阶段：是

### [P1] ROS 与 STM32 串口协议不一致并存在 odd-length 越界

- Finding ID：BBF-CUR-005
- 文档来源：当前新增 communication 代码，Wave 3B 未记录
- 文档原结论：N/A
- 当前仓库：`src/communication`
- 当前分支：`main`
- 当前 HEAD：`df256c180dbd4167f879b697e38d547521f1f8e2`
- 文件：ROS `serial_driver.cpp`；STM32 `Serial_32/include/serial.h`、`Serial_32/src/Serial.c`
- 行号：ROS `35-60,63-95`；STM32 header `20-40`；parser `186-219`
- 当前证据：ROS 使用单字节 additive checksum 且无 tail；STM32 期待 CRC16 low/high + `0xFF` tail；ROS 对 odd `len` 的 `j+1` 可越界
- 验证状态：REGRESSED
- 影响：通信不互通、错误命令解释、畸形输入触发未定义行为
- 触发条件：连接两端、奇数 payload length、噪声/截断 frame
- 建议：唯一协议 schema 与生成/共享实现；长度偶数/上限校验；ASan、CRC、截断/重同步测试
- 验收方法：两端 golden vectors 一致；所有畸形帧 fail-closed；sanitizer 无越界
- 是否阻塞 H0：是（该来源进入范围时）
- 是否阻塞 H1：是（serial 进入目标时）
- 是否阻塞后续硬件阶段：是

### [P1] PX4 source 已出现但尚未形成受治理 provenance/toolchain/profile

- Finding ID：BBF-CUR-006（映射 BBF-AUD-012）
- 文档来源：Wave 3B `21_PX4_PROVENANCE.md`
- 文档原结论：PX4 source/toolchain 缺失，A2 BLOCKED
- 当前仓库：`external/PX4-Autopilot`
- 当前分支：detached
- 当前 HEAD：`54f0455ffcd755534539a7cf33a09a20bf71d29d`
- 文件：Git identity；`src/modules/uxrce_dds_client/dds_topics.yaml`；root lock template
- 行号：DDS YAML `41,56,68,71,112,130,145`；当前无 `rc_channels`
- 当前证据：v1.16.2 exact tag、35 submodules、226/226 message equality已确认；但 checkout shallow/manifest 外，toolchain template 未解析，ARM compiler absent，`rc_channels` endpoint absent
- 验证状态：STILL_OPEN
- 影响：不能复现 firmware/profile，也不能证明 RC 安全输入或构建产物
- 触发条件：PX4 generation/build/SITL/FMUV3 promotion
- 建议：审批 origin/SHA/tag/submodules/board/toolchain，写非模板 lock；另行评审最小 DDS profile
- 验收方法：clean offline restore + 226 message compare + generator/profile hash + target build；本任务不刷写
- 是否阻塞 H0：是（关键依赖未治理）
- 是否阻塞 H1：是
- 是否阻塞后续硬件阶段：是

### [P1] Offboard Wave 3B final 仍不可由 root exact lock 恢复

- Finding ID：BBF-CUR-007
- 文档来源：Wave 3B `24_MANIFEST_MIGRATION_AND_SERIAL_DECISION.md`
- 文档原结论：local B2 HEAD 与 published root lock 不同
- 当前仓库：root + `src/offboard_cpp`
- 当前分支：`master` / `agent/wave3b-offboard-integration`
- 当前 HEAD：`0ed9d148...` / `976d6217...`
- 文件：`workspace.lock.repos`
- 行号：Offboard version `:15`
- 当前证据：lock 仍为 `cded3dc5...`，当前 final 为其后代 2 commits
- 验证状态：STILL_OPEN
- 影响：clean restore 不能得到已测试的 gate 实现
- 触发条件：恢复、CI、H1、SITL
- 建议：维护者确保 commit 可恢复并批准 exact lock 更新
- 验收方法：离线/clean restore 得到 `976d...` 或获批后继；内容 hash 与测试基线一致
- 是否阻塞 H0：是
- 是否阻塞 H1：是
- 是否阻塞后续硬件阶段：是

### [P1] H1 package boundary/依赖闭包未通过

- Finding ID：BBF-CUR-008（映射 BBF-AUD-010、031）
- 文档来源：Wave 3B canonical validation ledger
- 文档原结论：DDS wrapper 在 serial path conflict 前置退出
- 当前仓库：root
- 当前分支：master
- 当前 HEAD：`0ed9d148bfbfd22253142172bbfe93c51106fdfa`
- 文件：package profiles；`offboard_cpp`、`vision_to_dds` manifests/CMake
- 行号：`offboard_cpp/package.xml:13-18,31-33`; `CMakeLists.txt:17-24,63-77`; `vision_to_dds/package.xml:10-21`
- 当前证据：当前 boundary 仍 exit 2；Offboard 多余/未消费依赖，vision 直接使用 `builtin_interfaces` 但 manifest 未声明
- 验证状态：STILL_OPEN
- 影响：最小环境和权威 build 不可重复
- 触发条件：H1 build/packaging
- 建议：先修 canonical path；再按直接依赖闭包修 manifest/CMake，在隔离 `/tmp` build
- 验收方法：boundary PASS；目标三包 clean isolated build/test PASS，完整日志与 source identity 绑定
- 是否阻塞 H0：是
- 是否阻塞 H1：是
- 是否阻塞后续硬件阶段：是

### [P1] 感知 frame/time/device health 与 precision-landing 仍未闭环

- Finding ID：BBF-CUR-009（映射 BBF-AUD-008、009、022..024）
- 文档来源：初始 findings 与 Wave 3B handoff
- 文档原结论：视觉能力不得 promotion
- 当前仓库：`src/vision_to_dds`、`src/realsense-ros`
- 当前分支：detached
- 当前 HEAD：`0c3a0013...` / `8abb4657...`
- 文件：`vision_to_dds.cpp`、RealSense launch/config
- 行号：`vision_to_dds.cpp:75-83,126-162,260-345`
- 当前证据：默认 frame 与 T265 frame 角色没有受管一致性证明；时间/quality/reset/freshness 与掉线撤销逻辑不足；precision publisher 可参数启用但无独立 firmware/profile/SITL
- 验证状态：STILL_OPEN
- 影响：错误轴、陈旧/未来数据或错误设备可污染 PX4 estimator
- 触发条件：启用视觉 DDS 或 precision landing
- 建议：保持 production disabled；实现纯转换金样、timestamp/epoch/quality/device identity health gate
- 验收方法：frame/time/reset/dropout/non-finite 全部 0 PX4 publish；独立 SITL 后再考虑节点级
- 是否阻塞 H0：是（启用感知 profile 时）
- 是否阻塞 H1：否（核心三包 build 仍需依赖修复）
- 是否阻塞后续硬件阶段：是

### [P2] 硬件设备身份、重连与配置仍为实验级

- Finding ID：BBF-CUR-010
- 文档来源：硬件 inventory、初始 integration findings
- 文档原结论：RealSense/RPLIDAR/serial 保持 production 禁用
- 当前仓库：root nested hardware packages
- 当前分支：mixed
- 当前 HEAD：见 `03-repository-inventory.md`
- 文件：serial YAML/main、`px4_bringup/config/mavros_params.yaml`、RPLIDAR launches、RealSense launch
- 行号：serial YAML `1-4`; serial main `13-25`; MAVROS params `:4`
- 当前证据：`/dev/ttyS1`、`/dev/ttyUSB0`、`/dev/ttyTHS0:921600` 等硬编码并存；stable by-id/serial role、bounded reconnect、dropout policy 不完整
- 验证状态：STILL_OPEN
- 影响：误绑定、串口争用、掉线后陈旧状态
- 触发条件：误运行历史 bringup/driver
- 建议：继续 profile 隔离；未来按设备建立 stable identity、权限、timeout/reconnect/stop contract
- 验收方法：静态 profile/schema + 无设备节点测试；真实硬件另需明确授权
- 是否阻塞 H0：否（保持技术隔离时）
- 是否阻塞 H1：否
- 是否阻塞后续硬件阶段：是

### [P2] “current” 文档未记录新增 PX4 与 communication 漂移

- Finding ID：BBF-CUR-011
- 文档来源：`docs/handoff.md`、`docs/evidence/environment/current_environment.json`
- 文档原结论：PX4 source absent；communication absent；serial_driver_ros2 protected dirty
- 当前仓库：root/workspace
- 当前分支：master
- 当前 HEAD：`0ed9d148bfbfd22253142172bbfe93c51106fdfa`
- 文件：上述文档
- 行号：environment JSON `236-244`; handoff `20-35,42-52`
- 当前证据：PX4 source 与 communication 现已存在于新路径，旧 serial_driver_ros2 缺失
- 验证状态：CONTRADICTED
- 影响：后续 Agent 可能重复导入 source 或误判 serial 状态
- 触发条件：按旧 handoff 继续工作
- 建议：保留历史文件不改，本审查作为 dated supersession；下一波生成新的 current environment evidence
- 验收方法：current evidence 自动对比 workspace paths/HEAD/dirty，并链接 dated audit
- 是否阻塞 H0：否（但降低审计可信度）
- 是否阻塞 H1：否
- 是否阻塞后续硬件阶段：否

### [P2] 审查期间存在无法归因的 Git 远端元数据并发更新

- Finding ID：BBF-CUR-012
- 文档来源：本轮 command evidence
- 文档原结论：N/A
- 当前仓库：root
- 当前分支：master
- 当前 HEAD：`0ed9d148bfbfd22253142172bbfe93c51106fdfa`
- 文件：`.git/FETCH_HEAD`
- 行号：N/A（Git metadata）
- 当前证据：最终检查发现 mtime 为 22:29，内容指向同一 origin/master SHA；Agent 未执行 fetch/pull/remote-update，reflog/HEAD/status无对应变化
- 验证状态：NOT_VERIFIED
- 影响：并发外部操作会削弱“单一时点快照”和远端状态归因
- 触发条件：审查期间另一个用户、IDE或后台进程执行 fetch
- 建议：后续 gate 审查使用独占 worktree/文件系统 snapshot，并在开始/结束记录 refs 与 metadata
- 验收方法：独占窗口内 refs/FETCH_HEAD/worktree hash 无未授权变化
- 是否阻塞 H0：否（当前 content/HEAD 未变），但降低证据确定性
- 是否阻塞 H1：否
- 是否阻塞后续硬件阶段：否
