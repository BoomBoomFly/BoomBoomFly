#!/usr/bin/env python3
"""Read-only Domain 0 probe for the authorized G4-A2 RC/Agent loss test."""

import argparse
import json
import os
import pathlib
import time


OUTPUT_TOPICS = (
    "/fmu/out/rc_channels",
    "/fmu/out/failsafe_flags",
    "/fmu/out/vehicle_status_v1",
    "/fmu/out/vehicle_land_detected",
    "/fmu/out/timesync_status",
)


class StreamStats:
    def __init__(self):
        self.count = 0
        self.first_timestamp = None
        self.last_timestamp = None
        self.nonincreasing_timestamps = 0

    def add(self, timestamp):
        timestamp = int(timestamp)
        if self.first_timestamp is None:
            self.first_timestamp = timestamp
        if self.last_timestamp is not None and timestamp <= self.last_timestamp:
            self.nonincreasing_timestamps += 1
        self.last_timestamp = timestamp
        self.count += 1

    def result(self):
        return {
            "count": self.count,
            "first_timestamp_us": self.first_timestamp,
            "last_timestamp_us": self.last_timestamp,
            "nonincreasing_timestamps": self.nonincreasing_timestamps,
        }


class ProbeState:
    def __init__(self):
        self.streams = {
            name: StreamStats()
            for name in ("rc", "failsafe", "status", "land", "timesync")
        }
        self.events = []
        self._last_values = {}
        self.rc_online_seen = False
        self.rc_loss_seen = False
        self.rc_recovery_seen = False
        self.manual_loss_seen = False
        self.arming_states = set()
        self.nav_states = set()
        self.failsafe_values = set()
        self.landed_values = set()
        self.agent_present_seen = False
        self.agent_absent_seen = False
        self.agent_absent_since = None
        self.graph_samples = 0
        self.publisher_snapshots = []
        self.input_writer_violations = []

    def _transition(self, name, value, elapsed_s, timestamp_us):
        previous = self._last_values.get(name, object())
        if previous != value:
            self.events.append({
                "elapsed_s": round(float(elapsed_s), 3),
                "event": name,
                "previous": None if name not in self._last_values else previous,
                "value": value,
                "timestamp_us": int(timestamp_us),
            })
            self._last_values[name] = value

    def on_rc(self, message, elapsed_s):
        self.streams["rc"].add(message.timestamp)
        lost = bool(message.signal_lost)
        previous = self._last_values.get("rc_signal_lost")
        if not lost:
            self.rc_online_seen = True
        if lost:
            self.rc_loss_seen = True
        if previous is True and not lost:
            self.rc_recovery_seen = True
        self._transition("rc_signal_lost", lost, elapsed_s, message.timestamp)

    def on_failsafe(self, message, elapsed_s):
        self.streams["failsafe"].add(message.timestamp)
        lost = bool(message.manual_control_signal_lost)
        self.manual_loss_seen = self.manual_loss_seen or lost
        self._transition(
            "manual_control_signal_lost", lost, elapsed_s, message.timestamp
        )

    def on_status(self, message, elapsed_s):
        self.streams["status"].add(message.timestamp)
        arming_state = int(message.arming_state)
        nav_state = int(message.nav_state)
        failsafe = bool(message.failsafe)
        self.arming_states.add(arming_state)
        self.nav_states.add(nav_state)
        self.failsafe_values.add(failsafe)
        self._transition("arming_state", arming_state, elapsed_s, message.timestamp)
        self._transition("nav_state", nav_state, elapsed_s, message.timestamp)
        self._transition("vehicle_failsafe", failsafe, elapsed_s, message.timestamp)

    def on_land(self, message, elapsed_s):
        self.streams["land"].add(message.timestamp)
        landed = bool(message.landed)
        self.landed_values.add(landed)
        self._transition("landed", landed, elapsed_s, message.timestamp)

    def on_timesync(self, message):
        self.streams["timesync"].add(message.timestamp)

    def on_graph(self, elapsed_s, output_counts, input_counts):
        self.graph_samples += 1
        snapshot = {
            "elapsed_s": round(float(elapsed_s), 3),
            "outputs": dict(sorted(output_counts.items())),
            "inputs": dict(sorted(input_counts.items())),
        }
        self.publisher_snapshots.append(snapshot)
        for topic, count in input_counts.items():
            if count:
                self.input_writer_violations.append({
                    "elapsed_s": snapshot["elapsed_s"],
                    "topic": topic,
                    "count": int(count),
                })
        all_present = all(output_counts.get(topic) == 1 for topic in OUTPUT_TOPICS)
        all_absent = all(output_counts.get(topic) == 0 for topic in OUTPUT_TOPICS)
        if all_present:
            if not self.agent_present_seen:
                self.events.append({
                    "elapsed_s": snapshot["elapsed_s"],
                    "event": "agent_publishers_present",
                })
            self.agent_present_seen = True
            self.agent_absent_since = None
        elif self.agent_present_seen and all_absent:
            if not self.agent_absent_seen:
                self.events.append({
                    "elapsed_s": snapshot["elapsed_s"],
                    "event": "agent_publishers_absent",
                })
                self.agent_absent_since = float(elapsed_s)
            self.agent_absent_seen = True

    def action(self):
        if not self.agent_present_seen or not self.rc_online_seen:
            return "WAIT_BASELINE"
        if not self.rc_loss_seen:
            return "TURN_RC_OFF"
        if not self.manual_loss_seen:
            return "WAIT_PX4_MANUAL_LOSS"
        if not self.rc_recovery_seen:
            return "TURN_RC_ON"
        if not self.agent_absent_seen:
            return "READY_FOR_AGENT_EXIT"
        return "COMPLETE"

    def result(self, duration_s):
        failures = []
        if not self.rc_online_seen:
            failures.append("rc_online_not_observed")
        if not self.rc_loss_seen:
            failures.append("rc_signal_lost_not_observed")
        if not self.manual_loss_seen:
            failures.append("px4_manual_control_loss_not_observed")
        if not self.rc_recovery_seen:
            failures.append("rc_recovery_not_observed")
        if self.arming_states != {1}:
            failures.append("vehicle_not_always_disarmed")
        if not self.landed_values or self.landed_values != {True}:
            failures.append("vehicle_not_always_landed")
        if not self.agent_present_seen:
            failures.append("agent_publishers_never_present")
        if not self.agent_absent_seen:
            failures.append("agent_exit_not_observed")
        if self.input_writer_violations:
            failures.append("fmu_input_writer_detected")
        for name, stream in self.streams.items():
            if stream.count == 0:
                failures.append(name + "_stream_missing")
            if stream.nonincreasing_timestamps:
                failures.append(name + "_timestamp_nonincreasing")
        return {
            "status": "PASS" if not failures else "FAIL",
            "duration_s": round(float(duration_s), 3),
            "failures": failures,
            "action": self.action(),
            "streams": {name: stream.result() for name, stream in self.streams.items()},
            "events": self.events,
            "rc_online_seen": self.rc_online_seen,
            "rc_loss_seen": self.rc_loss_seen,
            "rc_recovery_seen": self.rc_recovery_seen,
            "manual_loss_seen": self.manual_loss_seen,
            "arming_states": sorted(self.arming_states),
            "nav_states": sorted(self.nav_states),
            "failsafe_values": sorted(self.failsafe_values),
            "landed_values": sorted(self.landed_values),
            "agent_present_seen": self.agent_present_seen,
            "agent_absent_seen": self.agent_absent_seen,
            "graph_samples": self.graph_samples,
            "publisher_snapshots": self.publisher_snapshots,
            "input_writer_violations": self.input_writer_violations,
        }


