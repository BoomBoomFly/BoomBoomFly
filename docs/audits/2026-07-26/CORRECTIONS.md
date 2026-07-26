# 2026-07-26 Audit Corrections

本文只记录 2026-07-26 日期化审计中的已知引用错误。原审计正文、原始 evidence、
receipts、schemas 和历史参数快照保持不变，继续作为不可变历史记录。

## 1. ADR 路径

原报告
[`05_PERCEPTION_AND_INTEGRATION.md`](05_PERCEPTION_AND_INTEGRATION.md)
在第 28、104 行引用：

```text
docs/adr/0001-dds-only-control-path.md
```

该路径在当前 tree 不存在。正确的 Accepted ADR 是：

[`docs/adr/0001-dds-only-control-authority.md`](../../adr/0001-dds-only-control-authority.md)

本勘误修正引用目标，不改变原报告对 DDS-only、安全隔离或感知风险的历史结论。

## 2. 参数快照路径

同一原报告在第 27、103 行引用：

```text
docs/evidence/px4_params_full_20260724T171437+0800.json
```

该路径在当前 tree 不存在，不能作为可解析 artifact 使用。当前 tree 实际保留的
2026-07-24 历史参数快照是：

[`docs/evidence/PX4_PARAMS_20260724T203458+0800.json`](../../evidence/PX4_PARAMS_20260724T203458+0800.json)

两个文件名的采集时间不同，因此本勘误不声称实际文件与原报告所指快照逐字等价。
实际保留文件只能标记为 `HISTORICAL_EVIDENCE`，不能代表当前 PX4 参数，也不能
满足当前 SITL、台架、刷写或 production 验收门。

## 3. 保留策略

- 不修改 [`05_PERCEPTION_AND_INTEGRATION.md`](05_PERCEPTION_AND_INTEGRATION.md)
  的历史正文。
- 不创建缺失路径的占位文件或伪造快照。
- 后续审查应引用本勘误和当前真实文件；若获得新的参数快照，应创建新的 dated
  evidence，并通过 evidence 索引与 supersession 机制登记。
