# Vision odometry writer contract

> Status: `UNIT_TESTED` for the bridge state machine only; PX4 delivery and EKF2
> consumption remain `UNVERIFIED`. This document does not authorize a node,
> Agent, SITL, camera, or hardware session.

## Frozen input and PX4 output contract

The only supported baseline is visual odometry. Precision landing is absent:
the node has no `LandingTargetPose` publisher or parameter.

| Item | Frozen value |
|---|---|
| TF input | `camera_odom_frame` (parent, ENU world) → `camera_link` (child, FLU body), exact names controlled by `world_frame_id` and `body_frame_id` |
| PX4 topic/type | `/fmu/in/vehicle_visual_odometry`, `px4_msgs/msg/VehicleOdometry` |
| PX4 pose/velocity frames | `POSE_FRAME_NED`, `VELOCITY_FRAME_NED`; body attitude is FRD |
| Position/velocity transform | `(E,N,U) -> (N,E,-D)`, i.e. `[y, x, -z]` |
| Attitude transform | `q_NED_FRD = q_NED_ENU * q_ENU_FLU * q_FLU_FRD`; both fixed basis changes are applied before publication |
| Diagonal covariance transform | ENU/FLU diagonal `[x,y,z] -> [y,x,z]` for position, velocity and orientation variance |
| Time source | TF stamp, node current time and `VehicleOdometry.timestamp{,_sample}` must use one ROS/XRCE-synchronised epoch. Both outgoing timestamps equal the accepted TF stamp in microseconds. |
| Writer QoS | KeepLast(1), best-effort, volatile |

The upstream vision source must publish these two health inputs in the same ROS
domain as the TF source:

| Input | Type | Purpose |
|---|---|---|
| `/vision/source_epoch` | `std_msgs/msg/UInt32` | Stable identifier for one source/device epoch. A value change is a restart and latches a fault. |
| `/vision/quality` | `std_msgs/msg/Int8` | Measured source quality, not a bridge constant. Default minimum is 50; a value lower than the threshold or older than 250 ms latches a fault. |

The defaults are `maximum_sample_age_s=0.20`,
`maximum_future_skew_s=0.02`, and `maximum_timestamp_jump_s=0.50`. Invalid or
empty values prevent startup; changing an upstream frame convention requires a
reviewed contract change, not a runtime guess.

## Fail-closed state machine

The writer starts unarmed. It needs an epoch, a fresh acceptable quality value,
and two strictly advancing finite TF samples before one PX4 message can be
published. The first TF sample is velocity warm-up; the second supplies a
finite differentiated NED velocity and transformed covariances.

`INPUT_TIMEOUT`, `TIMESTAMP_ROLLBACK`, `TIMESTAMP_JUMP`, `CLOCK_ROLLBACK`,
`INVALID_SAMPLE` (NaN/Inf or invalid quaternion), `SAMPLE_TOO_OLD`,
`SAMPLE_IN_FUTURE`, `QUALITY_LOW`, `QUALITY_TIMEOUT`, `SOURCE_EPOCH_CHANGED`,
and `FRAME_MISMATCH` stop the writer and emit one structured JSON event on
`/vision_to_dds_node/fault`. A repeated TF stamp ages into `INPUT_TIMEOUT`, so
a frozen image/odometry stream cannot be replayed indefinitely.

Before every writer tick the node counts same-name ROS graph instances. A count
other than one latches `DUPLICATE_WRITER` before TF/health evaluation, so a
second `/vision_to_dds_node` cannot become a second production writer.

Faults are latched. Healthy later data never resumes ACTIVE by itself. An
operator must explicitly invoke `~/reset_fault`; that increments
`reset_counter`, returns only to warm-up, and then requires the full health and
two-frame sequence again. `reset_counter` therefore denotes a bridge/source
epoch discontinuity rather than a fixed zero.

`body_frame/path` is optional diagnostics and is capped by `max_path_samples`
(200 by default); it is not part of the PX4 contract.

## Requirement to test mapping

| Requirement | Test / static assertion |
|---|---|
| ENU/FLU → NED/FRD math, position, velocity, quaternion and covariance | `VisionContract.GoldenEnuFluToNedFrdTransformsPositionVelocityAttitudeAndCovariance` |
| NaN/Inf and frame mismatch block writer | `VisionContract.RejectsNanAndFrameContractMismatch` |
| Clock reset, stamp rollback, source restart, manual-only recovery | `VisionContract.LatchesClockTimestampAndSourceRestartFaults` |
| Freeze, low quality and stamp jump block writer | `VisionContract.FreezeQualityTimeoutAndTimestampJumpStopTheWriter` |
| Diagnostic memory is bounded | `VisionContract.DiagnosticHistoryIsStrictlyBounded` |
| A duplicated visual writer is rejected before publish | `VisionContract.DuplicateWriterLatchesBeforeAnyOdometryCanPublish` |
| No callback sleep / no precision landing writer / one visual writer in package | source review plus `rg` evidence in the validation record |
| Direct `builtin_interfaces` build declaration | `package.xml` dependency and CMake `find_package` / target dependency |

## Integration prerequisites and limitations

The source must prove that its TF stamps, health callbacks and PX4 uXRCE time
are one synchronised epoch. This bridge cannot infer an unreported camera
reconnection; the source epoch publisher is mandatory for that event. It also
cannot prove a TF was derived from a live image: it rejects a non-advancing or
expired TF stamp, and the source quality/epoch publisher is responsible for
reporting upstream image health.

Before SITL, the PX4 v1.16.2 source/artifact, generated `px4_msgs`, exact
topic/type/QoS endpoints, EKF2 external-vision parameter profile, control
state-machine action on vision loss, and sole graph writer must be confirmed
in an approved isolated command card. No historical DDS session constitutes
that proof.
