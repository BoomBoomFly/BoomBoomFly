#!/usr/bin/env python3
"""Fail-closed launcher for one Wave 3B offline CI job."""

import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from typing import Dict, List, Mapping, Tuple


EXIT_ENVIRONMENT = 70
EXIT_LOCK = 78
EXIT_UPSTREAM = 79


def load(path: Path) -> Dict[str, object]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError("{} must contain an object".format(path))
    return value


def unresolved_locks(contract: Mapping[str, object]) -> List[str]:
    lock = contract.get("toolchain_lock")
    if not isinstance(lock, dict):
        return ["toolchain_lock"]
    return sorted(key for key, value in lock.items() if not isinstance(value, str) or not value)


def probe_bwrap(contract: Mapping[str, object]) -> Tuple[List[str], Dict[str, object]]:
    execution = contract["execution"]
    evidence: Dict[str, object] = {}
    errors: List[str] = []
    resolved = subprocess.run(
        ["bash", "-c", "command -v bwrap"], check=False,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    evidence["command_v_bwrap"] = {
        "exit_code": resolved.returncode, "stdout": resolved.stdout,
        "stderr": resolved.stderr}
    if resolved.returncode != 0:
        return ["command -v bwrap failed"], evidence
    expected_path = execution["bwrap_path"]
    if resolved.stdout.strip() != expected_path:
        errors.append("bwrap resolved to {}, expected {}".format(
            resolved.stdout.strip(), expected_path))
    version = subprocess.run(
        [expected_path, "--version"], check=False,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    evidence["bwrap_version"] = {
        "exit_code": version.returncode, "stdout": version.stdout,
        "stderr": version.stderr}
    if version.returncode != 0 or version.stdout.strip() != execution["bwrap_version"]:
        errors.append("/usr/bin/bwrap --version differs from the contract")
    capability_command = [
        expected_path, "--unshare-all", "--die-with-parent",
        "--ro-bind", "/usr", "/usr", "--ro-bind", "/bin", "/bin",
        "--ro-bind", "/lib", "/lib", "--ro-bind-try", "/lib64", "/lib64",
        "--proc", "/proc", "--tmpfs", "/tmp", "--", "/bin/true"]
    capability = subprocess.run(
        capability_command, check=False, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True)
    evidence["bwrap_capability"] = {
        "command": capability_command, "exit_code": capability.returncode,
        "stdout": capability.stdout, "stderr": capability.stderr}
    if capability.returncode != 0:
        errors.append("actual bwrap sandbox capability test failed")
    return errors, evidence


def platform_errors(contract: Mapping[str, object]) -> List[str]:
    expected = contract["platform"]
    errors: List[str] = []
    release = {}
    try:
        for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                release[key] = value.strip('"')
    except OSError as exc:
        errors.append("cannot read os-release: {}".format(exc))
    observed = {
        "architecture": platform.machine(),
        "os_release": release.get("VERSION_ID"),
        "python_version": platform.python_version(),
        "ros_distro": os.environ.get("ROS_DISTRO"),
    }
    for key, actual in observed.items():
        if actual != expected[key]:
            errors.append("{}={} expected {}".format(key, actual, expected[key]))
    try:
        import jsonschema  # type: ignore
    except ImportError:
        errors.append("jsonschema is not importable")
    else:
        version = getattr(jsonschema, "__version__", None)
        if version != expected["jsonschema_version"]:
            errors.append("jsonschema={} expected {}".format(
                version, expected["jsonschema_version"]))
        if not hasattr(jsonschema, expected["jsonschema_capability"]):
            errors.append("jsonschema lacks Draft202012Validator")
    return errors


def sandbox_command(root: Path, command: str) -> List[str]:
    """Build a network-unshared command with no device mount or bind."""
    return [
        "/usr/bin/bwrap", "--unshare-all", "--die-with-parent", "--new-session",
        "--ro-bind", "/usr", "/usr", "--ro-bind", "/bin", "/bin",
        "--ro-bind", "/lib", "/lib", "--ro-bind-try", "/lib64", "/lib64",
        "--ro-bind", "/etc", "/etc", "--dir", "/opt", "--dir", "/opt/ros",
        "--ro-bind-try", "/opt/ros/foxy", "/opt/ros/foxy",
        "--proc", "/proc", "--tmpfs", "/tmp", "--dir", "/tmp/home",
        "--ro-bind", str(root), str(root), "--chdir", str(root),
        "--setenv", "HOME", "/tmp/home", "--setenv", "PYTHONDONTWRITEBYTECODE", "1",
        "--setenv", "PYTHONPYCACHEPREFIX", "/tmp/pycache",
        "--", "/bin/bash", "-lc", command]


def write_artifacts(root: Path, job: str, classification: str,
                    diagnostics: List[str], evidence: Mapping[str, object]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "summary.json").write_text(json.dumps(
        {"job": job, "classification": classification}, sort_keys=True) + "\n",
        encoding="utf-8")
    (root / "diagnostics.txt").write_text("\n".join(diagnostics) + "\n", encoding="utf-8")
    (root / "ledger.json").write_text(json.dumps(
        {"job": job, "classification": classification, "evidence": evidence},
        indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one offline Wave 3B CI job.")
    parser.add_argument("--job", required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--contract", type=Path,
                        default=Path("test/ci_design/workflow_contract.json"))
    parser.add_argument("--job-graph", type=Path,
                        default=Path("test/ci_design/job_graph.json"))
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--needs-json", default=os.environ.get("WAVE3B_NEEDS_JSON", "{}"))
    args = parser.parse_args()
    try:
        contract, graph = load(args.contract), load(args.job_graph)
        needs = json.loads(args.needs_json)
        job = next(item for item in graph["jobs"] if item["id"] == args.job)
    except (OSError, ValueError, KeyError, StopIteration, json.JSONDecodeError) as exc:
        write_artifacts(args.artifact_root, args.job, "CONFIGURATION_ERROR", [str(exc)], {})
        return 2
    failed_needs = {key: value.get("result") for key, value in needs.items()
                    if value.get("result") != "success"}
    if failed_needs:
        write_artifacts(args.artifact_root, args.job, "UPSTREAM_GATE_BLOCKED",
                        [json.dumps(failed_needs, sort_keys=True)], {"needs": needs})
        return EXIT_UPSTREAM
    bwrap_errors, evidence = probe_bwrap(contract)
    if bwrap_errors:
        write_artifacts(args.artifact_root, args.job,
                        "BLOCKED_BY_EXECUTION_ENVIRONMENT", bwrap_errors, evidence)
        return EXIT_ENVIRONMENT
    missing = unresolved_locks(contract)
    if missing:
        write_artifacts(args.artifact_root, args.job, "BLOCKED_BY_DEPENDENCY_LOCK",
                        ["unresolved locks: " + ", ".join(missing)], evidence)
        return EXIT_LOCK
    environment_errors = platform_errors(contract)
    if environment_errors:
        write_artifacts(args.artifact_root, args.job,
                        "BLOCKED_BY_EXECUTION_ENVIRONMENT", environment_errors, evidence)
        return EXIT_ENVIRONMENT
    results = []
    for command in job["commands"]:
        completed = subprocess.run(sandbox_command(args.repository_root.resolve(), command),
                                   check=False, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
        results.append({"command": command, "exit_code": completed.returncode,
                        "stdout": completed.stdout, "stderr": completed.stderr})
        if completed.returncode != 0:
            write_artifacts(args.artifact_root, args.job, "GATE_FAILURE",
                            [json.dumps(results, indent=2)], {"bwrap": evidence})
            return completed.returncode or 1
    write_artifacts(args.artifact_root, args.job, "PASS", [], {"results": results})
    return 0


if __name__ == "__main__":
    sys.exit(main())
