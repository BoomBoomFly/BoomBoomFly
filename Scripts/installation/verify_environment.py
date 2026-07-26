#!/usr/bin/env python3
"""Validate or capture the BoomBoomFly environment/toolchain inventory."""

import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple


EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE_OR_IO = 2
EXIT_PROBE = 3
STATUS_VALUES = {"present", "missing", "unverified"}
REQUIREMENT_VALUES = {"required", "optional"}
HEX40 = re.compile(r"^[0-9a-f]{40}$")


class InventoryError(ValueError):
    """Raised for a malformed inventory."""


def run_command(argv: Sequence[str], cwd: Optional[Path] = None) -> Dict[str, Any]:
    command = [str(item) for item in argv]
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=False,
        )
        return {
            "command": command,
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except FileNotFoundError as exc:
        return {
            "command": command,
            "exit_code": 127,
            "stdout": "",
            "stderr": str(exc),
        }


def discover_repository_root(explicit_root: Optional[str]) -> Path:
    if explicit_root:
        root = Path(explicit_root).expanduser().resolve()
        if not root.is_dir():
            raise InventoryError("repository root is not a directory: {}".format(root))
        return root

    script_dir = Path(__file__).resolve().parent
    probe = run_command(["git", "-C", str(script_dir), "rev-parse", "--show-toplevel"])
    if probe["exit_code"] != 0:
        raise InventoryError(
            "cannot discover repository root with git: {}".format(
                probe["stderr"].strip()
            )
        )
    return Path(probe["stdout"].strip()).resolve()


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as stream:
            return json.load(stream)
    except FileNotFoundError:
        raise InventoryError("missing JSON file: {}".format(path))
    except (OSError, json.JSONDecodeError) as exc:
        raise InventoryError("cannot read JSON file {}: {}".format(path, exc))


def validate_json_schema(document: Any, schema: Any, label: str) -> None:
    try:
        import jsonschema
    except ImportError:
        raise InventoryError("jsonschema is required to validate {}".format(label))
    try:
        validator_class = jsonschema.validators.validator_for(schema)
        validator_class.check_schema(schema)
        errors = sorted(
            validator_class(schema, format_checker=jsonschema.FormatChecker()).iter_errors(
                document
            ),
            key=lambda item: list(item.absolute_path),
        )
    except jsonschema.exceptions.SchemaError as exc:
        raise InventoryError("invalid {} schema: {}".format(label, exc.message))
    if errors:
        location = ".".join(str(item) for item in errors[0].absolute_path) or "<root>"
        raise InventoryError(
            "{} schema violation at {}: {}".format(label, location, errors[0].message)
        )


def require_keys(value: Dict[str, Any], keys: Sequence[str], context: str) -> None:
    missing = [key for key in keys if key not in value]
    if missing:
        raise InventoryError(
            "{} missing required fields: {}".format(context, ", ".join(missing))
        )


def reject_moving_latest(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            reject_moving_latest(child, "{}.{}".format(path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_moving_latest(child, "{}[{}]".format(path, index))
    elif isinstance(value, str) and value.strip().lower() == "latest":
        raise InventoryError("{} uses forbidden moving version 'latest'".format(path))


def validate_probe(probe: Any, context: str) -> None:
    if not isinstance(probe, dict):
        raise InventoryError("{} must be an object".format(context))
    require_keys(
        probe,
        [
            "name",
            "requirement",
            "required_for",
            "status",
            "version",
            "command",
            "exit_code",
            "stdout",
            "stderr",
            "reason",
        ],
        context,
    )
    if probe["requirement"] not in REQUIREMENT_VALUES:
        raise InventoryError("{} has invalid requirement".format(context))
    if probe["status"] not in STATUS_VALUES:
        raise InventoryError("{} has invalid status".format(context))
    if (
        not isinstance(probe["required_for"], list)
        or not probe["required_for"]
        or not all(isinstance(item, str) and item for item in probe["required_for"])
    ):
        raise InventoryError("{} required_for must be a non-empty string array".format(context))
    if (
        not isinstance(probe["command"], list)
        or not probe["command"]
        or not all(isinstance(item, str) for item in probe["command"])
    ):
        raise InventoryError("{} command must be a non-empty argv array".format(context))
    if not isinstance(probe["exit_code"], int):
        raise InventoryError("{} exit_code must be an integer".format(context))
    if not isinstance(probe["stdout"], str) or not isinstance(probe["stderr"], str):
        raise InventoryError("{} stdout/stderr must be strings".format(context))
    if not isinstance(probe["reason"], str):
        raise InventoryError("{} reason must be a string".format(context))

    status = probe["status"]
    version = probe["version"]
    if status == "present":
        if probe["exit_code"] != 0:
            raise InventoryError("{} present probe must exit zero".format(context))
        if not isinstance(version, str) or not version.strip():
            raise InventoryError("{} present probe needs an exact version".format(context))
    elif status == "missing":
        if probe["exit_code"] == 0:
            raise InventoryError("{} missing probe must exit non-zero".format(context))
        if version is not None:
            raise InventoryError("{} missing probe version must be null".format(context))
    else:
        if not probe["reason"].strip():
            raise InventoryError("{} unverified probe needs a reason".format(context))


def validate_environment(document: Any) -> None:
    if not isinstance(document, dict):
        raise InventoryError("environment inventory must be an object")
    require_keys(
        document,
        [
            "schema_version",
            "environment_id",
            "captured_at",
            "repository",
            "platform",
            "ros",
            "tools",
            "px4_source",
            "limitations",
        ],
        "environment inventory",
    )
    reject_moving_latest(document)
    repository = document["repository"]
    if not isinstance(repository, dict):
        raise InventoryError("repository must be an object")
    require_keys(repository, ["origin", "branch", "head"], "repository")
    if not HEX40.match(repository["head"]):
        raise InventoryError("repository.head must be a lowercase 40-hex SHA")

    platform = document["platform"]
    if not isinstance(platform, dict):
        raise InventoryError("platform must be an object")
    require_keys(platform, ["os", "kernel", "architecture"], "platform")
    for name in ("os", "kernel", "architecture"):
        validate_probe(platform[name], "platform.{}".format(name))

    ros = document["ros"]
    if not isinstance(ros, dict):
        raise InventoryError("ros must be an object")
    require_keys(ros, ["distribution", "packages"], "ros")
    validate_probe(ros["distribution"], "ros.distribution")
    if not isinstance(ros["packages"], list):
        raise InventoryError("ros.packages must be an array")
    for index, probe in enumerate(ros["packages"]):
        validate_probe(probe, "ros.packages[{}]".format(index))

    if not isinstance(document["tools"], list) or not document["tools"]:
        raise InventoryError("tools must be a non-empty array")
    names = set()
    for index, probe in enumerate(document["tools"]):
        validate_probe(probe, "tools[{}]".format(index))
        if probe["name"] in names:
            raise InventoryError("duplicate tool name: {}".format(probe["name"]))
        names.add(probe["name"])

    px4 = document["px4_source"]
    if not isinstance(px4, dict):
        raise InventoryError("px4_source must be an object")
    require_keys(
        px4,
        [
            "managed_workspace",
            "host_search_status",
            "host_search_reason",
            "submodules",
        ],
        "px4_source",
    )
    validate_probe(px4["managed_workspace"], "px4_source.managed_workspace")
    validate_probe(px4["submodules"], "px4_source.submodules")
    if px4["host_search_status"] not in STATUS_VALUES:
        raise InventoryError("px4_source.host_search_status is invalid")
    if px4["host_search_status"] == "unverified" and not px4["host_search_reason"]:
        raise InventoryError("unverified host PX4 search requires a reason")
    if not isinstance(document["limitations"], list):
        raise InventoryError("limitations must be an array")


def validate_px4_lock(document: Any) -> None:
    if not isinstance(document, dict):
        raise InventoryError("PX4 lock template must be an object")
    require_keys(
        document,
        [
            "schema_version",
            "lock_id",
            "template",
            "status",
            "source",
            "submodules",
            "toolchain",
            "blockers",
        ],
        "PX4 lock",
    )
    reject_moving_latest(document)
    if document["template"] is not True:
        raise InventoryError("PX4 lock placeholder must keep template=true")
    if document["status"] != "unverified":
        raise InventoryError("PX4 lock template cannot claim locked/current status")
    source = document["source"]
    if not isinstance(source, dict):
        raise InventoryError("PX4 lock source must be an object")
    require_keys(source, ["origin", "commit", "ref"], "PX4 lock source")
    if source["commit"] is not None and not HEX40.match(source["commit"]):
        raise InventoryError("PX4 source commit must be null or lowercase 40-hex")
    if not isinstance(document["submodules"], list):
        raise InventoryError("PX4 lock submodules must be an array")
    for index, item in enumerate(document["submodules"]):
        if not isinstance(item, dict):
            raise InventoryError("PX4 submodule {} must be an object".format(index))
        require_keys(item, ["path", "origin", "commit"], "PX4 submodule")
        if not HEX40.match(item["commit"]):
            raise InventoryError("PX4 submodule commit must be lowercase 40-hex")
    if not isinstance(document["toolchain"], dict):
        raise InventoryError("PX4 lock toolchain must be an object")
    if not isinstance(document["blockers"], list) or not document["blockers"]:
        raise InventoryError("PX4 lock template must list blockers")


def probe_record(
    name: str,
    requirement: str,
    required_for: Sequence[str],
    result: Dict[str, Any],
    version: Optional[str],
    status: Optional[str] = None,
    reason: str = "",
) -> Dict[str, Any]:
    if status is None:
        status = "present" if result["exit_code"] == 0 else "missing"
    return {
        "name": name,
        "requirement": requirement,
        "required_for": list(required_for),
        "status": status,
        "version": version,
        "command": result["command"],
        "exit_code": result["exit_code"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "reason": reason,
    }


def first_line(value: str) -> Optional[str]:
    lines = value.strip().splitlines()
    return lines[0] if lines else None


def parse_os_release(raw: str) -> Optional[str]:
    for line in raw.splitlines():
        if line.startswith("PRETTY_NAME="):
            return line.split("=", 1)[1].strip().strip('"')
    return None


def tool_version_probe(
    name: str,
    argv: Sequence[str],
    requirement: str,
    required_for: Sequence[str],
    parser=first_line,
) -> Dict[str, Any]:
    result = run_command(argv)
    version = parser(result["stdout"]) if result["exit_code"] == 0 else None
    status = "present" if result["exit_code"] == 0 and version else "missing"
    reason = "" if status == "present" else "tool or exact version output is unavailable"
    return probe_record(
        name, requirement, required_for, result, version, status=status, reason=reason
    )


def probe_micro_xrce_agent() -> Dict[str, Any]:
    result = run_command(["which", "MicroXRCEAgent"])
    if result["exit_code"] != 0:
        return probe_record(
            "MicroXRCEAgent",
            "required",
            ["BBF-NEXT-T02"],
            result,
            None,
            status="missing",
            reason="binary is absent from PATH; it was not executed",
        )
    path = result["stdout"].strip()
    owner = run_command(["dpkg-query", "-S", path])
    combined = {
        "command": result["command"] + [";", "dpkg-query", "-S", path],
        "exit_code": owner["exit_code"],
        "stdout": result["stdout"] + owner["stdout"],
        "stderr": result["stderr"] + owner["stderr"],
    }
    return probe_record(
        "MicroXRCEAgent",
        "required",
        ["BBF-NEXT-T02"],
        combined,
        None,
        status="unverified",
        reason="binary exists but was deliberately not executed; package version is not proven",
    )


def managed_px4_probe(root: Path, explicit_source: Optional[str]) -> Dict[str, Any]:
    if explicit_source:
        candidates = [Path(explicit_source).expanduser().resolve()]
    else:
        candidates = [root / "PX4-Autopilot", root / "src" / "PX4-Autopilot"]
    selected = next((candidate for candidate in candidates if candidate.is_dir()), None)
    command = ["managed-directory-scan"] + [str(candidate) for candidate in candidates]
    if selected is None:
        managed_result = {
            "command": command,
            "exit_code": 1,
            "stdout": "",
            "stderr": "no managed PX4-Autopilot directory found",
        }
        managed = probe_record(
            "PX4-Autopilot source",
            "required",
            ["BBF-NEXT-T02"],
            managed_result,
            None,
            status="missing",
            reason="PX4 source is absent from the managed workspace candidates",
        )
        submodule_result = {
            "command": ["git", "-C", "<PX4_SOURCE>", "submodule", "status", "--recursive"],
            "exit_code": 1,
            "stdout": "",
            "stderr": "PX4 source is missing",
        }
        submodules = probe_record(
            "PX4 recursive submodules",
            "required",
            ["BBF-NEXT-T02"],
            submodule_result,
            None,
            status="unverified",
            reason="submodule state cannot be checked without PX4 source",
        )
    else:
        head_result = run_command(["git", "-C", str(selected), "rev-parse", "HEAD"])
        head = head_result["stdout"].strip() if head_result["exit_code"] == 0 else None
        status = "present" if head and HEX40.match(head) else "unverified"
        managed = probe_record(
            "PX4-Autopilot source",
            "required",
            ["BBF-NEXT-T02"],
            head_result,
            head,
            status=status,
            reason="" if status == "present" else "PX4 Git identity is not verifiable",
        )
        submodule_result = run_command(
            ["git", "-C", str(selected), "submodule", "status", "--recursive"]
        )
        submodules = probe_record(
            "PX4 recursive submodules",
            "required",
            ["BBF-NEXT-T02"],
            submodule_result,
            "recursive-status-recorded" if submodule_result["exit_code"] == 0 else None,
            status="present" if submodule_result["exit_code"] == 0 else "unverified",
            reason=(
                ""
                if submodule_result["exit_code"] == 0
                else "recursive submodule state could not be read"
            ),
        )
    return {
        "managed_workspace": managed,
        "host_search_status": "unverified",
        "host_search_reason": (
            "capture is intentionally bounded to managed or explicitly supplied paths"
        ),
        "submodules": submodules,
    }


def capture_environment(root: Path, px4_source: Optional[str]) -> Dict[str, Any]:
    origin = run_command(["git", "-C", str(root), "remote", "get-url", "origin"])
    branch = run_command(["git", "-C", str(root), "branch", "--show-current"])
    head = run_command(["git", "-C", str(root), "rev-parse", "HEAD"])
    if any(item["exit_code"] != 0 for item in (origin, branch, head)):
        raise InventoryError("repository identity probes failed")

    os_result = run_command(["cat", "/etc/os-release"])
    kernel_result = run_command(["uname", "-r"])
    arch_result = run_command(["uname", "-m"])
    ros_result = run_command(["printenv", "ROS_DISTRO"])

    ros_packages = []
    for package in (
        "ros-foxy-ros-core",
        "ros-foxy-ros-base",
        "ros-foxy-rclcpp",
        "ros-foxy-rmw-fastrtps-cpp",
    ):
        result = run_command(["dpkg-query", "-W", "-f=${Version}\\n", package])
        ros_packages.append(
            probe_record(
                package,
                "required",
                ["dds-only-build"],
                result,
                first_line(result["stdout"]) if result["exit_code"] == 0 else None,
                reason="" if result["exit_code"] == 0 else "ROS package is missing",
            )
        )

    tools = [
        tool_version_probe(
            "python3", [sys.executable, "--version"], "required", ["wave1-validation"]
        ),
        tool_version_probe("git", ["git", "--version"], "required", ["workspace-restore"]),
        tool_version_probe(
            "colcon",
            [
                sys.executable,
                "-c",
                "import importlib.metadata as m; print(m.version('colcon-core'))",
            ],
            "required",
            ["dds-only-build"],
        ),
        tool_version_probe("cmake", ["cmake", "--version"], "required", ["dds-only-build"]),
        tool_version_probe("ninja", ["ninja", "--version"], "optional", ["BBF-NEXT-T02"]),
        tool_version_probe("gcc", ["gcc", "-dumpfullversion"], "required", ["dds-only-build"]),
        tool_version_probe("g++", ["g++", "-dumpfullversion"], "required", ["dds-only-build"]),
        tool_version_probe(
            "arm-none-eabi-gcc",
            ["arm-none-eabi-gcc", "--version"],
            "required",
            ["BBF-NEXT-T02"],
        ),
        tool_version_probe(
            "arm-none-eabi-g++",
            ["arm-none-eabi-g++", "--version"],
            "required",
            ["BBF-NEXT-T02"],
        ),
        probe_micro_xrce_agent(),
    ]

    return {
        "schema_version": "1.0.0",
        "environment_id": "bbf-environment-{}".format(
            datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        ),
        "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "repository": {
            "origin": origin["stdout"].strip(),
            "branch": branch["stdout"].strip() or "(detached)",
            "head": head["stdout"].strip(),
        },
        "platform": {
            "os": probe_record(
                "operating_system",
                "required",
                ["dds-only-build"],
                os_result,
                parse_os_release(os_result["stdout"]),
                reason="" if os_result["exit_code"] == 0 else "OS release is unavailable",
            ),
            "kernel": probe_record(
                "kernel",
                "required",
                ["environment-identity"],
                kernel_result,
                first_line(kernel_result["stdout"]),
                reason="" if kernel_result["exit_code"] == 0 else "kernel is unavailable",
            ),
            "architecture": probe_record(
                "architecture",
                "required",
                ["dds-only-build"],
                arch_result,
                first_line(arch_result["stdout"]),
                reason="" if arch_result["exit_code"] == 0 else "architecture is unavailable",
            ),
        },
        "ros": {
            "distribution": probe_record(
                "ROS_DISTRO",
                "required",
                ["dds-only-build"],
                ros_result,
                first_line(ros_result["stdout"]) if ros_result["exit_code"] == 0 else None,
                reason="" if ros_result["exit_code"] == 0 else "ROS_DISTRO is not set",
            ),
            "packages": ros_packages,
        },
        "tools": tools,
        "px4_source": managed_px4_probe(root, px4_source),
        "limitations": [
            "This inventory is a host snapshot, not an apt repository snapshot or container digest.",
            "PX4 host-wide discovery is unverified; only managed or explicit paths are inspected.",
            "MicroXRCEAgent is never executed by this verifier.",
        ],
    }


def _normalized_probe_command(name: str, command: Sequence[str]) -> Tuple[str, ...]:
    """Normalize host paths while preserving the exact probe operation."""
    normalized = list(command)
    if name == "submodules" and len(normalized) >= 3 and normalized[1] == "-C":
        normalized[2] = "<PX4_SOURCE>"
    elif name == "managed_workspace" and normalized[:1] == ["managed-directory-scan"]:
        normalized = ["managed-directory-scan"] + [
            "<PX4_CANDIDATE_{}>".format(index)
            for index, unused in enumerate(normalized[1:], start=1)
        ]
    return tuple(normalized)


def _normalized_probe_stdout(name: str, stdout: str) -> Tuple[str, ...]:
    """Return stable lines; recursive submodule output is a semantic list."""
    lines = tuple(line.rstrip() for line in stdout.splitlines() if line.strip())
    return tuple(sorted(lines)) if name == "submodules" else lines


def compare_px4_probe(
    name: str, expected: Dict[str, Any], actual: Dict[str, Any]
) -> List[str]:
    """Compare reproducibility-relevant PX4 probe provenance."""
    errors = []
    for field in ("status", "version", "exit_code"):
        if expected[field] != actual[field]:
            errors.append(
                "px4_source.{}.{} expected {!r} but found {!r}".format(
                    name, field, expected[field], actual[field]
                )
            )
    left_command = _normalized_probe_command(name, expected["command"])
    right_command = _normalized_probe_command(name, actual["command"])
    if left_command != right_command:
        errors.append(
            "px4_source.{}.command expected {!r} but found {!r}".format(
                name, list(left_command), list(right_command)
            )
        )
    left_stdout = _normalized_probe_stdout(name, expected["stdout"])
    right_stdout = _normalized_probe_stdout(name, actual["stdout"])
    if left_stdout != right_stdout:
        errors.append("px4_source.{}.stdout differs from inventory".format(name))
    if expected["status"] in ("missing", "unverified") or actual["status"] in (
        "missing",
        "unverified",
    ):
        if expected["reason"].strip() != actual["reason"].strip():
            errors.append("px4_source.{}.reason differs from inventory".format(name))
    return errors


def compare_current(expected: Dict[str, Any], actual: Dict[str, Any]) -> List[str]:
    errors = []
    for field in ("origin", "branch", "head"):
        if expected["repository"][field] != actual["repository"][field]:
            errors.append(
                "repository.{} expected {!r} but found {!r}".format(
                    field,
                    expected["repository"][field],
                    actual["repository"][field],
                )
            )
    for section, names in (
        ("platform", ("os", "kernel", "architecture")),
    ):
        for name in names:
            left = expected[section][name]
            right = actual[section][name]
            if (left["status"], left["version"]) != (right["status"], right["version"]):
                errors.append(
                    "{}.{} expected {}/{} but found {}/{}".format(
                        section,
                        name,
                        left["status"],
                        left["version"],
                        right["status"],
                        right["version"],
                    )
                )
    if (
        expected["ros"]["distribution"]["status"],
        expected["ros"]["distribution"]["version"],
    ) != (
        actual["ros"]["distribution"]["status"],
        actual["ros"]["distribution"]["version"],
    ):
        errors.append("ROS distribution differs from inventory")
    expected_ros = {item["name"]: item for item in expected["ros"]["packages"]}
    actual_ros = {item["name"]: item for item in actual["ros"]["packages"]}
    if set(expected_ros) != set(actual_ros):
        errors.append(
            "ROS package probe set differs: expected {} found {}".format(
                sorted(expected_ros), sorted(actual_ros)
            )
        )
    for name in sorted(set(expected_ros) & set(actual_ros)):
        left = expected_ros[name]
        right = actual_ros[name]
        if (left["status"], left["version"]) != (right["status"], right["version"]):
            errors.append(
                "ROS package {} expected {}/{} but found {}/{}".format(
                    name, left["status"], left["version"], right["status"], right["version"]
                )
            )
    expected_tools = {item["name"]: item for item in expected["tools"]}
    actual_tools = {item["name"]: item for item in actual["tools"]}
    if set(expected_tools) != set(actual_tools):
        errors.append("tool probe set differs from inventory")
    for name, left in expected_tools.items():
        right = actual_tools.get(name)
        if right is None:
            errors.append("tool probe is missing: {}".format(name))
        elif (left["status"], left["version"]) != (right["status"], right["version"]):
            errors.append(
                "tool {} expected {}/{} but found {}/{}".format(
                    name,
                    left["status"],
                    left["version"],
                    right["status"],
                    right["version"],
                )
            )
    for name in ("managed_workspace", "submodules"):
        left = expected["px4_source"][name]
        right = actual["px4_source"][name]
        errors.extend(compare_px4_probe(name, left, right))
    if expected["px4_source"]["host_search_status"] != actual["px4_source"]["host_search_status"]:
        errors.append("PX4 host search status differs from inventory")
    return errors


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the checked-in environment inventory and PX4 lock placeholder, "
            "or explicitly capture a read-only host inventory."
        )
    )
    parser.add_argument("--repository-root", help="Explicit BoomBoomFly repository root")
    parser.add_argument("--inventory", help="Environment inventory JSON path")
    parser.add_argument("--schema", help="Environment JSON Schema path")
    parser.add_argument("--px4-lock", help="PX4 source/toolchain lock JSON path")
    parser.add_argument("--px4-lock-schema", help="PX4 lock JSON Schema path")
    parser.add_argument("--px4-source", help="Explicit PX4-Autopilot source path")
    parser.add_argument(
        "--check-current",
        action="store_true",
        help="Compare current read-only probes with the checked-in inventory",
    )
    parser.add_argument(
        "--capture",
        action="store_true",
        help="Capture current probes; requires --output and never runs MicroXRCEAgent",
    )
    parser.add_argument("--output", help="Capture output path")
    parser.add_argument(
        "--json-summary", action="store_true", help="Print the summary as JSON"
    )
    args = parser.parse_args(argv)
    if args.capture and not args.output:
        parser.error("--capture requires --output")
    if args.output and not args.capture:
        parser.error("--output requires --capture")
    return args


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        args = parse_args(argv)
        root = discover_repository_root(args.repository_root)
        inventory_path = (
            Path(args.inventory).expanduser().resolve()
            if args.inventory
            else root / "docs/evidence/environment/current_environment.json"
        )
        schema_path = (
            Path(args.schema).expanduser().resolve()
            if args.schema
            else root / "docs/evidence/schemas/environment.schema.json"
        )
        lock_path = (
            Path(args.px4_lock).expanduser().resolve()
            if args.px4_lock
            else root
            / "docs/evidence/environment/px4_source_toolchain_lock.template.json"
        )
        lock_schema_path = (
            Path(args.px4_lock_schema).expanduser().resolve()
            if args.px4_lock_schema
            else root / "docs/evidence/schemas/px4_source_toolchain_lock.schema.json"
        )

        environment_schema = load_json(schema_path)
        lock_schema = load_json(lock_schema_path)
        inventory = load_json(inventory_path)
        lock = load_json(lock_path)
        validate_json_schema(inventory, environment_schema, "environment inventory")
        validate_json_schema(lock, lock_schema, "PX4 source/toolchain lock")
        validate_environment(inventory)
        validate_px4_lock(lock)

        errors = []
        captured = None
        if args.check_current or args.capture:
            captured = capture_environment(root, args.px4_source)
            validate_json_schema(captured, environment_schema, "captured environment")
            validate_environment(captured)
        if args.check_current and captured is not None:
            errors.extend(compare_current(inventory, captured))
        if args.capture and captured is not None:
            output = Path(args.output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("w", encoding="utf-8") as stream:
                json.dump(captured, stream, indent=2, sort_keys=True)
                stream.write("\n")

        status = "PASS" if not errors else "FAIL"
        summary = {
            "status": status,
            "errors": errors,
            "inventory": str(inventory_path),
            "px4_lock": str(lock_path),
            "capture_output": str(Path(args.output).resolve()) if args.output else None,
            "hardware_accessed": False,
            "micro_xrce_agent_executed": False,
        }
        if args.json_summary:
            print(json.dumps(summary, sort_keys=True))
        else:
            print(
                "SUMMARY status={} errors={} hardware_accessed=no "
                "micro_xrce_agent_executed=no".format(status, len(errors))
            )
            for error in errors:
                print("ERROR {}".format(error), file=sys.stderr)
        return EXIT_OK if not errors else EXIT_VALIDATION
    except InventoryError as exc:
        print("SUMMARY status=FAIL errors=1", file=sys.stderr)
        print("ERROR {}".format(exc), file=sys.stderr)
        return EXIT_VALIDATION
    except OSError as exc:
        print("SUMMARY status=ERROR errors=1", file=sys.stderr)
        print("ERROR {}".format(exc), file=sys.stderr)
        return EXIT_USAGE_OR_IO
    except subprocess.SubprocessError as exc:
        print("SUMMARY status=ERROR errors=1", file=sys.stderr)
        print("ERROR probe failure: {}".format(exc), file=sys.stderr)
        return EXIT_PROBE


if __name__ == "__main__":
    sys.exit(main())
