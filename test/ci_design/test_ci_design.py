"""Tests for the Wave 3A design-only CI oracle."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from validate_ci_design import (
    EXPECTED_FIXTURE_KINDS,
    EXPECTED_JOBS,
    inspect_negative_fixture,
    validate_config,
)


HERE = Path(__file__).resolve().parent
CONFIG = HERE / "job_graph.json"
VALIDATOR = HERE / "validate_ci_design.py"
INVALID = HERE / "fixtures" / "invalid"


def load(path: Path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


class JobGraphTest(unittest.TestCase):
    def test_design_config_is_internally_consistent(self) -> None:
        self.assertEqual(validate_config(load(CONFIG)), [])

    def test_required_job_ids_are_exact_and_unique(self) -> None:
        jobs = load(CONFIG)["jobs"]
        ids = [job["id"] for job in jobs]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), EXPECTED_JOBS)

    def test_workflow_enablement_fails_until_every_lock_is_resolved(self) -> None:
        config = load(CONFIG)
        config["workflow_enabled"] = True
        errors = validate_config(config)
        self.assertTrue(
            any("workflow cannot be enabled" in error for error in errors),
            errors,
        )

    def test_fail_open_job_command_is_rejected(self) -> None:
        config = copy.deepcopy(load(CONFIG))
        config["jobs"][0]["commands"].append("unsafe-command || true")
        errors = validate_config(config)
        self.assertTrue(any("fail-open bypass" in error for error in errors))


class NegativeFixtureTest(unittest.TestCase):
    def test_fixture_set_covers_every_required_category(self) -> None:
        fixtures = sorted(INVALID.glob("*.json"))
        kinds = {load(path)["kind"] for path in fixtures}
        self.assertEqual(kinds, EXPECTED_FIXTURE_KINDS)
        self.assertEqual(len(fixtures), len(EXPECTED_FIXTURE_KINDS))

    def test_every_deliberately_broken_fixture_has_a_policy_violation(self) -> None:
        for path in sorted(INVALID.glob("*.json")):
            with self.subTest(fixture=path.name):
                self.assertTrue(inspect_negative_fixture(load(path)))

    def test_every_deliberately_broken_fixture_exits_nonzero(self) -> None:
        for path in sorted(INVALID.glob("*.json")):
            with self.subTest(fixture=path.name):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(VALIDATOR),
                        "--fixture",
                        str(path),
                    ],
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn("REJECT:", result.stderr)

    def test_positive_config_cli_exits_zero(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                "--config",
                str(CONFIG),
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS:", result.stdout)


if __name__ == "__main__":
    unittest.main()
