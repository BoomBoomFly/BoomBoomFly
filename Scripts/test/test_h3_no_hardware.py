#!/usr/bin/env python3
"""Bounded H3 integration of production nodes on an isolated fake ROS graph.

This harness never starts PX4, an XRCE Agent, MAVROS, or a device-backed node.
Every production FMU input is remapped below /wave4b_h3/fmu/in so the real
/fmu/in graph is never used.
"""

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import rclpy
from px4_msgs.msg import OffboardControlMode
from px4_msgs.msg import RcChannels
from px4_msgs.msg import TrajectorySetpoint
from px4_msgs.msg import VehicleCommand
from px4_msgs.msg import VehicleOdometry
from rclpy.node import Node
from std_msgs.msg import Bool


OUTPUT_TOPICS = {
    "/wave4b_h3/fmu/in/trajectory_setpoint": TrajectorySetpoint,
    "/wave4b_h3/fmu/in/offboard_control_mode": OffboardControlMode,
    "/wave4b_h3/fmu/in/vehicle_command": VehicleCommand,
    "/wave4b_h3/fmu/in/vehicle_visual_odometry": VehicleOdometry,
}
OFFBOARD_OUTPUT_TOPICS = tuple(list(OUTPUT_TOPICS)[:3])
FORBIDDEN_PROCESS_MARKERS = (
    "MicroXRCEAgent",
    "micro-xrce-dds-agent",
    "mavros",
    "PX4-Autopilot/build/",
    "serial_driver",
    "realsense",
    "rplidar",
)


class H3Error(RuntimeError):
    """A fail-closed H3 validation error."""


class Spy(Node):
    def __init__(self):
        super().__init__("wave4b_h3_publisher_spy")
        self.counts = {topic: 0 for topic in OUTPUT_TOPICS}
        self.subscriptions = []
        for topic, message_type in OUTPUT_TOPICS.items():
            self.subscriptions.append(
                self.create_subscription(
                    message_type,
                    topic,
                    lambda _message, observed_topic=topic: self._observe(observed_topic),
                    10,
                )
            )
        self.rc_publisher = self.create_publisher(
            RcChannels, "/wave4b_h3/fmu/out/rc_channels", 10
        )
        self.kill_publisher = self.create_publisher(Bool, "/wave4b_h3/offboard/kill", 10)

    def _observe(self, topic):
        self.counts[topic] += 1


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--install-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--domain-id", required=True, type=int)
    parser.add_argument("--phase-seconds", type=float, default=1.0)
    return parser.parse_args()


def validate_args(args):
    install_root = Path(args.install_root).resolve()
    output_root = Path(args.output_root).resolve()
    try:
        output_root.relative_to(Path("/tmp"))
    except ValueError:
        raise H3Error("--output-root must resolve below /tmp")
    if not 1 <= args.domain_id <= 232:
        raise H3Error("--domain-id must be an explicit isolated value in 1..232")
    if os.environ.get("ROS_DOMAIN_ID") != str(args.domain_id):
        raise H3Error("ROS_DOMAIN_ID must exactly match --domain-id")
    if args.phase_seconds < 0.5 or args.phase_seconds > 5.0:
        raise H3Error("--phase-seconds must be bounded to 0.5..5.0")
    offboard = install_root / "offboard_cpp/lib/offboard_cpp/offboard_node"
    vision = install_root / "vision_to_dds/lib/vision_to_dds/vision_to_dds_node"
    for executable in (offboard, vision):
        if not executable.is_file() or not os.access(str(executable), os.X_OK):
            raise H3Error("missing executable: {}".format(executable))
    output_root.mkdir(parents=True, exist_ok=False)
    return install_root, output_root, offboard, vision


