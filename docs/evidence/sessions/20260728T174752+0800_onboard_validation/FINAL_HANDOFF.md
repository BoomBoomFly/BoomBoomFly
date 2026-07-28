# BoomBoomFly onboard read-only validation handoff

Session: `20260728T174752+0800_onboard_validation`  
Host date: 2026-07-28, Asia/Shanghai  
Scope: workspace, T265/D435, vision ROS input, and PX4 uXRCE-DDS output-only validation. No arm, mode change, control command, parameter write, firmware flash, or flight was performed.

## Final disposition

**BLOCKED**

- `vision_to_dds` at the final locked SHA builds and passes its unit tests, so the adapter candidate is suitable for the next formal SITL exercise.
- The onboard system is not `READY_FOR_VISION_INTEGRATION`: the physical T265-to-adapter epoch/quality transition was not captured, the T265 mount/extrinsics are unknown, and the current static H0 check fails because the production vision default is not disabled.
- The onboard system is not declared `READY_FOR_SITL`: no SITL run was part of this hardware stage, H0 remains failed, and the current PX4 firmware version, board target, and complete parameter snapshot could not be obtained through the available read-only interfaces.

## Workspace contract

The remote `origin/master` advanced beyond the supplied `1608a293a5c4aac94919bae81174ed8ad0d81276` baseline during this run. The isolated clean worktree and the original root were both advanced non-destructively to the actual final remote head:

| Item | Final value | State |
|---|---|---|
| BoomBoomFly root | `d34ad84eddb9f181c986d20329431007a395463c` | `master`, matches `origin/master`; only this new session is untracked in the original root |
| Clean validation worktree | `/home/c/px4_ws/BoomBoomFly_onboard_20260728` | detached at `d34ad84...`, clean |
| `px4_msgs` | `392e831c1f659429ca83902e66820d7094591410` | locked |
| Micro-XRCE-DDS-Agent | `57d086216d01ec43121845d385894a25987f8a2c` | locked |
| `offboard_cpp` | `473dcb81b2b8ef9fb4a2f5dd849c9c27ce61c5c8` | locked |
| `vision_to_dds` | `42a0688a6f9e9b5bfc80314a9429475eb8a297eb` | final thread-4 lock; supersedes supplied candidate `650392...` |
| `px4_bringup` | `0fbdcbf6ee53d6927de75af1d98f22cf5bd4f917` | managed |
| `librealsense` | `c94410a420b74e5fb6a414bd12215c05ddd82b69` | managed |
| `realsense-ros` | `8abb4657c0add15f87b0edbfb67eaba2c1c2c439` | managed |
| Root-tracked `communication` | `eaaae53435ce706b32ee7dffc0c6643b43a12afe` | nested |
| Quarantined `serial_driver_ros` | `9d8c07814ad0f64f76c5fd8fe12072aebcbef431` | not in production set |

Complete final lock: `artifacts/workspace.final.lock.repos`, SHA-256 `08e65880adee64905c0aa4a01449cc9ab4cfa408ae5f03d6a4ed3ca12585322b`.

Latest gates against the final remote state:

| Gate | Result |
|---|---|
| Lock/manifest restoration | PASS |
| Package boundary | PASS: 83 classified, 71 discovered; production set is `offboard_cpp`, `px4_msgs`, `vision_to_dds` |
| Serial quarantine | PASS |
| Environment capture | PASS; `artifacts/environment.latest.json`, SHA-256 `0cd9d9c164612c2fb2df7809d5f61595f9e4ca7fbc767719a15d0a8fdf44cbf0` |
| Receipt replay | FAIL: structure valid, but 4 receipts unapproved: `librealsense`, `navigation_msgs`, `realsense_ros`, `vision_opencv` |
| H0 static check | FAIL: `vision production default is not disabled` |
| Final-lock `vision_to_dds` build/test | PASS: 2 CTest targets / 15 reported tests, 0 failures |
| Earlier full DDS workspace build/test | Build PASS; 14,371 tests with 1 `px4_msgs` generated-Python uncrustify result-file error; `offboard_cpp` and then-current vision tests passed |

## Runtime versions

| Component | Observed value |
|---|---|
| OS / kernel / architecture | Ubuntu 20.04.6 LTS; `5.10.104-tegra`; aarch64 NVIDIA Orin Nano |
| ROS / RMW | Foxy, ROS base `0.9.2`; `rmw_fastrtps_cpp` `1.3.2` |
| RealSense apt stack | `librealsense2` `2.56.5`; no DKMS package observed |
| RealSense local stack | `/usr/local` SDK `2.50.0`; ROS wrapper `4.0.4` built against it |
| Kernel UVC driver | `uvcvideo 1.1.1` |
| Micro XRCE-DDS Agent | source v2.4.2 at `57d086...`; binary SHA-256 `4dd7ae1025ab70ee6f6d7431848ade4bd4a3f72701f00bf6bdab8aaea5aeec10` |
| Fast DDS for Agent | v2.12.2 at `092848...` |

