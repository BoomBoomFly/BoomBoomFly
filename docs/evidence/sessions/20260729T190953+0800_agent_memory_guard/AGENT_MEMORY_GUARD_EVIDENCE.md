# PX4 DDS Agent 内存/DMA 生产门禁证据

Session：`20260729T190953+0800_agent_memory_guard`

日期：2026-07-29（Asia/Shanghai）

范围：对已定位的 Jetson UART RX DMA 内存故障补充软件 fail-closed 门禁并复验 G0/G1。
本 session 未重启 Jetson、未启动真实 Agent、未发布 `/fmu/in/*`、未写 PX4 参数、未 Arm，
也未进入 G3–G5。

## 已实现门禁

根提交 `133cf05fd49deb55b072bd061b310aaf7f7310e7` 新增
`Scripts/runtime/px4_dds_agent_guard.py`。生产 Agent 仅在以下条件全部满足时才可 `exec`：

- 显式 `ROS_DOMAIN_ID=0`；
- Agent 使用绝对路径且二进制 SHA-256 与命令行精确值一致；
- `/dev/ttyTHS0` 是字符设备且无现有 owner；
- 唯一 guard lock 可取得；
- `MemAvailable >= 1024 MiB`；
- DMA zone `free-above-high >= 256 MiB`；
- 不存在 VS Code extension host、Pylance 或 cpptools。

任一输入缺失、非法或低于阈值均返回非零且不启动 Agent。`--check-only` 执行完全相同的
preflight，但不会 `exec` Agent。权威构建脚本同时显式设置 `MAKEFLAGS=-j1` 和
`CMAKE_BUILD_PARALLEL_LEVEL=1`，避免 ARM64 首次构建按 CPU 数制造并发内存峰值。

## 实际验证

以提交 `133cf05fd49deb55b072bd061b310aaf7f7310e7` 执行：

```bash
bash Scripts/build/build_dds_only.sh \
  --output-root /tmp/boomboomfly_guard_validation
```

最终权威结果为：

```text
Summary: 4 packages finished
Summary: 3 packages finished
Summary: 50 tests, 0 errors, 0 failures, 0 skipped
```

同一入口再次通过 60 秒历史频率逻辑回放、四包精确 SHA、视觉默认关闭、launch 清单、
`/mission/start` 类型、单 writer、无生产 mock 和 mission_bridge 边界检查。独立 guard 单测
共 7 项，覆盖内存/DMA 解析、缺失或低水位、开发进程、绝对路径/精确 SHA、低内存、非
Domain 0 和串口 owner，全部 PASS。

只读生产预检使用 Agent SHA-256
`1a64daa54225a41c8e0e1f333481b7d9c4341c20939b1dce44b43e7ea45580b3`，结果：

```text
status=PASS
MemAvailable=2526572 KiB
DMA free-above-high=1545908 KiB
serial_dev=/dev/ttyTHS0
baudrate=921600
```

该命令带 `--check-only`，没有启动 Agent。采集最终证据时 Pylance、cpptools 和 extension host
均不存在，四个生产子仓均 clean。根仓仅有用户原有未跟踪参数文件、固件备份和本 evidence
session；用户文件未修改、未提交。

首次 clean 构建四包成功后，我在仍运行的 Bash 脚本上修改脚本文本，导致运行中解释器后续
文件偏移错位并在测试入口前报 `rs: command not found`。这是执行时序错误，不是包构建或测试
失败。停止修改运行中脚本后，完整入口连续三次执行均 PASS。证据归档第一次引用了不存在的
`mission_bridge/test_results` 路径并 exit 2；随后按真实 `Testing`/`test_results` 路径重建归档。

## 准入结论

软件门禁和复验 **PASS**，但 G2 仍为 **FAIL/BLOCKED**。现有 120 秒低压力对照与本轮
`--check-only` 不能替代一次干净 Jetson 重启后的拆桨长稳态真实 DDS soak。该 soak 必须保持
生产门禁通过、唯一 Agent/串口 owner、关键 `/fmu/in/*` writer 为 0，并证明整个窗口内
RC/timesync 连续且内核无新增 page allocation 或 UART RX descriptor 错误。

本 session 不构成“可以装桨飞行”的证据。
