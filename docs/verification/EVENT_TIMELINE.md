# SITL event timeline and offline assertions

## Scope and evidence boundary

The timeline format is an offline interchange contract for acceptance runners,
collectors, and deterministic tests. Schema or assertion success proves only that
the supplied files satisfy this contract. It does not prove that PX4, DDS, ROS 2,
or any flight-control path was executed.

The event schema version is `1.0.0`. A timeline is UTF-8 JSONL with exactly one
JSON object per non-blank line. A JSON array may be accepted by tools when
`--format json` is selected, but JSONL is the evidence format. Event order is
observed order: parsers must not sort records to make a failing timeline pass.

The authoritative structural definition is
[`schemas/event.schema.json`](schemas/event.schema.json). The scenario contract
is [`schemas/scenario.schema.json`](schemas/scenario.schema.json), and an
assertion result follows
[`schemas/result.schema.json`](schemas/result.schema.json).

## Event record

Every record contains all of these fields:

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | string | Exact schema version, currently `1.0.0`. |
| `timestamp` | string | Timezone-qualified ISO 8601 wall-clock timestamp. |
| `monotonic_timestamp` | number | Non-negative seconds from one monotonic clock. |
| `scenario_id` | string | The single scenario represented by the timeline. |
| `event_type` | string | Stable semantic event name. |
| `source` | string | Source identity key, not a display label. |
| `target` | string | Target identity key. |
| `topic` | string | Absolute ROS topic, or an empty string for non-topic events. |
| `message_type` | string | ROS interface type, or empty when `topic` is empty. |
| `correlation_id` | string | Bounded operation/lifecycle identifier. |
| `state_before` | string | State immediately before the event, or empty. |
| `state_after` | string | State immediately after the event, or empty. |
| `result` | string | `OBSERVED`, `ACCEPTED`, `REJECTED`, `TIMEOUT`, `ERROR`, or `CLEANED`. |
| `metadata` | object | Typed assertion metadata defined below. |

Numbers must be finite. `topic` and `message_type` are either both empty or both
non-empty. A non-empty topic starts with `/`. Blank JSONL records, mixed scenario
IDs, unknown top-level fields, naive timestamps, malformed JSON, and empty
timelines fail closed.

This structurally valid, deliberately non-authoritative example uses a fixture
source:

```json
{"correlation_id":"fixture-correlation","event_type":"FIXTURE_CHECK","message_type":"","metadata":{"correlation_phase":"SINGLE","synthetic":true,"timeline_origin":true},"monotonic_timestamp":0.0,"result":"OBSERVED","scenario_id":"SITL-NORMAL-001","schema_version":"1.0.0","source":"offline_fixture","state_after":"","state_before":"","target":"offline_assertion_runner","timestamp":"2026-07-26T00:00:00Z","topic":""}
```

## Monotonic order and deadline anchor

Both `timestamp` and `monotonic_timestamp` are nondecreasing in observed record
order. Equal values are permitted; record position is never used as an assertion
substitute. Ordering assertions compare monotonic timestamps and semantic event
IDs.

One event may set `metadata.timeline_origin` to `true`. If none does, the first
event's monotonic timestamp is the timeline origin. More than one origin marker
is invalid operational input and should not be emitted.

Every correlation has either:

- one event with `metadata.correlation_phase` equal to `SINGLE`; or
- exactly one `OPEN`, zero or more `MEMBER` events, and exactly one `CLOSE`, in
  that semantic order.

The timeline origin anchors scenario `stimuli.at` and expected-event `earliest`
and `deadline` values. A correlation `OPEN` proves lifecycle closure but does not
reset that scenario clock. This keeps fault injection at `2s` and an expected
event deadline at `2500ms` on one unambiguous time axis. An acceptance runner
includes `metadata.stimulus_id` on the corresponding stimulus observation.

Durations are decimal values with an explicit `ns`, `us`, `ms`, `s`, or `min`
unit. A matched expected event must occur in the inclusive interval:

```text
[timeline origin + earliest, timeline origin + deadline]
```

No assertion relies on a long fixed sleep. The producer records observations;
the offline tool evaluates bounded windows after collection.

## Expected, forbidden, count, and order assertions

An event selects an expected event specification using `metadata.event_id` and
the exact tuple
`(event_type, source, target, correlation_id)` with `*` accepted only where the
scenario specification uses it. When the event ID is absent, the tuple alone is
used. An event ID never overrides a source, target, type, or correlation
mismatch. Forbidden events are always selected by that semantic tuple, even if a
producer attaches a different event ID; relabeling an event cannot bypass a
forbidden-event assertion.

For each expected event, the tool checks:

- observed count is within the inclusive `count.min`/`count.max` range;
- every observation is inside `earliest`/`deadline`;
- `order_after` and `order_before` references are satisfied by monotonic time;
- repeated observations do not exceed `count.max`.

`A order_after B` means the first observation of A is no earlier than the last
observation of B. `A order_before B` means the last observation of A is no later
than the first observation of B. Missing endpoints fail the order assertion.

