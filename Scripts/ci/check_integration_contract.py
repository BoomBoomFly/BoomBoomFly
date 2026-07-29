#!/usr/bin/env python3
"""Fail-closed static gate for the DDS-only integration boundary."""

import json
import pathlib
import re
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE_PROFILE = ROOT / "config/profiles/dds_only_packages.yaml"
LAUNCH_PROFILE = ROOT / "config/profiles/dds_only_launch.yaml"
TOPIC_CONTRACT = ROOT / "config/profiles/dds_integration_contract.yaml"
LOCK_MANIFEST = ROOT / "workspace.lock.repos"
REPLAY_TOOL = ROOT / "Scripts/test/px4_interface_replay.py"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_PRODUCTION_PACKAGES = {
    "px4_msgs",
    "offboard_cpp",
    "vision_to_dds",
    "mission_bridge",
}


class GateError(RuntimeError):
    pass


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GateError("{} is not valid JSON/YAML-1.2: {}".format(path, exc))


def parse_lock_manifest():
    repositories = {}
    current = None
    for line in LOCK_MANIFEST.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^  (src/[^:]+):\s*$", line)
        if match:
            current = match.group(1)
            repositories[current] = {}
            continue
        if current is None:
            continue
        field = re.match(r"^    (type|url|version):\s*(\S+)\s*$", line)
        if field:
            repositories[current][field.group(1)] = field.group(2)
    return repositories


def check_exact_production_shas(package_profile):
    repositories = parse_lock_manifest()
    for package in package_profile["production_packages"]:
        package_path = package["path"]
        candidates = [
            repo_path for repo_path in repositories
            if package_path == repo_path or package_path.startswith(repo_path + "/")
        ]
        if not candidates:
            raise GateError("production package {} has no lock repository".format(package["name"]))
        repo_path = max(candidates, key=len)
        version = repositories[repo_path].get("version", "")
        if not SHA_RE.fullmatch(version):
            raise GateError("{} must use an exact 40-character SHA, got {!r}".format(
                repo_path, version))
        git_dir = ROOT / repo_path
        if (git_dir / ".git").exists():
            head = subprocess.check_output(
                ["git", "-C", str(git_dir), "rev-parse", "HEAD"],
                text=True).strip()
            if head != version:
                raise GateError("{} HEAD {} does not match lock SHA {}".format(
                    repo_path, head, version))
            dirty = subprocess.check_output(
                ["git", "-C", str(git_dir), "status", "--porcelain"],
                text=True).strip()
            if dirty:
                raise GateError("{} has uncommitted production changes".format(repo_path))


def check_package_boundary(package_profile):
    production = package_profile["production_packages"]
    names = {record["name"] for record in production}
    if names != EXPECTED_PRODUCTION_PACKAGES:
        raise GateError("authoritative package set must be {}, got {}".format(
            sorted(EXPECTED_PRODUCTION_PACKAGES), sorted(names)))
    tested = {record["name"] for record in production if record.get("test") is True}
    required_tests = EXPECTED_PRODUCTION_PACKAGES - {"px4_msgs"}
    if not required_tests.issubset(tested):
        raise GateError("production tests omit {}".format(sorted(required_tests - tested)))

    forbidden = {record["name"] for record in package_profile["forbidden_packages"]}
    if not {"serial", "serial_driver"}.issubset(forbidden):
        raise GateError("serial_driver_ros and legacy serial must remain quarantined")


def node_blocks(text):
    blocks = []
    for match in re.finditer(r"\bNode\s*\(", text):
        depth = 1
        index = match.end()
        quote = None
        escaped = False
        while index < len(text) and depth:
            char = text[index]
            if quote is not None:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
            elif char in ("'", '"'):
                quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            index += 1
        if depth != 0:
            raise GateError("unterminated Node(...) declaration")
        blocks.append(text[match.end():index - 1])
    return blocks


def launch_nodes(path):
    nodes = []
    for block in node_blocks(path.read_text(encoding="utf-8")):
        fields = {}
        for key in ("package", "executable", "name"):
            match = re.search(r"\b{}\s*=\s*['\"]([^'\"]+)['\"]".format(key), block)
            if match:
                fields[key] = match.group(1)
        if set(fields) == {"package", "executable", "name"}:
            nodes.append((fields["package"], fields["executable"], fields["name"]))
    return sorted(nodes)


