# BoomBoomFly onboard read-only validation handoff — authoritative V2

Session: `20260728T174752+0800_onboard_validation`  
Host date: 2026-07-28, Asia/Shanghai  
Safety scope: workspace, T265/D435, vision ROS input, and PX4 uXRCE-DDS output-only validation. No arm, mode change, control command, parameter write, firmware flash, or flight was performed.

This V2 is authoritative. It corrects the preserved-untracked-tree wording and two camera CSV hashes in `FINAL_HANDOFF.md`.

## Disposition

**BLOCKED**

- `vision_to_dds` at its final lock builds and passes tests; the adapter candidate can proceed to formal SITL.
- Not `READY_FOR_VISION_INTEGRATION`: physical T265-to-adapter epoch/quality transitions were not captured, body extrinsics are unknown, and H0 fails because the production vision default is not disabled.
- Not declared `READY_FOR_SITL`: SITL was not run in this hardware stage, H0 fails, and current PX4 firmware/board/full parameters are unavailable over the exposed read-only paths.

## Workspace and repository contract

`origin/master` advanced beyond supplied baseline `1608a293a5c4aac94919bae81174ed8ad0d81276`. The final remote and root head is `d34ad84eddb9f181c986d20329431007a395463c`.

| Repository | Final SHA | Note |
|---|---|---|
| BoomBoomFly root | `d34ad84eddb9f181c986d20329431007a395463c` | original root `master` matches `origin/master`; tracked tree clean; preserved old and new evidence sessions are untracked |
| Clean validation worktree | `d34ad84eddb9f181c986d20329431007a395463c` | `/home/c/px4_ws/BoomBoomFly_onboard_20260728`, detached and clean |
| `px4_msgs` | `392e831c1f659429ca83902e66820d7094591410` | locked |
| `Micro-XRCE-DDS-Agent` | `57d086216d01ec43121845d385894a25987f8a2c` | locked |
| `offboard_cpp` | `473dcb81b2b8ef9fb4a2f5dd849c9c27ce61c5c8` | locked |
| `vision_to_dds` | `42a0688a6f9e9b5bfc80314a9429475eb8a297eb` | final thread-4 lock; supersedes supplied `650392...` |
| `px4_bringup` | `0fbdcbf6ee53d6927de75af1d98f22cf5bd4f917` | managed |
| `gazebo_ros_pkgs` | `b6f7bf121d0c607825b65a28b227a5459a71821b` | managed |
| `rplidar_ros` | `24cc9b6dea97e045bda1408eaa867ce730fd3fc3` | managed |
| `imu_tools` | `d28555e487e4c1278c9a2e94143dc79dcc8941bf` | managed |
| `navigation_msgs` | `fe880e99d993e9d4dfbf37f00d839d32994610e1` | managed |
| `navigation2` | `ca482808a7a7c52ce01ae3c662dc2b980968fc16` | managed |
| `rtabmap_ros` | `b341e2a776a743b8d6741b8aae8ab560471cd966` | managed |
| `vision_opencv` | `72152d9d1d8edcfcafd707a1d0103810db8613ba` | managed |
| `librealsense` | `c94410a420b74e5fb6a414bd12215c05ddd82b69` | managed |
| `realsense-ros` | `8abb4657c0add15f87b0edbfb67eaba2c1c2c439` | managed |
| `rtabmap` | `0070de4aafab0feaf5e37b497b1354d2264d41c8` | managed |
| `slam_toolbox` | `4786e90c06a4dc6fa811c5057d4e88387fba3829` | managed |
| quarantined `serial_driver_ros` | `9d8c07814ad0f64f76c5fd8fe12072aebcbef431` | excluded from production set |
| root-tracked `communication` | `eaaae53435ce706b32ee7dffc0c6643b43a12afe` | nested repository |

Full start/final branch, remote, dirty, and HEAD records are under `raw/`; final identities are in `raw/74_final_versions_git_hashes.log`.

Final lock artifact: `artifacts/workspace.final.lock.repos`, SHA-256 `08e65880adee64905c0aa4a01449cc9ab4cfa408ae5f03d6a4ed3ca12585322b`.

| Gate | Result |
|---|---|
| Manifest/lock restoration | PASS |
| Package boundary | PASS: 83 classified, 71 discovered; production set `offboard_cpp`, `px4_msgs`, `vision_to_dds` |
| Serial quarantine | PASS |
| Environment capture | PASS; `artifacts/environment.latest.json`, SHA-256 `0cd9d9c164612c2fb2df7809d5f61595f9e4ca7fbc767719a15d0a8fdf44cbf0` |
| Receipt replay | FAIL: 4 unapproved receipts — `librealsense`, `navigation_msgs`, `realsense_ros`, `vision_opencv` |
| H0 static | FAIL: `vision production default is not disabled` |
| Final `vision_to_dds` build/test | PASS: 2 CTest targets / 15 reported tests, 0 failures |
| Earlier full DDS workspace build/test | Build PASS; 14,371 tests with one `px4_msgs` generated-Python uncrustify result-file error; offboard/vision tests passed |

