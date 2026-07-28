# Open findings

| ID | Severity | Status | Disposition |
|---|---|---|---|
| WSL-OFFBOARD-001 | P0 | CLOSED | single production adapter, ACK/freshness/authority/RC/kill gates, fail-closed tests |
| WSL-SERIAL-001 | P0 | CLOSED BY QUARANTINE | exact remote SHA; discovery/package/launch/writer reachability all zero |
| WSL-GOV-001 | P1 | CLOSED | `.gitmodules`, active lock, quarantine receipt, and remote recovery ledger agree |
| WSL-VISION-001 | P1 | CLOSED FOR CURRENT PROFILE | disabled by default; no estimator publisher/output in H2/H3 |
| WSL-PX4-H4-001 | P1 | OPEN | formal approved SITL command card and execution not yet completed |

```text
OPEN P0: 0
OPEN H5-RELEVANT P1: 1
```

Shortest remaining dependency order:

1. Native verifies handoff hashes and checks for conflict with its protected
   dirty state.
2. Native independently reviews H0 and rebuilds/tests/integrates exact source
   candidate on ARM64.
3. WSL prepares the exact H4 command card; user approves it; formal SITL runs
   and is cross-checked by native.
4. Native completes the H5-A card, two-person site readiness, and obtains the
   separate exact session authorization.

Serial runtime repair and enabled vision are outside this candidate. Any
attempt to enable either invalidates their current closure and requires a new
review.
