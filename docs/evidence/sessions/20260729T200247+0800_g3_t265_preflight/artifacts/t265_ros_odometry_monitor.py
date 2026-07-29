#!/usr/bin/env python3
import json
import math
import time
from collections import Counter

import rclpy
from nav_msgs.msg import Odometry
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy


class Monitor:
    def __init__(self, node):
        self.node = node
        self.first_wall = None
        self.previous_stamp_ns = None
        self.samples = 0
        self.timestamp_regressions = 0
        self.non_finite_values = 0
        self.invalid_quaternions = 0
        self.max_gap_ms = 0.0
        self.min_qnorm = math.inf
        self.max_qnorm = 0.0
        self.frames = Counter()
        self.children = Counter()
        self.pose_variance = Counter()
        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=20,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )
        self.subscription = node.create_subscription(
            Odometry, "/t265/pose/sample", self.callback, qos
        )

    def callback(self, message):
        now = time.monotonic()
        if self.first_wall is None:
            self.first_wall = now
        stamp_ns = message.header.stamp.sec * 1_000_000_000 + message.header.stamp.nanosec
        if self.previous_stamp_ns is not None:
            if stamp_ns <= self.previous_stamp_ns:
                self.timestamp_regressions += 1
            else:
                self.max_gap_ms = max(
                    self.max_gap_ms, (stamp_ns - self.previous_stamp_ns) / 1_000_000.0
                )
        self.previous_stamp_ns = stamp_ns
        p = message.pose.pose.position
        q = message.pose.pose.orientation
        v = message.twist.twist.linear
        w = message.twist.twist.angular
        values = [p.x, p.y, p.z, q.x, q.y, q.z, q.w, v.x, v.y, v.z, w.x, w.y, w.z]
        self.non_finite_values += sum(not math.isfinite(value) for value in values)
        qnorm = math.sqrt(q.x * q.x + q.y * q.y + q.z * q.z + q.w * q.w)
        if not math.isfinite(qnorm) or not 0.99 <= qnorm <= 1.01:
            self.invalid_quaternions += 1
        self.min_qnorm = min(self.min_qnorm, qnorm)
        self.max_qnorm = max(self.max_qnorm, qnorm)
        self.frames[message.header.frame_id] += 1
        self.children[message.child_frame_id] += 1
        self.pose_variance[f"{message.pose.covariance[0]:.9g}"] += 1
        self.samples += 1

    def report(self):
        span = 0.0 if self.first_wall is None else time.monotonic() - self.first_wall
        return {
            "domain_id": 231,
            "topic": "/t265/pose/sample",
            "elapsed_from_first_sample_s": round(span, 6),
            "samples": self.samples,
            "rate_hz": round(self.samples / span, 6) if span > 0 else 0.0,
            "max_stamp_gap_ms": round(self.max_gap_ms, 6),
            "timestamp_regressions": self.timestamp_regressions,
            "non_finite_values": self.non_finite_values,
            "invalid_quaternion_samples": self.invalid_quaternions,
            "quaternion_norm_min": self.min_qnorm if self.samples else None,
            "quaternion_norm_max": self.max_qnorm if self.samples else None,
            "frame_ids": dict(self.frames),
            "child_frame_ids": dict(self.children),
            "pose_covariance_0_counts": dict(self.pose_variance),
        }


def main():
    rclpy.init()
    node = rclpy.create_node("g3_t265_ros_odometry_monitor")
    monitor = Monitor(node)
    overall_deadline = time.monotonic() + 70.0
    try:
        while time.monotonic() < overall_deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
            if monitor.first_wall is not None and time.monotonic() - monitor.first_wall >= 60.0:
                break
    finally:
        node.destroy_node()
        rclpy.shutdown()
    report = monitor.report()
    expected_frames = report["frame_ids"] == {"odom_frame": monitor.samples}
    expected_children = report["child_frame_ids"] == {"t265_pose_frame": monitor.samples}
    report["status"] = (
        "PASS"
        if monitor.samples >= 6000
        and monitor.timestamp_regressions == 0
        and monitor.non_finite_values == 0
        and monitor.invalid_quaternions == 0
        and expected_frames
        and expected_children
        else "FAIL"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