Agent reproduction note: upstream Agent v2.4.2 names the deleted Fast DDS branch `2.12.x`. This run used official tag v2.12.2 in an isolated `/tmp` copy and CMake 3.27.9; no system package was overwritten.

## Camera functional matrix

| Check | Intel RealSense T265 | Intel RealSense D435 |
|---|---|---|
| Identity | FW `0.2.0.951`, PID `0B37`, USB 3.1 / 5 Gbps | FW `5.13.0.50`, PID `0B07`, USB 3.2 |
| SDK visibility | local SDK 2.50 enumerates it; apt SDK 2.56 does not | apt SDK 2.56 enumerates it; SDK recommends FW 5.15.1; not flashed |
| Tested streams | fisheye 1/2 848x800 Y8@30; gyro XYZ32F@200; accel XYZ32F@62; pose 6DOF@200 | depth Z16 640x480@30; color BGR8 640x480@30 |
| Epoch 1 | vendor pose: 2,673 lines / 15 s, ~178.2 Hz | 430+430 frames / 15 s, ~30.30 Hz; first frame 967.83 ms; stop 507.26 ms |
| Epoch 2 / reconnect | vendor pose: 2,712 lines / 15 s, ~180.8 Hz | 438+438 / 15 s, ~30.06 Hz; first frame 599.60 ms; stop 506.42 ms |
| Timestamp monotonicity | ROS odometry/TF strict, 0 duplicate/backward in 2,395 messages | color epoch 1: 1 duplicate/backward, 9 frame gaps; epoch 2 strict/no gaps; depth: 5 then 2 duplicate/backward, no frame-number gaps |
| Time offset / latency | wall-to-ROS-stamp median: odometry 6.34 ms, TF 6.64 ms; raw camera-clock offset unavailable | `global_time`; stabilized wall-minus-camera ~35 ms; median period 33.36 ms |
| ROS steady rate | odometry 199.54 Hz; TF 199.55 Hz over 12 s | camera-only validation |
| Release/reconnect | both epochs released, no owner/process, re-enumerated | both epochs released, no owner/process, re-enumerated |
| Source epoch | driver provides none; physical adapter reconnect increment not captured | host-side test epochs only |
| Static / occlusion / fast motion | static pose stable; physical occlusion and fast-motion quality transitions not induced | static acquisition passed; tracking changes N/A |
| Mount/extrinsics | observed `odom_frame -> t265_pose_frame`; body installation direction/extrinsics unknown | not established as body-pose source |

Simultaneous 12 s test passed: T265 2,097 pose samples (~174.75 Hz); D435 288 color and 288 depth (~30.33 Hz). Color timestamps were strict; depth had 4 duplicate/backward values and no frame-number gaps. Both released cleanly.

## Vision ROS/WSL input contract

| Interface | Type / QoS | Measured behavior |
|---|---|---|
| `/t265/pose/sample` | `nav_msgs/msg/Odometry`; BEST_EFFORT, VOLATILE | publisher `/t265/t265`; `odom_frame` -> `t265_pose_frame`; 199.54 Hz; strict stamp; median latency 6.34 ms |
| `/tf` | `tf2_msgs/msg/TFMessage`; RELIABLE, VOLATILE | dynamic `odom_frame` -> `t265_pose_frame`; 199.55 Hz; strict stamp; median latency 6.64 ms |
| `/t265/pose/metadata` | wrapper metadata | available |
| `/t265/imu` | wrapper IMU | available |
| `/tf_static` | static TF | available; no verified body-camera extrinsic |

The driver does not publish `/vision/source_epoch` or `/vision/quality`. Final locked adapter contract:

| Adapter output | Type / QoS | Contract |
|---|---|---|
| `/vision/source_epoch` | `std_msgs/msg/UInt32`; KeepLast(1), BEST_EFFORT, VOLATILE | increments on detected restart/reconnect per unit-tested logic |
| `/vision/quality` | `std_msgs/msg/Int8`; KeepLast(1), BEST_EFFORT, VOLATILE | 20 Hz; standalone no-source measured `0`; current T265 covariance maps to confidence 2 / quality 67 in tested code |

Unit tests cover normal input, freeze, reconnect, and quality mapping. Hardware graph connectivity was observed with no PX4 writer endpoint, but physical quality=67 and reconnect epoch transition were not captured. WSL/thread 4 must keep these as acceptance tests.

Do not start `/fmu/in/vehicle_visual_odometry` until H0 passes, T265 body extrinsics exist, physical epoch/quality transitions are captured, and SITL validates frame/time/reset semantics.

