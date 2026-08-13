#!/usr/bin/env python3
"""Check BoomBoomFly package ownership and dependency boundaries."""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOOMBOOM = ROOT / "px4" / "px4_ws" / "src" / "boomboom"
TI = BOOMBOOM / "ti"
BRINGUP_LAUNCH = BOOMBOOM / "px4_bringup" / "launch"

TI_PACKAGE_DIRS = {
    "boomboom_mission_core": "boomboom_mission_core",
    "boomboom_navigation": "boomboom_navigation",
    "boomboom_task_h": "TI_2025",
    "boomboom_task_d": "TI_2026",
}
COMMON_INTERFACES = (
    "msg/LocalPose.msg",
    "msg/FlightState.msg",
    "msg/TargetObservation.msg",
    "msg/DeviceCommand.msg",
    "msg/DeviceAck.msg",
    "action/ExecuteFlight.action",
)
CONTROL_TOPICS = (
    "/fmu/in/offboard_control_mode",
    "/fmu/in/trajectory_setpoint",
    "/fmu/in/vehicle_command",
)
CODE_SUFFIXES = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".py"}


def dependencies(package_xml: Path) -> set[str]:
    root = ET.parse(package_xml).getroot()
    return {
        (element.text or "").strip()
        for element in root
        if element.tag == "depend" or element.tag.endswith("_depend")
    }


def production_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in CODE_SUFFIXES:
            continue
        relative = path.relative_to(root)
        if any(part in {".git", "test", "tests", "docs", "templates"} for part in relative.parts):
            continue
        yield path


def main() -> int:
    errors: list[str] = []

    for launch_file in BOOMBOOM.rglob("*.launch.py"):
        if launch_file.parent != BRINGUP_LAUNCH:
            errors.append(
                "self-developed launch file must be owned by px4_bringup: "
                f"{launch_file.relative_to(ROOT)}"
            )

    for relative in COMMON_INTERFACES:
        path = BOOMBOOM / "common" / relative
        if not path.is_file():
            errors.append(f"missing common interface: {path.relative_to(ROOT)}")

    ti_dependencies: dict[str, set[str]] = {}
    for package, directory in TI_PACKAGE_DIRS.items():
        package_root = TI / directory
        manifest = package_root / "package.xml"
        if not manifest.is_file():
            errors.append(f"missing TI package manifest: {manifest.relative_to(ROOT)}")
            continue
        package_deps = dependencies(manifest)
        ti_dependencies[package] = package_deps
        if "px4_msgs" in package_deps:
            errors.append(f"{package} must not depend on px4_msgs")
        for interface_dir in ("msg", "srv", "action"):
            if (package_root / interface_dir).exists():
                errors.append(
                    f"{package} defines local {interface_dir}; public interfaces belong in common"
                )
        for source in production_files(package_root):
            text = source.read_text(encoding="utf-8", errors="replace")
            if "px4_msgs" in text:
                errors.append(f"{source.relative_to(ROOT)} directly references px4_msgs")
            if "/fmu/in/" in text:
                errors.append(f"{source.relative_to(ROOT)} directly references /fmu/in/*")
            if package in {"boomboom_task_h", "boomboom_task_d"} and (
                "boomboom_common/action/execute_flight" in text or "rclcpp_action" in text
            ):
                errors.append(
                    f"{source.relative_to(ROOT)} bypasses boomboom_navigation flight adapter"
                )

    for task_package in ("boomboom_task_h", "boomboom_task_d"):
        if "boomboom_navigation" not in ti_dependencies.get(task_package, set()):
            errors.append(f"{task_package} must depend on boomboom_navigation")

    if "boomboom_task_d" in ti_dependencies.get("boomboom_task_h", set()):
        errors.append("boomboom_task_h must not depend on boomboom_task_d")
    if "boomboom_task_h" in ti_dependencies.get("boomboom_task_d", set()):
        errors.append("boomboom_task_d must not depend on boomboom_task_h")

    offboard_manifest = BOOMBOOM / "offboard_cpp" / "package.xml"
    if offboard_manifest.is_file():
        forbidden = set(TI_PACKAGE_DIRS)
        coupled = dependencies(offboard_manifest) & forbidden
        if coupled:
            errors.append(f"offboard_cpp depends on TI packages: {sorted(coupled)}")

    for repository in BOOMBOOM.iterdir() if BOOMBOOM.is_dir() else ():
        if not repository.is_dir() or repository.name == "offboard_cpp":
            continue
        for source in production_files(repository):
            text = source.read_text(encoding="utf-8", errors="replace")
            for topic in CONTROL_TOPICS:
                if topic in text:
                    errors.append(
                        f"control topic {topic} appears outside offboard_cpp: "
                        f"{source.relative_to(ROOT)}"
                    )

    if errors:
        print("architecture verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        "verified common interface ownership, TI dependency isolation, "
        "and single offboard control-topic ownership"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
