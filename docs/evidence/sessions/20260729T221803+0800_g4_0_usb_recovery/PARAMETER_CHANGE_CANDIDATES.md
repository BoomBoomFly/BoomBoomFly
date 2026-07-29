# PX4 参数候选变更卡（未执行）

基线：`parameters-live-bytewise-after-replug.json`，974/974 参数，SHA-256
`7ff75ac24b0f91d5dcd931ad39c18eda8db068ba22316f71c227cd693e3e99fb`。

本卡只记录候选方案。**本 session 没有参数写入；以下任何一组都必须重新取得明确授权。**

## 风险组 A：Circuit breaker

| 参数 | 当前值 | 候选值 | 原因 | 写后验证 | 回滚值 |
|---|---:|---:|---|---|---:|
| `CBRK_SUPPLY_CHK` | `894281` | `0` | 当前魔数使 commander 直接跳过供电检查 | 重导参数；确认 power input；验证断供检查；不得 Arm | `894281` |
| `CBRK_IO_SAFETY` | `22027` | `0` | 当前魔数禁用 IO safety；实测 safety button available | 重启；重导参数；拆桨验证 safety 按钮状态 | `22027` |
| `CBRK_USB_CHK` | `197848` | `0` | 当前魔数禁用 USB connected arming check；源码明确推荐生产值为 0 | 重导参数；USB 连接时必须阻止 preflight，断开 USB 后复验 | `197848` |
| `CBRK_FLIGHTTERM` | `121212` | 待安全决策；如恢复则为 `0` | 当前魔数把 FailureDetector critical failure 从 Terminate 降为 Warn；改为 0 会引入主动终止行为 | 单独审批；重启；重导参数；仅拆桨验证故障策略，禁止直接飞行验证 | `121212` |

`CBRK_FLIGHTTERM` 不能与前三项机械合并写入。是否启用 flight termination 必须结合机型、飞行区域、
高度包线和失效策略单独决策。

## 风险组 B：围栏、任务时限与速度包线

| 参数 | 当前值 | 候选方向 | 说明 |
|---|---:|---|---|
| `GF_MAX_HOR_DIST` | `0 m` | 必须选定非零值 | 需要场地实测半径，当前不虚构数值 |
| `GF_MAX_VER_DIST` | `0 m` | 必须选定非零值 | 需要相对 home 的安全高度和测试场地净空 |
| `COM_FLT_TIME_MAX` | `-1 s` | 初次短悬停候选 `60 s` | 写前先核对任务软件自身的最长任务时限 |
| `MPC_XY_VEL_MAX` | `3.0 m/s` | 初次测试建议不高于 `1.0 m/s` | 最终值需结合 PX4 手动/自动模式影响审计 |
| `MPC_Z_VEL_MAX_UP` | `1.0 m/s` | 任务层继续限制 `0.3 m/s` | 不假设 PX4 参数允许直接设为任务值 |
| `MPC_Z_VEL_MAX_DN` | `0.5 m/s` | 任务层继续限制 `0.2 m/s` | 不假设 PX4 参数允许直接设为任务值 |
| `MIS_TAKEOFF_ALT` | `1.5 m` | 不用于本次 0.5 m VERTICAL_TEST | 普通任务高度由已锁定的 `vertical_test.yaml` 控制 |

围栏尺寸需要用户提供场地半径和净空后才能确定。不得把比赛高度 1.5 m 用于首次实机测试。

## 风险组 C：电池与 ULog

- 当前 `BAT1_SOURCE=0`、`BAT1_V_CHANNEL=-1`、`BAT1_I_CHANNEL=-1`；DDS 电池流存在，但
  cell voltage、容量和 time remaining 字段不完整。必须先确认实际电源模块/智能电池来源。
- 当前阈值为 low 15%、critical 7%、emergency 5%，`COM_LOW_BAT_ACT=2`。在确认来源和剩余量
  估算可信前，不进行低电失效注入。
- 当前 `COM_ARM_SDCARD=1`、`SDLOG_MODE=0`、`SDLOG_PROFILE=1`；MAVLink 能列出 19 个日志，
  但当前 logger 活跃状态、剩余空间和最新文件头仍未验证。

## 执行纪律

每个获批风险组都必须按以下顺序执行：

1. 保存写前 974 参数文件及 SHA-256；
2. 记录每个参数旧值、批准的新值、理由和回滚值；
3. 一次只写一个获批风险组；
4. 不假设写入成功，立即重新导出完整参数；
5. 对写前/写后文件做逐项 diff；
6. 只在拆桨、固定、ESC 动力隔离下执行对应验证；
7. 失败时按记录值逐项回滚，再次完整导出和 diff。
