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
OPEN P0: 3
OPEN H5-RELEVANT P1: 4
READY FOR NATIVE REBUILD: NO
```

The mandatory root baseline is present at `de3c3104074c5b851d944cb4c757cbfa7d6ede20` and a clean dedicated root worktree/branch was created at `/home/aa/px4_ws/BoomBoomFly-wave4b`, branch `wsl/wave4b-20260727`.  No recursive submodule update was performed.

The required Offboard candidate `976d6217d73a28b72e64300e2dd04bcbeeee30d7` is **not present** in the local Offboard object database.  The actual clean checkout is `DDS@cded3dc5b6906420db3767abd82b2df7ba6ea9f0`, which matches the existing root lock but is not a permitted substitution.  Therefore no source fix or build was attempted against a substituted candidate.

Serial has no uniquely provable canonical origin/path/immutable receipt.  It remains blocked and must not participate in discovery, build, launch, or production control.  The prior Wave 4A statement that `COLCON_IGNORE` quarantined it is not current: the marker is absent at `87f3907...`.

Historical reports were read as historical evidence only; their root `0ed9...`/Offboard `976...` claims were not promoted to current state.
