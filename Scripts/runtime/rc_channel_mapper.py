#!/usr/bin/env python3
"""Read-only, fail-closed capture of one explicitly authorized RC switch."""

import argparse
import hashlib
import json
import math
import pathlib
import statistics
import time


RC_TOPIC = "/fmu/out/rc_channels"
CHANNEL_COUNT = 18


class CaptureError(RuntimeError):
    """An RC capture invariant was violated."""


def percentile(values, fraction):
    values = sorted(float(value) for value in values)
    if not values:
        raise CaptureError("cannot summarize an empty channel")
    position = (len(values) - 1) * float(fraction)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return values[lower]
    weight = position - lower
    return values[lower] * (1.0 - weight) + values[upper] * weight


def sha256_bytes(content):
    return hashlib.sha256(content).hexdigest()


def encode_json(document):
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")


class CaptureState:
    def __init__(self, stages):
        self.stages = tuple(stages)
        self.frames = []
        self.last_timestamp = None
        self.failures = []
        self.graph_samples = 0

    def fail(self, reason):
        if reason not in self.failures:
            self.failures.append(reason)

    def on_graph(self, rc_publishers, input_publishers):
        self.graph_samples += 1
        if int(rc_publishers) != 1:
            self.fail("rc_publisher_count_not_one")
        if any(int(count) != 0 for count in input_publishers.values()):
            self.fail("fmu_input_writer_detected")

    def on_message(self, message, elapsed_s, stage):
        timestamp = int(message.timestamp)
        channels = [float(value) for value in message.channels]
        function = [int(value) for value in message.function]
        if stage not in self.stages:
            self.fail("unknown_stage")
        if timestamp <= 0:
            self.fail("invalid_timestamp")
        if self.last_timestamp is not None and timestamp <= self.last_timestamp:
            self.fail("timestamp_nonincreasing")
        self.last_timestamp = timestamp
        if int(message.channel_count) != CHANNEL_COUNT:
            self.fail("channel_count_not_18")
        if len(channels) != CHANNEL_COUNT:
            self.fail("channel_array_not_18")
        if bool(message.signal_lost):
            self.fail("rc_signal_lost")
        if any(not math.isfinite(value) or value < -1.0 or value > 1.0
               for value in channels):
            self.fail("invalid_channel_value")
        self.frames.append({
            "channel_count": int(message.channel_count),
            "channels": channels,
            "elapsed_s": round(float(elapsed_s), 6),
            "frame_drop_count": int(message.frame_drop_count),
            "function": function,
            "rssi": int(message.rssi),
            "signal_lost": bool(message.signal_lost),
            "stage": stage,
            "timestamp": timestamp,
            "timestamp_last_valid": int(message.timestamp_last_valid),
        })

    def summary(self):
        if not self.frames:
            self.fail("no_rc_samples")
        if self.graph_samples == 0:
            self.fail("no_graph_samples")
        stage_counts = {
            stage: sum(frame["stage"] == stage for frame in self.frames)
            for stage in self.stages
        }
        if any(count == 0 for count in stage_counts.values()):
            self.fail("stage_without_samples")

        channels = []
        if self.frames and all(len(frame["channels"]) == CHANNEL_COUNT
                               for frame in self.frames):
            for index in range(CHANNEL_COUNT):
                values = [frame["channels"][index] for frame in self.frames]
                per_stage = {}
                for stage in self.stages:
                    stage_values = [
                        frame["channels"][index]
                        for frame in self.frames
                        if frame["stage"] == stage
                    ]
                    if stage_values:
                        per_stage[stage] = {
                            "max": max(stage_values),
                            "median": statistics.median(stage_values),
                            "min": min(stage_values),
                            "p01": percentile(stage_values, 0.01),
                            "p99": percentile(stage_values, 0.99),
                        }
                channels.append({
                    "index_zero_based": index,
                    "max": max(values),
                    "median": statistics.median(values),
                    "min": min(values),
                    "per_stage": per_stage,
                    "rc_channel_one_based": index + 1,
                    "span": max(values) - min(values),
                })
        return {
            "channels": channels,
            "failures": list(self.failures),
            "frame_count": len(self.frames),
            "graph_samples": self.graph_samples,
            "stage_counts": stage_counts,
            "stages": list(self.stages),
            "status": "PASS" if not self.failures else "FAIL",
        }


