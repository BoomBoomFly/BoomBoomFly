# Offboard 最短路径

目标是先跑通任务 3：0.5 m 垂直起飞、悬停 3 s、垂直下降、PX4 Land、落地确认、
Disarm。暂不加入水平航线、D435 或精确降落。

## 0. 前置阻塞

当前锁定的 `offboard_cpp` 尚未完成 QGC 控制边界与生产垂直轨迹闭环。合并对应改动并
更新 `workspace.lock.repos` 前，以下流程只能用于开发和拆桨检查，不能装桨执行。

目标边界：

- RC、Kill、Offboard 模式和 Arm：QGC/PX4 负责；
- ROS 2：轨迹预流、任务状态机、Land 请求和落地后的 Disarm；
- ROS 2 不伪造 RC，不要求 owner/lease/epoch 才能进入轨迹预流。

## 1. 恢复和构建

```bash
bash Scripts/installation/uav_px4_dds_install.sh \
  --with-optional perception \
  --update \
  --require-colcon

bash Scripts/build/build_dds_only.sh
source install/setup.bash
```

## 2. 拆桨启动顺序

1. 确认螺旋桨已拆除，QGC 已连接。
2. 启动唯一的 DDS Agent。
3. 启动 T265 和 `vision_to_dds`。
4. 在 QGC 中确认 PX4 local position 有效、坐标方向正确且静止不漂移。
5. 启动 `offboard_cpp` 和垂直任务节点。
6. 确认轨迹 setpoint 已稳定预流至少 1 s。
7. 由 QGC 切入 Offboard，再由 QGC Arm。
8. 发送任务 3 START；观察状态机完整走到 Land、落地确认和 Disarm。

任何一步失败都应停止任务并回到安全状态，不自动重新进入 Offboard。

## 3. 验收

- 上升速度不超过 0.3 m/s；
- 目标高度 0.5 m；
- 悬停 3 s；
- 下降速度不超过 0.2 m/s；
- Land 已被 PX4 接受；
- `landed=true` 后才允许 Disarm；
- ACK 拒绝、超时或定位失效时不得继续下降状态机；
- 全程只有一个 `/fmu/in/*` writer。

通过拆桨流程不等于允许装桨。装桨前还必须完成
[安全清单](SAFETY_CHECKLIST.md)。
