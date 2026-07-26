# 文档、运维、安全与项目治理审查

> 后续变更（2026-07-26T16:46:43+08:00）：归档 `src/px4_bringup` 已对齐上游
> `DDS@0fbdcbf6`，并加入维护清单和精确 lock，但继续排除出 DDS-only 构建与运行。
> 下文的 `planned=15 verified=15 blockers=4` 是审查执行时的历史结果；更新后的
> exact-lock 只读审计为 `planned=16 verified=16 blockers=4`。

## 1. 审查基线与边界

- 审查时间：2026-07-26（Asia/Shanghai）
- 根仓库：`/home/c/BoomBoomFly`
- 分支：`agent/follow-latest-offboard`
- HEAD：`3ce28094e14ed720987c5fc6d1172e377f09b1cc`
- origin：`https://github.com/BoomBoomFly/BoomBoomFly.git`
- 开始时工作树：仅 `docs/audits/` 未跟踪；未覆盖任何既有修改。
- 本轮方式：只读检查当前 Git tree、强制基线文档、两个 evidence 文件、脚本、manifest、受管项目包元数据和主协调提供的 GitHub API 只读结果。
- 未执行：网络访问、远端修改、构建、测试、ROS/PX4/Agent/硬件启动、设备访问、参数/固件/Git 历史修改。

主协调提供的 2026-07-26 GitHub 只读核验结果：

| 项目 | 远端事实 |
|---|---|
| 可见性 | public |
| default branch | `master@62995b4e` |
| `master` protection | `false` |
| Actions workflows | 0 |
| rulesets | `[]` |
| milestones | `[]` |
| releases | `[]` |
| Issues | `has_issues=false` |
| detected license | `null` |
| wiki / projects | enabled / enabled |

上述结果由主协调通过只读 API 获取，本 Agent 未联网复验。对应命令为：

```bash
gh api repos/BoomBoomFly/BoomBoomFly
gh api repos/BoomBoomFly/BoomBoomFly/branches/master
gh api repos/BoomBoomFly/BoomBoomFly/actions/workflows
gh api repos/BoomBoomFly/BoomBoomFly/rulesets
gh api repos/BoomBoomFly/BoomBoomFly/milestones
gh api repos/BoomBoomFly/BoomBoomFly/releases
```

## 2. 已实现且本轮确认的能力

| 能力 | 状态 | 证据 |
|---|---|---|
| 根仓库身份与安全边界说明 | 已实现 | `README.md:1-4,107-108`、`docs/handoff.md:251-260` |
| 精确依赖 lock 与只读审计说明 | 已实现 | `README.md:23-95`、`workspace.lock.repos`、`Scripts/README.md:19-105` |
| `--verify-only` 文档结果 | 当前准确 | 本轮实际得到 `planned=15 verified=15 blockers=4`、exit 1，与 `README.md:47-60` 一致 |
| DDS-only 架构决策 | 已冻结 | `docs/adr/0001-dds-only-control-authority.md` |
| 控制 writer/profile 矩阵 | 已文档化 | `docs/CONTROL_AUTHORITY_MATRIX.md` |
| 历史 PX4 参数完整性 | 文件内完整 | JSON 声明 `expected_count=972`、`received_count=972`、`complete=true` |
| 本地 Markdown 链接 | 当前检查目标均存在 | README、handoff、ADR、matrix 中列出的相对文件均存在 |
| 脚本静态语法 | 本轮通过 | 四个 shell 文件 `bash -n` 返回 0；安装脚本 `--help` 正常 |
| production 状态 | 明确禁用 | `README.md:18`、`docs/handoff.md:5-6`、ADR |

文档只能证明“规则已写明”和“历史证据曾发生”；它不能替代当前源码、运行图、SITL、台架或实机验收。本文严格保留这个区分。

## 3. 发现

### BBF-GOV-001 — 根工程及项目自有包的许可证链不完整

