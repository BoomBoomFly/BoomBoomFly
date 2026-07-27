# 下一阶段计划

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

所有 Wave 4 任务必须在新分支/明确 ownership 下执行；不得清理当前 dirty checkout、
不得为通过门禁而放宽断言，不得自动进入 hardware/formal SITL。可并行只表示路径
ownership 不冲突，不表示可跳过前置 gate。

## Wave 4A：关闭 H0 静态阻塞项

### W4A-01 — Live authority/ACK/PRESTREAM gate 集成

- Task ID：W4A-01
- 当前问题：BBF-CUR-001；offline gate 未约束 live publisher
- 目标：三个 `/fmu/in/*` publisher 只有在 authority、ACK、fresh status、clock 和 PRESTREAM 全通过时可发布
- 授权修改路径：`src/offboard_cpp/include/**`、`src/**`、`test/**`、必要 config；root adapter 的新接口文件
- 禁止修改路径：PX4 source、serial、vision、现有 evidence、门禁阈值的降级
- 前置条件：冻结 C2→C++ transport interface；单一 Offboard writer
- 验收命令：nested Python contract；standalone C++ gate；新增 live FSM fake-transport unit tests；`grep` 证明 publish 仅经 gate
- 预期结果：ready 前/任何 reject/restart/duplicate writer 下 publish count 0
- 回滚方法：在独立提交中完成；失败时 `git revert <task-commit>`，不 reset 当前 dirty tree
- 风险：错误门可能 fail-open 或死锁；需 Control+Safety 双审
- 是否可并行：可与 W4A-03/04/05 并行；不可与其他 Offboard writer 并行
- 所属门禁：H0

### W4A-02 — RC/kill/auto-arm fail-closed

- Task ID：W4A-02
- 当前问题：BBF-CUR-002；`TEXT_RC` 和 auto-arm=true
- 目标：production 无 mock，fresh physical RC 与 kill latch 为 arm/mode 硬门，默认不自动解锁
- 授权修改路径：`src/offboard_cpp/CMakeLists.txt`、RC/input/FSM、profile config、tests
- 禁止修改路径：PX4 参数、硬件、SITL、降低 RC freshness/kill 标准
- 前置条件：与 W4A-01 的 gate API 冻结；PX4 RC endpoint 决策
- 验收命令：mock symbol/binary negative scan；RC stale/loss/kill/restart/parameter tests
- 预期结果：所有无效 RC 场景 ARM/MODE publish 0，恢复不自动 ACTIVE
- 回滚方法：独立提交可 `git revert`
- 风险：错误 kill/failsafe 动作可能比 PX4 原生策略更危险
- 是否可并行：设计/测试可与 W4A-01 并行，live FSM 修改必须串行
- 所属门禁：H0

### W4A-03 — Serial quarantine 与 canonical source 决策

- Task ID：W4A-03
- 当前问题：BBF-CUR-003/004/005；未跟踪执行路径、manifest/path 冲突、协议不一致
- 目标：维护者书面选择 exact origin/SHA/path/package disposition；未批准前 production discovery 为 0
- 授权修改路径：决策 ADR/manifest/profile/validator/tests；经批准后的单一 serial source
- 禁止修改路径：未经批准删除/移动 `src/communication` 或旧 gitlink；打开设备
- 前置条件：维护者确认当前 dirty state 的所有权和保留策略
- 验收命令：`verify_package_boundary.py --log-base /tmp/...`；manifest validator；serial protocol golden/negative tests
- 预期结果：唯一可追溯 disposition；包边界不再因未知路径失败；未授权 launch 无 serial writer
- 回滚方法：保留原 dirty tree；仅 revert manifest/ADR/task commit
- 风险：误认来源会丢用户更改或启用执行器写路径
- 是否可并行：可与 Offboard/PX4/vision 并行；该路径单一 writer
- 所属门禁：H0/H1

### W4A-04 — PX4 v1.16.2 provenance 与 RC endpoint 决策