## Software/runtime identity

| Component | Observed |
|---|---|
| Host | Ubuntu 20.04.6 LTS, kernel `5.10.104-tegra`, aarch64 Orin Nano |
| ROS / RMW | Foxy, ROS base `0.9.2`; `rmw_fastrtps_cpp` `1.3.2` |
| RealSense apt | `librealsense2` `2.56.5`; no DKMS package |
| RealSense local | `/usr/local` SDK `2.50.0`; ROS wrapper `4.0.4` linked to this stack |
| Kernel driver | `uvcvideo 1.1.1` |
| XRCE Agent | v2.4.2 at `57d086...`; binary SHA-256 `4dd7ae1025ab70ee6f6d7431848ade4bd4a3f72701f00bf6bdab8aaea5aeec10` |
| Fast DDS | v2.12.2 at `092848725b8425e4f05a8ccf7b3b8d513fabf733` |

Agent reproduction caveat: v2.4.2 names the removed Fast DDS branch `2.12.x`. This session used official tag v2.12.2 in `/tmp` with CMake 3.27.9; no system install was modified.

## T265/D435 matrix

| Check | T265 | D435 |
|---|---|---|
| Identity | Intel RealSense T265; FW `0.2.0.951`; PID `0B37`; USB 3.1 / 5 Gbps | Intel RealSense D435; FW `5.13.0.50`; PID `0B07`; USB 3.2 |
| SDK behavior | local 2.50 enumerates; apt 2.56 does not | apt 2.56 enumerates; recommends FW 5.15.1; no flash performed |
| Streams | fisheye 1/2 848x800 Y8@30; gyro@200; accel@62; pose 6DOF@200 | depth Z16 640x480@30; color BGR8 640x480@30 |
| Epoch 1 | 2,673 vendor pose lines / 15 s, ~178.2 Hz | 430 depth + 430 color / 15 s, ~30.30 Hz; first frame 967.83 ms; stop 507.26 ms |
| Epoch 2/reconnect | 2,712 lines / 15 s, ~180.8 Hz | 438+438 / 15 s, ~30.06 Hz; first frame 599.60 ms; stop 506.42 ms |
| Monotonicity | ROS odometry and TF strict; 0 duplicate/backward in 2,395 messages | color E1: 1 duplicate/backward, 9 frame gaps; color E2 strict/no gaps; depth: 5 then 2 duplicate/backward, no frame-number gaps |
| Clock/latency | wall minus ROS stamp median: odom 6.34 ms, TF 6.64 ms; raw camera-clock offset unavailable | `global_time`; stabilized wall minus camera ~35 ms; median period 33.36 ms |
| ROS frequency | odom 199.54 Hz; TF 199.55 Hz over 12 s | camera-only validation |
| Release/reconnect | complete release, no owner/process, re-enumerated | complete release, no owner/process, re-enumerated |
| Epoch/quality behavior | driver has neither topic; physical adapter reconnect transition not captured | not a pose-source contract |
| Motion conditions | static pose stable; occlusion/fast-motion transitions not induced | static depth/color passed |
| Frames/extrinsics | `odom_frame -> t265_pose_frame`; body mount direction/extrinsics unknown | no body-pose frame contract |

Dual 12 s run passed: T265 2,097 pose samples (~174.75 Hz), D435 288 color + 288 depth (~30.33 Hz). Color stamps strict; depth had four duplicate/backward timestamps and no frame-number gaps. Both released cleanly.

Correct camera artifacts:

- `artifacts/d435_frames.csv`: SHA-256 `8c37d078db87934b15a77337d7f2a2ba8771e32967ac0eccc63637978b149d25`
- `artifacts/dual_d435_frames.csv`: SHA-256 `12332024ee83269b6b4b1a03363bb66b508202da31aa65a9375caaec3e2fb5c2`

## Vision ROS contract for WSL/thread 4

| Topic | Type / QoS | Actual behavior |
|---|---|---|
| `/t265/pose/sample` | `nav_msgs/msg/Odometry`; BEST_EFFORT, VOLATILE | publisher `/t265/t265`; frame `odom_frame`, child `t265_pose_frame`; 199.54 Hz; strict stamps; median latency 6.34 ms |
| `/tf` | `tf2_msgs/msg/TFMessage`; RELIABLE, VOLATILE | dynamic `odom_frame -> t265_pose_frame`; 199.55 Hz; strict stamps; median latency 6.64 ms |
| `/t265/pose/metadata` | wrapper metadata | available |
| `/t265/imu` | wrapper IMU | available |
| `/tf_static` | static TF | available; no verified body-camera extrinsic |

The driver does not provide `/vision/source_epoch` or `/vision/quality`. Locked adapter `42a0688...` provides:

