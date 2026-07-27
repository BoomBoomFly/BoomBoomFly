# Wave 3B F2 — offline acceptance integration

Date: 2026-07-27
Result: **PASS — OFFLINE_SYNTHETIC ONLY**

## Scope and non-claims

F2 consumes the frozen B/C interface
`boom-boom-fly.authority-envelope/1.0.0` and preserves the A2 conclusion that
PX4 exact source/toolchain identity is `BLOCKED`. It does not start PX4, ROS,
Micro XRCE-DDS Agent, a publisher, formal SITL, a device, or hardware.

All new records carry:

```text
fixture_scope: OFFLINE_SYNTHETIC
synthetic: true
formal_sitl_evidence: false
px4_source_identity: BLOCKED
```

No result in this report is PX4, formal SITL, bench, hardware, flight, or
production evidence.

## Scenario and event contract

The catalog now contains `SITL-FAULT-025`, a bounded synthetic rejection
matrix. Its frozen cases are:

| Case | Stable event | Bound |
|---|---|---:|
| ACK timeout | `B2_ACK_TIMEOUT` | 500 ms |
| ACK rejection | `B2_ACK_RESULT_DENIED` | 500 ms |
| ACK correlation | `B2_ACK_CORRELATION_MISMATCH` | 500 ms |
| stale status/clock | `B2_STATUS_STALE` | 200 ms |
| future status/clock | `B2_STATUS_FUTURE` | 200 ms |
| backward clock | `B2_CLOCK_BACKWARD` | 200 ms |
| non-current owner | `AUTH_OWNER_NOT_CURRENT` | 100 ms |
| expired lease | `AUTH_LEASE_EXPIRED` | 100 ms |
| duplicate writer | `AUTH_DUPLICATE_WRITER` | 100 ms |
| graph epoch change | `AUTH_GRAPH_EPOCH_CHANGED` | 100 ms |
| process restart | `AUTH_RESTART_SAFE` | 100 ms |
| Offboard heartbeat loss | `B2_STATUS_STALE_OR_NOT_OFFBOARD` | 200 ms |
| source identity mismatch | `AUTH_SOURCE_EPOCH_CHANGED` | 100 ms |

Every case requires `accepted=false`, zero synthetic publish delta/count, the
exact frozen event code, and completion within its bound. The timeline also
requires a synthetic source-identity observation, one synthetic harness,
explicit cleanup, and no `PX4_PUBLISH` event.

## Implementation

- catalog entry and scenario:
  `docs/verification/scenarios/catalog.json` and
  `docs/verification/scenarios/faults/SITL-FAULT-025.json`;
- 16-record offline timeline:
  `test/sitl_acceptance/fixtures/valid/wave3b_runtime_timeline.jsonl`;
- fail-closed extension validation in `validate_scenario.py`;
- bounded event assertions in `assert_timeline.py`;
- catalog count update and two Wave 3B runtime test modules.

Negative tests remove cases, mutate event codes, increment publish counters,
exceed time bounds, or claim formal SITL evidence. Each returns a stable FAIL
or non-zero CLI result; none is ignored or converted to success.

## Validation

| Check | Result |
|---|---|
| F1+F2 unittest discovery | `PASS`, 27 tests |
| catalog validator | `PASS`, 12 normal + 25 fault = 37 |
| `SITL-FAULT-025` scenario validator | `PASS` |
| 16-event JSONL validator | `PASS` |
| timeline assertions | `PASS`, 29/29 |
| deterministic negative CLI cases | `PASS`, non-zero |
| scoped whitespace check | `PASS` |

## Decision

- stable A/B/C event-contract consumption: `PASS`;
- offline scenario/event/timeline acceptance: `PASS`;
- PX4 source identity: `EXPECTED BLOCKER` from A2;
- formal SITL: `BLOCKED`;
- prop-off bench evidence: `NOT APPLICABLE`;
- production: `BLOCKED`.
