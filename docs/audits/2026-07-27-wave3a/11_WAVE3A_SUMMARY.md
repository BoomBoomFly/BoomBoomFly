# Wave 3A summary and handoff

Date: 2026-07-27
Root start identity:
`agent/wave3a-software-gates@f34f5e647846cf20bbe8003b52c21035831b4fe1`
Overall gate: **BLOCKED — Wave 3A has not exited**

## Work-line disposition

| Work line | Delivered result | Current state | Boundary still open |
|---|---|---|---|
| A1 | exact local `px4_msgs` v1.16.2 and `RcChannels` consumer/spec alignment; minimum one-output profile design | `BLOCKED` | PX4-Autopilot source, recursive submodules, ARM toolchain, generated endpoint, build and SITL proof are absent |
| B1 | pure-Python ACK/freshness/PRESTREAM/authority consumer oracle; 12 tests | `UNIT_TESTED` | production FSM integration is absent; local nested commit `c744757a2df467807af240e34188869af65c603e` is not yet represented by the unchanged root dependency lock |
| C1 | Proposed ADR-0002, Draft 2020-12 envelope schema, stable rejection codes and synthetic consumer; 19 tests | `UNIT_TESTED` | architecture/control/safety review plus production arbiter, graph guard and adapter are absent |
| D1 | offline job graph, immutable-lock requirements and seven negative fixture categories; 8 tests | `UNIT_TESTED` | executable workflow, immutable runner/dependency lock and remote required checks are absent/not authorized |
| G1 | archive/optional profile design and strict synthetic validator; 10 tests | `UNIT_TESTED` | root manifest/installer migration is not authorized; `serial_driver_ros` disposition remains unresolved |
| H | OS/udev/USB inventory and prop-off safety runbook | `BLOCKED` at H0 | current disarmed/airframe/FC/PX4/parameter/safety identity and on-site prerequisites are incomplete; H2 did not start |

Canonical offline validation passed 115 root tests and 12 B1 tests. The local
DDS-only wrapper stopped before build because the protected untracked
`src/serial_driver_ros2` checkout conflicts with the expected
`src/serial_driver_ros` package path. Details are in the
[validation ledger](10_CANONICAL_VALIDATION.md).

## Frozen boundaries

- B1 may consume a C1 acceptance only when its own ACK, correlation,
  freshness, status and PRESTREAM gates also pass. Any rejection or latch keeps
  the synthetic PX4 publish count at zero.
- Manual recovery returns to a non-active ready state, revokes the old lease
  and never enters `ACTIVE` automatically.
- The baseline firmware-profile design adds only
  `/fmu/out/rc_channels`; precision landing remains absent.
- D1 remains design-only and G1 remains synthetic/profile-design-only.
- Root dependency manifests, DDS-only allowlist/forbidden set, installer and
  production files are unchanged.

## Required maintainer decisions

1. Approve an exact PX4-Autopilot v1.16.2 origin/commit, recursive submodule
   inventory and immutable build toolchain for A1 continuation.
2. Review ADR-0002 and freeze the B1/C1 runtime consumer interface before any
   production source integration.
3. Decide the canonical ownership/path of `src/serial_driver_ros` versus the
   protected dirty `src/serial_driver_ros2` checkout; do not clean or overwrite
   either to make the package gate pass.
4. Approve a runner/dependency lock before D1 can create an executable
   workflow; remote required checks remain a separate administrator action.
5. Approve G1 manifest/installer migration separately; the synthetic catalog
   is not an applied restore profile.
6. Keep formal SITL blocked until A/B/C/D exit gates pass. Hardware, flash,
   arm, mode, `/fmu/in/*`, propellers and flight require their own explicit
   authorizations and prerequisites.

```text
WAVE 3A: BLOCKED
FORMAL SITL: BLOCKED
PRODUCTION: BLOCKED
FIRMWARE FLASH: NOT AUTHORIZED
FLIGHT: NOT AUTHORIZED
```