- **级别：P1**
- **分类：许可证 / 发布合规**
- **归属：根仓库 + 受管项目依赖**
- **证据：**
  - 根目录不存在 `LICENSE*` 或 `COPYING*`；主协调远端 API 返回 `license=null`。
  - `src/offboard_cpp/package.xml:8-9` 声明 MIT，但该仓库根未找到许可证正文。
  - `src/vision_to_dds/package.xml:5-8` 仍是 `TODO` 描述和 `TODO: License declaration`，且未找到许可证正文。
  - `workspace.lock.repos` 固定了 15 个仓库，但没有根级许可证清单、NOTICE、SBOM 或许可证/EOL 处置记录。
- **现象：** 无法从根仓库确定 BoomBoomFly 自有代码的授权条款，也无法证明两个关键项目包与第三方组合的可分发性。
- **影响：** release、镜像、固件配套包或交付物可能没有合法分发依据；无法自动审核 notice/源代码义务。
- **触发条件：** 对外发布、组织内分发、生成二进制/容器/firmware artifact 或引入新依赖。
- **检查命令：**
  - `find . -maxdepth 1 -type f \( -iname 'LICENSE*' -o -iname 'COPYING*' \) -print`
  - `find src/offboard_cpp src/vision_to_dds -maxdepth 2 -type f \( -iname 'LICENSE*' -o -iname 'COPYING*' -o -iname 'NOTICE*' \) -print`
  - `nl -ba src/offboard_cpp/package.xml; nl -ba src/vision_to_dds/package.xml`
  - `gh api repos/BoomBoomFly/BoomBoomFly`
- **实际结果：** 根和两个关键项目包均无许可证正文；vision 包声明为 TODO；GitHub 未识别许可证。
- **预期结果：** 根工程和每个项目自有包有经维护者批准的 SPDX 许可证正文，package metadata 一致，并生成依赖许可证/NOTICE/SBOM。
- **建议修复：** 由权利人选择许可证；补根 LICENSE、各自有仓库许可证正文、SPDX 标识和 NOTICE；建立 lock-to-license inventory，未经批准的 unknown/TODO license 阻止 release。
- **验收标准：**
  - GitHub API 能识别根许可证；
  - `package.xml` 声明与仓库许可证正文一致；
  - 15 个 lock 项全部有 source、license、version、maintenance/EOL 和 notice 处置；
  - CI 生成 SBOM/NOTICE，unknown/TODO/冲突许可证使 release job 失败。
- **依赖项：** 维护者/法务授权；BBF-GOV-002。
- **预计工作量：M**
- **是否阻塞 production：是**

### BBF-GOV-002 — 默认分支无保护、无 CI workflow、无 required checks

- **级别：P1**
- **分类：CI / 分支治理 / 发布门**
- **归属：GitHub 仓库设置 + 根仓库**
- **证据：**
  - 根仓库无 `.github/workflows/`。
  - 主协调只读 API：Actions workflows=0、`master` protected=false、rulesets=`[]`。
  - `docs/handoff.md:278-285` 只列人工最终检查，没有远端强制门。
- **现象：** 任意具备写权限的人都可能把未构建、未测试或未审查的提交直接进入默认分支；文档规则不能阻止合并。
- **影响：** lock、控制代码、launch、安全文档和 release artifact 可绕过验证；历史“通过”无法绑定到合并提交。
- **触发条件：** 直接 push、PR 合并、依赖 lock 更新或 release。
- **检查命令：**
  - `find .github -maxdepth 3 -type f -print`
  - `gh api repos/BoomBoomFly/BoomBoomFly/branches/master`
  - `gh api repos/BoomBoomFly/BoomBoomFly/actions/workflows`
  - `gh api repos/BoomBoomFly/BoomBoomFly/rulesets`
