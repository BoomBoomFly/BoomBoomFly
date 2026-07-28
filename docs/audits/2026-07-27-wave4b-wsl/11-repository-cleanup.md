# 2026-07-28 repository cleanup receipt

Scope: clean WSL candidate `/home/aa/px4_ws/BoomBoomFly-wave4b`; original dirty
checkout, nested source worktrees, PX4 source, dated audits, evidence, receipts,
and hardware state were not modified.

## Deleted

`docs/planning/NEXT_PARALLEL_TASKS.md` was deleted because it presented mixed
Wave 3A/Wave 3B snapshots as the canonical current scheduler. Its current
replacement is `07-open-findings.md`, which records the Wave 4B blockers and
dependency order.

Pre-delete SHA256:
`fd6290fbf6a98a3b71cf3332753766e161000336c227aa548cf07cccb8796cd5`.
The deleted content remains recoverable from Git at
`a7976a4ab397c8e85a278191770625d848c86c6d:docs/planning/NEXT_PARALLEL_TASKS.md`.

## Updated instead of deleted

- `docs/handoff.md` remains the stable navigation path required by README,
  contributing guidance, architecture links, and cleanup invariants. Its stale
  Wave 3B body was replaced with a short Wave 4B navigation and gate summary.
- `README.md` and `docs/planning/BACKLOG.md` now link to the Wave 4B open
  findings instead of the deleted scheduler.

## Retained

Dated audits, evidence, receipts, schemas, `BACKLOG.md`, `MILESTONES.md`,
`DEPENDENCY_GRAPH.md`, and safety runbooks were retained. They contain audit
trace, safety gates, task mappings, or dependency constraints and are not safe
delete candidates. Generated backup, reject, temporary, editor, and Python
bytecode files were not present in the tracked candidate.

No build, ROS process, SITL, device, FMU graph, parameter, firmware, or hardware
operation was used for this cleanup.

## Validation

- repository cleanup invariant tests: 3/3 PASS;
- active references to the deleted scheduler: 0;
- broken links in modified navigation documents: 0;
- test log:
  `/tmp/boomboomfly-wave4b-cleanup-unittest-20260728.log`;
- test log SHA256:
  `a4e1c0b43353f2edc49c7213027ff256e14f1ef40f2a9468cf488d5df55a893d`.
