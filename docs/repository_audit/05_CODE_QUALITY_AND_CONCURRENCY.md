# C++、Python 与并发安全

## [P1-CODE-001] Offboard Odom 首帧状态在使用前未可靠初始化

- 严重度：P1
- 状态：已确认
- 领域：Code / Offboard
- 位置：
  - `src/offboard_cpp/include/lib/input.hpp:79-97`
  - `src/offboard_cpp/src/lib/input.cpp:218-253`
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:50-89,346-355`
- 证据：
  - `Odom_Data_t::p` 与 `pos_jump` 没有声明时初始化。
  - 构造器初始化 `rcv_stamp/q/recv_new_msg`，没有初始化 `p/v/w/pos_jump`。
  - `feed()` 先把 `rcv_stamp=node_->now()`，再用
    `rcv_stamp.nanoseconds()==0` 判断首帧；正常时钟下首帧分支不会成立。
  - 首帧 `(new_p-p).norm()` 读取未初始化的 `p`。
  - `odom_is_received()` 在 FSM 中直接读取 `pos_jump`。
- 影响：
  - 启动时定位可用性和位置跳变判断未定义，可能错误降级、错误切 mode 或使用错误初值。
- 根因：
  - 首帧标志错误地由更新后的时间戳推导，缺少显式 `has_received`。
- 建议：
  - 所有 Eigen/标志/时间显式初始化；增加 `has_received=false`。
  - 首帧先建立 baseline，不进行差分；后续检查 finite/frame/epoch/dt/jump。
- 前置条件：
  - 在 approved Offboard candidate 上修改并增加 first-frame/stale/reset tests。
- 是否涉及硬件：
  - 否

## [P2-CODE-002] Node、FSM 与输入对象形成 shared_ptr 所有权环

- 严重度：P2
- 状态：已确认
- 领域：Code / Concurrency
- 位置：
  - `src/offboard_cpp/src/node.cpp:7-20`
  - `src/offboard_cpp/include/lib/CtrlFSM.hpp:18-26`
  - `src/offboard_cpp/src/lib/CtrlFSM.cpp:33-42`
  - `src/offboard_cpp/include/lib/input.hpp:31-175`
- 证据：
  - node 拥有 `unique_ptr<CtrlFSM>`。
  - FSM 持有 `rclcpp::Node::SharedPtr`；每个输入对象也各持有 node shared_ptr。
  - parameter callback 存在于 node，lambda 又捕获 `self` shared_ptr。
- 影响：
  - shutdown 时对象可能无法析构，publisher/parameter callback 和资源生命周期不清晰。
  - 若以后改为 MultiThreadedExecutor，这组裸共享状态还没有 callback group/mutex 契约。
- 根因：
  - 将“访问 node API”建模成所有权，而不是非拥有引用/接口。
- 建议：
  - FSM/input 使用 `weak_ptr`、非拥有引用或窄接口；parameter callback 捕获 weak_ptr。
  - 明确单线程 executor 假设，或为共享状态建立 callback group/锁。
- 前置条件：
  - 生命周期测试：spin→shutdown→析构计数/FD/publisher 清理。
- 是否涉及硬件：
  - 否

## [P2-VISION-002] vision callback 可阻塞 executor 且路径内存无界增长

- 严重度：P2
- 状态：已确认
- 领域：Code / Sensor / Concurrency
- 位置：
  - `src/vision_to_dds/src/vision_to_dds.cpp:65-67`
  - `src/vision_to_dds/src/vision_to_dds.cpp:96-109`
  - `src/vision_to_dds/src/vision_to_dds.cpp:340-350`
- 证据：
  - `output_rate` 未验证正数/上限，直接用于 `1000.0/output_rate_`。
  - 每个新 TF 都 `body_path_.poses.push_back()`，没有窗口上限。
  - TF 异常时在 timer callback 内 `sleep_for(1s)`。
- 影响：
  - 错误参数可产生零/负周期；长时间运行内存持续增长；TF 故障阻塞同 executor 回调。
- 根因：
  - 调试可视化与实时 bridge 共用进程和热路径。
- 建议：
  - 校验 rate 范围；使用 bounded deque/可关闭 path。
  - 异常只节流日志并返回，恢复交由非阻塞状态机。
- 前置条件：
  - 纯软件 fault test：0/负/极高 rate、TF 中断、长时内存。
- 是否涉及硬件：
  - 否

## 其他具体观察

- `Takeoff_Land_Data_t::landed` 在 `input.hpp:166` 未初始化；应初始化为保守值并用
  `has_received` 区分未知，不能把未知等同 landed。
- 当前默认使用 `rclcpp::spin(node)` 单线程 executor，现有 callback/FSM 没有立即
  多线程数据竞争证据；若换 MultiThreadedExecutor 则共享 `fsm` 全部状态需要同步。
- serial write 在 `/cmd_vel` callback 内同步执行，timeout 为 1000 ms；虽然包被隔离，
  启用后会阻塞 executor，且没有 reconnect/backoff。
- Python 权威工具使用 argument list 调 subprocess，未发现生产路径拼接
  `shell=True` 的已确认注入点。
- `TODO` 主要集中在 package 元数据与历史/上游代码；不能仅凭 TODO 判定运行缺陷。