- Task ID：W4A-04
- 当前问题：BBF-CUR-006；checkout 未治理、toolchain/board lock 和 `rc_channels` 缺失
- 目标：把 exact source/tag/submodules/226 message identity 写入受批准 lock；评审最小 `rc_channels` profile
- 授权修改路径：新 dated evidence/lock proposal、PX4 profile patch proposal及其离线 tests
- 禁止修改路径：当前 PX4 checkout、firmware flash、PX4 参数、硬件
- 前置条件：PX4/Release maintainer批准 origin/SHA/board/toolchain
- 验收命令：tag/submodule/message hash verifier；lock schema；profile generator static test
- 预期结果：clean offline restore 可重复；baseline/profile差异精确；不产生硬件动作
- 回滚方法：proposal/lock 独立提交可 revert；外置 checkout不改
- 风险：shallow provenance、submodule/toolchain漂移、FMUv3资源约束
- 是否可并行：可与 W4A-01/03/05 并行；PX4 profile 单一 writer
- 所属门禁：H0/H1

### W4A-05 — Vision frame/time/device health fail-closed

- Task ID：W4A-05
- 当前问题：BBF-CUR-009；frame/time/reset/quality/dropout 未闭环
- 目标：在任何 frame/finite/age/epoch/device health 不满足时不创建或不使用 PX4 vision publisher
- 授权修改路径：`src/vision_to_dds/**`、perception profile/schema、pure tests
- 禁止修改路径：启动 RealSense、写 EKF2/PX4 参数、启用 precision landing baseline
- 前置条件：frame/time ADR 和 PX4 `VehicleOdometry` 契约
- 验收命令：轴向/四元数/covariance golden tests；zero/backward/future/freeze/reset/dropout tests
- 预期结果：异常输入 publish count 0；baseline precision publisher absent
- 回滚方法：独立 commit revert
- 风险：坐标/时间错误可直接污染 estimator
- 是否可并行：可与其他子系统并行；vision路径单一 writer
- 所属门禁：H0

## Wave 4B：建立可重复 H1 构建基线

### W4B-01 — Root locks 与当前 approved commits 对齐

- Task ID：W4B-01
- 当前问题：Offboard final、PX4/communication disposition 不可由 root lock恢复
- 目标：所有 active source exact、canonical、可恢复
- 授权修改路径：`workspace*.repos`、receipt/approval、installer/validator tests
- 禁止修改路径：nested dirty checkout、moving ref、网络自动更新
- 前置条件：W4A-03/04 决策；Offboard commit可恢复
- 验收命令：manifest validators；verify-only clean/offline fixture
- 预期结果：default active全部 exact PASS
- 回滚方法：revert lock/receipt提交
- 风险：lock 指向不可达 commit
- 是否可并行：与依赖声明修复可并行；manifest单一 writer
- 所属门禁：H1

### W4B-02 — Package/依赖闭包修复

- Task ID：W4B-02
- 当前问题：boundary exit2；offboard/vision manifests与直接依赖不一致
- 目标：production三包 discovery、path和直接依赖闭合
- 授权修改路径：三包 `package.xml`/CMake、boundary profile/tests
- 禁止修改路径：扩大 production allowlist、引入 MAVROS/serial/archive包
- 前置条件：W4A H0 blockers有明确隔离；W4A-03 path决定
- 验收命令：package boundary、XML/CMake dependency tests
- 预期结果：boundary exit0；无 forbidden/transitive accident
- 回滚方法：按包独立commit revert
- 风险：依赖删除过度或偶然 underlay 掩盖问题
- 是否可并行：可按包并行，profile由单一 owner
- 所属门禁：H1

### W4B-03 — Isolated H1 build/test receipt

- Task ID：W4B-03
- 当前问题：当前 HEAD 无 build artifact/log
- 目标：从明确 source identity 在 `/tmp` 完成目标包 build/test
- 授权修改路径：仅 `/tmp` build/install/log/test-results 和 dated evidence report
- 禁止修改路径：source、workspace build/install/log、设备、ROS launch
- 前置条件：H0不为NO-GO；W4B-01/02 PASS
- 验收命令：`Scripts/test/test_dds_only.sh --output-root /tmp/<unique>`
- 预期结果：build/test/test-result 全 0，receipt绑定 root/nested HEAD与hash
- 回滚方法：保留/归档 `/tmp` evidence；不改 source
- 风险：环境污染、旧 underlay、构建脚本意外设备动作
- 是否可并行：不可与相同 source build owner并行
- 所属门禁：H1

### W4B-04 — Immutable CI execution baseline

