# CODEOWNERS Proposal

> **DRAFT ONLY — DO NOT ENABLE**
>
> 本文中的 `@CONTROL-MAINTAINER`、`@PX4-MAINTAINER`、
> `@PERCEPTION-MAINTAINER` 和 `@RELEASE-MAINTAINER` 全部是职责占位符，
> 不是已验证的 GitHub 用户或 team。当前不得把下列规则复制到
> `.github/CODEOWNERS`、`CODEOWNERS` 或 `docs/CODEOWNERS`。

## 当前状态

- CODEOWNERS enforcement：`BLOCKED`。
- `.github/CODEOWNERS`：不存在，且本轮不创建。
- owner 映射：`BLOCKED`；仓库没有可验证的真实 GitHub 用户/team 清单。
- branch protection / required approval：`BLOCKED`，不得由本文推定。

只有仓库维护者确认真实 owner、权限和替补关系，并通过测试 PR 验证匹配和自动
review request 后，才能创建有效 CODEOWNERS。

## 角色占位符

| 占位符 | 预期职责 |
|---|---|
| `@CONTROL-MAINTAINER` | 控制 writer、authority、状态机、topic contract 和安全门 |
| `@PX4-MAINTAINER` | PX4 message、DDS firmware profile、target build 和 failsafe |
| `@PERCEPTION-MAINTAINER` | 坐标、时间、TF、视觉健康和 EKF2 输入契约 |
| `@RELEASE-MAINTAINER` | manifest、依赖、CI、evidence、release 和 rollback |

这些角色不证明任何真实账号存在。不得虚构用户名、team、邮箱或组织权限。

## 根仓库路径核对

下表只覆盖当前根仓库实际 tracked 的路径。`owner` 列仍是提议，不是 enforcement。

| 当前 tracked 路径 | 提议 owner |
|---|---|
| `*` | `@RELEASE-MAINTAINER` |
| `/workspace.lock.repos`、`/workspace.repos`、`/workspace.excluded_packages` | `@RELEASE-MAINTAINER`、`@PX4-MAINTAINER` |
| `/config/profiles/**` | `@RELEASE-MAINTAINER`、`@CONTROL-MAINTAINER`、`@PX4-MAINTAINER` |
| `/Scripts/build/**`、`/Scripts/installation/**` | `@RELEASE-MAINTAINER`、`@PX4-MAINTAINER` |
| `/Scripts/evidence/**` | `@RELEASE-MAINTAINER` |
| `/Scripts/test/**`、`/test/**` | `@RELEASE-MAINTAINER`、适用领域 owner |
| `/docs/adr/**` | 四个领域角色共同审查 |
| `/docs/CONTROL_AUTHORITY_MATRIX.md`、`/docs/architecture/**` | `@CONTROL-MAINTAINER`、`@PX4-MAINTAINER`、适用时 `@PERCEPTION-MAINTAINER` |
| `/docs/runbooks/**`、`/docs/verification/**` | `@CONTROL-MAINTAINER`、`@PX4-MAINTAINER`、`@RELEASE-MAINTAINER` |
| `/docs/evidence/**` | `@RELEASE-MAINTAINER`、证据结论对应的领域 owner |
| `/docs/governance/**`、`/CONTRIBUTING.md`、`/SECURITY.md` | `@RELEASE-MAINTAINER`、`@CONTROL-MAINTAINER` |

启用前必须把表格转换为经 GitHub CODEOWNERS 语法验证的规则，并用正向和负向
路径 fixture 检查 pattern 覆盖。本文不是可直接启用的配置。

## 外部 checkout 边界

`src/offboard_cpp/`、`src/vision_to_dds/`、`src/px4_msgs/` 和其他依赖目录由根
`.gitignore` 排除，内容不由根仓库追踪。根仓库 CODEOWNERS 不能为这些外部仓库的
内部文件提供可靠 review enforcement。

根仓库只治理它们在 manifest、lock、profile、receipt 和 evidence 中的引用。
依赖源码 owner 必须在各自 canonical repository 中单独配置；在此提议
`/src/offboard_cpp/**` 或 `/src/vision_to_dds/**` 会造成虚假的保护预期，因此不列入。

## PX4 firmware profile 路径

当前 tree 只有 `/config/profiles/**` 下的 DDS-only package/launch profile；不存在
`/profiles/px4-firmware/**`，也不存在已落地的 PX4 firmware profile 目录。

因此：

- 删除旧草案中不存在的 `/profiles/px4-firmware/**` 提议；
- 当前 `/config/profiles/**` 由 control、PX4 和 release 角色共同审查；
- 将来实际新增 firmware profile/patch 时，先冻结真实 tracked 路径，再在同一 PR
  更新本文、review policy、测试和最终 CODEOWNERS；
- 不为尚不存在的路径创建占位目录或空规则。

## 启用门

全部满足前，CODEOWNERS 保持 `BLOCKED`：

1. 维护者提供真实、存在且至少有仓库 read 权限的 GitHub 用户/team。
2. 每个高风险领域有主 owner 和可用替补；作者不能自批。
3. 占位符全部替换，且没有个人邮箱、虚构账号或无效 team。
4. 所有 pattern 与当前 tracked tree 一致；外部 checkout 在各自仓库治理。
5. 测试 PR 证明兜底、manifest、profile、control、runbook、evidence 和 governance
   路径会请求正确 reviewer。
6. 负向测试证明无关路径不会错误请求高风险 owner，新增高风险路径不会无 owner。
7. branch protection、required approvals 和管理员 bypass 规则由维护者单独评审。
8. [Review Policy](REVIEW_POLICY.md) 中的 required CI 尚未落地时，不得声称
   CODEOWNERS 已形成完整合并门。

启用动作本身必须由有权限的维护者执行；本文不授权修改远端设置。
