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
