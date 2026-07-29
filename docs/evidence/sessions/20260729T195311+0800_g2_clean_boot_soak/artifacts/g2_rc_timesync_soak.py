#!/usr/bin/env python3
import argparse
import json
import os
import time

import rclpy
from px4_msgs.msg import RcChannels, TimesyncStatus
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy


INPUT_TOPICS = (
    "/fmu/in/offboard_control_mode",
    "/fmu/in/trajectory_setpoint",
    "/fmu/in/vehicle_command",
    "/fmu/in/vehicle_visual_odometry",
)
OUTPUT_TOPICS = ("/fmu/out/rc_channels", "/fmu/out/timesync_status")


def mem_available_kib():
    with open("/proc/meminfo", encoding="utf-8") as stream:
        for line in stream:
            if line.startswith("MemAvailable:"):
                return int(line.split()[1])
    raise RuntimeError("MemAvailable missing")


def dma_headroom_kib():
    values = {}
    inside = False
    with open("/proc/zoneinfo", encoding="utf-8") as stream:
        for line in stream:
            stripped = line.strip()
            if stripped.startswith("Node ") and ", zone" in stripped:
                if inside:
                    break
                zone_fields = stripped.split()
                inside = len(zone_fields) >= 4 and zone_fields[-2:] == ["zone", "DMA"]
                continue
            if not inside:
                continue
            fields = stripped.split()
            if len(fields) == 3 and fields[:2] == ["pages", "free"]:
                values["free"] = int(fields[2])
            elif len(fields) == 2 and fields[0] == "high":
                values["high"] = int(fields[1])
            if "free" in values and "high" in values:
                break
    if set(values) != {"free", "high"}:
        raise RuntimeError("DMA zone free/high missing")
    return max(0, values["free"] - values["high"]) * os.sysconf("SC_PAGE_SIZE") // 1024


