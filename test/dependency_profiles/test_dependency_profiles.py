#!/usr/bin/env python3
"""Positive and fail-closed tests for synthetic dependency profiles."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


TEST_DIR = Path(__file__).resolve().parent
VALIDATOR_PATH = TEST_DIR / "validate_dependency_profiles.py"
FIXTURES = TEST_DIR / "fixtures"
SPEC = importlib.util.spec_from_file_location(
    "validate_dependency_profiles", VALIDATOR_PATH
)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class DependencyProfileTests(unittest.TestCase):
    def setUp(self):
        self.catalog = VALIDATOR.load_catalog(FIXTURES / "valid_profiles.json")

    def _run_fixture(self, name, *arguments):
        return subprocess.run(
            [sys.executable, str(VALIDATOR_PATH), str(FIXTURES / name)]
            + list(arguments),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

    def test_valid_catalog_passes(self):
        self.assertEqual([], VALIDATOR.validate_catalog(self.catalog))

    def test_default_restore_contains_only_active(self):
        profile_ids, repositories = VALIDATOR.selected_profiles(self.catalog)
        self.assertEqual(["active"], profile_ids)
        self.assertEqual(["src/px4_msgs"], [item["path"] for item in repositories])
        self.assertNotIn("src/px4_bringup", [item["path"] for item in repositories])
        self.assertNotIn("src/vision_opencv", [item["path"] for item in repositories])
        self.assertNotIn("src/navigation2", [item["path"] for item in repositories])

    def test_archive_and_optional_profiles_require_explicit_selection(self):
        profile_ids, repositories = VALIDATOR.selected_profiles(
            self.catalog,
            with_archive=True,
            optional=("perception", "navigation"),
        )
        self.assertEqual(
            [
                "active",
                "archive",
                "optional-perception",
                "optional-navigation",
            ],
            profile_ids,
        )
        self.assertEqual(
            [
                "src/px4_msgs",
                "src/px4_bringup",
                "src/vision_opencv",
                "src/navigation2",
            ],
            [item["path"] for item in repositories],
        )

    def test_moving_archive_ref_is_nonzero(self):
        result = self._run_fixture("moving_archive.json")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("moving or non-exact ref", result.stderr)

    def test_cross_profile_duplicate_path_is_nonzero(self):
        result = self._run_fixture("duplicate_path.json")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("duplicate path src/px4_msgs", result.stderr)

    def test_url_mismatch_is_nonzero(self):
        result = self._run_fixture("url_mismatch.json")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("URL mismatch for px4_bringup", result.stderr)

    def test_moving_optional_ref_fails_closed(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["profiles"]["optional-navigation"]["repositories"][0][
            "version"
        ] = "main"
        issues = VALIDATOR.validate_catalog(catalog)
        self.assertTrue(any("moving or non-exact ref" in issue for issue in issues))

    def test_duplicate_repository_id_fails_closed(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["profiles"]["archive"]["repositories"][0][
            "repository_id"
        ] = "px4_msgs"
        issues = VALIDATOR.validate_catalog(catalog)
        self.assertTrue(any("duplicate repository_id px4_msgs" in issue for issue in issues))

    def test_unresolved_serial_driver_cannot_enter_profile(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["canonical_urls"]["serial_driver_ros"] = (
            "https://github.com/example/serial_driver_ros.git"
        )
        catalog["profiles"]["archive"]["repositories"].append(
            {
                "repository_id": "serial_driver_ros",
                "path": "src/serial_driver_ros",
                "type": "git",
                "url": "https://github.com/example/serial_driver_ros.git",
                "version": "0123456789abcdef0123456789abcdef01234567",
            }
        )
        issues = VALIDATOR.validate_catalog(catalog)
        self.assertTrue(
            any("unresolved decision path" in issue for issue in issues)
        )

    def test_cli_help_and_positive_default(self):
        help_result = subprocess.run(
            [sys.executable, str(VALIDATOR_PATH), "--help"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        self.assertEqual(0, help_result.returncode)
        self.assertIn("--with-archive", help_result.stdout)
        self.assertIn("--with-optional", help_result.stdout)

        result = self._run_fixture("valid_profiles.json")
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(["active"], payload["selected_profiles"])
        self.assertEqual(["src/px4_msgs"], payload["repository_paths"])


if __name__ == "__main__":
    unittest.main()