| Topic | Type / QoS | Contract |
|---|---|---|
| `/vision/source_epoch` | `std_msgs/msg/UInt32`; KeepLast(1), BEST_EFFORT, VOLATILE | increments on restart/reconnect per unit-tested logic |
| `/vision/quality` | `std_msgs/msg/Int8`; KeepLast(1), BEST_EFFORT, VOLATILE | 20 Hz; measured no-source value `0`; current covariance maps to confidence 2 / quality 67 in code |

Unit tests cover normal input, freeze, reconnect, and quality mapping. Hardware graph connectivity was observed without any PX4 writer, but physical quality=67 and epoch increment were not captured. Thread 4 must retain those as acceptance tests.

Do not start `/fmu/in/vehicle_visual_odometry` until H0 passes, body extrinsics are supplied, physical epoch/quality transitions are captured, and SITL validates frame/time/reset semantics.

## PX4 read-only DDS contract

Preflight found no MAVROS, second Agent, old bringup, writer, `/fmu/in/*` publisher, or `/dev/ttyTHS0` owner. One Agent used `/dev/ttyTHS0` at 921600. All output publishers were bare DDS (`_CREATED_BY_BARE_DDS_APP_`) with BEST_EFFORT + TRANSIENT_LOCAL.

| Topic | Type | Publishers | Rate/samples | Timestamp/freshness |
|---|---|---:|---:|---|
| `/fmu/out/vehicle_status_v1` | `px4_msgs/msg/VehicleStatus` | 1 | 1.97 Hz | strict; median 21.27 ms |
| `/fmu/out/rc_channels` | unavailable | 0 | **MISSING** | no type/sample |
| `/fmu/out/battery_status` | `px4_msgs/msg/BatteryStatus` | 1 | 92.53 Hz | strict; median 10.89 ms |
| `/fmu/out/vehicle_odometry` | `px4_msgs/msg/VehicleOdometry` | 1 | 66.84 Hz | strict; median 12.16 ms; sample time 2.8–4.2 ms earlier |
| `/fmu/out/vehicle_land_detected` | `px4_msgs/msg/VehicleLandDetected` | 1 | 0.99 Hz | strict; median 12.74 ms |
| `/fmu/out/vehicle_command_ack` | `px4_msgs/msg/VehicleCommandAck` | 1 | 0 / 10 s | event topic; N/A in command-free run |
| `/fmu/out/timesync_status` | `px4_msgs/msg/TimesyncStatus` | 1 | 0.99 Hz | strict; median 12.68 ms; protocol 2; RTT 9,336 us |

Metrics: `artifacts/px4_output_metrics.json`, SHA-256 `8ee6fb10f035ab51e7dc9e853ed15a78eb6f15ffaee8d91a5c3a24a660539111`.

All 27 discovered `/fmu/in/*` endpoints had publisher count 0. After Agent shutdown: no Agent process, serial owner, or `/fmu/*` graph. ROS CLI can restart the normal daemon and show only `/parameter_events` and `/rosout`; these are not PX4 endpoints.

## PX4 version/board/parameter gap

| Requested item | Result |
|---|---|
| PX4 firmware version | **UNAVAILABLE** through observed DDS outputs |
| Board target | **UNAVAILABLE** |
| Full live parameter snapshot | **UNAVAILABLE** |
| Snapshot path / SHA-256 | N/A / N/A |

After Agent shutdown there was no `/dev/ttyACM*`, `/dev/ttyUSB*`, serial-by-id device, or MAVLink UDP listener. DDS exposed no read-only version/parameter service; no historical complete snapshot exists. `px4_msgs` `392e831...` identifies only the host schema. `/dev/ttyTHS0` was not multiplexed with a second protocol.

## Technical blockers

1. Disable production vision by default and make H0 pass.
2. Approve/regenerate four unapproved receipts.
3. Provide a separate read-only MAVLink/NSH/console path; collect `ver all`, board target, and complete parameter export/hash.
4. Define/verify T265-to-body rotation, translation, and frame convention.
5. Capture physical steady, freeze/occlusion, fast-motion, and reconnect adapter behavior; prove epoch and quality transitions.
6. Resolve or explicitly accept the T265 split SDK and D435 firmware recommendation; no firmware was changed here.
7. Run formal SITL with the final lock before enabling a hardware odometry writer.
8. Resolve missing `/fmu/out/rc_channels` if downstream requires it.

## Raw logs

Directory: `/home/c/px4_ws/BoomBoomFly/docs/evidence/sessions/20260728T174752+0800_onboard_validation/raw`

- `01`–`18`: workspace/sync/gates/full DDS build.
- `19`–`39`: cameras, profiles, individual/dual runs, ROS QoS/TF/time/rate/release.
- `40`–`53`: Agent build/runtime, serial/DDS graph/metrics/shutdown, PX4 transport audit.
- `55`–`60`: final remote lock, H0, final adapter build/test.
- `61`–`67`: adapter graph/standalone observations.
- `71`–`74`: final environment, receipts, quarantine, identities, process/device release.

Existing camera identity evidence was preserved. Final release audit found no Agent, RealSense process, vision adapter/writer, or `/dev/ttyTHS0`/video-device owner.
