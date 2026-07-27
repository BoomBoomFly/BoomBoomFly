# Open findings

| ID | Severity | Status | Gate impact | Short disposition |
|---|---|---|---|---|
| WSL-OFFBOARD-001 | P0 | OPEN | H0–H5 | latest `origin/DDS@cded...` has direct FMU writers, no live single gate/ACK/freshness/lease/RC/kill closure |
| WSL-SERIAL-001 | P0 | QUARANTINED FOR DISCOVERY / OPEN RUNTIME | H0–H5 | latest serial has `COLCON_IGNORE` at `9d8c078...`, but canonical governance and direct `/cmd_vel` to open/write safety remain |
| WSL-GOV-001 | P1 | OPEN | H0–H4 | root gitlink has no `.gitmodules`; locks/receipts cannot recover active source set |
| WSL-SERIAL-002 | P1 | OPEN | H1–H4 | ROS/STM32 protocol differs; odd-length parser protection is absent; no sanitizer fault proof |
| WSL-VISION-001 | P1 (P0 if enabled) | OPEN | H0–H4 | direct estimator writer lacks disabled-by-default and health/epoch/quality proof |
| WSL-PX4-001 | P1 | OPEN | H1–H4 | PX4 source/submodules/toolchain/board/RC profile not approved/locked; checkout has dirty nested gitlinks |

Shortest dependency order:

1. Keep the serial package quarantined and obtain a written canonical disposition (origin, path, production status, maintainer, offline recovery).
2. Repair root source mapping and create a dated latest-source receipt/lock including PX4 profile identity.
3. Implement and fault-test the single Offboard gate and disabled/health-gated vision on latest Offboard `DDS`.
4. Run fresh `/tmp` H1 and full H2; then isolated H3 and separately approved H4.
