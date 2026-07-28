#!/usr/bin/env python3
"""Static fail-closed H0 verifier for the Wave 4B production profile."""

import argparse
import configparser
import json
from pathlib import Path
import re
import subprocess
import sys


class H0Error(RuntimeError):
    """A production-safety invariant is missing."""


CONTROL_MESSAGE_TYPES = (
    "TrajectorySetpoint",
    "OffboardControlMode",
    "VehicleCommand",
)
CONTROL_TOPICS = (
    "fmu/in/trajectory_setpoint",
    "fmu/in/offboard_control_mode",
    "fmu/in/vehicle_command",
)


def require(condition, message):
    if not condition:
        raise H0Error(message)


def read(path):
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise H0Error("cannot read {}: {}".format(path, exc))


def source_files(root):
    package = root / "src/offboard_cpp"
    files = []
    for relative in ("src", "include"):
        files.extend((package / relative).rglob("*.cpp"))
        files.extend((package / relative).rglob("*.hpp"))
    return sorted(set(files))


def verify_offboard(root):
    package = root / "src/offboard_cpp"
    adapter = package / "src/safety_gate_adapter.cpp"
    require(adapter.is_file(), "production SafetyGateAdapter is missing")
    writer_files = set()
    topic_files = set()
    for path in source_files(root):
        text = read(path)
        owns_control_publisher = any(
            "create_publisher<px4_msgs::msg::{}>".format(name) in text
            for name in CONTROL_MESSAGE_TYPES
        )
        owns_control_topic = any(
            '"{}"'.format(topic) in text for topic in CONTROL_TOPICS
        )
        if owns_control_publisher and owns_control_topic:
            writer_files.add(path.resolve())
        if owns_control_topic:
            topic_files.add(path.resolve())
    expected = {adapter.resolve()}
    require(
        writer_files == expected,
        "control create_publisher ownership mismatch: {}".format(
            sorted(str(path) for path in writer_files)
        ),
    )
    require(
        topic_files == expected,
        "control topic ownership mismatch: {}".format(
            sorted(str(path) for path in topic_files)
        ),
    )
    adapter_text = read(adapter)
    for topic in CONTROL_TOPICS:
        require(
            adapter_text.count('"{}"'.format(topic)) == 1,
            "adapter must own exactly one literal for {}".format(topic),
        )

    require(not (package / "src/lib/CtrlFSM.cpp").exists(), "legacy direct CtrlFSM remains")
    require(not (package / "include/lib/CtrlFSM.hpp").exists(), "legacy CtrlFSM header remains")
    require(not (package / "text/mock_rc_control.py").exists(), "production mock RC remains")
    compiled_text = "\n".join(
        read(path)
        for path in source_files(root) + [package / "CMakeLists.txt"]
    )
    require("TEXT_RC" not in compiled_text, "TEXT_RC remains in production build/source")

    node = read(package / "src/node.cpp")
    gate_header = read(package / "include/safety_gate.hpp")
    gate_source = read(package / "src/safety_gate.cpp")
    config = read(package / "config/ctrl_param.yaml")
    require(
        'declare_parameter<bool>("takeoff_land.enable_arm", false)' in node,
        "production node does not default enable_arm to false",
    )
    require(
        re.search(r"^\s*enable_arm:\s*false(?:\s|#|$)", config, re.MULTILINE),
        "production YAML does not default enable_arm to false",
    )
    for token in (
        "WAIT",
        "PRESTREAM",
        "REQUEST_MODE",
        "REQUEST_ARM",
        "ACTIVE",
        "STANDBY_DISARMED",
        "FAULT_LATCHED",
    ):
        require(token in gate_header, "gate state is missing: {}".format(token))
    for token in (
        "vehicle_status_fresh",
        "odometry_fresh",
        "timesync_fresh",
        "rc_fresh",
        "kill_fresh",
        "setpoint_fresh",
        "mode_fresh",
        "setpoint_mode_paired",
        "clock_monotonic",
        "kill_latched",
        "manual_arm_enable",
        "single_writer",
        "single_owner",
        "owner_id",
        "lease_id",
        "epoch",
        "sequence",
    ):
        require(token in gate_header, "gate input is missing: {}".format(token))
    for token in (
        "command ACK timeout",
        "authority sequence changed while command pending",
        "manual recovery required",
        "manual activation required",
        "ACK rejected or correlation mismatch",
    ):
        require(token in gate_source, "fail-closed transition is missing: {}".format(token))
    require("result_param2" not in node, "ACK observer assumes result_param2 sequence echo")
    require("confirmation = 0" in adapter_text, "VehicleCommand confirmation is not protocol-safe")
    require(
        "graph_has_only_gate_writer()" in node,
        "runtime duplicate-writer gate is not connected",
    )
    timestamp_header = read(package / "include/timestamp_gate.hpp")
    timestamp_source = read(package / "src/timestamp_gate.cpp")
    for token in (
        "VEHICLE_STATUS",
        "ODOMETRY",
        "RC",
        "SETPOINT",
        "MODE",
        "COMMAND_ACK",
        "ZERO",
        "NO_TIMESYNC",
        "FROZEN",
        "BACKWARD",
        "FUTURE",
        "STALE",
    ):
        require(token in timestamp_header, "timestamp contract is missing: {}".format(token))
    for token in (
        "observe_timesync",
        "timestamp_fault_latched_",
        "timestamp_config_valid_",
        "TimestampStream::VEHICLE_STATUS",
        "TimestampStream::ODOMETRY",
        "TimestampStream::RC",
        "TimestampStream::SETPOINT",
        "TimestampStream::MODE",
        "TimestampStream::COMMAND_ACK",
    ):
        require(token in node, "production timestamp gate is not connected: {}".format(token))
    require(
        "restart_epoch" in timestamp_source and "last_timestamp_us_.fill(0)" in timestamp_source,
        "timestamp restart does not clear the prior epoch",
    )