def assert_no_forbidden_processes():
    result = subprocess.run(
        ["ps", "-eo", "pid=,args="],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    own_pid = os.getpid()
    parent_pid = os.getppid()
    matches = []
    for line in result.stdout.splitlines():
        fields = line.strip().split(None, 1)
        if len(fields) != 2:
            continue
        try:
            pid = int(fields[0])
        except ValueError:
            continue
        if pid in (own_pid, parent_pid):
            continue
        if any(marker.lower() in fields[1].lower() for marker in FORBIDDEN_PROCESS_MARKERS):
            matches.append(line.strip())
    if matches:
        raise H3Error("forbidden process already running: {}".format(matches))


def spin_for(node, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=min(0.05, deadline - time.monotonic()))


def command_for_offboard(executable):
    remaps = (
        ("fmu/in/trajectory_setpoint", "/wave4b_h3/fmu/in/trajectory_setpoint"),
        ("fmu/in/offboard_control_mode", "/wave4b_h3/fmu/in/offboard_control_mode"),
        ("fmu/in/vehicle_command", "/wave4b_h3/fmu/in/vehicle_command"),
        ("fmu/out/vehicle_status_v1", "/wave4b_h3/fmu/out/vehicle_status_v1"),
        ("fmu/out/vehicle_odometry", "/wave4b_h3/fmu/out/vehicle_odometry"),
        ("fmu/out/timesync_status", "/wave4b_h3/fmu/out/timesync_status"),
        ("fmu/out/rc_channels", "/wave4b_h3/fmu/out/rc_channels"),
        ("fmu/out/vehicle_command_ack", "/wave4b_h3/fmu/out/vehicle_command_ack"),
        ("offboard/cmd", "/wave4b_h3/offboard/cmd"),
        ("offboard/cmd_mode", "/wave4b_h3/offboard/cmd_mode"),
        ("offboard/authority", "/wave4b_h3/offboard/authority"),
        ("offboard/kill", "/wave4b_h3/offboard/kill"),
        ("offboard/manual_enable", "/wave4b_h3/offboard/manual_enable"),
        ("offboard/manual_arm_enable", "/wave4b_h3/offboard/manual_arm_enable"),
        ("offboard/manual_recovery", "/wave4b_h3/offboard/manual_recovery"),
    )
    command = [
        str(executable),
        "--ros-args",
        "-p",
        "safety.expected_owner:=wave4b-h3",
        "-p",
        "safety.expected_lease:=fake-lease",
        "-p",
        "safety.expected_epoch:=fake-epoch",
        "-p",
        "takeoff_land.enable_arm:=false",
    ]
    for source, target in remaps:
        command.extend(["-r", "{}:={}".format(source, target)])
    return command


def start_process(command, log_path):
    stream = log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=stream,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    return process, stream


def stop_process(process, stream, label):
    if process.poll() is None:
        process.send_signal(signal.SIGINT)
    try:
        return_code = process.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2.0)
        stream.close()
        raise H3Error("{} did not stop after SIGINT".format(label))
    stream.close()
    if return_code != 0:
        raise H3Error("{} exited with {}".format(label, return_code))


def publisher_counts(node):
    return {
        topic: len(node.get_publishers_info_by_topic(topic))
        for topic in OUTPUT_TOPICS
    }


def assert_graph_isolated(node):
    real_fmu_inputs = sorted(
        name
        for name, _types in node.get_topic_names_and_types()
        if name.startswith("/fmu/in/")
    )
    if real_fmu_inputs:
        raise H3Error("real FMU input graph appeared: {}".format(real_fmu_inputs))


def assert_expected_publishers(node, running):
    counts = publisher_counts(node)
    expected = {
        topic: (1 if running and topic in OFFBOARD_OUTPUT_TOPICS else 0)
        for topic in OUTPUT_TOPICS
    }
    if counts != expected:
        raise H3Error("publisher inventory mismatch: expected={} actual={}".format(expected, counts))
    if running:
        for topic in OFFBOARD_OUTPUT_TOPICS:
            infos = node.get_publishers_info_by_topic(topic)
            reliability = int(infos[0].qos_profile.reliability)
            if reliability != 2:
                raise H3Error(
                    "{} publisher is not best-effort (reliability={})".format(
                        topic, reliability
                    )
                )
    return counts


