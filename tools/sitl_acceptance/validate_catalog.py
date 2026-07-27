#!/usr/bin/env python3
"""Validate the BoomBoomFly offline SITL scenario catalog."""

import argparse
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional, Set


TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

from validate_scenario import SCHEMA_VERSION, validate_document  # noqa: E402


CATALOG_FIELDS = {"schema_version", "catalog_id", "status", "scenarios"}
ENTRY_FIELDS = {"scenario_id", "kind", "path"}
ALLOWED_STATUS = {
    "PLANNED",
    "STATICALLY_VERIFIED",
    "UNIT_TESTED",
    "BLOCKED",
    "UNVERIFIED",
}
EXPECTED_IDS = {
    *{"SITL-NORMAL-%03d" % index for index in range(1, 13)},
    *{"SITL-FAULT-%03d" % index for index in range(1, 26)},
}


def _error(errors: List[Dict[str, str]], code: str, path: str, message: str) -> None:
    errors.append({"code": code, "message": message, "path": path})


def _inside(base: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(base.resolve())
    except ValueError:
        return False
    return True


def _validate_entry_path(
    catalog_dir: Path,
    raw_path: Any,
    index: int,
    errors: List[Dict[str, str]],
) -> Optional[Path]:
    error_path = "$.scenarios[%d].path" % index
    if not isinstance(raw_path, str) or not raw_path:
        _error(errors, "TYPE", error_path, "must be a non-empty POSIX relative path")
        return None
    posix = PurePosixPath(raw_path)
    if posix.is_absolute() or ".." in posix.parts or posix.suffix != ".json":
        _error(errors, "CATALOG_PATH", error_path, "must be a traversal-free relative JSON path")
        return None
    if len(posix.parts) != 2 or posix.parts[0] not in {"normal", "faults"}:
        _error(errors, "CATALOG_PATH", error_path, "must be under normal/ or faults/")
        return None
    candidate = catalog_dir.joinpath(*posix.parts)
    if not _inside(catalog_dir, candidate):
        _error(errors, "CATALOG_PATH", error_path, "resolved path escapes the catalog directory")
        return None
    return candidate


def validate_catalog(document: Any, catalog_path: Path) -> Dict[str, Any]:
    """Return a stable catalog validation summary."""
    errors: List[Dict[str, str]] = []
    counts: Dict[str, int] = {
        "fault": 0,
        "normal": 0,
        "total": 0,
    }
    status_counts = {status: 0 for status in sorted(ALLOWED_STATUS)}
    if not isinstance(document, dict):
        _error(errors, "TYPE", "$", "catalog must be a JSON object")
        return _result(catalog_path, counts, status_counts, errors)
    for field in sorted(CATALOG_FIELDS - set(document)):
        _error(errors, "REQUIRED", "$." + field, "required field is missing")
    for field in sorted(set(document) - CATALOG_FIELDS):
        _error(errors, "UNKNOWN_FIELD", "$." + field, "field is not allowed")
    if document.get("schema_version") != SCHEMA_VERSION:
        _error(errors, "SCHEMA_VERSION", "$.schema_version", "must equal %s" % SCHEMA_VERSION)
    if not isinstance(document.get("catalog_id"), str) or not document.get("catalog_id"):
        _error(errors, "TYPE", "$.catalog_id", "must be a non-empty string")
    if document.get("status") not in ALLOWED_STATUS:
        _error(errors, "STATUS", "$.status", "unsupported catalog status")

    entries = document.get("scenarios")
    if not isinstance(entries, list):
        _error(errors, "TYPE", "$.scenarios", "must be an array")
        return _result(catalog_path, counts, status_counts, errors)

    catalog_dir = catalog_path.parent
    seen_ids: Set[str] = set()
    seen_paths: Set[str] = set()
    for index, entry in enumerate(entries):
        base = "$.scenarios[%d]" % index
        if not isinstance(entry, dict):
            _error(errors, "TYPE", base, "catalog entry must be an object")
            continue
        for field in sorted(ENTRY_FIELDS - set(entry)):
            _error(errors, "REQUIRED", base + "." + field, "required field is missing")
        for field in sorted(set(entry) - ENTRY_FIELDS):
            _error(errors, "UNKNOWN_FIELD", base + "." + field, "field is not allowed")
        scenario_id = entry.get("scenario_id")
        kind = entry.get("kind")
        if not isinstance(scenario_id, str) or not scenario_id:
            _error(errors, "TYPE", base + ".scenario_id", "must be a non-empty string")
        elif scenario_id in seen_ids:
            _error(errors, "DUPLICATE_ID", base + ".scenario_id", "scenario ID is duplicated")
        else:
            seen_ids.add(scenario_id)
        if kind not in {"normal", "fault"}:
            _error(errors, "KIND", base + ".kind", "must be normal or fault")
        candidate = _validate_entry_path(catalog_dir, entry.get("path"), index, errors)
        raw_path = entry.get("path")
        if isinstance(raw_path, str):
            if raw_path in seen_paths:
                _error(errors, "DUPLICATE_PATH", base + ".path", "scenario path is duplicated")
            seen_paths.add(raw_path)
        if candidate is None:
            continue
        if not candidate.is_file():
            _error(errors, "MISSING_SCENARIO", base + ".path", "referenced scenario does not exist")
            continue
        try:
            scenario = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            _error(errors, "SCENARIO_INPUT", base + ".path", str(exc))
            continue
        scenario_errors = validate_document(scenario, str(candidate))
        for item in scenario_errors:
            _error(
                errors,
                "SCENARIO_" + item["code"],
                base + ":" + item["path"],
                item["message"],
            )
        if scenario.get("scenario_id") != scenario_id:
            _error(errors, "ID_MISMATCH", base + ".scenario_id", "entry and scenario IDs differ")
        if candidate.stem != scenario_id:
            _error(errors, "FILENAME_MISMATCH", base + ".path", "filename must equal scenario ID")
        expected_kind = "normal" if str(scenario_id).startswith("SITL-NORMAL-") else "fault"
        if kind in {"normal", "fault"} and kind != expected_kind:
            _error(errors, "KIND_MISMATCH", base + ".kind", "kind does not match scenario ID")
        directory_kind = "normal" if candidate.parent.name == "normal" else "fault"
        if kind in {"normal", "fault"} and kind != directory_kind:
            _error(errors, "DIRECTORY_MISMATCH", base + ".path", "directory does not match kind")
        if kind in counts:
            counts[kind] += 1
        counts["total"] += 1
        scenario_status = scenario.get("status")
        if scenario_status in status_counts:
            status_counts[scenario_status] += 1

    missing_ids = sorted(EXPECTED_IDS - seen_ids)
    extra_ids = sorted(seen_ids - EXPECTED_IDS)
    for scenario_id in missing_ids:
        _error(errors, "MISSING_REQUIRED_SCENARIO", "$.scenarios", scenario_id)
    for scenario_id in extra_ids:
        _error(errors, "UNEXPECTED_SCENARIO", "$.scenarios", scenario_id)

    discovered = {
        path.relative_to(catalog_dir).as_posix()
        for directory in ("normal", "faults")
        for path in sorted((catalog_dir / directory).glob("*.json"))
    }
    for path in sorted(discovered - seen_paths):
        _error(errors, "UNLISTED_SCENARIO", "$.scenarios", path)
    for path in sorted(seen_paths - discovered):
        _error(errors, "MISSING_SCENARIO", "$.scenarios", path)
    return _result(catalog_path, counts, status_counts, errors)


def _result(
    catalog_path: Path,
    counts: Dict[str, int],
    status_counts: Dict[str, int],
    errors: List[Dict[str, str]],
) -> Dict[str, Any]:
    stable_errors = sorted(errors, key=lambda item: (item["path"], item["code"], item["message"]))
    return {
        "catalog": str(catalog_path),
        "counts": dict(sorted(counts.items())),
        "errors": stable_errors,
        "schema_version": SCHEMA_VERSION,
        "status": "PASS" if not stable_errors else "FAIL",
        "status_counts": dict(sorted(status_counts.items())),
        "tool": "validate_catalog",
        "validation_scope": "OFFLINE_SPEC_ONLY",
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the offline SITL scenario catalog.")
    parser.add_argument("--catalog", required=True, type=Path, help="catalog JSON path")
    parser.add_argument("--output", type=Path, help="optional JSON summary output path")
    args = parser.parse_args(argv)
    try:
        document = json.loads(args.catalog.read_text(encoding="utf-8"))
        summary = validate_catalog(document, args.catalog)
        encoded = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(encoded, encoding="utf-8")
        sys.stdout.write(encoded)
        return 0 if summary["status"] == "PASS" else 2
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        summary = {
            "catalog": str(args.catalog),
            "counts": {"fault": 0, "normal": 0, "total": 0},
            "errors": [{"code": "INPUT_ERROR", "message": str(exc), "path": str(args.catalog)}],
            "schema_version": SCHEMA_VERSION,
            "status": "FAIL",
            "status_counts": {},
            "tool": "validate_catalog",
            "validation_scope": "OFFLINE_SPEC_ONLY",
        }
        sys.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        return 3


if __name__ == "__main__":
    sys.exit(main())
