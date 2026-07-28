# Scripts

本目录只保留当前可审查、可测试的构建、evidence、依赖恢复和静态验证入口。
命令应从动态解析出的仓库根目录运行：

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"
```

## 目录结构

```text
Scripts/
├── README.md
├── build/
│   └── build_dds_only.sh
├── evidence/
│   ├── validate_evidence.py
│   ├── validate_index.py
│   └── validate_manifest.py
├── installation/
│   ├── uav_px4_dds_install.sh
│   ├── verify_environment.py
│   └── verify_workspace_receipts.py
└── test/
    ├── launch_guard/
    │   └── check_launch_safety.py
    ├── test_dds_only.sh
    └── verify_package_boundary.py
```

## DDS-only 构建

[`build/build_dds_only.sh`](build/build_dds_only.sh) 按
[`config/profiles/dds_only_packages.yaml`](../config/profiles/dds_only_packages.yaml)
中的精确 allowlist 构建，并要求所有 colcon 输出位于 `/tmp`。

```bash
bash Scripts/build/build_dds_only.sh --help
bash Scripts/build/build_dds_only.sh
```

构建成功不代表获准启动节点、SITL、硬件链或 production。

## Evidence 验证

`evidence/` 中的验证器离线检查 evidence、索引、release manifest 和 rollback
manifest；它们不执行 manifest 中记录的命令，也不访问硬件。

```bash
python3 Scripts/evidence/validate_evidence.py --help
python3 Scripts/evidence/validate_index.py
python3 Scripts/evidence/validate_manifest.py --help
```

权威格式和生命周期见
[`docs/evidence/SCHEMA.md`](../docs/evidence/SCHEMA.md)，当前登记项见
[`docs/evidence/index.yaml`](../docs/evidence/index.yaml)。

## 依赖恢复与环境检查

克隆仓库的统一入口为：

```bash
git clone https://github.com/BoomBoomFly/BoomBoomFly.git
cd BoomBoomFly
```

[`installation/uav_px4_dds_install.sh`](installation/uav_px4_dds_install.sh)
默认读取 `workspace.lock.repos`，只管理源码 checkout；它不安装 ROS、系统包、
udev 规则或 firmware，也不启动 Agent 或 ROS 节点。先查看帮助；对既有工作区
优先使用只读审计：

```bash
bash Scripts/installation/uav_px4_dds_install.sh --help
bash Scripts/installation/uav_px4_dds_install.sh \
  --verify-only \
  --skip-package-check
```

脚本会拒绝覆盖 dirty checkout、origin 不匹配和任何非精确 ref。
默认只选择 active exact-SHA profile；archive 和 optional sources 必须通过
`--with-archive` 或 `--with-optional perception|navigation` 显式加入。自定义
`--manifest` 同样必须只包含安全 `src/` 路径和精确 SHA；原 moving
`workspace.repos` 入口已退役。完整 profile 与安全语义见
[`docs/dependencies/SOURCE_PROFILES.md`](../docs/dependencies/SOURCE_PROFILES.md)。
`verify_environment.py` 与 `verify_workspace_receipts.py` 提供相应的离线环境和
dependency receipt 检查。

## 测试

[`test/test_dds_only.sh`](test/test_dds_only.sh) 在 `/tmp` 中构建并测试 DDS-only
package allowlist。`verify_package_boundary.py` 与
`launch_guard/check_launch_safety.py` 分别检查包边界和 launch 安全边界。

```bash
bash Scripts/test/test_dds_only.sh --help
bash Scripts/test/test_dds_only.sh
python3 -m unittest discover -s test -p 'test_*.py'
```

## SITL

当前不存在获准执行的项目级 SITL orchestration，SITL 运行状态为 `BLOCKED`。
canonical 规范、场景和离线测试入口为：

- [`docs/runbooks/SITL_ACCEPTANCE.md`](../docs/runbooks/SITL_ACCEPTANCE.md)
- [`docs/runbooks/SITL_SCENARIO_CATALOG.md`](../docs/runbooks/SITL_SCENARIO_CATALOG.md)
- [`docs/verification/`](../docs/verification/)
- [`tools/sitl_acceptance/`](../tools/sitl_acceptance/)
- [`test/sitl_acceptance/`](../test/sitl_acceptance/)

场景 schema/parser 的离线测试不能作为 PX4 SITL evidence；不得手工拼接启动命令
后声称 `SITL_VERIFIED`。
