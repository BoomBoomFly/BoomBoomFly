# 05 感知、硬件接口与系统集成审查

## 1. 审查结论

本报告仅基于当前 checkout 的源码、配置、manifest、Git 状态和既有证据进行静态审查。未启动 RealSense、RPLIDAR、USB Camera、VPU、MAVROS、Micro XRCE-DDS Agent、PX4、Offboard 或任何硬件 launch；未访问任何 `/dev` 设备；未读取或修改当前飞控参数。

当前感知到 PX4 的生产链路不可启用。主要阻塞是：外部视觉坐标系契约与实际 RealSense TF 命名未闭合；ROS/相机/PX4 时间域、数据新鲜度、复位与质量语义未建立可验证的安全契约；缺少受管的感知启动 profile 和 EKF2 前置检查；历史 T265 缺失时没有经测试的降级路径；旧 MAVROS/串口 launch 虽被文档禁止且列入 excluded，仍作为可执行源码存在并可能争用 DDS 专用串口。

### 状态分类

| 能力 | 当前判定 | 依据 |
|---|---|---|
| RealSense 上游驱动 | 已存在，未做本轮动态验证 | `src/realsense-ros/` |
| `vision_to_dds` 外部视觉发布器 | 已实现基础发布，安全契约部分实现 | `src/vision_to_dds/src/vision_to_dds.cpp` |
| 外部视觉 frame/TF 契约 | 文档声明与源码实现均不完整，未通过测试验证 | 默认 frame 与驱动实际 frame 不一致；无坐标转换测试 |
| 时间同步与 freshness | 部分实现时间戳填充，缺少跨时钟契约和故障处理 | ROS `now()` 与 TF stamp 混用；无 stale/reset 检测 |
| T265 缺失降级 | 文档记录硬件缺失；源码未验证安全降级 | 既有证据为历史记录；上游 launch 可无限等待设备 |
| D435/T265 角色划分 | 仅有零散文档/上游 launch 线索，项目 profile 缺失 | 无受管项目级 launch/YAML |
| 精准降落 | 代码路径存在但默认关闭；完整 profile 缺失 | 发布器可选，camera frame 参数未参与计算 |
| RPLIDAR | 仅有上游驱动；项目集成未完成 | 默认 `/dev/ttyUSB0`，udev 规则不按序列号区分 |
| USB Camera/VPU | 历史且 excluded 的路径存在，当前主线未集成 | `workspace.excluded_packages` 及旧 launch |
| EKF2 外部视觉前置条件 | 当前飞控状态未验证 | 只有 2026-07-24 历史参数快照 |

## 2. 历史证据与当前事实边界

- `docs/handoff.md:114-127` 记录的是既有硬件盘点：Jetson Orin Nano、D435 序列号 `227323021826`、USB Camera VID:PID `0bda:5858`、VPU `03e7:2150`，并记录 T265 和 RPLIDAR 当时未出现。这些是历史证据，本轮未重新枚举 USB，也不能推断设备当前仍连接或仍缺失。
- `docs/evidence/px4_params_full_20260724T171437+0800.json` 是 2026-07-24 的历史快照。该快照中 `EKF2_EV_CTRL=0`、`UXRCE_DDS_CFG=0` 等值不能代表当前飞控；`docs/handoff.md` 又记录 2026-07-25 后续 transport 调整，因此不得用该 JSON 声称当前 EKF2 或 DDS 参数状态。
- `docs/adr/0001-dds-only-control-path.md` 和 `docs/CONTROL_AUTHORITY_MATRIX.md` 将 DDS-only、单 writer、硬件 launch 隔离作为当前权威约束。旧 MAVROS/`px4_bringup` 路径只能作为风险对象审查，不能作为当前批准方案。
- `src/realsense-ros/`、`src/rplidar_ros/` 属于外部依赖仓库；其中通用默认值本身不等于根仓库缺陷。根仓库的缺陷在于没有受管的覆盖配置、设备身份策略、健康门和验收证据。

## 3. 详细发现

### BBF-INT-001

