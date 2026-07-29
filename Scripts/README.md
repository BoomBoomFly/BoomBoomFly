# Scripts

所有命令从仓库根目录执行。

## 工作区

```bash
# 恢复精确锁定的依赖
bash Scripts/installation/uav_px4_dds_install.sh \
  --with-optional perception --update --require-colcon

# 只校验现有 checkout
bash Scripts/installation/uav_px4_dds_install.sh \
  --with-optional perception --verify-only --require-colcon

```

## 构建与回放

```bash
bash Scripts/build/build_dds_only.sh
python3 Scripts/test/px4_interface_replay.py --self-test
ROS_DOMAIN_ID=231 python3 Scripts/test/px4_interface_replay.py --duration 65
```

回放脚本拒绝 Domain 0，不得加入生产 launch。

## 运行工具

- `runtime/px4_dds_agent_guard.py`：检查内存、串口、Domain 和 Agent SHA 后启动唯一 Agent。
- `runtime/px4_param_snapshot.py`：只读导出 PX4 参数快照。
- `runtime/px4_mavftp_get_ulog.py`：按需下载 PX4 ULog。
- `runtime/px4_log_inventory.py`：生成日志清单。

生产 Agent 先执行只检查：

```bash
ROS_DOMAIN_ID=0 python3 Scripts/runtime/px4_dds_agent_guard.py \
  --agent /absolute/path/to/MicroXRCEAgent \
  --agent-sha256 <64-hex-sha256> \
  --serial-dev /dev/ttyTHS0 \
  --baudrate 921600 \
  --check-only
```

去掉 `--check-only` 才会启动 Agent。任一检查失败都不得绕过。
