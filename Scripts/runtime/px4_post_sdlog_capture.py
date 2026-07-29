#!/usr/bin/env python3
"""Capture final PX4 parameters and download recent ULogs in one USB session."""

import argparse
import hashlib
import json
import pathlib
import sys


SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import px4_param_snapshot as snapshot  # noqa: E402


EXPECTED_PARAMETER_COUNT = 974
ULOG_MAGIC = b"ULog\x01\x12\x35"


class CaptureError(RuntimeError):
    """A fail-closed final capture error."""


def encoded_json(document):
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def write_bytes(path, content):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return hashlib.sha256(content).hexdigest()


def validate_final_snapshot(document):
    capture = document.get("capture", {})
    parameters = document.get("parameters", {})
    if not capture.get("complete"):
        raise CaptureError("final parameter snapshot is incomplete")
    if capture.get("expected_count") != EXPECTED_PARAMETER_COUNT:
        raise CaptureError("final expected_count is not 974")
    if len(parameters) != EXPECTED_PARAMETER_COUNT:
        raise CaptureError("final parameter count is not 974")
    indexes = {entry["index"] for entry in parameters.values()}
    if len(indexes) != EXPECTED_PARAMETER_COUNT:
        raise CaptureError("final parameter indexes are not unique")
    expected = {
        "SDLOG_MODE": 0,
        "SDLOG_BOOT_BAT": 0,
        "SDLOG_PROFILE": 1,
    }
    for name, value in expected.items():
        entry = parameters.get(name)
        if entry is None:
            raise CaptureError("final snapshot lacks {}".format(name))
        if entry["type"] != snapshot.MAV_PARAM_TYPE_INT32:
            raise CaptureError("final type mismatch for {}".format(name))
        if entry["value"] != value:
            raise CaptureError(
                "final value mismatch for {}: expected {}, got {}".format(
                    name, value, entry["value"]
                )
            )


def list_tree(ftp, root, max_depth=3):
    from pymavlink.mavftp import FtpError

    files = []
    pending = [(root.rstrip("/"), 0)]
    visited = set()
    while pending:
        directory, depth = pending.pop(0)
        if directory in visited:
            continue
        visited.add(directory)
        result = ftp.cmd_list([directory])
        if result.error_code != FtpError.Success:
            raise CaptureError(
                "MAVFTP list failed for {}: {}".format(
                    directory, int(result.error_code)
                )
            )
        for entry in ftp.list_result:
            if entry.name in (".", ".."):
                continue
            path = directory + "/" + entry.name
            if entry.is_dir:
                if depth >= max_depth:
                    raise CaptureError(
                        "MAVFTP log tree exceeds max depth at {}".format(path)
                    )
                pending.append((path, depth + 1))
            else:
                files.append({
                    "path": path,
                    "size_bytes": int(entry.size_b),
                })
    return sorted(files, key=lambda item: item["path"])


def select_recent_ulogs(files, count):
    candidates = [
        item for item in files
        if item["path"].lower().endswith(".ulg") and item["size_bytes"] > 0
    ]
    if len(candidates) < count:
        raise CaptureError(
            "requested {} recent ULogs but found {}".format(
                count, len(candidates)
            )
        )
    return candidates[-count:]


def download_ulogs(connection, mavftp_module, selected, output_dir):
    output_dir = pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded = []
    for index, entry in enumerate(selected):
        # PX4 can retain a stale FTP file session after an interrupted client.
        # A fresh MAVFTP instance sends OP_ResetSessions before every file.
        ftp = mavftp_module.MAVFTP(
            connection,
            target_system=1,
            target_component=1,
        )
        content = ftp.read(entry["path"], entry["size_bytes"])
        if content is None:
            raise CaptureError(
                "MAVFTP returned no data for {}".format(entry["path"])
            )
        if len(content) != entry["size_bytes"]:
            raise CaptureError(
                "MAVFTP size mismatch for {}: expected {}, got {}".format(
                    entry["path"], entry["size_bytes"], len(content)
                )
            )
        if not content.startswith(ULOG_MAGIC):
            raise CaptureError(
                "downloaded file lacks ULog magic: {}".format(entry["path"])
            )
        local_name = "{:02d}_{}".format(
            index, pathlib.PurePosixPath(entry["path"]).name
        )
        local_path = output_dir / local_name
        digest = write_bytes(local_path, content)
        downloaded.append({
            "remote_path": entry["path"],
            "local_path": str(local_path),
            "size_bytes": len(content),
            "sha256": digest,
        })
    return downloaded


