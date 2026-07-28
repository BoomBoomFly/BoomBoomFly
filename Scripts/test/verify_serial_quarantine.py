#!/usr/bin/env python3
"""Verify that the serial ROS package is recoverable but unreachable in production."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

import yaml


EXIT_OK = 0
EXIT_QUARANTINE = 2
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class QuarantineError(RuntimeError):
    pass


def run(command, cwd):
    result = subprocess.run(
        command,
        cwd=str(cwd),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if result.returncode != 0:
        raise QuarantineError(
            "command failed exit={} command={} stderr={}".format(
                result.returncode, " ".join(command), result.stderr.strip()
            )
        )
    return result.stdout


def load_yaml(path):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise QuarantineError("cannot load {}: {}".format(path, exc))


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise QuarantineError("cannot load {}: {}".format(path, exc))


def normalize_url(value):
    normalized = value.rstrip("/")
    return normalized[:-4] if normalized.endswith(".git") else normalized


def verify(root, serial_source, log_base):
    quarantine_path = root / "workspace.quarantine.repos"
    quarantine = load_yaml(quarantine_path)
    repositories = quarantine.get("repositories", {})
    if set(repositories) != {"src/serial_driver_ros"}:
        raise QuarantineError("quarantine manifest must contain only serial_driver_ros")
    entry = repositories["src/serial_driver_ros"]
    expected_url = "https://github.com/BoomBoomFly/serial_driver_ros.git"
    if entry.get("type") != "git" or normalize_url(entry.get("url", "")) != normalize_url(expected_url):
        raise QuarantineError("serial quarantine origin mismatch")
    expected_sha = entry.get("version", "")
    if not SHA_RE.fullmatch(expected_sha):
        raise QuarantineError("serial quarantine version must be an exact 40-character SHA")

    for active_name in ("workspace.lock.repos", "workspace.repos"):
        active = load_yaml(root / active_name)
        for path, active_entry in active.get("repositories", {}).items():
            active_url = normalize_url(str(active_entry.get("url", "")))
            if path == "src/serial_driver_ros" or active_url == normalize_url(expected_url):
                raise QuarantineError("serial source entered active manifest {}".format(active_name))

    package_profile = load_json(root / "config/profiles/dds_only_packages.yaml")
    if "workspace.quarantine.repos" not in package_profile.get("quarantine_manifests", []):
        raise QuarantineError("package profile does not register quarantine manifest")
    forbidden = {
        item["name"]: item["path"]
        for item in package_profile.get("forbidden_packages", [])
    }
    if forbidden.get("serial_driver") != "src/serial_driver_ros":
        raise QuarantineError("serial_driver forbidden path does not match quarantine path")
    production_names = {
        item["name"] for item in package_profile.get("production_packages", [])
    }
    if "serial_driver" in production_names:
        raise QuarantineError("serial_driver entered production package allowlist")

    launch_profile = load_json(root / "config/profiles/dds_only_launch.yaml")
    allowlisted_launches = sorted(launch_profile.get("production_allowlist", {}))
    serial_launch_references = []
    for relative in allowlisted_launches:
        text = (root / relative).read_text(encoding="utf-8")
        if re.search(r"serial_driver|/cmd_vel|/dev/tty", text, re.IGNORECASE):
            serial_launch_references.append(relative)
    if serial_launch_references:
        raise QuarantineError(
            "production launch references serial: {}".format(serial_launch_references)
        )

    source_result = None
    if serial_source is not None:
        source = serial_source.resolve()
        actual_url = run(["git", "remote", "get-url", "origin"], source).strip()
        actual_sha = run(["git", "rev-parse", "HEAD"], source).strip()
        status = run(["git", "status", "--porcelain=v2"], source)
        if normalize_url(actual_url) != normalize_url(expected_url):
            raise QuarantineError("serial checkout origin does not match quarantine manifest")
        if actual_sha != expected_sha:
            raise QuarantineError("serial checkout HEAD does not match quarantine manifest")
        if status:
            raise QuarantineError("serial quarantine checkout is dirty")
        marker = source / "COLCON_IGNORE"
        if not marker.is_file():
            raise QuarantineError("serial checkout lacks COLCON_IGNORE")
        try:
            log_base.resolve().relative_to(Path("/tmp"))
        except ValueError:
            raise QuarantineError("--log-base must resolve below /tmp")
        output = run(
            [
                "colcon",
                "--log-base",
                str(log_base.resolve()),
                "list",
                "--ignore-user-meta",
                "--base-paths",
                str(source),
            ],
            root,
        )
        if output.strip():
            raise QuarantineError("serial quarantine package was discovered: {}".format(output))
        source_result = {
            "origin": actual_url,
            "head": actual_sha,
            "clean": True,
            "colcon_discovery_count": 0,
            "marker_sha256": hashlib.sha256(marker.read_bytes()).hexdigest(),
        }

    return {
        "status": "PASS",
        "quarantine_manifest": str(quarantine_path),
        "serial_path": "src/serial_driver_ros",
        "serial_origin": expected_url,
        "serial_sha": expected_sha,
        "production_package_references": 0,
        "production_launch_references": 0,
        "source": source_result,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--serial-source")
    parser.add_argument("--log-base", required=True)
    args = parser.parse_args(argv)
    try:
        summary = verify(
            Path(args.workspace_root).resolve(),
            Path(args.serial_source) if args.serial_source else None,
            Path(args.log_base),
        )
    except (QuarantineError, OSError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return EXIT_QUARANTINE
    print(json.dumps(summary, sort_keys=True))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
