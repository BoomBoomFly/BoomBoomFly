# BBF-DOC-WAVE 文档一致性审查

> 报告状态：`STATICALLY_VERIFIED`
>
> 审查基线：`master@5a0e6edd4930474506a1046d414425893ebd800f`
>
> production：`BLOCKED`

## 1. 审查口径

本报告不删除或重写旧审计、handoff 或 evidence。旧报告是带日期的 `HISTORICAL_EVIDENCE`；当前 checkout 的事实由 Git identity、Accepted ADR、控制权矩阵和本轮静态核对决定。计划、草案和真实验证结果不得互相提升状态。

## 2. 重复文档

| 重复/重叠 | 观察 | 后续处置建议 |
|---|---|---|
| `README.md` 与 `docs/handoff.md` | 都包含当前版本、工作区、DDS session 和下一步；易同时漂移 | README 只保留稳定入口，handoff 只做短期导航；易变事实迁移到 machine-readable current receipt（T08/T00 范围） |
| handoff 与 `00_*`、`08_*`、`10_*` | 当前状态、路线和任务重复 | 审计保留历史；以 `DOCUMENT_AUTHORITY.md` 的权威规则区分 current/plan/history |
| ADR、根控制权矩阵与本轮 `CONTROL_AUTHORITY.md` | 控制 writer/owner 规则重复 | ADR 决策优先，根矩阵是规范规则，本轮文档只做运行映射，不得覆盖 ADR |
| `08_ROADMAP.md`、`10_NEXT_CODEX_TASKS.md` 与本轮 planning | 任务阶段重复且旧基线不同 | 旧文件保留历史；后续执行以当前 checkout 的 backlog/milestone 为导航，状态改变需新 receipt/evidence |

## 3. 冲突结论

| 位置 | 冲突 | 当前处置 |
|---|---|---|
| `src/offboard_cpp/README.md` | 仍包含 PX4 1.14.3、firmware 烧录、swarm/实飞示例和自动 arm 等历史说明 | 记录为包级历史说明；不得覆盖根 ADR 的 PX4 v1.16.2 DDS-only、单机和 production 禁用决策 |
| `src/px4_bringup` 与根 ADR/矩阵 | 可执行 launch 组合 MAVROS/旧 serial 并引用 DDS 专用端口 | 路径保持 `BLOCKED`；技术隔离由 T01 负责，本轮不改 package/allowlist |
| handoff “当前状态”与当前工作树 | handoff 记录旧分支/发布过程和其他 dirty checkout；当前根状态显示既有 `src/serial_driver_ros` dirty | handoff 作为带时间导航；当前结论以本报告身份表为准，不推断嵌套依赖已 clean |
| SITL 分级命名 | 旧 roadmap 曾描述六级细分，本轮任务要求四级 Level 0–3 | 本轮四级为治理门；每级内部仍可包含静态/单元/集成子检查，不把命名差异当运行通过 |

## 4. 过期路径

- `README.md`、`docs/handoff.md` 和历史审计包含 `/home/c/BoomBoomFly`；当前工作区是另一个路径。旧绝对路径不可作为可移植命令。
- `Scripts/README.md` 曾引用非 canonical clone 来源；canonical origin 以当前 `git remote -v` 为准。本轮受 T00/T01 范围限制未修改该文件。
- 旧硬件/感知包含个人路径、设备入口和历史 launch；它们继续保持 excluded/`BLOCKED`，不作为当前批准入口。

## 5. 旧 HEAD 与分支

下列旧身份只具有 `HISTORICAL_EVIDENCE` 状态：

- `agent/follow-latest-offboard@3ce28094e14ed720987c5fc6d1172e377f09b1cc`；
- handoff 中的旧 `master@16a0d8a` 和阶段分支；
- 旧审计执行时的其他远端 default HEAD。

本轮所有新文档统一绑定 `master@5a0e6edd4930474506a1046d414425893ebd800f`。提交本轮文档后，报告中的 “HEAD before” 仍是审计输入身份；“HEAD after” 只用于交接，不反向把本轮静态核对冒充新提交的动态验证。

## 6. 旧参数快照

