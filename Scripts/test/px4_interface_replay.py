#!/usr/bin/env python3
"""Props-off PX4 interface replay for the isolated DDS integration domain.

This tool is test infrastructure.  It refuses to start unless ROS_DOMAIN_ID is
the explicitly requested non-zero domain (231 by default), and no production
launch file references it.
"""

import argparse
import math
import os
import sys
import time


EXPECTED_RATES_HZ = {
    "timesync": 1.0,
    "status": 2.0,
    "land_detected": 1.0,
    "odometry": 50.0,
}
ACK_RESULTS = {"accept", "reject", "timeout"}
RC_CHANNEL_CAPACITY = 18


def require_isolated_domain(expected_domain):
    raw = os.environ.get("ROS_DOMAIN_ID", "")
    try:
        actual = int(raw)
    except ValueError:
        raise RuntimeError("ROS_DOMAIN_ID must be an integer")
    if actual == 0 or actual != expected_domain:
        raise RuntimeError(
            "replay refused: ROS_DOMAIN_ID={} but isolated domain {} is required".format(
                raw or "<unset>", expected_domain
            )
        )


def scheduled_count(rate_hz, duration_s):
    if not math.isfinite(rate_hz) or rate_hz <= 0.0:
        raise ValueError("rate must be finite and positive")
    if not math.isfinite(duration_s) or duration_s <= 0.0:
        raise ValueError("duration must be finite and positive")
    return int(math.floor(rate_hz * duration_s + 1.0e-9))


def fixed_rc_channels(configured):
    values = [float(value) for value in configured]
    if not values or len(values) > RC_CHANNEL_CAPACITY:
        raise ValueError("RC replay requires 1..18 configured channels")
    return values + [0.0] * (RC_CHANNEL_CAPACITY - len(values))


def run_self_test():
    duration_s = 60.0
    expected = {
        "timesync": 60,
        "status": 120,
        "land_detected": 60,
        "odometry": 3000,
        "setpoint_mode": 3000,
    }
    observed = {
        name: scheduled_count(rate, duration_s)
        for name, rate in {
            **EXPECTED_RATES_HZ,
            "setpoint_mode": 50.0,
        }.items()
    }
    if observed != expected:
        raise AssertionError("frequency schedule mismatch: {}".format(observed))
    if ACK_RESULTS != {"accept", "reject", "timeout"}:
        raise AssertionError("ACK scenario set is incomplete")
    padded = fixed_rc_channels([0.0] * 8)
    if len(padded) != 18 or padded[8:] != [0.0] * 10:
        raise AssertionError("RcChannels fixed-array padding is invalid")
    print(
        "PASS px4_interface_replay self-test: duration=60s counts={} ack={}".format(
            observed, sorted(ACK_RESULTS)
        )
    )


