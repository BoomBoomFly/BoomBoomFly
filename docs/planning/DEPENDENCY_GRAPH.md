# BoomBoomFly Task Dependency Graph

> 文档状态：`PLANNED`
>
> 图中节点是本地 backlog 项或既有工作线，不代表真实 GitHub Issue。箭头 `A --> B`
> 表示 B 的集成/验收依赖 A；纯设计或失败测试可以在接口冻结后提前并行。

## P0/P1 依赖图

```mermaid
flowchart LR
    T00["T00<br/>workspace and toolchain baseline"]
    T01["T01<br/>DDS-only package and launch boundary"]
    T08["T08<br/>evidence and rollback schema"]

    A010["TASK-010<br/>DDS-only boundary"]
    A011["TASK-011<br/>dirty receipts"]
    A012["TASK-012<br/>PX4 rc_channels profile"]
    A013["TASK-013<br/>required CI"]
    A018["TASK-018<br/>transport identity"]

    A006["TASK-006<br/>input validity"]
    A004["TASK-004<br/>ACK and fresh status"]
    A003["TASK-003<br/>PRESTREAM"]
    A001["TASK-001<br/>graph guard"]
    A002["TASK-002<br/>owner and lease"]
    A017["TASK-017<br/>atomic input"]
    A005["TASK-005<br/>RC and kill"]
    A019["TASK-019<br/>safety config"]
    A007["TASK-007<br/>fault lattice"]
    A014["TASK-014<br/>safety tests"]

    A015["TASK-015<br/>PX4 DDS SITL"]
    A016["TASK-016<br/>endpoint contract"]

    A008["TASK-008<br/>vision frames"]
    A009["TASK-009<br/>vision time and health"]
    A022["TASK-022<br/>perception and EKF2 profile"]
    A023["TASK-023<br/>sensor identity"]
    A024["TASK-024<br/>precision landing"]

    A020["TASK-020<br/>license decision"]
    A021["TASK-021<br/>staged runbook"]

    T00 --> A011
    T01 --> A010
    T08 --> A012
    T08 --> A021

    A011 --> A012
    A010 --> A013
    A010 --> A018
    A010 --> A001

    A006 --> A004
    A006 --> A003
    A004 --> A003
    A018 --> A001
    A001 --> A002
    A002 --> A017
    A003 --> A005
    A012 --> A005
    A005 --> A019
    A004 --> A007
    A005 --> A007
    A014 --> A007

    A012 --> A015
    A018 --> A015
    A014 --> A015
    A012 --> A016
    A015 --> A016

    A018 --> A022
    A008 --> A009
    A008 --> A022
    A009 --> A022
    A022 --> A023
    A012 --> A024
    A008 --> A024
    A009 --> A024
    A022 --> A024

    A003 --> A014
    A004 --> A014
    A002 --> A014
    A017 --> A014
    A019 --> A014

    A012 --> A021
    A015 --> A021
    A007 --> A021

    P0G["ALL_P0_CLOSED<br/>AUD-001 through AUD-009"]
    A001 --> P0G
    A002 --> P0G
    A003 --> P0G
    A004 --> P0G
    A005 --> P0G
    A006 --> P0G
    A007 --> P0G
    A008 --> P0G
    A009 --> P0G
    P0G --> A021
```

## 里程碑依赖图

```mermaid
flowchart TD
    M0["M0<br/>可复现基线"]
    M1["M1<br/>PX4 DDS firmware profile"]
    M2["M2<br/>Offboard 安全闭环"]
    M3["M3<br/>SITL 验收"]
    M4["M4<br/>感知状态估计"]
    M5["M5<br/>拆桨台架"]
    M6["M6<br/>有限实机"]
    P0G["ALL_P0_CLOSED<br/>AUD-001 through AUD-009"]

    M0 --> M1
    M0 --> M2
    M1 --> M2
    M1 --> M3
    M2 --> M3
    M2 --> M4
    M3 --> M4
    M3 --> M5
    M4 -. "仅带视觉 profile" .-> M5
    P0G --> M5
    M5 --> M6
```