def assert_zero_messages(spy, label):
    nonzero = {topic: count for topic, count in spy.counts.items() if count}
    if nonzero:
        raise H3Error("{} observed unexpected output: {}".format(label, nonzero))


def main():
    args = parse_args()
    install_root, output_root, offboard, vision = validate_args(args)
    assert_no_forbidden_processes()
    evidence = {
        "status": "FAIL",
        "hardware_accessed": False,
        "real_fmu_graph_used": False,
        "formal_sitl_run": False,
        "ros_domain_id": args.domain_id,
        "commands": [],
        "phases": [],
    }
    rclpy.init(args=[])
    spy = Spy()
    processes = []
    try:
        vision_command = [str(vision), "--ros-args", "-p", "enable_vision_dds:=false"]
        vision_process, vision_stream = start_process(
            vision_command, output_root / "vision-disabled.log"
        )
        processes.append((vision_process, vision_stream, "vision"))
        vision_return = vision_process.wait(timeout=5.0)
        vision_stream.close()
        processes.pop()
        evidence["commands"].append(
            {"name": "vision_disabled", "argv": vision_command, "exit_code": vision_return}
        )
        if vision_return != 0:
            raise H3Error("disabled vision node did not exit cleanly")

        spin_for(spy, args.phase_seconds)
        assert_graph_isolated(spy)
        assert_expected_publishers(spy, running=False)
        assert_zero_messages(spy, "disabled vision")
        evidence["phases"].append({"name": "vision_disabled", "output_count": 0})

        offboard_command = command_for_offboard(offboard)
        for run_index in (1, 2):
            process, stream = start_process(
                offboard_command, output_root / "offboard-run-{}.log".format(run_index)
            )
            processes.append((process, stream, "offboard-run-{}".format(run_index)))
            spin_for(spy, args.phase_seconds)
            if process.poll() is not None:
                raise H3Error("offboard run {} exited early".format(run_index))
            assert_graph_isolated(spy)
            graph_counts = assert_expected_publishers(spy, running=True)
            assert_zero_messages(spy, "offboard no-input run {}".format(run_index))

            rc = RcChannels()
            rc.channel_count = 1
            rc.channels[0] = 0.0
            rc.signal_lost = False
            spy.rc_publisher.publish(rc)
            kill = Bool()
            kill.data = False
            spy.kill_publisher.publish(kill)
            spin_for(spy, args.phase_seconds)
            assert_zero_messages(spy, "incomplete then stale input run {}".format(run_index))

            kill.data = True
            spy.kill_publisher.publish(kill)
            spin_for(spy, args.phase_seconds)
            assert_zero_messages(spy, "kill-latched run {}".format(run_index))

            stop_process(process, stream, "offboard-run-{}".format(run_index))
            processes.pop()
            spin_for(spy, args.phase_seconds)
            assert_expected_publishers(spy, running=False)
            assert_zero_messages(spy, "post-exit run {}".format(run_index))
            evidence["commands"].append(
                {
                    "name": "offboard_run_{}".format(run_index),
                    "argv": offboard_command,
                    "exit_code": 0,
                }
            )
            evidence["phases"].append(
                {
                    "name": "offboard_run_{}".format(run_index),
                    "publisher_inventory": graph_counts,
                    "output_count": 0,
                    "clean_exit": True,
                }
            )

        assert_no_forbidden_processes()
        evidence["status"] = "PASS"
        result_path = output_root / "h3-result.json"
        result_path.write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(evidence, sort_keys=True))
        return 0
    except (H3Error, subprocess.TimeoutExpired) as exc:
        evidence["error"] = str(exc)
        (output_root / "h3-result.json").write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print("H3 FAIL: {}".format(exc), file=sys.stderr)
        return 2
    finally:
        for process, stream, label in reversed(processes):
            try:
                stop_process(process, stream, label)
            except H3Error:
                pass
        spy.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    sys.exit(main())
