# Scripts

本目录只保留当前实机工作区需要的源码恢复、构建和 evidence 检查入口。
所有命令均从仓库根目录执行。

```bash
cd "$(git rev-parse --show-toplevel)"
```

## 目录

```text
Scripts/
├── build/
│   └── build_dds_only.sh
├── evidence/
│   ├── validate_evidence.py
│   ├── validate_index.py
│   └── validate_manifest.py
└── installation/
    ├── uav_px4_dds_install.sh
    ├── verify_environment.py
    └── verify_workspace_receipts.py
```

## 恢复源码

`installation/uav_px4_dds_install.sh` 根据根目录
`workspace.lock.repos` 将功能包恢复到 `src/`。

恢复 active profile 和 RealSense 依赖：

```bash
bash Scripts/installation/uav_px4_dds_install.sh \
  --with-optional perception \
  --update \
  --require-colcon
```

只检查已经存在的 checkout：

```bash
bash Scripts/installation/uav_px4_dds_install.sh \
  --with-optional perception \
  --verify-only \
  --require-colcon
```

脚本不会覆盖 dirty checkout，也不会启动 DDS Agent、ROS 2 节点或飞控。
`src/communication` 同样由该脚本从 `main` 拉取。

## 构建

`build/build_dds_only.sh` 根据
`config/profiles/dds_only_packages.yaml` 选择 DDS 主链功能包，并将 colcon
输出放在 `/tmp`。

```bash
bash Scripts/build/build_dds_only.sh --help
bash Scripts/build/build_dds_only.sh
```

构建入口会先执行根仓通信/集成门禁，再对 `px4_msgs`、`offboard_cpp`、
`vision_to_dds` 和 `mission_bridge` 执行权威 `colcon build`，并测试三个
项目包。`px4_msgs` 是精确 SHA 锁定的接口依赖，仅构建；其 ROS Foxy
生成代码 lint 不属于项目门禁。

## Evidence

以下脚本只检查记录格式，不访问飞控和相机：

```bash
python3 Scripts/evidence/validate_evidence.py --help
python3 Scripts/evidence/validate_index.py
python3 Scripts/evidence/validate_manifest.py --help
```

格式定义见
[`docs/evidence/SCHEMA.md`](../docs/evidence/SCHEMA.md)。
