# 02 — 构建系统、测试与 CI 审查

## 1. 审查结论

当前 checkout 的最小 DDS 核心（`px4_msgs`、`offboard_cpp`、`vision_to_dds`）可以被
ROS 2 Foxy/colcon 发现；`offboard_cpp` 已具备 C++17、`-Wall -Wextra -Wpedantic`
以及 9 个 gtest case，`vision_to_dds` 具备 ament lint 注册。项目脚本、核心
launch/Python、XML 和 YAML 的本轮隔离语法检查通过；3 个核心包隔离构建成功，
Offboard 9/9 gtest 通过，但 `vision_to_dds` 当前有 3/6 个 lint executable
失败，因此本次核心测试总结果是**失败**。

但工程尚未形成“从 DDS-only manifest 到可发布 artifact”的自动化闭环。最严重的
构建问题是：当前文档推荐的裸 `colcon build --symlink-install` 会发现并可能构建
已经被架构明确禁止的 MAVROS、旧 bringup、旧 serial 和其他历史包；机器可读的
`workspace.excluded_packages` 没有被根级 colcon 配置强制应用。根仓库同时缺少
CI、DDS-only 构建入口、SITL 入口、合并门禁和发布 artifact 流程。现有测试集中在
RC 输入校验和一个源码字符串 topic 断言，未覆盖 Offboard FSM、命令 ACK、QoS、
writer 唯一性、故障注入或视觉坐标/时间逻辑。

**结论：production 不可启用。** 构建可用性是“局部已验证”，测试闭环和 CI 是
“部分实现/关键能力缺失”，不能把文档中历史的 9/9 gtest 通过等同于 production
接口、SITL 或安全验收通过。

## 2. 审查对象与方法

- 根仓库：`/home/c/BoomBoomFly`
- 分支：`agent/follow-latest-offboard`
- HEAD：`3ce28094e14ed720987c5fc6d1172e377f09b1cc`
- ROS：`/opt/ros/foxy`，`ROS_DISTRO=foxy`
- 核心自研/受管包：`src/offboard_cpp`、`src/vision_to_dds`，消息契约
  `src/px4_msgs`
- 受管第三方仓库只检查包发现、manifest 与项目级集成边界；没有把第三方上游自带
  workflow 当作 BoomBoomFly 根仓库 CI。

必读基线均存在并已完整读取：

- `README.md`
- `docs/handoff.md`
- `docs/CONTROL_AUTHORITY_MATRIX.md`
- `docs/adr/0001-dds-only-control-authority.md`
- `docs/evidence/OFFBOARD_PX4_MSGS_COMPAT_20260724.md`
- `workspace.lock.repos`
- `workspace.repos`
- `workspace.excluded_packages`
- `Scripts/README.md`
- `.gitignore`

本轮没有联网、安装依赖、启动 Agent/PX4/ROS 节点、访问串口、发送消息、修改源码
或复用工作区原有 `build/`、`install/`。隔离构建输出使用：

```text
/tmp/boomboomfly_audit_20260726_agent_b/build
/tmp/boomboomfly_audit_20260726_agent_b/install
/tmp/boomboomfly_audit_20260726_agent_b/log
```

注意：首次 `colcon list/graph` 包发现没有显式 `--log-base`；colcon 与并行审查
产生了被 `.gitignore` 忽略的工作区 `log/`（本轮观察到 `log/list_*`、
`log/graph_*` 和 `log/COLCON_IGNORE`）。按用户边界未删除或覆盖这些文件。后续
构建/测试均显式隔离到 `/tmp`。这是审查命令的副作用，不是源码变更或构建证据。

## 3. 实际检查结果

### 3.1 包发现

命令：

```bash
source /opt/ros/foxy/setup.bash
colcon list --base-paths src
colcon graph --base-paths src --packages-up-to offboard_cpp vision_to_dds ...
```

实际结果：

