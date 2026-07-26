#!/usr/bin/env python3
"""Fail-closed static launch safety guard; never imports or runs launch files."""

import argparse
import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


EXIT_PASS = 0
EXIT_DENIED = 1
EXIT_REVIEW = 2
SKIP_DIRS = {".git", "build", "install", "log", "__pycache__"}


class GuardError(RuntimeError):
    pass


def git_root(candidate: Path) -> Path:
    completed = subprocess.run(
        ["git", "-C", str(candidate), "rev-parse", "--show-toplevel"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise GuardError(completed.stderr.decode("utf-8", "replace").strip())
    return Path(completed.stdout.decode("utf-8").strip()).resolve()


def safe_relative(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or value in ("", "."):
        raise GuardError("unsafe repository-relative path: {}".format(value))
    return path


def is_launch_path(path: Path) -> bool:
    name = path.name
    return (
        name.endswith(".launch.py")
        or name.endswith(".launch.xml")
        or name.endswith(".launch")
        or ("launch" in path.parts and path.suffix in (".py", ".xml"))
    )


def discover_launches(source_root: Path) -> List[str]:
    result = []
    for current, directories, files in os.walk(str(source_root)):
        directories[:] = sorted(item for item in directories if item not in SKIP_DIRS)
        current_path = Path(current)
        for filename in sorted(files):
            path = current_path / filename
            if is_launch_path(path):
                result.append(path.relative_to(source_root).as_posix())
    return sorted(result)


def load_profile(path: Path) -> Dict[str, Any]:
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GuardError("cannot read profile {}: {}".format(path, error))
    if not isinstance(profile, dict):
        raise GuardError("profile root must be an object")
    return profile


def validate_profile(profile: Dict[str, Any], schema_path: Path) -> None:
    try:
        import jsonschema
    except ImportError:
        raise GuardError("jsonschema is required for launch profile validation")
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(profile), key=lambda item: list(item.path))
    except (OSError, json.JSONDecodeError, jsonschema.exceptions.SchemaError) as error:
        raise GuardError("invalid launch profile schema: {}".format(error))
    if errors:
        first = errors[0]
        location = ".".join(str(item) for item in first.path) or "<root>"
        raise GuardError("profile schema {}: {}".format(location, first.message))


def call_name(node: ast.Call) -> str:
    target = node.func
    parts = []
    while isinstance(target, ast.Attribute):
        parts.append(target.attr)
        target = target.value
    if isinstance(target, ast.Name):
        parts.append(target.id)
    return ".".join(reversed(parts))


def keyword(call: ast.Call, name: str) -> Optional[ast.AST]:
    for item in call.keywords:
        if item.arg == name:
            return item.value
    return None


class StaticValues:
    def __init__(self, assignments: Dict[str, ast.AST]):
        self.assignments = assignments
        self.active: Set[str] = set()

    def strings(self, node: Optional[ast.AST]) -> Tuple[List[str], bool]:
        if node is None:
            return [], False
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return [node.value], False
            if isinstance(node.value, (bool, int, float)) or node.value is None:
                return [str(node.value)], False
            return [], True
        if isinstance(node, ast.Name):
            if node.id in self.active or node.id not in self.assignments:
                return [], True
            self.active.add(node.id)
            result = self.strings(self.assignments[node.id])
            self.active.remove(node.id)
            return result
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            values: List[str] = []
            dynamic = False
            for element in node.elts:
                strings, unresolved = self.strings(element)
                values.extend(strings)
                dynamic = dynamic or unresolved
            return values, dynamic
        if isinstance(node, ast.Dict):
            values = []
            dynamic = False
            for value in node.values:
                strings, unresolved = self.strings(value)
                values.extend(strings)
                dynamic = dynamic or unresolved
            return values, dynamic
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left, left_dynamic = self.strings(node.left)
            right, right_dynamic = self.strings(node.right)
            if len(left) == 1 and len(right) == 1:
                return [left[0] + right[0]], left_dynamic or right_dynamic
            return left + right, True
        if isinstance(node, ast.JoinedStr):
            values = []
            for item in node.values:
                if isinstance(item, ast.Constant) and isinstance(item.value, str):
                    values.append(item.value)
                else:
                    return values, True
            return ["".join(values)], False
        if isinstance(node, ast.Call):
            name = call_name(node)
            if name.endswith("FindPackageShare") and node.args:
                package, dynamic = self.strings(node.args[0])
                if len(package) == 1 and not dynamic:
                    return ["package:" + package[0]], False
                return [], True
            if isinstance(node.func, ast.Attribute) and node.func.attr == "find":
                return self.strings(node.func.value)
            if name.endswith("LaunchConfiguration"):
                default = keyword(node, "default")
                if default is None:
                    return [], True
                return self.strings(default)
            if name.endswith(("PathJoinSubstitution", "os.path.join")):
                source = node.args[0] if name.endswith("PathJoinSubstitution") and node.args else None
                pieces_node = source if source is not None else ast.List(elts=list(node.args), ctx=ast.Load())
                pieces, dynamic = self.strings(pieces_node)
                if pieces:
                    prefix = pieces[0]
                    if prefix.startswith("package:"):
                        return [prefix + "/" + "/".join(pieces[1:])], dynamic
                    return ["/".join(pieces)], dynamic
                return [], True
            values = []
            dynamic = False
            for argument in node.args:
                strings, unresolved = self.strings(argument)
                values.extend(strings)
                dynamic = dynamic or unresolved
            return values, True if not values else dynamic
        return [], True


def matches_any(values: Iterable[str], patterns: Sequence[str]) -> List[str]:
    findings = []
    for value in values:
        for pattern in patterns:
            if re.search(pattern, value, flags=re.IGNORECASE):
                findings.append("{} matches {}".format(value, pattern))
    return findings


def canonical_nodes(nodes: Sequence[Dict[str, str]]) -> List[Tuple[str, str, str]]:
    """Return a deterministic multiset representation for exact allowlist checks."""
    return sorted(
        (node["package"], node["executable"], node["name"])
        for node in nodes
    )


def package_file(
    source_root: Path, launch_path: Path, semantic: str
) -> Optional[Path]:
    if semantic.startswith("package:"):
        package_and_path = semantic[len("package:") :].split("/", 1)
        package = package_and_path[0]
        relative = package_and_path[1] if len(package_and_path) == 2 else ""
        candidates = list((source_root / "src").glob("**/package.xml"))
        for package_xml in candidates:
            try:
                text = package_xml.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if re.search(r"<name>\s*{}\s*</name>".format(re.escape(package)), text):
                return package_xml.parent / relative
        return None
    candidate = Path(semantic)
    if candidate.is_absolute():
        return candidate
    return launch_path.parent / candidate


def scan_parameter_file(
    path: Path, profile: Dict[str, Any], findings: List[str], reviews: List[str]
) -> None:
    if not path.is_file():
        reviews.append("parameter file cannot be resolved: {}".format(path))
        return
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as error:
        reviews.append("parameter file cannot be read: {}".format(error))
        return
    for match in matches_any([text], profile["device_patterns"] + profile["agent_patterns"]):
        findings.append("parameter file {}: {}".format(path, match))


def analyze_python(
    path: Path, source_root: Path, profile: Dict[str, Any]
) -> Dict[str, Any]:
    findings: List[str] = []
    reviews: List[str] = []
    nodes: List[Dict[str, str]] = []
    writers: Dict[str, int] = {}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="strict"), filename=str(path))
    except (OSError, UnicodeError, SyntaxError) as error:
        return {
            "findings": [],
            "nodes": [],
            "reviews": ["cannot parse Python: {}".format(error)],
            "writers": {},
        }
    assignments: Dict[str, ast.AST] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments[target.id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            assignments[node.target.id] = node.value
    values = StaticValues(assignments)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = call_name(node).split(".")[-1]
        if name in ("OpaqueFunction", "PythonExpression", "Command"):
            reviews.append("dynamic launch action {} at line {}".format(name, node.lineno))
        if name in ("Node", "ComposableNode", "LifecycleNode"):
            package_values, package_dynamic = values.strings(keyword(node, "package"))
            executable_node = keyword(node, "executable") or keyword(node, "node_executable")
            executable_values, executable_dynamic = values.strings(executable_node)
            name_node = keyword(node, "name") or keyword(node, "node_name")
            name_values, name_dynamic = values.strings(name_node)
            if len(package_values) != 1 or package_dynamic:
                reviews.append("dynamic Node package at line {}".format(node.lineno))
            if len(executable_values) != 1 or executable_dynamic:
                reviews.append("dynamic Node executable at line {}".format(node.lineno))
            if len(name_values) != 1 or name_dynamic:
                reviews.append("dynamic or missing Node name at line {}".format(node.lineno))
            findings.extend(
                "Node line {}: {}".format(node.lineno, item)
                for item in matches_any(package_values, profile["forbidden_package_patterns"])
            )
            findings.extend(
                "Node line {}: {}".format(node.lineno, item)
                for item in matches_any(executable_values, profile["forbidden_executable_patterns"])
            )
            if len(package_values) == 1 and len(executable_values) == 1:
                identity = package_values[0] + "/" + executable_values[0]
                for topic in profile["writer_inventory"].get(identity, []):
                    writers[topic] = writers.get(topic, 0) + 1
            if (
                len(package_values) == 1
                and not package_dynamic
                and len(executable_values) == 1
                and not executable_dynamic
                and len(name_values) == 1
                and not name_dynamic
            ):
                nodes.append({
                    "package": package_values[0],
                    "executable": executable_values[0],
                    "name": name_values[0],
                })
            safety_nodes = [
                keyword(node, "arguments"),
                keyword(node, "remappings"),
                keyword(node, "parameters"),
            ]
            for value_node in safety_nodes:
                strings, _ = values.strings(value_node)
                findings.extend(
                    "Node line {}: {}".format(node.lineno, item)
                    for item in matches_any(
                        strings,
                        profile["device_patterns"]
                        + profile["agent_patterns"]
                        + profile["forbidden_topic_patterns"],
                    )
                )
                for semantic in strings:
                    if semantic.endswith((".yaml", ".yml")):
                        resolved = package_file(source_root, path, semantic)
                        if resolved is None:
                            reviews.append("unresolved parameter reference {}".format(semantic))
                        else:
                            scan_parameter_file(resolved, profile, findings, reviews)
        elif name == "ExecuteProcess":
            command_values, dynamic = values.strings(keyword(node, "cmd"))
            if dynamic or not command_values:
                reviews.append("dynamic ExecuteProcess at line {}".format(node.lineno))
            else:
                findings.append("ExecuteProcess is not allowed at line {}".format(node.lineno))
            findings.extend(
                "ExecuteProcess line {}: {}".format(node.lineno, item)
                for item in matches_any(
                    command_values,
                    profile["device_patterns"]
                    + profile["agent_patterns"]
                    + profile["forbidden_executable_patterns"],
                )
            )
            shell_values, _ = values.strings(keyword(node, "shell"))
            if any(value.lower() == "true" for value in shell_values):
                findings.append("shell=True at line {}".format(node.lineno))
        elif name == "IncludeLaunchDescription":
            include_values, dynamic = values.strings(node.args[0] if node.args else None)
            if dynamic or not include_values:
                reviews.append("dynamic IncludeLaunchDescription at line {}".format(node.lineno))
            matches = matches_any(
                include_values,
                profile["forbidden_package_patterns"]
                + profile["forbidden_executable_patterns"],
            )
            findings.extend(
                "Include line {}: {}".format(node.lineno, item) for item in matches
            )
            if include_values and not matches:
                reviews.append("included launch requires explicit review at line {}".format(node.lineno))
        elif name == "DeclareLaunchArgument":
            default_values, dynamic = values.strings(keyword(node, "default_value"))
            findings.extend(
                "argument default line {}: {}".format(node.lineno, item)
                for item in matches_any(
                    default_values, profile["device_patterns"] + profile["agent_patterns"]
                )
            )
            if dynamic and default_values:
                reviews.append("dynamic launch argument default at line {}".format(node.lineno))
    for topic, count in sorted(writers.items()):
        if count > 1:
            findings.append("multiple writers for {}: {}".format(topic, count))
    return {
        "findings": sorted(set(findings)),
        "nodes": nodes,
        "reviews": sorted(set(reviews)),
        "writers": writers,
    }


def analyze_xml(path: Path, profile: Dict[str, Any]) -> Dict[str, Any]:
    findings: List[str] = []
    reviews: List[str] = []
    nodes: List[Dict[str, str]] = []
    writers: Dict[str, int] = {}
    try:
        root = ET.parse(str(path)).getroot()
    except (OSError, ET.ParseError) as error:
        return {
            "findings": [],
            "nodes": [],
            "reviews": ["cannot parse XML: {}".format(error)],
            "writers": {},
        }
    for element in root.iter():
        tag = element.tag.split("}")[-1]
        values = list(element.attrib.values())
        if tag == "node":
            package = element.attrib.get("pkg", element.attrib.get("package", ""))
            executable = element.attrib.get("type", element.attrib.get("exec", ""))
            name = element.attrib.get("name", "")
            if not package or "$(" in package:
                reviews.append("dynamic XML node package")
            if not executable or "$(" in executable:
                reviews.append("dynamic XML node executable")
            if not name or "$(" in name:
                reviews.append("dynamic or missing XML node name")
            findings.extend(
                "XML node: " + item
                for item in matches_any([package], profile["forbidden_package_patterns"])
            )
            findings.extend(
                "XML node: " + item
                for item in matches_any([executable], profile["forbidden_executable_patterns"])
            )
            identity = package + "/" + executable
            for topic in profile["writer_inventory"].get(identity, []):
                writers[topic] = writers.get(topic, 0) + 1
            if (
                package
                and "$(" not in package
                and executable
                and "$(" not in executable
                and name
                and "$(" not in name
            ):
                nodes.append({
                    "package": package,
                    "executable": executable,
                    "name": name,
                })
        if tag == "include":
            if any("$(" in value for value in values):
                reviews.append("dynamic XML include")
            findings.extend(
                "XML include: " + item
                for item in matches_any(
                    values,
                    profile["forbidden_package_patterns"]
                    + profile["forbidden_executable_patterns"],
                )
            )
        findings.extend(
            "XML {}: {}".format(tag, item)
            for item in matches_any(
                values,
                profile["device_patterns"]
                + profile["agent_patterns"]
                + profile["forbidden_topic_patterns"],
            )
        )
    for topic, count in sorted(writers.items()):
        if count > 1:
            findings.append("multiple writers for {}: {}".format(topic, count))
    return {
        "findings": sorted(set(findings)),
        "nodes": nodes,
        "reviews": sorted(set(reviews)),
        "writers": writers,
    }


def analyze(path: Path, source_root: Path, profile: Dict[str, Any]) -> Dict[str, Any]:
    if path.suffix == ".xml" or path.name.endswith(".launch"):
        return analyze_xml(path, profile)
    return analyze_python(path, source_root, profile)


def refresh_inventory(profile_path: Path, source_root: Path, profile: Dict[str, Any]) -> None:
    allowed = set(profile["production_allowlist"])
    actual = discover_launches(source_root)
    missing_allowed = sorted(allowed - set(actual))
    if missing_allowed:
        raise GuardError("allowed launch missing: {}".format(", ".join(missing_allowed)))
    profile["historical_denied_inventory"] = sorted(set(actual) - allowed)
    profile_path.write_text(
        json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Statically scan launch files without importing or running them."
    )
    result.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[3])
    result.add_argument("--source-workspace-root", type=Path)
    result.add_argument("--profile", type=Path)
    result.add_argument("--schema", type=Path)
    result.add_argument("--check-file", action="append", type=Path)
    result.add_argument(
        "--refresh-inventory",
        action="store_true",
        help="Explicitly rewrite only historical_denied_inventory in the profile",
    )
    return result