class Px4Replay:
    def __init__(self, node, args, messages, qos_profile):
        self.node = node
        self.args = args
        self.msg = messages
        self.qos = qos_profile
        self.boot_monotonic = time.monotonic()
        self.boot_us = 10_000_000
        self.armed = False
        self.nav_state = messages["VehicleStatus"].NAVIGATION_STATE_MANUAL
        self.z_m = 0.0
        self.target_z_m = 0.0
        self.vz_m_s = 0.0
        self.land_requested = False
        self.last_motion = time.monotonic()

        self.timesync_pub = node.create_publisher(
            messages["TimesyncStatus"], "/fmu/out/timesync_status", qos_profile
        )
        self.status_pub = node.create_publisher(
            messages["VehicleStatus"], "/fmu/out/vehicle_status_v1", qos_profile
        )
        self.land_pub = node.create_publisher(
            messages["VehicleLandDetected"],
            "/fmu/out/vehicle_land_detected",
            qos_profile,
        )
        self.odom_pub = node.create_publisher(
            messages["VehicleOdometry"], "/fmu/out/vehicle_odometry", qos_profile
        )
        self.rc_pub = node.create_publisher(
            messages["RcChannels"], "/fmu/out/rc_channels", qos_profile
        )
        self.ack_pub = node.create_publisher(
            messages["VehicleCommandAck"], "/fmu/out/vehicle_command_ack", qos_profile
        )
        self.command_sub = node.create_subscription(
            messages["VehicleCommand"],
            "/fmu/in/vehicle_command",
            self.on_command,
            qos_profile,
        )
        self.setpoint_sub = node.create_subscription(
            messages["TrajectorySetpoint"],
            "/fmu/in/trajectory_setpoint",
            self.on_setpoint,
            qos_profile,
        )

        node.create_timer(1.0 / EXPECTED_RATES_HZ["timesync"], self.publish_timesync)
        node.create_timer(1.0 / EXPECTED_RATES_HZ["status"], self.publish_status)
        node.create_timer(1.0 / EXPECTED_RATES_HZ["land_detected"], self.publish_land)
        node.create_timer(1.0 / EXPECTED_RATES_HZ["odometry"], self.publish_odometry)
        node.create_timer(1.0 / args.rc_rate_hz, self.publish_rc)

    def now_us(self):
        return self.boot_us + int((time.monotonic() - self.boot_monotonic) * 1_000_000)

    def publish_timesync(self):
        message = self.msg["TimesyncStatus"]()
        message.timestamp = self.now_us()
        message.source_protocol = message.SOURCE_PROTOCOL_DDS
        self.timesync_pub.publish(message)

    def publish_status(self):
        message = self.msg["VehicleStatus"]()
        message.timestamp = self.now_us()
        message.arming_state = (
            message.ARMING_STATE_ARMED if self.armed else message.ARMING_STATE_DISARMED
        )
        message.nav_state = self.nav_state
        message.nav_state_user_intention = self.nav_state
        message.vehicle_type = message.VEHICLE_TYPE_ROTARY_WING
        message.pre_flight_checks_pass = True
        message.power_input_valid = True
        self.status_pub.publish(message)

    def publish_land(self):
        landed = abs(self.z_m) <= 0.03 and abs(self.vz_m_s) <= 0.05
        message = self.msg["VehicleLandDetected"]()
        message.timestamp = self.now_us()
        message.ground_contact = landed
        message.maybe_landed = landed
        message.landed = landed
        message.at_rest = landed
        message.close_to_ground_or_skipped_check = abs(self.z_m) <= 0.15
        self.land_pub.publish(message)

    def advance_motion(self):
        now = time.monotonic()
        dt_s = min(max(now - self.last_motion, 0.0), 0.1)
        self.last_motion = now
        target = 0.0 if self.land_requested else self.target_z_m
        error = target - self.z_m
        limit = self.args.descent_speed if error > 0.0 else self.args.ascent_speed
        self.vz_m_s = max(-limit, min(limit, error * 2.0))
        self.z_m += self.vz_m_s * dt_s
        if abs(error) <= 0.005:
            self.z_m = target
            self.vz_m_s = 0.0

    def publish_odometry(self):
        self.advance_motion()
        message = self.msg["VehicleOdometry"]()
        message.timestamp = self.now_us()
        message.timestamp_sample = message.timestamp
        message.pose_frame = message.POSE_FRAME_NED
        message.velocity_frame = message.VELOCITY_FRAME_NED
        message.position = [0.0, 0.0, float(self.z_m)]
        message.q = [1.0, 0.0, 0.0, 0.0]
        message.velocity = [0.0, 0.0, float(self.vz_m_s)]
        message.angular_velocity = [0.0, 0.0, 0.0]
        message.position_variance = [0.01, 0.01, 0.01]
        message.orientation_variance = [0.01, 0.01, 0.01]
        message.velocity_variance = [0.01, 0.01, 0.01]
        message.quality = 100
        self.odom_pub.publish(message)

    def publish_rc(self):
        message = self.msg["RcChannels"]()
        message.timestamp = self.now_us()
        message.timestamp_last_valid = message.timestamp
        message.channels = fixed_rc_channels(self.args.rc_channels)
        message.channel_count = len(self.args.rc_channels)
        message.rssi = 100
        message.signal_lost = False
        self.rc_pub.publish(message)

    def on_setpoint(self, message):
        if len(message.position) >= 3 and math.isfinite(message.position[2]):
            self.target_z_m = float(message.position[2])

    def command_result(self, command):
        command_name = {
            self.msg["VehicleCommand"].VEHICLE_CMD_DO_SET_MODE: "offboard",
            self.msg["VehicleCommand"].VEHICLE_CMD_NAV_LAND: "land",
        }.get(command.command, "other")
        if command.command == self.msg["VehicleCommand"].VEHICLE_CMD_COMPONENT_ARM_DISARM:
            command_name = "arm" if command.param1 >= 0.5 else "disarm"
        return getattr(self.args, "{}_ack".format(command_name), self.args.other_ack)

    def on_command(self, command):
        result = self.command_result(command)
        if result == "timeout":
            return
        ack = self.msg["VehicleCommandAck"]()
        ack.timestamp = self.now_us()
        ack.command = command.command
        ack.result = (
            ack.VEHICLE_CMD_RESULT_ACCEPTED
            if result == "accept"
            else ack.VEHICLE_CMD_RESULT_DENIED
        )
        ack.target_system = command.source_system
        ack.target_component = command.source_component
        ack.from_external = False
        self.ack_pub.publish(ack)
        if result != "accept":
            return
        if command.command == command.VEHICLE_CMD_DO_SET_MODE:
            self.nav_state = self.msg["VehicleStatus"].NAVIGATION_STATE_OFFBOARD
        elif command.command == command.VEHICLE_CMD_COMPONENT_ARM_DISARM:
            self.armed = command.param1 >= 0.5
        elif command.command == command.VEHICLE_CMD_NAV_LAND:
            self.land_requested = True
            self.nav_state = self.msg["VehicleStatus"].NAVIGATION_STATE_AUTO_LAND