class StreamStats:
    def __init__(self):
        self.count = 0
        self.first_receive = None
        self.last_receive = None
        self.max_gap = 0.0
        self.first_timestamp = None
        self.last_timestamp = None
        self.nonincreasing_timestamps = 0

    def add(self, timestamp):
        now = time.monotonic()
        if self.first_receive is None:
            self.first_receive = now
            self.first_timestamp = timestamp
        if self.last_receive is not None:
            self.max_gap = max(self.max_gap, now - self.last_receive)
        if self.last_timestamp is not None and timestamp <= self.last_timestamp:
            self.nonincreasing_timestamps += 1
        self.last_receive = now
        self.last_timestamp = timestamp
        self.count += 1

    def rate_hz(self):
        if self.count < 2 or self.last_receive <= self.first_receive:
            return 0.0
        return (self.count - 1) / (self.last_receive - self.first_receive)

    def result(self):
        return {
            "count": self.count,
            "rate_hz": round(self.rate_hz(), 6),
            "max_gap_s": round(self.max_gap, 6),
            "first_timestamp_us": self.first_timestamp,
            "last_timestamp_us": self.last_timestamp,
            "nonincreasing_timestamps": self.nonincreasing_timestamps,
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=620.0)
    args = parser.parse_args()
    if os.environ.get("ROS_DOMAIN_ID") != "0":
        raise SystemExit("ROS_DOMAIN_ID=0 required")

    rclpy.init()
    node = rclpy.create_node("g2_rc_timesync_read_only_soak")
    qos = QoSProfile(
        history=HistoryPolicy.KEEP_LAST,
        depth=20,
        reliability=ReliabilityPolicy.BEST_EFFORT,
        durability=DurabilityPolicy.TRANSIENT_LOCAL,
    )
    rc = StreamStats()
    timesync = StreamStats()
    rc_channel_counts = set()
    rc_signal_lost_values = set()

    def on_rc(message):
        rc.add(int(message.timestamp))
        rc_channel_counts.add(int(message.channel_count))
        rc_signal_lost_values.add(bool(message.signal_lost))

    def on_timesync(message):
        timesync.add(int(message.timestamp))

    node.create_subscription(RcChannels, "/fmu/out/rc_channels", on_rc, qos)
    node.create_subscription(TimesyncStatus, "/fmu/out/timesync_status", on_timesync, qos)

    start = time.monotonic()
    next_graph = start
    next_progress = start + 30.0
    graph_samples = 0
    input_writer_violations = []
    output_writer_violations = []
    min_mem_kib = None
    min_dma_kib = None

    try:
        while time.monotonic() - start < args.duration:
            rclpy.spin_once(node, timeout_sec=0.1)
            now = time.monotonic()
            if now >= next_graph:
                graph_samples += 1
                for topic in INPUT_TOPICS:
                    count = len(node.get_publishers_info_by_topic(topic))
                    if count != 0:
                        input_writer_violations.append(
                            {"elapsed_s": round(now - start, 3), "topic": topic, "count": count}
                        )
                for topic in OUTPUT_TOPICS:
                    count = len(node.get_publishers_info_by_topic(topic))
                    if count != 1:
                        output_writer_violations.append(
                            {"elapsed_s": round(now - start, 3), "topic": topic, "count": count}
                        )
                current_mem = mem_available_kib()
                current_dma = dma_headroom_kib()
                min_mem_kib = current_mem if min_mem_kib is None else min(min_mem_kib, current_mem)
                min_dma_kib = current_dma if min_dma_kib is None else min(min_dma_kib, current_dma)
                next_graph += 5.0
            if now >= next_progress:
                print(
                    json.dumps(
                        {
                            "progress_s": round(now - start, 1),
                            "rc_count": rc.count,
                            "timesync_count": timesync.count,
                            "rc_max_gap_s": round(rc.max_gap, 6),
                            "timesync_max_gap_s": round(timesync.max_gap, 6),
                            "min_mem_available_kib": min_mem_kib,
                            "min_dma_headroom_kib": min_dma_kib,
                            "input_writer_violations": len(input_writer_violations),
                            "output_writer_violations": len(output_writer_violations),
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
                next_progress += 30.0
    finally:
        elapsed = time.monotonic() - start
        node.destroy_node()
        rclpy.shutdown()

    failures = []
    if elapsed < 600.0:
        failures.append("duration_below_600s")
    if rc.count < elapsed * 20.0:
        failures.append("rc_rate_too_low")
    if timesync.count < elapsed * 0.5:
        failures.append("timesync_rate_too_low")
    if rc.max_gap > 0.5:
        failures.append("rc_gap_above_0.5s")
    if timesync.max_gap > 2.5:
        failures.append("timesync_gap_above_2.5s")
    if rc.nonincreasing_timestamps:
        failures.append("rc_timestamp_nonincreasing")
    if timesync.nonincreasing_timestamps:
        failures.append("timesync_timestamp_nonincreasing")
    if input_writer_violations:
        failures.append("input_writer_detected")
    if output_writer_violations:
        failures.append("output_writer_count_not_one")
    if min_mem_kib is None or min_mem_kib < 1024 * 1024:
        failures.append("memory_below_guard_threshold")
    if min_dma_kib is None or min_dma_kib < 256 * 1024:
        failures.append("dma_headroom_below_guard_threshold")

    result = {
        "status": "PASS" if not failures else "FAIL",
        "duration_s": round(elapsed, 3),
        "failures": failures,
        "rc": rc.result(),
        "timesync": timesync.result(),
        "rc_channel_counts": sorted(rc_channel_counts),
        "rc_signal_lost_values": sorted(rc_signal_lost_values),
        "graph_samples": graph_samples,
        "input_writer_violations": input_writer_violations,
        "output_writer_violations": output_writer_violations,
        "min_mem_available_kib": min_mem_kib,
        "min_dma_headroom_kib": min_dma_kib,
    }
    print("FINAL " + json.dumps(result, sort_keys=True), flush=True)
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