Every forbidden specification has `{ "min": 0, "max": 0 }`. Any matching record
fails the result; warnings cannot turn this into success.

## Endpoint, publisher, type, and QoS observations

Each endpoint contract is evidenced by at least one `ENDPOINT_OBSERVED` event:

- top-level `topic` equals the contract topic;
- top-level `message_type` equals the contract type;
- `metadata.qos` exactly equals the scenario QoS object;
- `metadata.publishers` is a list of source identity keys;
- the list length is inside `publisher_count`;
- `required_source` is present in that list.

All observations for the endpoint must be well formed and satisfy the contract.
A second writer therefore cannot be hidden by also providing one valid snapshot.
The event is an offline observation record; the tool never queries a ROS graph.

Example metadata shape:

```json
{
  "correlation_phase": "MEMBER",
  "event_id": "N002-E02",
  "publishers": ["declared_source"],
  "qos": {
    "depth": 1,
    "durability": "volatile",
    "history": "keep_last",
    "reliability": "best_effort"
  }
}
```

## Source identity observations

The scenario `source_identity.profile_ref` must equal `profile.profile_id`. Each
binding requires one or more `SOURCE_IDENTITY_OBSERVED` events whose top-level
`source` is the binding source. Metadata contains:

| Metadata key | Required value |
|---|---|
| `profile_id` | Scenario `source_identity.profile_ref`. |
| `identity_kind` | Binding `identity_kind`. |
| `observed_identity` | Binding `expected`. |
| `mock` | Binding `mock`, as a JSON boolean. |
| `synthetic` | `true` only for openly synthetic evidence. |

Every identity observation for that source must match. Synthetic or mock input
cannot assert an authoritative PX4 identity and cannot close a PX4 contract gate.

## State transitions

A state change is a `STATE_TRANSITION` event. Its `state_before` and
`state_after` values match the scenario transition, and
`metadata.trigger_event_id` names the triggering expected event. Transitions are
selected by content, ordered by monotonic time, and evaluated against their
explicit deadline from the matching trigger observation. The engine never uses a
fixed record number.

The triggering observation uses either its normal `metadata.event_id` or a
`metadata.trigger_id` when the state-transition trigger is a more specific
condition (for example, an event plus a result value). That observation must
exist at or before the state transition. A transition record cannot satisfy two
declared transition steps.

## Participant cardinality and cleanup

`PARTICIPANT_SNAPSHOT` events carry:

```json
{
  "participant_counts": {
    "declared_participant": 1
  }
}
```

Keys are scenario participant IDs and values are non-negative integers. The last
well-formed snapshot is checked against every `participant_cardinality`
assertion, and all participant snapshots must be well formed.

Exactly one successful cleanup observation is required:

- `event_type` is `CLEANUP_COMPLETE`;
- `result` is `CLEANED`;
- `metadata.participant_counts` is well formed;
- `metadata.cleanup_started_monotonic` is a finite monotonic timestamp no later
  than the completion event;
- every ID in `cleanup.expected_absent_participants` has count zero;
- later participant snapshots cannot reintroduce an expected-absent ID.

The completion event must occur no later than
`cleanup_started_monotonic + cleanup.deadline`. Missing or malformed cleanup
evidence fails offline assertion.

## Tools and exit codes

All commands use Python 3.8 standard-library code and operate only on explicit
files:

```bash
python3 tools/sitl_acceptance/parse_timeline.py \
  --input timeline.jsonl \
  --format jsonl \
  --output parse-summary.json

python3 tools/sitl_acceptance/assert_timeline.py \
  --scenario docs/verification/scenarios/normal/SITL-NORMAL-001.json \
  --timeline timeline.jsonl \
  --format jsonl \
  --output assertion-result.json

python3 tools/sitl_acceptance/report_result.py \
  --scenario docs/verification/scenarios/normal/SITL-NORMAL-001.json \
  --timeline timeline.jsonl \
  --format jsonl \
  --output assertion-result.json
```

Exit code `0` means all checks in that command passed, `2` means validly read
input failed validation/assertions, and `3` means an input/output or parse
operation failed. JSON output is stably key-sorted. Output files are optional
except for `report_result.py`; without an output option the other tools are
read-only.

`report_result.py` writes the result-schema document and prints a separate JSON
summary with an explicit offline-only disclaimer. It does not start services,
access devices, invoke subprocesses, access a network, or alter a scenario.

## Result interpretation

Result `PASS` means every named offline assertion passed for the exact timeline
digest in `input_sha256`. `FAIL` means at least one structural error or assertion
failure occurred. `BLOCKED` is reserved by the result schema for a runner that
cannot collect required formal evidence; this offline engine reports missing
evidence as failure rather than silently downgrading it.

Requirement and audit traceability comes from the referenced scenario's
`requirement_ids` and `audit_ids`. Those IDs are not duplicated in the result
schema, preventing an assertion report from changing the frozen mapping.
Runtime acceptance requires separately authorized execution, authoritative
source-identity evidence, and the scenario's declared dependencies.
