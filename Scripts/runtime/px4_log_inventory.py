#!/usr/bin/env python3
"""Read the PX4 MAVLink log inventory without changing vehicle state."""

import argparse
import datetime
import hashlib
import json
import pathlib
import time


class InventoryError(RuntimeError):
    """A fail-closed MAVLink log inventory error."""


def now_iso8601():
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()


def collect_inventory(connection, device, heartbeat_timeout_s, timeout_s):
    from pymavlink import mavutil

    heartbeat = connection.wait_heartbeat(timeout=heartbeat_timeout_s)
    if heartbeat is None:
        raise InventoryError("no MAVLink heartbeat")
    source_system = int(heartbeat.get_srcSystem())
    source_component = int(heartbeat.get_srcComponent())
    if source_system != 1 or source_component != 1:
        raise InventoryError(
            "unexpected heartbeat source {}/{}".format(
                source_system, source_component
            )
        )
    if int(heartbeat.autopilot) != mavutil.mavlink.MAV_AUTOPILOT_PX4:
        raise InventoryError("heartbeat is not from PX4")
    if int(heartbeat.base_mode) & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED:
        raise InventoryError("vehicle is ARMED; refusing inventory request")

    connection.mav.log_request_list_send(1, 1, 0, 0xFFFF)
    entries = {}
    expected_count = None
    last_log_num = None
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        message = connection.recv_match(
            type="LOG_ENTRY", blocking=True, timeout=1.0
        )
        if message is None:
            if expected_count is not None and len(entries) >= expected_count:
                break
            continue
        expected_count = int(message.num_logs)
        last_log_num = int(message.last_log_num)
        log_id = int(message.id)
        entries[log_id] = {
            "id": log_id,
            "size_bytes": int(message.size),
            "time_utc": int(message.time_utc),
        }
        if len(entries) >= expected_count:
            break

    complete = expected_count is not None and len(entries) >= expected_count
    return {
        "capture": {
            "complete": complete,
            "device": device,
            "expected_count": expected_count,
            "last_log_num": last_log_num,
            "received_count": len(entries),
            "source_component": source_component,
            "source_system": source_system,
            "timestamp": now_iso8601(),
        },
        "entries": [entries[key] for key in sorted(entries)],
    }


def write_document(path, document):
    encoded = (
        json.dumps(document, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    pathlib.Path(path).write_bytes(encoded)
    return hashlib.sha256(encoded).hexdigest()


def main():
    from pymavlink import mavutil

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/ttyACM0")
    parser.add_argument("--output", required=True)
    parser.add_argument("--heartbeat-timeout-s", type=float, default=30.0)
    parser.add_argument("--timeout-s", type=float, default=30.0)
    args = parser.parse_args()

    connection = mavutil.mavlink_connection(
        args.device, autoreconnect=False
    )
    try:
        document = collect_inventory(
            connection,
            args.device,
            args.heartbeat_timeout_s,
            args.timeout_s,
        )
    except (OSError, InventoryError, ValueError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}))
        return 1
    finally:
        connection.close()

    digest = write_document(args.output, document)
    summary = {
        "complete": document["capture"]["complete"],
        "entries": document["capture"]["received_count"],
        "last_log_num": document["capture"]["last_log_num"],
        "output": args.output,
        "sha256": digest,
        "status": "PASS" if document["capture"]["complete"] else "FAIL",
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if document["capture"]["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
