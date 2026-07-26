#!/usr/bin/env python3
"""Validate BoomBoomFly evidence metadata without changing the workspace."""

import argparse
import hashlib
import json
import math
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


EXIT_OK = 0
EXIT_SCHEMA = 3
EXIT_INTEGRITY = 4
EXIT_POLICY = 5
EXIT_ENVIRONMENT = 6


class ValidationIssue:
    """One validation failure with a stable category and human-readable text."""

    def __init__(self, category: str, message: str) -> None:
        self.category = category
        self.message = message


def _reject_json_constant(value: str) -> None:
    raise ValueError("non-finite JSON number is forbidden: {0}".format(value))


def load_document(path: Path) -> Any:
    """Load strict JSON or safe YAML, rejecting non-finite numeric values."""

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError("cannot read {0}: {1}".format(path, exc)) from exc

    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            value = json.loads(text, parse_constant=_reject_json_constant)
        except (ValueError, json.JSONDecodeError) as exc:
            raise RuntimeError("invalid JSON in {0}: {1}".format(path, exc)) from exc
    elif suffix in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("PyYAML is required to parse {0}".format(path)) from exc
        try:
            value = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise RuntimeError("invalid YAML in {0}: {1}".format(path, exc)) from exc
    else:
        raise RuntimeError(
            "unsupported document extension for {0}; use .json, .yaml, or .yml".format(path)
        )
    _reject_non_finite(value, path.name)
    return value


