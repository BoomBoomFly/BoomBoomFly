#!/usr/bin/env python3
"""Validate the Wave 3A CI design without creating or running a workflow.

The validator is standard-library only.  It validates the proposed job graph
and provides deterministic non-zero exits for deliberately broken CI fixtures.
It does not contact GitHub, execute job commands, or claim workflow coverage.
"""

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Dict, Iterable, List, Set


EXPECTED_JOBS = {
    "governance-static",
    "python-unit",
    "dds-boundary",
    "evidence-integrity",
    "sitl-spec-offline",
    "supply-chain-static",
    "dds-build-test",
}
EXPECTED_FIXTURE_KINDS = {
    "manifest",
    "profile",
    "topic",
    "link",
    "schema",
    "secret",
    "license",
}
LOCK_FIELDS = {
    "runner_image_digest",
    "ros_apt_snapshot",
    "python_runtime",
    "colcon_bundle",
    "compiler_bundle",
}
EXACT_SHA = re.compile(r"^[0-9a-f]{40}$")


def load_json(path: Path) -> Dict[str, object]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError("top-level JSON value must be an object")
    return value


def validate_config(config: Dict[str, object]) -> List[str]:
    errors: List[str] = []
    if config.get("document_kind") != "wave3a-ci-design-only":
        errors.append("document_kind must identify design-only configuration")
    if config.get("schema_version") != 1:
        errors.append("schema_version must equal 1")

    platform = config.get("platform_contract")
    if not isinstance(platform, dict):
        errors.append("platform_contract must be an object")
    else:
        required_platform = {
            "os": "ubuntu-20.04",
            "ros_distro": "foxy",
            "python_series": "3.8",
            "jsonschema_capability": "Draft202012Validator",
        }
        for key, expected in required_platform.items():
            if platform.get(key) != expected:
                errors.append(f"platform_contract.{key} must equal {expected}")

    artifact_policy = config.get("artifact_policy")
    if not isinstance(artifact_policy, dict):
        errors.append("artifact_policy must be an object")
    else:
        for field in (
            "success_summary_days",
            "failure_diagnostics_days",
            "machine_readable_ledger_days",
        ):
            value = artifact_policy.get(field)
            if not isinstance(value, int) or value <= 0:
                errors.append(f"artifact_policy.{field} must be a positive integer")

    lock = config.get("toolchain_lock")
    unresolved = config.get("unresolved_workflow_locks")
    if not isinstance(lock, dict):
        errors.append("toolchain_lock must be an object")
        lock = {}
    if not isinstance(unresolved, list) or set(unresolved) != LOCK_FIELDS:
        errors.append("unresolved_workflow_locks must list every required lock")
    for field in LOCK_FIELDS:
        if field not in lock:
            errors.append(f"toolchain_lock is missing {field}")

    workflow_enabled = config.get("workflow_enabled")
    if not isinstance(workflow_enabled, bool):
        errors.append("workflow_enabled must be boolean")
    elif workflow_enabled:
        missing = sorted(field for field in LOCK_FIELDS if not lock.get(field))
        if missing:
            errors.append(
                "workflow cannot be enabled with unresolved locks: "
                + ", ".join(missing)
            )

    fixture_kinds = config.get("negative_fixture_kinds")
    if not isinstance(fixture_kinds, list) or set(fixture_kinds) != EXPECTED_FIXTURE_KINDS:
        errors.append("negative_fixture_kinds must match the seven required kinds")

    jobs = config.get("jobs")
    if not isinstance(jobs, list):
        errors.append("jobs must be an array")
        return errors

    by_id: Dict[str, Dict[str, object]] = {}
    for index, raw_job in enumerate(jobs):
        if not isinstance(raw_job, dict):
            errors.append(f"jobs[{index}] must be an object")
            continue
        job_id = raw_job.get("id")
        if not isinstance(job_id, str) or not job_id:
            errors.append(f"jobs[{index}].id must be a non-empty string")
            continue
        if job_id in by_id:
            errors.append(f"duplicate job id: {job_id}")
        by_id[job_id] = raw_job
        if raw_job.get("fail_closed") is not True:
            errors.append(f"{job_id}: fail_closed must be true")
        if raw_job.get("network") != "disabled":
            errors.append(f"{job_id}: network must be disabled")
        timeout = raw_job.get("timeout_minutes")
        if not isinstance(timeout, int) or timeout <= 0 or timeout > 60:
            errors.append(f"{job_id}: timeout_minutes must be in 1..60")
        commands = raw_job.get("commands")
        if (
            not isinstance(commands, list)
            or not commands
            or not all(isinstance(command, str) and command.strip() for command in commands)
        ):
            errors.append(f"{job_id}: commands must be a non-empty string array")
        elif any("|| true" in command or "--no-verify" in command for command in commands):
            errors.append(f"{job_id}: commands contain a fail-open bypass")
        needs = raw_job.get("needs")
        if not isinstance(needs, list) or not all(
            isinstance(dependency, str) for dependency in needs
        ):
            errors.append(f"{job_id}: needs must be a string array")
        if not isinstance(raw_job.get("artifact_class"), str):
            errors.append(f"{job_id}: artifact_class is required")

    if set(by_id) != EXPECTED_JOBS:
        errors.append(
            "job ids differ from required graph: "
            + ", ".join(sorted(set(by_id) ^ EXPECTED_JOBS))
        )
    errors.extend(_validate_dependencies(by_id))
    return errors