- **ID:** BBF-INT-001
- **级别:** P0
- **分类:** 外部视觉坐标系 / TF / PX4 接口
- **归属:** 根仓库 `vision_to_dds` 集成契约；涉及外部依赖 `realsense-ros`
- **证据:**
  - `src/vision_to_dds/src/vision_to_dds.cpp:24-31`：`rotateWorldToBody()` 只对 X/Y 进行平面旋转，Z 不变。
  - `src/vision_to_dds/src/vision_to_dds.cpp:90-109`：默认 target/source frame 为 `/camera_odom_frame`、`/camera_link`，默认角度为 `gamma=-π/2`、`yaw=+π/2`。
  - `src/vision_to_dds/src/vision_to_dds.cpp:262-336`：用自定义旋转和四元数乘法后，将结果声明为 PX4 `POSE_FRAME_FRD`。
  - `src/realsense-ros/realsense2_camera/include/constants.h:100-101`：上游默认 base/odom frame 为 `link`、`odom_frame`。
  - `src/realsense-ros/realsense2_camera/src/base_realsense_node.cpp:413-496`：T265 pose/odom 的父 frame 为 `odom_frame`，子 frame 为 `${camera_name}_pose_frame`。
  - `src/px4_msgs/msg/VehicleOdometry.msg:9-18`：PX4 world-fixed frame 为 NED/FRD，position、quaternion 必须符合该枚举语义。
  - 检查命令：`nl -ba src/vision_to_dds/src/vision_to_dds.cpp`；`rg -n "DEFAULT_ODOM_FRAME_ID|POSE_FRAME_FRD|camera_odom_frame|camera_link" src/vision_to_dds src/realsense-ros src/px4_msgs/msg/VehicleOdometry.msg`
  - 实际结果：桥接器默认 frame 与驱动默认 frame 不一致；转换是自定义常量旋转，未发现 ENU/NED、FLU/FRD 的成体系数学说明或测试。
  - 预期结果：输入 TF、输出 PX4 frame、轴方向、四元数方向和符号应有单一契约，并由数值测试证明。
- **现象:** 代码将转换结果标记为 FRD，但未证明平面旋转加 Z 不变可对所有输入满足 ENU/NED、FLU/FRD 约定；默认 TF 名称也无法直接匹配上游 RealSense 输出。
- **影响:** 错误的坐标轴、符号或 frame 可能向 EKF2 注入方向相反或姿态错误的测量，导致估计跳变、控制发散或危险 setpoint。
- **触发条件:** 启用 `vision_to_dds`，特别是以默认参数连接 T265/RealSense TF，或更改 camera orientation 后仍沿用常量旋转。
- **建议修复:** 定义版本化 frame 契约；使用经审查的完整 3D 刚体变换；项目 profile 必须显式给出 source/target frame；拒绝缺失或非预期 TF；禁止以默认魔数推断安装姿态。
- **验收标准:**
  - 对 ENU→NED、FLU→FRD 的单位向量、姿态和复合旋转建立数值单元测试；
  - project launch 中实际 frame 与 RealSense 产生的 TF 完全匹配；
  - 以已知姿态/位移 bag 或 SITL publisher 验证 PX4 接收值及符号；
  - TF 缺失、跳变或 frame 不匹配时不发布 `/fmu/in/vehicle_visual_odometry`；
  - 坐标契约、安装外参、frame tree 与测试向量写入权威文档。
- **依赖项:** 设备角色/启动 profile（BBF-INT-003、BBF-INT-004）；PX4 DDS 契约审查结果。
- **预计工作量:** L
- **是否阻塞 production:** 是

### BBF-INT-002

