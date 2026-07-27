# Wave 4B WSL summary

Capture: 2026-07-27T23:24:45+08:00.  Environment is WSL2 `rog`, user `aa`,
Linux `6.6.87.2-microsoft-standard-WSL2`, `x86_64`, ROS Foxy.  This evidence
package is a source-identity and static-safety disposition only.  No hardware,
ROS node, Agent, MAVROS, PX4, SITL, serial device, camera, lidar, or real FMU
graph was used.

## Decision

```text
H0: NO-GO
H1-WSL PRECHECK: NOT-RUN
H2: NO-GO
H3: NOT-RUN
H4: NOT-RUN
H5: BLOCKED
OPEN P0: 2
OPEN H5-RELEVANT P1: 4
READY FOR NATIVE REBUILD: NO
```

The mandatory root baseline is present at `de3c3104074c5b851d944cb4c757cbfa7d6ede20` and a clean dedicated root worktree/branch was created at `/home/aa/px4_ws/BoomBoomFly-wave4b`, branch `wsl/wave4b-20260727`.  No recursive submodule update was performed.

On 2026-07-28 the user superseded the fixed-SHA requirement and authorized following the latest Offboard repository.  An approved `git fetch --prune origin` established the upstream default as `origin/DDS@cded3dc5b6906420db3767abd82b2df7ba6ea9f0` (unchanged by fetch); it matches the existing root lock.  A dedicated worktree tracks that branch.  This resolves only the former identity block: the live single-gate/ACK/RC/kill/freshness P0 remains open.

On 2026-07-28 the user likewise authorized following the latest serial repository while keeping it isolated.  `origin/master@87f3907...` was unchanged by the approved fetch.  Dedicated branch `wsl/wave4b-serial-quarantine@9d8c078...` adds only `COLCON_IGNORE`; `colcon list` returned 0 with discovery count 0.  This is discovery quarantine only—not source governance, runtime arbitration, or a repair of the direct `/cmd_vel` execution path.

Historical reports were read as historical evidence only; their root `0ed9...`/Offboard `976...` claims were not promoted to current state.
