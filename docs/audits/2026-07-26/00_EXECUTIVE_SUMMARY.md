# BoomBoomFly 工程审查执行摘要

> 后续变更（2026-07-26T16:46:43+08:00）：归档 `src/px4_bringup` 已对齐上游
> `DDS@0fbdcbf6`，并加入维护清单和精确 lock，但继续排除出 DDS-only 构建与运行。
> 本报告中的 15/16 项统计保留为审查执行时的历史结果；更新后的只读结果为 exact
> `planned=16 verified=16 blockers=4`、moving
> `planned=17 verified=16 blockers=5`。

## 审查对象与基线

| 项目 | 值 |
|---|---|
| 仓库 | `/home/c/BoomBoomFly` |
| origin | `https://github.com/BoomBoomFly/BoomBoomFly.git` |
| 本地分支 | `agent/follow-latest-offboard` |
| 本地 HEAD | `3ce28094e14ed720987c5fc6d1172e377f09b1cc` |
| 审查时间 | 2026-07-26T15:53+08:00 ～ 2026-07-26T16:34:26+08:00 |
| 主机 | NVIDIA Orin Nano / aarch64；Ubuntu 20.04.6；kernel 5.10.104-tegra |
| 工具基线 | ROS 2 Foxy；Git 2.25.1；Python 3.8.10；colcon 可用 |
| 工作树基线 | 根仓库 `git status --short` 无输出 |
| 工作树结束状态 | 仅 `docs/audits/2026-07-26/` 的 11 份新报告为 untracked；tracked/source 无修改 |
| 远端只读状态 | public；默认 `master@62995b4e...`；master 未保护；0 Actions workflow；0 ruleset；Issues 关闭；无 milestone/release；license 未声明 |

仓库身份门已通过。本地分支/HEAD 与 GitHub 默认 `master` 是不同事实：本报告审查的是本地 `agent/follow-latest-offboard@3ce28094...`，不把远端默认分支状态冒充本地 checkout，也未执行 fetch/pull。

## 当前工程阶段

工程处于“**接口契约已部分修复、控制安全闭环和可发布验证体系尚未形成**”阶段：

- DDS-only 架构、单一 writer/owner 规则和 production 禁用决策已冻结在 ADR/控制权矩阵。
- PX4 v1.16.2 的 `vehicle_status_v1` topic 修复已进入锁定 Offboard checkout。
- 核心包可以构建，RC parser 的局部兼容性测试通过。
- 真实 PX4 DDS output session 只有 2026-07-25 的历史只读取证；本轮未动态复验。
- 运行时 graph guard、owner/lease、VehicleCommand ACK、统一 freshness/fault handling、视觉坐标/时间闭环、SITL/台架/回滚仍未完成。

因此当前不是 production candidate，也不是可进入拆桨台架控制验收的版本。

## 已完成或已验证的能力

1. 仓库 identity、分支和 HEAD 已确认。
2. `workspace.lock.repos` 的 15 个路径、origin 和 HEAD 均匹配；verify-only 完整遍历并因四个保留 dirty checkout 正确返回非零。
3. `px4_msgs@392e831c...`、Micro XRCE-DDS Agent `v2.4.2@57d08621...`、`offboard_cpp@cded3dc5...`、`vision_to_dds@0c3a0013...` 均与 lock 对齐。
4. 在 `/tmp/boomboomfly_audit_20260726_agent_b/` 隔离构建 `px4_msgs`、`offboard_cpp`、`vision_to_dds` 成功，3 packages finished，约 13 分 15 秒。
5. Offboard 2/2 CTest executable、9/9 gtest case 通过；覆盖 7 个 RC parser case 和 2 个 topic 源码契约 case。
6. 核心 Bash、Python launch/script、XML/YAML 静态语法通过。
7. ADR 明确 production 只允许 uXRCE-DDS，当前单机根 namespace，MAVROS 不属于批准路径。
8. `vision_to_dds` 默认 `enable_precland=false` 时不创建精降 publisher，这是正确的 fail-closed 默认。

需要同时保留的负向结果：`vision_to_dds` 3/6 lint executable 失败，展开为 305 tests 中 287 个 lint diagnostics；这不是构建失败，但说明核心组合不是 test-clean。

## 当前最主要的五个不足

1. **控制权和命令事务不安全。** 无 graph guard、owner/lease、ACK pending、fresh status 二次确认；启动/重连会立即发布控制流。
2. **RC 安全闭环不可成立。** PX4 firmware 未导出 `/fmu/out/rc_channels`，production 又无条件编译 mock override，且无 RC 时自动起飞路径可跳过检查。
3. **故障处理和数据有效性不闭合。** Odom/landed 未初始化、首帧逻辑错误，DDS/RC/odom/status/battery loss 和 landing 降级策略不一致。
4. **视觉输入在坐标和时间上未被证明。** ENU/NED/FLU/FRD、TF、sample/publish time、reset/quality/freshness 无数学与测试闭环。
5. **工程发布门缺失。** 默认包发现仍包含禁止组件；无 PX4 DDS SITL、required CI、branch protection、统一 evidence/release/rollback 和拆桨台架 runbook。

## 统一发现统计

六个分域报告共有 64 个原始发现；合并重复根因后，统一登记为：

| 等级 | 数量 | production 含义 |
|---|---:|---|
| P0 | 9 | 安全阻塞，必须全部关闭 |
| P1 | 15 | 集成/发布阻塞，必须按适用 profile 关闭 |
| P2 | 19 | 工程质量与治理，其中若干阻塞发布/台架证据 |
| P3 | 1 | 长期工具链一致性 |
| 合计 | 44 | 详见 `07_FINDINGS_REGISTER.md` |

