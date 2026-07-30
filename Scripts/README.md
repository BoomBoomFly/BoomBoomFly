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

```

项目仓分别跟随 `offboard_cpp/DDS`、`vision_to_dds/master` 和
`communication/main`。更新只允许 fast-forward；实际 checkout 和提交记录在
`log/repository-versions.tsv`。
