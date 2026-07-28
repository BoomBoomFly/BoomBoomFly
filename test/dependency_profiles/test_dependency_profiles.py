#!/usr/bin/env python3
"""Positive and fail-closed tests for synthetic dependency profiles."""

import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


TEST_DIR = Path(__file__).resolve().parent
VALIDATOR_PATH = TEST_DIR / "validate_dependency_profiles.py"
FIXTURES = TEST_DIR / "fixtures"
REPO_ROOT = TEST_DIR.parents[1]
INSTALLER = REPO_ROOT / "Scripts" / "installation" / "uav_px4_dds_install.sh"
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

    def test_abbreviated_sha_is_nonzero(self):
        result = self._run_fixture("non_exact_sha.json")
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

    def test_root_has_one_governed_manifest(self):
        self.assertEqual(
            ["workspace.lock.repos"],
            sorted(path.name for path in REPO_ROOT.glob("workspace*.repos")),
        )

    def test_real_profile_manifest_is_exact_and_disjoint(self):
        self.assertEqual([], VALIDATOR.validate_manifest_profiles(REPO_ROOT))
        profile_ids, repositories = VALIDATOR.selected_manifest_profiles(
            REPO_ROOT,
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
        paths = [entry["path"] for entry in repositories]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(16, len(paths))
        self.assertNotIn("src/serial_driver_ros", paths)
        self.assertNotIn("src/serial_driver_ros2", paths)
        all_entries = VALIDATOR.load_repos_manifest(
            REPO_ROOT / VALIDATOR.PROFILE_MANIFEST
        )
        quarantine = [
            entry for entry in all_entries if entry["profile"] == "quarantine"
        ]
        self.assertEqual(["src/serial_driver_ros"], [entry["path"] for entry in quarantine])

    def test_real_manifest_cli_default_excludes_archive_and_optional(self):
        result = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR_PATH),
                "--manifest-root",
                str(REPO_ROOT),
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(["active"], payload["selected_profiles"])
        self.assertEqual(4, len(payload["repository_paths"]))
        self.assertNotIn("src/px4_bringup", payload["repository_paths"])

    def test_real_manifest_mutations_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            manifest = temp_root / VALIDATOR.PROFILE_MANIFEST
            shutil.copy2(REPO_ROOT / VALIDATOR.PROFILE_MANIFEST, manifest)

            original = manifest.read_text(encoding="utf-8")
            manifest.write_text(original.replace("0fbdcbf6ee53d6927de75af1d98f22cf5bd4f917", "DDS"), encoding="utf-8")
            issues = VALIDATOR.validate_manifest_profiles(temp_root)
            self.assertTrue(any("moving or non-exact ref" in issue for issue in issues))

            manifest.write_text(original.replace("src/px4_bringup", "src/px4_msgs"), encoding="utf-8")
            issues = VALIDATOR.validate_manifest_profiles(temp_root)
            self.assertTrue(any("duplicate path src/px4_msgs" in issue for issue in issues))

            manifest.write_text(original.replace("AyasOwen", "substitution"), encoding="utf-8")
            issues = VALIDATOR.validate_manifest_profiles(temp_root)
            self.assertTrue(any("URL mismatch for src/px4_bringup" in issue for issue in issues))

            manifest.write_text(original.replace("# profile: active\n", "", 1), encoding="utf-8")
            issues = VALIDATOR.validate_manifest_profiles(temp_root)
            self.assertTrue(any("missing a profile marker" in issue for issue in issues))

    def test_installer_profile_flags_are_explicit_and_offline_dry_run(self):
        help_result = subprocess.run(
            ["bash", str(INSTALLER), "--help"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        self.assertEqual(0, help_result.returncode, help_result.stderr)
        self.assertIn("--with-archive", help_result.stdout)
        self.assertIn("--with-optional <name>", help_result.stdout)

        with tempfile.TemporaryDirectory() as temp_dir:
            base_args = [
                "bash",
                str(INSTALLER),
                "--src-dir",
                str(Path(temp_dir) / "src"),
                "--dry-run",
                "--skip-package-check",
            ]
            default = subprocess.run(
                base_args,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            self.assertEqual(0, default.returncode, default.stderr)
            self.assertIn("Profiles:     active", default.stdout)
            self.assertNotIn("[PLAN] px4_bringup", default.stdout)

            composed = subprocess.run(
                base_args
                + [
                    "--with-archive",
                    "--with-optional",
                    "perception",
                    "--with-optional",
                    "navigation",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            self.assertEqual(0, composed.returncode, composed.stderr)
            self.assertIn("Profiles:     active archive optional-perception optional-navigation", composed.stdout)
            self.assertIn("px4_bringup", composed.stdout)

            custom_exact = subprocess.run(
                base_args + ["--manifest", str(REPO_ROOT / "workspace.lock.repos")],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            self.assertEqual(0, custom_exact.returncode, custom_exact.stderr)
            self.assertIn("Repositories:16", custom_exact.stdout)

            moving_manifest = Path(temp_dir) / "moving.repos"
            moving_manifest.write_text(
                "repositories:\n"
                "  src/example:\n"
                "    type: git\n"
                "    url: https://example.com/example.git\n"
                "    version: main\n",
                encoding="utf-8",
            )
            moving_denied = subprocess.run(
                base_args + ["--manifest", str(moving_manifest)],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            self.assertNotEqual(0, moving_denied.returncode)
            self.assertIn("not a 40-character lock SHA", moving_denied.stderr)

            removed_flag = subprocess.run(
                base_args
                + [
                    "--manifest",
                    str(REPO_ROOT / "workspace.lock.repos"),
                    "--allow-moving-refs",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            self.assertNotEqual(0, removed_flag.returncode)
            self.assertIn("Unknown option: --allow-moving-refs", removed_flag.stderr)

            external_manifest = Path(temp_dir) / "external.repos"
            external_manifest.write_text(
                "repositories:\n"
                "  ../communication:\n"
                "    type: git\n"
                "    url: https://example.com/communication.git\n"
                "    version: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n",
                encoding="utf-8",
            )
            external_denied = subprocess.run(
                base_args + ["--manifest", str(external_manifest)],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            self.assertNotEqual(0, external_denied.returncode)
            self.assertIn("Manifest path must be below src/", external_denied.stderr)

            conflicting = subprocess.run(
                base_args
                + [
                    "--manifest",
                    str(REPO_ROOT / "workspace.lock.repos"),
                    "--with-archive",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            self.assertNotEqual(0, conflicting.returncode)
            self.assertIn("cannot be combined", conflicting.stderr)


if __name__ == "__main__":
    unittest.main()