## Production 建议

**不可以启用 production。**

当前同时存在错误控制权、非预期 mode/arm 请求、陈旧/未初始化反馈、RC mock 绕过和错误视觉注入的 P0 风险。production、拆桨台架控制和有限实机控制均应保持禁用。允许继续的范围是 offline static、隔离 build/test、锁定 PX4 firmware profile 的静态生成/SITL/FMUV3 build（不刷写），以及不连接真实 PX4 的单元/集成测试。

## 最短关键路径

1. 冻结可复现基线：DDS-only 包 allowlist、四个 dirty receipt、PX4 source/submodule/toolchain、evidence schema、required CI。
2. 构建 `rc_channels` PX4 v1.16.2 profile：静态生成 → PX4-source SITL payload → FMUv3 build/hash；不刷写。
3. 完成 Offboard 安全闭环：移除 production mock、ACK/freshness、PRESTREAM、owner/lease、graph guard、fault lattice。
4. 通过 PX4 DDS SITL 正常/故障矩阵；失败阻止合并。
5. 冻结视觉坐标/时间/设备 profile，再完成 EKF2/SITL 证据。
6. 所有 P0/P1 关闭后，编制并实际演练拆桨台架和回滚；最后另行申请有限实机授权。

## 本次实际运行的命令类别

### 仓库与依赖

```bash
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git rev-parse HEAD
git status --short
git log
git diff
git ls-files -s
git submodule status --recursive
git -C <managed-repo> rev-parse/status/remote/describe/diff
bash Scripts/installation/uav_px4_dds_install.sh --verify-only --skip-package-check
bash Scripts/installation/uav_px4_dds_install.sh \
  --manifest workspace.repos --allow-moving-refs --verify-only --skip-package-check
```

关键实际结果：

- exact lock：`planned=15 verified=15 blockers=4`，exit 1；
- moving manifest：`planned=16 verified=15 blockers=5`，第五项为缺失 `../communication`；
- `git submodule status --recursive` 因无 `.gitmodules` 映射的历史 gitlink 返回 128。

### 静态检查与构建测试

```bash
find / grep / sed / nl / awk / wc / file / stat
colcon list --base-paths src
colcon graph --base-paths src ...
bash -n <reviewed scripts>
PYTHONPYCACHEPREFIX=/tmp/... python3 -m compileall ...
python3 -c '<parse package.xml, manifests, YAML>'
colcon --log-base /tmp/... build --build-base /tmp/... --install-base /tmp/...
colcon --log-base /tmp/... test ...
colcon test-result ...
git diff --check
```

构建/测试实际结果：

- 核心 3 包隔离 build 成功；
- Offboard 9/9 gtest 通过；
- `vision_to_dds` 3/6 lint executable 失败。

`colcon list/graph` 虽用于只读发现，但该环境仍在工作区被 `.gitignore` 排除的 `log/` 下生成了 `list_*`、`graph_*` 和 `COLCON_IGNORE` 日志。未删除或覆盖这些产物；tracked/source 未因此改变。后续 build/test 全部隔离到 `/tmp`。

### GitHub 只读治理核验

```bash
gh auth status
gh api repos/BoomBoomFly/BoomBoomFly ...
gh api repos/BoomBoomFly/BoomBoomFly/branches ...
gh api repos/BoomBoomFly/BoomBoomFly/actions/workflows ...
gh api repos/BoomBoomFly/BoomBoomFly/rulesets ...
gh api repos/BoomBoomFly/BoomBoomFly/milestones?state=all ...
gh api repos/BoomBoomFly/BoomBoomFly/releases ...
```

仅执行 read-only API；未修改远端、issue、PR、分支、workflow 或仓库设置。

## 因环境或安全边界未验证

- 未 clone/fetch/pull/submodule update，未取得当前缺失的 PX4-Autopilot source/toolchain。
- 未构建 PX4 firmware、未静态生成自定义 DDS profile、未构建/验证 `.px4` artifact。
- 未启动 PX4 SITL、Micro XRCE-DDS Agent、MAVROS、Offboard、视觉、相机、雷达或任何 hardware launch。
- 未访问 `/dev/ttyTHS0`、`/dev/ttyACM*`、`/dev/ttyUSB*`。
- 未读取或写入当前 PX4 参数；2026-07-24 JSON 明确只作为调整前历史快照。
- 未 arm、未切换飞行模式、未发送 setpoint、VehicleCommand 或任何 `/fmu/in/*`。
- 未动态检查 ROS graph、publisher 唯一性、QoS 实际兼容、PX4 input 交付、ACK result、failsafe、EKF2 融合。
- 未执行拆桨台架、回滚演练或实机控制。
- 未运行完整第三方工作区测试、clang-tidy/cppcheck/shellcheck/sanitizer；没有安装缺失工具。

## 报告导航

- `01_REPOSITORY_AND_DEPENDENCIES.md`
- `02_BUILD_TEST_AND_CI.md`
- `03_PX4_DDS_OFFBOARD_CONTRACT.md`
- `04_SAFETY_AND_CONTROL_AUTHORITY.md`
- `05_PERCEPTION_AND_INTEGRATION.md`
- `06_DOCUMENTATION_AND_GOVERNANCE.md`
- `07_FINDINGS_REGISTER.md`
- `08_ROADMAP.md`
- `09_VALIDATION_MATRIX.md`
- `10_NEXT_CODEX_TASKS.md`
