#!/usr/bin/env python3
"""Evaluate a scenario contract against an offline JSON/JSONL event timeline."""

import argparse
import datetime
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

if __package__:
    from .parse_timeline import parse_timeline
    from .validate_scenario import SCENARIO_ID_RE, SCHEMA_VERSION, validate_scenario
else:
    from parse_timeline import parse_timeline
    from validate_scenario import SCENARIO_ID_RE, SCHEMA_VERSION, validate_scenario


DURATION_RE = re.compile(r"^(0|[1-9][0-9]*)(\.[0-9]+)?(ns|us|ms|s|min)$")
DURATION_FACTORS = {
    "ns": 0.000000001,
    "us": 0.000001,
    "ms": 0.001,
    "s": 1.0,
    "min": 60.0,
}


def _duration_seconds(value: str) -> float:
    match = DURATION_RE.fullmatch(value)
    if not match:
        raise ValueError("duration has no supported unit: %r" % value)
    unit = match.group(3)
    return float(value[: -len(unit)]) * DURATION_FACTORS[unit]


def _timestamp_seconds(value: str) -> float:
    parsed = datetime.datetime.fromisoformat(
        value[:-1] + "+00:00" if value.endswith("Z") else value
    )
    if parsed.tzinfo is None:
        raise ValueError("timestamp has no timezone")
    return parsed.timestamp()


def _assertion(
    assertion_id: str, passed: bool, details: Dict[str, Any]
) -> Dict[str, Any]:
    return {
        "assertion_id": assertion_id,
        "details": details,
        "status": "PASS" if passed else "FAIL",
    }


def _error(code: str, path: str, message: str) -> Dict[str, str]:
    return {"code": code, "message": message, "path": path}


def _matches_field(observed: Any, required: Any) -> bool:
    return required == "*" or observed == required


def _event_matches(
    event: Dict[str, Any],
    specification: Dict[str, Any],
    use_declared_event_id: bool = True,
) -> bool:
    metadata = event.get("metadata", {})
    observed_id = metadata.get("event_id") if isinstance(metadata, dict) else None
    semantic_match = all(
        _matches_field(event.get(field), specification.get(field))
        for field in ("event_type", "source", "target", "correlation_id")
    )
    if use_declared_event_id and observed_id is not None:
        return observed_id == specification.get("event_id") and semantic_match
    return semantic_match


def _matching_events(
    events: Sequence[Dict[str, Any]],
    specification: Dict[str, Any],
    use_declared_event_id: bool = True,
) -> List[Dict[str, Any]]:
    return [
        event
        for event in events
        if _event_matches(event, specification, use_declared_event_id)
    ]


def _origin_time(events: Sequence[Dict[str, Any]]) -> float:
    marked = [
        float(event["monotonic_timestamp"])
        for event in events
        if event.get("metadata", {}).get("timeline_origin") is True
    ]
    return marked[0] if marked else float(events[0]["monotonic_timestamp"])


