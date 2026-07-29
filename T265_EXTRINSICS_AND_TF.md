# T265 外参与 TF 准入记录

审计时间：2026-07-29。当前状态：`H2 BLOCKED / EXTRINSICS UNMEASURED`。

本文件不猜测外参，不提供零平移或单位旋转默认值。本轮后续修改仅构建并在隔离的
`ROS_DOMAIN_ID=231` 运行 `vision_to_dds` 测试；没有启动 production launch、没有向实机
Domain 0 创建或发送视觉里程计，也不开发 D435 精确降落。外参完成并通过五动作验证前，
不允许写入生产配置或装桨起飞。

## 当前证据

2026-07-29T08:42:55+08:00、`ROS_DOMAIN_ID=0` 的只读检查中，没有 RealSense、
`vision_to_dds` 或 TF broadcaster 进程；`ros2 node list` 为空，仅有
`/parameter_events` 与 `/rosout`。因此本轮不能重新实测 T265。

2026-07-28 历史实机记录见
`docs/evidence/sessions/20260728T174752+0800_onboard_validation/ONBOARD_VALIDATION.md`：

| 项目 | 历史实测 | 证据限制 |
|---|---|---|
| T265 topic | `/t265/pose/sample`，约 199.54 Hz | 未保留逐帧原始 T265 artifact，不能在本轮重算 |
| 动态 TF | `odom_frame -> t265_pose_frame`，约 199.55 Hz | 当前无 live TF |
| 时间戳 | odom/TF 严格递增；中位延迟约 6.3/6.6 ms | 只代表该次约束内采样 |
| 双相机运行 | T265 约 174.75 Hz | D435 不进入本定位链 |
| 设备重连 | 两轮释放、重新枚举成功 | 不等于定位链可安全跨重连恢复 |
| 外参 | 未知 | 直接阻断 H2 |

真实遮挡、冻结、USB 断开/重连后的 quality/source epoch 尚无闭环证据。静止不等于冻结；
冻结必须由时间戳停止前进来判定。

## 坐标轴与 wrapper 变换

锁定的 RealSense ROS wrapper 在
`src/realsense-ros/realsense2_camera/src/base_realsense_node.cpp` 中执行：

```text
ROS x = -T265_raw_z
ROS y = -T265_raw_x
ROS z =  T265_raw_y
```

并发布 `odom_frame -> <camera_name>_pose_frame`；`camera_name=t265` 时即历史实测的
`odom_frame -> t265_pose_frame`。

| 坐标系 | +X | +Y | +Z | 依据/备注 |
|---|---|---|---|---|
| T265 原始 API | 朝右侧成像器 | 朝设备顶部 | 向设备背面/机身内部 | `src/librealsense/doc/t265.md`；tracking origin 为两鱼眼成像器在 PCB 上的中心 |
| ROS `t265_pose_frame` | 从镜头面向外 | 朝左侧成像器 | 朝设备顶部 | 由上面的 wrapper 映射得到 |
| ROS `base_link` | 机头/前 | 机体左 | 机体上 | REP-103 FLU；现场必须在机体上贴轴标 |
| PX4 body FRD | 前 | 右 | 下 | 只作后续 PX4 消息/杆臂换算对照 |

这些定义不能推导本机安装姿态。相机支架朝向、机体原点和 CoG 仍必须实测。

## 最终 TF 契约

```text
odom_frame
  └── dynamic ──> t265_pose_frame
                     └── measured static ──> base_link
```

最终语义参数：

```yaml
world_frame_id: odom_frame
body_frame_id: base_link
```

静态边需要的是 `^t265_pose T_base_link`：平移是 base 原点在 T265 ROS pose frame 中
的位置，旋转把 `base_link` 坐标向量表达为 `t265_pose_frame` 坐标。若现场测到的是更
常见的 `^base T_t265`，必须先取逆，不能把同一组数直接抄到反向 TF。

## 外参测量表

RPY 约定冻结为 `R = Rz(yaw) * Ry(pitch) * Rx(roll)`。生产记录同时保存 RPY 和归一化
四元数，但 broadcaster 只选一种表达；需检查 `RᵀR=I`、`det(R)=+1`、`||q||=1`。