- **ID:** BBF-INT-002
- **级别:** P0
- **分类:** 时间同步 / freshness / 数据有效性
- **归属:** 根仓库 `vision_to_dds`；涉及 RealSense 时钟行为
- **证据:**
  - `src/vision_to_dds/src/vision_to_dds.cpp:12-21`：`toUsec()` 直接转换 ROS stamp。
  - `src/vision_to_dds/src/vision_to_dds.cpp:262-336`：`timestamp` 使用节点 `now()`，`timestamp_sample` 使用 TF stamp；未检查二者时间域、年龄、未来时间、跳变、NaN/Inf。
  - 同一函数将 `reset_counter=0`、`quality=1` 固定写入，并使用固定 variance；没有依据传感器状态调整。
  - `src/realsense-ros/realsense2_camera/src/base_realsense_node.cpp:640-676`：硬件时钟路径含“设备时钟可能周期性复位”的处理背景，并以 ROS 基准映射相机时间。
  - `src/px4_msgs/msg/VehicleOdometry.msg:5-31`：timestamp 定义为系统启动以来微秒，并明确 reset counter、quality 语义。
  - `src/vision_to_dds/src/vision_to_dds.cpp:340-343`：诊断 path 持续追加，无上限。
  - 检查命令：`rg -n "timestamp|timestamp_sample|reset_counter|quality|position_variance|orientation_variance|body_path" src/vision_to_dds/src/vision_to_dds.cpp src/px4_msgs/msg/VehicleOdometry.msg`
  - 实际结果：未发现跨时钟同步模型、最大样本年龄、时间倒退/复位检测、质量退化或 finite 检查。
  - 预期结果：发布前验证时间域、新鲜度、连续性和数值有效性；传感器 reset/失锁必须可观测并 fail-closed。
- **现象:** 桥接器把不同来源的时间直接填入 PX4 消息，同时恒定宣称质量和 reset 状态。
- **影响:** 陈旧、未来、复位后或非有限的测量可能被当作有效外部视觉数据；PX4 侧无法可靠区分传感器重启与连续轨迹。
- **触发条件:** RealSense 重连/复位、ROS 时间跳变、仿真时间切换、TF 缓存陈旧、传感器输出 NaN/Inf 或节点阻塞。
- **建议修复:** 明确 PX4 与 ROS 时间同步策略；实现最大年龄、单调性、有限值、跳变和重启检测；正确推进 reset counter；质量和 covariance 来自真实状态；不健康时停止发布并输出结构化诊断。
- **验收标准:**
  - 时间戳正常、倒退、冻结、未来、设备 reset 的单元测试全部通过；
  - stale/NaN/Inf/跳变样本不进入 `/fmu/in/*`；
  - reset counter 在设备/轨迹复位时递增并具有测试；
  - 质量、covariance 和健康状态有明确来源，不再固定伪装为有效；
  - SITL 注入时间冻结与重连时，EKF/控制链保持安全并产生可追溯诊断。
- **依赖项:** PX4 时间同步方案；BBF-INT-001 frame 契约；测试基础设施。
- **预计工作量:** L
- **是否阻塞 production:** 是

### BBF-INT-003

- **ID:** BBF-INT-003
- **级别:** P1
- **分类:** 受管 launch / EKF2 前置条件 / 集成 profile
- **归属:** 根仓库
- **证据:**
  - `src/vision_to_dds/CMakeLists.txt:44-52`：测试段仅启用 lint；未发现坐标、时间、TF 或消息契约测试。
  - 对 `src/vision_to_dds` 执行 `find ...` 与 `rg -n "launch|yaml|EKF2|diagnostic"`：未发现受管的项目级 launch/YAML/EKF2 preflight。
  - `src/vision_to_dds/src/vision_to_dds.cpp:79-84`：节点构造时直接创建 `/fmu/in/vehicle_visual_odometry` publisher。
  - 历史 `docs/evidence/px4_params_full_20260724T171437+0800.json` 中 `EKF2_EV_CTRL=0`，但该文件早于后续 transport 变更，不能代表当前值。
  - `docs/adr/0001-dds-only-control-path.md`：当前没有批准的硬件项目 launch，要求隔离验证。
  - 实际结果：具备发布代码，但缺少声明设备、frame、时间、QoS、EKF2 条件、健康门和禁止误启动的单一 profile。
  - 预期结果：生产候选 profile 应 fail-closed，启动前只读验证所有前置条件，且默认不产生控制/硬件副作用。
