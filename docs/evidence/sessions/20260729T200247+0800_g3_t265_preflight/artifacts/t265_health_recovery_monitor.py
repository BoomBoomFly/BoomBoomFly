#!/usr/bin/env python3
import json
import time

import rclpy
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import Int8, UInt32


class Monitor:
    def __init__(self, node):
        self.started = time.monotonic()
        self.quality_events = []
        self.epoch_events = []
        self.last_quality = None
        self.last_epoch = None
        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=20,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )
        self.quality_sub = node.create_subscription(
            Int8, "/vision/quality", self.on_quality, qos
        )
        self.epoch_sub = node.create_subscription(
            UInt32, "/vision/source_epoch", self.on_epoch, qos
        )

    def elapsed(self):
        return round(time.monotonic() - self.started, 3)

    def on_quality(self, message):
        if message.data != self.last_quality:
            self.quality_events.append({"elapsed_s": self.elapsed(), "value": message.data})
            self.last_quality = message.data

    def on_epoch(self, message):
        if message.data != self.last_epoch:
            self.epoch_events.append({"elapsed_s": self.elapsed(), "value": message.data})
            self.last_epoch = message.data


def main():
    rclpy.init()
    node = rclpy.create_node("g3_t265_health_recovery_monitor")
    monitor = Monitor(node)
    deadline = time.monotonic() + 42.0
    try:
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        topic_map = dict(node.get_topic_names_and_types())
        input_topics = {name for name in topic_map if name.startswith("/fmu/in/")}
        input_counts = {
            topic: len(node.get_publishers_info_by_topic(topic))
            for topic in sorted(
                input_topics
                | {
                    "/fmu/in/offboard_control_mode",
                    "/fmu/in/trajectory_setpoint",
                    "/fmu/in/vehicle_command",
                    "/fmu/in/vehicle_visual_odometry",
                }
            )
        }
        node.destroy_node()
        rclpy.shutdown()

    quality_values = [event["value"] for event in monitor.quality_events]
    epoch_values = [event["value"] for event in monitor.epoch_events]
    recovered = False
    if 0 in quality_values:
        zero_index = quality_values.index(0)
        recovered = 67 in quality_values[zero_index + 1 :]
    report = {
        "domain_id": 231,
        "duration_s": 42.0,
        "quality_events": monitor.quality_events,
        "source_epoch_events": monitor.epoch_events,
        "maximum_input_publisher_counts_at_end": input_counts,
        "status": (
            "PASS"
            if 67 in quality_values
            and recovered
            and len(set(epoch_values)) >= 2
            and epoch_values == sorted(epoch_values)
            and all(count == 0 for count in input_counts.values())
            else "FAIL"
        ),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