| 字段 | 精确定义 | 单位 | 实测值 | 不确定度/工具 |
|---|---|---:|---|---|
| `x` | base 原点沿 T265 ROS +X 的位置 | m | `UNMEASURED` | `TBD` |
| `y` | base 原点沿 T265 ROS +Y 的位置 | m | `UNMEASURED` | `TBD` |
| `z` | base 原点沿 T265 ROS +Z 的位置 | m | `UNMEASURED` | `TBD` |
| roll | `base_link` 相对 T265 绕 +X | rad/deg | `UNMEASURED` | `TBD` |
| pitch | `base_link` 相对 T265 绕 +Y | rad/deg | `UNMEASURED` | `TBD` |
| yaw | `base_link` 相对 T265 绕 +Z | rad/deg | `UNMEASURED` | `TBD` |
| `qx,qy,qz,qw` | `^t265_pose q_base_link` | — | `UNMEASURED` | `TBD` |
| base 原点 | 机体采用的明确基准点 | — | `UNDEFINED` | 标记/照片 |
| CoG | 带实机电池时的重心 | — | `UNMEASURED` | 平衡夹具 |
| tracking origin | 两鱼眼成像器 PCB 中心 | — | `DEFINED, NOT LOCATED ON AIRFRAME` | 标尺/CMM |
| 安装状态 | 支架版次、孔位、紧固、照片 | — | `UNRECORDED` | `TBD` |

测量顺序：先标记 base 原点和三轴；从 tracking origin 到 base 原点测三轴平移；用安装面、
机体轴线、水平仪/角度仪测旋转；再以三个非共线受控平移交叉验证。不得把相机外壳中心、
Pixhawk 外壳中心或估计 CoG 擅自当成同一点。

`EKF2_EV_POS_X/Y/Z` 是 T265 跟踪原点相对飞行器 CoG 的 PX4 FRD 杆臂，不是上述 ROS
TF 数值的直接复制。应从同一测量记录另行做方向和原点换算。

## 五动作符号验证

全部拆桨，保持 `/fmu/in/*` 无 writer。加载临时静态 TF 后只做被动查看：

```bash
ros2 run tf2_ros tf2_echo odom_frame base_link
ros2 topic hz /t265/pose/sample
ros2 topic hz /tf
```

位移应投影到动作开始时的 `base_link`，不能假定 `odom_frame +X` 永远等于机头。

| 动作 | `odom_frame -> base_link` 预期 | 记录值/结果 |
|---|---|---|
| 静止 | stamp 持续严格递增；无重复/回退/长时间停止；漂移和噪声记录为实测值，不要求绝对零 | `NOT RUN` |
| 前移 | 初始 body 投影 `Δx > 0`，交叉轴显著小于主轴 | `NOT RUN` |
| 右移 | ROS FLU 初始 body 投影 `Δy < 0` | `NOT RUN` |
| 抬高 | ROS FLU 初始 body 投影 `Δz > 0` | `NOT RUN` |
| 从上向下看顺时针偏航 | ROS +Z 右手系下 `Δyaw < 0`；避开 ±π wrap | `NOT RUN` |

每次动作至少记录起止 pose、主轴量级、交叉轴、四元数范数、最大帧间隔、重复/回退计数。
任一符号错误、比例异常或 TF 多 parent/闭环即失败。

## 冻结和重连验收

1. 正常静止和运动各记录实际频率、最大帧间隔、stamp 单调性。
2. 分别做纹理遮挡、USB 断开、重新接入；记录最后一帧、TF 消失时间、恢复首帧、stamp
   是否回退和设备枚举时间。
3. 冻结期间视觉 writer 必须停止，不能重发最后 pose。
4. 每次重连必须产生新的 source epoch；重新稳定和人工重新授权前不得恢复 writer。
5. 快速运动/跟踪降级时 quality 必须下降并阻断不合格输入。

历史证据只证明设备可重新枚举，没有证明第 3–5 项。当前 checkout 也没有相应生产实现，
所以本节仍是 `BLOCKED/NOT RUN`。

## 静态 TF 命令与 launch 草案

本机 ROS 2 Foxy 已确认四元数语法为：

```text
x y z qx qy qz qw parent child
```

仅在测量完成后的临时命令模板（占位符故意不可直接执行）：

```bash
ros2 run tf2_ros static_transform_publisher \
  MEASURED_X_M MEASURED_Y_M MEASURED_Z_M \
  MEASURED_QX MEASURED_QY MEASURED_QZ MEASURED_QW \
  t265_pose_frame base_link
```

launch 草案，同样故意没有默认外参：

```python
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    names = ('x_m', 'y_m', 'z_m', 'qx', 'qy', 'qz', 'qw')
    return LaunchDescription(
        [DeclareLaunchArgument(name) for name in names] +
        [Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='t265_pose_to_base_link',
            arguments=[
                LaunchConfiguration('x_m'),
                LaunchConfiguration('y_m'),
                LaunchConfiguration('z_m'),
                LaunchConfiguration('qx'),
                LaunchConfiguration('qy'),
                LaunchConfiguration('qz'),
                LaunchConfiguration('qw'),
                't265_pose_frame',
                'base_link',
            ],
        )]
    )
```

上线前确认 `base_link` 没有其他 parent/broadcaster，避免重复 TF 或闭环。外参未测量前
禁止把草案写入生产 launch/config。

## `vision_to_dds` 静态审计