- **现象:** 感知链没有从设备身份、TF 到 DDS 与 EKF2 的受管配置源，历史参数快照也无法证明当前飞控已满足前置条件。
- **影响:** 操作者可能以错误 frame、错误设备或错误 EKF2 融合设置启动外部视觉；环境差异难以复现。
- **触发条件:** 手工运行 `vision_to_dds`、复制上游 launch、依赖节点默认参数或将历史快照当作当前配置。
- **建议修复:** 建立只读 preflight 与分层 profile（SITL、sensor-only、bench、production）；显式声明设备 serial、frame、外参、时间策略、QoS、预期 PX4 参数和 writer 权限；默认禁止发布，健康条件全部满足后再授权。
- **验收标准:**
  - 所有 profile 有 schema、默认安全值和静态验证；
  - 当前 PX4 参数以经授权的只读快照核验，历史快照仅作比较；
  - 缺少设备/TF/时间同步/EKF2 前置条件时启动失败且不发布 `/fmu/in/*`；
  - sensor-only profile 不启动控制节点，不 arm、不切模式；
  - CI 验证 launch 参数、topic、frame 和 profile 互斥性。
- **依赖项:** BBF-INT-001、BBF-INT-002；DDS 单 writer/owner 机制。
- **预计工作量:** L
- **是否阻塞 production:** 是

### BBF-INT-004

- **ID:** BBF-INT-004
- **级别:** P1
- **分类:** RealSense 设备识别 / 角色 / 缺失降级
- **归属:** 根仓库集成策略；涉及外部依赖默认行为
- **证据:**
  - `docs/handoff.md:114-127`：历史盘点中 D435 存在，T265 不存在；本轮未动态验证。
  - `src/realsense-ros/realsense2_camera/launch/rs_launch.py:25-74`：`serial_no`、`usb_port_id`、`device_type` 默认空；`wait_for_device_timeout=-1`；launch 直接启动节点。
  - `src/realsense-ros/realsense2_camera/launch/rs_d400_and_t265_launch.py:25-30`：组合 launch 仅按 `d4.`/`t265` 类型匹配，未固定序列号。
  - `src/realsense-ros/realsense2_camera/src/realsense_node_factory.cpp:90-170,264-335`：支持 serial/port/type 选择，但非正超时可持续等待设备；USB2 会降级。
  - `src/realsense-ros/realsense2_camera/launch/rs_multi_camera_launch.py:68-73`：示例使用零值静态变换连接两个相机，不能作为真实外参。
  - `src/realsense-ros/realsense2_camera/launch/rs_t265_launch.py` 当前为未跟踪文件，而该依赖的 CMake 安装整个 launch 目录。
  - 实际结果：上游能力可支持稳定选择，但根仓库未提供 serial/角色/外参/超时/降级的受管配置；T265 launch 的本地未跟踪状态不可复现。
  - 预期结果：D435、T265 职责和设备身份明确；缺失任一设备时进入已定义安全状态，而不是无限等待或误选同型号设备。
- **现象:** D435/T265 角色没有在项目配置中编码，缺失 T265 的安全降级未实现/未测试。
- **影响:** 设备枚举顺序变化可能绑定错误设备；T265 缺失或掉线时系统可能挂起、反复重连或继续使用陈旧外部视觉。
- **触发条件:** 多台同型 RealSense、USB 重枚举、USB2 降速、T265 不存在/重连、依赖干净恢复后未跟踪 launch 消失。
- **建议修复:** 使用 serial/稳定 USB topology 双重识别；定义 D435（深度/图像）与 T265（里程计）的职责；设置有限设备等待；设备丢失立即撤销视觉健康与 DDS 发布许可；外参必须来自标定 artifact。
- **验收标准:**
  - 错误序列号、重复设备、USB2、设备拔出均有自动化测试或台架证据；
  - T265 不存在时控制链不启用外部视觉依赖能力；
  - D435-only 与 T265-enabled profile 明确分离；
  - 标定外参具备 SHA-256、设备序列号、日期和适用 frame；
  - 干净恢复不依赖未跟踪 launch 文件。
