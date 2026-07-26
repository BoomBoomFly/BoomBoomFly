#!/usr/bin/env python3
"""Fail-closed verification for the BoomBoomFly DDS-only package boundary."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET


EXIT_OK = 0
EXIT_BOUNDARY = 2
EXIT_USAGE = 3
DEPENDENCY_TAGS = {
    "depend",
    "build_depend",
    "build_export_depend",
    "buildtool_depend",
    "buildtool_export_depend",
    "exec_depend",
    "test_depend",
}
CATEGORIES = (
    "production_packages",
    "forbidden_packages",
    "managed_nonproduction_packages",
)


class BoundaryError(RuntimeError):
    """A deterministic package-boundary validation failure."""


def repository_root(explicit_root):
    if explicit_root:
        return Path(explicit_root).resolve()
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if result.returncode != 0:
        raise BoundaryError(
            "cannot determine repository root: {}".format(result.stderr.strip())
        )
    return Path(result.stdout.strip()).resolve()


def safe_relative_path(value, label):
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise BoundaryError("{} must be a repository-relative path: {}".format(label, value))
    return path


def load_profile(path):
    try:
        with path.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
    except (OSError, ValueError) as exc:
        raise BoundaryError("cannot load profile {}: {}".format(path, exc))
    if data.get("schema_version") != 1:
        raise BoundaryError("profile schema_version must be 1")
    inventory = {}
    category_names = {}
    for category in CATEGORIES:
        entries = data.get(category)
        if not isinstance(entries, list):
            raise BoundaryError("profile field {} must be a list".format(category))
        category_names[category] = set()
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise BoundaryError("{}[{}] must be an object".format(category, index))
            name = entry.get("name")
            raw_path = entry.get("path")
            if not isinstance(name, str) or not name:
                raise BoundaryError("{}[{}].name is required".format(category, index))
            if not isinstance(raw_path, str) or not raw_path:
                raise BoundaryError("{}[{}].path is required".format(category, index))
            relative = safe_relative_path(raw_path, "{}[{}].path".format(category, index))
            if name in inventory:
                raise BoundaryError("package {} is classified more than once".format(name))
            inventory[name] = {"category": category, "path": relative}
            category_names[category].add(name)
    if not category_names["production_packages"]:
        raise BoundaryError("production package allowlist must not be empty")
    return data, inventory, category_names


def read_excluded(path):
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise BoundaryError("cannot read excluded package list {}: {}".format(path, exc))
    values = []
    for line in lines:
        value = line.split("#", 1)[0].strip()
        if value:
            values.append(value)
    if len(values) != len(set(values)):
        raise BoundaryError("excluded package list contains duplicates")
    return set(values)


def parse_colcon_output(output, root):
    packages = {}
    for line_number, line in enumerate(output.splitlines(), 1):
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) < 2:
            raise BoundaryError(
                "invalid colcon list output at line {}: {}".format(line_number, line)
            )
        name = fields[0].strip()
        package_path = Path(fields[1].strip()).resolve()
        try:
            relative = package_path.relative_to(root)
        except ValueError:
            raise BoundaryError(
                "colcon discovered package {} outside repository: {}".format(
                    name, package_path
                )
            )
        if name in packages:
            raise BoundaryError("colcon reported duplicate package name {}".format(name))
        packages[name] = relative
    return packages


def run_colcon_list(colcon, root, log_base, paths):
    command = [
        colcon,
        "--log-base",
        str(log_base),
        "list",
        "--ignore-user-meta",
    ]
    if paths:
        command.extend(["--paths"] + [str(root / path) for path in paths])
    else:
        command.extend(["--base-paths", str(root / "src")])
    result = subprocess.run(
        command,
        cwd=str(root),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if result.returncode != 0:
        raise BoundaryError(
            "colcon list failed (exit={}): {}\ncommand={}".format(
                result.returncode, result.stderr.strip(), " ".join(command)
            )
        )
    return parse_colcon_output(result.stdout, root), command


def package_dependencies(package_xml):
    try:
        root = ET.parse(str(package_xml)).getroot()
    except (OSError, ET.ParseError) as exc:
        raise BoundaryError("cannot parse {}: {}".format(package_xml, exc))
    dependencies = set()
    for child in root:
        if child.tag in DEPENDENCY_TAGS and child.text and child.text.strip():
            dependencies.add(child.text.strip())
    return dependencies


def verify(root, profile_path, excluded_path, colcon, log_base):
    _, inventory, categories = load_profile(profile_path)
    excluded = read_excluded(excluded_path)
    forbidden = categories["forbidden_packages"]
    if excluded != forbidden:
        raise BoundaryError(
            "workspace.excluded_packages differs from forbidden profile: "
            "missing={} extra={}".format(
                sorted(excluded - forbidden), sorted(forbidden - excluded)
            )
        )

    production_entries = [
        inventory[name] for name in sorted(categories["production_packages"])
    ]
    production_paths = [entry["path"] for entry in production_entries]
    for name in sorted(categories["production_packages"]):
        package_xml = root / inventory[name]["path"] / "package.xml"
        if not package_xml.is_file():
            raise BoundaryError(
                "allowlisted package {} is missing {}".format(name, package_xml)
            )
        parsed_name = ET.parse(str(package_xml)).getroot().findtext("name")
        if parsed_name != name:
            raise BoundaryError(
                "allowlisted path/name mismatch: expected {} at {}, found {}".format(
                    name, package_xml, parsed_name
                )
            )

    discovered, full_command = run_colcon_list(colcon, root, log_base / "full", [])
    unknown = sorted(set(discovered) - set(inventory))
    if unknown:
        raise BoundaryError("unclassified ROS packages discovered: {}".format(unknown))
    for name, path in sorted(discovered.items()):
        expected = inventory[name]["path"]
        if path != expected:
            raise BoundaryError(
                "package {} path mismatch: expected {}, found {}".format(
                    name, expected, path
                )
            )
    missing_production = sorted(categories["production_packages"] - set(discovered))
    if missing_production:
        raise BoundaryError(
            "allowlisted packages not discovered: {}".format(missing_production)
        )

    authoritative, authoritative_command = run_colcon_list(
        colcon, root, log_base / "authoritative", production_paths
    )
    expected_production = categories["production_packages"]
    if set(authoritative) != expected_production:
        raise BoundaryError(
            "authoritative discovery mismatch: expected={}, found={}".format(
                sorted(expected_production), sorted(authoritative)
            )
        )
    for name, path in sorted(authoritative.items()):
        if path != inventory[name]["path"]:
            raise BoundaryError(
                "authoritative package {} path mismatch: expected {}, found {}".format(
                    name, inventory[name]["path"], path
                )
            )

    workspace_packages = set(discovered)
    for name in sorted(expected_production):
        package_xml = root / inventory[name]["path"] / "package.xml"
        workspace_dependencies = package_dependencies(package_xml) & workspace_packages
        disallowed = sorted(workspace_dependencies - expected_production)
        if disallowed:
            raise BoundaryError(
                "allowlisted package {} has non-allowlisted workspace dependencies: {}".format(
                    name, disallowed
                )
            )

    return {
        "status": "PASS",
        "profile": str(profile_path),
        "production_packages": sorted(expected_production),
        "classified_packages": len(inventory),
        "discovered_packages": len(discovered),
        "full_discovery_command": full_command,
        "authoritative_discovery_command": authoritative_command,
        "log_base": str(log_base),
    }


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Verify the exact DDS-only package allowlist, full workspace "
            "classification, and workspace dependency closure."
        )
    )
    parser.add_argument(
        "--workspace-root",
        help="repository root (default: git rev-parse --show-toplevel)",
    )
    parser.add_argument(
        "--profile",
        help="profile path (default: config/profiles/dds_only_packages.yaml)",
    )
    parser.add_argument(
        "--excluded-packages",
        help="excluded package list (default: workspace.excluded_packages)",
    )
    parser.add_argument("--colcon", default="colcon", help="colcon executable")
    parser.add_argument(
        "--log-base",
        help="colcon log directory; must resolve below /tmp",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        root = repository_root(args.workspace_root)
        profile = Path(args.profile).resolve() if args.profile else (
            root / "config/profiles/dds_only_packages.yaml"
        )
        excluded = (
            Path(args.excluded_packages).resolve()
            if args.excluded_packages
            else root / "workspace.excluded_packages"
        )
        log_base = (
            Path(args.log_base).resolve()
            if args.log_base
            else Path("/tmp") / "boomboomfly_package_boundary_{}".format(os.getpid())
        )
        try:
            log_base.relative_to(Path("/tmp"))
        except ValueError:
            raise BoundaryError("--log-base must resolve below /tmp")
        summary = verify(root, profile, excluded, args.colcon, log_base)
    except (BoundaryError, OSError, ET.ParseError) as exc:
        print(
            json.dumps(
                {"status": "FAIL", "error": str(exc)},
                sort_keys=True,
            )
        )
        return EXIT_BOUNDARY
    print(json.dumps(summary, sort_keys=True))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
