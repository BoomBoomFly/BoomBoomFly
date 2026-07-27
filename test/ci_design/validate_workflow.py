#!/usr/bin/env python3
"""Statically validate the Wave 3B local workflow."""

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Dict, List, Mapping, Set


JOB = re.compile(r"^  ([a-z][a-z0-9-]*):\s*$")
USES = re.compile(r"^\s*uses:\s*([^@\s]+)@([0-9a-f]{40})(?:\s+#.*)?$")


def load(path: Path) -> Dict[str, object]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError("contract must be an object")
    return value


def job_ids(text: str) -> Set[str]:
    result: Set[str] = set()
    inside = False
    for line in text.splitlines():
        if line == "jobs:":
            inside = True
            continue
        if inside and line and not line.startswith(" "):
            break
        if inside:
            match = JOB.match(line)
            if match:
                result.add(match.group(1))
    return result


def validate(text: str, contract: Mapping[str, object]) -> List[str]:
    errors: List[str] = []
    if contract.get("document_kind") != "wave3b-local-ci-workflow-contract":
        errors.append("unexpected workflow contract kind")
    if contract.get("workflow_required_remotely") is not False:
        errors.append("workflow must remain non-required remotely")
    platform = contract.get("platform", {})
    frozen_platform = {
        "runner_label": "ubuntu-20.04", "architecture": "x86_64",
        "os_release": "20.04", "python_version": "3.8.10",
        "jsonschema_version": "4.19.2",
        "jsonschema_capability": "Draft202012Validator", "ros_distro": "foxy"}
    for key, value in frozen_platform.items():
        if platform.get(key) != value:
            errors.append("platform.{} must equal {}".format(key, value))
    execution = contract.get("execution", {})
    for key in ("allow_network_in_gate", "allow_device_paths", "allow_hardware",
                "allow_ros_launch"):
        if execution.get(key) is not False:
            errors.append("execution.{} must remain false".format(key))
    if execution.get("bwrap_path") != "/usr/bin/bwrap":
        errors.append("bwrap path must remain /usr/bin/bwrap")
    if execution.get("bwrap_version") != "bubblewrap 0.4.0":
        errors.append("bwrap version contract changed")
    if contract.get("artifact_retention_days") != {
            "summary": 14, "diagnostics": 30, "ledger": 90}:
        errors.append("artifact retention contract changed")
    expected = set(contract["expected_job_ids"])
    actual = job_ids(text)
    if actual != expected:
        errors.append("job IDs differ: " + ", ".join(sorted(actual ^ expected)))
    forbidden = (
        "continue-on-error", "command -v bubblewrap", "/dev", "ros2 launch",
        "roslaunch", "pull_request:", "push:", "schedule:")
    for marker in forbidden:
        if marker.lower() in text.lower():
            errors.append("forbidden workflow marker: " + marker)
    required = (
        "workflow_dispatch:", "permissions:\n  contents: read", "command -v bwrap",
        "/usr/bin/bwrap --version", "python3 Scripts/ci/run_offline_gate.py",
        "retention-days: 14", "retention-days: 30", "retention-days: 90",
        "OFFLINE_SYNTHETIC", "if: ${{ always() }}")
    for marker in required:
        if marker not in text:
            errors.append("missing workflow marker: " + marker)
    runner = platform.get("runner_label")
    if text.count("runs-on: " + runner) != len(expected):
        errors.append("every job must use the frozen runner label")
    for identity in expected:
        if text.count("WAVE3B_JOB_ID: " + identity) != 1:
            errors.append(identity + " must set its exact gate identity once")
    observed: Dict[str, Set[str]] = {}
    for line in text.splitlines():
        if "uses:" not in line:
            continue
        match = USES.match(line)
        if not match:
            errors.append("action is not pinned to a 40-character SHA: " + line.strip())
            continue
        observed.setdefault(match.group(1), set()).add(match.group(2))
    actions = contract["actions"]
    expected_actions = {
        "actions/checkout": actions["checkout"],
        "actions/upload-artifact": actions["upload_artifact"],
    }
    for repository, revision in expected_actions.items():
        if observed.get(repository) != {revision}:
            errors.append(repository + " pin differs from the contract")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Wave 3B workflow statically.")
    parser.add_argument("--workflow", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    args = parser.parse_args()
    try:
        errors = validate(args.workflow.read_text(encoding="utf-8"), load(args.contract))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("ERROR: {}".format(exc), file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print("REJECT: " + error, file=sys.stderr)
        return 1
    print("PASS: Wave 3B local workflow is manual, pinned, and fail-closed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
