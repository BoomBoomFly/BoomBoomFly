#!/usr/bin/env python3
"""Fail-closed, read-only MAVLink snapshot of PX4 legacy parameters."""

import argparse
import hashlib
import json
import math
import pathlib
import struct
import time


MAV_PARAM_TYPE_UINT8 = 1
MAV_PARAM_TYPE_INT8 = 2
MAV_PARAM_TYPE_UINT16 = 3
MAV_PARAM_TYPE_INT16 = 4
MAV_PARAM_TYPE_UINT32 = 5
MAV_PARAM_TYPE_INT32 = 6
MAV_PARAM_TYPE_UINT64 = 7
MAV_PARAM_TYPE_INT64 = 8
MAV_PARAM_TYPE_REAL32 = 9
MAV_PARAM_TYPE_REAL64 = 10

INTEGER_FORMATS = {
    MAV_PARAM_TYPE_UINT8: "<B",
    MAV_PARAM_TYPE_INT8: "<b",
    MAV_PARAM_TYPE_UINT16: "<H",
    MAV_PARAM_TYPE_INT16: "<h",
    MAV_PARAM_TYPE_UINT32: "<I",
    MAV_PARAM_TYPE_INT32: "<i",
}

SELECTED = (
    "BAT1_I_CHANNEL",
    "BAT1_N_CELLS",
    "BAT1_SOURCE",
    "BAT1_V_CHANNEL",
    "BAT_CRIT_THR",
    "BAT_EMERGEN_THR",
    "BAT_LOW_THR",
    "COM_ARM_SDCARD",
    "COM_DL_LOSS_T",
    "COM_DLL_EXCEPT",
    "COM_FAIL_ACT_T",
    "COM_FLT_TIME_MAX",
    "COM_KILL_DISARM",
    "COM_LOW_BAT_ACT",
    "COM_OBC_LOSS_T",
    "COM_OBL_RC_ACT",
    "COM_OF_LOSS_T",
    "COM_RCL_EXCEPT",
    "COM_RC_IN_MODE",
    "COM_RC_LOSS_T",
    "EKF2_EV_CTRL",
    "EKF2_EV_DELAY",
    "EKF2_EV_NOISE_MD",
    "EKF2_EVP_NOISE",
    "EKF2_EVV_NOISE",
    "EKF2_HGT_REF",
    "EKF2_RNG_CTRL",
    "GF_ACTION",
    "GF_MAX_HOR_DIST",
    "GF_MAX_VER_DIST",
    "GF_PREDICT",
    "GF_SOURCE",
    "NAV_DLL_ACT",
    "NAV_RCL_ACT",
    "SDLOG_BOOT_BAT",
    "SDLOG_MISSION",
    "SDLOG_MODE",
    "SDLOG_PROFILE",
    "SYS_USB_AUTO",
    "USB_MAV_MODE",
    "UXRCE_DDS_CFG",
    "UXRCE_DDS_DOM_ID",
    "UXRCE_DDS_SYNCT",
)


class SnapshotError(RuntimeError):
    """A fail-closed snapshot validation error."""


def param_name(message):
    value = message.param_id
    if isinstance(value, bytes):
        value = value.decode("ascii", errors="strict")
    return value.rstrip("\0")


def decode_param_value(raw_value, param_type):
    """Decode PX4's MAVLink bytewise PARAM_VALUE representation.

    PX4 stores integer bits in the four-byte ``param_value`` field. For
    example, INT32 -1 has the float bit pattern 0xffffffff and therefore
    appears as NaN if it is incorrectly converted as a numeric float.
    """
    param_type = int(param_type)
    raw_value = float(raw_value)
    if param_type in INTEGER_FORMATS:
        raw_bytes = struct.pack("<f", raw_value)
        return struct.unpack_from(INTEGER_FORMATS[param_type], raw_bytes)[0]
    if param_type == MAV_PARAM_TYPE_REAL32:
        if not math.isfinite(raw_value):
            raise SnapshotError("non-finite REAL32 parameter")
        return raw_value
    if param_type in (MAV_PARAM_TYPE_UINT64, MAV_PARAM_TYPE_INT64,
                      MAV_PARAM_TYPE_REAL64):
        raise SnapshotError(
            "64-bit parameter type {} is not representable in legacy "
            "PARAM_VALUE".format(param_type)
        )
    raise SnapshotError("unsupported MAV_PARAM_TYPE {}".format(param_type))


def encode_param_value(value, param_type):
    """Encode a value using PX4's bytewise legacy PARAM_SET representation."""
    param_type = int(param_type)
    if param_type in INTEGER_FORMATS:
        try:
            raw_bytes = struct.pack(INTEGER_FORMATS[param_type], int(value))
        except (OverflowError, struct.error, ValueError) as error:
            raise SnapshotError(
                "value {} is invalid for MAV_PARAM_TYPE {}".format(
                    value, param_type
                )
            ) from error
        return struct.unpack("<f", raw_bytes.ljust(4, b"\0"))[0]
    if param_type == MAV_PARAM_TYPE_REAL32:
        value = float(value)
        if not math.isfinite(value):
            raise SnapshotError("non-finite REAL32 parameter")
        return value
    if param_type in (MAV_PARAM_TYPE_UINT64, MAV_PARAM_TYPE_INT64,
                      MAV_PARAM_TYPE_REAL64):
        raise SnapshotError(
            "64-bit parameter type {} is not representable in legacy "
            "PARAM_SET".format(param_type)
        )
    raise SnapshotError("unsupported MAV_PARAM_TYPE {}".format(param_type))


