# uav_mission

更新日期：2026-10-15。当前修订未重新构建或运行，历史结果不覆盖当前源码。任务与控制是独立 ROS 2 节点，通过 `uav_interfaces`
的目标、状态和命令接口通信。任务可使用 MAVROS 或 DDS 后端，不持有跨包控制对象，
不直接处理 PX4 消息、原始 VIO 测量、相机或飞控内部控制器。可选健康门控与新增状态字段见 [共享契约](https://github.com/BoomBoomFly/uav_ws/blob/main/docs/%E5%BD%93%E5%89%8Dsrc%E9%9D%99%E6%80%81%E5%AE%A1%E6%9F%A5.md)。

## 实际实现

`mission_node.cpp` 接收统一状态，以 20 Hz 驱动 `FlightTask`，为目标附加当前 ROS 时间戳，
调用飞行命令 Service，并提供取消入口。`flight_task.cpp` 负责阶段、超时、误差和结果。
节点启动后自动等待就绪并推进任务；当前没有独立的启动 Service、任务 Action 或集群任务入口。
任务阶段及命令结果通过诊断话题和日志报告，接口见 [共享契约](https://github.com/BoomBoomFly/uav_ws/blob/main/docs/%E5%BD%93%E5%89%8Dsrc%E9%9D%99%E6%80%81%E5%AE%A1%E6%9F%A5.md)，完成后节点退出。

```text
WAIT_READY → PREPARE_OFFBOARD → REQUEST_OFFBOARD → REQUEST_ARM
  → TAKEOFF → STABILIZE → HOVER → REQUEST_LAND → LANDING
  → 地面仍解锁时 REQUEST_DISARM → FINISHED

故障／空中取消 → SAFETY_LAND → 命令处理及新鲜地面/未解锁确认 → FINISHED
人工接管 → 停止自动目标和命令 → FINISHED（未确认安全降落）
```

开始前要求新鲜连接、有效定位、新鲜地面／未解锁状态以及控制后端未锁止。
准备阶段连续发布当前位置目标，按任务 prestream_s 等待，默认 1.2 s；该值需大于控制后端的预发送要求。
命令派发、最终接受、实际 OFFBOARD／armed／AUTO.LAND 状态分别确认。
起飞高度相对就绪时的本地位置，不使用绝对 z=1 作为起飞目标。

当前阶段只由 `FlightTask::Stage` 定义；未使用的旧阶段枚举文件已删除。没有后端工厂、插件或 MissionExecutor。
需要航点、搜索、视觉降落或多任务编排时再按实际需求扩展。

## 接口与失败处理

| 接口 | 当前行为 |
| --- | --- |
| `/uav_control/target`，PoseStamped | 发布本地 map／ENU 位置与 yaw，控制节点维护飞控发送循环 |
| `/uav_control/state`，VehicleState | 读取状态／定位／落地有效性、命令结果及控制锁止 |
| `/uav_control/command`，FlightCommand | 递增非零 command_id；请求 SET_OFFBOARD、ARM、LAND、DISARM |
| `/uav_mission/cancel`，Trigger | 接受取消；若可能已解锁，转入安全降落并等待地面／未解锁确认 |

`dispatched=true` 不代表 PX4 接受，更不代表实际状态已经改变。
`control_inhibited`／`control_message` 使任务识别只读或故障锁止，
防止定位／通信恢复后继续旧任务。降落交接阶段仍能确认 AUTO.LAND、落地和未解锁，
不会仅因停止 Offboard 心跳而报错。MAVROS 后端也发布实际锁止状态及原因。

启用 `require_vio_health` 时，任务订阅 `/uav_bridge/diagnostics` 的
`uav_bridge/odom_bridge` v1 状态；只有桥接已启用、未暂停且真实视觉更新和输入都新鲜时才继续。
桥接的 `published` 计数只表示本地 publisher 调用，不能证明 PX4 收到或 EKF2 融合。
任务运行中 VIO 健康失效会进入既有失败／安全降落路径；桥接恢复供数不会恢复旧任务，
需完成地面复位后显式启动新任务。

空中失败或取消时，仍拥有 OFFBOARD 控制且定位/状态有效才请求 LAND。后端已经锁止时，任务只观察兜底降落，避免重复 LAND。
ARM 尚未解决时取消会保留命令关联；地面需要后续 DISARM 接受与实际未解锁确认，不用旧地面状态提前完成。
安全 LAND 最终拒绝/超时后停止任务侧 LAND 重试和目标流；地面 DISARM 与此前 LAND 失败分别处理，限制见 [共享审查](https://github.com/BoomBoomFly/uav_ws/blob/main/docs/%E5%BD%93%E5%89%8Dsrc%E9%9D%99%E6%80%81%E5%AE%A1%E6%9F%A5.md)。
已解锁时启动任务直接失败；人工切到非 OFFBOARD/AUTO.LAND 模式后停止自动控制。
链路／定位无效时，不把旧观测当成落地结果，安全阶段可能持续等待。
控制节点停止后的实际 Offboard-loss 行为取决于 PX4 配置，任务超时与心跳丢失需分开验证。
地面重新就绪由 DDS `/uav_control/reset` 完成，之后显式启动新任务。
任务节点不自动调用 reset，也不自动重新开始旧任务。

取消命令需要先加载与任务相同的 overlay：

```bash
ros2 service call /uav_mission/cancel std_srvs/srv/Trigger '{}'
```

取消 Service 成功只证明取消请求被接受；完成需核对最终日志与飞控状态。

## 参数与启动

实际参数位于集中配置 [`uav_bringup/config/uav.yaml`](https://github.com/BoomBoomFly/uav_bringup/blob/main/config/uav.yaml) 的 `uav_mission` 分区：

| 参数 | 默认值 |
| --- | --- |
| takeoff_height_m | 1.0 m |
| horizontal_tolerance_m / vertical_tolerance_m | 0.2 / 0.15 m |
| stable_duration_s / hover_duration_s | 2.0 / 10.0 s |
| prestream_s | 1.2 s；大于控制后端预发送要求 |
| ready_timeout_s / command_timeout_s | 集中配置 30.0 / 5.0 s；command_timeout_s 代码默认 7.0 s |
| takeoff_timeout_s / landing_timeout_s | 30.0 / 45.0 s |
| state_timeout_s | 1.0 s |
| require_vio_health / vio_health_timeout_s | 代码默认 false / 2.0 s，集中配置未覆盖 |

yaw 误差会记录，但当前不是悬停通过阈值。表中区分集中配置与代码回退值，实飞条件另行冻结。
接口路径为 `src/uav_interfaces`，全部消费者需同步重建新增的状态字段。

当前统一入口读取集中配置。DDS/MAVROS 后端和只读状态分别由 `uav_control.backend` 与所选后端分区决定；
`start_mission:=true` 只启动任务节点，不会关闭只读保护。自动任务在配置为允许控制并完成飞控、定位验证后才可启动：

```bash
# 从工作区根目录执行，先加载经过核对的 overlay
ros2 launch uav_bringup uav.launch.py config_file:=/absolute/path/to/uav.yaml start_mission:=true
```

该入口不启动 PX4、Agent 或 Gazebo。同一次试验只运行一个控制后端和一个目标来源。
`uav_mission` 没有独立任务 launch；运行 `mission_node` 会自动推进任务，不能用于只读检查。

## 验证边界

当前 CMake 未注册任务测试；旧 flight_task 回归及历史 SITL 不覆盖当前修订。接口变更需与全部消费者一起重建。
待验收项与历史证据集中见 [当前源码与验证边界](https://github.com/BoomBoomFly/uav_ws/blob/main/docs/%E5%BD%93%E5%89%8Dsrc%E9%9D%99%E6%80%81%E5%AE%A1%E6%9F%A5.md)，
运行与故障顺序见 [DDS 开发流程](https://github.com/BoomBoomFly/uav_ws/blob/main/docs/DDS%E5%BC%80%E5%8F%91%E6%B5%81%E7%A8%8B.md)。
