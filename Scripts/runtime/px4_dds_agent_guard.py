#!/usr/bin/env python3
"""Fail-closed launcher for the production PX4 serial DDS Agent."""

import argparse
import fcntl
import hashlib
import json
import os
import pathlib
import re
import stat
import sys
import tempfile


DEFAULT_MIN_MEM_AVAILABLE_MIB = 1024
DEFAULT_MIN_DMA_HEADROOM_MIB = 256
DEFAULT_LOCK_FILE = "/tmp/boomboomfly_px4_dds_agent.lock"
DEVELOPMENT_PROCESS_PATTERNS = (
    re.compile(r"pylance", re.IGNORECASE),
    re.compile(r"cpptools", re.IGNORECASE),
    re.compile(r"--type=extensionHost", re.IGNORECASE),
)


class GuardError(RuntimeError):
    pass


def read_mem_available_kib(path):
    for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"MemAvailable:\s+(\d+)\s+kB", line)
        if match:
            return int(match.group(1))
    raise GuardError("MemAvailable is missing from {}".format(path))


def read_zone_watermarks(path, zone_name="DMA"):
    lines = pathlib.Path(path).read_text(encoding="utf-8").splitlines()
    inside = False
    values = {}
    for line in lines:
        zone = re.fullmatch(r"Node\s+\d+, zone\s+(\S+)", line.strip())
        if zone:
            if inside:
                break
            inside = zone.group(1) == zone_name
            continue
        if not inside:
            continue
        match = re.fullmatch(r"\s*(pages free|min|low|high)\s+(\d+)\s*", line)
        if match and match.group(1) not in values:
            values[match.group(1)] = int(match.group(2))
        if set(values) == {"pages free", "min", "low", "high"}:
            break
    missing = {"pages free", "min", "low", "high"} - set(values)
    if missing:
        raise GuardError("zone {} lacks {} in {}".format(
            zone_name, sorted(missing), path))
    return values


