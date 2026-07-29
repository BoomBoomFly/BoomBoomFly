# G4-0 USB 恢复、当前参数与 ULog 审计

Session：`20260729T221803+0800_g4_0_usb_recovery`
日期：2026-07-29（Asia/Shanghai）
结论：**当前完整参数导出 PASS、ULog 目录枚举 PASS；G4 仍 BLOCKED，整体 NO-GO。**

## 安全边界

全部桨叶拆除、机体固定、ESC 动力隔离。全程没有 Arm、参数写入、VehicleCommand、offboard、
vision、mission bridge 或电机动作。所有 MAVLink 输出仅为 `PARAM_REQUEST_LIST`、缺项
`PARAM_REQUEST_READ`、`LOG_REQUEST_LIST` 和日志头 `LOG_REQUEST_DATA` 只读请求。

## USB 恢复与解码器修复

Pixhawk 在 22:17 重新枚举为 `/dev/ttyACM0`、USB `26ac:0011 PX4_FMU_v2.x`，串口无 owner。
第一次参数流在 `BAT1_I_CHANNEL` 处被旧脚本误判为非有限值。根因不是参数损坏，而是 PX4 legacy
MAVLink 使用 bytewise 参数编码：INT32 `-1` 的 32 位位型为 `0xffffffff`，如果直接数值转换会
表现为 NaN。

新增 `Scripts/runtime/px4_param_snapshot.py`：

- 按 `MAV_PARAM_TYPE` 从四字节位型恢复 UINT8/INT8/UINT16/INT16/UINT32/INT32；
- REAL32 仍要求 finite；未知类型和 legacy 协议无法表示的 64 位类型 fail-closed；
- 显式使用 system 1/component 1；
- 支持按缺失 index 发只读 `PARAM_REQUEST_READ`；
- 同时校验名称数、index 数和声明的 expected count。

5 项新解码测试与 7 项既有 Agent guard 测试合计 12/12 PASS。

USB 数据面只在物理重枚举后的即时窗口稳定响应；普通打开端口时 heartbeat、参数和日志请求会
再次静默。一次软件 `usbreset` 尝试因 sudo 需要密码而在执行 reset 前退出，没有绕过权限。

## 当前完整参数

第二次受监控物理重插后导出结果：

```text
complete=true
expected_count=974
received_count=974
received_index_count=974
encoding=px4_mavlink_bytewise
SHA-256=7ff75ac24b0f91d5dcd931ad39c18eda8db068ba22316f71c227cd693e3e99fb
```

与 `docs/2026.7.29.params`（SHA-256
`2c3b9c6ea6efa4e5fdbb25fa0edc3cd0261f883408b7ae10729ca8c52e1105b0`）比较：

- 当前新增 `_HASH_CHECK`，历史的 `WV_YRATE_MAX` 不再存在；
- `COM_RAM_MAX` 从 95 变为 100；
- `MAV_0_RATE` 从 1200 变为 4000；
- 其余共有参数在容差内一致。

## 当前安全参数结论

以下均来自本次 974/974 实时导出，不再是历史推断：

| 项目 | 当前值 | 结论 |
|---|---:|---|
| `CBRK_SUPPLY_CHK` | `894281` | 命中魔数，commander 跳过供电有效性检查 |
| `CBRK_IO_SAFETY` | `22027` | 命中魔数，IO safety 被禁用 |
| `CBRK_USB_CHK` | `197848` | 命中魔数，USB connected arming check 被禁用 |
| `CBRK_FLIGHTTERM` | `121212` | 命中魔数，FailureDetector critical failure 从 Terminate 降为 Warn |
| `CBRK_BUZZER` | `0` | 未禁用蜂鸣器 |
| `CBRK_VTOLARMING` | `0` | 未启用 VTOL 固定翼模式 arming bypass |
| `GF_MAX_HOR_DIST` | `0 m` | 水平围栏距离未配置 |
| `GF_MAX_VER_DIST` | `0 m` | 垂直围栏距离未配置 |
| `COM_FLT_TIME_MAX` | `-1 s` | 飞行时间上限关闭 |
| `COM_RC_LOSS_T` | `0.5 s` | RC loss 检测时限存在 |
| `COM_OF_LOSS_T` | `0.5 s` | offboard loss 检测时限存在 |
| `COM_OBL_RC_ACT` | `4` | 动作枚举须在主动 G4 前按当前 PX4 版本核对 |
| `COM_LOW_BAT_ACT` | `2` | 动作枚举须在低电测试前核对 |
| `EKF2_RNG_CTRL` | `0` | 没有假设 range aid |

PX4 源码 `a8f2dbdfff4792c92f576060ab947f8e588d6f8b` 的参数说明和实际分支已保存到
`artifacts/circuit-breaker-source-evidence.txt`，避免只凭魔数名称推断。

没有执行任何参数修改。候选值、验证方法和回滚值见 `PARAMETER_CHANGE_CANDIDATES.md`。

## 电池与 ULog

当前参数确认：

- `BAT1_SOURCE=0`、`BAT1_V_CHANNEL=-1`、`BAT1_I_CHANNEL=-1`、4 cells；
- low/critical/emergency 阈值为 15%/7%/5%；
- `COM_ARM_SDCARD=1`、`SDLOG_MODE=0`、`SDLOG_PROFILE=1`。

第三次受监控物理重插后，PX4 system 1/component 1 在 0.336 秒内返回 19 个 `LOG_ENTRY`，日志
大小 288,171–2,575,246 bytes，证明 SD/MAVLink 日志目录可访问。随后请求最新日志前 90 字节时
USB 数据面已再次静默，未收到 `LOG_DATA`；因此没有验证 ULog magic、当前 logger 活跃状态或
剩余空间，不能把“可列目录”写成“ULog 完全就绪”。

## Agent guard 与收尾

尝试通过生产 guard 启动唯一 Agent 读取最新 preflight 时，guard 在启动 Agent 前 fail-closed：

```text
DMA free-above-high 233508 KiB is below required 262144 KiB
```

因此 Agent 没有启动，`/dev/ttyTHS0` 没有 owner，也没有产生 `/fmu/in/*` writer。前一 G4-0
session 的实时状态仍是 `pre_flight_checks_pass=false`，本 session 不宣称已经刷新该状态。

## 判定

当前参数导出阻塞已经解除，历史参数也已完成可复核 diff；但以下任一项都足以保持 NO-GO：

1. 四个生产相关 circuit breaker 处于禁用魔数；
2. 水平/垂直围栏距离为 0，最长飞行时间为 -1；
3. 电池来源和容量/time-remaining 估算尚未证实；
4. ULog 当前写入状态、剩余空间和文件头未验证；
5. Agent guard 当前因 DMA 水位拒绝启动；
6. 主动 G4 失效测试尚未逐项授权或执行。

所以 **G4 仍为 BLOCKED，禁止进入 G5，禁止装桨飞行。**
