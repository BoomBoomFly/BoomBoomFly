"""Shared helpers for synthetic-only SITL acceptance fixtures."""

import copy
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[1]
TOOLS_DIR = REPO_ROOT / "tools" / "sitl_acceptance"
FIXTURE_DIR = TEST_DIR / "fixtures"
VALID_DIR = FIXTURE_DIR / "valid"
INVALID_DIR = FIXTURE_DIR / "invalid"

if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))


def load_json(path: Path) -> Any:
    """Load one UTF-8 JSON fixture."""
    return json.loads(path.read_text(encoding="utf-8"))


def load_scenario() -> Dict[str, Any]:
    """Return a fresh copy of the synthetic baseline scenario."""
    return copy.deepcopy(load_json(VALID_DIR / "synthetic_scenario.json"))


def load_timeline() -> List[Dict[str, Any]]:
    """Return the synthetic baseline JSONL records in their recorded order."""
    records: List[Dict[str, Any]] = []
    text = (VALID_DIR / "synthetic_timeline.jsonl").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line:
            records.append(json.loads(line))
    return records


def load_cases(name: str) -> List[Dict[str, Any]]:
    """Load declarative negative mutations."""
    value = load_json(INVALID_DIR / name)
    if not isinstance(value, list):
        raise ValueError("case fixture must be an array: %s" % name)
    return value


def event_by_id(events: List[Dict[str, Any]], event_id: str) -> Dict[str, Any]:
    """Return the synthetic event carrying the requested specification ID."""
    for event in events:
        if event.get("metadata", {}).get("event_id") == event_id:
            return event
    raise KeyError(event_id)


def apply_scenario_mutation(
    scenario: Dict[str, Any], mutation: Dict[str, Any]
) -> Dict[str, Any]:
    """Apply one bounded, fixture-declared negative scenario mutation."""
    result = copy.deepcopy(scenario)
    operation = mutation["operation"]
    value = mutation.get("value")
    if operation == "remove_scenario_id":
        result.pop("scenario_id")
    elif operation == "duplicate_expected_event_id":
        duplicate = copy.deepcopy(result["expected_events"][0])
        duplicate["event_type"] = "SYNTHETIC_DUPLICATE_EVENT"
        result["expected_events"].append(duplicate)
    elif operation == "remove_expected_deadline":
        result["expected_events"][0].pop("deadline")
    elif operation == "timeout_without_unit":
        result["timeouts"][0]["duration"] = value
    elif operation == "unknown_dependency":
        result["dependencies"] = [value]
    elif operation == "remove_expected_source":
        result["expected_events"][0].pop("source")
    elif operation == "malformed_forbidden_event":
        result["forbidden_events"][0] = value
    elif operation == "illegal_status":
        result["status"] = value
    elif operation == "blocked_without_blocker":
        result["status"] = "BLOCKED"
        result["dependencies"] = []
    elif operation == "mock_claims_px4":
        result["source_identity"]["bindings"][0]["expected"] = value
    elif operation == "hardware_path":
        result["limitations"].append(value)
    elif operation == "serial_transport":
        result["profile"]["transport"] = value
    elif operation == "firmware_operation":
        result["preconditions"].append(value)
    elif operation == "real_hardware_arm":
        result["preconditions"].append(value)
    elif operation == "forbidden_status":
        result["status"] = value
    else:
        raise ValueError("unknown scenario mutation: %s" % operation)
    return result


def apply_timeline_mutation(
    events: List[Dict[str, Any]], mutation: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Apply one bounded, fixture-declared negative timeline mutation."""
    result = copy.deepcopy(events)
    operation = mutation["operation"]
    if operation == "wall_timestamp_rollback":
        result[1]["timestamp"] = "2025-12-31T23:59:59Z"
    elif operation == "monotonic_rollback":
        result[2]["monotonic_timestamp"] = 0.5
    elif operation == "correlation_mismatch":
        result[-1]["correlation_id"] = "synthetic-unclosed-other"
    elif operation == "deadline_exceeded":
        for index, event in enumerate(result[1:], 1):
            event["monotonic_timestamp"] = 5.0 + index
            event["timestamp"] = "2026-01-01T00:00:%02dZ" % (5 + index)
    elif operation == "forbidden_event":
        forbidden = copy.deepcopy(result[1])
        forbidden.update(
            {
                "event_type": "SYNTHETIC_FORBIDDEN_EVENT",
                "monotonic_timestamp": 1.5,
                "timestamp": "2026-01-01T00:00:01.500000Z",
            }
        )
        forbidden["metadata"] = {
            "event_id": "SYN-F01",
            "correlation_phase": "MEMBER",
            "fixture_scope": "SYNTHETIC_OFFLINE_FIXTURE",
            "synthetic": True,
        }
        result.insert(2, forbidden)
    elif operation == "missing_cleanup":
        result.pop()
    elif operation == "publisher_count":
        event_by_id(result, "SYN-E02")["metadata"]["publishers"] = [
            "synthetic_harness",
            "synthetic_duplicate",
        ]
    elif operation == "source_identity":
        event_by_id(result, "SYN-E01")["metadata"]["observed_identity"] = (
            "WRONG_SYNTHETIC_IDENTITY"
        )
    elif operation == "expected_event_source":
        event_by_id(result, "SYN-E02")["source"] = "wrong_synthetic_source"
    elif operation == "state_transition_order":
        first = event_by_id(result, "SYN-E03")
        second = event_by_id(result, "SYN-E04")
        first["monotonic_timestamp"] = 3.0
        first["timestamp"] = "2026-01-01T00:00:03Z"
        second["monotonic_timestamp"] = 2.5
        second["timestamp"] = "2026-01-01T00:00:02.500000Z"
        result.sort(key=lambda event: event["monotonic_timestamp"])
    elif operation == "duplicate_expected_event":
        duplicate = copy.deepcopy(event_by_id(result, "SYN-E02"))
        duplicate["monotonic_timestamp"] = 1.5
        duplicate["timestamp"] = "2026-01-01T00:00:01.500000Z"
        duplicate["metadata"]["correlation_phase"] = "MEMBER"
        result.append(duplicate)
        result.sort(key=lambda event: event["monotonic_timestamp"])
    else:
        raise ValueError("unknown timeline mutation: %s" % operation)
    return result