## PX4 uXRCE-DDS output-only contract

Preflight found no MAVROS, second Agent, old bringup, vision writer, `/fmu/in/*` publisher, or `/dev/ttyTHS0` owner. Exactly one Agent used `/dev/ttyTHS0` at 921600 baud. Outputs were bare-DDS publishers (`_CREATED_BY_BARE_DDS_APP_`) using BEST_EFFORT + TRANSIENT_LOCAL.

| Requested topic | Type | Publishers | Rate / samples | Timestamp / freshness |
|---|---|---:|---:|---|
| `/fmu/out/vehicle_status_v1` | `px4_msgs/msg/VehicleStatus` | 1 | 1.97 Hz | strict; median freshness 21.27 ms |
| `/fmu/out/rc_channels` | unavailable | 0 | **MISSING** | no type/samples |
| `/fmu/out/battery_status` | `px4_msgs/msg/BatteryStatus` | 1 | 92.53 Hz | strict; median freshness 10.89 ms |
| `/fmu/out/vehicle_odometry` | `px4_msgs/msg/VehicleOdometry` | 1 | 66.84 Hz | strict; median freshness 12.16 ms; sample timestamp ~2.8–4.2 ms earlier |
| `/fmu/out/vehicle_land_detected` | `px4_msgs/msg/VehicleLandDetected` | 1 | 0.99 Hz | strict; median freshness 12.74 ms |
| `/fmu/out/vehicle_command_ack` | `px4_msgs/msg/VehicleCommandAck` | 1 | 0 in 10 s | event topic; N/A in command-free run |
| `/fmu/out/timesync_status` | `px4_msgs/msg/TimesyncStatus` | 1 | 0.99 Hz | strict; median freshness 12.68 ms; protocol 2; RTT 9,336 us |

Metrics: `artifacts/px4_output_metrics.json`, SHA-256 `8ee6fb10f035ab51e7dc9e853ed15a78eb6f15ffaee8d91a5c3a24a660539111`.

All 27 discovered `/fmu/in/*` endpoints had publisher count 0. After Agent shutdown there was no Agent process, serial owner, or `/fmu/*` graph. A later ROS CLI query may start the normal ROS daemon and expose only `/parameter_events` and `/rosout`; those are not PX4 endpoints.

## PX4 version, board, and parameters

| Artifact | Result |
|---|---|
| Current PX4 firmware version | **UNAVAILABLE** from observed DDS outputs |
| Current board target | **UNAVAILABLE** from observed DDS outputs |
| Complete live parameter snapshot | **UNAVAILABLE** |
| Snapshot path / SHA-256 | N/A / N/A |

After Agent shutdown there was no `/dev/ttyACM*`, `/dev/ttyUSB*`, serial-by-id device, or MAVLink UDP listener. DDS exposed no read-only version/parameter service, and no historical full snapshot exists. `px4_msgs` `392e831...` proves only the host schema, not vehicle firmware. `/dev/ttyTHS0` was not multiplexed with a second protocol.

## Blocking items

1. Disable the production vision default and rerun H0.
2. Approve/regenerate the four unapproved receipts.
3. Establish a separate read-only MAVLink/NSH/console path and capture `ver all`, board target, and a complete parameter export with SHA-256.
4. Define and verify T265-to-body rotation, translation, and frame convention.
5. Capture physical adapter behavior during steady, freeze/occlusion, fast motion, and reconnect; prove epoch increment and quality transitions.
6. Resolve or accept the T265 split SDK stack and D435 firmware recommendation; this run changed neither.
7. Run formal SITL with the locked adapter before enabling any hardware odometry writer.
8. Determine why `/fmu/out/rc_channels` is absent if downstream requires it.

## Raw evidence

Raw command/stdout/stderr/exit evidence:

`/home/c/px4_ws/BoomBoomFly/docs/evidence/sessions/20260728T174752+0800_onboard_validation/raw`

- `01`–`18`: workspace, sync, initial gates, full DDS workspace build/test.
- `19`–`39`: camera identity/profiles, device and dual tests, ROS graph/QoS/frame/time/rate/release.
- `40`–`53`: Agent build/runtime, serial ownership, DDS graph/metrics/shutdown, version/parameter transport audit.
- `55`–`60`: final remote lock, H0, final adapter build/test.
- `61`–`67`: adapter graph/standalone contract.
- `71`–`74`: final environment, receipts, quarantine, version, process, and device-release audit.

Camera data: `artifacts/d435_frames.csv`, SHA-256 `8c37e4767a8fc7ca25a7605515f23c81ebc238c0f7be3b3f0dd4b87926d63d55`; dual-device CSV SHA-256 `123320bc6b9284ee47ca8cccd22a7db2f88777775e6bcfd86aece744e465cb05`. Existing camera identity evidence was not overwritten.