def parse_channels(raw):
    values = [float(item.strip()) for item in raw.split(",") if item.strip()]
    if not values or len(values) > 18 or any(not math.isfinite(v) for v in values):
        raise argparse.ArgumentTypeError("rc channels require 1..18 finite values")
    if any(v < -1.0 or v > 1.0 for v in values):
        raise argparse.ArgumentTypeError("rc channels must be within [-1, 1]")
    return values


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--self-test", action="store_true")
    result.add_argument("--domain-id", type=int, default=231)
    result.add_argument("--duration", type=float, default=65.0)
    result.add_argument("--rc-rate-hz", type=float, default=20.0)
    result.add_argument(
        "--rc-channels",
        type=parse_channels,
        default=parse_channels("0,0,0,0,0,0,0,0"),
    )
    result.add_argument("--ascent-speed", type=float, default=0.3)
    result.add_argument("--descent-speed", type=float, default=0.2)
    for name in ("offboard", "arm", "land", "disarm", "other"):
        result.add_argument(
            "--{}-ack".format(name), choices=sorted(ACK_RESULTS), default="accept"
        )
    return result


def main():
    args = parser().parse_args()
    if args.self_test:
        run_self_test()
        return 0
    require_isolated_domain(args.domain_id)
    if args.duration <= 0.0 or args.rc_rate_hz <= 0.0:
        raise RuntimeError("duration and RC rate must be positive")

    import rclpy
    from px4_msgs.msg import (
        RcChannels,
        TimesyncStatus,
        TrajectorySetpoint,
        VehicleCommand,
        VehicleCommandAck,
        VehicleLandDetected,
        VehicleOdometry,
        VehicleStatus,
    )
    from rclpy.qos import qos_profile_sensor_data

    messages = {
        cls.__name__: cls
        for cls in (
            RcChannels,
            TimesyncStatus,
            TrajectorySetpoint,
            VehicleCommand,
            VehicleCommandAck,
            VehicleLandDetected,
            VehicleOdometry,
            VehicleStatus,
        )
    }
    rclpy.init()
    node = rclpy.create_node("px4_interface_replay_domain_{}".format(args.domain_id))
    Px4Replay(node, args, messages, qos_profile_sensor_data)
    deadline = time.monotonic() + args.duration
    try:
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        node.destroy_node()
        rclpy.shutdown()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, ValueError) as exc:
        print("ERROR: {}".format(exc), file=sys.stderr)
        sys.exit(2)
