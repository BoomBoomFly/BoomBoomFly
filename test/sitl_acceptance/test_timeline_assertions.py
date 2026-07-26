"""Offline assertion tests over conspicuously synthetic event timelines."""

import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from assert_timeline import assert_files, main, run_assertions
from fixture_utils import (
    VALID_DIR,
    apply_timeline_mutation,
    load_cases,
    load_scenario,
    load_timeline,
)
from parse_timeline import parse_timeline


def failed_assertion_ids(result):
    """Return the stable IDs of failed assertions."""
    return {
        item["assertion_id"]
        for item in result["assertions"]
        if item["status"] == "FAIL"
    }


class TimelineAssertionTests(unittest.TestCase):
    """Cover each required temporal, identity, and cardinality rejection."""

    def test_valid_synthetic_timeline_passes_offline_only(self) -> None:
        result = assert_files(
            VALID_DIR / "synthetic_scenario.json",
            VALID_DIR / "synthetic_timeline.jsonl",
            "jsonl",
        )
        self.assertEqual("PASS", result["status"])
        self.assertEqual([], result["errors"])
        self.assertGreater(result["summary"]["assertions_passed"], 0)
        self.assertEqual(0, result["summary"]["assertions_failed"])

    def test_all_declared_negative_timelines_fail(self) -> None:
        scenario = load_scenario()
        for case in load_cases("timeline_cases.json"):
            with self.subTest(case_id=case["case_id"]):
                events = apply_timeline_mutation(load_timeline(), case)
                encoded = json.dumps(events, sort_keys=True).encode("utf-8")
                result = run_assertions(
                    scenario, events, hashlib.sha256(encoded).hexdigest()
                )
                failures = failed_assertion_ids(result)
                self.assertEqual("FAIL", result["status"])
                if "expected_assertion" in case:
                    self.assertIn(case["expected_assertion"], failures)
                else:
                    self.assertTrue(
                        any(
                            item.startswith(case["expected_assertion_prefix"])
                            for item in failures
                        ),
                        failures,
                    )

    def test_parse_preserves_observed_order(self) -> None:
        expected = load_timeline()
        parsed, errors = parse_timeline(
            VALID_DIR / "synthetic_timeline.jsonl", "jsonl"
        )
        self.assertEqual([], errors)
        self.assertEqual(
            [item["metadata"]["event_id"] for item in expected],
            [item["metadata"]["event_id"] for item in parsed],
        )

    def test_assert_cli_invalid_timeline_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.jsonl"
            path.write_text('{"truncated":\n', encoding="utf-8")
            stream = io.StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "--scenario",
                        str(VALID_DIR / "synthetic_scenario.json"),
                        "--timeline",
                        str(path),
                        "--format",
                        "jsonl",
                    ]
                )
            result = json.loads(stream.getvalue())
            self.assertNotEqual(0, exit_code)
            self.assertEqual("FAIL", result["status"])
            self.assertTrue(result["errors"])


if __name__ == "__main__":
    unittest.main()