def execute(args):
    from pymavlink import mavftp, mavutil

    connection = mavutil.mavlink_connection(
        args.device, autoreconnect=False, source_system=250
    )
    try:
        heartbeat = connection.wait_heartbeat(timeout=args.heartbeat_timeout_s)
        if heartbeat is None:
            raise CaptureError("no MAVLink heartbeat")
        source_system = int(heartbeat.get_srcSystem())
        source_component = int(heartbeat.get_srcComponent())
        if source_system != 1 or source_component != 1:
            raise CaptureError(
                "unexpected heartbeat source {}/{}".format(
                    source_system, source_component
                )
            )
        if int(heartbeat.autopilot) != mavutil.mavlink.MAV_AUTOPILOT_PX4:
            raise CaptureError("heartbeat is not from PX4")
        if (
            int(heartbeat.base_mode)
            & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
        ):
            raise CaptureError("vehicle is ARMED; refusing final capture")

        document = snapshot.collect_parameters(
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
        validate_final_snapshot(document)
        snapshot_sha256 = write_bytes(
            args.snapshot_output, encoded_json(document)
        )

        ftp = mavftp.MAVFTP(
            connection,
            target_system=1,
            target_component=1,
        )
        files = list_tree(ftp, args.log_root, args.max_log_tree_depth)
        selected = select_recent_ulogs(files, args.download_recent)
        inventory = {
            "device": args.device,
            "files": files,
            "log_root": args.log_root,
            "selected": selected,
            "downloaded": [],
            "status": "INVENTORY_PASS_DOWNLOAD_PENDING",
        }
        inventory_sha256 = write_bytes(
            args.inventory_output, encoded_json(inventory)
        )
        downloaded = download_ulogs(
            connection, mavftp, selected, args.download_dir
        )
        inventory["downloaded"] = downloaded
        inventory["status"] = "PASS"
        inventory_sha256 = write_bytes(
            args.inventory_output, encoded_json(inventory)
        )
        return {
            "status": "PASS",
            "parameter_count": len(document["parameters"]),
            "snapshot_sha256": snapshot_sha256,
            "inventory_sha256": inventory_sha256,
            "downloaded": downloaded,
        }
    finally:
        connection.close()


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/ttyACM0")
    parser.add_argument("--snapshot-output", required=True)
    parser.add_argument("--inventory-output", required=True)
    parser.add_argument("--download-dir", required=True)
    parser.add_argument("--download-recent", type=int, default=2)
    parser.add_argument("--log-root", default="/fs/microsd/log")
    parser.add_argument("--max-log-tree-depth", type=int, default=3)
    parser.add_argument("--heartbeat-timeout-s", type=float, default=30.0)
    parser.add_argument("--idle-timeout-s", type=float, default=8.0)
    parser.add_argument("--overall-timeout-s", type=float, default=180.0)
    parser.add_argument("--max-recovery-rounds", type=int, default=8)
    parser.add_argument("--recovery-batch-size", type=int, default=64)
    args = parser.parse_args(argv)
    if args.download_recent <= 0:
        parser.error("--download-recent must be positive")
    if args.max_log_tree_depth <= 0:
        parser.error("--max-log-tree-depth must be positive")
    return args


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = execute(args)
    except (OSError, CaptureError, snapshot.SnapshotError, ValueError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
