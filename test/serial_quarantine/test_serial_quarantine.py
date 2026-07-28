"""Pure-software fault tests for the non-production serial quarantine."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "Scripts/test/verify_serial_quarantine.py"
SPEC = importlib.util.spec_from_file_location("verify_serial_quarantine", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SerialQuarantineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="bbf_serial_quarantine_")
        self.root = Path(self.temp.name)
        (self.root / "config/profiles").mkdir(parents=True)
        (self.root / "launch").mkdir()
        (self.root / "launch/safe.launch.py").write_text(
            "from launch import LaunchDescription\n", encoding="utf-8"
        )
        self.quarantine = {
            "repositories": {
                "src/serial_driver_ros": {
                    "type": "git",
                    "url": "https://github.com/BoomBoomFly/serial_driver_ros.git",
                    "version": "9d8c07814ad0f64f76c5fd8fe12072aebcbef431",
                }
            }
        }
        self.active_lock = {
            "repositories": {
                "src/offboard_cpp": {
                    "type": "git",
                    "url": "https://github.com/BoomBoomFly/offboard_cpp.git",
                    "version": "cded3dc5b6906420db3767abd82b2df7ba6ea9f0",
                }
            }
        }
        self.package_profile = {
            "quarantine_manifests": ["workspace.lock.repos"],
            "production_packages": [
                {"name": "offboard_cpp", "path": "src/offboard_cpp"}
            ],
            "forbidden_packages": [
                {"name": "serial_driver", "path": "src/serial_driver_ros"}
            ],
        }
        self.launch_profile = {
            "production_allowlist": {
                "launch/safe.launch.py": {
                    "nodes": [{"package": "offboard_cpp", "executable": "offboard_node"}]
                }
            }
        }
        self.write_fixture()

    def tearDown(self):
        self.temp.cleanup()

    def write_fixture(self):
        def render(repositories):
            lines = []
            for path, entry in sorted(repositories.items()):
                lines.extend(
                    [
                        "  {}:".format(path),
                        "    type: {}".format(entry["type"]),
                        "    url: {}".format(entry["url"]),
                        "    version: {}".format(entry["version"]),
                    ]
                )
            return "\n".join(lines)

        manifest = (
            "repositories:\n"
            "# profile: active\n"
            + render(self.active_lock["repositories"])
            + "\n# profile: quarantine\n"
            + render(self.quarantine["repositories"])
            + "\n"
        )
        (self.root / "workspace.lock.repos").write_text(manifest, encoding="utf-8")
        (self.root / "config/profiles/dds_only_packages.yaml").write_text(
            json.dumps(self.package_profile), encoding="utf-8"
        )
        (self.root / "config/profiles/dds_only_launch.yaml").write_text(
            json.dumps(self.launch_profile), encoding="utf-8"
        )

    def verify(self):
        return MODULE.verify(self.root, None, Path("/tmp/bbf_serial_quarantine_test"))

    def test_valid_quarantine_is_accepted(self):
        result = self.verify()
        self.assertEqual("PASS", result["status"])
        self.assertEqual(0, result["production_launch_references"])
        self.assertEqual(0, result["production_package_references"])

    def test_moving_ref_is_rejected(self):
        self.quarantine["repositories"]["src/serial_driver_ros"]["version"] = "master"
        self.write_fixture()
        with self.assertRaisesRegex(MODULE.QuarantineError, "exact 40-character SHA"):
            self.verify()

    def test_active_manifest_entry_is_rejected(self):
        self.active_lock["repositories"]["src/serial_driver_ros"] = dict(
            self.quarantine["repositories"]["src/serial_driver_ros"]
        )
        self.write_fixture()
        with self.assertRaisesRegex(
            MODULE.QuarantineError, "entered non-quarantine profile active"
        ):
            self.verify()

    def test_production_package_entry_is_rejected(self):
        self.package_profile["production_packages"].append(
            {"name": "serial_driver", "path": "src/serial_driver_ros"}
        )
        self.write_fixture()
        with self.assertRaisesRegex(MODULE.QuarantineError, "production package"):
            self.verify()

    def test_production_launch_reference_is_rejected(self):
        (self.root / "launch/safe.launch.py").write_text(
            "Node(package='serial_driver', executable='serial_driver')\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(MODULE.QuarantineError, "production launch"):
            self.verify()

    def test_wrong_origin_is_rejected(self):
        self.quarantine["repositories"]["src/serial_driver_ros"]["url"] = (
            "https://example.invalid/serial_driver_ros.git"
        )
        self.write_fixture()
        with self.assertRaisesRegex(MODULE.QuarantineError, "origin mismatch"):
            self.verify()


if __name__ == "__main__":
    unittest.main()
