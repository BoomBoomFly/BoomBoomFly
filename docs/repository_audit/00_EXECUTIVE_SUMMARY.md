# 仓库完整审查执行摘要

- 审查日期：2026-07-28（Asia/Shanghai）
- 仓库：`/home/c/px4_ws/BoomBoomFly`
- 根基线：`master@df01b9280c0e79a05ad1e4cec727e7427c9251ca`
- 目标：PX4 v1.16.2、ROS 2 Foxy、DDS-only production
- 方法：8 个独立只读线程已启动；线程 B 返回部分证据，其余线程超时后由主协调线程逐域补证
- 硬件访问：否
- ROS/PX4/Agent/launch/SITL 启动：否
- 网络访问：否
- 源码、配置修改：否；文档入口与治理同步更新：是
- 删除：86 个过时报告、handoff、dated evidence 与旧 planning 文件（Git 可恢复）

`docs/repository_audit` 原先不存在，本报告直接创建于该目录。完成审查后，用户明确
授权删除已被本报告取代的日期化审查、旧 `current_audit`、失效 handoff、dated
evidence 与旧 planning 快照；当前工作树只保留本报告作为统一审查入口。

## 结论

当前工作区是 **NO-GO**。根仓库本身干净且本地 `HEAD == origin/master`，但两个
production 源码仓库没有检出根锁指定版本：

- `offboard_cpp`：锁 `722e05a…`，实际 `976d621…`
- `vision_to_dds`：锁 `b366db7…`，实际 `0c3a001…`

Wave 4B 的 H0–H3 通过记录绑定锁定版本；当前旧 Offboard checkout 仍直接发布
三个 `/fmu/in/*` 控制话题，没有实例化已测试的安全门，并保留 `TEXT_RC` 和
默认自动解锁。仓库自带当前态静态验证器实际返回：

```text
H0_EXIT=2
{"error":"production SafetyGateAdapter is missing","status":"FAIL"}
```

因此历史 WSL 构建/测试通过不能提升当前工作区门禁。

## 风险统计

| 严重度 | 数量 | 主要阻塞 |
|---|---:|---|
| P0 | 2 | live PX4 writer 绕过安全门；默认自动解锁/mock RC |
| P1 | 8 | production SHA 漂移、视觉契约、RC topic、初始状态、串口协议、旧 launch、DDS/SITL 缺口 |
| P2 | 7 | 依赖声明、生命周期、视觉阻塞/内存、设备身份、CI、系统依赖、文档漂移 |
| P3 | 4 | 冗余依赖/元数据、生成目录、README 漂移、测试工具缺口 |
| 合计 | 21 | 详见 `09_RISK_REGISTER.md` |

## 最关键的 10 个问题

1. `[P0-CTRL-001]` 当前 Offboard live writer 没有接入 `OffboardRuntimeGate`。
2. `[P0-CTRL-002]` `TEXT_RC` 无条件编译、`enable_arm=true`，无 fresh RC 分支仍可进入解锁流程。
3. `[P1-GIT-001]` Offboard/vision checkout 与 exact lock 不一致，当前历史门禁证据失配。
4. `[P1-CODE-001]` Odom 首帧判定错误，`p/pos_jump` 在安全判断前可能未初始化。
5. `[P1-VISION-001]` 视觉发布混用时钟、固定 frame/quality/reset，缺少健康与 epoch 门。
6. `[P1-CTRL-003]` Offboard 依赖 `/fmu/out/rc_channels`，而文档确认 v1.16.2 默认 DDS topics 不导出它。
7. `[P1-LAUNCH-001]` 旧 `px4_bringup` 仍含 MAVROS、相机、串口和控制组合入口。
8. `[P1-SER-001]` 隔离串口两端协议不一致，ROS 解析奇数长度还可能越界。
9. `[P1-GIT-002]` 多个 optional checkout 大规模 dirty；虽有 receipt，当前可选构建不是 clean baseline。
10. `[P1-CTRL-004]` 当前没有获准执行的项目级 DDS/SITL orchestration 与 transport command card。

## 门禁

```text
静态审查门：NO-GO
软件构建门：NOT RUN
SITL 门：NOT RUN
实机门：NOT AUTHORIZED
```

操作性判定：

- 构建：**NO-GO**（当前 H0 先失败；本轮未运行 build）
- SITL：**NO-GO**（无获准 orchestration；本轮未运行）
- 实机：**NO-GO**（存在 P0 且未授权）

## 已确认的正向事实

- `px4_msgs@392e831…` 与 lock 一致，并指向 tag `v1.16.2`。
- `VehicleStatus.msg` 为 `MESSAGE_VERSION=1`，当前 Offboard topic 常量使用
  `fmu/out/vehicle_status_v1`。
- production 包边界静态验证通过：75 个可发现包中仅 3 个被权威路径选择。
- 串口 quarantine 静态验证通过：发现数、production launch 引用、production
  package 引用均为 0。
- CI action 使用 immutable SHA，权限为 `contents: read`。
- 未发现私钥、证书、`.env` 或非 fixture 的明显凭据候选。

## 审查限制

- 未 fetch，不能声称远端实时 ahead/behind 或 remote 可用性。
- 未 build、未运行 ROS graph、未执行 formal SITL。
- 未探测 USB、串口、相机、雷达、飞控或网络端点。
- PX4 firmware 源码不在当前工作区；v1.16.2 firmware topic 与参数结论依赖仓库
  已有锁定证据，最终仍需 Phase 0 固件身份卡确认。

## 推荐下一条 Codex 指令

> 只读执行 Phase 0：核对并冻结 `workspace.lock.repos`、当前 nested HEAD、Wave 4B
> receipt 与 PX4 v1.16.2 firmware/topic profile；不要 checkout、fetch、build、启动
> ROS/PX4 或访问硬件，输出精确的 GO/NO-GO 差异清单。