- **实际结果：** 无 workflow、无保护、无 ruleset。
- **预期结果：** 默认分支禁止直接写入，至少要求 review、resolved conversations、线性/受控历史及固定的 build/test/lint/docs/security checks。
- **建议修复：** 先建立无硬件 CI，再启用 branch ruleset 和 required checks；release 仅消费同一次通过的构建产物。
- **验收标准：**
  - PR 必须通过 manifest verify、shell/static checks、隔离 build/test、文档链接和 secret/license scans；
  - required check 失败时无法合并；
  - 默认分支禁止 force push/delete 和未经 review 的直接更新；
  - release artifact 可追溯到同一 root HEAD、lock hash、工具链和测试 run。
- **依赖项：** BBF-GOV-001；构建/测试审查路线。
- **预计工作量：L**
- **是否阻塞 production：是**

### BBF-GOV-003 — 缺少发布、四级验收、故障排查与回滚运行手册

- **级别：P1**
- **分类：运维 / 发布 / 回滚 / 安全验收**
- **归属：根仓库**
- **证据：**
  - `docs/handoff.md:225-249` 只有下一阶段概要和“回滚表待定义”，不是可执行 runbook。
  - `docs/CONTROL_AUTHORITY_MATRIX.md:110-140` 提供 graph 断言，但没有 firmware build、SITL、拆桨台架、实机四级门的逐步流程。
  - `docs/evidence/` 仅有一份兼容性累积记录和一份历史参数 JSON。
  - 主协调只读 API：releases=`[]`。
- **现象：** 没有 release checklist、artifact promotion、停止条件、故障树、恢复/回滚表、事故取证或签字机制；也没有证明四级验收被执行的证据包。
- **影响：** 操作者容易把历史 output-only 证据误当作控制验收；故障时无法可靠恢复到已知 firmware/config/source 状态。
- **触发条件：** firmware profile 构建、SITL 通过后进入台架、首次实机、部署失败或现场回滚。
- **检查命令：**
  - `grep -RInE 'runbook|playbook|rollback|回滚|故障排查|发布流程|拆桨' README.md docs Scripts/README.md`
  - `find docs/evidence -maxdepth 2 -type f -print`
  - `gh api repos/BoomBoomFly/BoomBoomFly/releases`
- **实际结果：** 仅有计划性描述，无完整 runbook、release 或四级验收记录。
- **预期结果：** 静态/单元→SITL→拆桨台架→有限实机逐级晋升；每级有前置条件、命令、观察点、停止条件、验收者、证据和回滚。
- **建议修复：** 建立 versioned operations handbook 和四级 acceptance checklist；定义 firmware/参数/companion/Agent 的原子 release manifest 及上一稳定版本回滚流程。
- **验收标准：**
  - 每级未通过时下一等级入口不可用；
  - 每次验收记录 root/dependency/PX4 SHA、配置/工具链 hash、原始日志、负责人和时间；
  - 回滚演练能恢复已知 artifact、参数快照与 graph profile；
  - 建立 transport、DDS discovery、Offboard reject、sensor loss 和 build failure 排障表。
- **依赖项：** BBF-GOV-001、002；firmware profile；安全 FSM。
- **预计工作量：L**
- **是否阻塞 production：是**

### BBF-GOV-004 — 缺少 CONTRIBUTING、SECURITY 和 CODEOWNERS

- **级别：P2**
- **分类：安全披露 / 贡献流程 / 所有权**
- **归属：根仓库 + GitHub 设置**
- **证据：**
  - 根目录不存在 `CONTRIBUTING.md`、`SECURITY.md`、`CODEOWNERS` 或 `.github/CODEOWNERS`。
  - `.github/` 不存在。
  - 主协调远端结果未提供等效 ruleset/owner 审批规则。
