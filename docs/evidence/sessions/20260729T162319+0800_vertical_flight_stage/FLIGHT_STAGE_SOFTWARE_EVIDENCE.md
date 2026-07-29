# 普通垂直飞行阶段软件证据

Session：`20260729T162319+0800_vertical_flight_stage`  
日期：2026-07-29（Asia/Shanghai）  
范围：G0 源码/构建和 G1 Domain 231 隔离软件回放。无硬件访问、无刷写、无参数写入、
无 Domain 0 输入 writer、无 Arm/电机/装桨飞行。

## 源码身份

| 组件 | 权威构建 SHA | 构建前状态 |
|---|---|---|
| 根集成 | `292cdc1717ae57db2f68b695e1c8a66c6d66c16c` | clean，master ahead 1 |
| px4_msgs | `392e831c1f659429ca83902e66820d7094591410` | clean，detached |
| offboard_cpp | `e24bb3facfcf4126ad7b3d216a768a040758e895` | clean，DDS ahead 1 |
| vision_to_dds | `470cf59cf8fbcddd17b12e9d31f084e87f5f2fac` | clean，master ahead 1 |
| communication | `e6d6126acd16050216e5f091e61d58a96ef3ed65` | clean，main ahead 1 |

`workspace.lock.repos` 对四个生产仓均使用完整 40 字符 SHA。视觉唯一指向
`BoomBoomFly/vision_to_dds`；`serial_driver_ros` 保持 quarantine；`mission_bridge` 进入权威构建。

## 实际命令和结果

```bash
bash Scripts/build/build_dds_only.sh \
  --output-root /tmp/boomboomfly_vertical_stage_20260729T162319
```

脚本强制 `ROS_DOMAIN_ID=231`，先执行根集成门禁，再 clean build 四包、test 三包、读取 verbose
结果。实际结果：

```text
Summary: 4 packages finished [13min 35s]
Summary: 3 packages finished [5.04s]
Summary: 50 tests, 0 errors, 0 failures, 0 skipped
```

门禁同时验证：四包精确 SHA 且 clean、视觉默认关闭、三份生产 launch 节点清单、
`/mission/start` UInt32 和 UInt64 context 契约、控制/视觉 writer 清单、无生产 mock、
mission_bridge 无 PX4 writer、serial 隔离，以及 60 秒实机历史频率逻辑回放。

offboard 测试覆盖 1/2/1/50 Hz 抖动、setpoint/mode 50 Hz、1 Hz landed、完整 VERTICAL_TEST、
四类 ACK 拒绝/超时、RC/odom/timesync 断流、kill、重复 START、旧 session/seq/epoch 和单 writer。
vision 测试覆盖默认 0 writer、production 恰好 1 writer、外参/四元数/有限数/TF/时间/质量/epoch/
断流恢复和自定义参数不可覆盖生产契约。mission_bridge 覆盖 CRC、长度、session、START、heartbeat、
串口断开/重连和无 PX4 writer/伪造 RC。

## 回放器运行时缺陷与修复

首次 runtime 命令包装因 source Foxy 前启用 nounset 而退出；去掉 nounset 后进入节点并发现
`RcChannels.channels` 必须固定长度 18，而初版按配置长度赋值。没有删除测试或放宽断言：根提交
`01325b9` 增加固定数组填充和自检，随后结果为：

```text
ROS_DOMAIN_ID=231 ... px4_interface_replay.py --duration 2  -> exit 0
ROS_DOMAIN_ID=0   ... px4_interface_replay.py --duration 1  -> exit 2（预期拒绝）
```

根提交 `a82ca0a` 进一步禁止权威测试生成 pycache；三个生产子仓最终均 clean。

## 判定与限制

- G0：PASS（软件构建/契约证据）。
- G1：PASS（Domain 231 确定性回放/状态机证据）。
- G2：BLOCKED；目标固件未刷写，实机 `/fmu/out/rc_channels` 未验证。
- G3：BLOCKED；无实测 T265 外参和 PX4 estimator 接受证据。
- G4：BLOCKED；未执行拆桨失效矩阵。
- G5：PROHIBITED；本任务未获装桨、Arm 或飞行授权。

因此本 session 绝不构成“可以装桨飞行”的证据。

