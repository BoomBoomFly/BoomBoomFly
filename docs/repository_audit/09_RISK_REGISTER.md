# 风险登记册

## 汇总

| 严重度 | 已确认 | 高概率 | 待验证 | 合计 |
|---|---:|---:|---:|---:|
| P0 | 2 | 0 | 0 | 2 |
| P1 | 6 | 2 | 0 | 8 |
| P2 | 7 | 0 | 0 | 7 |
| P3 | 4 | 0 | 0 | 4 |
| 合计 | 19 | 2 | 0 | 21 |

“待现场验证事项”单独列在各硬件/视觉 finding 的“是否涉及硬件”与下一阶段计划，
不把缺乏现场证据的推断升级为已确认问题。

## 登记

| ID | 严重度 | 状态 | 领域 | 摘要 | 当前处置 | 阻塞门 |
|---|---|---|---|---|---|---|
| P0-CTRL-001 | P0 | 已确认 | PX4/Offboard | live writer 未接安全门，H0 exit 2 | 禁止启动 | 静态/构建提升/SITL/实机 |
| P0-CTRL-002 | P0 | 已确认 | PX4/Offboard | 默认 auto-arm + TEXT_RC + 无 fresh RC 可跳过检查 | 禁止启动 | 静态/SITL/实机 |
| P1-GIT-001 | P1 | 已确认 | Git/Build | Offboard/vision HEAD 与 exact lock 不一致 | Phase 0 冻结 | 构建/SITL/实机 |
| P1-GIT-002 | P1 | 已确认 | Git/Build/Sensor | optional repos 大规模 dirty | receipt 保护，不清理 | optional build/传感器 |
| P1-CTRL-003 | P1 | 高概率 | PX4/DDS | v1.16.2 默认 DDS 缺 RC safety topic | 定制 firmware/profile 待定 | SITL/实机 |
| P1-VISION-001 | P1 | 高概率 | Vision/PX4 | frame/time/quality/reset/health 契约不闭合 | writer 保持禁用 | 视觉/SITL/实机 |
| P1-CODE-001 | P1 | 已确认 | Code/Offboard | Odom 首帧读取未初始化状态 | 修复并 fault test | 静态/SITL/实机 |
| P1-SER-001 | P1 | 已确认 | Serial | ROS/STM32 协议不一致，odd len 越界 | quarantine PASS | 串口台架/集成 |
| P1-LAUNCH-001 | P1 | 已确认 | Launch/MAVLink | archive bringup 可手工组合硬件/MAVROS/控制 | forbidden | SITL/实机 |
| P1-CTRL-004 | P1 | 已确认 | DDS/Test | 无获准项目级 DDS/SITL orchestration | Phase 2 实现 | SITL/实机 |
| P2-BUILD-001 | P2 | 已确认 | Build | vision 缺 builtin_interfaces 直接依赖声明 | approved SHA 上修 | clean build |
| P2-CODE-002 | P2 | 已确认 | Code | node/FSM/input shared_ptr 环 | 生命周期重构 | 稳定性 |
| P2-VISION-002 | P2 | 已确认 | Vision/Code | callback sleep、path 无界、rate 未验证 | 纯软件修复 | 视觉长稳 |
| P2-HW-001 | P2 | 已确认 | Hardware/Config | `/dev/tty*` 默认和身份不稳定 | stable identity profile | 台架/实机 |
| P2-CI-001 | P2 | 已确认 | CI | workflow 仅手工触发且假设 bwrap | required gate 设计 | 合并/release |
| P2-REPRO-001 | P2 | 已确认 | Reproducibility | apt/rosdep/toolchain 无可重放锁 | 环境锁/SBOM | clean build/release |
| P2-DOC-001 | P2 | 已确认，已清理 | Docs/Git | 旧 handoff/报告链接可误用历史 GO | 旧文件已删除，入口已更新 | 已解除 |
| P3-REPO-001 | P3 | 已确认 | Git/Cleanup | 源码树内 build/log/cache | 仅候选 | 维护 |
| P3-BUILD-001 | P3 | 已确认 | Build | Offboard 冗余 rosidl/action 依赖 | 精简 | 维护 |
| P3-TEST-001 | P3 | 已确认 | Test | 无 sanitizer/coverage/static analyzer 门 | Phase 1 增加 | 质量 |
| P3-DOC-001 | P3 | 已确认 | Docs/Serial | communication README 路径过时 | 更新 | 维护 |

## 交叉验证结果

1. 文档 vs 代码：ADR 说 safety gate/production disabled；当前代码仍直接 publish，H0 实证 FAIL。
2. package vs include：`builtin_interfaces` 直接 include 但未声明。
3. launch vs node：Offboard 参数文件确实传入；危险 `enable_arm=true` 也因此真实生效。
4. PX4 topic vs messages：`vehicle_status_v1` 已匹配；`rc_channels` firmware export 未闭合。
5. DDS vs MAVLink：目标权威是 DDS-only；旧 MAVROS launch 仍在 archive，不得运行。
6. SITL vs 实机：无批准 SITL orchestration；旧 launch 使用真实设备默认，不能混用。
7. 根 vs nested：根 clean 不代表 nested clean或匹配 lock。
8. 文档路径：README 链接存在，但“current”语义绑定旧 SHA。
9. 清理候选引用：marker/历史 evidence 均保留；没有将被引用文件列为直接删除。
10. 无证据代理结论：未纳入确认问题；超时线程由主线程重新取证。

## 门禁映射

```text
静态审查门：NO-GO
  blockers: P0-CTRL-001, P0-CTRL-002, P1-GIT-001, P1-CODE-001

软件构建门：NOT RUN
  prerequisites not met; package boundary alone is PASS

SITL 门：NOT RUN
  blockers: static gate, exact source, RC topic/profile, orchestration

实机门：NOT AUTHORIZED
  blockers: all above plus hardware identity/bench approvals
```