def _validate_dependencies(jobs: Dict[str, Dict[str, object]]) -> List[str]:
    errors: List[str] = []
    for job_id, job in jobs.items():
        for dependency in job.get("needs", []):
            if dependency not in jobs:
                errors.append(f"{job_id}: unknown dependency {dependency}")
            if dependency == job_id:
                errors.append(f"{job_id}: self dependency")

    visiting: Set[str] = set()
    visited: Set[str] = set()

    def visit(job_id: str) -> None:
        if job_id in visited:
            return
        if job_id in visiting:
            errors.append(f"dependency cycle includes {job_id}")
            return
        visiting.add(job_id)
        for dependency in jobs[job_id].get("needs", []):
            if dependency in jobs:
                visit(dependency)
        visiting.remove(job_id)
        visited.add(job_id)

    for job_id in sorted(jobs):
        visit(job_id)
    return errors


def inspect_negative_fixture(fixture: Dict[str, object]) -> List[str]:
    """Return policy violations; every committed invalid fixture must have one."""
    kind = fixture.get("kind")
    payload = fixture.get("payload")
    if kind not in EXPECTED_FIXTURE_KINDS:
        return ["unknown fixture kind"]
    if not isinstance(payload, dict):
        return ["fixture payload must be an object"]

    violations: List[str] = []
    if kind == "manifest":
        version = payload.get("version")
        if not isinstance(version, str) or not EXACT_SHA.fullmatch(version):
            violations.append("manifest version is not an exact 40-character SHA")
        if payload.get("url") != payload.get("expected_url"):
            violations.append("manifest URL differs from the approved source")
    elif kind == "profile":
        active = set(_string_list(payload.get("active_paths")))
        archive = set(_string_list(payload.get("archive_paths")))
        optional = set(_string_list(payload.get("optional_paths")))
        forbidden = set(_string_list(payload.get("forbidden_packages")))
        packages = set(_string_list(payload.get("production_packages")))
        if active & archive or active & optional or archive & optional:
            violations.append("active/archive/optional paths overlap")
        if forbidden & packages:
            violations.append("production profile includes a forbidden package")
    elif kind == "topic":
        if payload.get("actual_topic") != payload.get("expected_topic"):
            violations.append("topic name differs from the frozen contract")
        writer_count = payload.get("writer_count")
        if not isinstance(writer_count, int) or writer_count != 1:
            violations.append("control topic writer cardinality is not exactly one")
        if payload.get("actual_type") != payload.get("expected_type"):
            violations.append("topic type differs from the frozen contract")
    elif kind == "link":
        if payload.get("exists") is not True:
            violations.append("relative documentation link target is missing")
        target = payload.get("target")
        if not isinstance(target, str) or target.startswith("/") or ".." in Path(target).parts:
            violations.append("documentation link escapes the repository")
    elif kind == "schema":
        if payload.get("draft") != "https://json-schema.org/draft/2020-12/schema":
            violations.append("schema draft is not frozen to 2020-12")
        if payload.get("additional_properties") is not False:
            violations.append("schema permits undeclared properties")
        required = set(_string_list(payload.get("required")))
        expected_required = set(_string_list(payload.get("expected_required")))
        if not expected_required or not expected_required.issubset(required):
            violations.append("schema omits required safety fields")
    elif kind == "secret":
        if payload.get("scanner_match") is True:
            violations.append("secret scanner matched fixture content")
        if payload.get("tracked_secret") is True:
            violations.append("tracked file contains secret-like material")
    elif kind == "license":
        if not payload.get("spdx_id"):
            violations.append("dependency has no SPDX license identity")
        if payload.get("policy_allowed") is not True:
            violations.append("dependency license is not policy-approved")
    return violations


def _string_list(value: object) -> Iterable[str]:
    if not isinstance(value, list):
        return ()
    return (item for item in value if isinstance(item, str))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the design-only CI graph or one negative fixture."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--config", type=Path)
    mode.add_argument("--fixture", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        document = load_json(args.config or args.fixture)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.config:
        errors = validate_config(document)
    else:
        errors = inspect_negative_fixture(document)
    if errors:
        for error in errors:
            print(f"REJECT: {error}", file=sys.stderr)
        return 1
    print("PASS: CI design document is internally consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