- `docs/evidence/PX4_PARAMS_20260724T203458+0800.json` 是调整前 `HISTORICAL_EVIDENCE`，不能代表当前 PX4 参数。
- 感知审计引用 `docs/evidence/px4_params_full_20260724T171437+0800.json`，当前 tree 不存在该路径；应改为指向真实历史文件或明确“报告执行时路径”，但本轮不重写旧审计。
- 任何 Level 2/3 promotion 都要求重新获取与当前 firmware/source/transport identity 绑定的只读参数快照；未经另行授权不得采集。

## 7. 无效与未验证链接

已发现的本地无效引用：

1. `docs/audits/2026-07-26/05_PERCEPTION_AND_INTEGRATION.md` 引用不存在的 `docs/adr/0001-dds-only-control-path.md`；当前真实 ADR 是 `0001-dds-only-control-authority.md`。
2. 同一报告引用当前 tree 不存在的 `docs/evidence/px4_params_full_20260724T171437+0800.json`。

旧审计不直接修改；建议后续增加勘误索引或不可变审计的 `supersedes/correction` 元数据。外部 HTTP 链接未做网络可达性验证；本轮只检查仓库内相对链接。

## 8. 敏感信息

- 旧 README/handoff/evidence/audit 含个人绝对路径、真实设备 serial、VID:PID、串口拓扑和个人邮箱；它们是既有历史内容，本任务没有复制到新文档。
- 本轮新文档允许出现 `/dev/ttyTHS0` 等安全资源名称和 `@CONTROL-MAINTAINER` 等角色占位；前者不是硬件唯一标识，后者明确不可直接启用。
- `SECURITY.md` 未虚构邮箱，联系地址保留 `待维护者填写`。
- 发布公开 evidence 前仍需 T08/安全治理线执行脱敏策略；本轮未修改 evidence 基础设施。

## 9. 状态标记与草案检查

- 本轮能力状态只使用规定枚举；未使用项目禁止的含糊进度措辞。
- `BENCH_ACCEPTANCE_DRAFT.md` 和 `LIMITED_FLIGHT_ACCEPTANCE_DRAFT.md` 均显著标记 DRAFT、`UNVERIFIED` 和 `BLOCKED`。
- “文档 `IMPLEMENTED`”仅表示流程文本存在，不表示 Level 0–3 动态验收通过。
- 历史 9/9 gtest 和真实 DDS output session 均标记为 `HISTORICAL_EVIDENCE`，不是本轮结果。
- production、`rc_channels` firmware profile、graph guard、owner/lease、ACK、PRESTREAM、fault lattice 和实机控制保持 `BLOCKED`、`PLANNED` 或 `UNVERIFIED`。

## 10. Markdown 与 Mermaid

- 仓库内未发现已安装的 Markdown link checker；使用自定义只读相对路径检查。锚点和外链可达性不由该检查证明。
- 仓库内未发现 `mmdc`；使用自定义 fence 配对、diagram header 和基础结构检查。渲染级语法验证为 `BLOCKED`，未安装新工具。
- 最终命令和结果记录于本报告第 12 节及主协调终端交接。

## 11. Independent Reviewer 结论

Reviewer 对架构、runbook、治理、planning 和审计文件完成了只读独立复核，未直接修改文件。三轮发现均由主协调修复并经定点复查。最终结论为 `STATICALLY_VERIFIED`：未解决文档级 P0 为 0，P1 为 0。

## 12. 检查结果

| 检查 | 结果 |
|---|---|
| `git diff --check` | `STATICALLY_VERIFIED`：working-tree 与 staged/cached 检查均 PASS |
| 本轮文件相对 Markdown links | `STATICALLY_VERIFIED`：PASS |
| 旧文档 broken-reference scan | `STATICALLY_VERIFIED`：发现第 7 节两类既有问题 |
| Mermaid 基础结构 | `STATICALLY_VERIFIED`：PASS；渲染级 `BLOCKED` |
| 新文档个人绝对路径 | `STATICALLY_VERIFIED`：无命中 |
| 新文档硬件唯一标识/敏感内容 | `STATICALLY_VERIFIED`：无真实唯一标识或 secret；角色占位/待填联系人已解释 |
| 草案冒充验证 | `STATICALLY_VERIFIED`：无 |
| Reviewer 文档级 P0/P1 | 0 / 0 |