def _ordering_assertions(events: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    monotonic_values = [float(event["monotonic_timestamp"]) for event in events]
    wall_values = [_timestamp_seconds(str(event["timestamp"])) for event in events]
    monotonic_ok = all(
        current >= previous
        for previous, current in zip(monotonic_values, monotonic_values[1:])
    )
    wall_ok = all(
        current >= previous for previous, current in zip(wall_values, wall_values[1:])
    )
    origin_markers = sum(
        event.get("metadata", {}).get("timeline_origin") is True for event in events
    )
    return [
        _assertion(
            "timeline.monotonic_order",
            monotonic_ok,
            {"events_checked": len(events), "nondecreasing": monotonic_ok},
        ),
        _assertion(
            "timeline.wall_timestamp_order",
            wall_ok,
            {"events_checked": len(events), "nondecreasing": wall_ok},
        ),
        _assertion(
            "timeline.origin_cardinality",
            origin_markers <= 1,
            {"maximum": 1, "observed": origin_markers},
        ),
    ]


def _correlation_assertion(events: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    problems: List[Dict[str, Any]] = []
    correlation_ids = sorted({str(event["correlation_id"]) for event in events})
    for correlation_id in correlation_ids:
        grouped = [
            event for event in events if str(event["correlation_id"]) == correlation_id
        ]
        phases = [
            str(event.get("metadata", {}).get("correlation_phase", "MEMBER"))
            for event in grouped
        ]
        invalid = sorted({phase for phase in phases if phase not in {"OPEN", "MEMBER", "CLOSE", "SINGLE"}})
        single_valid = len(grouped) == 1 and phases == ["SINGLE"]
        paired_valid = (
            phases.count("OPEN") == 1
            and phases.count("CLOSE") == 1
            and phases[0] == "OPEN"
            and phases[-1] == "CLOSE"
            and "SINGLE" not in phases
        )
        if invalid or not (single_valid or paired_valid):
            problems.append(
                {
                    "correlation_id": correlation_id,
                    "phases": phases,
                    "reason": "expected one SINGLE or an OPEN...CLOSE lifecycle",
                }
            )
    return _assertion(
        "timeline.correlation_closed",
        not problems,
        {"correlations_checked": len(correlation_ids), "problems": problems},
    )


def _event_contract_assertions(
    scenario: Dict[str, Any],
    events: Sequence[Dict[str, Any]],
    origin: float,
) -> List[Dict[str, Any]]:
    assertions: List[Dict[str, Any]] = []
    observed_by_id: Dict[str, List[Dict[str, Any]]] = {}
    for specification in scenario["expected_events"]:
        observed_by_id[specification["event_id"]] = _matching_events(events, specification)
    for specification in scenario["forbidden_events"]:
        observed_by_id[specification["event_id"]] = _matching_events(
            events, specification, use_declared_event_id=False
        )
    for specification in scenario["expected_events"]:
        event_id = specification["event_id"]
        observed = observed_by_id[event_id]
        count = len(observed)
        minimum = specification["count"]["min"]
        maximum = specification["count"]["max"]
        count_ok = minimum <= count <= maximum
        assertions.append(
            _assertion(
                "expected.%s.count" % event_id,
                count_ok,
                {"actual": count, "maximum": maximum, "minimum": minimum},
            )
        )
        earliest = origin + _duration_seconds(specification["earliest"])
        deadline = origin + _duration_seconds(specification["deadline"])
        out_of_window = [
            float(event["monotonic_timestamp"])
            for event in observed
            if not earliest <= float(event["monotonic_timestamp"]) <= deadline
        ]
        assertions.append(
            _assertion(
                "expected.%s.deadline" % event_id,
                not out_of_window and count >= minimum,
                {
                    "deadline_monotonic": deadline,
                    "earliest_monotonic": earliest,
                    "out_of_window": out_of_window,
                },
            )
        )
    for specification in scenario["forbidden_events"]:
        event_id = specification["event_id"]
        observed = observed_by_id[event_id]
        assertions.append(
            _assertion(
                "forbidden.%s.count" % event_id,
                len(observed) == 0,
                {"actual": len(observed), "required": 0},
            )
        )
    for specification in scenario["expected_events"]:
        event_id = specification["event_id"]
        observed = observed_by_id[event_id]
        for predecessor in specification["order_after"]:
            preceding = observed_by_id.get(predecessor, [])
            passed = bool(observed) and bool(preceding) and min(
                float(item["monotonic_timestamp"]) for item in observed
            ) >= max(float(item["monotonic_timestamp"]) for item in preceding)
            assertions.append(
                _assertion(
                    "order.%s.after.%s" % (event_id, predecessor),
                    passed,
                    {
                        "event_count": len(observed),
                        "predecessor_count": len(preceding),
                    },
                )
            )
        for successor in specification["order_before"]:
            following = observed_by_id.get(successor, [])
            passed = bool(observed) and bool(following) and max(
                float(item["monotonic_timestamp"]) for item in observed
            ) <= min(float(item["monotonic_timestamp"]) for item in following)
            assertions.append(
                _assertion(
                    "order.%s.before.%s" % (event_id, successor),
                    passed,
                    {"event_count": len(observed), "successor_count": len(following)},
                )
            )
    return assertions


def _endpoint_assertions(
    scenario: Dict[str, Any], events: Sequence[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    assertions: List[Dict[str, Any]] = []
    for index, contract in enumerate(scenario["assertions"]["endpoint_contracts"]):
        snapshots = [
            event
            for event in events
            if event["event_type"] == "ENDPOINT_OBSERVED"
            and event["topic"] == contract["topic"]
        ]
        valid_snapshots: List[Dict[str, Any]] = []
        for event in snapshots:
            metadata = event["metadata"]
            publishers = metadata.get("publishers")
            if (
                event["message_type"] == contract["message_type"]
                and metadata.get("qos") == contract["qos"]
                and isinstance(publishers, list)
                and all(isinstance(item, str) for item in publishers)
            ):
                valid_snapshots.append(event)
        counts = [len(event["metadata"]["publishers"]) for event in valid_snapshots]
        required_source = contract["required_source"]
        source_present = any(
            required_source in event["metadata"]["publishers"]
            for event in valid_snapshots
        )
        minimum = contract["publisher_count"]["min"]
        maximum = contract["publisher_count"]["max"]
        count_ok = bool(counts) and all(minimum <= count <= maximum for count in counts)
        assertion_id = "endpoint.%03d.%s" % (
            index,
            hashlib.sha256(contract["topic"].encode("utf-8")).hexdigest()[:12],
        )
        assertions.append(
            _assertion(
                assertion_id,
                bool(snapshots)
                and len(valid_snapshots) == len(snapshots)
                and count_ok
                and source_present,
                {
                    "contract_valid_snapshots": len(valid_snapshots),
                    "message_type": contract["message_type"],
                    "observed_snapshots": len(snapshots),
                    "publisher_counts": counts,
                    "publisher_maximum": maximum,
                    "publisher_minimum": minimum,
                    "qos": contract["qos"],
                    "required_source": required_source,
                    "source_present": source_present,
                    "topic": contract["topic"],
                },
            )
        )
    return assertions


def _source_identity_assertions(
    scenario: Dict[str, Any], events: Sequence[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    assertions: List[Dict[str, Any]] = []
    profile_id = scenario["profile"]["profile_id"]
    profile_ref = scenario["source_identity"]["profile_ref"]
    profile_consistent = profile_id == profile_ref
    assertions.append(
        _assertion(
            "source_identity.profile_ref",
            profile_consistent,
            {"profile_id": profile_id, "profile_ref": profile_ref},
        )
    )
    for binding in scenario["source_identity"]["bindings"]:
        source = binding["source"]
        observations = [
            event
            for event in events
            if event["event_type"] == "SOURCE_IDENTITY_OBSERVED"
            and event["source"] == source
        ]
        matching = [
            event
            for event in observations
            if event["metadata"].get("profile_id") == profile_ref
            and event["metadata"].get("identity_kind") == binding["identity_kind"]
            and event["metadata"].get("observed_identity") == binding["expected"]
            and event["metadata"].get("mock") is binding["mock"]
            and not (
                event["metadata"].get("synthetic") is True
                and "PX4"
                in (
                    str(binding["identity_kind"]) + " " + str(binding["expected"])
                ).upper()
            )
        ]
        assertions.append(
            _assertion(
                "source_identity.%s" % source,
                bool(observations) and len(matching) == len(observations),
                {
                    "expected": binding["expected"],
                    "matching_observations": len(matching),
                    "observations": len(observations),
                    "profile_ref": profile_ref,
                },
            )
        )
    return assertions


def _state_assertions(
    scenario: Dict[str, Any],
    events: Sequence[Dict[str, Any]],
    origin: float,
) -> List[Dict[str, Any]]:
    assertions: List[Dict[str, Any]] = []
    previous_time = -math.inf
    consumed_events: set = set()
    for index, transition in enumerate(scenario["assertions"]["state_transitions"]):
        candidates = [
            event
            for event in events
            if event["event_type"] == "STATE_TRANSITION"
            and event["state_before"] == transition["from"]
            and event["state_after"] == transition["to"]
            and event["metadata"].get("trigger_event_id") == transition["trigger"]
            and float(event["monotonic_timestamp"]) >= previous_time
            and id(event) not in consumed_events
        ]
        selected = min(
            candidates,
            key=lambda item: float(item["monotonic_timestamp"]),
            default=None,
        )
        trigger_events = [
            event
            for event in events
            if event["metadata"].get("event_id") == transition["trigger"]
            or event["metadata"].get("trigger_id") == transition["trigger"]
        ]
        preceding_triggers = (
            [
                event
                for event in trigger_events
                if selected is not None
                and float(event["monotonic_timestamp"])
                <= float(selected["monotonic_timestamp"])
            ]
            if selected is not None
            else []
        )
        trigger_precedes = bool(preceding_triggers)
        trigger_time = (
            max(
                float(event["monotonic_timestamp"])
                for event in preceding_triggers
            )
            if preceding_triggers
            else origin
        )
        deadline = trigger_time + _duration_seconds(transition["deadline"])
        passed = (
            selected is not None
            and float(selected["monotonic_timestamp"]) <= deadline
            and trigger_precedes
        )
        if selected is not None:
            previous_time = float(selected["monotonic_timestamp"])
            consumed_events.add(id(selected))
        assertions.append(
            _assertion(
                "state_transition.%03d" % index,
                passed,
                {
                    "deadline_monotonic": deadline,
                    "from": transition["from"],
                    "observed_monotonic": (
                        float(selected["monotonic_timestamp"])
                        if selected is not None
                        else None
                    ),
                    "to": transition["to"],
                    "trigger": transition["trigger"],
                    "trigger_monotonic": (
                        trigger_time if preceding_triggers else None
                    ),
                    "trigger_observations": len(trigger_events),
                    "trigger_precedes": trigger_precedes,
                },
            )
        )
    return assertions


def _participant_counts(metadata: Dict[str, Any]) -> Optional[Dict[str, int]]:
    value = metadata.get("participant_counts")
    if not isinstance(value, dict):
        return None
    if not all(
        isinstance(key, str)
        and isinstance(count, int)
        and not isinstance(count, bool)
        and count >= 0
        for key, count in value.items()
    ):
        return None
    return value


def _participant_assertions(
    scenario: Dict[str, Any],
    events: Sequence[Dict[str, Any]],
    origin: float,
) -> List[Dict[str, Any]]:
    assertions: List[Dict[str, Any]] = []
    snapshots = [
        event for event in events if event["event_type"] == "PARTICIPANT_SNAPSHOT"
    ]
    valid_snapshots = [
        event for event in snapshots if _participant_counts(event["metadata"]) is not None
    ]
    latest = valid_snapshots[-1] if valid_snapshots else None
    for cardinality in scenario["assertions"]["participant_cardinality"]:
        participant_id = cardinality["participant_id"]
        observed = (
            _participant_counts(latest["metadata"]).get(participant_id, 0)
            if latest is not None
            else None
        )
        minimum = cardinality["count"]["min"]
        maximum = cardinality["count"]["max"]
        passed = (
            bool(snapshots)
            and len(valid_snapshots) == len(snapshots)
            and observed is not None
            and minimum <= observed <= maximum
        )
        assertions.append(
            _assertion(
                "participant.%s.cardinality" % participant_id,
                passed,
                {"actual": observed, "maximum": maximum, "minimum": minimum},
            )
        )
    cleanup_candidates = [
        event
        for event in events
        if event["event_type"] == "CLEANUP_COMPLETE"
        and event["result"] == "CLEANED"
    ]
    cleanup_events = [
        event
        for event in cleanup_candidates
        if _participant_counts(event["metadata"]) is not None
    ]
    cleanup = cleanup_events[-1] if cleanup_events else None
    cleanup_started = (
        cleanup["metadata"].get("cleanup_started_monotonic")
        if cleanup is not None
        else None
    )
    cleanup_started_valid = (
        isinstance(cleanup_started, (int, float))
        and not isinstance(cleanup_started, bool)
        and math.isfinite(cleanup_started)
        and cleanup_started >= origin
        and cleanup is not None
        and cleanup_started <= float(cleanup["monotonic_timestamp"])
    )
    cleanup_deadline = (
        float(cleanup_started) + _duration_seconds(scenario["cleanup"]["deadline"])
        if cleanup_started_valid
        else origin + _duration_seconds(scenario["cleanup"]["deadline"])
    )
    cleanup_within_deadline = (
        cleanup is not None
        and cleanup_started_valid
        and float(cleanup["monotonic_timestamp"]) <= cleanup_deadline
    )
    absent = scenario["cleanup"]["expected_absent_participants"]
    residual = {}
    if cleanup is not None:
        cleanup_counts = _participant_counts(cleanup["metadata"])
        residual = {
            participant_id: cleanup_counts.get(participant_id, 0)
            for participant_id in absent
            if cleanup_counts.get(participant_id, 0) != 0
        }
        cleanup_time = float(cleanup["monotonic_timestamp"])
        for snapshot in valid_snapshots:
            if float(snapshot["monotonic_timestamp"]) > cleanup_time:
                counts = _participant_counts(snapshot["metadata"])
                for participant_id in absent:
                    if counts.get(participant_id, 0) != 0:
                        residual[participant_id] = counts[participant_id]
    assertions.append(
        _assertion(
            "cleanup.participants_absent",
            len(cleanup_candidates) == 1
            and len(cleanup_events) == 1
            and cleanup_within_deadline
            and not residual,
            {
                "cleanup_candidates": len(cleanup_candidates),
                "cleanup_deadline_monotonic": cleanup_deadline,
                "cleanup_observed": cleanup is not None,
                "cleanup_started_monotonic": (
                    float(cleanup_started) if cleanup_started_valid else None
                ),
                "cleanup_within_deadline": cleanup_within_deadline,
                "expected_absent_participants": absent,
                "residual": residual,
            },
        )
    )
    return assertions


def run_assertions(
    scenario: Any,
    events: Sequence[Dict[str, Any]],
    input_sha256: str,
    initial_errors: Optional[Iterable[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Return a result-schema-shaped document for offline checks."""
    errors = list(initial_errors or [])
    scenario_errors = validate_scenario(scenario)
    errors.extend(
        _error("SCENARIO_%s" % item["code"], item["path"], item["message"])
        for item in scenario_errors
    )
    candidate_id = scenario.get("scenario_id") if isinstance(scenario, dict) else None
    scenario_id = (
        candidate_id
        if isinstance(candidate_id, str) and SCENARIO_ID_RE.fullmatch(candidate_id)
        else "SITL-NORMAL-000"
    )
    if events and any(event.get("scenario_id") != scenario_id for event in events):
        errors.append(
            _error(
                "SCENARIO_MISMATCH",
                "$",
                "every timeline event must match the scenario ID",
            )
        )
    assertions: List[Dict[str, Any]] = []
    if not errors and events:
        origin = _origin_time(events)
        assertions.extend(_ordering_assertions(events))
        assertions.append(_correlation_assertion(events))
        assertions.extend(_event_contract_assertions(scenario, events, origin))
        assertions.extend(_endpoint_assertions(scenario, events))
        assertions.extend(_source_identity_assertions(scenario, events))
        assertions.extend(_state_assertions(scenario, events, origin))
        assertions.extend(_participant_assertions(scenario, events, origin))
    failed = sum(item["status"] == "FAIL" for item in assertions)
    passed = sum(item["status"] == "PASS" for item in assertions)
    errors = sorted(errors, key=lambda item: (item["path"], item["code"], item["message"]))
    assertions = sorted(assertions, key=lambda item: item["assertion_id"])
    return {
        "assertions": assertions,
        "errors": errors,
        "input_sha256": input_sha256,
        "scenario_id": scenario_id,
        "schema_version": SCHEMA_VERSION,
        "status": "PASS" if not errors and failed == 0 and bool(assertions) else "FAIL",
        "summary": {
            "assertions_blocked": 0,
            "assertions_failed": failed,
            "assertions_passed": passed,
            "events_read": len(events),
        },
        "tool": "assert_timeline",
    }


def assert_files(
    scenario_path: Path, timeline_path: Path, input_format: str = "auto"
) -> Dict[str, Any]:
    timeline_bytes = timeline_path.read_bytes()
    with scenario_path.open("r", encoding="utf-8") as stream:
        scenario = json.load(stream)
    events, parse_errors = parse_timeline(timeline_path, input_format)
    return run_assertions(
        scenario,
        events,
        hashlib.sha256(timeline_bytes).hexdigest(),
        parse_errors,
    )


def _fatal_result(scenario_id: str, input_sha256: str, message: str) -> Dict[str, Any]:
    return {
        "assertions": [],
        "errors": [_error("INPUT_ERROR", "$", message)],
        "input_sha256": input_sha256,
        "scenario_id": scenario_id,
        "schema_version": SCHEMA_VERSION,
        "status": "FAIL",
        "summary": {
            "assertions_blocked": 0,
            "assertions_failed": 0,
            "assertions_passed": 0,
            "events_read": 0,
        },
        "tool": "assert_timeline",
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Assert a machine-readable scenario against an offline JSON/JSONL "
            "timeline. PASS is not formal PX4 SITL acceptance."
        )
    )
    parser.add_argument("--scenario", required=True, type=Path, help="scenario JSON path")
    parser.add_argument("--timeline", required=True, type=Path, help="timeline JSON/JSONL path")
    parser.add_argument(
        "--format",
        choices=("auto", "json", "jsonl"),
        default="auto",
        help="timeline input format",
    )
    parser.add_argument("--output", type=Path, help="optional result JSON path")
    args = parser.parse_args(argv)
    try:
        result = assert_files(args.scenario, args.timeline, args.format)
        encoded = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(encoded, encoding="utf-8")
        sys.stdout.write(encoded)
        return 0 if result["status"] == "PASS" else 2
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        digest = "0" * 64
        try:
            if args.timeline.is_file():
                digest = hashlib.sha256(args.timeline.read_bytes()).hexdigest()
        except OSError:
            digest = "0" * 64
        result = _fatal_result(
            "SITL-NORMAL-000",
            digest,
            "%s: %s" % (type(exc).__name__, exc),
        )
        sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        return 3


if __name__ == "__main__":
    sys.exit(main())
