# Wave 4B WSL summary

Capture completed 2026-07-28 on WSL2 host `rog`, user `aa`, `x86_64`,
ROS 2 Foxy. The immutable software candidate is root
`1ea582b8e7fa8aff4d284cf108c9a6c7bb510b56` with the nested identities in
`01-source-identities.md`. The commit containing this report is evidence-only;
it does not change that tested source candidate.

Before merge to `master`, current `master@bcde328…` was integrated on the
candidate branch at `7cbd4276ab27ef97c93436529cefb1fa5a3ab1c9`. That
integration advances the governed communication gitlink to remotely
recoverable `eaaae53435ce706b32ee7dffc0c6643b43a12afe`, preserves
`update=none`, removes the retired moving `workspace.repos`, and retains the
exact Offboard/vision/quarantine identities below. A fresh integration H1
receipt also passed 14,598 tests with zero errors, failures, or skips.

```text
ENVIRONMENT: WSL
ROOT HEAD: 1ea582b8e7fa8aff4d284cf108c9a6c7bb510b56
WORKTREE CLEAN: YES (source candidate and every checked-out nested repository)
H0: GO
H1-WSL PRECHECK: PASS
H1-NATIVE: NOT-RUN
H2: GO
H3: GO
H4: NOT-RUN
OPEN P0: 0
OPEN H5-RELEVANT P1: 1
HARDWARE ACCESSED: NO
FORMAL SITL RUN: false
REAL FMU GRAPH USED: false
SOURCE FILES MODIFIED: YES
REPORTS CREATED: docs/audits/2026-07-27-wave4b-wsl/
WSL_READY_FOR_NATIVE_REBUILD: true
READY FOR H5-A REQUEST: NO
```

H1 used a fresh `/tmp/boomboomfly-wave4b-h1-20260728-08` and passed boundary,
build, test, and test-result: 3 production packages and 14,598 tests with zero
errors, failures, or skips. H2 re-executed the safety gate, RC, topic-contract,
vision, and serial-quarantine suites. H3 used isolated `ROS_DOMAIN_ID=217`,
remapped all apparent FMU inputs below `/wave4b_h3`, observed zero control
messages through two production-node runs/restarts, and left zero forbidden
processes.

Serial remains intentionally quarantined at exact remote commit
`9d8c07814ad0f64f76c5fd8fe12072aebcbef431`: discovery count, production
package references, and production launch references are all zero. Its unsafe
runtime/protocol implementation is not claimed fixed and is not part of this
candidate.

H5-A remains blocked by native ARM64 rebuild/independent H0-H3 verification,
formal approved H4 SITL, the PX4 board/toolchain/RC/profile command card, and
the separately approved two-person physical session. No device, serial port,
PX4, Agent, MAVROS, camera, lidar, or real `/fmu/in` graph was used.
