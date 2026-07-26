#!/usr/bin/env python3
"""Validate BoomBoomFly release and rollback manifests without executing them."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from validate_evidence import (
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


ZERO_SHA256 = "0" * 64
PLACEHOLDER_TOKENS = ("REPLACE", "TBD", "TODO")


def artifact_issues(
    repo_root: Path, artifact: Dict[str, Any], label: str
) -> List[ValidationIssue]:
    candidate, path_error = contained_path(repo_root, artifact["path"])
    if path_error:
        return [ValidationIssue("integrity", "{0}: {1}".format(label, path_error))]
    if candidate is None or not candidate.is_file():
        return [
            ValidationIssue(
                "integrity",
                "{0}: artifact is missing or not a regular file: {1}".format(
                    label, artifact["path"]
                ),
            )
        ]
    actual = sha256_file(candidate)
    if actual != artifact["sha256"]:
        return [
            ValidationIssue(
                "integrity",
                "{0}: SHA-256 mismatch: expected {1}, got {2}".format(
                    label, artifact["sha256"], actual
                ),
            )
        ]
    return []


def has_placeholder(value: str) -> bool:
    upper = value.upper()
    return any(token in upper for token in PLACEHOLDER_TOKENS)


def command_issues(
    repo_root: Path, command: Dict[str, Any], label: str, allow_placeholders: bool
) -> List[ValidationIssue]:
    issues = []
    cwd, path_error = contained_path(repo_root, command["cwd"])
    if path_error:
        issues.append(ValidationIssue("policy", "{0}.cwd: {1}".format(label, path_error)))
    elif cwd is None or not cwd.is_dir():
        issues.append(
            ValidationIssue(
                "policy",
                "{0}.cwd does not name an existing directory: {1}".format(
                    label, command["cwd"]
                ),
            )
        )
    if not allow_placeholders and any(has_placeholder(part) for part in command["argv"]):
        issues.append(ValidationIssue("policy", "{0} contains a placeholder".format(label)))
    return issues


def release_issues(
    manifest: Dict[str, Any], repo_root: Path, expected_head: str
) -> List[ValidationIssue]:
    issues = []
    is_template = manifest["lifecycle"] == "template"
    issues.extend(
        command_issues(
            repo_root,
            manifest["promotion_command"],
            "promotion_command",
            allow_placeholders=is_template,
        )
    )
    if is_template:
        return issues

    repository = manifest["repository"]
    actual_origin = git_value(repo_root, ["config", "--get", "remote.origin.url"])
    if normalized_origin(repository["origin"]) != normalized_origin(actual_origin):
        issues.append(ValidationIssue("policy", "release repository origin mismatch"))
    if manifest["lifecycle"] in ("candidate", "approved"):
        if repository["root_head"] != expected_head:
            issues.append(
                ValidationIssue(
                    "policy",
                    "release root HEAD is stale: expected {0}, got {1}".format(
                        expected_head, repository["root_head"]
                    ),
                )
            )
    dependency_names = [item["name"] for item in manifest["dependency_shas"]]
    if len(dependency_names) != len(set(dependency_names)):
        issues.append(ValidationIssue("policy", "dependency names must be unique"))
    for index, artifact in enumerate(manifest["artifacts"]):
        issues.extend(artifact_issues(repo_root, artifact, "artifacts[{0}]".format(index)))
    issues.extend(
        artifact_issues(repo_root, manifest["rollback_manifest"], "rollback_manifest")
    )
    return issues


def verified_execution_issues(
    manifest: Dict[str, Any], repo_root: Path
) -> List[ValidationIssue]:
    """Bind a verified rollback to independently valid execution metadata."""

    issues = []
    for field, hash_field in (
        ("pre_state_artifact", "pre_state_hash"),
        ("target_state_artifact", "target_state_hash"),
    ):
        artifact = manifest[field]
        if artifact is None:
            issues.append(
                ValidationIssue("policy", "verified rollback requires {0}".format(field))
            )
            continue
        issues.extend(artifact_issues(repo_root, artifact, field))
        if artifact["sha256"] != manifest[hash_field]:
            issues.append(
                ValidationIssue(
                    "policy",
                    "{0}.sha256 must equal {1}".format(field, hash_field),
                )
            )

    reference = manifest["execution_evidence"]
    if reference is None:
        issues.append(
            ValidationIssue("policy", "verified rollback requires execution_evidence")
        )
        return issues
    metadata_artifact = {
        "path": reference["metadata_path"],
        "sha256": reference["sha256"],
    }
    integrity = artifact_issues(
        repo_root, metadata_artifact, "execution_evidence.metadata_path"
    )
    issues.extend(integrity)
    if integrity:
        return issues

    metadata_path, path_error = contained_path(repo_root, reference["metadata_path"])
    if path_error or metadata_path is None:
        return issues
    try:
        metadata = load_document(metadata_path)
        expected_head = git_value(repo_root, ["rev-parse", "HEAD"])
        evidence_schema = repo_root / "docs/evidence/schemas/evidence.schema.json"
        evidence_issues = validate_record(
            metadata, evidence_schema, repo_root, expected_head, verify_artifacts=True
        )
    except RuntimeError as exc:
        return [
            ValidationIssue(
                "environment", "cannot validate execution evidence: {0}".format(exc)
            )
        ]
    issues.extend(
        ValidationIssue(
            issue.category,
            "execution_evidence: {0}".format(issue.message),
        )
        for issue in evidence_issues
    )
    if evidence_issues or not isinstance(metadata, dict):
        return issues

    if metadata["evidence_id"] != reference["evidence_id"]:
        issues.append(ValidationIssue("policy", "execution evidence ID mismatch"))
    if metadata["evidence_type"] != "rollback":
        issues.append(
            ValidationIssue("policy", "execution evidence must have evidence_type=rollback")
        )
    if metadata["status"] != "current":
        issues.append(ValidationIssue("policy", "execution evidence must be current"))
    if metadata["exit_code"] != 0 or metadata["test_result"]["outcome"] != "passed":
        issues.append(ValidationIssue("policy", "execution evidence must record a passing run"))
    if metadata["reviewer"]["state"] != "approved":
        issues.append(ValidationIssue("policy", "execution evidence must be reviewer-approved"))
    if metadata["command"] != manifest["exact_command"]:
        issues.append(
            ValidationIssue("policy", "execution evidence command differs from exact_command")
        )

    recorded_artifacts = {
        (item["path"], item["sha256"]) for item in metadata["artifacts"]
    }
    for label in ("pre_state_artifact", "target_state_artifact", "exact_artifact"):
        artifact = manifest[label]
        if artifact is not None and (artifact["path"], artifact["sha256"]) not in recorded_artifacts:
            issues.append(
                ValidationIssue(
                    "policy", "execution evidence does not bind {0}".format(label)
                )
            )
    return issues


def rollback_issues(manifest: Dict[str, Any], repo_root: Path) -> List[ValidationIssue]:
    issues = []
    is_template = manifest["manifest_state"] == "template"
    issues.extend(
        command_issues(
            repo_root,
            manifest["exact_command"],
            "exact_command",
            allow_placeholders=is_template,
        )
    )
    for index, verification in enumerate(manifest["verification"]):
        issues.extend(
            command_issues(
                repo_root,
                verification["command"],
                "verification[{0}].command".format(index),
                allow_placeholders=is_template,
            )
        )
        if not is_template and has_placeholder(verification["expected"]):
            issues.append(
                ValidationIssue(
                    "policy", "verification[{0}].expected contains a placeholder".format(index)
                )
            )
    if is_template:
        return issues

    if manifest["pre_state_hash"] == ZERO_SHA256:
        issues.append(ValidationIssue("policy", "pre_state_hash is still a template value"))
    if manifest["target_state_hash"] == ZERO_SHA256:
        issues.append(ValidationIssue("policy", "target_state_hash is still a template value"))
    if manifest["exact_artifact"]["sha256"] == ZERO_SHA256:
        issues.append(ValidationIssue("policy", "exact_artifact hash is still a template value"))
    if has_placeholder(manifest["exact_artifact"]["path"]):
        issues.append(ValidationIssue("policy", "exact_artifact path contains a placeholder"))
    if has_placeholder(manifest["stop_condition"]):
        issues.append(ValidationIssue("policy", "stop_condition contains a placeholder"))
    issues.extend(artifact_issues(repo_root, manifest["exact_artifact"], "exact_artifact"))
    if manifest["manifest_state"] in ("executed", "verified"):
        for role in ("operator", "observer"):
            if manifest[role]["identity"] is None or manifest[role]["recorded_at"] is None:
                issues.append(
                    ValidationIssue(
                        "policy", "{0} identity and time are required after execution".format(role)
                    )
                )
    if manifest["manifest_state"] == "verified" and manifest["result"] != "passed":
        issues.append(ValidationIssue("policy", "verified rollback must have result=passed"))
    if manifest["manifest_state"] == "verified":
        issues.extend(verified_execution_issues(manifest, repo_root))
    return issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate release or rollback manifest structure, policy, and hashes."
    )
    parser.add_argument("manifest", nargs="+", help="Manifest JSON/YAML file(s)")
    parser.add_argument(
        "--kind", required=True, choices=("release", "rollback"), help="Manifest schema kind"
    )
    parser.add_argument(
        "--repo-root",
        help="Explicit Git repository root; defaults to the root containing this script",
    )
    parser.add_argument(
        "--schema",
        help="Explicit JSON Schema path; defaults according to --kind",
    )
    parser.add_argument(
        "--expected-head",
        help="Expected root SHA for candidate/approved release; defaults to current Git HEAD",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        repo_root = discover_repo_root(args.repo_root)
        schema_path = (
            Path(args.schema).resolve()
            if args.schema
            else repo_root / "docs/evidence/schemas/{0}.schema.json".format(args.kind)
        )
        expected_head = args.expected_head or git_value(repo_root, ["rev-parse", "HEAD"])
        if len(expected_head) != 40 or any(char not in "0123456789abcdef" for char in expected_head):
            raise RuntimeError("--expected-head must be a lowercase 40-character Git SHA")

        results = []
        all_issues = []
        for raw_path in args.manifest:
            path = Path(raw_path).resolve()
            manifest = load_document(path)
            issues = schema_issues(manifest, schema_path)
            if not issues:
                if not isinstance(manifest, dict):
                    issues = [ValidationIssue("schema", "manifest must be an object")]
                elif args.kind == "release":
                    issues = release_issues(manifest, repo_root, expected_head)
                else:
                    issues = rollback_issues(manifest, repo_root)
            all_issues.extend(issues)
            results.append(
                {
                    "path": str(path),
                    "result": "PASS" if not issues else "FAIL",
                    "issues": [
                        {"category": issue.category, "message": issue.message} for issue in issues
                    ],
                }
            )
    except RuntimeError as exc:
        issue = ValidationIssue("environment", str(exc))
        all_issues = [issue]
        results = [
            {
                "path": None,
                "result": "FAIL",
                "issues": [{"category": issue.category, "message": issue.message}],
            }
        ]

    code = exit_code_for(all_issues)
    print(
        json.dumps(
            {
                "validator": "{0}_manifest".format(args.kind),
                "result": "PASS" if code == 0 else "FAIL",
                "exit_code": code,
                "manifests": results,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return code


if __name__ == "__main__":
    sys.exit(main())
