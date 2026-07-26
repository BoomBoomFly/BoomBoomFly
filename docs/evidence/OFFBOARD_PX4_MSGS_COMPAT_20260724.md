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
entry before returning non-zero. After publishing the Offboard fix and updating
the root lock, its result at that update was `planned=15`, `verified=15`,
`blockers=4`. On 2026-07-26, archived `px4_bringup` was aligned with its
upstream default `DDS@0fbdcbf6`, added to the source manifests, and kept in
`workspace.excluded_packages`. The subsequent read-only exact-lock audit
reported `planned=16`, `verified=16`, `blockers=4`; no existing dirty
repository was reset, fetched, checked out, updated or otherwise changed by
either audit.

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

## Publication

- Offboard commit: `0c41de3cf8d56982bd67a5be56a9e281f3d9fc8f`
- pushed branch: `agent/px4-v116-rc-safety`
- PR [BoomBoomFly/offboard_cpp#1](https://github.com/BoomBoomFly/offboard_cpp/pull/1)
  merged to `DDS` as `c4a95b95fc70cec2e807a4bdcf4c672961a3307a`
- follow-up commit: `73569b2db19b6178bfa0a30ac38911175517cc97`
- follow-up branch: `agent/px4-v116-status-contract`
- PR [BoomBoomFly/offboard_cpp#2](https://github.com/BoomBoomFly/offboard_cpp/pull/2)
  merged to `DDS` as `cded3dc5b6906420db3767abd82b2df7ba6ea9f0`
- the companion BoomBoomFly lock now pins that merge commit

## Topic decision

- `/fmu/out/rc_channels` remains a required safety-interlock input for the
  Offboard control profile. A future PX4 v1.16.2 custom DDS firmware profile
  must export it before Offboard runtime is considered.
- `/fmu/in/landing_target_pose` is not required by the baseline profile.
  `vision_to_dds` already defaults `enable_precland=false` and does not create
  that publisher while disabled. Precision landing requires a separate custom
  firmware/profile and separate verification.
- No firmware was built or flashed and no PX4 parameter was changed here.

## Read-only hardware DDS follow-up

> Captured: 2026-07-25T20:02:13+08:00 to 2026-07-25T20:31:08+08:00
> Scope: explicitly authorized transport and output-only validation. No
> Offboard, vision, MAVROS, PX4 input publisher, arm, mode, setpoint, vehicle
> command, parameter write or firmware flash was started.

The maintainer reported changing the TELEM2/MAVLink/DDS parameters before this
test. The exact post-change parameter values were not recaptured because no PX4
USB or alternate MAVLink device was present. The 2026-07-24 JSON parameter
snapshot therefore remains historical pre-change evidence.

Preflight checks found `/dev/ttyTHS0` present, the user in `dialout`, no process
holding the device, and no running Agent, MAVROS, Offboard or vision process.
The locked Agent source was clean at:

```text
Micro-XRCE-DDS-Agent@57d086216d01ec43121845d385894a25987f8a2c
```

Agent v2.4.2 was built under `/tmp` with the system ROS 2 Foxy Fast DDS,
Fast CDR and spdlog dependencies. No checkout or system package was modified.
The serial probe used:

```bash
MicroXRCEAgent serial -D /dev/ttyTHS0 -b 921600 -v 6
```

Within approximately 0.3 seconds, client `0x00000001` established session
`0x81`, and participant `/px4_micro_xrce_dds` was created. The Agent then
created DDS publishers/datawriters and continuously forwarded payloads.

ROS 2 discovery confirmed the default input/output graph. In particular:

- `/fmu/out/battery_status` has one PX4 publisher and decoded live
  `BatteryStatus` payloads (`connected=true`, four cells, approximately 16 V);
- `/fmu/out/vehicle_status_v1` has one PX4 publisher;
- `/fmu/out/rc_channels` is absent and `ros2 topic info` reports unknown topic.

The versioned status topic is required by the locked message definition:

```text
src/px4_msgs/msg/VehicleStatus.msg: uint32 MESSAGE_VERSION = 1
```

At capture time, Offboard subscribed to `fmu/out/vehicle_status` without the
`_v1` suffix. The earlier compile/unit tests did not cover this runtime contract.
PR #1 was already merged before the mismatch was fixed, so the repair was made
and validated later in the local working tree as recorded below.

After validation the Agent was stopped, `/dev/ttyTHS0` was released, and the
root, Agent, `px4_msgs`, and Offboard worktrees were checked. No source checkout
was changed by the runtime test.

## Local VehicleStatus contract repair

> Captured: 2026-07-25
> Scope: local source repair and isolated build/test only.

The follow-up repair aligns the production subscription with the PX4 v1.16.2
versioned output while keeping the runtime path fail-closed.

Changes:

- `include/topics.hpp` defines `fmu/out/vehicle_status_v1` once;
- `src/node.cpp` uses that constant for the production subscription;
- `test/test_topic_contract.cpp` checks the exact topic, production use of the
  constant, and absence of the legacy literal;
- `CMakeLists.txt` registers the new gtest executable.

Validation:

- isolated `px4_msgs` and `offboard_cpp` build: 2 packages finished;
- full Offboard CTest: 2/2 executables, 9 gtest cases, 0 failures;
- `git diff --check`: passed.

The validation itself made no commit, push, PX4 parameter change, firmware
build/flash, Agent, Offboard runtime, ROS hardware node or serial-device access.
The validated source was later committed as `73569b2d`, pushed to
`agent/px4-v116-status-contract`, and opened as draft PR #2; publishing did not
perform any hardware or runtime action.
