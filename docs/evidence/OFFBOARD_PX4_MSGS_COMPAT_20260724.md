# Offboard / px4_msgs v1.16.2 compatibility evidence

> Captured: 2026-07-24 (Asia/Shanghai)
> Build scope: isolated under `/tmp`; no hardware node or control process was started.

## Inputs

- `offboard_cpp`: `BoomBoomFly/offboard_cpp@8925f8ae82258fb9f1378543f1a0dea16c15a282`
- `px4_msgs`: `PX4/px4_msgs@392e831c1f659429ca83902e66820d7094591410` (`v1.16.2`)
- ROS: Foxy

## Result

`px4_msgs` built successfully. `offboard_cpp` failed while compiling its core
library:

```text
src/offboard_cpp/src/lib/CtrlFSM.cpp:454:
error: ‘ARMING_STATE_STANDBY’ is not a member of ‘px4_msgs::msg::VehicleStatus’

src/offboard_cpp/src/lib/input.cpp:230:
error: ‘px4_msgs::msg::BatteryStatus’ has no member named ‘voltage_filtered_v’
```

The locked message definitions instead provide:

- `VehicleStatus::ARMING_STATE_DISARMED`
- `BatteryStatus.voltage_v`
- `RcChannels.channels[]` scaled to `-1..1` (throttle `0..1`)

The current Offboard RC parser treats the same array as PWM microseconds
(`1000..2000`), so RC handling is also semantically incompatible even after
the two compile errors are fixed.


The user-requested build in the current workspace was also executed:

```bash
source /opt/ros/foxy/setup.bash
colcon build --packages-up-to offboard_cpp
```

It failed earlier during CMake configuration because `src/px4_msgs` is absent
and no installed `px4_msgsConfig.cmake` was available. This dependency failure
is separate from the two source-compatibility failures above.

## Reproduction

```bash
source /opt/ros/foxy/setup.bash
colcon --log-base /tmp/boomboomfly_compat_log build \
  --base-paths /tmp/boomboomfly_px4_msgs_audit \
  /home/c/BoomBoomFly/src/offboard_cpp \
  --build-base /tmp/boomboomfly_compat_build \
  --install-base /tmp/boomboomfly_compat_install \
  --packages-up-to offboard_cpp \
  --event-handlers console_direct+
```

Summary: one package finished (`px4_msgs`), one failed (`offboard_cpp`).

## Current-workspace resolution

> Completed: 2026-07-24T22:28:44+08:00
> Scope: source restoration, build and unit tests only. No ROS runtime node,
> Agent, PX4 input publisher or hardware control path was started.

The three missing exact checkouts were restored without updating any existing
repository:

- `px4_msgs@392e831c1f659429ca83902e66820d7094591410`;
- `Micro-XRCE-DDS-Agent@57d086216d01ec43121845d385894a25987f8a2c`;
- `vision_to_dds@0c3a00137f3c90a4051ac1bc1029ec56beb669b6`.

Direct read-only verification of all 15 lock entries found matching HEAD and
origin for every repository:

| Repository | HEAD | origin | worktree |
|---|---|---|---|
| `px4_msgs` | match | match | clean |
| `Micro-XRCE-DDS-Agent` | match | match | clean |
| `gazebo_ros_pkgs` | match | match | clean |
| `imu_tools` | match | match | clean |
| `librealsense` | match | match | pre-existing dirty |
| `navigation2` | match | match | clean |
| `navigation_msgs` | match | match | pre-existing dirty |
| `offboard_cpp` | match | match | dirty from this compatibility fix |
| `realsense-ros` | match | match | pre-existing dirty |
| `rplidar_ros` | match | match | clean |
| `rtabmap` | match | match | clean |
| `rtabmap_ros` | match | match | clean |
| `slam_toolbox` | match | match | clean |
| `vision_opencv` | match | match | pre-existing dirty |
| `vision_to_dds` | match | match | clean |

At evidence-capture time, the official `--verify-only` command was deliberately
fail-closed and stopped at the first pre-existing dirty checkout
(`librealsense`). The installer was subsequently updated to audit every manifest
entry before returning non-zero. Its current result is `planned=15`,
`verified=15`, `blockers=5`; no existing dirty repository is reset, fetched,
checked out, updated or otherwise changed.

The `offboard_cpp` fix now:

- reads `BatteryStatus.voltage_v`;
- recognizes `VehicleStatus::ARMING_STATE_DISARMED`;
- consumes normalized `RcChannels` values instead of PWM microseconds;
- checks first-frame receipt, `signal_lost`, `channel_count`, configured and
  physical array bounds, finite/range validity and receive-time freshness;
- clears stale/invalid switch state fail-closed and guards FSM RC consumers;
- updates the isolated mock publisher to emit a valid normalized frame.

Validation:

```text
colcon build --packages-up-to offboard_cpp
Summary: 2 packages finished

colcon test --packages-select offboard_cpp
7 tests passed, 0 failed

colcon test-result --verbose --test-result-base build/offboard_cpp
Summary: 8 tests, 0 errors, 0 failures, 0 skipped
```

The seven gtests cover no first frame, `signal_lost`, insufficient channels,
configured-index overflow, stale data, non-finite/out-of-range RC values and
normalized mapping.

## Topic decision

- `/fmu/out/rc_channels` remains a required safety-interlock input for the
  Offboard control profile. A future PX4 v1.16.2 custom DDS firmware profile
  must export it before Offboard runtime is considered.
- `/fmu/in/landing_target_pose` is not required by the baseline profile.
  `vision_to_dds` already defaults `enable_precland=false` and does not create
  that publisher while disabled. Precision landing requires a separate custom
  firmware/profile and separate verification.
- No firmware was built or flashed and no PX4 parameter was changed here.
