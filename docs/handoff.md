# BoomBoomFly current handoff

Updated: 2026-07-28

Environment: WSL2 / x86_64 / ROS 2 Foxy

Production: `BLOCKED`

This file is a short navigation entry. Dated audits remain immutable historical
evidence; current claims require matching source identities and receipts.

## Current WSL identities

- root evidence branch: `wsl/wave4b-20260727`; resolve its current commit with
  `git rev-parse HEAD`;
- root source baseline:
  `de3c3104074c5b851d944cb4c757cbfa7d6ede20`;
- latest Offboard default branch:
  `origin/DDS@cded3dc5b6906420db3767abd82b2df7ba6ea9f0`;
- latest serial upstream:
  `origin/master@87f3907f0b3b906d474a8d1e1dc9677ab0c4298f`;
- serial discovery quarantine:
  `wsl/wave4b-serial-quarantine@9d8c07814ad0f64f76c5fd8fe12072aebcbef431`.

The serial quarantine only proves colcon discovery count zero. It does not make
manual serial execution safe. No WSL result replaces a native ARM64 rebuild of
the same approved source candidate.

## Current gate status

```text
H0: NO-GO
H1-WSL PRECHECK: NOT-RUN
H2: NO-GO
H3: NOT-RUN
H4: NOT-RUN
HARDWARE ACCESSED: NO
FORMAL SITL RUN: NO
REAL FMU GRAPH USED: NO
READY FOR H5-A REQUEST: NO
```

Open P0 items are the latest Offboard production writer/gate closure and the
serial runtime open/write path outside its discovery quarantine. Vision,
source governance, PX4 toolchain/profile locking, and native rebuild remain
open H5-relevant P1 work.

## Authoritative navigation

- [Wave 4B WSL summary](audits/2026-07-27-wave4b-wsl/00-summary.md)
- [source identities](audits/2026-07-27-wave4b-wsl/01-source-identities.md)
- [H0 closure review](audits/2026-07-27-wave4b-wsl/02-h0-closure.md)
- [open findings and dependency order](audits/2026-07-27-wave4b-wsl/07-open-findings.md)
- [machine-readable handoff](audits/2026-07-27-wave4b-wsl/08-handoff.json)
- [latest-source and serial-isolation receipt](audits/2026-07-27-wave4b-wsl/10-follow-latest-isolation.md)
- [repository cleanup receipt](audits/2026-07-27-wave4b-wsl/11-repository-cleanup.md)
- [document authority policy](governance/DOCUMENT_AUTHORITY.md)

No hardware access, `/fmu/in/*` publication, arm/mode command, parameter
change, firmware flash, Agent/MAVROS startup, or formal SITL is authorized by
this handoff.
