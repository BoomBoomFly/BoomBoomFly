# Wave 3B prop-off bench readiness

Date: 2026-07-27
Current phase: software integration gates
Hardware access performed: **NO**

## Authorization boundary

Wave 3B does not authorize formal SITL, an armed bench, firmware flashing,
parameter writes, reboot, mode change, actuator commands, automatic Offboard,
propeller installation, takeoff, or flight.

H0/H1 are sequentially downstream of the complete software-gate decision.
They may begin only after the coordinator presents the following checklist and
a human operator supplies an explicit `GO`.

```text
SOFTWARE GATES: BLOCKED — A2/D2 execution/package boundary/DDS build
ROOT HEAD: PENDING COORDINATOR ROOT SUMMARY COMMIT
OFFBOARD HEAD: 976d6217d73a28b72e64300e2dd04bcbeeee30d7
PX4 SOURCE IDENTITY: BLOCKED — exact PX4-Autopilot source/toolchain absent
KNOWN BLOCKERS: immutable CI locks; unpublished Offboard lock; serial path conflict
PROPS REMOVED: UNCONFIRMED
VEHICLE SECURED: UNCONFIRMED
HUMAN OPERATOR PRESENT: UNCONFIRMED
PHYSICAL POWER CUTOFF: UNCONFIRMED
DECISION: NO-GO
```

This record is intentionally `NO-GO` until every field is populated and the
operator explicitly changes the decision to `GO`. Silence, inference, a
software test pass, an attached device, or prior authorization is not a GO.

## H0 allowed actions after GO

- Read-only identify airframe, flight controller, and hardware revision.
- Read current PX4 firmware/version, sensor/RC/estimator/DDS health, safety
  switch, and prearm status.
- Record firmware identity and a privacy-safe parameter hash.
- Confirm propellers removed, vehicle secured, operator present, and physical
  power cutoff available.

## H1 allowed actions after H0 passes

- Disarmed-only transport, topic, QoS, and writer-cardinality observation.
- Disarmed sensor/time/frame/freshness observation.
- Read-only RC, DDS, estimator, and readiness observation.
- Verify real `/fmu/in/*` publish count remains zero before readiness.

H0/H1 must not write parameters, reboot, flash, arm, change mode, command an
actuator, start automatic Offboard, install propellers, or fly.

## Firmware-flash stop form

If any observation suggests flashing, H stops without flashing and presents:

```text
AIRFRAME:
FLIGHT CONTROLLER:
CURRENT FIRMWARE:
TARGET FIRMWARE:
TARGET SHA/HASH:
PARAMETER BACKUP:
ROLLBACK IMAGE:
HUMAN APPROVER:
DECISION: GO / NO-GO
```

Per-artifact, fully populated human confirmation is mandatory. It is not part
of the current software phase.

## Current decision

- software-to-H0 transition: `CLOSED — SOFTWARE GATES NOT ALL PASS`
- human GO record: `NONE REQUESTED / NONE RECEIVED`
- H0: `NOT EXECUTED — HUMAN-GATED`
- H1: `NOT EXECUTED — HUMAN-GATED`
- prop-off armed bench: `NOT AUTHORIZED`
- formal SITL: `NOT ENTERED`
- flight: `NOT AUTHORIZED`