- **现象：** 没有漏洞私下报告渠道、支持版本/响应 SLA、代码风格/测试要求，也没有按控制、PX4、硬件、文档区域分配强制 reviewer。
- **影响：** 安全问题可能被公开披露或无人响应；高风险控制变更可能由非领域 owner 合并。
- **触发条件：** 外部贡献、漏洞报告、关键文件 PR、维护者离线。
- **检查命令：** `for f in CONTRIBUTING.md SECURITY.md CODEOWNERS .github/CODEOWNERS; do test -e "$f" || echo "MISSING $f"; done`
- **实际结果：** 四项均缺失。
- **预期结果：** 有明确贡献/安全策略和可执行 CODEOWNERS，关键区域至少一名具名 owner 审批。
- **建议修复：** 补三类文件；为 firmware、control authority、launch、manifest、evidence 分配 owner；与 branch ruleset 绑定。
- **验收标准：**
  - GitHub Security 页面显示有效策略与私下报告方式；
  - PR 模板要求风险、测试、硬件边界和回滚；
  - 关键路径 PR 自动请求且必须获得对应 owner approval；
  - 维护者轮换与 orphaned area 检查有记录。
- **依赖项：** 维护团队名单；BBF-GOV-002。
- **预计工作量：S**
- **是否阻塞 production：是**

### BBF-GOV-005 — handoff 被当作唯一巨大状态源，且已与远端默认分支漂移

- **级别：P2**
- **分类：状态管理 / 文档漂移**
- **归属：根仓库**
- **证据：**
  - `README.md:20-21` 声明完整当前状态、证据、验证与下一步“只维护”在 handoff。
  - `docs/handoff.md` 共 289 行，混合仓库状态、硬件清单、参数、topic、构建、路线、安全边界和删除历史。
  - `docs/handoff.md:3,27,287-289` 更新时间为 2026-07-25，记录 `master@16a0d8a`。
  - 当前本地 HEAD 为 `3ce2809`；主协调远端只读核验默认分支为 `master@62995b4e`。
- **现象：** “单一巨大状态文件”同时承担易变事实、历史事件、权威决策和任务计划；当前已经无法表示远端默认分支最新事实。
- **影响：** 新窗口可能以旧 base/设备状态/历史参数开始工作；更新一个章节容易遗漏相关章节，难以 review 和自动检测过期。
- **触发条件：** 默认分支推进、硬件/参数改变、阶段切换或多人并行更新。
- **检查命令：**
  - `wc -l docs/handoff.md`
  - `git rev-parse HEAD`
  - `git log --oneline --decorate -12`
  - `gh api repos/BoomBoomFly/BoomBoomFly`
- **实际结果：** handoff 为 289 行，记录的 master SHA 落后于远端只读事实。
- **预期结果：** handoff 只做短期入口；稳定事实分别由 ADR、inventory、runbook、status receipt 和 roadmap 管理，并以生成索引聚合。
- **建议修复：** 拆分 current status receipt、hardware inventory、operations、roadmap、historical log；给每份文件 schema/version/owner/updated_at/source SHA，handoff 只链接并标明 freshness。
- **验收标准：**
  - current status 由脚本从 Git/manifest/证据元数据生成；
  - 文档记录的 root/default/dependency SHA 与当前核验一致；
  - 历史参数和当前参数视觉上、机器上均不可混淆；
  - CI 在过期时间或 SHA 不一致时失败。
- **依赖项：** BBF-GOV-006、010。
- **预计工作量：M**
- **是否阻塞 production：否**

### BBF-GOV-006 — evidence 缺少统一、不可变、机器可验证的证据包规范

- **级别：P2**
- **分类：证据治理 / 可追溯性**
- **归属：根仓库**
- **证据：**
  - `docs/evidence/OFFBOARD_PX4_MSGS_COMPAT_20260724.md:1-60` 先记录失败，随后在同一文件追加修复、发布和第二天硬件 follow-up。
  - 同文件 `:3-10` 有日期和两个依赖 SHA，但缺统一 root HEAD、环境/toolchain、命令退出码、artifact hash、验收者字段。
  - `docs/evidence/PX4_PARAMS_20260724T203458+0800.json:1-18` 有 capture time、transport 和计数，但缺 root/PX4 binary hash、采集工具版本/命令、证据文件 hash 和签字。
  - `docs/handoff.md:99-101` 正确声明 JSON 已过期，但 JSON 本身没有 `historical/superseded_by` 元数据。
