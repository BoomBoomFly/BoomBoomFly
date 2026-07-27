# Wave 3B summary and gate decision

Date: 2026-07-27  
Root start: `agent/wave3a-software-gates@afb4fdcecb22596056432492d1ad284919b065cd`  
Root work branch: `agent/wave3b-integration-gates`  
Offboard: `agent/wave3b-offboard-integration@976d6217d73a28b72e64300e2dd04bcbeeee30d7`

## Outcome

- A2: `BLOCKED`; exact local `px4_msgs@392e831c...` is verified, but exact
  PX4-Autopilot source, recursive submodules, DDS generator/profile, ARM
  toolchain, and board identity are absent.
- B2/C2: pure-software runtime contract `PASS`; C1+C2 36 tests, B1 12 tests,
  and B2 standalone C++ gate pass. Live node/publisher routing is not claimed.
- D2: manual non-required workflow/static contract `PASS`; reproducible job
  execution remains `BLOCKED` by eight immutable locks and the retired hosted
  Ubuntu 20.04 runner label.
- G2: active/archive/optional manifest migration `PASS`; real restore remains
  fail-closed on documented local states.
- Serial: `REQUIRES_MAINTAINER_DECISION`; the legacy gitlink and protected
  dirty `serial_driver_ros2` checkout were not altered or selected.
- F2: offline acceptance `PASS`; 27 tests and 29 timeline assertions, all
  explicitly synthetic.
- DDS wrapper: exit 2 before build at the protected serial path conflict.
- H0/H1: not executed. The software gate set is not all PASS, so the human GO
  transition was not opened.

## Remaining gates before formal SITL

1. Import and approve exact PX4 v1.16.2 source, recursive submodules,
   generator/profile, immutable toolchain, and board lock.
2. Publish or otherwise provide a reproducible approved Offboard commit, then
   update the root exact lock; the current B2 commit is local and push is not
   authorized.
3. Wire the tested authority/Offboard gates into the live node/publisher path
   and verify the transport adapter without weakening the frozen interface.
4. Resolve the canonical serial source/path with a maintainer decision while
   preserving the dirty checkout, then pass package boundary and DDS build.
5. Supply the immutable CI runner/dependency bundle locks and execute every
   stable job without `continue-on-error`.
6. Rerun the complete offline gates from a reproducible clean restore.

## Hardware decision

Because A2, D2 execution, the reproducible Offboard lock, package boundary,
and DDS build remain blocked, the coordinator decision is `NO-GO`. No `/dev`
access, firmware query, device inventory, ROS/PX4/Agent process, real topic,
parameter operation, reboot, flash, arm, mode change, actuator command, or
flight was performed.

```text
FORMAL SITL: BLOCKED UNTIL A/B/C/D/G SOFTWARE GATES PASS
PROP-OFF DISARMED BENCH: HUMAN-GATED
PROP-OFF ARMED BENCH: NOT AUTHORIZED
FIRMWARE FLASH: REQUIRES PER-ARTIFACT HUMAN CONFIRMATION
PROPELLER INSTALLATION: NOT AUTHORIZED
INDOOR FLIGHT: BLOCKED
ARM / MODE / TAKEOFF / ABORT AUTHORITY: HUMAN ONLY
PRODUCTION: BLOCKED
```
