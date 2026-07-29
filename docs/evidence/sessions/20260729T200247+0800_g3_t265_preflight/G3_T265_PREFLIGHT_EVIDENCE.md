# G3 T265 视觉/EKF 拆桨预检证据

Session：`20260729T200247+0800_g3_t265_preflight`

日期：2026-07-29（Asia/Shanghai）

范围：用户明确批准 G3 拆桨视觉/EKF 阶段，但没有授权 PX4 参数写入。全程未启动 Agent、
Offboard 或 mission bridge，未发布任何 `/fmu/in/*`，未发送 VehicleCommand，未 Arm、未启动
电机。由于工作区没有实测 `t265_pose_frame -> base_link` 外参，生产视觉 writer 和 EKF 融合均
保持 fail-closed。

## 设备与锁定软件

- T265：`952322110550`，固件 `0.2.0.951`，USB 3.1。
- T265 兼容运行库：`/usr/local/lib/librealsense2.so.2.50`。
- `realsense-ros`：精确锁定 `8abb4657c0add15f87b0edbfb67eaba2c1c2c439`（4.0.4）。
- `vision_opencv/cv_bridge`：精确锁定
  `72152d9d1d8edcfcafd707a1d0103810db8613ba`。
- `vision_to_dds`：`470cf59cf8fbcddd17b12e9d31f084e87f5f2fac`，clean。

现场 `realsense-ros` checkout 有 98 个既有 mode-only 差异和一个未跟踪 launch 文件。没有在该
checkout 上构建或修改；使用 `git archive <exact SHA>` 提取到 `/tmp`，避免把 dirty 内容带入
验证。

## 隔离构建与测试

第一次隔离构建在 `realsense2_camera` 配置阶段因当前 underlay 没有 `cv_bridge` 失败。加入
同样精确锁定的 clean `cv_bridge` 后重试：

```text
Summary: 3 packages finished [1min 41s]
cv_bridge                    PASS
realsense2_camera_msgs       PASS
realsense2_camera            PASS
```

生成的驱动库链接 `librealsense2.so.2.50`。相机库和节点 SHA-256 分别为：

```text
6796d4c0e6fb4fd46bc055db3c905ba5d983931ec5c2ec607f2f6530be04e82e
847f9cd9eeb29ba512188a0b16f3ed90149112f6823c7de4722fd1481fcf9186
```

测试结果不能概括成全 PASS：

- `cv_bridge`：4/4 CTest PASS，其中 gtest 9/9，Python tests PASS。
- `realsense2_camera_msgs`：29/29 CTest PASS。
- 汇总 XML：330 tests，0 error，0 failure。
- `colcon test` 在进入相机包前因 colcon 期望工作区内
  `install/librealsense2/share/librealsense2/package.sh` 返回 1；实际编译和运行均链接系统
  `/usr/local` 2.50。
- 直接运行相机包配置的 8 个 CTest 时仅 `xmllint` PASS，其余 7 个是上游 4.0.4 的 copyright、
  cppcheck 和格式 lint 失败。没有删除或跳过这些失败。

## 真实 T265 数据

### Librealsense 只读流

保存的 60 秒采样结果：

```text
elapsed=60.029499 s
samples=11876
rate=199.557001 Hz
max_gap=5.104736 ms
timestamp regressions=0
frame regressions=0
non-finite values=0
invalid quaternion samples=0
quaternion norm=[1.0, 1.0]
tracker confidence counts=[1, 0, 11875, 0]
```

启动瞬间一个样本置信度为 0，其余为 2（中等）。这证明流连续性，不等于外参正确或 EKF 已
接受。

### ROS `nav_msgs/Odometry`

锁定驱动在 `ROS_DOMAIN_ID=231`、固定 T265 序列号且仅启用 pose 的 60 秒结果：

```text
topic=/t265/pose/sample
elapsed=60.010743 s
samples=11975
rate=199.547603 Hz
max timestamp gap=5.029376 ms
timestamp regressions=0
non-finite values=0
invalid quaternion samples=0
frame_id: odom_frame (11975/11975)
child_frame_id: t265_pose_frame (11975/11975)
pose covariance[0]: 0.1 (11975/11975)
status=PASS
```

因此锁定驱动的真实话题和 `odom_frame -> t265_pose_frame` 契约与
`vision_to_dds` 一致。

### 断流与恢复

只启动健康适配器和相机驱动，受控停止并恢复 ROS 相机流：

```text
quality:      66 -> 0 -> 66
source_epoch:  2 -> 3
production minimum_quality: 50
input writers: all 0
status against production contract: PASS
```

适配器的整数表达式将 tracker confidence 2 映射为 66，但源码注释写成 67；生产阈值为 50，
因此不影响本次门禁判定，注释漂移仍须后续修正。一次由 `timeout` 进程组信号触发的驱动停止
在完成 Stop/Close 后以 `-11` 退出；另外两次停止干净。没有 core dump，退出稳定性作为剩余
风险保留。两个后续 PID 复现实验因 wrapper/后台 SIGINT 语义错误而作废，日志保留但不用于
结论。

## 外参与参数门

全工作区按 `*t265*.yaml`、`*extrinsic*.yaml`、`*extrinsics*.yaml` 搜索，没有任何实测 YAML；
仓库只有包含 `REQUIRED_*` 占位符的模板。隔离 Domain 231 生产启动负向测试退出码为 1：

```text
RuntimeError: production launch requires
t265_to_base_link_extrinsics_file:=/absolute/measured.yaml
```

当前参数快照 `docs/2026.7.29.params` SHA-256 为
`2c3b9c6ea6efa4e5fdbb25fa0edc3cd0261f883408b7ae10729ca8c52e1105b0`：

```text
EKF2_EV_CTRL=3
EKF2_EV_DELAY=0
EKF2_EV_NOISE_MD=0
EKF2_HGT_REF=3
```

PX4 v1.16.2 本地源码定义 `EKF2_EV_CTRL` bit 0 为水平位置、bit 1 为垂直位置、bit 2 为 3D
速度、bit 3 为 yaw，因此现值 3 已是位置分量，不含速度或 yaw。本次没有写参数。

## 最终释放与结论

最终没有 Agent、RealSense、vision、offboard 或 mission bridge 进程，DDS 串口无 owner。
Domain 0 连续 10 秒、20 次图采样中四个关键 `/fmu/in/*` publisher 最大值均为 0。本次 boot
的 Jetson UART/DMA 错误匹配数为 0。

G3 **BLOCKED / 预检部分完成**。T265 原始流、ROS odometry frame/time/数值和健康适配器断流
恢复均取得真实证据；但没有实测 `t265_pose_frame -> base_link` 外参，故没有创建生产 writer，
没有启动 Agent，也没有取得任何 estimator fusion/innovation/reset 证据。G4 未进入，G5 仍
禁止，整体继续 **NO-GO / 不允许装桨飞行**。
