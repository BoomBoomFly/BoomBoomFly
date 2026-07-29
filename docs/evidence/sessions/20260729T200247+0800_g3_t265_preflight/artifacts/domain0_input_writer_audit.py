#!/usr/bin/env python3
import json
import time

import rclpy


def main():
    rclpy.init()
    node = rclpy.create_node("g3_domain0_read_only_graph_audit")
    mandatory = {
        "/fmu/in/offboard_control_mode",
        "/fmu/in/trajectory_setpoint",
        "/fmu/in/vehicle_command",
        "/fmu/in/vehicle_visual_odometry",
    }
    observations = []
    deadline = time.monotonic() + 10.0
    try:
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.2)
            topic_map = dict(node.get_topic_names_and_types())
            input_topics = {name for name in topic_map if name.startswith("/fmu/in/")}
            counts = {}
            for topic in sorted(input_topics | mandatory):
                counts[topic] = len(node.get_publishers_info_by_topic(topic))
            observations.append(
                {
                    "elapsed_s": round(10.0 - max(0.0, deadline - time.monotonic()), 3),
                    "input_publishers": counts,
                }
            )
            time.sleep(0.3)
    finally:
        node.destroy_node()
        rclpy.shutdown()

    maxima = {}
    for observation in observations:
        for topic, count in observation["input_publishers"].items():
            maxima[topic] = max(maxima.get(topic, 0), count)
    report = {
        "domain_id": 0,
        "duration_s": 10.0,
        "samples": len(observations),
        "maximum_input_publisher_counts": maxima,
        "status": "PASS" if all(count == 0 for count in maxima.values()) else "FAIL",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