- **现象：** 文件名带日期，但没有统一 schema、状态、来源链、不可变原始日志和 supersession 机制；单一 Markdown 不断追加不同阶段结论。
- **影响：** 难以自动判断证据属于哪个 commit/profile、是否被后续结果取代，以及 release artifact 是否来自同一次验证。
- **触发条件：** 新 build/SITL/bench/实机记录、参数重采、历史结论被修复。
- **检查命令：**
  - `find docs/evidence -maxdepth 2 -type f -print`
  - `nl -ba docs/evidence/OFFBOARD_PX4_MSGS_COMPAT_20260724.md`
  - `nl -ba docs/evidence/PX4_PARAMS_20260724T203458+0800.json | sed -n '1,18p'`
- **实际结果：** 两个 evidence 文件格式不同，关键 provenance 字段不齐，历史/当前关系依赖 handoff 解释。
- **预期结果：** 每次验证生成独立、不可修改的 evidence bundle 和机器可读 receipt；后续修复创建新 bundle，通过 `supersedes` 关联。
- **建议修复：** 定义 JSON/YAML evidence schema，固定 capture id、scope、profile、root/lock/dependency/PX4/toolchain SHA、命令/exit、artifact SHA-256、raw log、result、limitations、approver。
- **验收标准：**
  - schema 校验纳入 CI；
  - 修改已发布 evidence 会触发完整性失败；
  - 每条验收结论可追溯到命令、退出码和原始输出；
  - historical/superseded/current 状态可机器查询，旧参数不能被 production 消费。
- **依赖项：** BBF-GOV-002、003。
- **预计工作量：M**
- **是否阻塞 production：是（须在四级验收前完成）**

### BBF-GOV-007 — public 仓库暴露个人路径、硬件序列号与部署拓扑

- **级别：P2**
- **分类：信息披露 / 隐私**
- **归属：根仓库文档与 evidence**
- **证据：**
  - 主协调远端结果：仓库为 public。
  - `README.md:8,15`：公开本机绝对路径和 PX4 UART/baud。
  - `docs/handoff.md:118-125`：公开主机型号、用户组、UART、D435/USB camera 序列号、VID:PID 和设备缺失情况。
  - `docs/evidence/OFFBOARD_PX4_MSGS_COMPAT_20260724.md:53,166-179`：包含 `/home/c`、串口、用户权限与 Agent 命令。
  - `src/offboard_cpp/package.xml:8`、`src/vision_to_dds/package.xml:7`：公开个人邮箱。
  - 精确 token/private-key 特征扫描未发现真实匹配；第一次宽松 `ghr_` 特征命中 librealsense 函数名，经严格 token 格式复核为误报。
- **现象：** 未发现 token、密码或私钥，但公开资料足以识别具体设备和主机部署；维护者邮箱和硬件 serial 也被永久写入历史。
- **影响：** 增加设备跟踪、定向攻击、社会工程和环境指纹风险。
- **触发条件：** public clone、fork、搜索引擎索引或 evidence 再分发。
- **检查命令：**
  - `grep -RInE '/home/...|serial ...|/dev/tty...|VID:PID' README.md docs Scripts/README.md`
  - `git grep -nEI 'github_pat_|ghp_|AKIA|xox[baprs]-|BEGIN .* PRIVATE KEY'`
- **实际结果：** 找到个人/设备标识；严格凭据特征无真实命中。
- **预期结果：** public 文档只使用占位符或匿名设备 ID；敏感原始 evidence 存放在受控位置并保留脱敏摘要。
- **建议修复：** 建立 data classification/redaction policy；旋转或删除凭据不是本轮所需，因为未发现凭据；对 serial、用户名、绝对路径、内网/端口拓扑脱敏。
- **验收标准：**
  - public tree 不含真实硬件 serial、个人 home path 或不必要的用户/设备权限信息；
  - 个人联系信息经明确同意或改用组织安全邮箱；
  - secret + PII/device-ID scan 成为 required check；
  - 私有原始证据和公开摘要的访问/保留策略明确。
