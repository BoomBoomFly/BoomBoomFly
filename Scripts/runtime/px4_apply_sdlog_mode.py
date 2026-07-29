#!/usr/bin/env python3
"""Apply the explicitly approved temporary PX4 SDLOG_MODE transaction."""

import argparse
import json
import pathlib
import string
import sys


SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import px4_apply_approved_circuit_breakers as transaction_base  # noqa: E402
import px4_param_snapshot as snapshot  # noqa: E402


EXPECTED_PARAMETER_COUNT = 974
ALLOWED_DERIVED_DIFFS = {"_HASH_CHECK"}
MODE_CHANGES = {
    "enable": {
        "name": "SDLOG_MODE",
        "before": 0,
        "after": 2,
        "type": snapshot.MAV_PARAM_TYPE_INT32,
    },
    "rollback": {
        "name": "SDLOG_MODE",
        "before": 2,
        "after": 0,
        "type": snapshot.MAV_PARAM_TYPE_INT32,
    },
}
REQUIRED_COMPANION_VALUES = {
    "SDLOG_BOOT_BAT": 0,
    "SDLOG_PROFILE": 1,
}


class TransactionError(RuntimeError):
    """A fail-closed SD logging parameter transaction error."""


def validate_snapshot_shape(document, label):
    capture = document.get("capture", {})
    parameters = document.get("parameters", {})
    if not capture.get("complete"):
        raise TransactionError("{} snapshot is incomplete".format(label))
    if capture.get("expected_count") != EXPECTED_PARAMETER_COUNT:
        raise TransactionError(
            "{} expected_count is not {}".format(
                label, EXPECTED_PARAMETER_COUNT
            )
        )
    if len(parameters) != EXPECTED_PARAMETER_COUNT:
        raise TransactionError(
            "{} parameter count is not {}".format(
                label, EXPECTED_PARAMETER_COUNT
            )
        )
    indexes = {entry["index"] for entry in parameters.values()}
    if len(indexes) != EXPECTED_PARAMETER_COUNT:
        raise TransactionError(
            "{} parameter indexes are not unique".format(label)
        )


def validate_baseline(document, change):
    validate_snapshot_shape(document, "baseline")
    parameters = document["parameters"]
    target = parameters.get(change["name"])
    if target is None:
        raise TransactionError("baseline lacks {}".format(change["name"]))
    if target["type"] != change["type"]:
        raise TransactionError(
            "baseline type mismatch for {}".format(change["name"])
        )
    if target["value"] != change["before"]:
        raise TransactionError(
            "baseline value mismatch for {}: expected {}, got {}".format(
                change["name"], change["before"], target["value"]
            )
        )
    for name, expected_value in REQUIRED_COMPANION_VALUES.items():
        entry = parameters.get(name)
        if entry is None:
            raise TransactionError("baseline lacks {}".format(name))
        if entry["type"] != snapshot.MAV_PARAM_TYPE_INT32:
            raise TransactionError("baseline type mismatch for {}".format(name))
        if entry["value"] != expected_value:
            raise TransactionError(
                "baseline value mismatch for {}: expected {}, got {}".format(
                    name, expected_value, entry["value"]
                )
            )


def load_baseline(path, expected_sha256, change):
    actual_sha256 = transaction_base.sha256_file(path)
    if actual_sha256 != expected_sha256:
        raise TransactionError(
            "baseline SHA-256 mismatch: expected {}, got {}".format(
                expected_sha256, actual_sha256
            )
        )
    document = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    validate_baseline(document, change)
    return document, actual_sha256