- **依赖项:** BBF-INT-003；设备清单与 udev 策略。
- **预计工作量:** M
- **是否阻塞 production:** 是

### BBF-INT-005

- **ID:** BBF-INT-005
- **级别:** P1
- **分类:** 精准降落接口
- **归属:** 根仓库 `vision_to_dds`
- **证据:**
  - `src/vision_to_dds/src/vision_to_dds.cpp:129-162`：precision landing 默认关闭；开启后发布 `/fmu/in/landing_target_pose`，声明 camera frame 参数。
  - `src/vision_to_dds/src/vision_to_dds.cpp:209-254`：计算中查找 target 和 vehicle 相对 world 的 TF，使用同一平面旋转，固定 covariance/valid 标志。
  - `rg -n "precland_camera_frame_id_" src/vision_to_dds`：该参数只被声明、读取和打印，未用于 TF 查询或坐标计算。
  - `src/px4_msgs/msg/LandingTargetPose.msg:1-26`：消息要求相对/绝对位置遵守 north-aligned NED 等 frame 语义。
  - 未发现 precision-landing 独立 launch、YAML、固件 topic profile、目标 freshness/置信度测试。
  - 实际结果：存在实验性发布路径，但 camera frame 配置无效，valid/covariance 恒定，完整闭环证据缺失。
  - 预期结果：精准降落必须是独立、默认禁用、固件 topic 明确、目标丢失 fail-closed 的 profile。
- **现象:** 可选发布器并未形成可验证的精准降落产品能力。
- **影响:** 目标 TF 陈旧、坐标错误或置信度不足时仍可能被标记为有效，造成错误降落目标。
- **触发条件:** 将 `precland_enabled` 设为 true，并在未完成独立 firmware/profile 验收时使用。
- **建议修复:** 保持 production 禁用；修正 camera frame 的真实使用；增加 target age/quality/finite 检查；独立固件 profile 与 SITL 故障注入；不得与普通视觉里程计混为同一验收。
- **验收标准:**
  - 默认和 production profile 中 precision landing 保持关闭，直至专项批准；
  - camera frame 参数参与受测试的完整转换；
  - 目标丢失、陈旧、跳变、NaN/Inf 时 `rel_pos_valid=false` 或停止发布并触发安全策略；
  - PX4 实际 publisher/bridge 端确认 topic 可用，不用 mock 代替；
  - SITL、拆桨台架分别通过正常与目标丢失场景。
- **依赖项:** BBF-INT-001、BBF-INT-002；PX4 firmware DDS profile。
- **预计工作量:** L
- **是否阻塞 production:** 是，仅阻塞精准降落能力；在功能完全禁用且无法误启时不阻塞其他 production profile。

### BBF-INT-006

- **ID:** BBF-INT-006
- **级别:** P1
- **分类:** 旧 launch / 串口所有权 / 意外启动
- **归属:** 根仓库治理边界及 excluded 历史包
- **证据:**
  - `src/px4_bringup/launch/include/px4_fly.launch.py:8-47`：启动 T265，并延时启动 MAVROS/视觉桥。
  - `src/px4_bringup/launch/start_all_2025TI.launch.py:8-48`：组合启动 px4、串口、图像和旧 offboard 路径。
  - `src/px4_bringup/launch/include/serial_and_image_2025TI.launch.py:8-55`：自动启动 serial driver、USB camera 与 YOLO。
  - `src/px4_bringup/config/mavros_params.yaml:4`：MAVROS hardcode `/dev/ttyTHS0:921600`。
  - `src/t265_all_nodes/...` 的历史 launch hardcode `/dev/ttyUSB0:57600` 和 USB port `2-2`。
  - `docs/handoff.md` 与 ADR 将 `/dev/ttyTHS0:921600` 作为 DDS transport，并禁止旧 MAVROS/project launch；这些包也列在 `workspace.excluded_packages`。
  - Agent A 的静态包发现显示 excluded 包仍可能被普通 workspace discovery 发现；excluded 不是不可执行隔离。
  - 实际结果：策略上禁止，但源码入口仍能组合启动硬件和控制节点，并可能争用 DDS 串口。
  - 预期结果：历史路径应被机械隔离，不能被默认 build/discovery/launch 误触发，串口所有权应集中声明。