def main(arguments: Optional[Sequence[str]] = None) -> int:
    options = parser().parse_args(arguments)
    try:
        root = git_root(options.repository_root)
        source_root = git_root(options.source_workspace_root or root)
        profile_path = options.profile or root / "config/profiles/dds_only_launch.yaml"
        schema_path = options.schema or root / "config/profiles/dds_only_launch.schema.json"
        profile = load_profile(profile_path)
        validate_profile(profile, schema_path)
        if options.refresh_inventory:
            refresh_inventory(profile_path, source_root, profile)
            print(json.dumps({"result": "UPDATED", "profile": str(profile_path)}, sort_keys=True))
            return EXIT_PASS
        if options.check_file:
            denied = 0
            review = 0
            reports = []
            for raw_path in options.check_file:
                path = raw_path if raw_path.is_absolute() else source_root / raw_path
                report = analyze(path.resolve(), source_root, profile)
                reports.append({"path": str(raw_path), **report})
                denied += bool(report["findings"])
                review += bool(report["reviews"])
            result = "DENIED" if denied else ("REQUIRES_REVIEW" if review else "PASS")
            print(json.dumps({"result": result, "reports": reports}, sort_keys=True))
            return EXIT_DENIED if denied else (EXIT_REVIEW if review else EXIT_PASS)

        actual = discover_launches(source_root)
        allowed = set(profile["production_allowlist"])
        historical = set(profile["historical_denied_inventory"])
        actual_set = set(actual)
        missing = sorted((allowed | historical) - actual_set)
        unclassified = sorted(actual_set - allowed - historical)
        errors: List[str] = []
        reviews: List[str] = []
        allowed_reports = []
        denied_with_findings = 0
        for relative in actual:
            report = analyze(source_root / relative, source_root, profile)
            if relative in allowed:
                allowed_reports.append({"path": relative, **report})
                errors.extend("{}: {}".format(relative, item) for item in report["findings"])
                reviews.extend("{}: {}".format(relative, item) for item in report["reviews"])
                expected_nodes = profile["production_allowlist"][relative]["nodes"]
                if canonical_nodes(report["nodes"]) != canonical_nodes(expected_nodes):
                    errors.append(
                        "{}: exact Node allowlist mismatch; expected={} actual={}".format(
                            relative,
                            json.dumps(expected_nodes, sort_keys=True),
                            json.dumps(report["nodes"], sort_keys=True),
                        )
                    )
            elif report["findings"]:
                denied_with_findings += 1
        if missing:
            errors.append("profile paths missing: {}".format(", ".join(missing)))
        if unclassified:
            reviews.append("unclassified launch paths: {}".format(", ".join(unclassified)))
        if errors:
            result = "DENIED"
            exit_code = EXIT_DENIED
        elif reviews:
            result = "REQUIRES_REVIEW"
            exit_code = EXIT_REVIEW
        else:
            result = "PASS"
            exit_code = EXIT_PASS
        print(
            json.dumps(
                {
                    "allowed": len(allowed & actual_set),
                    "allowed_reports": allowed_reports,
                    "denied": len(historical & actual_set),
                    "denied_with_findings": denied_with_findings,
                    "errors": errors,
                    "production_enabled": profile["production_enabled"],
                    "result": result,
                    "reviews": reviews,
                    "unclassified": len(unclassified),
                },
                sort_keys=True,
            )
        )
        return exit_code
    except (GuardError, OSError, KeyError) as error:
        print(json.dumps({"result": "INVALID", "error": str(error)}, sort_keys=True))
        return EXIT_DENIED


if __name__ == "__main__":
    sys.exit(main())