- `px4_msgs`、`offboard_cpp`、`vision_to_dds` 均被正确发现；
- 核心图为 `px4_msgs -> {offboard_cpp, vision_to_dds}`；
- 裸包发现同时发现 `mavros`、`mavros_extras`、`mavros_msgs`、`libmavconn`、
  `mavlink`、`px4_bringup`、`vision_to_mavros`、`serial`、`serial_driver`、
  `offboard_py`、`cv_yolo_paddle_pkg`、`opencv_cpp`；
- 除第三方仓库自身少量 ignore 标记外，没有根级 `colcon.meta`、
  `colcon.defaults` 或对应 `COLCON_IGNORE` 落实 DDS-only 排除清单。

预期结果：项目推荐的默认构建入口只发现/构建批准的 DDS-only 包，或必须显式拒绝
未落实排除清单的构建。

### 3.2 静态语法检查

命令：

```bash
bash -n Scripts/installation/uav_px4_dds_install.sh \
  Scripts/build/m1_build.sh \
  Scripts/installation/car_install.sh \
  Scripts/simulation/uav_sim.sh

PYTHONPYCACHEPREFIX=/tmp/boomboomfly_audit_20260726_agent_b/pycache \
  python3 -m compileall -q -f \
  src/offboard_cpp/launch src/offboard_cpp/text src/vision_to_dds

python3 -c '<解析核心 package.xml、workspace manifests 和 ctrl_param.yaml>'
```

实际结果：`bash/xml/yaml/python syntax: PASS`。Python 字节码仅写入 `/tmp`。

预期结果：语法可解析；同时应由 CI 自动重复执行。当前后半项未实现。

### 3.3 隔离构建与测试

命令：

```bash
source /opt/ros/foxy/setup.bash
colcon --log-base /tmp/boomboomfly_audit_20260726_agent_b/log build \
  --base-paths src/px4_msgs src/offboard_cpp src/vision_to_dds \
  --build-base /tmp/boomboomfly_audit_20260726_agent_b/build \
  --install-base /tmp/boomboomfly_audit_20260726_agent_b/install \
  --packages-up-to offboard_cpp vision_to_dds
```

实际构建结果：`px4_msgs`、`vision_to_dds`、`offboard_cpp` 全部成功，
`Summary: 3 packages finished [13min 15s]`。

测试命令复用上述隔离 build/install，并使用 `/tmp/boomboomfly_audit_20260726_agent_b/test-log`；实际结果：
- `offboard_cpp` 2/2 CTest executable、9/9 gtest case 通过；
- `vision_to_dds` 的 `copyright`、`cpplint`、`uncrustify` 失败，3/6 CTest executable 失败；
- `colcon test-result` 为 `305 tests, 0 errors, 287 failures, 0 skipped`；287 项主要是 lint 展开诊断，不是功能 case。

预期结果：3 包构建成功且 Offboard gtest、vision lint 全部通过；当前仅构建和 Offboard gtest 达标。

## 4. 正向能力

1. `offboard_cpp/CMakeLists.txt:4-9` 固定 C++17 并启用常用警告。
2. `offboard_cpp/CMakeLists.txt:69-89` 注册两个 gtest executable；当前源码包含
   7 个 RC 校验 case 和 2 个 topic contract case。
3. `vision_to_dds/CMakeLists.txt:44-52` 注册 ament lint；本轮实际执行暴露出
   3/6 lint executable 失败，说明检查存在但尚未闭合。
4. `workspace.lock.repos` 精确固定核心仓库 SHA，允许最小包构建使用精确消息版本。
5. 核心 Bash、launch/Python、XML/YAML 在本轮无硬件隔离语法检查中通过。
6. 历史兼容性证据明确区分了最初失败、后续源码修复和 9/9 gtest；本轮没有把该
   历史记录冒充新的 SITL 或实机控制验收。

## 5. 发现统计

| 等级 | 数量 |
|---|---:|
| P0 | 0 |
| P1 | 4 |
| P2 | 6 |
| P3 | 1 |

## 6. 详细发现

### BBF-BUILD-001 — DDS-only 排除清单没有被默认构建入口强制执行

