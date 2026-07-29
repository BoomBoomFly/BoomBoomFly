#!/usr/bin/env python3
"""Apply the explicitly approved PX4 circuit-breaker safety group."""

import argparse
import datetime
import hashlib
import json
import pathlib
import sys
import time


SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import px4_param_snapshot as snapshot  # noqa: E402


APPROVED_CHANGES = (
    {
        "name": "CBRK_SUPPLY_CHK",
        "before": 894281,
        "after": 0,
        "type": snapshot.MAV_PARAM_TYPE_INT32,
    },
    {
        "name": "CBRK_IO_SAFETY",
        "before": 22027,
        "after": 0,
        "type": snapshot.MAV_PARAM_TYPE_INT32,
    },
    {
        "name": "CBRK_USB_CHK",
        "before": 197848,
        "after": 0,
        "type": snapshot.MAV_PARAM_TYPE_INT32,
    },
)
ALLOWED_DERIVED_DIFFS = {"_HASH_CHECK"}
EXPECTED_PARAMETER_COUNT = 974


class TransactionError(RuntimeError):
    """A fail-closed parameter transaction error."""


def now_iso8601():
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def write_json(path, document):
    encoded = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    pathlib.Path(path).write_bytes(encoded)
    return hashlib.sha256(encoded).hexdigest()


def validate_baseline(document):
    capture = document.get("capture", {})
    parameters = document.get("parameters", {})
    if not capture.get("complete"):
        raise TransactionError("baseline snapshot is incomplete")
    if capture.get("expected_count") != EXPECTED_PARAMETER_COUNT:
        raise TransactionError("baseline expected_count is not 974")
    if len(parameters) != EXPECTED_PARAMETER_COUNT:
        raise TransactionError("baseline parameter count is not 974")
    indexes = {entry["index"] for entry in parameters.values()}
    if len(indexes) != EXPECTED_PARAMETER_COUNT:
        raise TransactionError("baseline parameter indexes are not unique")
    for change in APPROVED_CHANGES:
        entry = parameters.get(change["name"])
        if entry is None:
            raise TransactionError("baseline lacks {}".format(change["name"]))
        if entry["type"] != change["type"]:
            raise TransactionError(
                "baseline type mismatch for {}".format(change["name"])
            )
        if entry["value"] != change["before"]:
            raise TransactionError(
                "baseline value mismatch for {}: expected {}, got {}".format(
                    change["name"], change["before"], entry["value"]
                )
            )


def load_baseline(path, expected_sha256):
    actual_sha256 = sha256_file(path)
    if actual_sha256 != expected_sha256:
        raise TransactionError(
            "baseline SHA-256 mismatch: expected {}, got {}".format(
                expected_sha256, actual_sha256
            )
        )
    document = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    validate_baseline(document)
    return document, actual_sha256


def read_parameter(connection, target_system, target_component, name,
                   timeout_s=3.0, retries=3):
    encoded_name = name.encode("ascii")
    for _ in range(retries):
        connection.mav.param_request_read_send(
            target_system, target_component, encoded_name, -1
        )
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            message = connection.recv_match(
                type="PARAM_VALUE", blocking=True, timeout=0.5
            )
            if message is None or snapshot.param_name(message) != name:
                continue
            param_type = int(message.param_type)
            return {
                "index": int(message.param_index),
                "type": param_type,
                "value": snapshot.decode_param_value(
                    message.param_value, param_type
                ),
            }
    raise TransactionError("timeout reading {}".format(name))


def set_parameter(connection, target_system, target_component, change,
                  timeout_s=3.0, retries=3):
    encoded_name = change["name"].encode("ascii")
    encoded_value = snapshot.encode_param_value(
        change["after"], change["type"]
    )
    last_value = None
    for _ in range(retries):
        connection.mav.param_set_send(
            target_system,
            target_component,
            encoded_name,
            encoded_value,
            change["type"],
        )
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            message = connection.recv_match(
                type="PARAM_VALUE", blocking=True, timeout=0.5
            )
            if message is None or snapshot.param_name(message) != change["name"]:
                continue
            param_type = int(message.param_type)
            value = snapshot.decode_param_value(message.param_value, param_type)
            last_value = value
            if param_type == change["type"] and value == change["after"]:
                return {
                    "index": int(message.param_index),
                    "type": param_type,
                    "value": value,
                }
    raise TransactionError(
        "no verified PARAM_VALUE ACK for {}={} (last value {})".format(
            change["name"], change["after"], last_value
        )
    )


