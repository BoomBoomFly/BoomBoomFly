# 历史证据说明

为缩短仓库恢复和审阅时间，当前清理分支删除了 `docs/evidence/sessions/` 中的大体积日志、
ULog、截图和重复报告，也移除了只服务于旧证据格式的一次性校验脚本。

删除不改写 Git 历史。完整原始证据可从清理前提交
[`0247d7e`](https://github.com/BoomBoomFly/BoomBoomFly/tree/0247d7e8717428890252422c821bd92e1dbaa3b5/docs/evidence)
恢复。

保留结论：

- G0–G3：PASS；
- G4：严格口径下尚无完整场景通过，仍为 BLOCKED；
- G5：未授权。

当前仓库只保留仍被环境校验使用的环境快照和 schema。新的实机测试应优先把简短结论写入
`STATUS.md`，大体积原始日志保存到外部归档，不再提交到主仓库。
