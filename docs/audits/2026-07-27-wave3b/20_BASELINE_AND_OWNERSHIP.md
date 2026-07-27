# Wave 3B baseline and ownership

Date: 2026-07-27
Repository root: `/home/c/BoomBoomFly`, resolved with
`git rev-parse --show-toplevel`

## Baseline decision

The reported root and Offboard identities matched the observed state. No
reset, clean, stash, fetch, pull, overwrite, force checkout, or protected
checkout mutation was performed.

| Identity | Expected | Observed | Result |
|---|---|---|---|
| root branch | `agent/wave3a-software-gates` | `agent/wave3a-software-gates` | `PASS` |
| root HEAD | `afb4fdcecb22596056432492d1ad284919b065cd` | `afb4fdcecb22596056432492d1ad284919b065cd` | `PASS` |
| root dirty state | only `?? src/serial_driver_ros2/` | only `?? src/serial_driver_ros2/` | `PASS` |
| Offboard branch | `DDS`, ahead 1, clean | `DDS`, ahead 1, clean | `PASS` |
| Offboard HEAD | `c744757a2df467807af240e34188869af65c603e` | `c744757a2df467807af240e34188869af65c603e` | `PASS` |
| bwrap executable | `/usr/bin/bwrap` | `/usr/bin/bwrap` | `PASS` |
| bwrap version | `bubblewrap 0.4.0` | `bubblewrap 0.4.0` | `PASS` |

The root working branch created from that baseline is
`agent/wave3b-integration-gates`.

## Root baseline

- origin: `https://github.com/BoomBoomFly/BoomBoomFly.git`
- starting HEAD: `afb4fdcecb22596056432492d1ad284919b065cd`
- tracked gitlink: `src/serial_driver_ros` at
  `87f3907f0b3b906d474a8d1e1dc9677ab0c4298f`
- protected pre-existing untracked checkout:
  `src/serial_driver_ros2/`

The last twelve root commits were recorded before the branch was created.
The root baseline was headed by
`afb4fdc feat(validation): add Wave 3A software gates`, followed by
`f34f5e6 docs(planning): assign post-cleanup parallel work`.

## Nested repository ledger

An empty branch cell means detached HEAD. Dirty counts are captured as
modified/deleted/untracked. All pre-existing dirty nested repositories are
read-only for Wave 3B unless explicitly owned below.

| Path | Branch | HEAD | Origin | Status |
|---|---|---|---|---|
| `src/mavros` | detached | `48b53ccdf95f10b2ab3366c6e061fad2a76bd6c8` | `git@github.com:mavlink/mavros.git` | dirty: 325/0/0 |
| `src/Micro-XRCE-DDS-Agent` | detached | `57d086216d01ec43121845d385894a25987f8a2c` | `https://github.com/eProsima/Micro-XRCE-DDS-Agent.git` | clean |
| `src/ros2_foxy_vision_to_mavros` | `main` | `3d395fdc0d034758f8846f8a4cb6dc7e22185d63` | `git@github.com:AyasOwen/ros2_foxy_vision_to_mavros.git` | dirty: 1/0/0 |
| `src/offboard_py` | `master` | `38887f08dd91719d3efa5d969d9cb7eceff7463d` | `git@hly:BoomBoomFly/px4_offboard_py.git` | clean |
| `src/realsense-ros` | detached | `8abb4657c0add15f87b0edbfb67eaba2c1c2c439` | `https://github.com/IntelRealSense/realsense-ros.git` | dirty: 98/0/1 |
| `src/mavlink` | detached | `22b62f8d55feb72f306d4c0147467beee490030d` | `https://github.com/mavlink/mavlink-gbp-release.git` | dirty: 233/0/2 |
| `src/slam_toolbox` | `foxy-devel` | `4786e90c06a4dc6fa811c5057d4e88387fba3829` | `https://github.com/SteveMacenski/slam_toolbox.git` | clean |
| `src/px4_bringup` | `DDS` | `0fbdcbf6ee53d6927de75af1d98f22cf5bd4f917` | `https://github.com/AyasOwen/px4_bringup.git` | clean |
| `src/navigation2` | `foxy-devel` | `ca482808a7a7c52ce01ae3c662dc2b980968fc16` | `https://github.com/ros-navigation/navigation2.git` | clean |
| `src/serial_driver_ros2` | `main` | `8614989c8b9e60176a83d5d32a058801fafdb8d6` | `https://github.com/BoomBoomFly/serial_driver_ros2.git` | protected dirty: 4/0/1 |
| `src/librealsense` | detached | `c94410a420b74e5fb6a414bd12215c05ddd82b69` | `https://github.com/IntelRealSense/librealsense.git` | dirty: 3347/0/0 |
| `src/rplidar_ros` | `ros2` | `24cc9b6dea97e045bda1408eaa867ce730fd3fc3` | `https://github.com/Slamtec/rplidar_ros.git` | clean |
| `src/vision_opencv` | `foxy` | `72152d9d1d8edcfcafd707a1d0103810db8613ba` | `https://github.com/ros-perception/vision_opencv.git` | dirty: 0/17/0 |
| `src/gazebo_ros_pkgs` | `foxy` | `b6f7bf121d0c607825b65a28b227a5459a71821b` | `https://github.com/ros-simulation/gazebo_ros_pkgs` | clean |
| `src/offboard_cpp` | `DDS` | `c744757a2df467807af240e34188869af65c603e` | `https://github.com/BoomBoomFly/offboard_cpp.git` | clean, ahead 1 |
| `src/rtabmap_ros` | `foxy-devel` | `b341e2a776a743b8d6741b8aae8ab560471cd966` | `https://github.com/introlab/rtabmap_ros.git` | clean |
| `src/vision_to_dds` | detached | `0c3a00137f3c90a4051ac1bc1029ec56beb669b6` | `https://github.com/wanone111/vision_to_dds.git` | clean |
| `src/imu_tools` | `foxy` | `d28555e487e4c1278c9a2e94143dc79dcc8941bf` | `https://github.com/ccny-ros-pkg/imu_tools.git` | clean |
| `src/px4_msgs` | detached | `392e831c1f659429ca83902e66820d7094591410` | `https://github.com/PX4/px4_msgs.git` | clean |
| `src/navigation_msgs` | `foxy` | `fe880e99d993e9d4dfbf37f00d839d32994610e1` | `https://github.com/ros-planning/navigation_msgs.git` | dirty: 0/13/0 |
| `src/serial-ros2` | `master` | `ae46504ae7d4a199ea9bba0e73a6f083bf172f80` | `https://github.com/RoverRobotics-forks/serial-ros2.git` | clean |
| `src/rtabmap` | `foxy-devel` | `0070de4aafab0feaf5e37b497b1354d2264d41c8` | `https://github.com/introlab/rtabmap.git` | clean |
| `src/serial_driver_ros` | n/a | index gitlink `87f3907f0b3b906d474a8d1e1dc9677ab0c4298f` | unavailable | checkout absent/uninitialized |
| `../communication` | n/a | unavailable | unavailable | path absent |