def parameter_diffs(before, after):
    before_parameters = before["parameters"]
    after_parameters = after["parameters"]
    differences = []
    for name in sorted(set(before_parameters) | set(after_parameters)):
        old = before_parameters.get(name)
        new = after_parameters.get(name)
        if old != new:
            differences.append({"name": name, "before": old, "after": new})
    return differences


def validate_post_snapshot(baseline, post):
    if not post.get("capture", {}).get("complete"):
        raise TransactionError("post-write snapshot is incomplete")
    if post["capture"].get("expected_count") != EXPECTED_PARAMETER_COUNT:
        raise TransactionError("post-write expected_count is not 974")
    if len(post.get("parameters", {})) != EXPECTED_PARAMETER_COUNT:
        raise TransactionError("post-write parameter count is not 974")
    indexes = {entry["index"] for entry in post["parameters"].values()}
    if len(indexes) != EXPECTED_PARAMETER_COUNT:
        raise TransactionError("post-write parameter indexes are not unique")

    differences = parameter_diffs(baseline, post)
    changed_names = {difference["name"] for difference in differences}
    expected_names = {change["name"] for change in APPROVED_CHANGES}
    missing = expected_names - changed_names
    unexpected = changed_names - expected_names - ALLOWED_DERIVED_DIFFS
    if missing:
        raise TransactionError(
            "approved parameters missing from diff: {}".format(sorted(missing))
        )
    if unexpected:
        raise TransactionError(
            "unexpected parameters changed: {}".format(sorted(unexpected))
        )
    for change in APPROVED_CHANGES:
        entry = post["parameters"].get(change["name"])
        if entry is None or entry["type"] != change["type"]:
            raise TransactionError(
                "post-write type missing/mismatched for {}".format(
                    change["name"]
                )
            )
        if entry["index"] != baseline["parameters"][change["name"]]["index"]:
            raise TransactionError(
                "post-write index changed for {}".format(change["name"])
            )
        if entry["value"] != change["after"]:
            raise TransactionError(
                "post-write value mismatch for {}".format(change["name"])
            )
    return differences


def collect_full_snapshot(connection, args, source_system, source_component):
    return snapshot.collect_parameters(
        connection,
        args.device,
        source_system,
        source_component,
        1,
        1,
        args.idle_timeout_s,
        args.overall_timeout_s,
        args.max_recovery_rounds,
        args.recovery_batch_size,
    )