- **现象:** 文档禁令未转化为技术隔离和 launch 安全门。
- **影响:** 误运行旧 launch 可能同时启动 MAVROS、串口、感知和控制 writer，争用 TELEM2/DDS transport，违反控制权矩阵。
- **触发条件:** 操作者按旧文档或包名运行 launch；CI/colcon 未应用 excluded 清单；串口设备节点复用。
- **建议修复:** 在不删除历史证据的前提下将旧包从受管 workspace 机械隔离；为批准 launch 建立 allowlist；串口资源设单一 owner；加入静态测试禁止 production 配置引用 MAVROS、旧 offboard 或 `/dev/ttyTHS0`。
- **验收标准:**
  - 默认 build/list/launch 不包含旧 `px4_bringup`、MAVROS、历史 serial/control 包；
  - CI 扫描批准 profile，禁止 `/dev/ttyTHS0` 被 DDS 之外组件引用；
  - 任意批准 launch 不会隐式启动硬件或控制 writer；
  - serial ownership 文档、配置和运行时诊断一致；
  - 旧路径只在明确的 archival 标识下保留且有不可误用说明。
- **依赖项:** workspace 隔离机制；控制权 graph guard。
- **预计工作量:** M
- **是否阻塞 production:** 是

### BBF-INT-007

- **ID:** BBF-INT-007
- **级别:** P2
- **分类:** RPLIDAR 设备识别 / 参数化 / TF
- **归属:** 根仓库集成缺失；涉及外部依赖默认配置
- **证据:**
  - `src/rplidar_ros/src/node.cpp:79-97`：通用默认串口 `/dev/ttyUSB0`，baud 依赖模型。
  - `src/rplidar_ros/launch/`：各型号 launch 使用不同 baud，但多数默认 `/dev/ttyUSB0`，frame 为 `laser`。
  - `src/rplidar_ros/scripts/rplidar.rules:3`：按 CP210x VID:PID `10c4:ea60` 建立 `rplidar` symlink，未按设备序列号区分，并设置 `MODE="0777"`。
  - `docs/handoff.md:114-127`：历史盘点当时未检测到 RPLIDAR；本轮未动态验证。
  - 未发现根仓库级 RPLIDAR 型号、serial、baud、TF 外参、health timeout 或 USB 带宽配置。
  - 实际结果：只有上游通用能力，没有项目级稳定身份和集成验收。
  - 预期结果：明确型号、baud、稳定设备名、最小权限、frame/TF 与缺失降级。
- **现象:** RPLIDAR 接入仍处于未集成状态。
- **影响:** 同类 CP210x 设备可能被错误映射；错误 baud/model、过宽设备权限或缺失 TF 会导致不可复现和错误数据。
- **触发条件:** 安装 RPLIDAR、连接多个 USB 串口设备、设备枚举变化或直接使用上游默认 launch。
- **建议修复:** 先确认硬件型号和 serial，再建立项目 udev 规则与最小权限；固定 baud/frame；标定 TF；定义无雷达 profile 与设备掉线行为。
- **验收标准:**
  - udev 名称按 serial/明确属性唯一绑定，权限不使用 0777；
  - 型号和 baud 在 profile 中固定并经过只读探测/台架验证；
  - `laser` 到机体 frame 的外参有标定 artifact；
  - 雷达缺失/掉线不会启动依赖能力，且有诊断；
  - USB 带宽与 RealSense 并发台架测试有证据。
- **依赖项:** 当前硬件清单；设备到货/可用后方能动态验收。
- **预计工作量:** M
- **是否阻塞 production:** 否，前提是所有 production profile 明确不依赖且不启动 RPLIDAR。