虚线表示 M4 只阻塞启用外部视觉的台架/实机 profile；它不授权绕过 M2/M3，也不让
纯 telemetry 台架自动获批。`ALL_P0_CLOSED` 是独立聚合门，覆盖 AUD-001 至 AUD-009，
不能由 M3/M4 的阶段箭头替代。对“启用视觉前”的条件 P0，关闭方式必须是完成验收，
或以静态和运行负向测试证明对应视觉 profile 被机械禁用；仅写“本次不用视觉”不能
满足该门。

## 可并行矩阵

| 波次 | 可并行工作 | 并行前冻结项 | 汇合门 |
|---|---|---|---|
| Wave 0 | T00、T01、T08 | 各自文件所有权 | M0 baseline review |
| Wave 1 | TASK-012 静态生成；TASK-006 validity；TASK-004 ACK 测试；TASK-002 协议；TASK-013 CI 骨架 | endpoint、epoch、authority schema | M1/M2 interface review |
| Wave 2 | TASK-003 PRESTREAM；TASK-001 graph guard；TASK-017 atomic input；TASK-008 frame；TASK-009 time tests | Offboard envelope、profile identity、frame/time ADR | M2 unit gate |
| Wave 3 | TASK-005 RC/kill；TASK-019 safety config；TASK-014 fault tests；TASK-022 perception profile | M1 RC source、M2 interfaces | fault table approval |
| Wave 4 | TASK-015 normal/fault scenarios/reader assertions；TASK-016 endpoint verification | orchestration and event taxonomy | M3 SITL gate |
| Wave 5 | TASK-023 sensor degradation；TASK-024 precision-landing design only；TASK-021 bench checklist preparation | M3 results、M4 ordinary vision status | M4/M5 go/no-go |

“可并行”只表示不同文件或已冻结接口上的工作可以并行；同一实现文件的最终集成仍由
单一 owner 串行完成。

## 禁止并行的关系

| 先行任务 | 禁止并行/提前的后续任务 | 原因 |
|---|---|---|
| T00/T01/T08 | 其他工作线修改其 scripts/schema/receipt/allowlist/evidence 基础设施 | 文件所有权冲突和事实源分叉 |
| TASK-002 / TASK-017 | Offboard 输入接口的两个独立实现 | owner/lease 与 atomic envelope 必须是同一事务协议 |
| TASK-003 / TASK-004 / TASK-006 | 同时改动同一 FSM/input 文件而未冻结接口 | 高概率覆盖 freshness、ACK 和 PRESTREAM 安全条件 |
| TASK-007 | 未经 Safety Reviewer 批准就实现 Land/Position/停止输出策略 | 危险故障动作不可由实现者单独决定 |
| TASK-012 | TASK-015 的 RC/PX4 endpoint 正式验收 | 没有 PX4 source/profile 时 mock 不能代替 |
| TASK-014 | TASK-015 全量故障注入 | 测试 hook、事件码和 bounded timeout 尚未形成 |
| TASK-008 / TASK-009 | TASK-022 的视觉 publisher enable | frame/time 任一未闭合都会产生危险视觉输入 |
| TASK-022 | TASK-023 真实设备验收、TASK-024 精降实现 | 普通视觉 profile 和健康门必须先完成 |
| M3 | M5 实际拆桨台架 | SITL 未过不得 promotion |
| M5 | M6 有限实机 | 台架与实际 rollback 未通过，且实机需另行授权 |

## 关键路径

```text
T00/T08 -> TASK-011 -> TASK-012 -> TASK-015 -> TASK-021 -> M5 -> M6
T01 -> TASK-010 -> TASK-018 -> TASK-001 -> TASK-002 -> TASK-017
TASK-006 -> TASK-004 -> TASK-003 -> TASK-005 -> TASK-007
上述控制链 -> TASK-014 -> TASK-015
TASK-008 -> TASK-009 -> TASK-022 -> TASK-023
```

最长安全关键路径是 firmware 权威 RC source、Offboard 安全闭环和 SITL 验收三条链的
汇合；排期不得用文档完成或 mock 测试替代其中任一运行门。
