"""Wave 3B B/C event-contract integration over offline synthetic records."""

import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from assert_timeline import assert_files, main as assert_main, run_assertions
from fixture_utils import REPO_ROOT
from validate_scenario import WAVE3B_REQUIRED_CASES, validate_scenario


SCENARIO = REPO_ROOT / "docs/verification/scenarios/faults/SITL-FAULT-025.json"
TIMELINE = (
    REPO_ROOT
    / "test/sitl_acceptance/fixtures/valid/wave3b_runtime_timeline.jsonl"
)


def load_scenario():
    return json.loads(SCENARIO.read_text(encoding="utf-8"))


def load_timeline():
    return [
        json.loads(line)
        for line in TIMELINE.read_text(encoding="utf-8").splitlines()
        if line
    ]


class Wave3BRuntimeMatrixTests(unittest.TestCase):
    def test_complete_offline_matrix_passes_without_px4_identity(self):
        result = assert_files(SCENARIO, TIMELINE, "jsonl")
        self.assertEqual("PASS", result["status"])
        self.assertEqual(16, result["summary"]["events_read"])
        case_assertions = {
            item["assertion_id"]
            for item in result["assertions"]
            if item["assertion_id"].startswith("wave3b.")
            and item["assertion_id"].endswith(".contract")
        }
        self.assertEqual(len(WAVE3B_REQUIRED_CASES), len(case_assertions))
        for event in load_timeline():
            metadata = event["metadata"]
            self.assertEqual("OFFLINE_SYNTHETIC", metadata["fixture_scope"])
            self.assertTrue(metadata["synthetic"])
            self.assertFalse(metadata["formal_sitl_evidence"])
            self.assertEqual("BLOCKED", metadata["px4_source_identity"])

    def test_wrong_event_code_fails_deterministically(self):
        events = load_timeline()
        target = next(
            event
            for event in events
            if event["metadata"].get("contract_case_id") == "ACK_CORRELATION"
        )
        target["metadata"]["event_code"] = "AUTH_ACCEPTED"
        result = run_assertions(load_scenario(), events, "synthetic-mutation")
        self.assertEqual("FAIL", result["status"])
        failed = {
            item["assertion_id"]
            for item in result["assertions"]
            if item["status"] == "FAIL"
        }
        self.assertIn("wave3b.ack_correlation.contract", failed)

    def test_publish_or_timeout_mutation_returns_nonzero_cli(self):
        mutations = (("synthetic_publish_count", 1), ("monotonic_timestamp", 0.75))
        for field, value in mutations:
            with self.subTest(field=field):
                events = load_timeline()
                target = next(
                    event
                    for event in events
                    if event["metadata"].get("contract_case_id") == "ACK_TIMEOUT"
                )
                if field == "monotonic_timestamp":
                    target[field] = value
                    target["timestamp"] = "2026-07-27T00:00:00.750000Z"
                    events.sort(key=lambda event: event["monotonic_timestamp"])
                else:
                    target["metadata"][field] = value
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "mutated.jsonl"
                    path.write_text(
                        "".join(
                            json.dumps(event, sort_keys=True) + "\n"
                            for event in events
                        ),
                        encoding="utf-8",
                    )
                    stream = io.StringIO()
                    with redirect_stdout(stream):
                        exit_code = assert_main(
                            [
                                "--scenario",
                                str(SCENARIO),
                                "--timeline",
                                str(path),
                                "--format",
                                "jsonl",
                            ]
                        )
                self.assertNotEqual(0, exit_code)
                self.assertEqual("FAIL", json.loads(stream.getvalue())["status"])

    def test_missing_case_or_evidence_promotion_is_rejected(self):
        missing = load_scenario()
        missing["extensions"]["wave3b_runtime_contract"]["cases"].pop()
        self.assertTrue(
            any(error["code"] == "WAVE3B_CASE_MISSING" for error in validate_scenario(missing))
        )

        promoted = copy.deepcopy(load_scenario())
        promoted["evidence"]["acceptance_level"] = "FORMAL_SITL"
        promoted["evidence"]["synthetic_fixture_allowed"] = False
        self.assertTrue(
            any(error["code"] == "WAVE3B_EVIDENCE" for error in validate_scenario(promoted))
        )


if __name__ == "__main__":
    unittest.main()