def verify_vision(root):
    source = read(root / "src/vision_to_dds/src/vision_to_dds.cpp")
    declaration = source.find('declare_parameter<bool>("enable_vision_dds", false)')
    first_publisher = source.find("create_publisher<")
    require(declaration >= 0, "vision production default is not disabled")
    require(first_publisher > declaration, "vision publisher precedes disabled default")
    navigation_start = source.find("void VisionToDDS::navigationParameters()")
    navigation_publish = source.find("create_publisher<", navigation_start)
    disabled_return = source.find("if (!enable_vision_dds_)", navigation_start)
    require(
        navigation_start >= 0
        and disabled_return > navigation_start
        and navigation_publish > disabled_return,
        "vision navigation path lacks an early disabled return",
    )
    constructor = source.find("VisionToDDS::VisionToDDS()")
    buffer_create = source.find("std::make_shared<tf2_ros::Buffer>", constructor)
    constructor_guard = source.find("if (!enable_vision_dds_)", constructor)
    require(
        constructor >= 0 and constructor_guard > constructor and buffer_create > constructor_guard,
        "vision constructor creates transport before the disabled guard",
    )


def verify_serial_and_source_governance(root):
    active_lock = read(root / "workspace.lock.repos")
    quarantine = read(root / "workspace.quarantine.repos")
    require(
        "src/serial_driver_ros:" not in active_lock,
        "serial appears in an active source manifest",
    )
    require(
        not (root / "workspace.repos").exists(),
        "retired moving workspace.repos manifest was restored",
    )
    require(
        "src/serial_driver_ros:" in quarantine
        and "9d8c07814ad0f64f76c5fd8fe12072aebcbef431" in quarantine,
        "serial exact quarantine lock is missing",
    )
    require(
        re.search(r"version:\s*[0-9a-f]{40}\s*$", quarantine, re.MULTILINE),
        "serial quarantine uses a moving ref",
    )

    parser = configparser.ConfigParser()
    try:
        with (root / ".gitmodules").open("r", encoding="utf-8") as stream:
            parser.read_file(stream)
    except (OSError, configparser.Error) as exc:
        raise H0Error("invalid .gitmodules: {}".format(exc))
    section = 'submodule "src/communication"'
    require(parser.has_section(section), "communication .gitmodules mapping is missing")
    require(parser.get(section, "path") == "src/communication", "communication path mismatch")
    require(
        parser.get(section, "url") == "https://github.com/BoomBoomFly/communication.git",
        "communication origin mismatch",
    )
    require(parser.get(section, "update") == "none", "communication is not fail-closed")
    result = subprocess.run(
        ["git", "ls-files", "-s", "src/communication"],
        cwd=str(root),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    require(result.returncode == 0, "cannot inspect communication gitlink")
    fields = result.stdout.split()
    require(
        len(fields) >= 2
        and fields[0] == "160000"
        and fields[1] == "eaaae53435ce706b32ee7dffc0c6643b43a12afe",
        "communication gitlink identity mismatch",
    )


def verify_launch_profile(root):
    path = root / "config/profiles/dds_only_launch.yaml"
    try:
        profile = json.loads(read(path))
    except ValueError as exc:
        raise H0Error("invalid launch profile: {}".format(exc))
    require(profile.get("production_enabled") is False, "production launch must remain disabled")
    allowlist = profile.get("production_allowlist", {})
    require(
        list(allowlist) == ["src/offboard_cpp/launch/offboard_control.launch.py"],
        "production launch allowlist changed",
    )
    forbidden = ("mavros", "MicroXRCEAgent", "serial", "mock", "realsense", "rplidar")
    serialized = json.dumps(allowlist).lower()
    require(
        not any(token.lower() in serialized for token in forbidden),
        "production allowlist contains a forbidden control/device path",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", required=True)
    args = parser.parse_args()
    root = Path(args.workspace_root).resolve()
    try:
        verify_offboard(root)
        verify_vision(root)
        verify_serial_and_source_governance(root)
        verify_launch_profile(root)
    except H0Error as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 2
    print(
        json.dumps(
            {
                "status": "PASS",
                "offboard_control_writer_files": [
                    "src/offboard_cpp/src/safety_gate_adapter.cpp"
                ],
                "production_enable_arm": False,
                "production_text_rc": False,
                "vision_enabled": False,
                "serial_production": False,
                "communication_update": "none",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
