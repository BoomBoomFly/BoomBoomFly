#!/usr/bin/env python3
"""Positive and fail-closed tests for the DDS-only package boundary."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPOSITORY_ROOT / "Scripts/test/verify_package_boundary.py"
SPEC = importlib.util.spec_from_file_location("verify_package_boundary", MODULE_PATH)
BOUNDARY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BOUNDARY)


class PackageBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(
            prefix="boomboomfly_package_boundary_", dir="/tmp"
        )
        self.root = Path(self.temporary.name)
        self.profile_path = self.root / "profile.yaml"
        self.excluded_path = self.root / "workspace.excluded_packages"
        self.log_base = self.root / "log"
        self.profile = {
            "schema_version": 1,
            "production_packages": [
                {"name": "core_a", "path": "src/core_a"},
                {"name": "core_b", "path": "src/core_b"},
            ],
            "forbidden_packages": [
                {"name": "serial_driver", "path": "src/serial_driver_ros"},
            ],
            "managed_nonproduction_packages": [
                {"name": "support_pkg", "path": "src/support_pkg"},
            ],
        }
        self._write_package("core_a", ["core_b"])
        self._write_package("core_b")
        self._write_package("serial_driver")
        self._write_package("support_pkg")
        self._write_inputs()

    def tearDown(self):
        self.temporary.cleanup()

    def _write_package(self, name, dependencies=None):
        package_dir = self.root / "src" / name
        package_dir.mkdir(parents=True, exist_ok=True)
        dependency_xml = "".join(
            "<depend>{}</depend>".format(dependency)
            for dependency in (dependencies or [])
        )
        (package_dir / "package.xml").write_text(
            "<package format=\"3\"><name>{}</name><version>0.0.0</version>"
            "<description>fixture</description>"
            "<maintainer email=\"fixture@example.invalid\">fixture</maintainer>"
            "<license>MIT</license>{}</package>".format(name, dependency_xml),
            encoding="utf-8",
        )

    def _write_inputs(self):
        self.profile_path.write_text(
            json.dumps(self.profile, indent=2), encoding="utf-8"
        )
        forbidden = [
            item["name"] for item in self.profile["forbidden_packages"]
        ]
        self.excluded_path.write_text(
            "\n".join(forbidden) + "\n", encoding="utf-8"
        )

    def _discovered(self):
        values = {}
        for category in (
            "production_packages",
            "forbidden_packages",
            "managed_nonproduction_packages",
        ):
            for item in self.profile[category]:
                values[item["name"]] = Path(item["path"])
        return values

    def _verify(self, full=None, authoritative=None):
        discovered = full if full is not None else self._discovered()
        selected = authoritative if authoritative is not None else {
            item["name"]: Path(item["path"])
            for item in self.profile["production_packages"]
        }
        with mock.patch.object(
            BOUNDARY,
            "run_colcon_list",
            side_effect=[
                (discovered, ["colcon", "list", "full"]),
                (selected, ["colcon", "list", "authoritative"]),
            ],
        ):
            return BOUNDARY.verify(
                self.root,
                self.profile_path,
                self.excluded_path,
                "colcon",
                self.log_base,
            )

    def test_valid_exact_boundary_passes(self):
        summary = self._verify()
        self.assertEqual("PASS", summary["status"])
        self.assertEqual(["core_a", "core_b"], summary["production_packages"])

    def test_forbidden_package_added_to_allowlist_fails(self):
        self.profile["production_packages"].append(
            {"name": "serial_driver", "path": "src/serial_driver_ros"}
        )
        self._write_inputs()
        with self.assertRaisesRegex(
            BOUNDARY.BoundaryError, "classified more than once"
        ):
            self._verify()

    def test_indirect_forbidden_dependency_fails(self):
        self._write_package("core_b", ["serial_driver"])
        with self.assertRaisesRegex(
            BOUNDARY.BoundaryError, "forbidden dependencies"
        ):
            self._verify()

    def test_undiscovered_direct_forbidden_dependency_fails(self):
        self._write_package("core_a", ["serial_driver"])
        discovered = self._discovered()
        del discovered["serial_driver"]
        with self.assertRaisesRegex(
            BOUNDARY.BoundaryError, "forbidden dependencies"
        ):
            self._verify(full=discovered)

    def test_missing_allowlisted_package_fails(self):
        self.profile["production_packages"].append(
            {"name": "missing_pkg", "path": "src/missing_pkg"}
        )
        self._write_inputs()
        with self.assertRaisesRegex(
            BOUNDARY.BoundaryError, "allowlisted package missing_pkg is missing"
        ):
            self._verify()

    def test_direct_non_allowlisted_workspace_dependency_fails(self):
        self._write_package("core_a", ["support_pkg"])
        with self.assertRaisesRegex(
            BOUNDARY.BoundaryError, "non-allowlisted workspace dependencies"
        ):
            self._verify()

    def test_new_unclassified_ros_package_fails(self):
        discovered = self._discovered()
        discovered["new_package"] = Path("src/new_package")
        with self.assertRaisesRegex(
            BOUNDARY.BoundaryError, "unclassified ROS packages"
        ):
            self._verify(full=discovered)

    def test_authoritative_discovery_extra_package_fails(self):
        selected = {
            "core_a": Path("src/core_a"),
            "core_b": Path("src/core_b"),
            "serial_driver": Path("src/serial_driver_ros"),
        }
        with self.assertRaisesRegex(
            BOUNDARY.BoundaryError, "authoritative discovery mismatch"
        ):
            self._verify(authoritative=selected)

    def test_profile_and_excluded_list_must_match(self):
        self.excluded_path.write_text("serial\nserial_driver\n", encoding="utf-8")
        with self.assertRaisesRegex(
            BOUNDARY.BoundaryError, "differs from forbidden profile"
        ):
            self._verify()


if __name__ == "__main__":
    unittest.main()
