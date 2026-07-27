# Wave 3B B2/C2 runtime integration

Date: 2026-07-27
Scope: pure-software authority and Offboard integration only

## Interface freeze

The coordinator froze
[`boom-boom-fly.authority-envelope/1.0.0`](../../authority/WAVE3B_BC_INTERFACE_FREEZE.md)
after C2 implementation and tests, before B2 adapter consumption.

C2 and B2 have disjoint file ownership:

- C2: root `tools/authority/**` and `test/authority/**`;
- B2: nested `src/offboard_cpp` supporting source and tests;
- coordinator: freeze record and this integration report.

No two writers modified the same file. C2 stopped writing before B2 was
assigned authority consumption.

## Frozen decision boundary

The authority adapter freezes owner principal/instance, lease identity and
bounds, sequence, created/deadline monotonic time, source/graph epochs,
command correlation, kind, and payload. The runtime decision freezes stable
event code, accepted flag, latch/runtime states, envelope/correlation
identity, and offline-only synthetic publish counters.

B2 may treat authority as satisfied only for an exact `AUTH_ACCEPTED` decision
with `accepted=true`, clear latch, matching identity, and non-fault state. It
must independently require correct accepted PX4 ACK correlation, a fresh
OFFBOARD VehicleStatus, valid monotonic clock, and PRESTREAM of at least one
second and at least twenty continuous valid samples.

## C2 implementation result

C2 added:

- `tools/authority/adapter.py`;
- `tools/authority/runtime.py`;
- `test/authority/test_authority_runtime.py`.

The runtime implements:

- exact owner and lease enforcement;
- lease expiry and retired-lease reuse rejection;
- source/graph epoch enforcement;
- duplicate and out-of-order sequence rejection;
- continuous writer/owner cardinality and graph identity monitoring;
- fault latch with no automatic recovery;
- human-authorized recovery to `READY` with no lease;
- restart to `SAFE_INITIAL` with no baseline or lease;
- zero synthetic publish delta for rejected commands.

The coordinator reran the combined authority suite: C1+C2 passed 36/36 tests.
No ROS, PX4, Agent, publisher, launch, device, or hardware access occurred.

## B2 implementation result

B2 added a transport-neutral C++17 gate in the nested Offboard repository:

- `include/lib/offboard_runtime_gate.hpp`;
- `src/lib/offboard_runtime_gate.cpp`;
- `test/test_offboard_runtime_gate.cpp`;
- a minimal CMake link from the production `px4_offboard_lib` and a standalone
  test target.

The gate consumes the frozen C2 decision fields and accepts only exact
`AUTH_ACCEPTED`, `accepted=true`, clear latch, `ACTIVE`, and matching
envelope/correlation identity. It then independently enforces:

- all seven VehicleCommand ACK results;
- command, target, source, sequence, envelope, correlation, source epoch, and
  local gate epoch correlation;
- ACK future, before-command, late, and timeout rejection;
- fresh, non-future, exact-epoch OFFBOARD VehicleStatus;
- monotonic consumer/frame clocks and explicit restart reset;
- PRESTREAM of at least twenty consecutive samples spanning at least one
  second;
- zero synthetic publication before all gates pass;
- restart without inherited ACK, status, authority, PRESTREAM, or readiness.

Coordinator rerun results:

| Check | Result |
|---|---|
| existing B1 Python contract suite | `PASS`, 12/12 |
| B2 standalone C++17 compile with `-Wall -Wextra -Wpedantic -Werror` | `PASS` |
| B2 standalone runtime executable | `PASS` |
| nested diff whitespace check | `PASS` |

The independently committed nested identity is
`976d6217d73a28b72e64300e2dd04bcbeeee30d7` on
`agent/wave3b-offboard-integration`. The nested worktree is clean.

## Cross-line result

The Wave 3B pure-software B/C boundary is `PASS` at the frozen struct/event
contract:

- C2 authority runtime and C1 regressions: 36/36;
- B2 Offboard runtime and B1 regressions: PASS;
- authority rejection/latch/identity mismatch: B2 publish count remains zero;
- correct accepted authority alone: no publish;
- correct accepted ACK alone: no publish;
- fresh OFFBOARD status alone: no publish;
- all authority, ACK, status, clock, and PRESTREAM conditions: only then may
  the offline synthetic counter increment.

This is a production-supporting library and build link, not a live ROS
publisher integration claim. The current Offboard node/FSM does not yet route
real DDS inputs and outputs through this gate, and no live C2-to-C++ transport
adapter was executed. Those facts block formal SITL and bench promotion even
though the pure-software runtime contract passes.

All counters and fixtures in this record are synthetic/offline. They are not
formal SITL, prop-off bench, hardware, or flight evidence.