### BBF-INT-008

- **ID:** BBF-INT-008
- **级别:** P2
- **分类:** USB Camera / VPU / 历史感知路径
- **归属:** excluded 历史包
- **证据:**
  - `src/opencv_cpp/launch/image.launch.py:10-12`：默认设备 `/dev/usb_camera`，根仓库未发现对应 udev 规则。
  - `src/opencv_cpp/src/...`：节点另有 `/dev/video0` 默认值并固定 1280×720。
  - `src/cv_yolo_paddle_pkg/launch/yolo_node.launch.py:16,36`：hardcode 旧 `/home/c/px4_ws/...` 模型和输出路径，并默认保存视频。
  - `src/cv_yolo_paddle_pkg/...`：推理路径调用 CUDA，未发现历史 Myriad VPU 的设备选择或 OpenVINO 配置。
  - `workspace.excluded_packages` 与 `Scripts/README.md` 将这些包排除在当前主线。
  - `docs/handoff.md:114-127` 的 USB Camera/VPU 信息为历史盘点，本轮未动态验证。
  - 实际结果：历史代码不可移植、未绑定稳定设备身份，也未形成 VPU 或 USB 带宽策略。
  - 预期结果：如重新纳入主线，应有明确硬件后端、相机 serial/udev、资源预算和可复现模型 artifact。
- **现象:** USB Camera/VPU 路径是保留的历史实验，不是可发布能力。
- **影响:** 误用会因个人路径、设备枚举、计算后端和磁盘写入行为产生失败或资源争用。
- **触发条件:** 直接运行旧 launch，或将 excluded 包误认为当前支持能力。
- **建议修复:** 当前保持禁用并标记 archival；只有明确业务需要时才重建受管 profile，禁止沿用个人绝对路径；模型、后端、输出和设备选择全部参数化。
- **验收标准:**
  - 默认 workspace 和批准 launch 不发现/不启动该历史路径；
  - 若恢复开发，模型 artifact 有来源、许可证、hash 和版本；
  - camera 使用稳定身份，后端与 VPU/CUDA 能力显式选择；
  - 禁止默认录制，磁盘/USB/算力预算有测试；
  - 缺少相机或加速器时安全退出，不影响飞控 transport。
- **依赖项:** 产品需求确认；workspace 隔离。
- **预计工作量:** M
- **是否阻塞 production:** 否，前提是保持 excluded 且技术上不可误启。

### BBF-INT-009

- **ID:** BBF-INT-009
- **级别:** P2
- **分类:** 运行时健壮性 / 诊断 / 资源边界
- **归属:** 根仓库 `vision_to_dds`
- **证据:**
  - `src/vision_to_dds/src/vision_to_dds.cpp:96-97`：`output_rate` 默认 20，未发现正数、上限或 finite 校验。
  - `src/vision_to_dds/src/vision_to_dds.cpp:55-70`：首个 TF 等待后建立 wall timer；异常处理主要是日志与 sleep。
  - `src/vision_to_dds/src/vision_to_dds.cpp:340-343`：`body_path_` 每帧追加 pose，未设置长度或时间上限。
  - `rg -n "diagnostic|health|bond|lifecycle|body_path.*erase|output_rate.*>" src/vision_to_dds`：未发现结构化健康输出、lifecycle gate、path 裁剪或参数约束。
  - 实际结果：非法速率可能导致 timer 配置异常；长时间运行 path 内存持续增长；上层无法机器判定视觉健康。
  - 预期结果：所有参数有边界；诊断资源有上限；健康状态可供控制权仲裁使用。
- **现象:** 节点缺少参数约束、资源上限和机器可读诊断。
- **影响:** 长时间运行产生内存增长；配置错误不能提前失败；控制节点可能无法区分“节点存活”和“视觉健康”。
- **触发条件:** 长航时运行、错误 `output_rate`、TF 间歇丢失或传感器反复重连。
- **建议修复:** 增加参数 descriptor/范围；对 path 采用固定窗口或默认关闭；发布结构化 health/age/reset/TF 状态；在不健康时撤销 DDS 发布资格。
- **验收标准:**
  - 非法速率/角度/frame 参数在启动时 fail-closed；
  - 24 小时等效压力测试中内存有界；
  - TF 缺失、陈旧、reset 和恢复均反映在诊断状态；
  - 控制权/graph guard 可消费该健康状态；
  - 诊断与日志不会暴露不必要的设备标识。
