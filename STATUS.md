# 当前状态

截至 2026-07-30，项目状态为 **NO-GO**：可以继续软件开发和拆桨验证，不能据此
直接装桨、Arm 或起飞。

| 门禁 | 状态 | 结论 |
| --- | --- | --- |
| G0 源码与构建 | PASS | 精确 SHA、构建和接口门禁已验证 |
| G1 隔离回放 | PASS | Domain 231 下的垂直任务与异常路径已验证 |
| G2 DDS/RC | PASS | 真实 RC、Agent 和 620 s 拆桨 soak 已验证 |
| G3 T265/EKF | PASS | 视觉位置融合、断流退出和恢复已有实机证据 |
| G4 失效闭环 | BLOCKED | 严格口径下 0/10 场景具备完整独立证据 |
| G5 首次装桨 | NOT AUTHORIZED | 仅在 G0–G4 全 PASS 后评审 |

## 当前硬阻塞

锁定的 `offboard_cpp` 仍以安全门和 PX4 消息转发为主，缺少可直接使用的生产级
起飞—悬停—下降状态机、着陆完成判定和完整 Land/Disarm 闭环。旧安全门还依赖
ROS 侧 RC/owner/lease/activation 等输入，不符合当前“RC 只在 QGC/PX4 配置”的边界。

因此当前仓库单独启动不会可靠地自行起飞，也不应通过放宽安全条件绕过该阻塞。

## 下一阶段

1. 在 `offboard_cpp` 完成 QGC/PX4 控制边界。
2. 实现任务 3：0.5 m、上升不超过 0.3 m/s、悬停 3 s、下降不超过
   0.2 m/s、Land、落地确认、Disarm。
3. 更新根仓 `workspace.lock.repos`，重新执行 G0/G1。
4. 按五类失效场景完成 G4 拆桨验证。
5. G0–G4 全 PASS 后再申请首次低高度装桨测试。

本阶段不引入 D435 精确降落；先完成 T265 下的普通垂直降落。

## 锁定版本

- `offboard_cpp`: `e24bb3facfcf4126ad7b3d216a768a040758e895`
- `vision_to_dds`: `470cf59cf8fbcddd17b12e9d31f084e87f5f2fac`
- `communication`: `e6d6126acd16050216e5f091e61d58a96ef3ed65`
- PX4 参数 SHA-256:
  `a9d100fb9d67e115df94c3005b511ddc0b09ec7645b1b995c7366474ba58667c`