- **级别：** P1
- **分类：** 构建边界 / 包发现
- **证据：**
  - `workspace.excluded_packages:1-17` 列出 14 个明确排除包；
  - `Scripts/README.md:122` 声称由安装脚本或旧 M1 脚本显式传
    `--packages-skip`；
  - `Scripts/README.md:136-143` 推荐的当前工作区构建却是裸
    `colcon build --symlink-install`；
  - 只读检查 `find src -name COLCON_IGNORE ...` 没有发现对这些根级历史包的
    排除标记；
  - 实际 `colcon list --base-paths src` 发现 MAVROS、旧 bringup、旧 serial 和
    3 个首版排除包。
- **现象：** manifest 表达的是 DDS-only，但源码树中的历史包仍会被默认 colcon
  发现；排除规则仅是旁路文本文件/脚本参数，不是默认构建契约。
- **影响：** 开发者或未来 CI 按当前 README/脚本说明构建时，可能把禁止组件和
  moving/历史源码混入构建或 release install space，导致本地与发布基线不一致。
- **触发条件：** 在仓库根目录执行裸 `colcon list` 或文档推荐的裸
  `colcon build --symlink-install`。
- **复现命令：**
  `source /opt/ros/foxy/setup.bash && colcon list --base-paths src`
- **实际结果：** 发现上述被排除/禁止包。
- **预期结果：** 默认入口只发现 DDS-only allowlist，或在检测到额外包时
  fail-closed。
- **建议修复：** 新建权威 DDS-only 构建脚本/colcon defaults，从
  `workspace.excluded_packages` 生成或校验 skip 参数；构建前比较实际包集合与
  allowlist，出现额外关键控制包时返回非零。不要依赖人工复制 skip 列表。
- **验收标准：**
  - 干净恢复工作区执行权威入口只选择批准包；
  - 每个 `workspace.excluded_packages` 条目存在时均不进入构建图；
  - 人工放入 `mavros` 或旧 bringup 后入口 fail-closed；
  - CI 对 allowlist/实际 `colcon list` 差异设置 required check。
- **依赖项：** Agent A 的 manifest/实际 checkout 审核结论。
- **预计工作量：** M
- **是否阻塞 production：** 是

### BBF-BUILD-002 — 根仓库没有 CI、required build gate 或 DDS-only release 流程

- **级别：** P1
- **分类：** CI / 发布治理
- **证据：**
  - 检查命令：
    `find .github -maxdepth 3 -type f -print`；
  - 实际结果：根目录 `.github` 不存在；
  - `Scripts/README.md:124-132` 将现有 M1 脚本明确标为历史 MAVROS 工具，并说明
    DDS-only 分组构建“后续”建立；
  - 根目录未发现 `colcon.meta`、`colcon.defaults`、`.clang-tidy`、
    `.shellcheckrc` 或 release workflow。
- **现象：** 第三方仓库各自的 workflow 不验证 BoomBoomFly 的精确 lock、包
  allowlist、核心组合构建或项目 tests；根仓库没有任何自动门。
- **影响：** package.xml/CMake/topic/launch 回归不会被自动阻止，测试失败不能
  证明会阻止合并或发布；本地历史成功无法复现为受保护的持续证据。
- **触发条件：** 任意 PR、lock 更新、核心依赖变更或 release。
- **复现命令：** 上述 `find`，以及
  `find . -maxdepth 2 -name 'colcon.*' -o -name '.clang-tidy' ...`。
- **实际结果：** 项目级配置为空。
- **预期结果：** 根 CI 使用精确 lock 恢复/验证，运行 DDS-only build/test/lint，
  且失败阻止合并和 artifact 发布。
- **建议修复：** 建立最小 CI：manifest 静态校验、包 allowlist、Foxy 容器/镜像
  digest、核心 build、test-result、launch/YAML/Bash 静态检查、diff check；
  release job 仅消费通过的同一 build，并记录 source/lock/toolchain SHA。
- **验收标准：**
  - PR 自动运行且失败返回 non-success；
  - 合并规则要求核心 build/test check（GitHub branch protection 需管理员另行
    配置并取证）；
  - release artifact 只能来自通过 required checks 的 commit；
  - CI 不联网追随 moving ref，或把 resolved HEAD 作为输入与证据。