- **依赖项:** BBF-INT-002、BBF-INT-003；统一诊断规范。
- **预计工作量:** M
- **是否阻塞 production:** 否，但应在 production 验收前完成。

## 4. Production 阻塞项

| ID | 阻塞范围 | 解除条件摘要 |
|---|---|---|
| BBF-INT-001 | 所有外部视觉控制 | 完整 frame 契约、数值测试、实际 TF 匹配 |
| BBF-INT-002 | 所有外部视觉控制 | 时间同步、freshness、reset、finite 与故障注入 |
| BBF-INT-003 | 感知→DDS→EKF2 链路 | 受管 profile、只读 preflight、健康门 |
| BBF-INT-004 | 依赖 T265 的能力 | 稳定设备身份和缺失/掉线降级 |
| BBF-INT-005 | 精准降落能力 | 独立 firmware/profile、目标质量与丢失测试 |
| BBF-INT-006 | 整体 production | 旧 launch 技术隔离、串口单一所有权 |

在上述条件满足前，建议只允许静态检查、单元测试、SITL 和经过批准的 sensor-only/transport-read-only 验证；不得将 `vision_to_dds` 或旧 launch 用于实机控制。

## 5. 推荐实施顺序

1. 先完成 BBF-INT-006 的旧路径隔离和串口所有权，防止后续验证误启动冲突组件。
2. 并行定义 BBF-INT-001 frame 契约与 BBF-INT-002 时间/健康契约；两者均完成后才允许建立 DDS 外部视觉测试。
3. 建立 BBF-INT-003 受管 sensor-only/SITL profile，并加入只读 EKF2 preflight。
4. 在明确实际硬件清单后处理 BBF-INT-004；不能把历史 T265 缺失记录当作当前枚举结果。
5. 普通视觉里程计闭环通过后，再单独开展 BBF-INT-005 精准降落。
6. RPLIDAR、USB Camera/VPU 按明确产品需求恢复；当前保持不可误启。

## 6. 本代理实际执行的检查

本代理使用的命令类型均为只读静态检查：

```text
git status --short
git ls-files
find <受审目录> -type f
rg -n <模式> <源码/配置/文档>
nl -ba <源码/配置>
sed -n <范围> <文件>
python3 -c 'json.load(...)'   # 只解析历史参数 JSON，不访问硬件
```

未运行构建、测试、launch 或 ROS graph 命令；未访问网络；未读取 `/dev`；未启动任何节点；未修改源码、参数、固件或 Git 历史。

## 7. 未验证项目

- 当前 D435、T265、RPLIDAR、USB Camera、VPU 的连接状态、serial、VID:PID、USB topology 与带宽。
- 当前 `/dev` 映射、udev 规则生效状态、串口所有者和 TELEM2 实际连接。
- 当前 RealSense firmware/SDK 运行行为、TF tree、frame rate、时间戳和重连行为。
- 当前 PX4 EKF2、DDS、serial 参数；历史 JSON 只作为时间点证据。
- `vision_to_dds` 与 PX4 v1.16.2 的实时 QoS、topic、EKF 融合和 estimator status。
- 外部视觉的坐标符号、时间延迟、漂移、reset、掉线恢复与闭环稳定性。
- 精准降落的固件 publisher、SITL、拆桨台架和实机行为。
- RPLIDAR 型号、baud、扫描 frame、USB 带宽以及与 RealSense 并发运行。

## 8. 统计

| 等级 | 数量 |
|---|---:|
| P0 | 2 |
| P1 | 4 |
| P2 | 3 |
| P3 | 0 |
| 合计 | 9 |