## bwrap correction and capability probe

`bubblewrap` is the package/version name; no same-named executable is
required. Wave 3B uses only:

```text
command -v bwrap
/usr/bin/bwrap --version
```

The real capability probe was:

```text
/usr/bin/bwrap --unshare-all --die-with-parent --ro-bind / / \
  --proc /proc --dev /dev /bin/true
```

It returned exit code `0`, with empty stdout and empty stderr. Therefore bwrap
capability is `PASS`; the earlier same-named-command lookup is discarded and
must not be reused as an environment conclusion.

## Exclusive ownership

| Thread | Exclusive write ownership |
|---|---|
| Coordinator | `docs/planning/NEXT_PARALLEL_TASKS.md`, `docs/handoff.md`, this record, `22_BC_RUNTIME_INTEGRATION.md`, `26_PROP_OFF_BENCH_READINESS.md`, `27_WAVE3B_VALIDATION.md`, `28_WAVE3B_SUMMARY.md`, B/C freeze record, validation ledger, staging and commits |
| A2 | `21_PX4_PROVENANCE.md` and a new lock proposal only if exact local provenance is complete |
| B2 | `src/offboard_cpp/**` supporting runtime source/tests only; no root package/launch boundary |
| C2 | new authority runtime/adapter files under `tools/authority/`, C2-only tests/fixtures under `test/authority/`; no Offboard files |
| D2 | `.github/workflows/**`, CI-only files under `test/ci_design/`, `23_CI_IMPLEMENTATION.md`; no dependency-profile validator/config |
| G2 | `workspace*.repos`, archive/optional manifests, installer manifest arguments, `test/dependency_profiles/**`, dependency docs, `24_MANIFEST_MIGRATION_AND_SERIAL_DECISION.md`; no CI-design files and no nested checkout |
| F2 | `tools/sitl_acceptance/**`, `test/sitl_acceptance/**`, `docs/verification/**`, `25_OFFLINE_ACCEPTANCE.md` |
| H | hardware inventory/bench evidence only after explicit human `GO`; no concurrent hardware access |

## B/C shared-interface freeze process

C2 owns the first implementation of the envelope/lease/event adapter. B2 may
work in parallel only on Offboard-local ACK, status freshness, clock, restart,
and PRESTREAM behavior that does not consume the C2 adapter. The coordinator
will review and freeze the C2 observable interface before assigning B2 adapter
consumption. No C2 writer may modify any file in `src/offboard_cpp`, and no B2
writer may modify root authority files.

The frozen field set is owner principal/instance ID, lease ID, sequence,
deadline, source epoch, graph epoch, command correlation ID, rejection event
taxonomy, latch state, recovery authorization, and consumer state. The
recovery destination is safe non-active `READY`; it is never automatic
`ACTIVE`.

## Hardware boundary

H0/H1 are not yet entered. No process may inspect `/dev`, start PX4/Agent/ROS,
publish a real topic, arm, change mode, write parameters, reboot, flash
firmware, command an actuator, install propellers, or fly during the software
phase.