- **依赖项：** BBF-BUILD-001；仓库管理员配置权限。
- **预计工作量：** L
- **是否阻塞 production：** 是

### BBF-BUILD-003 — 关键 Offboard 控制状态机没有行为测试

- **级别：** P1
- **分类：** 单元测试 / 安全关键逻辑
- **证据：**
  - `src/offboard_cpp/CMakeLists.txt:69-89` 只注册
    `test_rc_input` 和 `test_topic_contract`；
  - `src/offboard_cpp/test/test_rc_input.cpp:46-142` 的 7 个 case 仅覆盖 RC
    输入有效性/映射；
  - `src/offboard_cpp/test/test_topic_contract.cpp:16-40` 的 2 个 case 仅覆盖一个
    topic 常量和源码文本；
  - 扫描命令：
    `grep -RInE 'ament_add_|TEST(_F)?\\(' src/offboard_cpp src/vision_to_dds`；
  - 对测试目录搜索 `VehicleCommandAck|trajectory|odometry|QoS` 未发现对应 case。
- **现象：** `CtrlFSM.cpp` 的状态迁移、setpoint 预热、命令拒绝/超时、状态
  freshness、loss/recovery 没有单元或组件测试。测试中构造 `CtrlFSM` 只调用 RC
  freshness helper，不驱动状态机。
- **影响：** 控制逻辑的关键回归可在 9/9 gtest 继续通过时进入主分支；测试通过
  只证明局部 RC parser 和一个字面 topic。
- **触发条件：** 修改 `CtrlFSM.cpp`、输入/参数处理、PX4 消息或状态条件。
- **复现命令：** 上述测试注册/关键词扫描。
- **实际结果：** 2 个 executable、9 个 case，无 FSM/ACK/失联行为 case。
- **预期结果：** 状态迁移表及每条 fail-closed 边都具有可重复测试。
- **建议修复：** 将时间、命令发送和 PX4 输入抽象为可注入接口；为正常迁移、
  ACK 分类、超时、stale RC/odom/status、DDS loss、重启恢复和 NaN/Inf 建立
  deterministic tests，再增加 SITL 故障注入。
- **验收标准：**
  - 每个 FSM 状态和合法/非法边至少一个测试；
  - 未收到 ACCEPTED ACK 不得进入后续状态；
  - 任一关键输入 stale/loss 均进入规定安全态；
  - test 名称和结果能映射到安全需求 ID；
  - 失败阻止 CI 合并。
- **依赖项：** Agent C/D 的正式接口和安全状态定义。
- **预计工作量：** XL
- **是否阻塞 production：** 是

### BBF-BUILD-004 — 没有项目级 SITL/DDS 集成测试入口

- **级别：** P1
- **分类：** 集成测试 / SITL
- **证据：**
  - `Scripts/simulation/uav_sim.sh` 实测大小为 `0 bytes`；
  - `Scripts/README.md:158-168` 明确称该文件为空；
  - `docs/handoff.md` 声明当前没有隔离 PX4-Autopilot 源码、`gz-sim` 和项目级
    SITL 入口；
  - 根 `.github` 缺失，无 SITL workflow；
  - 现有 `test_topic_contract.cpp` 不启动 PX4 publisher，只检查源文件字符串。
- **现象：** 无法从项目权威入口验证 DDS session、真实 PX4 publisher、topic
  类型/QoS、Offboard 激活、loss/recovery 或固件 profile。
- **影响：** mock/源码级测试可能与 PX4 实际 bridge 契约分离；之前已经发生
  `vehicle_status_v1` 只有实机 discovery 才发现的回归。
- **触发条件：** PX4/px4_msgs/Agent/Offboard/topic/QoS 任一变更。
- **复现命令：**
  `stat -c '%n size=%s bytes' Scripts/simulation/uav_sim.sh`。
- **实际结果：** `size=0 bytes`。
- **预期结果：** 锁定的、隔离的、无硬件 SITL DDS 正常与故障场景。
- **建议修复：** 在 PX4 firmware profile 和工具链锁定后建立
  `sitl-dds` profile，固定 PX4/Agent/px4_msgs，使用独立 ROS domain；验收
  payload 必须来自 PX4 publisher，不允许 mock 替代。
