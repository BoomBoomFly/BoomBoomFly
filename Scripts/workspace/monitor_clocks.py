#!/usr/bin/env python3
"""Record realtime, monotonic, and boottime without changing system time."""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path


NS_PER_MS = 1_000_000
NS_PER_SEC = 1_000_000_000


def sample() -> tuple[int, int, int]:
    """Take a closely grouped three-clock sample in nanoseconds."""
    return (
        time.clock_gettime_ns(time.CLOCK_REALTIME),
        time.clock_gettime_ns(time.CLOCK_MONOTONIC),
        time.clock_gettime_ns(time.CLOCK_BOOTTIME),
    )


def ms(value_ns: int) -> float:
    return value_ns / NS_PER_MS


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "record Linux realtime/monotonic/boottime and report realtime steps "
            "and suspend/resume gaps; it does not modify time or services"
        )
    )
    parser.add_argument("--duration-sec", type=float, default=180.0)
    parser.add_argument("--interval-ms", type=float, default=100.0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--realtime-step-ms",
        type=float,
        default=100.0,
        help="absolute delta(realtime-monotonic) treated as a realtime step (default: 100)",
    )
    parser.add_argument(
        "--suspend-gap-ms",
        type=float,
        default=1000.0,
        help="positive delta(boottime-monotonic) treated as suspend/resume (default: 1000)",
    )
    parser.add_argument(
        "--require-suspend",
        action="store_true",
        help="exit nonzero unless a suspend/resume gap is observed",
    )
    args = parser.parse_args()

    if args.duration_sec <= 0 or args.interval_ms <= 0:
        parser.error("--duration-sec and --interval-ms must be positive")
    if args.realtime_step_ms < 0 or args.suspend_gap_ms < 0:
        parser.error("thresholds must be non-negative")
    if not hasattr(time, "CLOCK_BOOTTIME"):
        print("CLOCK_BOOTTIME is unavailable on this Python/platform", file=sys.stderr)
        return 4

    args.output.parent.mkdir(parents=True, exist_ok=True)
    interval_ns = round(args.interval_ms * NS_PER_MS)
    realtime_step_ns = round(args.realtime_step_ms * NS_PER_MS)
    suspend_gap_ns = round(args.suspend_gap_ms * NS_PER_MS)
    started_rt, started_mono, started_boot = sample()
    deadline_mono = started_mono + round(args.duration_sec * NS_PER_SEC)
    previous = (started_rt, started_mono, started_boot)
    samples = 0
    realtime_steps = 0
    suspend_events = 0
    max_abs_rt_minus_mono_delta = 0
    max_boot_minus_mono_delta = 0

    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            (
                "sample",
                "realtime_ns",
                "monotonic_ns",
                "boottime_ns",
                "realtime_minus_monotonic_ns",
                "boottime_minus_monotonic_ns",
                "delta_realtime_minus_monotonic_ns",
                "delta_boottime_minus_monotonic_ns",
            )
        )
        while True:
            current = sample()
            rt, mono, boot = current
            prev_rt, prev_mono, prev_boot = previous
            rt_minus_mono_delta = (rt - mono) - (prev_rt - prev_mono)
            boot_minus_mono_delta = (boot - mono) - (prev_boot - prev_mono)
            max_abs_rt_minus_mono_delta = max(
                max_abs_rt_minus_mono_delta, abs(rt_minus_mono_delta)
            )
            max_boot_minus_mono_delta = max(
                max_boot_minus_mono_delta, boot_minus_mono_delta
            )
            if abs(rt_minus_mono_delta) >= realtime_step_ns:
                realtime_steps += 1
                print(
                    f"realtime-step sample={samples} delta_ms={ms(rt_minus_mono_delta):+.3f}",
                    file=sys.stderr,
                )
            if boot_minus_mono_delta >= suspend_gap_ns:
                suspend_events += 1
                print(
                    f"suspend-resume sample={samples} gap_ms={ms(boot_minus_mono_delta):+.3f}",
                    file=sys.stderr,
                )
            writer.writerow(
                (
                    samples,
                    rt,
                    mono,
                    boot,
                    rt - mono,
                    boot - mono,
                    rt_minus_mono_delta,
                    boot_minus_mono_delta,
                )
            )
            samples += 1
            previous = current
            if mono >= deadline_mono:
                break
            next_mono = started_mono + samples * interval_ns
            delay_ns = next_mono - time.clock_gettime_ns(time.CLOCK_MONOTONIC)
            if delay_ns > 0:
                time.sleep(delay_ns / NS_PER_SEC)

    elapsed_mono_ms = ms(previous[1] - started_mono)
    elapsed_boot_ms = ms(previous[2] - started_boot)
    print(f"csv={args.output}")
    print(f"samples={samples} elapsed_monotonic_ms={elapsed_mono_ms:.3f}")
    print(f"elapsed_boottime_ms={elapsed_boot_ms:.3f}")
    print(f"realtime_steps={realtime_steps} threshold_ms={args.realtime_step_ms:.3f}")
    print(
        "max_abs_delta_realtime_minus_monotonic_ms="
        f"{ms(max_abs_rt_minus_mono_delta):.3f}"
    )
    print(f"suspend_events={suspend_events} threshold_ms={args.suspend_gap_ms:.3f}")
    print(
        "max_delta_boottime_minus_monotonic_ms="
        f"{ms(max_boot_minus_mono_delta):.3f}"
    )

    if realtime_steps:
        return 2
    if args.require_suspend and not suspend_events:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
