"""Structural event validation tests using synthetic records only."""

import copy
import io
import json
import unittest
from contextlib import redirect_stdout

from fixture_utils import INVALID_DIR, VALID_DIR, load_json, load_timeline
from validate_event import load_events, main, validate_event, validate_events


class EventValidationTests(unittest.TestCase):
    """Check event schema enforcement and JSONL parsing."""

    def test_valid_synthetic_event(self) -> None:
        self.assertEqual(
            [], validate_event(load_json(VALID_DIR / "synthetic_event.json"))
        )

    def test_valid_synthetic_jsonl(self) -> None:
        events, parse_errors = load_events(
            VALID_DIR / "synthetic_timeline.jsonl", "jsonl"
        )
        self.assertEqual([], parse_errors)
        self.assertEqual([], validate_events(events))
        self.assertEqual(6, len(events))

    def test_missing_required_event_fields_fail_closed(self) -> None:
        errors = validate_event(load_json(INVALID_DIR / "malformed_event.json"))
        self.assertGreater(len(errors), 0)
        self.assertIn("REQUIRED", {item["code"] for item in errors})

    def test_synthetic_event_cannot_claim_px4_identity(self) -> None:
        event = copy.deepcopy(load_timeline()[0])
        event["metadata"]["identity_kind"] = "PX4 authoritative source"
        errors = validate_event(event)
        self.assertIn("MOCK_IDENTITY", {item["code"] for item in errors})

    def test_cli_parse_failure_is_nonzero_and_json(self) -> None:
        stream = io.StringIO()
        with redirect_stdout(stream):
            exit_code = main(["--input", str(INVALID_DIR / "malformed_json.json")])
        summary = json.loads(stream.getvalue())
        self.assertNotEqual(0, exit_code)
        self.assertEqual("FAIL", summary["status"])
        self.assertTrue(summary["errors"])


if __name__ == "__main__":
    unittest.main()
