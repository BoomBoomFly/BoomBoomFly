# 命令与安全边界证据

本轮只执行静态检查、`/tmp` 纯软件构建入口及单元/host tests。没有执行 `ros2 launch`、`ros2 run`、PX4/SITL、MicroXRCEAgent、MAVROS、串口访问、RealSense/RPLIDAR、`/fmu/in/*` 发布、arm/takeoff/land、参数写入、安装、push/merge/rebase/reset/clean。

| 类别/命令 | 结果 | 边界与证据 |
|---|---:|---|
| 基线全文读取 | PASS | 完整读取指定 current_audit 八份文档后才行动 |
| package boundary（隔离前） | exit 2 | expected `src/serial_driver_ros`，found nested serial；H1 未到 colcon |
| `Scripts/test/test_dds_only.sh --output-root /tmp/boomboomfly_wave4a_h1_build_20260727T231500` | FAILED prerequisite | output 仅在 `/tmp`；无 build/install artifact |
| package boundary（`COLCON_IGNORE` 后） | PASS | 75 packages；仅证明 serial 不再被 DDS-only discovery 发现 |
| package boundary Python fixtures | PASS 9/9 | pure software |
| Offboard runtime gate g++ + binary | PASS | transport-neutral；不是 ROS node/PX4 |
| Offboard Python contracts | PASS 12/12 | test-only oracle |
| root Python static/fixture suite | PASS 152/152 | 不驱动 live node |
| STM32 parser ASan/UBSan compile | PASS | host-only，无 HAL/UART |
| STM32 parser ASan/UBSan binary | FAIL exit 134 | `test_serial_parser.c:105` length assertion；不能记作 sanitizer clean pass |
| launch guard fixtures | PASS 11/11 | 静态测试，不构成 H3 |
| final `git diff --check` | PASS | 无 tracked diff whitespace error；untracked audit reports/communication 仍存在 |

## 最终工作树披露

root 仍记录 deleted `src/serial_driver_ros` gitlink、untracked `src/communication/` 与本 audit directory；communication 本身有三项 deleted old `Serial_ROS2` files 和 untracked nested serial。唯一归因于本 Wave 的源侧改动为 nested serial `COLCON_IGNORE`；其余 dirty 状态遵循 current_audit 基线，未清理、reset、stage 或覆盖。

所有生成的纯软件工件位于 `/tmp`；构建证据目录为 `/tmp/boomboomfly_wave4a_h1_build_20260727T231500`。没有硬件访问或正式 SITL 的命令证据，因此：

```text
HARDWARE ACCESSED: NO
FORMAL SITL RUN: NO
PROPELLERS INSTALLED: NOT VERIFIED
```