- **依赖项：** 安全联系人；evidence storage 决策。
- **预计工作量：S**
- **是否阻塞 production：否，但阻塞公开 evidence 发布**

### BBF-GOV-008 — 缺少架构图、数据流图、节点图与部署拓扑

- **级别：P2**
- **分类：架构文档**
- **归属：根仓库**
- **证据：**
  - `docs/` 中只有 handoff、矩阵、一个 ADR 和两个 evidence 文件。
  - 未找到 Mermaid/Graphviz/PlantUML 或 PNG/SVG/drawio 架构资源。
  - ADR 的 ASCII 链路只描述 `ROS 2 ↔ Agent ↔ PX4`，未表达节点、topic、时钟、TF、设备、故障边界和部署主机。
- **现象：** 控制矩阵能回答“谁允许写”，但不能直观看出完整数据流、部署边界和故障传播。
- **影响：** 新维护者容易混淆 PX4/ROS 时间域、feedback/command、sensor/vision、single/multi-agent 和硬件串口 ownership。
- **触发条件：** 新节点、firmware profile、多机、感知链或故障分析。
- **检查命令：**
  - `find docs -maxdepth 3 -type f`
  - `grep -RInE 'mermaid|digraph|sequenceDiagram|flowchart|架构图|数据流图|部署拓扑' README.md docs`
- **实际结果：** 没有图形化架构资产。
- **预期结果：** 版本化图至少覆盖 component/deployment、node/topic/QoS、control authority、TF/frame、time domains 和 safety/fault transitions。
- **建议修复：** 使用文本源格式维护小型图集，并从同一 topic/profile inventory 生成关键关系，避免图与代码漂移。
- **验收标准：**
  - 图上每个 writer/consumer 与代码和控制矩阵一致；
  - 区分 Jetson、PX4、Agent、传感器和 network/domain 边界；
  - CI 渲染/语法检查并验证 topic inventory；
  - 架构变更 PR 必须同步 ADR/图。
- **依赖项：** 统一 profile/topic inventory。
- **预计工作量：M**
- **是否阻塞 production：否**

### BBF-GOV-009 — 恢复说明含非权威 clone URL，且保留空占位与过期历史入口

- **级别：P2**
- **分类：过期文档 / 占位脚本 / 操作误导**
- **归属：根仓库**
- **证据：**
  - `Scripts/README.md:31-35` 使用 `https://github.com/wanone111/BoomBoomFly.git`，当前确认的 canonical origin 是 `https://github.com/BoomBoomFly/BoomBoomFly.git`；旧 URL 是否重定向本轮未联网验证。
  - `Scripts/installation/car_install.sh` 与 `Scripts/simulation/uav_sim.sh` 均为 0 bytes、不可执行。
  - `Scripts/README.md:148-168` 把空文件作为未来入口。
  - `Scripts/README.md:126-134` 和 `.gitignore:30-36` 继续保留旧 M1/MAVROS patch 例外，而 handoff 已声明相关补丁被删除。
- **现象：** 一份运维说明同时包含当前 DDS 恢复、空占位和已退出基线的历史脚本；canonical clone 命令不一致。
- **影响：** 新环境可能 clone 非权威 fork/重定向地址，或误把空/历史脚本当作受支持入口。
- **触发条件：** 从空白环境按 Scripts README 操作、搜索“simulation/install”入口。
- **检查命令：**
  - `git remote -v`
  - `nl -ba Scripts/README.md`
  - `stat -c '%A %n %s bytes' Scripts/installation/car_install.sh Scripts/simulation/uav_sim.sh Scripts/build/m1_build.sh`
  - `nl -ba .gitignore`
