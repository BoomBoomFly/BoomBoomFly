# BoomBoomFly Wave 3B handoff

> Updated: 2026-07-27
> Purpose: current workspace navigation; ADRs, machine-readable profiles, and
> dated audit records remain authoritative.
> Production: `BLOCKED`

## Open the workspace

Never assume a personal checkout path:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"
git status --short --branch
git rev-parse HEAD
```

Preserve every existing dirty checkout. Do not reset, clean, stash, force
checkout, move, rename, or overwrite `src/serial_driver_ros2/` or another
protected nested repository.

## Wave 3B identities

- root start:
  `agent/wave3a-software-gates@afb4fdcecb22596056432492d1ad284919b065cd`;
- root work branch: `agent/wave3b-integration-gates`;
- nested Offboard start:
  `DDS@c744757a2df467807af240e34188869af65c603e`;
- nested Offboard final:
  `agent/wave3b-offboard-integration@976d6217d73a28b72e64300e2dd04bcbeeee30d7`,
  clean;
- protected serial checkout:
  `src/serial_driver_ros2 main@8614989c8b9e60176a83d5d32a058801fafdb8d6`,
  four modified plus one untracked, untouched.

Resolve the final root commit with `git rev-parse HEAD`; the Wave 3B summary
commit contains this handoff and therefore cannot self-record its own hash.

## Gate status

- A2: `BLOCKED`; exact PX4-Autopilot source/submodules/DDS generator/toolchain
  and board identity are absent. Exact `px4_msgs@392e831c...` alone is not a
  source lock.
- B2/C2: pure-software runtime contract `PASS`; frozen interface is
  `boom-boom-fly.authority-envelope/1.0.0`. Live node/publisher routing remains
  unverified.
- D2: manual non-required workflow/static validation `PASS`; execution remains
  `BLOCKED_BY_DEPENDENCY_LOCK` (exit 78).
- G2: active/archive/optional migration `PASS`; serial remains
  `REQUIRES_MAINTAINER_DECISION`.
- F2: `OFFLINE_SYNTHETIC` acceptance `PASS`; it is not formal SITL evidence.
- package boundary and DDS wrapper: exit 2 on the protected serial path
  conflict; no DDS build occurred.
- H0/H1: not executed; software gates did not all pass, so no human GO was
  requested or received.

Canonical results:

- [Wave 3B baseline and ownership](audits/2026-07-27-wave3b/20_BASELINE_AND_OWNERSHIP.md)
- [Wave 3B validation ledger](audits/2026-07-27-wave3b/27_WAVE3B_VALIDATION.md)
- [Wave 3B summary](audits/2026-07-27-wave3b/28_WAVE3B_SUMMARY.md)
- [B/C interface freeze](authority/WAVE3B_BC_INTERFACE_FREEZE.md)
- [source profiles](dependencies/SOURCE_PROFILES.md)
- [canonical planning](planning/NEXT_PARALLEL_TASKS.md)

## Next authorized work

Only software-blocker closure is ready to schedule:

1. import an approved offline exact PX4 v1.16.2 source/submodule/toolchain set;
2. publish or otherwise make the Offboard B2 commit reproducibly restorable,
   then update its exact root lock;
3. integrate the tested B/C gates into the live node/publisher path;
4. obtain the maintainer serial canonical-source/path decision without touching
   the protected checkout;
5. provide immutable CI runner/dependency locks and rerun the complete offline
   and DDS-only gates.

Formal SITL, hardware access without the human checklist, an armed bench,
firmware flashing without per-artifact confirmation, propeller installation,
and flight are outside the current handoff authorization.

```text
FORMAL SITL: BLOCKED UNTIL A/B/C/D/G SOFTWARE GATES PASS
PROP-OFF DISARMED BENCH: HUMAN-GATED; CURRENT DECISION NO-GO
PROP-OFF ARMED BENCH: NOT AUTHORIZED
FIRMWARE FLASH: REQUIRES PER-ARTIFACT HUMAN CONFIRMATION
PROPELLER INSTALLATION: NOT AUTHORIZED
INDOOR FLIGHT: BLOCKED
ARM / MODE / TAKEOFF / ABORT AUTHORITY: HUMAN ONLY
PRODUCTION: BLOCKED
```
