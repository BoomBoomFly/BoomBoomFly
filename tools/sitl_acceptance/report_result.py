#!/usr/bin/env python3
"""Generate a result-schema-shaped report from offline scenario assertions."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

if __package__:
    from .assert_timeline import assert_files
else:
    from assert_timeline import assert_files


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate an offline SITL assertion result JSON. A PASS records only "
            "fixture/timeline checks and never closes the formal PX4 contract gate."
        )
    )
    parser.add_argument("--scenario", required=True, type=Path, help="scenario JSON path")
    parser.add_argument("--timeline", required=True, type=Path, help="timeline JSON/JSONL path")
    parser.add_argument("--output", required=True, type=Path, help="result JSON output path")
    parser.add_argument(
        "--format",
        choices=("auto", "json", "jsonl"),
        default="auto",
        help="timeline input format",
    )
    args = parser.parse_args(argv)
    try:
        result = assert_files(args.scenario, args.timeline, args.format)
        result["tool"] = "report_result"
        encoded = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        args.output.write_text(encoded, encoding="utf-8")
        summary: Dict[str, Any] = {
            "assertion_status": result["status"],
            "disclaimer": (
                "Offline result only; it is not evidence that PX4 SITL or a PX4 "
                "publisher contract passed."
            ),
            "output": str(args.output),
            "scenario_id": result["scenario_id"],
            "schema_version": result["schema_version"],
            "status": "PASS" if result["status"] == "PASS" else "FAIL",
            "tool": "report_result",
            "validation_scope": "OFFLINE_ASSERTION_ONLY",
        }
        sys.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        return 0 if result["status"] == "PASS" else 2
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        summary = {
            "errors": [
                {
                    "code": "REPORT_ERROR",
                    "message": "%s: %s" % (type(exc).__name__, exc),
                    "path": str(args.output),
                }
            ],
            "output": str(args.output),
            "status": "FAIL",
            "tool": "report_result",
            "validation_scope": "OFFLINE_ASSERTION_ONLY",
        }
        sys.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        return 3


if __name__ == "__main__":
    sys.exit(main())
