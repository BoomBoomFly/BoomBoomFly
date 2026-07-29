#!/usr/bin/env python3
"""Download one explicitly identified PX4 ULog through read-only MAVFTP."""

import argparse
import hashlib
import json
import pathlib


ULOG_MAGIC = b"ULog\x01\x12\x35"


class DownloadError(RuntimeError):
    """A fail-closed exact ULog download error."""


def validate_content(remote_path, expected_size, content):
    if content is None:
        raise DownloadError("MAVFTP returned no data for {}".format(remote_path))
    if len(content) != expected_size:
        raise DownloadError(
            "MAVFTP size mismatch for {}: expected {}, got {}".format(
                remote_path, expected_size, len(content)
            )
        )
    if not content.startswith(ULOG_MAGIC):
        raise DownloadError(
            "downloaded file lacks ULog magic: {}".format(remote_path)
        )


def execute(args):
    from pymavlink import mavftp, mavutil

    connection = mavutil.mavlink_connection(
        args.device, autoreconnect=False, source_system=250
    )
    try:
        heartbeat = connection.wait_heartbeat(timeout=args.heartbeat_timeout_s)
        if heartbeat is None:
            raise DownloadError("no MAVLink heartbeat")
        source_system = int(heartbeat.get_srcSystem())
        source_component = int(heartbeat.get_srcComponent())
        if source_system != 1 or source_component != 1:
            raise DownloadError(
                "unexpected heartbeat source {}/{}".format(
                    source_system, source_component
                )
            )
        if int(heartbeat.autopilot) != mavutil.mavlink.MAV_AUTOPILOT_PX4:
            raise DownloadError("heartbeat is not from PX4")
        if (
            int(heartbeat.base_mode)
            & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
        ):
            raise DownloadError("vehicle is ARMED; refusing ULog download")

        ftp = mavftp.MAVFTP(
            connection,
            target_system=1,
            target_component=1,
        )
        content = ftp.read(args.remote_path, args.expected_size)
        validate_content(args.remote_path, args.expected_size, content)
        output = pathlib.Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(content)
        digest = hashlib.sha256(content).hexdigest()
        return {
            "status": "PASS",
            "remote_path": args.remote_path,
            "output": str(output),
            "size_bytes": len(content),
            "sha256": digest,
        }
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/ttyACM0")
    parser.add_argument("--remote-path", required=True)
    parser.add_argument("--expected-size", type=int, required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--heartbeat-timeout-s", type=float, default=30.0)
    args = parser.parse_args()
    if not args.remote_path.startswith("/fs/microsd/log/"):
        parser.error("--remote-path must be under /fs/microsd/log/")
    if args.expected_size <= 0:
        parser.error("--expected-size must be positive")
    try:
        result = execute(args)
    except (OSError, DownloadError, ValueError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
