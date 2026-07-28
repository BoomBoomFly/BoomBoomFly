# T265 visual-odometry startup card

> Status: `READY_FOR_FORMAL_SITL` for the software candidate only. Hardware,
> PX4 delivery and EKF2 consumption remain `UNVERIFIED`; this card is not
> flight authorization.

## Checked driver interface

The checked-in legacy `realsense2_camera` T265 source publishes
`/camera/odom/sample` as `nav_msgs/msg/Odometry`, with dynamic TF
`odom_frame -> camera_pose_frame` when `camera_name=camera`. The pose odometry
stamp and dynamic TF stamp are both constructed from the same driver frame
time. Its tracking confidence is represented in pose covariance, not as a
separate ROS status topic. `t265_health_adapter_node` converts that measured
covariance to `/vision/quality` and emits `/vision/source_epoch` for source
startup/reconnect boundaries; it leaves TF untouched.

The D435 is explicitly out of the PX4 localization chain in this stage. It may
be launched separately for depth/image inspection only and must not publish
the TF or health inputs selected below.

## Camera-only bring-up for the camera owner

Use a dedicated ROS domain and first keep the bridge output off `/fmu/in/*`:

```bash
ros2 launch realsense2_camera rs_launch.py \
  camera_name:=camera enable_pose:=true pose_fps:=200 linear_accel_cov:=0.01

ros2 run vision_to_dds t265_health_adapter_node --ros-args \
  -p odometry_topic:=/camera/odom/sample \
  -p source_epoch_topic:=/vision/source_epoch \
  -p quality_topic:=/vision/quality \
  -p linear_accel_covariance:=0.01 \
  -p stream_timeout_s:=0.20

ros2 run vision_to_dds vision_to_dds_node --ros-args \
  -p world_frame_id:=odom_frame \
  -p body_frame_id:=camera_pose_frame \
  -p vehicle_visual_odometry_topic:=/validation/vehicle_visual_odometry
```

Before any PX4-connected run, record the actual graph and verify all of the
following from the running device: the odometry header frame/stamp equals the
dynamic TF pair/stamp, the static transform chain is expected, ROS and uXRCE
use the same epoch, measured quality is at least 50 and refreshed, and exactly
one `/vision_to_dds_node` exists. Deliberately stopping the pose source must
produce quality 0 no later than the configured timeout; reconnect or timestamp
rollback must advance source epoch; neither event may resume visual odometry
without `~/reset_fault` and two advancing TF samples.

## Formal SITL hand-off

Thread 3 should use `PX4_DDS_SITL_BASELINE` in an isolated ROS domain and run
the frozen normal graph discovery plus the vision fault scenarios. Supply a
synthetic SITL TF source in an explicitly configured ENU/FLU pair, a measured
test health source publishing `/vision/quality` and `/vision/source_epoch`,
and this bridge with the matching `world_frame_id` and `body_frame_id`.

The formal card must prove the actual PX4 source/artifact, generated
`px4_msgs`, `/fmu/in/vehicle_visual_odometry` type and KeepLast(1),
best-effort, volatile endpoints, sole writer cardinality, EKF2 external-vision
parameter snapshot, and EKF2 acceptance/loss behavior. Do not launch the T265
adapter or D435 in SITL. Precision landing remains out of scope: this package
contains no `landing_target_pose` publisher.