def check_launch_inventory(launch_profile):
    for relative, record in launch_profile["production_allowlist"].items():
        path = ROOT / relative
        if not path.is_file():
            raise GateError("allowlisted launch is missing: {}".format(relative))
        expected = sorted(
            (node["package"], node["executable"], node["name"])
            for node in record["nodes"])
        actual = launch_nodes(path)
        if actual != expected:
            raise GateError("launch inventory mismatch for {}: expected {}, actual {}".format(
                relative, expected, actual))
        source = path.read_text(encoding="utf-8").lower()
        if "px4_interface_replay" in source or re.search(r"\bmock[_-]?(?:px4|rc)\b", source):
            raise GateError("test replay/mock is forbidden in production launch {}".format(
                relative))


def check_topic_contract(contract):
    topic_types = {}
    for topic in contract["topics"]:
        name = topic["name"]
        msg_type = topic["type"]
        previous = topic_types.setdefault(name, msg_type)
        if previous != msg_type:
            raise GateError("{} has conflicting types {} and {}".format(
                name, previous, msg_type))
        for endpoint in topic["endpoints"]:
            path = ROOT / endpoint["path"]
            if not path.is_file():
                raise GateError("topic endpoint source is missing: {}".format(endpoint["path"]))
            source = path.read_text(encoding="utf-8")
            for evidence in endpoint["evidence"]:
                if evidence not in source:
                    raise GateError("{} {} lacks type/topic evidence {!r}".format(
                        name, endpoint["role"], evidence))


def check_vision_default(contract):
    record = contract["vision_default"]
    path = ROOT / record["config"]
    text = path.read_text(encoding="utf-8")
    if record["required_text"] not in text:
        raise GateError("vision default must create no PX4 writer: missing {!r}".format(
            record["required_text"]))


def check_isolated_replay():
    if not REPLAY_TOOL.is_file():
        raise GateError("isolated PX4 replay tool is missing")
    source = REPLAY_TOOL.read_text(encoding="utf-8")
    required = (
        'os.environ.get("ROS_DOMAIN_ID"',
        "actual == 0",
        "default=231",
        '"/fmu/out/timesync_status"',
        '"/fmu/out/vehicle_status_v1"',
        '"/fmu/out/vehicle_land_detected"',
        '"/fmu/out/vehicle_odometry"',
        '"/fmu/out/rc_channels"',
        '"/fmu/out/vehicle_command_ack"',
    )
    missing = [item for item in required if item not in source]
    if missing:
        raise GateError("replay isolation/frequency contract lacks {}".format(missing))
    subprocess.check_call([sys.executable, str(REPLAY_TOOL), "--self-test"])


def check_single_writer(package_profile, launch_profile):
    inventory = launch_profile["writer_inventory"]
    owners = {}
    for owner, topics in inventory.items():
        for topic in topics:
            normalized = "/" + topic.lstrip("/")
            if normalized in owners:
                raise GateError("{} has multiple declared writers: {} and {}".format(
                    normalized, owners[normalized], owner))
            owners[normalized] = owner

    discovered = set()
    topic_re = re.compile(r"(?<![A-Za-z0-9_])/?fmu/in/[A-Za-z0-9_/]+")
    for package in package_profile["production_packages"]:
        source_root = ROOT / package["path"] / "src"
        if not source_root.is_dir():
            continue
        for path in source_root.rglob("*"):
            if path.suffix not in (".cpp", ".cc", ".c", ".hpp", ".h"):
                continue
            for topic in topic_re.findall(path.read_text(encoding="utf-8", errors="replace")):
                discovered.add("/" + topic.lstrip("/"))
    undeclared = sorted(discovered - set(owners))
    if undeclared:
        raise GateError("production sources contain undeclared /fmu/in writers/topics: {}".format(
            undeclared))


def main():
    package_profile = load_json(PACKAGE_PROFILE)
    launch_profile = load_json(LAUNCH_PROFILE)
    contract = load_json(TOPIC_CONTRACT)
    check_package_boundary(package_profile)
    check_exact_production_shas(package_profile)
    check_launch_inventory(launch_profile)
    check_topic_contract(contract)
    check_vision_default(contract)
    check_isolated_replay()
    check_single_writer(package_profile, launch_profile)
    print(json.dumps({
        "status": "PASS",
        "gate": "dds_integration_contract",
        "production_packages": len(package_profile["production_packages"]),
        "topics": len(contract["topics"]),
        "launches": len(launch_profile["production_allowlist"]),
        "fmu_writers": sum(len(value) for value in launch_profile["writer_inventory"].values()),
    }, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (GateError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        print("ERROR: {}".format(exc), file=sys.stderr)
        sys.exit(1)
