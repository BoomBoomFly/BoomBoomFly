"""Schema-semantic tests for synthetic offline SITL scenarios."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from fixture_utils import (
    INVALID_DIR,
    apply_scenario_mutation,
    load_cases,
    load_scenario,
)
from validate_scenario import main, validate_scenario


class ScenarioValidationTests(unittest.TestCase):
    """Exercise valid and fail-closed scenario paths."""

    def test_synthetic_baseline_is_valid(self) -> None:
        self.assertEqual([], validate_scenario(load_scenario()))

    def test_declared_negative_schema_cases_are_rejected(self) -> None:
        for case in load_cases("scenario_cases.json"):
            with self.subTest(case_id=case["case_id"]):
                document = apply_scenario_mutation(load_scenario(), case)
                errors = validate_scenario(document)
                self.assertGreater(len(errors), 0)
                self.assertIn(case["expected_code"], {item["code"] for item in errors})

    def test_cli_returns_nonzero_json_summary_for_invalid_input(self) -> None:
        stream = io.StringIO()
        with redirect_stdout(stream):
            exit_code = main(
                ["--scenario", str(INVALID_DIR / "malformed_json.json")]
            )
        summary = json.loads(stream.getvalue())
        self.assertNotEqual(0, exit_code)
        self.assertEqual("FAIL", summary["status"])
        self.assertTrue(summary["errors"])

    def test_cli_writes_explicit_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            scenario_path = Path(directory) / "scenario.json"
            output_path = Path(directory) / "summary.json"
            scenario_path.write_text(
                json.dumps(load_scenario(), sort_keys=True), encoding="utf-8"
            )
            stream = io.StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "--scenario",
                        str(scenario_path),
                        "--output",
                        str(output_path),
                    ]
                )
            self.assertEqual(0, exit_code)
            self.assertEqual("PASS", json.loads(output_path.read_text())["status"])


if __name__ == "__main__":
    unittest.main()
