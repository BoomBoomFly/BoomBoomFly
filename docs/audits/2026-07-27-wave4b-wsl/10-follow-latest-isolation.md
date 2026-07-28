# 2026-07-28 follow-latest and serial isolation receipt

User direction superseding the prior fixed Offboard SHA requirement:

1. Follow the latest Offboard repository.
2. Follow the latest serial repository; isolate it at this phase.

An approved `git fetch --prune origin` refreshed both remotes without pull, merge, rebase, push, or checkout of existing worktrees. The results were unchanged: Offboard remote default `DDS@cded3dc5b6906420db3767abd82b2df7ba6ea9f0`; serial remote default `master@87f3907f0b3b906d474a8d1e1dc9677ab0c4298f`.

Dedicated worktrees were created. `offboard_cpp-wave4b` tracks `origin/DDS`. Serial branch `wsl/wave4b-serial-quarantine` adds only `COLCON_IGNORE` at commit `9d8c07814ad0f64f76c5fd8fe12072aebcbef431`; marker SHA256 is `37bcea51021e7b206f471e78419ab6fd4b38a95f2a35d4fd36e0cba9c31b289e`.

Discovery-only command `colcon list --base-paths /home/aa/px4_ws/serial_driver_ros-wave4b --log-base /tmp/boomboomfly-wave4b-serial-quarantine-list-20260728` exited 0 and produced no package lines: **discovery count=0**. It did not build, launch, open a device, or form a ROS graph.

The command unexpectedly created `log/list_2026-07-28_00-23-12/logger_all.log` in the new source worktree despite the `/tmp` log option. It was immediately preserved—not deleted—and moved as a complete directory to `/tmp/boomboomfly-wave4b-serial-quarantine-worktree-log-20260728T000000`; logger SHA256 is `31ab58b7c0f018670ed91a7df1ce289891d9504b358aeb6f29041a58c0037a96`. The serial worktree is clean after the move.

This receipt does **not** close H0: direct serial open/write remains reachable if the package is manually built/run, and latest Offboard retains direct production writers and missing fail-closed gate behavior.