- 实际组件位于 `BoomBoomFly/src/vision_to_dds`，修改前干净 HEAD 为 `72bd682`（当时
  `origin/master`）。用户声明基线 `42a0688` 仍不在本地对象库；当前修改建立在
  `72bd682` 上，来源差异仍须纳入 receipt。
- 当前源码已有默认 false 的 `enable_vision_dds`。false 时不创建
  `/fmu/in/vehicle_visual_odometry` publisher，也不创建 TF listener；H0 图级单测通过。
- 接口已是 `world_frame_id=odom_frame`、`body_frame_id=base_link`。production launch
  强制这两个 frame、标准 PX4 topic 和显式 `production:=true enable_vision_dds:=true`，
  custom YAML 不能静默重定向这些值。
- production launch 只接受绝对路径的实测外参文件，并校验 parent/child、有限数、数值占位符
  和单位四元数；仓库仍只含不可执行模板，没有写入任何真实或猜测外参。
- production launch 现在启动 `t265_health_adapter_node`，默认订阅本机已观测的
  `/t265/pose/sample`。quality 来自 RealSense wrapper 的 covariance-encoded
  `tracker_confidence`，不是固定值；冻结、timeout、stamp 回退会降为无效并推进 source epoch。
- bridge 对 source epoch、quality、frame、stamp age/future/rollback/jump、输入冻结和重复 writer
  fail-closed；fault 需要人工 reset 和两个新 TF 样本 warm-up，不会自动恢复为 ACTIVE。
- `VisionContract` 已显式完成 ENU/FLU 到 NED/FRD 的位置、姿态、速度和方差转换；坐标符号、
  非单位四元数、NaN、stamp 回退等均有单测。
- 构建 `px4_msgs` 与 `vision_to_dds` 成功；隔离 Domain 231 的包测试结果为
  `29 tests, 0 errors, 0 failures, 0 skipped`。测试没有连接实机 Domain 0。

这些修改关闭了旧版的接口、默认 writer 和软件重连语义缺口，但不能替代真实外参、五动作、
live TF 及拔插恢复验证，也没有证明 PX4 EKF 已接受视觉。

## 本轮软件变更 receipt

| 字段 | 记录 |
|---|---|
| 用户授权 | 2026-07-29 当前任务“进行修改” |
| 记录时间 | `2026-07-29T10:11:35+08:00` |
| 组件路径 | `/home/c/px4_ws/BoomBoomFly/src/vision_to_dds` |
| 修改前 Git SHA | `72bd68251f209b6ce6e82ebe8a2e089dad927fd1`，修改前 clean |
| 最终 source diff SHA-256 | `1b563f82e357d260a969a0c120dd923eadd60fd03edd77dae0a3bb4a03b33dff` |
| 原始 PX4 参数 | 未写参；沿用审计快照 SHA-256 `f669480ed8fd3f8066a6ab3132667a4be5a13dce956f7f23139efeff409222ce` |
| 飞控/固件 | 未连接、未刷写；最后已知 PX4 v1.16.2 / Pixhawk 2.4.8 / `PX4_FMU_V3` |
| 构建 | `colcon build --base-paths src --packages-up-to vision_to_dds`，随后 package-only rebuild；成功 |
| 最终测试 | `ROS_DOMAIN_ID=143 colcon test --packages-select vision_to_dds`；`29 tests, 0 errors, 0 failures, 0 skipped` |
| 实机动作 | 无 Agent、无 production launch、无 Domain 0 `/fmu/in/*`、无 Arm/电机动作 |

源码回滚时先保存并复核当前 diff，以审核过的 patch 执行 `git apply --reverse`；新增的
`test/test_production_launch.py` 先移动到带时间戳的 `/tmp` 归档，再 package-only rebuild/test。
禁止用 reset/checkout 覆盖工作区。PX4 参数和固件本轮未变，因此没有飞控侧回滚动作。

## H2 判定

| 项目 | 状态 |
|---|---|
| 历史 T265 topic/TF 频率与 stamp | `PASS（历史证据）` |
| 当前 live T265/TF | `BLOCKED` |
| T265 原始轴到 wrapper ROS 轴 | `PASS（源码确认）` |
| `odom_frame -> t265_pose_frame` | `PASS（历史证据）` |
| `t265_pose_frame -> base_link` 真值 | `BLOCKED / UNMEASURED` |
| 五动作符号 | `BLOCKED / NOT RUN` |
| 冻结/重连软件契约 | `PASS（单测）`；live 拔插仍 `BLOCKED` |
| 最终 frame 参数接口 | `PASS（静态/单测）` |
| ROS→PX4 坐标转换 | `PASS（单测）`；五动作仍 `BLOCKED` |

真实 `odom_frame -> base_link` 目前未知；H2 不通过，不允许装桨起飞。