def _reject_non_finite(value: Any, location: str) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise RuntimeError("non-finite number at {0}".format(location))
    if isinstance(value, dict):
        for key, child in value.items():
            _reject_non_finite(child, "{0}.{1}".format(location, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_non_finite(child, "{0}[{1}]".format(location, index))


def discover_repo_root(explicit_root: Optional[str]) -> Path:
    """Find and verify the Git root without depending on the current directory."""

    start = Path(explicit_root).resolve() if explicit_root else Path(__file__).resolve().parent
    result = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or "git rev-parse failed"
        raise RuntimeError("cannot determine repository root from {0}: {1}".format(start, detail))
    return Path(result.stdout.strip()).resolve()


def git_value(repo_root: Path, arguments: Sequence[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root)] + list(arguments),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or "git command failed"
        raise RuntimeError("{0}: {1}".format(" ".join(arguments), detail))
    return result.stdout.strip()


def normalized_origin(value: str) -> str:
    """Normalize common HTTPS and SSH GitHub origin spellings for comparison."""

    normalized = value.strip()
    if normalized.startswith("git@github.com:"):
        normalized = "https://github.com/" + normalized[len("git@github.com:") :]
    elif normalized.startswith("ssh://git@github.com/"):
        normalized = "https://github.com/" + normalized[len("ssh://git@github.com/") :]
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    return normalized.rstrip("/").lower()


def schema_issues(document: Any, schema_path: Path) -> List[ValidationIssue]:
    try:
        from jsonschema import Draft7Validator, FormatChecker
        from jsonschema.exceptions import SchemaError
    except ImportError as exc:
        raise RuntimeError("jsonschema is required for schema validation") from exc

    schema = load_document(schema_path)
    try:
        Draft7Validator.check_schema(schema)
    except SchemaError as exc:
        raise RuntimeError("invalid schema {0}: {1}".format(schema_path, exc.message)) from exc
    validator = Draft7Validator(schema, format_checker=FormatChecker())
    issues = []
    for error in sorted(validator.iter_errors(document), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        issues.append(ValidationIssue("schema", "{0}: {1}".format(location, error.message)))
    return issues


def contained_path(repo_root: Path, raw_path: str) -> Tuple[Optional[Path], Optional[str]]:
    candidate_path = Path(raw_path)
    if candidate_path.is_absolute():
        return None, "absolute path is forbidden: {0}".format(raw_path)
    candidate = (repo_root / candidate_path).resolve()
    try:
        candidate.relative_to(repo_root)
    except ValueError:
        return None, "path escapes repository root: {0}".format(raw_path)
    return candidate, None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
    except OSError as exc:
        raise RuntimeError("cannot hash {0}: {1}".format(path, exc)) from exc
    return digest.hexdigest()


def _artifact_issues(repo_root: Path, artifact: Dict[str, Any], label: str) -> List[ValidationIssue]:
    issues = []
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
        issues.append(
            ValidationIssue(
                "integrity",
                "{0}: SHA-256 mismatch for {1}: expected {2}, got {3}".format(
                    label, artifact["path"], artifact["sha256"], actual
                ),
            )
        )
    return issues


def _parse_time(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    return datetime.fromisoformat(normalized)


def semantic_issues(
    document: Dict[str, Any],
    repo_root: Path,
    expected_head: str,
    verify_artifacts: bool = True,
) -> List[ValidationIssue]:
    """Run checks that JSON Schema cannot express."""

    issues = []
    evidence_id = document["evidence_id"]
    if document["supersedes"] == evidence_id or document["superseded_by"] == evidence_id:
        issues.append(ValidationIssue("policy", "evidence cannot supersede itself"))
    if document["supersedes"] is not None and document["supersedes"] == document["superseded_by"]:
        issues.append(ValidationIssue("policy", "supersedes and superseded_by cannot be equal"))

    dependency_names = [item["name"] for item in document["dependency_shas"]]
    if len(dependency_names) != len(set(dependency_names)):
        issues.append(ValidationIssue("policy", "dependency names must be unique"))

    start_time = _parse_time(document["start_time"])
    end_time = _parse_time(document["end_time"])
    if (start_time is None) != (end_time is None):
        issues.append(ValidationIssue("policy", "start_time and end_time must both be set or null"))
    elif start_time is not None and end_time is not None and end_time < start_time:
        issues.append(ValidationIssue("policy", "end_time precedes start_time"))

    cwd, cwd_error = contained_path(repo_root, document["command"]["cwd"])
    if cwd_error:
        issues.append(ValidationIssue("policy", "command.cwd: {0}".format(cwd_error)))
    elif cwd is not None and not cwd.is_dir():
        issues.append(
            ValidationIssue(
                "policy",
                "command.cwd does not name an existing directory: {0}".format(
                    document["command"]["cwd"]
                ),
            )
        )

    if document["status"] == "current":
        repository = document["repository"]
        if repository["root_head"] != expected_head:
            issues.append(
                ValidationIssue(
                    "policy",
                    "current evidence root HEAD is stale: expected {0}, got {1}".format(
                        expected_head, repository["root_head"]
                    ),
                )
            )
        actual_origin = git_value(repo_root, ["config", "--get", "remote.origin.url"])
        if normalized_origin(repository["origin"]) != normalized_origin(actual_origin):
            issues.append(
                ValidationIssue(
                    "policy",
                    "current evidence origin mismatch: expected {0}, got {1}".format(
                        actual_origin, repository["origin"]
                    ),
                )
            )
        if document["start_time"] is None or document["end_time"] is None:
            issues.append(
                ValidationIssue("policy", "current evidence requires start_time and end_time")
            )

    artifacts: List[Tuple[str, Dict[str, Any]]] = []
    if document["stdout_artifact"] is not None:
        artifacts.append(("stdout_artifact", document["stdout_artifact"]))
    if document["stderr_artifact"] is not None:
        artifacts.append(("stderr_artifact", document["stderr_artifact"]))
    artifacts.extend(
        ("artifacts[{0}]".format(index), artifact)
        for index, artifact in enumerate(document["artifacts"])
    )
    if verify_artifacts:
        for label, artifact in artifacts:
            issues.extend(_artifact_issues(repo_root, artifact, label))
    else:
        issues.append(
            ValidationIssue(
                "policy", "artifact hash verification was explicitly disabled; result is UNVERIFIED"
            )
        )
    return issues


def validate_record(
    document: Any,
    schema_path: Path,
    repo_root: Path,
    expected_head: str,
    verify_artifacts: bool = True,
) -> List[ValidationIssue]:
    issues = schema_issues(document, schema_path)
    if issues:
        return issues
    if not isinstance(document, dict):
        return [ValidationIssue("schema", "evidence metadata must be an object")]
    return semantic_issues(document, repo_root, expected_head, verify_artifacts)


def exit_code_for(issues: Iterable[ValidationIssue]) -> int:
    categories = {issue.category for issue in issues}
    if "environment" in categories:
        return EXIT_ENVIRONMENT
    if "policy" in categories:
        return EXIT_POLICY
    if "integrity" in categories:
        return EXIT_INTEGRITY
    if "schema" in categories:
        return EXIT_SCHEMA
    return EXIT_OK


def print_summary(results: List[Dict[str, Any]], exit_code: int) -> None:
    print(
        json.dumps(
            {
                "validator": "evidence",
                "result": "PASS" if exit_code == EXIT_OK else "FAIL",
                "exit_code": exit_code,
                "records": results,
            },
            indent=2,
            sort_keys=True,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate evidence metadata, provenance, paths, and artifact SHA-256 values."
    )
    parser.add_argument("metadata", nargs="+", help="Evidence metadata JSON/YAML file(s)")
    parser.add_argument(
        "--repo-root",
        help="Explicit Git repository root; defaults to the root containing this script",
    )
    parser.add_argument(
        "--schema",
        help="Evidence JSON Schema path; defaults to docs/evidence/schemas/evidence.schema.json",
    )
    parser.add_argument(
        "--expected-head",
        help="Expected 40-character root Git SHA for current evidence; defaults to current HEAD",
    )
    parser.add_argument(
        "--no-artifact-hash-check",
        action="store_true",
        help="Do not hash artifacts; this is fail-closed and returns an UNVERIFIED policy failure",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        repo_root = discover_repo_root(args.repo_root)
        schema_path = (
            Path(args.schema).resolve()
            if args.schema
            else repo_root / "docs/evidence/schemas/evidence.schema.json"
        )
        expected_head = args.expected_head or git_value(repo_root, ["rev-parse", "HEAD"])
        if len(expected_head) != 40 or any(char not in "0123456789abcdef" for char in expected_head):
            raise RuntimeError("--expected-head must be a lowercase 40-character Git SHA")

        all_results = []
        all_issues = []
        for raw_path in args.metadata:
            path = Path(raw_path).resolve()
            document = load_document(path)
            issues = validate_record(
                document,
                schema_path,
                repo_root,
                expected_head,
                verify_artifacts=not args.no_artifact_hash_check,
            )
            all_issues.extend(issues)
            all_results.append(
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
        all_results = [
            {
                "path": None,
                "result": "FAIL",
                "issues": [{"category": issue.category, "message": issue.message}],
            }
        ]
        all_issues = [issue]
    code = exit_code_for(all_issues)
    print_summary(all_results, code)
    return code


if __name__ == "__main__":
    sys.exit(main())