- **实际结果：** clone URL 与 canonical origin 不同；两个占位脚本 0 bytes；历史例外仍存在。
- **预期结果：** 文档只展示 canonical source；未实现入口明确不可执行并从主操作路径隔离；历史工具有归档标签和退出日期。
- **建议修复：** 更正 canonical URL；用 roadmap issue 代替空脚本；把历史 M1 路径移入明确 archive/unsupported 区或从操作索引移除。
- **验收标准：**
  - 空白恢复文档引用当前 canonical repository/default branch；
  - 所有展示为命令的脚本存在、可执行、`--help` 有安全范围和 dry-run；
  - CI 检查文档命令路径与 executable bit；
  - unsupported 历史入口不能被 production profile 引用。
- **依赖项：** BBF-GOV-010；维护者确认历史保留策略。
- **预计工作量：S**
- **是否阻塞 production：否**

### BBF-GOV-010 — 项目无 issue/milestone、完成定义或可执行阶段治理

- **级别：P2**
- **分类：项目治理 / 任务追踪**
- **归属：GitHub 设置 + 根仓库**
- **证据：**
  - 主协调只读 API：`has_issues=false`、milestones=`[]`。
  - handoff 使用 `P0-03`、`P0-05`、`P1-03`、`P1-04`、`P1-09` 等任务编号，但仓库中没有对应机器可查询 register、owner、deadline 或状态定义。
  - wiki/projects 启用，但本轮没有受管、版本化的治理内容证据。
- **现象：** 风险编号存在于文档文字中，却没有唯一任务记录、依赖图、负责人、里程碑和 Definition of Done。
- **影响：** 高优先级依赖可能漏做、重复做或错误并行；“完成”可能只代表文档更新而非测试和证据通过。
- **触发条件：** 多代理/多人并行、阶段推进、P0/P1 关闭、release 决策。
- **检查命令：**
  - `grep -RInE 'P[0-3]-[0-9]+' README.md docs Scripts/README.md`
  - `gh api repos/BoomBoomFly/BoomBoomFly`
  - `gh api repos/BoomBoomFly/BoomBoomFly/milestones`
- **实际结果：** Issues 关闭、无 milestone；任务 ID 只存在于文档。
- **预期结果：** 每个发现有唯一 issue/本地 register、owner、依赖、验收证据和完成状态；里程碑对应路线阶段。
- **建议修复：** 启用 Issues 或建立仓库内机器可读 tracker；定义 P0-P3 triage、DoR/DoD、风险接受权限和 milestone gate。
- **验收标准：**
  - 所有 production blocker 可查询 owner、状态、依赖和验收链接；
  - P0/P1 未满足验收标准不能关闭；
  - milestone 自动汇总阻塞关系且与 roadmap 一致；
  - 风险接受必须记录批准人、范围和失效日期。
- **依赖项：** 团队治理选择；BBF-GOV-004。
- **预计工作量：S**
- **是否阻塞 production：否**

### BBF-GOV-011 — 文档链接与命令缺少自动化持续验证

- **级别：P2**
- **分类：文档质量门**
- **归属：根仓库 / CI**
- **证据：**
  - 本轮手工检查 README、handoff、ADR、matrix 的列出相对目标均存在。
  - 本轮 `bash -n` 对四个 shell 文件通过，安装脚本 `--help` 正常。
  - 根仓库没有 Markdown link checker、spell/style checker、shellcheck workflow 或文档命令 smoke test。
  - 外部链接和 URL 重定向因本轮禁止联网而未验证。
- **现象：** 当前本地链接大体有效，但这种状态依赖人工检查；错误 canonical URL 已证明“文件存在”不足以保证操作正确。
- **影响：** 文件移动、分支/PR 链接变化、命令选项漂移或外部文档失效不会阻止合并。
- **触发条件：** 文档重构、脚本参数变更、外部上游版本变更。
- **检查命令：**
  - `grep -RInE '\]\([^)]+\)|<https?://' README.md docs Scripts/README.md`
  - 对列出的相对目标执行 `test -e`
  - `bash -n Scripts/**/*.sh`
