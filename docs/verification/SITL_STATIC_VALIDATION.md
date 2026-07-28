# SITL static validation

## Scope and claim boundary

This suite validates the machine-readable acceptance specification and synthetic
JSON/JSONL behavior offline. It uses no ROS graph, network, device, flight
controller, simulator, or subprocess service. A passing test means only that the
schema, catalog, parser, and assertion logic behaved as specified for deterministic
fixtures.

The fixtures are labeled `SYNTHETIC_OFFLINE_FIXTURE`. They are not captured PX4
events, cannot establish a PX4 source identity, cannot close a PX4 contract gate,
and are not evidence that any simulator run passed. Formal execution remains
blocked until its scenario dependencies and authorization are satisfied.

## Test layout

| Test module | Offline contract |
|---|---|
| `test_scenario_validation.py` | Valid scenario plus required fields, IDs, bounded units, dependencies, event shape, status, and blocker rejection |
| `test_event_validation.py` | Event and JSONL structure, required fields, parse errors, and synthetic identity rejection |
| `test_timeline_assertions.py` | Wall/monotonic order, correlation closure, deadlines, forbidden counts, cleanup, publisher cardinality, identity, state order, and duplicate counts |
| `test_catalog_integrity.py` | Exactly 12 normal and 25 fault scenarios; the 25th is explicitly offline synthetic, with unique IDs, file references, and scenario semantic validation |
| `test_safety_boundaries.py` | Every prohibited safety fixture is rejected with a non-empty error list and the expected error code |

The valid fixture contains a synthetic endpoint, two synthetic state transitions,
a bounded five-second observation window, one source-identity binding, one
participant cardinality assertion, and explicit cleanup. It exercises the complete
offline assertion path without naming or impersonating a live publisher.

Negative cases are declared under `fixtures/invalid/`. Safety fixtures deliberately
contain prohibited values. Tests consume every case, assert that validation returns
at least one error, and require its designated safety error code. Those values
must not be copied into a runnable profile or normal scenario.

## Commands

Run from the repository root:

```bash
python3 -m unittest discover \
  -s test/sitl_acceptance \
  -p 'test_*.py' \
  -v
```

Compile without writing bytecode into the repository:

```bash
PYTHONPYCACHEPREFIX=/tmp/boomboomfly_sitl_spec_validation/pycache \
python3 -m compileall \
  tools/sitl_acceptance \
  test/sitl_acceptance
```

Validate the project catalog:

```bash
python3 tools/sitl_acceptance/validate_catalog.py \
  --catalog docs/verification/scenarios/catalog.json
```

Validate the synthetic fixture explicitly:

```bash
python3 tools/sitl_acceptance/validate_scenario.py \
  --scenario test/sitl_acceptance/fixtures/valid/synthetic_scenario.json

python3 tools/sitl_acceptance/validate_event.py \
  --input test/sitl_acceptance/fixtures/valid/synthetic_timeline.jsonl

python3 tools/sitl_acceptance/assert_timeline.py \
  --scenario test/sitl_acceptance/fixtures/valid/synthetic_scenario.json \
  --timeline test/sitl_acceptance/fixtures/valid/synthetic_timeline.jsonl
```

Each command emits a stable JSON summary. Exit code `0` denotes an offline check
pass, `2` denotes validation or assertion failure, and `3` denotes an input or
processing error. Any nonzero code fails the check; warnings do not substitute for
success.

## Required negative coverage

Scenario validation rejects:

- missing scenario identity;
- duplicate nested identity;
- missing expected-event deadline;
- timeout without a supported unit;
- unknown dependency;
- expected event without source;
- malformed forbidden event;
- unsupported status;
- blocked status without a blocker.

Timeline assertions reject:

- wall timestamp rollback;
- monotonic-time rollback;
- correlation lifecycle mismatch;
- deadline overrun;
- observed forbidden event;
- missing cleanup;
- wrong publisher count;
- wrong source identity;
- state-transition order mismatch;
- expected-event count overflow.

Safety validation rejects:

- a synthetic or mock source claiming authoritative identity;
- hardware-device paths or serial transport in a SITL scenario;
- firmware programming or real-hardware arming instructions;
- runtime, bench, or flight verification status claims.

## Reviewer checklist

1. All fixture sources and metadata remain visibly synthetic.
2. The valid fixture uses `OFFLINE_SPEC` evidence and makes no runtime claim.
3. Every negative case produces a nonzero rejection and expected code/assertion.
4. The catalog test validates every referenced scenario, not a hand-maintained
   count alone.
5. Timeline order is evaluated by timestamps and event identities, never fixed line
   numbers.
6. Deadlines are bounded durations; no sleep is used as an assertion.
7. Test imports and tools remain Python 3.8 standard-library compatible.
8. No code opens a network connection, device, ROS graph, or service process.

The reviewer may classify this suite as `UNIT_TESTED` only for offline tooling.
Project scenarios retain their declared status and blockers; static or unit
validation must never be promoted into formal SITL evidence.
