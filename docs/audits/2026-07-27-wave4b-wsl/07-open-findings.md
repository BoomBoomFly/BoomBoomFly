# Open findings

| ID | Severity | Status | Gate impact | Short disposition |
|---|---|---|---|---|
| WSL-IDENT-001 | P0 | OPEN | H0–H5 | required Offboard `976d...` is unavailable locally; actual `cded...` must not be substituted |
| WSL-OFFBOARD-001 | P0 | OPEN | H0–H5 | available non-candidate has direct FMU writers, no live single gate/ACK/freshness/lease/RC/kill closure |
| WSL-SERIAL-001 | P0 | BLOCKED | H0–H5 | canonical origin/path/SHA/owner/recovery absent; direct `/cmd_vel` to open/write path remains |
| WSL-GOV-001 | P1 | OPEN | H0–H4 | root gitlink has no `.gitmodules`; locks/receipts cannot recover active source set |
| WSL-SERIAL-002 | P1 | OPEN | H1–H4 | ROS/STM32 protocol differs; odd-length parser protection is absent; no sanitizer fault proof |
| WSL-VISION-001 | P1 (P0 if enabled) | OPEN | H0–H4 | direct estimator writer lacks disabled-by-default and health/epoch/quality proof |
| WSL-PX4-001 | P1 | OPEN | H1–H4 | PX4 source/submodules/toolchain/board/RC profile not approved/locked; checkout has dirty nested gitlinks |

Shortest dependency order:

1. Supply immutable Offboard `976d...` receipt/source or explicitly approve a different candidate; do not infer either from a moving branch.
2. Obtain a written serial canonical disposition (origin, SHA, path, production status, maintainer, offline recovery); remain quarantined pending it.
3. Repair root source mapping and create exact locks/receipts including PX4 profile identity.
4. Implement and fault-test the single Offboard gate and disabled/health-gated vision on that exact candidate.
5. Run fresh `/tmp` H1 and full H2; then isolated H3 and separately approved H4.