def collect_parameters(connection, device, source_system, source_component,
                       target_system, target_component, idle_timeout_s,
                       overall_timeout_s, max_recovery_rounds,
                       recovery_batch_size):
    connection.mav.param_request_list_send(target_system, target_component)

    parameters = {}
    seen_indexes = set()
    expected_count = None
    started = time.monotonic()
    last_new = started
    recovery_rounds = 0

    while time.monotonic() - started < overall_timeout_s:
        message = connection.recv_match(
            type="PARAM_VALUE", blocking=True, timeout=1.0
        )
        now = time.monotonic()
        if message is None:
            if now - last_new < idle_timeout_s:
                continue
            if expected_count is None or recovery_rounds >= max_recovery_rounds:
                break
            missing = [
                index for index in range(expected_count)
                if index not in seen_indexes
            ]
            if not missing:
                break
            for index in missing[:recovery_batch_size]:
                connection.mav.param_request_read_send(
                    target_system, target_component, b"", index
                )
            recovery_rounds += 1
            last_new = now
            continue

        name = param_name(message)
        param_type = int(message.param_type)
        value = decode_param_value(message.param_value, param_type)
        index = int(message.param_index)
        message_count = int(message.param_count)
        if expected_count is None:
            expected_count = message_count
        elif expected_count != message_count:
            raise SnapshotError(
                "parameter count changed from {} to {}".format(
                    expected_count, message_count
                )
            )
        if name not in parameters:
            last_new = now
        parameters[name] = {
            "index": index,
            "type": param_type,
            "value": value,
        }
        seen_indexes.add(index)
        if expected_count is not None and len(seen_indexes) >= expected_count:
            break

    complete = (
        expected_count is not None
        and len(parameters) == expected_count
        and len(seen_indexes) == expected_count
    )
    return {
        "capture": {
            "complete": complete,
            "device": device,
            "elapsed_s": round(time.monotonic() - started, 6),
            "encoding": "px4_mavlink_bytewise",
            "expected_count": expected_count,
            "received_count": len(parameters),
            "received_index_count": len(seen_indexes),
            "recovery_rounds": recovery_rounds,
            "source_component": source_component,
            "source_system": source_system,
            "target_component": target_component,
            "target_system": target_system,
        },
        "parameters": dict(sorted(parameters.items())),
        "selected": {name: parameters.get(name) for name in SELECTED},
    }


def capture(args):
    from pymavlink import mavutil

    connection = mavutil.mavlink_connection(args.device, autoreconnect=False)
    heartbeat = connection.wait_heartbeat(timeout=args.heartbeat_timeout_s)
    if heartbeat is None:
        raise SnapshotError("no MAVLink heartbeat")

    source_system = int(heartbeat.get_srcSystem())
    source_component = int(heartbeat.get_srcComponent())
    target_system = args.target_system or source_system
    target_component = args.target_component or source_component or 1
    return collect_parameters(
        connection,
        args.device,
        source_system,
        source_component,
        target_system,
        target_component,
        args.idle_timeout_s,
        args.overall_timeout_s,
        args.max_recovery_rounds,
        args.recovery_batch_size,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="/dev/ttyACM0")
    parser.add_argument("--output", required=True)
    parser.add_argument("--heartbeat-timeout-s", type=float, default=15.0)
    parser.add_argument("--idle-timeout-s", type=float, default=5.0)
    parser.add_argument("--overall-timeout-s", type=float, default=120.0)
    parser.add_argument("--target-system", type=int, default=1)
    parser.add_argument("--target-component", type=int, default=1)
    parser.add_argument("--max-recovery-rounds", type=int, default=5)
    parser.add_argument("--recovery-batch-size", type=int, default=64)
    args = parser.parse_args()

    try:
        document = capture(args)
    except (OSError, SnapshotError, UnicodeError, ValueError) as error:
        raise SystemExit("FAIL: {}".format(error))

    encoded = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    output = pathlib.Path(args.output)
    output.write_bytes(encoded)
    digest = hashlib.sha256(encoded).hexdigest()
    summary = {
        "complete": document["capture"]["complete"],
        "expected_count": document["capture"]["expected_count"],
        "output": str(output),
        "received_count": document["capture"]["received_count"],
        "received_index_count": document["capture"]["received_index_count"],
        "selected": document["selected"],
        "sha256": digest,
        "status": "PASS" if document["capture"]["complete"] else "FAIL",
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    raise SystemExit(0 if document["capture"]["complete"] else 1)


if __name__ == "__main__":
    main()
