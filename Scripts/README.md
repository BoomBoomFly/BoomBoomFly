# Scripts

所有命令从仓库根目录执行。

## 工作区

```bash
# 快进三个项目仓，并恢复精确锁定的第三方依赖
bash Scripts/installation/uav_px4_dds_install.sh \
  --with-optional perception --update --require-colcon

# 只校验现有 checkout
bash Scripts/installation/uav_px4_dds_install.sh \
  --with-optional perception --verify-only --require-colcon

# WSL：恢复清单中全部可同步的 src 仓库（不复制任何未提交文件）
bash Scripts/installation/uav_px4_dds_install.sh \
  --with-current-src --update --require-colcon

```

项目仓分别跟随 `offboard_cpp/DDS`、`vision_to_dds/master` 和
`communication/main`。更新只允许 fast-forward；实际 checkout 和提交记录在
`log/repository-versions.tsv`。

`--with-current-src` 选择 active、archive、optional-perception 与
optional-navigation profile；quarantine 条目仍不会下载。项目仓按清单声明的分支更新，
第三方仓库按 `workspace.lock.repos` 中的精确 SHA 恢复。该命令不传输本机未提交修改、
未跟踪文件或构建产物。
