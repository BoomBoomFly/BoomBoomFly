# 2026-07-28 vision validation record

> Record status: `unverified` for SITL and hardware. This is a human-readable
> work record, not a schema-backed `current` evidence entry.

## Identity at start

| Repository | Branch / HEAD | Dirty state | Lock target |
|---|---|---|---|
| root `BoomBoomFly` | `master` / `2900914bf14da3baafd15a5326b74e5df2c89b16` | `M src/communication` (unrelated; preserved) | n/a |
| `src/vision_to_dds` | `master` / `0c3a00137f3c90a4051ac1bc1029ec56beb669b6` | clean | `b366db72cde55d9a1a7ef6bb734073fd8a43c4ae` |

The nested checkout did not match the governed lock before this work. No
fetch, checkout to the lock, reset, clean, camera, Agent, ROS node, PX4,
SITL, or hardware command was performed.

## This thread's commits

| Scope | Branch | Commit |
|---|---|---|
| `src/vision_to_dds` | `codex/vision-validation-20260728` | `6503921` (`Add fail-closed vision odometry contract`) |

The root integration commit records this validation note and the nested commit
hash above. The root intentionally ignores source checkout directories, so it
does not alter the nested gitlink. Neither commit makes the evidence `current`:
the governed lock remains different and SITL has not run.

## This thread's Level-0 commands

| Command | Exit | Result |
|---|---:|---|
| `git status`, `rev-parse HEAD`, lock comparison | 0 | Identity captured; lock mismatch remains a blocker. |
| `cmake -S src/vision_to_dds ... -DBUILD_TESTING=ON` | 0 | Isolated `/tmp/bbf-vision-build` configure passed. |
| `cmake --build /tmp/bbf-vision-build/vision_to_dds -- -j4` | 0 | Bridge and test executable built. |
| `ctest --output-on-failure` in isolated build directory | 0 | 1/1 CTest target, 6/6 gtests passed. |
| `python3 test/dependency_profiles/test_dependency_profiles.py` | 0 | 16/16 profile tests passed. |
| `python3 test/package_boundary/test_package_boundary.py` | 0 | 9/9 package-boundary tests passed. |
| static `rg` for landing target and callback sleep | 0 | No precision-landing or callback sleep symbol; one odometry publisher creation. |
| `git diff --check` | 0 | No whitespace error. |

An earlier `colcon` invocation used `--log-base` in the wrong position and
returned exit 2; it was not used as acceptance evidence. Dependency generation
was then completed in the isolated `/tmp` prefix before the passing CMake/CTest
run above.

## Follow-up candidate integration (2026-07-28)

The follow-up candidate extends the `6503921` fail-closed bridge with the
checked legacy T265 ROS interface adapter. It reads only
`/camera/odom/sample` covariance and source stamps, publishes the mandatory
`/vision/quality` and `/vision/source_epoch` health inputs, and does not
implement a second visual algorithm, modify TF stamps, or add a precision
landing publisher. The 7 adapter tests cover normal tracking, low/failed
tracking, freeze timeout, reconnect epoch increment, timestamp rollback,
initial message timeout, and reset plus two-TF recovery warm-up.

The candidate was rebuilt cleanly with a freshly built and installed isolated
`px4_msgs` dependency. CTest passed the original 6 bridge gtests and the 7
adapter gtests (13 total). An ASan/UBSan build passed the same two CTest targets
outside the ptrace-restricted filesystem sandbox; LeakSanitizer cannot run
inside that sandbox and is not used as a pass claim there. `git diff --check`
passed. Root dependency-profile, package-boundary, evidence and index checks
remain to be recorded with the root lock integration commit.

After the lock integration, dependency `--verify-only` passed all four active
exact SHAs and the evidence validator/index passed (14/14 evidence unit tests).
The package-boundary unit suite passed (9/9), but its live workspace scan is
currently blocked by the pre-existing unrelated
`src/communication/Serial/serial_driver_ros` checkout: it exposes package
`serial_driver` at a path different from the governed quarantine path
`src/serial_driver_ros`. This candidate did not modify that checkout.

The legacy driver statically exposes `odom_frame -> camera_pose_frame` and
encodes tracker confidence in covariance. This is an interface finding only:
camera frame convention, timestamp epoch, quality calibration, reconnect
behavior, extrinsics and latency require the hardware card in
`docs/runbooks/T265_VISION_STARTUP.md`.

## Cross-thread and SITL status

| Required confirmation | Status | Consequence |
|---|---|---|
| Thread 3: PX4 topic/type/QoS and EKF2 consumer | `UNVERIFIED` in this worktree; only static source inspection was possible | No claim that PX4 receives or EKF2 consumes this writer. |
| Thread 2: approved control action for vision loss | `UNVERIFIED` | Bridge stops its writer; controller/failsafe action is not asserted. |
| Formal isolated SITL timeline | `NOT RUN` | No actual PX4, Agent, ROS graph or EKF2 evidence exists. |
| Hardware sensor validation | `NOT RUN` | Camera timestamp epoch, quality calibration, reconnect signal, extrinsics, source frame convention, latency and freeze behaviour remain open. |
| Four-thread commit/hash consolidation | `PENDING` | Only this thread's commits can be recorded here after review; absent threads must not be inferred. |

Therefore this record is not `current` under `docs/evidence/SCHEMA.md`, and no
historical evidence is relabelled. The correct decision is **NO-GO** until the
lock mismatch, cross-thread confirmations and approved SITL card are closed.