def write_capture(raw_path, summary_path, state, metadata):
    raw_content = b"".join(
        (json.dumps(frame, sort_keys=True) + "\n").encode("utf-8")
        for frame in state.frames
    )
    raw_path = pathlib.Path(raw_path)
    summary_path = pathlib.Path(summary_path)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(raw_content)
    document = state.summary()
    document["metadata"] = metadata
    document["raw"] = {
        "path": str(raw_path),
        "sha256": sha256_bytes(raw_content),
    }
    summary_content = encode_json(document)
    summary_path.write_bytes(summary_content)
    return {
        "raw_sha256": document["raw"]["sha256"],
        "status": document["status"],
        "summary_sha256": sha256_bytes(summary_content),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--switch-label", required=True)
    parser.add_argument("--stages", required=True,
                        help="comma-separated observed positions/cycles")
    parser.add_argument("--stage-duration-s", type=float, default=5.0)
    parser.add_argument("--raw-output", required=True)
    parser.add_argument("--summary-output", required=True)
    args = parser.parse_args(argv)
    stages = tuple(stage.strip() for stage in args.stages.split(",") if stage.strip())
    if not stages or len(set(stages)) != len(stages):
        parser.error("--stages must contain unique non-empty labels")
    if args.stage_duration_s < 3.0:
        parser.error("--stage-duration-s must be at least 3 seconds")

    import os
    if os.environ.get("ROS_DOMAIN_ID") != "0":
        parser.error("capture requires explicit ROS_DOMAIN_ID=0")
    import rclpy
    from px4_msgs.msg import RcChannels
    from rclpy.qos import (
        DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy,
    )

    rclpy.init()
    node = rclpy.create_node("rc_channel_mapper_read_only")
    qos = QoSProfile(
        history=HistoryPolicy.KEEP_LAST,
        depth=20,
        reliability=ReliabilityPolicy.BEST_EFFORT,
        durability=DurabilityPolicy.VOLATILE,
    )
    state = CaptureState(stages)
    started = time.monotonic()
    total_duration = len(stages) * args.stage_duration_s

    def elapsed():
        return time.monotonic() - started

    def current_stage():
        index = min(int(elapsed() // args.stage_duration_s), len(stages) - 1)
        return stages[index]

    node.create_subscription(
        RcChannels,
        RC_TOPIC,
        lambda message: state.on_message(message, elapsed(), current_stage()),
        qos,
    )
    next_graph = started
    announced_stage = None
    try:
        while elapsed() < total_duration and not state.failures:
            stage = current_stage()
            if stage != announced_stage:
                print(json.dumps({"observe_stage": stage}, sort_keys=True), flush=True)
                announced_stage = stage
            rclpy.spin_once(node, timeout_sec=0.1)
            now = time.monotonic()
            if now >= next_graph:
                names = {name for name, unused in node.get_topic_names_and_types()}
                inputs = sorted(name for name in names if name.startswith("/fmu/in/"))
                state.on_graph(
                    len(node.get_publishers_info_by_topic(RC_TOPIC)),
                    {
                        topic: len(node.get_publishers_info_by_topic(topic))
                        for topic in inputs
                    },
                )
                next_graph = now + 0.5
    except KeyboardInterrupt:
        state.fail("capture_interrupted")
    finally:
        result = write_capture(
            args.raw_output,
            args.summary_output,
            state,
            {
                "stage_duration_s": args.stage_duration_s,
                "switch_label": args.switch_label,
            },
        )
        node.destroy_node()
        rclpy.shutdown()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
