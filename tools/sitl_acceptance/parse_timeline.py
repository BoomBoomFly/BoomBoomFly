#!/usr/bin/env python3
"""Parse and structurally validate an offline SITL event timeline."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if __package__:
    from .validate_event import SCHEMA_VERSION, load_events, validate_events
else:
    from validate_event import SCHEMA_VERSION, load_events, validate_events


def _error(code: str, path: str, message: str) -> Dict[str, str]:
    return {"code": code, "message": message, "path": path}


def parse_timeline(
    path: Path, input_format: str = "auto"
) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """Return validated event objects and stable errors without reordering records."""
    raw_events, errors = load_events(path, input_format)
    errors.extend(validate_events(raw_events))
    events: List[Dict[str, Any]] = [
        event for event in raw_events if isinstance(event, dict)
    ]
    scenario_ids = {
        event.get("scenario_id")
        for event in events
        if isinstance(event.get("scenario_id"), str)
    }
    if len(scenario_ids) > 1:
        errors.append(
            _error(
                "MIXED_SCENARIO",
                "$",
                "one timeline must contain events for exactly one scenario",
            )
        )
    if not raw_events:
        errors.append(_error("EMPTY_TIMELINE", "$", "timeline must contain at least one event"))
    return events, sorted(
        errors, key=lambda item: (item["path"], item["code"], item["message"])
    )


def _write_json(path: Path, document: Dict[str, Any]) -> None:
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, events: List[Dict[str, Any]]) -> None:
    encoded = "".join(
        json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for event in events
    )
    path.write_text(encoded, encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Parse offline SITL JSON/JSONL events without connecting to ROS or "
            "changing their observed order."
        )
    )
    parser.add_argument("--input", required=True, type=Path, help="input JSON or JSONL path")
    parser.add_argument(
        "--format",
        choices=("auto", "json", "jsonl"),
        default="auto",
        help="input format; auto uses the filename suffix",
    )
    parser.add_argument("--output", type=Path, help="optional JSON parse summary path")
    parser.add_argument(
        "--normalized-output",
        type=Path,
        help="optional canonical JSONL path; written only when parsing succeeds",
    )
    args = parser.parse_args(argv)
    try:
        events, errors = parse_timeline(args.input, args.format)
        scenario_ids = sorted(
            {
                str(event.get("scenario_id"))
                for event in events
                if event.get("scenario_id") is not None
            }
        )
        summary: Dict[str, Any] = {
            "errors": errors,
            "events_read": len(events),
            "input": str(args.input),
            "scenario_ids": scenario_ids,
            "schema_version": SCHEMA_VERSION,
            "status": "PASS" if not errors else "FAIL",
            "tool": "parse_timeline",
            "validation_scope": "OFFLINE_TIMELINE_PARSE_ONLY",
        }
        if not errors and args.normalized_output:
            _write_jsonl(args.normalized_output, events)
            summary["normalized_output"] = str(args.normalized_output)
        encoded = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(encoded, encoding="utf-8")
        sys.stdout.write(encoded)
        return 0 if not errors else 2
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        summary = {
            "errors": [
                _error("INPUT_ERROR", str(args.input), "%s: %s" % (type(exc).__name__, exc))
            ],
            "events_read": 0,
            "input": str(args.input),
            "scenario_ids": [],
            "schema_version": SCHEMA_VERSION,
            "status": "FAIL",
            "tool": "parse_timeline",
            "validation_scope": "OFFLINE_TIMELINE_PARSE_ONLY",
        }
        encoded = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        sys.stdout.write(encoded)
        return 3


if __name__ == "__main__":
    sys.exit(main())
