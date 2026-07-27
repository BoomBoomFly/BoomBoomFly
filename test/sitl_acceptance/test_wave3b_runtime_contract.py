"""Wave 3B B/C contract checks using offline synthetic records only."""

import copy
import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from assert_timeline import main, run_assertions
from fixture_utils import REPO_ROOT, VALID_DIR, load_json
from validate_event import validate_events
from validate_scenario import WAVE3B_REQUIRED_CASES, validate_scenario


SCENARIO = REPO_ROOT / "docs/verification/scenarios/faults/SITL-FAULT-025.json"
TIMELINE = VALID_DIR / "wave3b_runtime_timeline.jsonl"


def load_events():
    return [json.loads(line) for line in TIMELINE.read_text(encoding="utf-8").splitlines()]


class Wave3BRuntimeContractTests(unittest.TestCase):
    def test_matrix_is_valid_and_passes_offline_only(self):
        scenario = load_json(SCENARIO)
        events = load_events()
        self.assertEqual([], validate_scenario(scenario))
        self.assertEqual([], validate_events(events))
        result = run_assertions(scenario, events, hashlib.sha256(TIMELINE.read_bytes()).hexdigest())
        self.assertEqual("PASS", result["status"], result)
        self.assertEqual("BLOCKED", scenario["extensions"]["wave3b_runtime_contract"]["px4_source_identity"])

    def test_every_required_case_is_present(self):
        cases = load_json(SCENARIO)["extensions"]["wave3b_runtime_contract"]["cases"]
        self.assertEqual(set(WAVE3B_REQUIRED_CASES), {case["case_id"] for case in cases})

    def test_each_missing_case_fails_deterministically(self):
        scenario = load_json(SCENARIO)
        for case_id in WAVE3B_REQUIRED_CASES:
            with self.subTest(case_id=case_id):
                events = [event for event in load_events() if event["metadata"].get("contract_case_id") != case_id]
                digest = hashlib.sha256(json.dumps(events, sort_keys=True).encode()).hexdigest()
                first = run_assertions(scenario, events, digest)
                second = run_assertions(scenario, copy.deepcopy(events), digest)
                self.assertEqual("FAIL", first["status"])
                self.assertEqual(first, second)
                self.assertIn("wave3b.%s.contract" % case_id.lower(), {item["assertion_id"] for item in first["assertions"] if item["status"] == "FAIL"})

    def test_publish_increment_timeout_and_live_claim_fail(self):
        scenario = load_json(SCENARIO)
        mutations = []
        publish = load_events()
        publish[1]["metadata"]["synthetic_publish_count"] = 1
        mutations.append(publish)
        timeout = load_events()
        timeout_case = next(
            event
            for event in timeout
            if event["metadata"].get("contract_case_id") == "CLOCK_STALE"
        )
        timeout_case["metadata"]["observation_started_monotonic"] = -1.0
        mutations.append(timeout)
        live = load_events()
        live[1]["metadata"]["formal_sitl_evidence"] = True
        mutations.append(live)
        for events in mutations:
            result = run_assertions(scenario, events, "0" * 64)
            self.assertEqual("FAIL", result["status"])

    def test_contract_mutations_are_rejected(self):
        scenario = load_json(SCENARIO)
        scenario["extensions"]["wave3b_runtime_contract"]["px4_source_identity"] = "VERIFIED"
        self.assertIn("WAVE3B_CONTRACT", {item["code"] for item in validate_scenario(scenario)})

    def test_cli_negative_is_deterministic_nonzero(self):
        events = load_events()
        events[1]["metadata"]["synthetic_publish_delta"] = 1
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "negative.jsonl"
            path.write_text("".join(json.dumps(event, sort_keys=True) + "\n" for event in events), encoding="utf-8")
            outputs = []
            for _ in range(2):
                stream = io.StringIO()
                with redirect_stdout(stream):
                    exit_code = main(["--scenario", str(SCENARIO), "--timeline", str(path), "--format", "jsonl"])
                self.assertEqual(2, exit_code)
                outputs.append(json.loads(stream.getvalue()))
            self.assertEqual(outputs[0], outputs[1])
            self.assertEqual("FAIL", outputs[0]["status"])


if __name__ == "__main__":
    unittest.main()
