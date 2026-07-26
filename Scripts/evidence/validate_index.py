#!/usr/bin/env python3
"""Validate the non-destructive BoomBoomFly evidence index."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from validate_evidence import (
    EXIT_ENVIRONMENT,
    ValidationIssue,
    contained_path,
    discover_repo_root,
    exit_code_for,
    git_value,
    load_document,
    normalized_origin,
    schema_issues,
    sha256_file,
    validate_record,
)


def _link_issues(entries: Dict[str, Dict[str, Any]]) -> List[ValidationIssue]:
    issues = []
    for evidence_id, entry in entries.items():
        previous_id = entry["supersedes"]
        next_id = entry["superseded_by"]
        if previous_id == evidence_id or next_id == evidence_id:
            issues.append(
                ValidationIssue("policy", "{0}: supersession self-reference".format(evidence_id))
            )
        if previous_id is not None:
            if previous_id not in entries:
                issues.append(
                    ValidationIssue(
                        "policy",
                        "{0}: supersedes missing entry {1}".format(evidence_id, previous_id),
                    )
                )
            elif entries[previous_id]["superseded_by"] != evidence_id:
                issues.append(
                    ValidationIssue(
                        "policy",
                        "{0}: supersedes link is not reciprocal with {1}".format(
                            evidence_id, previous_id
                        ),
                    )
                )
        if next_id is not None:
            if next_id not in entries:
                issues.append(
                    ValidationIssue(
                        "policy",
                        "{0}: superseded_by missing entry {1}".format(evidence_id, next_id),
                    )
                )
            elif entries[next_id]["supersedes"] != evidence_id:
                issues.append(
                    ValidationIssue(
                        "policy",
                        "{0}: superseded_by link is not reciprocal with {1}".format(
                            evidence_id, next_id
                        ),
                    )
                )

    for start_id in entries:
        seen = set()
        cursor = start_id
        while cursor is not None and cursor in entries:
            if cursor in seen:
                issues.append(
                    ValidationIssue(
                        "policy", "supersession cycle detected from {0}".format(start_id)
                    )
                )
                break
            seen.add(cursor)
            cursor = entries[cursor]["supersedes"]
    return issues


def semantic_index_issues(
    index: Dict[str, Any],
    repo_root: Path,
    evidence_schema_path: Path,
    expected_head: str,
) -> List[ValidationIssue]:
    issues = []
    actual_origin = git_value(repo_root, ["config", "--get", "remote.origin.url"])
    if normalized_origin(index["repository"]["origin"]) != normalized_origin(actual_origin):
        issues.append(
            ValidationIssue(
                "policy",
                "index origin mismatch: expected {0}, got {1}".format(
                    actual_origin, index["repository"]["origin"]
                ),
            )
        )

    entries_by_id: Dict[str, Dict[str, Any]] = {}
    seen_paths = set()
    for position, entry in enumerate(index["entries"]):
        evidence_id = entry["evidence_id"]
        label = "entries[{0}] ({1})".format(position, evidence_id)
        if evidence_id in entries_by_id:
            issues.append(ValidationIssue("policy", "{0}: duplicate evidence_id".format(label)))
        else:
            entries_by_id[evidence_id] = entry
        if entry["path"] in seen_paths:
            issues.append(ValidationIssue("policy", "{0}: duplicate evidence path".format(label)))
        seen_paths.add(entry["path"])

        artifact_path, path_error = contained_path(repo_root, entry["path"])
        if path_error:
            issues.append(ValidationIssue("integrity", "{0}: {1}".format(label, path_error)))
        elif artifact_path is None or not artifact_path.is_file():
            issues.append(
                ValidationIssue(
                    "integrity",
                    "{0}: indexed evidence is missing: {1}".format(label, entry["path"]),
                )
            )
        else:
            actual_hash = sha256_file(artifact_path)
            if actual_hash != entry["sha256"]:
                issues.append(
                    ValidationIssue(
                        "integrity",
                        "{0}: SHA-256 mismatch: expected {1}, got {2}".format(
                            label, entry["sha256"], actual_hash
                        ),
                    )
                )

        if entry["known_historical"] and entry["status"] == "current":
            issues.append(
                ValidationIssue(
                    "policy", "{0}: known historical evidence cannot be current".format(label)
                )
            )
        if entry["status"] == "superseded" and entry["superseded_by"] is None:
            issues.append(
                ValidationIssue(
                    "policy", "{0}: superseded status requires superseded_by".format(label)
                )
            )
        if entry["status"] == "current":
            if index["repository"]["root_head"] != expected_head:
                issues.append(
                    ValidationIssue(
                        "policy",
                        "{0}: current index HEAD is stale: expected {1}, got {2}".format(
                            label, expected_head, index["repository"]["root_head"]
                        ),
                    )
                )
            if entry["metadata_path"] is None:
                issues.append(
                    ValidationIssue(
                        "policy", "{0}: current evidence requires metadata_path".format(label)
                    )
                )

        if entry["metadata_path"] is not None:
            metadata_path, metadata_error = contained_path(repo_root, entry["metadata_path"])
            if metadata_error:
                issues.append(
                    ValidationIssue("integrity", "{0}: {1}".format(label, metadata_error))
                )
            elif metadata_path is None or not metadata_path.is_file():
                issues.append(
                    ValidationIssue(
                        "integrity",
                        "{0}: metadata file is missing: {1}".format(
                            label, entry["metadata_path"]
                        ),
                    )
                )
            else:
                metadata = load_document(metadata_path)
                metadata_issues = validate_record(
                    metadata, evidence_schema_path, repo_root, expected_head
                )
                issues.extend(
                    ValidationIssue(
                        issue.category,
                        "{0} metadata: {1}".format(label, issue.message),
                    )
                    for issue in metadata_issues
                )
                if isinstance(metadata, dict):
                    if metadata.get("evidence_id") != evidence_id:
                        issues.append(
                            ValidationIssue(
                                "policy",
                                "{0}: metadata evidence_id does not match index".format(label),
                            )
                        )
                    if metadata.get("status") != entry["status"]:
                        issues.append(
                            ValidationIssue(
                                "policy",
                                "{0}: metadata status does not match index".format(label),
                            )
                        )

    issues.extend(_link_issues(entries_by_id))
    return issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate evidence index schema, links, hashes, and supersession."
    )
    parser.add_argument(
        "--index",
        help="Evidence index JSON/YAML; defaults to docs/evidence/index.yaml",
    )
    parser.add_argument(
        "--repo-root",
        help="Explicit Git repository root; defaults to the root containing this script",
    )
    parser.add_argument(
        "--schema",
        help="Index JSON Schema; defaults to docs/evidence/schemas/evidence_index.schema.json",
    )
    parser.add_argument(
        "--evidence-schema",
        help="Evidence metadata schema; defaults to docs/evidence/schemas/evidence.schema.json",
    )
    parser.add_argument(
        "--expected-head",
        help="Expected root SHA for current entries; defaults to current Git HEAD",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        repo_root = discover_repo_root(args.repo_root)
        index_path = (
            Path(args.index).resolve() if args.index else repo_root / "docs/evidence/index.yaml"
        )
        schema_path = (
            Path(args.schema).resolve()
            if args.schema
            else repo_root / "docs/evidence/schemas/evidence_index.schema.json"
        )
        evidence_schema_path = (
            Path(args.evidence_schema).resolve()
            if args.evidence_schema
            else repo_root / "docs/evidence/schemas/evidence.schema.json"
        )
        expected_head = args.expected_head or git_value(repo_root, ["rev-parse", "HEAD"])
        if len(expected_head) != 40 or any(char not in "0123456789abcdef" for char in expected_head):
            raise RuntimeError("--expected-head must be a lowercase 40-character Git SHA")

        index = load_document(index_path)
        issues = schema_issues(index, schema_path)
        if not issues:
            if not isinstance(index, dict):
                issues = [ValidationIssue("schema", "index must be an object")]
            else:
                issues = semantic_index_issues(
                    index, repo_root, evidence_schema_path, expected_head
                )
    except RuntimeError as exc:
        issues = [ValidationIssue("environment", str(exc))]
        index_path = Path(args.index).resolve() if args.index else None

    code = exit_code_for(issues)
    print(
        json.dumps(
            {
                "validator": "evidence_index",
                "index": str(index_path) if index_path is not None else None,
                "result": "PASS" if code == 0 else "FAIL",
                "exit_code": code,
                "issues": [
                    {"category": issue.category, "message": issue.message} for issue in issues
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return code


if __name__ == "__main__":
    sys.exit(main())