- **验收标准：**
  - 一条命令建立并销毁隔离 SITL；
  - 验证 `vehicle_status_v1`、`rc_channels`、`battery_status`、ACK 的 type/QoS/
    publisher identity；
  - 覆盖 DDS/RC/odometry/status loss 和 command rejection；
  - 所有日志、版本、退出码落入隔离 artifact；
  - 不访问任何 `/dev/tty*`。
- **依赖项：** PX4 v1.16.2 源码/toolchain/firmware profile；BBF-BUILD-002。
- **预计工作量：** XL
- **是否阻塞 production：** 是

### BBF-BUILD-005 — `vision_to_dds` 没有功能单元测试或集成测试

- **级别：** P2
- **分类：** 测试覆盖 / 感知接口
- **证据：**
  - `src/vision_to_dds/CMakeLists.txt:44-52` 仅调用
    `ament_lint_auto_find_test_dependencies()`；
  - 包内没有 `test/` 文件；
  - 核心实现 `src/vision_to_dds/src/vision_to_dds.cpp:231,308-310` 处理 PX4
    timestamp，`80-84` 创建外部视觉 publisher，但没有测试目标。
- **现象：** 坐标转换、时间戳、TF lookup/freeze、NaN/Inf、reset、精降开关均仅
  依赖代码审查。
- **影响：** 视觉输出在编译/lint 通过时仍可能产生错误 frame、时间或消息语义。
- **触发条件：** TF、相机时间、PX4 消息或坐标变换变更。
- **复现命令：**
  `grep -RInE 'ament_add_|TEST(_F)?\\(' src/vision_to_dds`。
- **实际结果：** 仅 lint 注册，无功能测试。
- **预期结果：** 纯函数单测 + 组件级消息测试覆盖主要变换与 fail-closed 条件。
- **建议修复：** 提取坐标/时间转换纯函数；以固定向量、四元数、边界时间、失效
  TF 和非有限输入构建参数化测试；精降 profile 单独测试。
- **验收标准：**
  - ENU/NED、FLU/FRD 基准向量和姿态测试；
  - timestamp/sample timestamp 边界测试；
  - TF 缺失/stale/freeze/NaN 时不发布控制侧消息；
  - 默认 `enable_precland=false` 不创建对应 writer；
  - CI 自动执行。
- **依赖项：** Agent E 的 frame/time 契约。
- **预计工作量：** L
- **是否阻塞 production：** 是（启用视觉 profile 时）

### BBF-BUILD-006 — topic contract 测试只匹配源码字符串，未验证真实接口/QoS

- **级别：** P2
- **分类：** 接口回归测试
- **证据：**
  - `src/offboard_cpp/test/test_topic_contract.cpp:25-39` 打开
    `src/node.cpp`，对换行和字面字符串执行 `find()`；
  - `src/offboard_cpp/include/topics.hpp:7` 仅集中
    `vehicle_status_v1`，其他 `/fmu/*` 不在该文件；
  - 测试没有构造节点、查询 endpoint/type/QoS，也不检查 PX4 publisher。
- **现象：** 格式化代码可造成假失败；使用等价封装可造成假阴性；其余 topic、
  `_v1` 版本、QoS 和 namespace 没有统一契约回归。
- **影响：** 编译和 9/9 gtest 不能证明 ROS/PX4 端点兼容。
- **触发条件：** topic/QoS/namespace/节点构造或源码排版改变。
- **复现命令：** `nl -ba src/offboard_cpp/test/test_topic_contract.cpp`。
- **实际结果：** 两个纯字符串断言。
- **预期结果：** 编译期常量表 + 节点组件/图 introspection + SITL publisher
  contract 分层验证。
- **建议修复：** 集中管理所有接口和 QoS；单测常量；组件测试查询节点 endpoint；
  SITL 测试核验 PX4 publisher 的实际 type/QoS/唯一性。
