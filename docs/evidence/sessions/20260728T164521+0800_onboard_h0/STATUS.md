# Onboard H0 session status

- Session ID: `20260728T164521+0800_onboard_h0`
- Capture window: 2026-07-28 16:45–16:55 +08:00
- Current phase: H0 OS preliminary inventory only
- Overall decision: `NO-GO`
- Evidence lifecycle: `unverified`
- Hardware interaction: OS/sysfs/device-node metadata read only; no device opened
- PX4 parameter access: none
- Firmware access: none
- Agent/ROS/QGC/control process started: none

## Confirmed in this session

- Root repository: `master` at `2900914bf14da3baafd15a5326b74e5df2c89b16`.
- Lock blob: `e619420a8871a645222e331b72600dd2218afd08`.
- Companion computer: NVIDIA Orin Nano Developer Kit, Tegra SoC revision A01, arm64.
- OS/kernel: Ubuntu 20.04.6 LTS; Linux 5.10.104-tegra.
- ROS: Foxy; `ros-foxy-rmw-fastrtps-cpp` 1.3.2 installed.
- Runtime `RMW_IMPLEMENTATION` and `ROS_DOMAIN_ID`: unset in the capture shell.
- Agent source: v2.4.2 at locked SHA `57d086216d01ec43121845d385894a25987f8a2c`.
- Agent runtime: `MicroXRCEAgent` absent from PATH; no built binary found below the source tree.
- Sensors enumerated without opening them: Intel RealSense D435 (VID:PID 8086:0b07),
  a second USB Camera2, and a Movidius MA2X5X device.
- RealSense host packages: librealsense2 2.56.5; no installed
  `ros-foxy-realsense2-*` Debian package was found.
- `/dev/ttyTHS0` maps to platform UART `3100000.serial`; no owner was reported by
  `fuser` or `lsof` at capture time.
- No MicroXRCEAgent, MAVROS, Offboard, vision, old bringup, mock RC, RealSense,
  or QGC process was found by the bounded process scan.
- Clock: Asia/Shanghai, NTP synchronized. Evidence volume had 34 GiB available.

## Blocking and failed gates

- H0 is incomplete: no Human Operator disarmed confirmation timestamp and no
  Safety Officer physical disconnect/kill reachability confirmation were supplied.
- Airframe, FC model/revision, installed PX4 firmware/target/hash, bootloader,
  RC/receiver/kill mapping, QGC independent link, battery, estimator and prearm
  health remain `UNVERIFIED`.
- No approved device/protocol probe was run; no current parameter snapshot exists,
  so parameter hash is `UNVERIFIED`.
- `/fmu/out/rc_channels` and `/fmu/out/vehicle_status_v1` were not queried because
  no Agent or ROS graph was started. Their runtime availability is `UNVERIFIED`.
- Root evidence index is stale: it binds `df01b9280c0e79a05ad1e4cec727e7427c9251ca`,
  not the current root HEAD.
- Active dependencies do not match the lock: `offboard_cpp` is
  `976d6217d73a28b72e64300e2dd04bcbeeee30d7` versus locked `722e05a...`;
  `vision_to_dds` is `0c3a00137f3c90a4051ac1bc1029ec56beb669b6`
  versus locked `b366db7...`.
- Optional vision dependencies are dirty; the existing receipts must be matched
  and approved before they can support a candidate.
- The repository risk register still has P0-CTRL-001 and P0-CTRL-002 open, and
  Level 1 is `BLOCKED`. H2, H3 and finite flight are therefore `NO-GO`.

## Compatibility decision

- Host baseline against Ubuntu 20.04 / ROS 2 Foxy: compatible at OS/ROS level.
- PX4 v1.16.2 installed compatibility: `BLOCKED` because installed FC/firmware
  identity is unknown.
- `rc_channels`: static baseline says PX4 v1.16.2 default DDS profile does not
  publish it; no custom installed artifact or runtime endpoint was proven.
- `vehicle_status_v1`: statically expected for v1.16.2, but runtime endpoint is
  unverified.
- QGC/DDS serial contention: no active owner was found at capture time, but no
  approved independent QGC link was identified; bench use remains blocked.
- Vision hardware: D435 presence is confirmed only at USB/sysfs level. Camera
  stream, calibration, frame/time/EKF2 contract, health/fault behavior and
  ROS writer identity are unverified; it is not accepted for today's minimum
  visual-localization flight scenario.

## Questions for threads 2/3/4

- Provide exact root SHA, every governed dependency SHA/dirty receipt, firmware
  artifact SHA-256, profile/config hash, and complete required test results.
- Provide closure/reviewer evidence for both open P0 findings and all applicable P1s.
- Firmware thread: provide PX4 v1.16.2 source/submodule/toolchain identity, target,
  FMUv3 artifact hash, generated topic manifest proving `rc_channels` and
  `vehicle_status_v1`, installed-identity read-only probe, and rollback artifact.
- Vision thread: provide D435/profile identity, calibration, frame/time/reset/quality
  contract, EKF2 mapping, graph cardinality and loss/freeze test results.
- Control/SITL thread: provide `SITL_VERIFIED` evidence for graph guard, owner/lease,
  ACK/freshness/PRESTREAM, RC hard gate, kill latch and fault lattice.

## Next authorization needed

Before any FC protocol or parameter read, record the exact approved read-only probe,
fields, transport and link; Human Operator must provide a current disarmed timestamp
and Safety Officer must confirm physical disconnect/kill reachability. H2/H3 cannot
be authorized until the software/SITL/P0 gates above are closed.
