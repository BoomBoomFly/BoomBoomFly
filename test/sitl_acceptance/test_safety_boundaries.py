"""Safety-boundary rejection tests for synthetic negative fixtures."""

import unittest

from fixture_utils import apply_scenario_mutation, load_cases, load_scenario
from validate_scenario import validate_scenario


class SafetyBoundaryTests(unittest.TestCase):
    """Prove every prohibited literal in safety fixtures causes rejection."""

    def test_every_safety_fixture_is_rejected_nonzero(self) -> None:
        cases = load_cases("safety_cases.json")
        self.assertGreater(len(cases), 0)
        for case in cases:
            with self.subTest(case_id=case["case_id"]):
                scenario = apply_scenario_mutation(load_scenario(), case)
                errors = validate_scenario(scenario)
                self.assertGreater(
                    len(errors),
                    0,
                    "prohibited synthetic fixture unexpectedly validated",
                )
                self.assertIn(case["expected_code"], {item["code"] for item in errors})

    def test_safety_fixture_values_are_explicitly_consumed(self) -> None:
        cases = load_cases("safety_cases.json")
        self.assertEqual(9, len(cases))
        self.assertEqual(9, len({case["case_id"] for case in cases}))
        self.assertTrue(all(case.get("value") for case in cases))
        self.assertTrue(all(case.get("expected_code") for case in cases))


if __name__ == "__main__":
    unittest.main()