- **验收标准：**
  - 覆盖所有 `/fmu/in/*`、关键 `/fmu/out/*` 和 `/offboard/*`；
  - 精确检查消息类型、版本化名称、reliability/durability/history/depth；
  - 旧 topic 字面量和默认 ROS QoS 回归均失败；
  - SITL 层至少接收一帧 PX4 原生 payload。
- **依赖项：** Agent C topic/QoS 契约；BBF-BUILD-004。
- **预计工作量：** M
- **是否阻塞 production：** 否（由对应 P1/SITL 门共同阻塞）

### BBF-BUILD-007 — launch 与配置只有人工语法检查，没有自动静态验证

- **级别：** P2
- **分类：** launch/YAML 验证
- **证据：**
  - 本轮隔离 `compileall` 和 YAML parse 通过；
  - 核心 CMake/test 扫描未发现 `launch_testing`、参数 schema 或 launch
    description 断言；
  - `offboard_cpp` 安装全部 `launch/`（`CMakeLists.txt:139-149`），其中包含
    control/demo/animal/swarm 入口，但 CI/allowlist 不存在。
- **现象：** 当前检查只能证明可解析，不能证明默认参数安全、禁止入口未被
  production profile 引入、文件路径存在或 node/action 数量符合矩阵。
- **影响：** launch 编排回归可能意外加入 writer/mock/旧节点，且无法在合并前
  fail-closed。
- **触发条件：** 修改 launch、YAML、安装路径或 profile 默认值。
- **复现命令：**
  `grep -RInE 'launch_testing|ament_add_pytest' src/offboard_cpp src/vision_to_dds`。
- **实际结果：** 无匹配。
- **预期结果：** 离线 launch AST/profile allowlist 和参数 schema 检查。
- **建议修复：** 在不执行节点的情况下解析 LaunchDescription，断言 production
  allowlist、默认禁用 demo/animal/swarm/mock/硬件；对 YAML 建立键/类型/范围
  schema。
- **验收标准：**
  - 所有项目 launch 可离线导入；
  - production profile 节点、writer、namespace 精确匹配控制权矩阵；
  - 缺失 config、未知参数、错误类型/范围均失败；
  - 测试不打开设备、不启动控制节点。
- **依赖项：** Agent D/E 的 profile 与安全参数契约。
- **预计工作量：** M
- **是否阻塞 production：** 是

### BBF-BUILD-008 — package 依赖声明与源码直接使用不一致

- **级别：** P2
- **分类：** package.xml / CMake 维护
- **证据：**
  - `offboard_cpp/package.xml:13-15,18` 声明
    `rosidl_default_generators`、`rosidl_interface_packages`、`action_msgs`，
    但包内无自定义 interface，源码扫描无 `action_msgs` 使用；
  - `offboard_cpp/CMakeLists.txt:17-20,64-67` 要求/链接 tf2 与 OpenCV，源码扫描
    没有 tf2/OpenCV 使用（Eigen 有直接使用）；
  - `vision_to_dds/include/vision_to_dds/vision_to_dds.hpp:7` 直接 include
    `builtin_interfaces/msg/time.hpp`，但
    `vision_to_dds/package.xml:10-21` 没有直接声明 `builtin_interfaces`；
  - `offboard_cpp/package.xml:32-33` 声明 ament lint，但
    `CMakeLists.txt:69-89` 未调用 `ament_lint_auto`。
- **现象：** 不必要依赖扩大构建面，直接依赖缺失依靠传递依赖偶然成功，测试依赖
  声明和实际注册漂移。
- **影响：** 最小环境、依赖升级或打包时可能失败；依赖图不能准确表达源码契约。
- **触发条件：** 干净 rosdep/二进制依赖环境、上游导出关系改变或 release build。
- **复现命令：**
  `grep -RInE 'OpenCV|action_msgs|rosidl|builtin_interfaces' ...`。
- **实际结果：** 得到上述声明/使用差异。
- **预期结果：** 每个直接 include/链接都有直接依赖；无未使用 build 依赖。
- **建议修复：** 用 `ament_lint_cmake`/`rosdep` 和 include 扫描整理 manifest；
  删除无接口的 rosidl group/generator 与未使用库，补
  `builtin_interfaces`；决定并落实 offboard lint 注册。
