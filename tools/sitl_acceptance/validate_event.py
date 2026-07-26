#!/usr/bin/env python3
"""Validate offline SITL timeline JSON or JSONL events."""

import argparse
import datetime
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


SCHEMA_VERSION = "1.0.0"
SCENARIO_ID_RE = re.compile(r"^SITL-(NORMAL|FAULT)-[0-9]{3}$")
REQUIRED_FIELDS = {
    "schema_version",
    "timestamp",
    "monotonic_timestamp",
    "scenario_id",
    "event_type",
    "source",
    "target",
    "topic",
    "message_type",
    "correlation_id",
    "state_before",
    "state_after",
    "result",
    "metadata",
}
ALLOWED_RESULTS = {"OBSERVED", "ACCEPTED", "REJECTED", "TIMEOUT", "ERROR", "CLEANED"}


def _error(errors: List[Dict[str, str]], code: str, path: str, message: str) -> None:
    errors.append({"code": code, "message": message, "path": path})


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError:
        return False
    return parsed.tzinfo is not None


def validate_event(event: Any, event_index: int = 0) -> List[Dict[str, str]]:
    """Return stable structural errors for one timeline event."""
    errors: List[Dict[str, str]] = []
    base = "$[%d]" % event_index
    if not isinstance(event, dict):
        return [{"code": "TYPE", "message": "event must be a JSON object", "path": base}]
    for field in sorted(REQUIRED_FIELDS - set(event)):
        _error(errors, "REQUIRED", base + "." + field, "required field is missing")
    for field in sorted(set(event) - REQUIRED_FIELDS):
        _error(errors, "UNKNOWN_FIELD", base + "." + field, "field is not allowed")
    if event.get("schema_version") != SCHEMA_VERSION:
        _error(errors, "SCHEMA_VERSION", base + ".schema_version", "must equal %s" % SCHEMA_VERSION)
    if not _valid_timestamp(event.get("timestamp")):
        _error(errors, "TIMESTAMP", base + ".timestamp", "must be an ISO 8601 timestamp with timezone")
    monotonic = event.get("monotonic_timestamp")
    if (
        not isinstance(monotonic, (int, float))
        or isinstance(monotonic, bool)
        or not math.isfinite(monotonic)
        or monotonic < 0
    ):
        _error(errors, "MONOTONIC_TIMESTAMP", base + ".monotonic_timestamp", "must be finite and non-negative")
    scenario_id = event.get("scenario_id")
    if not isinstance(scenario_id, str) or not SCENARIO_ID_RE.fullmatch(scenario_id):
        _error(errors, "SCENARIO_ID", base + ".scenario_id", "must match SITL-(NORMAL|FAULT)-NNN")
    for field in ("event_type", "source", "target", "correlation_id"):
        if not _nonempty(event.get(field)):
            _error(errors, "TYPE", base + "." + field, "must be a non-empty string")
    for field in ("topic", "message_type", "state_before", "state_after"):
        if not isinstance(event.get(field), str):
            _error(errors, "TYPE", base + "." + field, "must be a string")
    topic = event.get("topic")
    message_type = event.get("message_type")
    if isinstance(topic, str) and topic and not topic.startswith("/"):
        _error(errors, "TOPIC", base + ".topic", "non-empty topic must be absolute")
    if isinstance(topic, str) and isinstance(message_type, str) and bool(topic) != bool(message_type):
        _error(errors, "TOPIC_TYPE_PAIR", base, "topic and message_type must both be empty or both be non-empty")
    if event.get("result") not in ALLOWED_RESULTS:
        _error(errors, "RESULT", base + ".result", "unsupported result")
    metadata = event.get("metadata")
    if not isinstance(metadata, dict):
        _error(errors, "TYPE", base + ".metadata", "must be an object")
    else:
        identity = str(metadata.get("identity_kind", "")).upper()
        synthetic = metadata.get("synthetic") is True or metadata.get("mock") is True
        if synthetic and "PX4" in identity:
            _error(errors, "MOCK_IDENTITY", base + ".metadata", "synthetic source cannot claim PX4 identity")
    return sorted(errors, key=lambda item: (item["path"], item["code"], item["message"]))


def load_events(path: Path, input_format: str = "auto") -> Tuple[List[Any], List[Dict[str, str]]]:
    """Load JSON/JSONL. Parse errors are returned and never treated as warnings."""
    errors: List[Dict[str, str]] = []
    text = path.read_text(encoding="utf-8")
    selected = input_format
    if selected == "auto":
        selected = "jsonl" if path.suffix.lower() == ".jsonl" else "json"
    if selected == "json":
        value = json.loads(text)
        return (value if isinstance(value, list) else [value]), errors
    events: List[Any] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            _error(errors, "BLANK_LINE", "line:%d" % line_number, "blank JSONL records are forbidden")
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            _error(errors, "JSON_PARSE", "line:%d" % line_number, str(exc))
    return events, errors


def validate_events(events: List[Any]) -> List[Dict[str, str]]:
    errors: List[Dict[str, str]] = []
    for index, event in enumerate(events):
        errors.extend(validate_event(event, index))
    return sorted(errors, key=lambda item: (item["path"], item["code"], item["message"]))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate offline SITL timeline event JSON/JSONL.")
    parser.add_argument("--input", required=True, type=Path, help="input JSON or JSONL path")
    parser.add_argument(
        "--format",
        choices=("auto", "json", "jsonl"),
        default="auto",
        help="input format; auto uses the filename suffix",
    )
    parser.add_argument("--output", type=Path, help="optional JSON summary output path")
    args = parser.parse_args(argv)
    try:
        events, errors = load_events(args.input, args.format)
        errors.extend(validate_events(events))
        errors = sorted(errors, key=lambda item: (item["path"], item["code"], item["message"]))
        summary: Dict[str, Any] = {
            "errors": errors,
            "events_read": len(events),
            "input": str(args.input),
            "schema_version": SCHEMA_VERSION,
            "status": "PASS" if not errors else "FAIL",
            "tool": "validate_event",
            "validation_scope": "OFFLINE_EVENT_ONLY",
        }
        encoded = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(encoded, encoding="utf-8")
        sys.stdout.write(encoded)
        return 0 if not errors else 2
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        summary = {
            "errors": [{"code": "INPUT_ERROR", "message": str(exc), "path": str(args.input)}],
            "events_read": 0,
            "input": str(args.input),
            "schema_version": SCHEMA_VERSION,
            "status": "FAIL",
            "tool": "validate_event",
            "validation_scope": "OFFLINE_EVENT_ONLY",
        }
        sys.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        return 3


if __name__ == "__main__":
    sys.exit(main())
