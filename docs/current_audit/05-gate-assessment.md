# 门禁评估

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

## 本轮 gate schema

本报告使用用户本轮定义的 H0=静态审查、H1=纯软件构建。Wave 3B
`26_PROP_OFF_BENCH_READINESS.md` 曾将 H0/H1 用于硬件身份/firmware confirmation；
这些同名旧结论对本轮 gate 为 `NOT_APPLICABLE`，不能直接复制。

## 结论

```text
H0 静态审查：NO-GO
H1 纯软件构建：NOT-RUN
H2 单元测试：NO-GO
H3 无硬件节点级测试：NOT-RUN
H4 SITL：NOT-RUN
H5 台架硬件：NOT-RUN
H6 拆桨实机：NOT-RUN
H7 受控飞行：NOT-RUN
```

## H0 静态审查：NO-GO

精确阻塞项：

1. BBF-AUD-001..009 的原验收标准均未达到：live node 未接 runtime gate，
   ACK/owner/lease/PRESTREAM/freshness/fault/RC/vision 闭环仍开。
2. P0 `BBF-CUR-003`：未跟踪 serial 节点提供 `/cmd_vel`→串口硬件写路径，
   无 authority/watchdog/interlock。
3. 根工作树包含删除的关键 gitlink 和来源/路径不一致的未跟踪
   `src/communication`；不满足“所有仓库身份和关键来源明确”。
4. package boundary 当前可复现 exit 2；serial canonical source/path 未决。
5. Offboard Wave 3B final 未进入 root exact lock。
6. PX4 source/tag/submodules/message equality已从“缺失”改善为可验证，但 checkout
   未受治理；board/toolchain/profile lock、ARM compiler 和 `rc_channels` endpoint
   仍不闭合。
7. dangerous production defaults 仍包括 `TEXT_RC` 和 auto-arm=true。
8. 视觉 production package 仍缺 frame/time/reset/quality/device health gate。

因此不能使用 `CONDITIONAL`：当前有多个未隔离 live P0 和关键来源不明问题。

## H1 纯软件构建：NOT-RUN

本轮没有执行目标三包的 `colcon build`，没有当前 source tree 对应的完整 build log、
install artifact 或 test result。唯一 build 前置复核为：

```text
package boundary: exit 2
error: package serial_driver path mismatch:
expected src/serial_driver_ros,
found src/communication/Serial/serial_driver_ros
```

即使历史 standalone C++ compile 或旧 Wave 3B build 通过，也不能提升当前 H1。
并且 H0 为 NO-GO，本轮规则不允许进入 H1。

## H2 单元测试：NO-GO（仅部分执行）

当前安全执行并通过：

- root Python unittest：152/152；
- nested Offboard Python contract：12/12；
- transport-neutral Offboard runtime C++ standalone compile/test：PASS。

未执行/未覆盖：

- ROS/ament 当前构建产物上的全部 gtest；
- live CtrlFSM/ROS transport/publisher 行为；
- serial parser/CRC/reconnect/watchdog（当前 serial 包无对应闭包）；
- vision frame/time/reset/dropout 的完整 unit/fault suite；
- package target 的完整 current unit suite。

故障覆盖中的 ACK/owner/restart/clock 多数仅为 offline/synthetic oracle；不能替代
live behavior。由于已执行的是“部分测试”而非零测试，H2 判 `NO-GO`，而不是 GO
或把局部 PASS 误称完整执行。

## H3–H7

| Gate | 结果 | 原因 |
|---|---|---|
| H3 无硬件节点级 | NOT-RUN | H0 NO-GO、H1 NOT-RUN；未启动 ROS node/graph |
| H4 formal SITL | NOT-RUN | 未执行 PX4/Agent/SITL；catalog/timeline 仅 synthetic |
| H5 台架硬件 | NOT-RUN | 未授权且软件门未通过 |
| H6 拆桨实机 | NOT-RUN | 未授权 |
| H7 受控飞行 | NOT-RUN | 未授权 |

## 进入条件

- 可以继续：隔离、无 ROS graph/设备的纯函数、parser、FSM、clock/transport 单元与
  fault-injection 测试。
- 不可进入无硬件节点级：须先关闭 live P0、通过 H0，并建立当前 H1 build。
- 不可进入 formal SITL：须再纳管 PX4 source/toolchain/profile、补 `rc_channels`
  决策、完成 live wiring 与完整 H2。
- 不可进入任何硬件阶段：formal SITL 与相应 promotion checklist 未通过，且本轮
  没有硬件授权。
