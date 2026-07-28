#!/usr/bin/env python3
"""Offline tests for the launch safety guard."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "Scripts/test/launch_guard/check_launch_safety.py"
SPEC = importlib.util.spec_from_file_location("check_launch_safety", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load launch guard")
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)
FIXTURES = Path(__file__).resolve().parent / "fixtures"


class LaunchGuardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = GUARD.load_profile(
            ROOT / "config/profiles/dds_only_launch.yaml"
        )

    def scan(self, name):
        return GUARD.analyze(FIXTURES / name, ROOT, self.profile)

    def test_safe_single_writer_passes_static_analysis(self):
        report = self.scan("safe_one_writer.launch.py")
        self.assertEqual([], report["findings"])
        self.assertEqual([], report["reviews"])
        self.assertEqual([
            {
                "package": "offboard_cpp",
                "executable": "offboard_node",
                "name": "offboard_control_node",
            }
        ], report["nodes"])
        self.assertEqual(1, report["writers"]["/fmu/in/vehicle_command"])

    def test_dangerous_node_and_yaml_are_denied(self):
        report = self.scan("dangerous_node.launch.py")
        joined = "\n".join(report["findings"])
        self.assertIn("serial_driver", joined)
        self.assertIn("/dev/ttyACM0", joined)

    def test_execute_process_agent_and_device_are_denied(self):
        report = self.scan("dangerous_process.launch.py")
        joined = "\n".join(report["findings"])
        self.assertIn("ExecuteProcess is not allowed", joined)
        self.assertIn("MicroXRCEAgent", joined)
        self.assertIn("/dev/ttyTHS0", joined)

    def test_dangerous_include_is_denied(self):
        report = self.scan("dangerous_include.launch.py")
        self.assertTrue(any("px4_bringup" in item for item in report["findings"]))

    def test_duplicate_fmu_writer_is_denied(self):
        report = self.scan("duplicate_writer.launch.py")
        self.assertTrue(any(
            "multiple writers for /fmu/in/vehicle_command" in item
            for item in report["findings"]
        ))

    def test_dynamic_launch_requires_review(self):
        report = self.scan("dynamic_requires_review.launch.py")
        self.assertEqual([], report["findings"])
        self.assertTrue(report["reviews"])

    def test_xml_node_and_device_are_denied(self):
        report = self.scan("dangerous_xml.launch.xml")
        joined = "\n".join(report["findings"])
        self.assertIn("rplidar", joined)
        self.assertIn("/dev/ttyUSB9", joined)
        self.assertEqual([
            {
                "package": "rplidar_ros",
                "executable": "rplidar_node",
                "name": "lidar",
            }
        ], report["nodes"])

    def test_missing_node_names_require_review_for_python_and_xml(self):
        with tempfile.TemporaryDirectory(
            prefix="boomboomfly_launch_name_", dir="/tmp"
        ) as temporary:
            root = Path(temporary)
            python_launch = root / "missing_name.launch.py"
            python_launch.write_text(
                "from launch_ros.actions import Node\n"
                "node = Node(package='demo', executable='demo')\n",
                encoding="utf-8",
            )
            xml_launch = root / "missing_name.launch.xml"
            xml_launch.write_text(
                "<launch><node pkg='demo' exec='demo'/></launch>\n",
                encoding="utf-8",
            )
            python_report = GUARD.analyze(python_launch, ROOT, self.profile)
            xml_report = GUARD.analyze(xml_launch, ROOT, self.profile)
            self.assertEqual([], python_report["nodes"])
            self.assertEqual([], xml_report["nodes"])
            self.assertTrue(any(
                "missing Node name" in item
                for item in python_report["reviews"]
            ))
            self.assertTrue(any(
                "missing XML node name" in item
                for item in xml_report["reviews"]
            ))

    def test_check_file_exit_codes(self):
        cases = [
            ("safe_one_writer.launch.py", GUARD.EXIT_PASS, "PASS"),
            ("dangerous_node.launch.py", GUARD.EXIT_DENIED, "DENIED"),
            ("dynamic_requires_review.launch.py", GUARD.EXIT_REVIEW,
             "REQUIRES_REVIEW"),
        ]
        for filename, expected_code, expected_result in cases:
            with self.subTest(filename=filename):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    code = GUARD.main([
                        "--repository-root", str(ROOT),
                        "--check-file", str(FIXTURES / filename),
                    ])
                self.assertEqual(expected_code, code)
                self.assertEqual(
                    expected_result, json.loads(output.getvalue())["result"]
                )

    def test_extra_benign_node_in_allowlisted_launch_is_denied(self):
        with tempfile.TemporaryDirectory(
            prefix="boomboomfly_launch_allowlist_", dir="/tmp"
        ) as temporary:
            source = Path(temporary)
            subprocess.run(["git", "init", "-q", str(source)], check=True)
            allowed = source / "src/offboard_cpp/launch/offboard_control.launch.py"
            allowed.parent.mkdir(parents=True)
            allowed.write_text(
                "from launch import LaunchDescription\n"
                "from launch_ros.actions import Node\n\n"
                "def generate_launch_description():\n"
                "    return LaunchDescription([\n"
                "        Node(package='offboard_cpp', "
                "executable='offboard_node', name='offboard_control_node'),\n"
                "        Node(package='vision_to_dds', "
                "executable='vision_to_dds_node', name='unexpected_benign'),\n"
                "    ])\n",
                encoding="utf-8",
            )
            profile = dict(self.profile)
            profile["historical_denied_inventory"] = []
            profile_path = source / "profile.json"
            profile_path.write_text(
                json.dumps(profile, indent=2) + "\n", encoding="utf-8"
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = GUARD.main([
                    "--repository-root", str(ROOT),
                    "--source-workspace-root", str(source),
                    "--profile", str(profile_path),
                    "--schema", str(
                        ROOT / "config/profiles/dds_only_launch.schema.json"
                    ),
                ])
            self.assertEqual(GUARD.EXIT_DENIED, code)
            result = json.loads(output.getvalue())
            self.assertEqual("DENIED", result["result"])
            self.assertTrue(any(
                "exact Node allowlist mismatch" in item
                for item in result["errors"]
            ))

    def test_new_unclassified_launch_requires_review(self):
        with tempfile.TemporaryDirectory(
            prefix="boomboomfly_launch_guard_", dir="/tmp"
        ) as temporary:
            source = Path(temporary)
            subprocess.run(["git", "init", "-q", str(source)], check=True)
            allowed = source / "src/offboard_cpp/launch/offboard_control.launch.py"
            allowed.parent.mkdir(parents=True)
            shutil.copy2(FIXTURES / "safe_one_writer.launch.py", allowed)
            new_launch = source / "src/new_package/launch/new.launch.py"
            new_launch.parent.mkdir(parents=True)
            shutil.copy2(FIXTURES / "safe_one_writer.launch.py", new_launch)

            profile = dict(self.profile)
            profile["historical_denied_inventory"] = []
            profile_path = source / "profile.json"
            profile_path.write_text(
                json.dumps(profile, indent=2) + "\n", encoding="utf-8"
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = GUARD.main([
                    "--repository-root", str(ROOT),
                    "--source-workspace-root", str(source),
                    "--profile", str(profile_path),
                    "--schema", str(
                        ROOT / "config/profiles/dds_only_launch.schema.json"
                    ),
                ])
            self.assertEqual(GUARD.EXIT_REVIEW, code)
            result = json.loads(output.getvalue())
            self.assertEqual("REQUIRES_REVIEW", result["result"])
            self.assertEqual(1, result["unclassified"])


if __name__ == "__main__":
    unittest.main()
