import copy
import importlib.util
import json
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "Scripts/runtime/px4_apply_approved_circuit_breakers.py"


def load_transaction():
    spec = importlib.util.spec_from_file_location(
        "px4_apply_approved_circuit_breakers", SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def baseline_document(transaction):
    parameters = {
        "P{:03d}".format(index): {
            "index": index,
            "type": transaction.snapshot.MAV_PARAM_TYPE_INT32,
            "value": index,
        }
        for index in range(970)
    }
    for offset, change in enumerate(transaction.APPROVED_CHANGES, start=970):
        parameters[change["name"]] = {
            "index": offset,
            "type": change["type"],
            "value": change["before"],
        }
    parameters["_HASH_CHECK"] = {
        "index": 65535,
        "type": transaction.snapshot.MAV_PARAM_TYPE_UINT32,
        "value": 123456,
    }
    return {
        "capture": {
            "complete": True,
            "expected_count": 974,
        },
        "parameters": parameters,
    }


class ApprovedCircuitBreakerTransactionTest(unittest.TestCase):
    def setUp(self):
        self.transaction = load_transaction()

    def test_group_is_exact_and_excludes_flight_termination(self):
        self.assertEqual(
            [change["name"] for change in self.transaction.APPROVED_CHANGES],
            ["CBRK_SUPPLY_CHK", "CBRK_IO_SAFETY", "CBRK_USB_CHK"],
        )
        self.assertTrue(
            all(change["after"] == 0 for change in self.transaction.APPROVED_CHANGES)
        )
        self.assertNotIn(
            "CBRK_FLIGHTTERM",
            {change["name"] for change in self.transaction.APPROVED_CHANGES},
        )

    def test_baseline_requires_974_unique_parameters_and_old_values(self):
        baseline = baseline_document(self.transaction)
        self.transaction.validate_baseline(baseline)
        baseline["parameters"]["CBRK_SUPPLY_CHK"]["value"] = 0
        with self.assertRaisesRegex(
            self.transaction.TransactionError, "baseline value mismatch"
        ):
            self.transaction.validate_baseline(baseline)

    def test_post_diff_allows_only_group_and_hash(self):
        baseline = baseline_document(self.transaction)
        post = copy.deepcopy(baseline)
        for change in self.transaction.APPROVED_CHANGES:
            post["parameters"][change["name"]]["value"] = change["after"]
        post["parameters"]["_HASH_CHECK"]["value"] = 654321
        differences = self.transaction.validate_post_snapshot(baseline, post)
        self.assertEqual(
            {difference["name"] for difference in differences},
            {
                "CBRK_SUPPLY_CHK",
                "CBRK_IO_SAFETY",
                "CBRK_USB_CHK",
                "_HASH_CHECK",
            },
        )

    def test_unexpected_or_missing_diff_fails_closed(self):
        baseline = baseline_document(self.transaction)
        post = copy.deepcopy(baseline)
        for change in self.transaction.APPROVED_CHANGES:
            post["parameters"][change["name"]]["value"] = change["after"]
        post["parameters"]["P001"]["value"] = 999
        with self.assertRaisesRegex(
            self.transaction.TransactionError, "unexpected parameters"
        ):
            self.transaction.validate_post_snapshot(baseline, post)

        post = copy.deepcopy(baseline)
        post["parameters"]["CBRK_SUPPLY_CHK"]["value"] = 0
        with self.assertRaisesRegex(
            self.transaction.TransactionError, "missing from diff"
        ):
            self.transaction.validate_post_snapshot(baseline, post)

    def test_baseline_hash_mismatch_fails_before_connection(self):
        baseline = baseline_document(self.transaction)
        with tempfile.TemporaryDirectory(prefix="px4_param_transaction.") as temp:
            path = pathlib.Path(temp) / "baseline.json"
            path.write_text(json.dumps(baseline), encoding="utf-8")
            with self.assertRaisesRegex(
                self.transaction.TransactionError, "SHA-256 mismatch"
            ):
                self.transaction.load_baseline(path, "0" * 64)


if __name__ == "__main__":
    unittest.main()