def write_json(path, document):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration-s", type=float, default=300.0)
    parser.add_argument("--graph-period-s", type=float, default=1.0)
    parser.add_argument("--post-agent-loss-s", type=float, default=5.0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    if os.environ.get("ROS_DOMAIN_ID") != "0":
        parser.error("production probe requires explicit ROS_DOMAIN_ID=0")
    if min(args.duration_s, args.graph_period_s, args.post_agent_loss_s) <= 0:
        parser.error("durations must be positive")

    import rclpy
    from px4_msgs.msg import (
        FailsafeFlags, RcChannels, TimesyncStatus, VehicleLandDetected,
        VehicleStatus,
    )
    from rclpy.qos import (
        DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy,
    )

    rclpy.init()
    node = rclpy.create_node("g4_a2_rc_agent_loss_read_only_probe")
    qos = QoSProfile(
        history=HistoryPolicy.KEEP_LAST,
        depth=20,
        reliability=ReliabilityPolicy.BEST_EFFORT,
        durability=DurabilityPolicy.TRANSIENT_LOCAL,
    )
    state = ProbeState()
    started = time.monotonic()

    def elapsed():
        return time.monotonic() - started

    node.create_subscription(
        RcChannels, OUTPUT_TOPICS[0], lambda msg: state.on_rc(msg, elapsed()), qos
    )
    node.create_subscription(
        FailsafeFlags, OUTPUT_TOPICS[1],
        lambda msg: state.on_failsafe(msg, elapsed()), qos,
    )
    node.create_subscription(
        VehicleStatus, OUTPUT_TOPICS[2],
        lambda msg: state.on_status(msg, elapsed()), qos,
    )
    node.create_subscription(
        VehicleLandDetected, OUTPUT_TOPICS[3],
        lambda msg: state.on_land(msg, elapsed()), qos,
    )
    node.create_subscription(
        TimesyncStatus, OUTPUT_TOPICS[4], lambda msg: state.on_timesync(msg), qos
    )

    next_graph = started
    next_progress = started
    interrupted = False
    try:
        while elapsed() < args.duration_s:
            rclpy.spin_once(node, timeout_sec=0.1)
            now = time.monotonic()
            if now >= next_graph:
                topic_names = {name for name, unused in node.get_topic_names_and_types()}
                input_topics = sorted(name for name in topic_names if name.startswith("/fmu/in/"))
                input_counts = {
                    topic: len(node.get_publishers_info_by_topic(topic))
                    for topic in input_topics
                }
                output_counts = {
                    topic: len(node.get_publishers_info_by_topic(topic))
                    for topic in OUTPUT_TOPICS
                }
                state.on_graph(elapsed(), output_counts, input_counts)
                next_graph = now + args.graph_period_s
            if now >= next_progress:
                print(json.dumps({
                    "elapsed_s": round(elapsed(), 1),
                    "action": state.action(),
                    "rc_count": state.streams["rc"].count,
                    "status_count": state.streams["status"].count,
                    "input_writer_violations": len(state.input_writer_violations),
                }, sort_keys=True), flush=True)
                next_progress = now + 1.0
            if (state.agent_absent_since is not None and
                    elapsed() - state.agent_absent_since >= args.post_agent_loss_s):
                break
    except KeyboardInterrupt:
        interrupted = True
    finally:
        total = elapsed()
        result = state.result(total)
        result["interrupted"] = interrupted
        write_json(args.output, result)
        print("FINAL " + json.dumps(result, sort_keys=True), flush=True)
        node.destroy_node()
        rclpy.shutdown()
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