def execute(args):
    from pymavlink import mavutil

    baseline, baseline_sha256 = load_baseline(
        args.baseline, args.baseline_sha256
    )
    transaction = {
        "approved_changes": list(APPROVED_CHANGES),
        "baseline": {
            "path": args.baseline,
            "sha256": baseline_sha256,
        },
        "device": args.device,
        "started_at": now_iso8601(),
        "status": "STARTED",
        "writes": [],
    }
    write_json(args.transaction_output, transaction)

    connection = mavutil.mavlink_connection(args.device, autoreconnect=False)
    changed = []
    original_error = None
    try:
        heartbeat = connection.wait_heartbeat(timeout=args.heartbeat_timeout_s)
        if heartbeat is None:
            raise TransactionError("no MAVLink heartbeat")
        source_system = int(heartbeat.get_srcSystem())
        source_component = int(heartbeat.get_srcComponent())
        base_mode = int(heartbeat.base_mode)
        autopilot = int(heartbeat.autopilot)
        if source_system != 1 or source_component != 1:
            raise TransactionError(
                "unexpected heartbeat source {}/{}".format(
                    source_system, source_component
                )
            )
        if autopilot != mavutil.mavlink.MAV_AUTOPILOT_PX4:
            raise TransactionError("heartbeat is not from PX4")
        if base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED:
            raise TransactionError("vehicle is ARMED; refusing parameter write")
        transaction["heartbeat"] = {
            "autopilot": autopilot,
            "base_mode": base_mode,
            "source_component": source_component,
            "source_system": source_system,
            "system_status": int(heartbeat.system_status),
        }

        live_before = {}
        for change in APPROVED_CHANGES:
            entry = read_parameter(connection, 1, 1, change["name"])
            live_before[change["name"]] = entry
            if entry["type"] != change["type"]:
                raise TransactionError(
                    "live type mismatch for {}".format(change["name"])
                )
            if entry["value"] != change["before"]:
                raise TransactionError(
                    "live value mismatch for {}: expected {}, got {}".format(
                        change["name"], change["before"], entry["value"]
                    )
                )
        transaction["live_before"] = live_before
        transaction["status"] = "PRECHECK_PASS"
        write_json(args.transaction_output, transaction)

        for change in APPROVED_CHANGES:
            ack = set_parameter(connection, 1, 1, change)
            changed.append(change)
            transaction["writes"].append(
                {"change": change, "ack": ack, "verified": True}
            )
            transaction["status"] = "WRITE_IN_PROGRESS"
            write_json(args.transaction_output, transaction)

        live_after = {}
        for change in APPROVED_CHANGES:
            entry = read_parameter(connection, 1, 1, change["name"])
            live_after[change["name"]] = entry
            if entry["value"] != change["after"]:
                raise TransactionError(
                    "live post-read mismatch for {}".format(change["name"])
                )
        transaction["live_after"] = live_after

        post = collect_full_snapshot(
            connection, args, source_system, source_component
        )
        post_sha256 = write_json(args.post_output, post)
        differences = validate_post_snapshot(baseline, post)
        transaction["post_snapshot"] = {
            "path": args.post_output,
            "sha256": post_sha256,
            "complete": post["capture"]["complete"],
            "count": len(post["parameters"]),
        }
        transaction["differences"] = differences
        transaction["status"] = "PASS"
        transaction["completed_at"] = now_iso8601()
        transaction_sha256 = write_json(args.transaction_output, transaction)
        return {
            "status": "PASS",
            "post_snapshot_sha256": post_sha256,
            "transaction_sha256": transaction_sha256,
            "difference_names": [item["name"] for item in differences],
        }
    except Exception as error:  # rollback is required for any partial group
        original_error = "{}: {}".format(type(error).__name__, error)
        transaction["error"] = original_error
        transaction["status"] = "FAIL_ROLLBACK_PENDING" if changed else "FAIL_PRECHECK"
        write_json(args.transaction_output, transaction)
        rollback_results = []
        rollback_ok = True
        for change in reversed(changed):
            rollback_change = dict(change)
            rollback_change["after"] = change["before"]
            try:
                ack = set_parameter(connection, 1, 1, rollback_change)
                rollback_results.append(
                    {"name": change["name"], "ack": ack, "verified": True}
                )
            except Exception as rollback_error:
                rollback_ok = False
                rollback_results.append(
                    {
                        "name": change["name"],
                        "verified": False,
                        "error": "{}: {}".format(
                            type(rollback_error).__name__, rollback_error
                        ),
                    }
                )
        transaction["rollback"] = rollback_results
        transaction["status"] = (
            "FAIL_ROLLED_BACK" if rollback_ok else "FAIL_ROLLBACK_UNVERIFIED"
        )
        transaction["completed_at"] = now_iso8601()
        write_json(args.transaction_output, transaction)
        raise TransactionError(
            "{}; rollback_status={}".format(
                original_error, transaction["status"]
            )
        )
    finally:
        connection.close()


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/ttyACM0")
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--baseline-sha256", required=True)
    parser.add_argument("--post-output", required=True)
    parser.add_argument("--transaction-output", required=True)
    parser.add_argument("--heartbeat-timeout-s", type=float, default=30.0)
    parser.add_argument("--idle-timeout-s", type=float, default=8.0)
    parser.add_argument("--overall-timeout-s", type=float, default=120.0)
    parser.add_argument("--max-recovery-rounds", type=int, default=5)
    parser.add_argument("--recovery-batch-size", type=int, default=64)
    parser.add_argument(
        "--execute-approved-circuit-breaker-group", action="store_true"
    )
    args = parser.parse_args(argv)
    if not args.execute_approved_circuit_breaker_group:
        parser.error("explicit --execute-approved-circuit-breaker-group required")
    if args.baseline_sha256 != (
        "7ff75ac24b0f91d5dcd931ad39c18eda8db068ba22316f71c227cd693e3e99fb"
    ):
        parser.error("baseline SHA-256 must match the approved live snapshot")
    return args


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = execute(args)
    except (OSError, TransactionError, snapshot.SnapshotError,
            UnicodeError, ValueError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
