#!/usr/bin/env python3
"""Tests for the fail-closed environment inventory verifier."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "Scripts/installation/verify_environment.py"
INVENTORY = ROOT / "docs/evidence/environment/current_environment.json"
LOCK = ROOT / "docs/evidence/environment/px4_source_toolchain_lock.template.json"
ENVIRONMENT_SCHEMA = ROOT / "docs/evidence/schemas/environment.schema.json"
LOCK_SCHEMA = ROOT / "docs/evidence/schemas/px4_source_toolchain_lock.schema.json"

SPEC = importlib.util.spec_from_file_location("verify_environment", str(SCRIPT))
VERIFY = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VERIFY)


class EnvironmentValidationTests(unittest.TestCase):
    def setUp(self):
        with INVENTORY.open("r", encoding="utf-8") as stream:
            self.inventory = json.load(stream)
        with LOCK.open("r", encoding="utf-8") as stream:
            self.lock = json.load(stream)

    def assert_environment_rejected(self, document):
        with self.assertRaises(VERIFY.InventoryError):
            VERIFY.validate_environment(document)

    def test_checked_in_documents_validate(self):
        VERIFY.validate_environment(self.inventory)
        VERIFY.validate_px4_lock(self.lock)
        with ENVIRONMENT_SCHEMA.open("r", encoding="utf-8") as stream:
            VERIFY.validate_json_schema(
                self.inventory, json.load(stream), "environment inventory"
            )
        with LOCK_SCHEMA.open("r", encoding="utf-8") as stream:
            VERIFY.validate_json_schema(self.lock, json.load(stream), "PX4 lock")

    def test_json_schema_rejects_additional_property(self):
        document = copy.deepcopy(self.inventory)
        document["unexpected"] = True
        with ENVIRONMENT_SCHEMA.open("r", encoding="utf-8") as stream:
            schema = json.load(stream)
        with self.assertRaises(VERIFY.InventoryError):
            VERIFY.validate_json_schema(document, schema, "environment inventory")

    def test_current_compare_rejects_stale_provenance_and_ros_version(self):
        current = copy.deepcopy(self.inventory)
        current["repository"]["head"] = "0" * 40
        current["ros"]["packages"][0]["version"] = "0.0.0"
        issues = VERIFY.compare_current(self.inventory, current)
        self.assertTrue(any("repository.head" in issue for issue in issues), issues)
        self.assertTrue(any("ROS package" in issue for issue in issues), issues)

    def test_current_compare_rejects_submodule_provenance_tampering(self):
        mutations = (
            ("stdout", " 0" * 20 + " modules/example\n", "stdout"),
            (
                "command",
                ["git", "-C", "<PX4_SOURCE>", "submodule", "status"],
                "command",
            ),
            ("exit_code", 9, "exit_code"),
            ("reason", "unverified for a different reason", "reason"),
        )
        for field, value, expected_fragment in mutations:
            with self.subTest(field=field):
                current = copy.deepcopy(self.inventory)
                current["px4_source"]["submodules"][field] = value
                issues = VERIFY.compare_current(self.inventory, current)
                self.assertTrue(
                    any(
                        "px4_source.submodules.{}".format(expected_fragment) in issue
                        for issue in issues
                    ),
                    issues,
                )

    def test_current_compare_normalizes_only_host_specific_px4_paths(self):
        expected = copy.deepcopy(self.inventory)
        current = copy.deepcopy(self.inventory)
        expected_probe = expected["px4_source"]["submodules"]
        current_probe = current["px4_source"]["submodules"]
        expected_probe.update(
            {
                "status": "present",
                "version": "recursive-status-recorded",
                "command": [
                    "git",
                    "-C",
                    "/machine-a/PX4-Autopilot",
                    "submodule",
                    "status",
                    "--recursive",
                ],
                "exit_code": 0,
                "stdout": " 1111111111111111111111111111111111111111 modules/a\n"
                " 2222222222222222222222222222222222222222 modules/b\n",
                "stderr": "",
                "reason": "",
            }
        )
        current_probe.update(copy.deepcopy(expected_probe))
        current_probe["command"][2] = "/machine-b/PX4-Autopilot"
        current_probe["stdout"] = (
            " 2222222222222222222222222222222222222222 modules/b\n"
            " 1111111111111111111111111111111111111111 modules/a\n"
        )
        issues = VERIFY.compare_current(expected, current)
        self.assertFalse(
            any("px4_source.submodules" in issue for issue in issues), issues
        )

    def test_current_compare_rejects_present_submodule_reason_tampering(self):
        expected = copy.deepcopy(self.inventory)
        current = copy.deepcopy(self.inventory)
        for document in (expected, current):
            document["px4_source"]["submodules"].update(
                {
                    "status": "present",
                    "version": "recursive-status-recorded",
                    "exit_code": 0,
                    "stdout": (
                        " 1111111111111111111111111111111111111111 modules/a\n"
                    ),
                    "stderr": "",
                    "reason": "",
                }
            )
        current["px4_source"]["submodules"]["reason"] = "tampered"
        issues = VERIFY.compare_current(expected, current)
        self.assertTrue(
            any("px4_source.submodules.reason" in issue for issue in issues), issues
        )

    def test_missing_required_field_is_rejected(self):
        document = copy.deepcopy(self.inventory)
        del document["platform"]
        self.assert_environment_rejected(document)

    def test_moving_latest_is_rejected(self):
        document = copy.deepcopy(self.inventory)
        document["tools"][0]["version"] = "latest"
        self.assert_environment_rejected(document)

    def test_present_probe_with_nonzero_exit_is_rejected(self):
        document = copy.deepcopy(self.inventory)
        document["tools"][0]["exit_code"] = 1
        self.assert_environment_rejected(document)

    def test_missing_probe_with_zero_exit_is_rejected(self):
        document = copy.deepcopy(self.inventory)
        missing = next(
            item for item in document["tools"] if item["name"] == "arm-none-eabi-gcc"
        )
        missing["exit_code"] = 0
        self.assert_environment_rejected(document)

    def test_unverified_probe_requires_reason(self):
        document = copy.deepcopy(self.inventory)
        document["px4_source"]["submodules"]["reason"] = ""
        self.assert_environment_rejected(document)

    def test_bad_repository_head_is_rejected(self):
        document = copy.deepcopy(self.inventory)
        document["repository"]["head"] = "deadbeef"
        self.assert_environment_rejected(document)

    def test_px4_template_cannot_claim_locked(self):
        document = copy.deepcopy(self.lock)
        document["status"] = "locked"
        with self.assertRaises(VERIFY.InventoryError):
            VERIFY.validate_px4_lock(document)

    def test_px4_non_sha_commit_is_rejected(self):
        document = copy.deepcopy(self.lock)
        document["source"]["commit"] = "v1.16.2"
        with self.assertRaises(VERIFY.InventoryError):
            VERIFY.validate_px4_lock(document)

    def test_help_works_outside_repository(self):
        with tempfile.TemporaryDirectory(prefix="bbf environment help ") as temp_dir:
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--help"],
                cwd=temp_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("--check-current", completed.stdout)

    def test_capture_writes_only_explicit_temp_output(self):
        with tempfile.TemporaryDirectory(prefix="bbf environment capture ") as temp_dir:
            output = Path(temp_dir) / "captured environment.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repository-root",
                    str(ROOT),
                    "--capture",
                    "--output",
                    str(output),
                ],
                cwd=temp_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            with output.open("r", encoding="utf-8") as stream:
                captured = json.load(stream)
            VERIFY.validate_environment(captured)
            agent = next(
                item for item in captured["tools"] if item["name"] == "MicroXRCEAgent"
            )
            self.assertNotIn("--version", agent["command"])
            self.assertEqual(captured["px4_source"]["host_search_status"], "unverified")


if __name__ == "__main__":
    unittest.main()
