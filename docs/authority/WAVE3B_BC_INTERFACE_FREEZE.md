# Wave 3B B/C runtime interface freeze

Freeze date: 2026-07-27
Interface version: `boom-boom-fly.authority-envelope/1.0.0`
Coordinator decision: **FROZEN FOR WAVE 3B B2 CONSUMPTION**

This record freezes the pure-software boundary between the C2 authority
runtime and the B2 Offboard readiness gate. It does not authorize a real PX4
publication, Offboard mode, arming, SITL, bench operation, or flight.

## Immutable authority input

The C2 adapter exposes exactly these identity, ordering, time, and command
fields:

```text
interface_version
envelope_id
owner_principal_id
owner_instance_id
lease_id
lease_lifecycle
lease_issued_monotonic_ns
lease_expires_monotonic_ns
sequence
created_monotonic_ns
deadline_monotonic_ns
source_epoch
graph_epoch
correlation_id
command_kind
command_payload
```

Adapting a document never grants authority. Missing or unknown envelope fields
fail closed as `AUTH_SCHEMA_INVALID`, and the command payload is copied so the
adapter result cannot alias later caller mutation.

## Authority decision consumed by B2

B2 consumes the following observable decision fields:

```text
event_code
accepted
latch_state
runtime_state
envelope_id
correlation_id
synthetic_publish_delta
synthetic_publish_count
```

The last two fields are offline instrumentation only. They are never PX4, ROS,
SITL, bench, or flight evidence.

Runtime states are:

```text
SAFE_INITIAL
READY
ACTIVE
FAULT_LATCHED
```

Only `accepted == true`, `event_code == AUTH_ACCEPTED`,
`latch_state == CLEAR`, matching envelope/correlation identity, and a
non-fault runtime state may satisfy the authority half of B2. Those fields do
not independently authorize publication: B2 must still satisfy ACK
correlation/result, fresh VehicleStatus, clock validity, PRESTREAM continuity,
and all readiness gates.

## Stable event taxonomy

C2 preserves the complete C1 rejection taxonomy and adds exactly one
Wave 3B lease-reuse rejection:

```text
AUTH_LEASE_REUSE_REJECTED
```

The positive lifecycle events are:

```text
AUTH_RUNTIME_INITIALIZED
AUTH_GRAPH_HEALTHY
AUTH_LEASE_GRANTED
AUTH_RECOVERY_ACKNOWLEDGED
AUTH_RESTART_SAFE
```

`AUTH_ACCEPTED` remains the only accepted command decision. No unknown or
lifecycle event may be treated as accepted.

## Latch, lease, and recovery

- Duplicate writer/owner, graph identity/cardinality change, or source epoch
  change retires the current lease and latches `FAULT_LATCHED`.
- A recovered graph shape does not clear the latch.
- Recovery requires an explicit `human_authorized` acknowledgement of a
  reviewed one-writer/one-owner snapshot.
- Recovery returns to `READY` with no lease. It never enters `ACTIVE`.
- A retired lease ID may not be reused after reconnect, recovery, or restart.
- Restart returns to `SAFE_INITIAL` with no graph baseline and no lease.

## File ownership after freeze

- C2/root authority implementation:
  `tools/authority/adapter.py`, `tools/authority/runtime.py`, and
  `test/authority/test_authority_runtime.py`.
- B2/nested Offboard implementation: files within `src/offboard_cpp` only.
- The coordinator owns this record and the cross-line validation report.

No C2 writer may change Offboard files while B2 consumes this version. Any
field or taxonomy change requires a new interface version and coordinator
review.

## Freeze evidence

At freeze time, `python3 -m unittest discover -s test/authority
-p 'test_*.py' -v` passed all 36 C1+C2 tests. No ROS, PX4, Agent, launch,
publisher, device, or hardware process was started.