- **验收标准：**
  - 干净最小环境 `rosdep check` 成功；
  - package.xml 与 CMake 的依赖集合有审查清单；
  - 删除任一传递依赖不影响正确直接依赖；
  - `ament_lint` 声明与实际 test 注册一致。
- **依赖项：** 无。
- **预计工作量：** S
- **是否阻塞 production：** 否

### BBF-BUILD-009 — 缺少统一 lint、静态分析、sanitizer 与 warnings-as-errors 门

- **级别：** P2
- **分类：** 质量门
- **证据：**
  - 根目录检查未发现 `.clang-tidy`、`.clang-format`、`.shellcheckrc`、
    `.pre-commit-config.yaml` 或 code coverage 配置；
  - `offboard_cpp/CMakeLists.txt:7-9` 和
    `vision_to_dds/CMakeLists.txt:14-16` 仅启用
    `-Wall -Wextra -Wpedantic`，未将项目代码 warning 设为错误；
  - `offboard_cpp` 声明 lint test dependency 但未注册；
  - 隔离测试实际为 Offboard 9/9 gtest 通过，但 vision 的 `copyright`、
    `cpplint`、`uncrustify` 失败，3/6 CTest executable 失败；
  - `colcon test-result` 展开为 305 项、287 项失败，集中在缺少 LICENSE/版权声明、
    header guard/include、tab/格式等 lint 诊断；
  - 根 CI 缺失。
- **现象：** vision 已注册的 lint 在精确 checkout 实际失败，却没有根 CI 阻止
  合并；Offboard lint 未注册，其他静态/sanitizer 门也不统一。
- **影响：** 当前核心组合不是 test-clean，工程质量回归仍主要依靠人工审查。
- **触发条件：** 任意源码/脚本变更。
- **复现命令：** 根质量配置 `find` 与上述 CMake 行检查；隔离执行
  `colcon test --packages-select offboard_cpp vision_to_dds`。
- **实际结果：** 无根级门；已注册的 vision lint 当前失败。
- **预期结果：** 第一方代码 warning-free，并按风险分层运行 lint/static/sanitizer。
- **建议修复：** 对第一方 targets 开启 warnings-as-errors；增加
  clang-format/clang-tidy/cppcheck、shellcheck；在 x86_64/可用平台运行
  ASan/UBSan（不要强迫所有第三方 target 使用项目 flags）。
- **验收标准：**
  - 当前 `vision_to_dds` 6/6 lint executable 通过；
  - 第一方 warning 导致 CI 失败；
  - clang-tidy/shellcheck 对固定版本运行；
  - ASan/UBSan 单测无报告；
  - 第三方 warning 与第一方门分离、版本固定。
- **依赖项：** BBF-BUILD-002。
- **预计工作量：** M
- **是否阻塞 production：** 否

### BBF-BUILD-010 — 核心包 C++ 标准未统一或说明兼容边界

- **级别：** P3
- **分类：** 工具链一致性
- **证据：**
  - `offboard_cpp/CMakeLists.txt:4-5` 强制 C++17；
  - `vision_to_dds/CMakeLists.txt:9-12` 仅在未设置时默认 C++14；
  - 根仓库没有 toolchain preset/container digest 或 C++ 标准政策。
- **现象：** 同一核心组合存在不同且语义不同的标准设置，外部环境可覆盖 vision
  标准但不能覆盖 offboard 标准。
- **影响：** 当前可编译不代表跨 CI/开发机编译行为完全一致；未来公共库和工具链
  升级增加维护成本。
- **触发条件：** 更换编译器、根级设置 `CMAKE_CXX_STANDARD`、共享代码。
- **复现命令：** `nl -ba` 检查两个 CMake。
- **实际结果：** C++17 required 与 C++14 default 并存。
- **预期结果：** 根级文档/CI 明确支持标准；包采用一致语义，或记录必须不同的原因。
- **建议修复：** 在工具链基线中统一第一方 C++ 标准和最低编译器；避免全局影响
  第三方仓库。