- Task ID：W4B-04
- 当前问题：8 个 immutable lock unresolved，workflow non-required
- 目标：本地/受管 runner可重复执行所有 stable jobs
- 授权修改路径：CI lock、workflow、CI tests/docs
- 禁止修改路径：remote branch protection（另需管理员授权）、降低失败标准
- 前置条件：依赖 bundle/runner digest批准
- 验收命令：offline runner全部 job；negative fixtures继续非零
- 预期结果：无 exit78 lock blocker；artifact ledger完整
- 回滚方法：revert CI commit/lock
- 风险：供应链、retired Ubuntu 20.04 runner
- 是否可并行：可与 W4B-03设计并行，最终receipt串行
- 所属门禁：H1/release

## Wave 4C：单元测试和故障注入

### W4C-01 — Live FSM/transport failure matrix

- Task ID：W4C-01
- 当前问题：offline oracle不覆盖live FSM/publisher
- 目标：可注入 clock/transport/graph 的生产 FSM tests
- 授权修改路径：Offboard test seams、tests、fake transport
- 禁止修改路径：以mock冒充SITL/PX4消费
- 前置条件：W4A-01/02完成，H1 PASS
- 验收命令：ACK、owner、RC、DDS、odom、status、battery、restart、clock、NaN表驱动 suite
- 预期结果：所有 invalid case publish 0；完整 suite PASS
- 回滚方法：tests与seam独立commit revert
- 风险：测试过拟合实现
- 是否可并行：可按场景分工，production seam单一 owner
- 所属门禁：H2

### W4C-02 — Serial protocol/parser fault tests

- Task ID：W4C-02
- 当前问题：两端协议不一致、odd length越界、无断线恢复测试
- 目标：版本化统一协议和纯软件模拟后端
- 授权修改路径：获批 serial source/tests/common protocol
- 禁止修改路径：真实串口、执行器、放宽CRC
- 前置条件：W4A-03 canonical决定
- 验收命令：golden vectors、partial/CRC/odd/oversize/fuzz/ASan、disconnect/timeout
- 预期结果：无越界，错误帧零输出，timeout零速/关闭
- 回滚方法：revert task commit
- 风险：协议升级兼容性
- 是否可并行：可与 vision/Offboard tests并行
- 所属门禁：H2

### W4C-03 — Vision transform/time/dropout tests

- Task ID：W4C-03
- 当前问题：感知 P0/P1 无完整测试闭环
- 目标：纯函数与publisher suppression全覆盖
- 授权修改路径：vision tests/profile fixtures
- 禁止修改路径：真实相机/PX4
- 前置条件：W4A-05
- 验收命令：frame/time/quality/reset/dropout/nonfinite matrix
- 预期结果：完整相关 unit suite PASS
- 回滚方法：revert test/implementation commits
- 风险：TF语义误建模
- 是否可并行：是
- 所属门禁：H2

## Wave 4D：无硬件节点集成

### W4D-01 — 隔离 ROS graph/fake transport 集成

- Task ID：W4D-01
- 当前问题：尚无 node-level 证据
- 目标：不绑定 `/dev`、不启动 Agent/PX4 的受控 ROS graph 测试
- 授权修改路径：launch_test/fake transport/test profiles、`/tmp` logs
- 禁止修改路径：真实 `/fmu/in/*` domain、设备、Agent/MAVROS、SITL
- 前置条件：H0/H1/H2 GO；静态 launch guard批准 test入口
- 验收命令：bounded launch_test，唯一 writer、restart、zero-publish assertions
- 预期结果：H3候选证据；不宣称PX4消费
- 回滚方法：终止测试进程并revert test commit
- 风险：连接到非隔离 DDS domain
- 是否可并行：场景可并行，但domain/port必须唯一
- 所属门禁：H3

## Wave 4E：SITL 前置准备

### W4E-01 — Formal SITL readiness review（不在此任务运行）

- Task ID：W4E-01
- 当前问题：source/toolchain/profile/场景虽部分存在，promotion条件未闭合
- 目标：形成可执行、bounded、隔离、可回滚的 formal SITL run proposal
- 授权修改路径：SITL orchestration proposal、scenario bindings、readiness report
- 禁止修改路径：本任务实际启动 SITL/Agent、真实串口/硬件、mock替代PX4
- 前置条件：H0/H1/H2/H3 GO；exact PX4 lock和topic/QoS manifest
- 验收命令：static validator、dry-run parser、port/domain collision check
- 预期结果：人工批准前保持 NOT-RUN；批准后每场景可独立bounded执行
- 回滚方法：revert orchestration proposal
- 风险：误连接真实domain/serial、把synthetic当formal evidence
- 是否可并行：scenario mapping可并行；最终runbook单一owner
- 所属门禁：H4前置