def validate_post_snapshot(baseline, post, change):
    validate_snapshot_shape(post, "post-write")
    differences = transaction_base.parameter_diffs(baseline, post)
    changed_names = {difference["name"] for difference in differences}
    missing = {change["name"]} - changed_names
    unexpected = (
        changed_names - {change["name"]} - ALLOWED_DERIVED_DIFFS
    )
    if missing:
        raise TransactionError(
            "approved parameter missing from diff: {}".format(sorted(missing))
        )
    if unexpected:
        raise TransactionError(
            "unexpected parameters changed: {}".format(sorted(unexpected))
        )

    old_entry = baseline["parameters"][change["name"]]
    new_entry = post["parameters"].get(change["name"])
    if new_entry is None or new_entry["type"] != change["type"]:
        raise TransactionError("post-write SDLOG_MODE type missing/mismatched")
    if new_entry["index"] != old_entry["index"]:
        raise TransactionError("post-write SDLOG_MODE index changed")
    if new_entry["value"] != change["after"]:
        raise TransactionError("post-write SDLOG_MODE value mismatch")

    for name, expected_value in REQUIRED_COMPANION_VALUES.items():
        if post["parameters"][name] != baseline["parameters"][name]:
            raise TransactionError("{} changed unexpectedly".format(name))
        if post["parameters"][name]["value"] != expected_value:
            raise TransactionError("{} value mismatch".format(name))
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

    change = MODE_CHANGES[args.direction]
    baseline, baseline_sha256 = load_baseline(
        args.baseline, args.baseline_sha256, change
    )
    transaction = {
        "approved_change": change,
        "baseline": {
            "path": args.baseline,
            "sha256": baseline_sha256,
        },
        "device": args.device,
        "direction": args.direction,
        "started_at": transaction_base.now_iso8601(),
        "status": "STARTED",
        "writes": [],
    }
    transaction_base.write_json(args.transaction_output, transaction)

    connection = mavutil.mavlink_connection(args.device, autoreconnect=False)
    changed = False
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
        expected_live = dict(REQUIRED_COMPANION_VALUES)
        expected_live[change["name"]] = change["before"]
        for name, expected_value in expected_live.items():
            entry = transaction_base.read_parameter(
                connection, 1, 1, name
            )
            live_before[name] = entry
            if entry["type"] != snapshot.MAV_PARAM_TYPE_INT32:
                raise TransactionError(
                    "live type mismatch for {}".format(name)
                )
            if entry["value"] != expected_value:
                raise TransactionError(
                    "live value mismatch for {}: expected {}, got {}".format(
                        name, expected_value, entry["value"]
                    )
                )
        transaction["live_before"] = live_before
        transaction["status"] = "PRECHECK_PASS"
        transaction_base.write_json(args.transaction_output, transaction)

        ack = transaction_base.set_parameter(connection, 1, 1, change)
        changed = True
        transaction["writes"].append(
            {"change": change, "ack": ack, "verified": True}
        )
        transaction["status"] = "WRITE_ACK_VERIFIED"
        transaction_base.write_json(args.transaction_output, transaction)

        live_after = transaction_base.read_parameter(
            connection, 1, 1, change["name"]
        )
        if (
            live_after["type"] != change["type"]
            or live_after["value"] != change["after"]
        ):
            raise TransactionError("live post-read mismatch for SDLOG_MODE")
        transaction["live_after"] = {change["name"]: live_after}

        post = collect_full_snapshot(
            connection, args, source_system, source_component
        )
        post_sha256 = transaction_base.write_json(args.post_output, post)
        differences = validate_post_snapshot(baseline, post, change)
        transaction["post_snapshot"] = {
            "path": args.post_output,
            "sha256": post_sha256,
            "complete": post["capture"]["complete"],
            "count": len(post["parameters"]),
        }
        transaction["differences"] = differences
        transaction["status"] = "PASS"
        transaction["completed_at"] = transaction_base.now_iso8601()
        transaction_sha256 = transaction_base.write_json(
            args.transaction_output, transaction
        )
        return {
            "status": "PASS",
            "direction": args.direction,
            "post_snapshot_sha256": post_sha256,
            "transaction_sha256": transaction_sha256,
            "difference_names": [
                item["name"] for item in differences
            ],
        }
    except Exception as error:
        original_error = "{}: {}".format(type(error).__name__, error)
        transaction["error"] = original_error
        transaction["status"] = (
            "FAIL_ROLLBACK_PENDING" if changed else "FAIL_PRECHECK"
        )
        transaction_base.write_json(args.transaction_output, transaction)
        rollback_results = []
        rollback_ok = True
        if changed:
            rollback_change = dict(change)
            rollback_change["after"] = change["before"]
            try:
                ack = transaction_base.set_parameter(
                    connection, 1, 1, rollback_change
                )
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
        transaction["status"] = transaction_base.failure_status(
            int(changed), rollback_ok
        )
        transaction["completed_at"] = transaction_base.now_iso8601()
        transaction_base.write_json(args.transaction_output, transaction)
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
    parser.add_argument(
        "--direction", required=True, choices=sorted(MODE_CHANGES)
    )
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--baseline-sha256", required=True)
    parser.add_argument("--post-output", required=True)
    parser.add_argument("--transaction-output", required=True)
    parser.add_argument("--heartbeat-timeout-s", type=float, default=30.0)
    parser.add_argument("--idle-timeout-s", type=float, default=8.0)
    parser.add_argument("--overall-timeout-s", type=float, default=180.0)
    parser.add_argument("--max-recovery-rounds", type=int, default=8)
    parser.add_argument("--recovery-batch-size", type=int, default=64)
    parser.add_argument(
        "--execute-approved-sdlog-transaction", action="store_true"
    )
    args = parser.parse_args(argv)
    if not args.execute_approved_sdlog_transaction:
        parser.error("explicit --execute-approved-sdlog-transaction required")
    if (
        len(args.baseline_sha256) != 64
        or any(char not in string.hexdigits for char in args.baseline_sha256)
    ):
        parser.error("baseline SHA-256 must be exactly 64 hexadecimal digits")
    args.baseline_sha256 = args.baseline_sha256.lower()
    return args


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = execute(args)
    except (
        OSError,
        TransactionError,
        transaction_base.TransactionError,
        snapshot.SnapshotError,
        UnicodeError,
        ValueError,
    ) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