- **验收标准：**
  - CI 输出编译器/CMake/C++ 标准；
  - 两核心包标准行为一致或有 ADR 说明；
  - 至少两种受支持构建环境结果一致。
- **依赖项：** 工具链冻结任务。
- **预计工作量：** S
- **是否阻塞 production：** 否

### BBF-BUILD-011 — 测试/构建证据和 release artifact 没有机器可复核链

- **级别：** P2
- **分类：** 构建证据 / artifact
- **证据：**
  - `.gitignore:1-3` 忽略 `build/`、`install/`、`log/`，这是正确的源码卫生策略；
  - `docs/evidence/OFFBOARD_PX4_MSGS_COMPAT_20260724.md` 保存的是人工整理摘要，
    没有本次 HEAD 对应的 JUnit、完整 compiler invocation、环境清单或 install
    artifact hash；
  - 根 `.github` 和 release workflow 缺失；
  - `docs/handoff.md` 明确 firmware artifact SHA、toolchain 和 SITL 证据尚缺。
- **现象：** 可以阅读“曾通过”，但不能由机器把 release artifact 追溯到同一
  commit/lock/toolchain/test run。
- **影响：** 历史结论容易被当作当前事实；发布回滚和二进制来源无法独立复核。
- **触发条件：** 发布、环境迁移、事故回溯或依赖更新。
- **复现命令：** 检查根 workflow、evidence 文件树和 `.gitignore`。
- **实际结果：** 只有摘要文档/历史证据，无自动 artifact chain。
- **预期结果：** 源码不提交可再生构建目录，但 CI 持久化版本化日志、JUnit、
  SBOM/依赖清单和 artifact hashes。
- **建议修复：** 定义证据 schema；CI 生成环境/manifest/命令/退出码/JUnit/
  warnings/artifact SHA-256，release manifest 引用 immutable CI run。
- **验收标准：**
  - 任一 release 可从 SHA 追溯 lock、工具链、构建日志和测试结果；
  - artifact SHA-256 与下载/回滚包一致；
  - 历史 evidence 明确 `captured_at` 与适用 HEAD；
  - 不把工作区 `build/install/log` 纳入 Git。
- **依赖项：** BBF-BUILD-002；firmware profile 构建任务。
- **预计工作量：** M
- **是否阻塞 production：** 是（发布链）

## 7. 未验证项与边界

- 未运行硬件、Agent、MAVROS、Offboard、视觉、相机、雷达或任何 launch。
- 未访问 `/dev/tty*`，未发送 ROS/PX4 消息。
- 未运行全工作区构建：历史/第三方包范围巨大，且默认包集合违反当前 DDS-only
  baseline；这不是代码失败证据。
- 未运行 PX4 firmware、FMUv3 或 SITL 构建：当前仓库没有 PX4-Autopilot
  checkout/toolchain，且禁止联网下载。
- 未验证 GitHub branch protection、required checks 和 release 设置：根仓库无
  workflow，且本轮禁止联网；外部设置标记为**未验证**，不声称其不存在。
- 未运行 clang-tidy/cppcheck/shellcheck/sanitizer：项目没有固定配置/版本，
  不在本轮安装工具。
- 完整第三方 test suite 未运行；其上游 CI 不能替代 BoomBoomFly 集成 CI。
- 隔离核心构建和已注册测试已完成，结果见 3.3；没有把测试失败误报为环境缺依赖
  或构建失败。

## 8. 建议执行顺序

1. 先修 BBF-BUILD-001，建立 DDS-only 包 allowlist 与权威构建入口。
2. 在此基础上修 BBF-BUILD-002，把最小核心 build/test/static checks 变为 required
   CI；同时落地 BBF-BUILD-008/009 的低成本清理。
3. 并行设计 BBF-BUILD-003 与 Agent C/D 的安全需求—测试映射。
4. PX4 firmware profile/toolchain 固定后实施 BBF-BUILD-004 和 006。
5. 在视觉坐标/时间契约冻结后实施 BBF-BUILD-005。
6. 最后建立 BBF-BUILD-011 的 release artifact 与四级验收证据链。
