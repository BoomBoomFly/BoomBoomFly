# G4 Agent gap ULog 补证报告

Session：`20260729T234922+0800_g4_agent_gap_ulog`

日期：2026-07-29 至 2026-07-30（Asia/Shanghai）
结论：**Agent DDS 退出/恢复 PASS；gap 内 PX4 状态仍 BLOCKED；G4 未通过。**

## 授权与安全边界

本次操作在全部桨叶已拆除、机体固定、ESC 动力隔离的条件下进行。没有 Arm、没有发送
`VehicleCommand`、没有启动电机，也没有启动任何生产飞行节点或 `/fmu/in/*` writer。
唯一参数操作是用户批准的临时日志事务：

1. `SDLOG_MODE` 从 `0` 改为 `2`；
2. 冷启动确认持久化；
3. 执行 Agent 退出/恢复；
4. `SDLOG_MODE` 从 `2` 回滚为 `0`；
5. 冷启动并对全部 974 项参数做最终逐项复核。

`SDLOG_BOOT_BAT=0`、`SDLOG_PROFILE=1` 始终未变。任何异常都会触发 fail-closed 回滚。

## 参数事务与回滚

| 检查点 | 完整度 | `SDLOG_MODE` | SHA-256 |
|---|---:|---:|---|
| 写前 | 974/974 | 0 | `3754450ffd3f971e87a18f8828833d921312bac638c98ddcc7cce5df962c1e3c` |
| 启用写后 | 974/974 | 2 | `b703d969e6fd0bd6bedbdf319398de347c1e9cee38c38085921d8ffeb7191a2a` |
| 启用后冷启动 | 974/974 | 2 | `c96ceb028ed820605dfbbeefea24b6282910b094c3d06a859c8225b32490d7ed` |
| 回滚写后 | 974/974 | 0 | `1f548bbf87a476522cbec1d0b5e40e04a34c71e87130a860c1c1eb4d920b83eb` |
| 回滚后冷启动 | 974/974 | 0 | `b7f9b8e6a2dbbf1fb8930e98223bd7445ce4e723f639cebcc2dae8577c49a834` |
| 最终重试回读 | 974/974 | 0 | `cfce95638c1db887bd27fd0d240bb26af69578bc131d9fbc41ed81bf45681336` |

启用与回滚事务均为 PASS。每次写后全量 diff 只包含目标 `SDLOG_MODE` 和 PX4 派生
`_HASH_CHECK`。最终冷启动参数字典与写前字典逐项比较为零差异；参数已经完整恢复。

## Agent gap 实测

guard 使用 Agent SHA-256
`4cbc5038cb74391a8ecec3ed6cd94e588530cae937b5498d6796bf2c68433995`。
退出前直接 ROS 样本确认：

- `arming_state=1`、`nav_state=2`、`failsafe=false`；
- `landed=true`、`at_rest=true`；
- RC `signal_lost=false`，18 个通道；
- 27 个 `/fmu/in/*` topic 的 publisher 均为 0。

唯一 Agent 在 `2026-07-30T00:10:43.757078957+08:00` 退出；图检查连续 5 秒确认五个
PX4 输出 publisher 均为 0，且没有输入 writer。Agent 在
`2026-07-30T00:11:32.819922714+08:00` 恢复，wall-clock gap 约 49.063 秒。恢复后直接样本
再次确认上述飞行、落地和 RC 状态不变，五个输出各恢复为唯一 writer，27 个输入 writer
仍全部为 0。最终 Agent 已停止，串口和进程均释放。

该结果直接证明 DDS 数据面退出与恢复，但退出期间同一遥测链路不可见，不能据此推断 PX4
内部 mode、failsafe 或 Land 行为。

## ULog 结果与阻塞

MAVFTP 完整列出 19 个 ULog，但目录日期只包括 2026-03-23、2026-03-25、2026-04-06 和
旧式 `sess100` 至 `sess102`，没有 2026-07-29 或 2026-07-30 的当次日志。下载并校验了三个
旧日志：

| 远端日志 | 大小 | SHA-256 |
|---|---:|---|
| `sess100/log100.ulg` | 1,013,020 | `dfae3da52baa361d087442541c81445bf03582b320e40121036525ed9bebec04` |
| `sess101/log100.ulg` | 718,383 | `b39d9510a53d00f3e6fac89517179fc84472050916fbcf2480cf7d462427e263` |
| `sess102/log100.ulg` | 2,575,246 | `e41f00b99acf46df6e9792c8a32901428b33424a50e5bd43fb35c2c62bbc6566` |

三个文件的大小、SHA-256 和 ULog magic 均通过，`pyulog` 也可解析；但嵌入参数均为
`SDLOG_MODE=0`，无法与本次 Agent gap 建立时间或配置身份关联，因此不能作为当次证据。

USB MAVLink shell 只读诊断确认 SD 卡已挂载且空间充足，但 `logger status`、`param` 和
`ver` 在该 shell 中返回 `command not found`。与之相对，已刷固件对应的本地构建配置明确
启用 logger/param/ver，ELF 与 map 也包含并注册 `logger_main`、`param_main`、`ver_main`。
该运行态不一致尚未解释，必须在后续独立拆桨 session 中复核，不能用猜测补齐证据。

因此：

- Agent DDS 退出/恢复：**PASS**；
- 退出前与恢复后 PX4 状态：**直接观测 PASS**；
- gap 内 PX4 mode/failsafe/Land 状态：**BLOCKED / 无当次独立 ULog**；
- G4 总门：**BLOCKED**；
- G5：**PROHIBITED**。

## 软件验证

新增工具对参数基线 SHA、974 项完整度、精确写入方向、非预期 diff、Armed 状态、MAVLink
来源、ULog 大小与 magic 均 fail-closed。实际执行：

```text
python3 -m unittest discover -s test/runtime -p 'test_*.py' -v
Ran 35 tests in 0.096s
OK
```

完整输出见 `artifacts/final-runtime-tests.log`。本报告不是装桨、Arm 或飞行授权。
