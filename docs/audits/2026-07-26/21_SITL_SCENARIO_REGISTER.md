# BBF-SITL-SPEC-WAVE 场景登记册

> 登记状态：`STATICALLY_VERIFIED`
>
> 动态 PX4 SITL：`UNVERIFIED`
>
> 场景事实源：`docs/verification/scenarios/catalog.json`（schema `1.0.0`）

`Deadline` 是规范中的最大有界检测/完成窗口，不是本轮测量值。`Source identity`
是正式执行时必须证明的 identity class；本轮仅校验其声明结构。

| Scenario ID | 类型 | 对应 Audit/Task | 状态 | Blocker | Source identity | Deadline | 自动恢复 | 实现负责人 |
|---|---|---|---|---|---|---|---|---|
| SITL-NORMAL-001 | 正常 | AUD-003/012; T00/T01/T08 | `BLOCKED` | T00,T01,T08 | locked PX4 + Agent artifacts | 5s | 不适用 | Integration/Test Maintainer |
| SITL-NORMAL-002 | 正常 | AUD-003/012; T00/T01/T03/T08 | `BLOCKED` | T00,T01,T03,T08 | locked PX4 + approved Offboard | 3s | 不适用 | Integration/Test Maintainer |
| SITL-NORMAL-003 | 正常 | AUD-003; T00/T01/T03/T08 | `BLOCKED` | T00,T01,T03,T08 | locked PX4 artifact | 500ms | 不适用 | Integration/Test Maintainer |
| SITL-NORMAL-004 | 正常 | AUD-009; T00/T01/T05/T08 | `BLOCKED` | T00,T01,T05,T08,safety | locked PX4 artifact | 500ms | 不适用 | Integration/Test Maintainer |
| SITL-NORMAL-005 | 正常 | AUD-009; T00/T01/T03/T05/T08 | `BLOCKED` | T00,T01,T03,T05,T08,safety | locked PX4 artifact | 500ms | 不适用 | Integration/Test Maintainer |
| SITL-NORMAL-006 | 正常 | AUD-009; T00/T01/T03/T05/T08 | `BLOCKED` | T00,T01,T03,T05,T08,safety | locked PX4 artifact | 500ms | 不适用 | Integration/Test Maintainer |
| SITL-NORMAL-007 | 正常 | AUD-005/012; T00/T01/T02/T05/T08 | `BLOCKED` | T00,T01,T02,T05,T08 | locked PX4 artifact | 500ms | 不适用 | PX4 + Integration Maintainer |
| SITL-NORMAL-008 | 正常 | AUD-003/005/009; T00–T05/T08 | `BLOCKED` | T00–T05,T08,safety | PX4 + approved Offboard | 500ms | 不适用 | Control + Integration Maintainer |
| SITL-NORMAL-009 | 正常 | AUD-003; T01/T03/T04/T06/T08 | `BLOCKED` | T01,T03,T04,T06,T08 | PX4 + approved Offboard | 1600ms | 不适用 | Control + Integration Maintainer |
| SITL-NORMAL-010 | 正常 | AUD-003/008; T01/T03/T04/T06/T08 | `BLOCKED` | T01,T03,T04,T06,T08 | PX4 + approved Offboard | 1s | 不适用 | Control + PX4 Maintainer |
| SITL-NORMAL-011 | 正常 | AUD-003/008; T01/T03–T06/T08 | `BLOCKED` | T01,T03–T06,T08,safety | PX4 + approved Offboard | 600ms | 不适用 | Control + Safety Reviewer |
| SITL-NORMAL-012 | 正常 | AUD-002/034; T00/T01/T04/T06/T08 | `BLOCKED` | T00,T01,T04,T06,T08 | PX4 + Agent + recorder | 5s | 不适用 | Integration/Test Maintainer |
| SITL-FAULT-001 | 故障 | AUD-004/007/014; T00/T01/T03/T05/T06/T08 | `BLOCKED` | T00,T01,T03,T05,T06,T08 | PX4 + Offboard profile | 500ms | 否 | Safety + Integration Maintainer |
| SITL-FAULT-002 | 故障 | AUD-004/007/014; T00/T01/T03/T05/T06/T08 | `BLOCKED` | T00,T01,T03,T05,T06,T08 | PX4 + Offboard profile | 500ms | 否 | Safety + Integration Maintainer |
| SITL-FAULT-003 | 故障 | AUD-004/007/014; T00/T01/T03/T05/T06/T08 | `BLOCKED` | T00,T01,T03,T05,T06,T08 | PX4 + Offboard profile | 500ms | 否 | Safety + Integration Maintainer |
| SITL-FAULT-004 | 故障 | AUD-004/007/014; T00/T01/T03/T05/T06/T08 | `BLOCKED` | T00,T01,T03,T05,T06,T08 | PX4 + Offboard profile | 750ms | 否 | Safety + Integration Maintainer |
| SITL-FAULT-005 | 故障 | AUD-004/006/007; T00/T01/T03/T05/T06/T08 | `BLOCKED` | T00,T01,T03,T05,T06,T08,safety | PX4 + Offboard profile | 750ms | 否 | Safety + Control Maintainer |
| SITL-FAULT-006 | 故障 | AUD-006/007/014; T00/T01/T03/T05/T06/T08 | `BLOCKED` | T00,T01,T03,T05,T06,T08,safety | PX4 + Offboard profile | 750ms | 否 | Safety + Control Maintainer |
| SITL-FAULT-007 | 故障 | AUD-003/005/007; T00–T03/T05/T06/T08 | `BLOCKED` | T00–T03,T05,T06,T08 | PX4 + Offboard profile | 1250ms | 否 | Safety + PX4 Maintainer |
| SITL-FAULT-008 | 故障 | AUD-005/007/014; T00–T03/T05/T06/T08 | `BLOCKED` | T00–T03,T05,T06,T08,safety | PX4 + Offboard profile | 500ms | 否 | Safety + PX4 Maintainer |
| SITL-FAULT-009 | 故障 | AUD-005/007/014; T00–T03/T05/T06/T08 | `BLOCKED` | T00–T03,T05,T06,T08,safety | PX4 + Offboard profile | 750ms | 否 | Safety + PX4 Maintainer |
| SITL-FAULT-010 | 故障 | AUD-006/007/014; T00/T01/T03/T05/T06/T08 | `BLOCKED` | T00,T01,T03,T05,T06,T08,safety | PX4 + Offboard profile | 750ms | 否 | Safety + Control Maintainer |
| SITL-FAULT-011 | 故障 | AUD-007/014/018; T00/T01/T04–T06/T08 | `BLOCKED` | T00,T01,T04–T06,T08,safety | PX4 + Agent profile | 750ms | 否 | Safety + Integration Maintainer |
| SITL-FAULT-012 | 故障 | AUD-007/014/018; T00/T01/T04–T06/T08 | `BLOCKED` | T00,T01,T04–T06,T08,safety | PX4 + Agent profile | 1250ms | 否 | Safety + Integration Maintainer |
| SITL-FAULT-013 | 故障 | AUD-004/007/014; T00/T01/T03–T06/T08 | `BLOCKED` | T00,T01,T03–T06,T08,safety | PX4 + Offboard profile | 1250ms | 否 | Safety + PX4 Maintainer |
| SITL-FAULT-014 | 故障 | AUD-002/007/014; T00/T01/T04–T06/T08 | `BLOCKED` | T00,T01,T04–T06,T08,safety | owner + authority lease | 750ms | 否 | Safety + Control Maintainer |
| SITL-FAULT-015 | 故障 | AUD-001/002/014; T00/T01/T04–T06/T08 | `BLOCKED` | T00,T01,T04–T06,T08 | owner + duplicate owner | 500ms | 否 | Control + Integration Maintainer |
| SITL-FAULT-016 | 故障 | AUD-001/014; T00/T01/T04–T06/T08 | `BLOCKED` | T00,T01,T04–T06,T08 | approved + duplicate writer | 500ms | 否 | Control + Integration Maintainer |
| SITL-FAULT-017 | 故障 | AUD-001/014/018; T00/T01/T04–T06/T08 | `BLOCKED` | T00,T01,T04–T06,T08 | profile guard + Offboard | 500ms | 否 | Control + Integration Maintainer |
| SITL-FAULT-018 | 故障 | AUD-001/014/018; T00/T01/T04–T06/T08 | `BLOCKED` | T00,T01,T04–T06,T08 | PX4 + Agent profile | 750ms | 否 | PX4 + Integration Maintainer |
| SITL-FAULT-019 | 故障 | AUD-006/007/009; T00/T01/T03/T05/T06/T08 | `BLOCKED` | T00,T01,T03,T05,T06,T08,safety | PX4 + Offboard epoch | 500ms | 否 | Safety + Control Maintainer |
| SITL-FAULT-020 | 故障 | AUD-006/007/009; T00/T01/T03/T05/T06/T08 | `BLOCKED` | T00,T01,T03,T05,T06,T08,safety | PX4 + Offboard epoch | 500ms | 否 | Safety + Control Maintainer |
| SITL-FAULT-021 | 故障 | AUD-006/014/017; T00/T01/T03–T06/T08 | `BLOCKED` | T00,T01,T03–T06,T08,safety | owner lease + Offboard | 500ms | 否 | Safety + Control Maintainer |
| SITL-FAULT-022 | 故障 | AUD-001/005/014; T00–T02/T04–T06/T08 | `BLOCKED` | T00–T02,T04–T06,T08 | PX4 endpoint + contaminant | 500ms | 否 | Test + PX4 Maintainer |
| SITL-FAULT-023 | 故障 | AUD-007/009/014; T00/T01/T03/T05/T06/T08 | `BLOCKED` | T00,T01,T03,T05,T06,T08,safety | sensor + vision endpoint | 750ms | 否 | Safety + Perception Maintainer |
| SITL-FAULT-024 | 故障 | AUD-006/008/014; T00/T01/T05/T06/T08 | `BLOCKED` | T00,T01,T05,T06,T08,safety | sensor/frame + vision endpoint | 500ms | 否 | Safety + Perception Maintainer |

## 统计

```text
normal scenarios: 12
fault scenarios: 24
PLANNED: 0
STATICALLY_VERIFIED: 0
UNIT_TESTED: 0
BLOCKED: 36
UNVERIFIED: 0
```

场景状态保持 `BLOCKED`，即使 schema、catalog 和 synthetic fixture 单元测试通过也
不提升。`automatic_recovery=false` 适用于全部 24 个故障场景；恢复必须消费 T05
批准的 reset/health-window 策略。