def dma_headroom_kib(zone_values, page_size_bytes=None):
    if page_size_bytes is None:
        page_size_bytes = os.sysconf("SC_PAGE_SIZE")
    free_above_high = zone_values["pages free"] - zone_values["high"]
    return max(0, free_above_high * page_size_bytes // 1024)


def read_cmdline(path):
    try:
        return pathlib.Path(path).read_bytes().replace(b"\0", b" ").decode(
            "utf-8", errors="replace")
    except (OSError, ValueError):
        return ""


def development_processes(proc_root="/proc", own_pid=None):
    own_pid = os.getpid() if own_pid is None else own_pid
    matches = []
    for process_dir in pathlib.Path(proc_root).iterdir():
        if not process_dir.name.isdigit() or int(process_dir.name) == own_pid:
            continue
        cmdline = read_cmdline(process_dir / "cmdline")
        if not cmdline:
            continue
        if any(pattern.search(cmdline) for pattern in DEVELOPMENT_PROCESS_PATTERNS):
            matches.append((int(process_dir.name), cmdline.strip()))
    return sorted(matches)


def serial_owners(device, proc_root="/proc", own_pid=None):
    own_pid = os.getpid() if own_pid is None else own_pid
    device_stat = os.stat(device)
    if not stat.S_ISCHR(device_stat.st_mode):
        raise GuardError("serial device is not a character device: {}".format(device))
    owners = []
    for process_dir in pathlib.Path(proc_root).iterdir():
        if not process_dir.name.isdigit() or int(process_dir.name) == own_pid:
            continue
        fd_dir = process_dir / "fd"
        try:
            descriptors = list(fd_dir.iterdir())
        except OSError:
            continue
        for descriptor in descriptors:
            try:
                descriptor_stat = descriptor.stat()
            except OSError:
                continue
            if (stat.S_ISCHR(descriptor_stat.st_mode)
                    and descriptor_stat.st_rdev == device_stat.st_rdev):
                owners.append((int(process_dir.name), read_cmdline(process_dir / "cmdline")))
                break
    return sorted(owners)


def sha256_file(path):
    digest = hashlib.sha256()
    with pathlib.Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_agent(agent, expected_sha256):
    path = pathlib.Path(agent)
    if not path.is_absolute():
        raise GuardError("--agent must be an absolute path")
    if not path.is_file() or not os.access(str(path), os.X_OK):
        raise GuardError("Agent is missing or not executable: {}".format(path))
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise GuardError("--agent-sha256 must be 64 lowercase hexadecimal characters")
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise GuardError("Agent SHA-256 mismatch: expected {}, got {}".format(
            expected_sha256, actual))
    return actual


def preflight(args):
    if os.environ.get("ROS_DOMAIN_ID") != "0":
        raise GuardError("production Agent requires explicit ROS_DOMAIN_ID=0")
    actual_sha256 = validate_agent(args.agent, args.agent_sha256)
    mem_available_kib = read_mem_available_kib(args.meminfo)
    zone_values = read_zone_watermarks(args.zoneinfo)
    dma_available_kib = dma_headroom_kib(zone_values)
    required_mem_kib = args.min_mem_available_mib * 1024
    required_dma_kib = args.min_dma_headroom_mib * 1024
    if mem_available_kib < required_mem_kib:
        raise GuardError("MemAvailable {} KiB is below required {} KiB".format(
            mem_available_kib, required_mem_kib))
    if dma_available_kib < required_dma_kib:
        raise GuardError("DMA free-above-high {} KiB is below required {} KiB".format(
            dma_available_kib, required_dma_kib))
    development = development_processes(args.proc_root)
    if development:
        raise GuardError("development processes are forbidden in flight window: {}".format(
            [pid for pid, _ in development]))
    owners = serial_owners(args.serial_dev, args.proc_root)
    if owners:
        raise GuardError("serial device {} already has owners {}".format(
            args.serial_dev, [pid for pid, _ in owners]))
    return {
        "agent_sha256": actual_sha256,
        "baudrate": args.baudrate,
        "dma_free_above_high_kib": dma_available_kib,
        "mem_available_kib": mem_available_kib,
        "serial_dev": args.serial_dev,
    }


def acquire_lock(path):
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        os.close(descriptor)
        raise GuardError("another guarded Agent owns {}".format(path)) from exc
    os.set_inheritable(descriptor, True)
    return descriptor


def self_test():
    with tempfile.TemporaryDirectory(prefix="px4_dds_guard.") as directory:
        root = pathlib.Path(directory)
        meminfo = root / "meminfo"
        zoneinfo = root / "zoneinfo"
        meminfo.write_text("MemAvailable: 2097152 kB\n", encoding="utf-8")
        zoneinfo.write_text(
            "Node 0, zone DMA\n"
            "  pages free 100000\n"
            "        min 6000\n"
            "        low 7500\n"
            "        high 9000\n"
            "Node 0, zone Normal\n",
            encoding="utf-8",
        )
        assert read_mem_available_kib(meminfo) == 2097152
        values = read_zone_watermarks(zoneinfo)
        assert values["pages free"] == 100000
        assert dma_headroom_kib(values, 4096) == 364000
        process = root / "123"
        process.mkdir()
        (process / "cmdline").write_bytes(b"pylance\0--stdio\0")
        assert development_processes(root, own_pid=999) == [(123, "pylance --stdio")]
    print(json.dumps({"status": "PASS", "self_test": "px4_dds_agent_guard"}, sort_keys=True))


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", help="absolute MicroXRCEAgent executable path")
    parser.add_argument("--agent-sha256", help="required exact Agent binary SHA-256")
    parser.add_argument("--serial-dev", default="/dev/ttyTHS0")
    parser.add_argument("--baudrate", type=int, default=921600)
    parser.add_argument("--min-mem-available-mib", type=int,
                        default=DEFAULT_MIN_MEM_AVAILABLE_MIB)
    parser.add_argument("--min-dma-headroom-mib", type=int,
                        default=DEFAULT_MIN_DMA_HEADROOM_MIB)
    parser.add_argument("--lock-file", default=DEFAULT_LOCK_FILE)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--meminfo", default="/proc/meminfo", help=argparse.SUPPRESS)
    parser.add_argument("--zoneinfo", default="/proc/zoneinfo", help=argparse.SUPPRESS)
    parser.add_argument("--proc-root", default="/proc", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.self_test:
        return args
    if not args.agent or not args.agent_sha256:
        parser.error("--agent and --agent-sha256 are required")
    if args.baudrate <= 0 or args.min_mem_available_mib <= 0 or args.min_dma_headroom_mib <= 0:
        parser.error("baudrate and memory thresholds must be positive")
    return args


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.self_test:
        self_test()
        return 0
    lock_descriptor = acquire_lock(args.lock_file)
    try:
        result = preflight(args)
        result.update({"status": "PASS", "check_only": bool(args.check_only)})
        print(json.dumps(result, sort_keys=True), flush=True)
        if args.check_only:
            return 0
        command = [
            args.agent,
            "serial",
            "--dev",
            args.serial_dev,
            "-b",
            str(args.baudrate),
        ]
        os.execv(args.agent, command)
    finally:
        os.close(lock_descriptor)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (GuardError, OSError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True),
              file=sys.stderr)
        sys.exit(2)