- **实际结果：** 已检查的本地目标存在；脚本语法通过；无自动化质量门；外链未验证。
- **预期结果：** PR 中自动验证本地/锚点/批准外链、命令路径、shell syntax/style 和文档中的版本/SHA freshness。
- **建议修复：** 在无硬件 CI 中加入 Markdown link checker、文档 lint、shellcheck、示例命令 dry-run 和 canonical URL allowlist。
- **验收标准：**
  - broken relative/anchor link 阻止合并；
  - 文档引用不存在/不可执行脚本或未知参数时失败；
  - 外链采用缓存/允许失败策略但产生可追踪告警；
  - README/handoff 的版本与生成 inventory 不一致时失败。
- **依赖项：** BBF-GOV-002、005。
- **预计工作量：S**
- **是否阻塞 production：否**

## 4. Production 治理阻塞项

1. `BBF-GOV-001`：没有完整许可证与第三方合规链。
2. `BBF-GOV-002`：默认分支无保护、无 required checks。
3. `BBF-GOV-003`：没有 release、四级验收和回滚 runbook。
4. `BBF-GOV-004`：没有安全披露流程和关键区域强制 owner。
5. `BBF-GOV-006`：证据格式不能可靠绑定到 release/profile/commit。

这些治理阻塞不替代控制安全阻塞；任何一组未清零，production 都不应启用。

## 5. 建议治理顺序

1. 立即确定许可证、安全联系人、CODEOWNERS，并停止新增未脱敏 public evidence。
2. 建立无硬件 CI、required checks 和 default-branch ruleset。
3. 定义 evidence schema、release manifest、四级验收与回滚 runbook。
4. 把 handoff 拆为短入口加生成式 current-status receipt；历史内容进入不可变 evidence。
5. 启用 issue/机器可读 tracker 与 milestone/DoD，再将 P0/P1 路线映射到 owner 和依赖。
6. 补架构图、链接/文档 lint，清理占位和非 canonical 操作入口。

## 6. 未验证项

- 未联网，因此外部 Markdown URL、旧 `wanone111/BoomBoomFly` 是否重定向、GitHub wiki/projects 内容均未验证。
- GitHub 设置来自主协调的当日只读 API 结果，本 Agent 未独立调用 API。
- 未检查 GitHub 组织级安全策略、成员权限、webhook、Deploy Keys、Secrets、Environments 或 audit log；这些需要相应只读权限。
- token/private-key 扫描是模式匹配，不构成完整 secret history scan；未扫描 Git 历史中已删除内容。
- 未验证文档中历史硬件、参数和运行结论；它们仅按带日期 evidence 使用。
- 未运行构建/测试/SITL/台架/实机；当前“9/9 gtest”和 DDS session 均是历史声明。

## 7. 本报告实际执行的主要命令

```bash
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git rev-parse HEAD
git status --short
git log --oneline --decorate -12
git ls-files
find docs Scripts .github -maxdepth 3 -type f
wc -l <强制基线文件>
nl -ba <强制基线与项目 package.xml>
grep -RInE <文档、链接、架构、运维、凭据与设备标识模式>
git grep -nEI <token/private-key 特征>
stat -c '%A %n %s bytes' Scripts/**/*.sh
bash -n Scripts/installation/uav_px4_dds_install.sh \
  Scripts/installation/car_install.sh \
  Scripts/simulation/uav_sim.sh \
  Scripts/build/m1_build.sh
bash Scripts/installation/uav_px4_dds_install.sh --help
bash Scripts/installation/uav_px4_dds_install.sh \
  --verify-only --skip-package-check
```

`--verify-only` 实际返回 exit 1，并完整汇总 `planned=15 cloned=0 updated=0 verified=15 blockers=4`；四个 blocker 是既有 dirty 第三方 checkout，命令明确报告未修改文件或 Git refs。这与当前 README/handoff 的该项描述一致，不是代码缺陷，也没有被当作失败的工程能力。

## 8. 数量统计

| P0 | P1 | P2 | P3 | 合计 |
|---:|---:|---:|---:|---:|
| 0 | 3 | 8 | 0 | 11 |
