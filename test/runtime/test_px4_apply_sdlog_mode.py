import copy
import importlib.util
import json
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "Scripts/runtime/px4_apply_sdlog_mode.py"


def load_transaction():
    spec = importlib.util.spec_from_file_location(
        "px4_apply_sdlog_mode", SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def baseline_document(transaction, direction):
    change = transaction.MODE_CHANGES[direction]
    parameters = {
        "P{:03d}".format(index): {
            "index": index,
            "type": transaction.snapshot.MAV_PARAM_TYPE_INT32,
            "value": index,
        }
        for index in range(971)
    }
    parameters["SDLOG_MODE"] = {
        "index": 971,
        "type": change["type"],
        "value": change["before"],
    }
    parameters["SDLOG_BOOT_BAT"] = {
        "index": 972,
        "type": transaction.snapshot.MAV_PARAM_TYPE_INT32,
        "value": 0,
    }
    parameters["SDLOG_PROFILE"] = {
        "index": 973,
        "type": transaction.snapshot.MAV_PARAM_TYPE_INT32,
        "value": 1,
    }
    return {
        "capture": {
            "complete": True,
            "expected_count": 974,
        },
        "parameters": parameters,
    }


class SdlogModeTransactionTest(unittest.TestCase):
    def setUp(self):
        self.transaction = load_transaction()

    def test_directions_are_exactly_zero_to_two_and_two_to_zero(self):
        self.assertEqual(
            self.transaction.MODE_CHANGES,
            {
                "enable": {
                    "name": "SDLOG_MODE",
                    "before": 0,
                    "after": 2,
                    "type": self.transaction.snapshot.MAV_PARAM_TYPE_INT32,
                },
                "rollback": {
                    "name": "SDLOG_MODE",
                    "before": 2,
                    "after": 0,
                    "type": self.transaction.snapshot.MAV_PARAM_TYPE_INT32,
                },
            },
        )

    def test_baseline_requires_full_snapshot_and_companion_values(self):
        change = self.transaction.MODE_CHANGES["enable"]
        baseline = baseline_document(self.transaction, "enable")
        self.transaction.validate_baseline(baseline, change)

        baseline["parameters"]["SDLOG_BOOT_BAT"]["value"] = 1
        with self.assertRaisesRegex(
            self.transaction.TransactionError, "SDLOG_BOOT_BAT"
        ):
            self.transaction.validate_baseline(baseline, change)

        baseline = baseline_document(self.transaction, "enable")
        baseline["capture"]["complete"] = False
        with self.assertRaisesRegex(
            self.transaction.TransactionError, "incomplete"
        ):
            self.transaction.validate_baseline(baseline, change)

    def test_post_diff_allows_only_sdlog_mode_and_hash(self):
        change = self.transaction.MODE_CHANGES["enable"]
        baseline = baseline_document(self.transaction, "enable")
        post = copy.deepcopy(baseline)
        post["parameters"]["SDLOG_MODE"]["value"] = 2
        differences = self.transaction.validate_post_snapshot(
            baseline, post, change
        )
        self.assertEqual(
            [difference["name"] for difference in differences],
            ["SDLOG_MODE"],
        )

    def test_unexpected_or_missing_diff_fails_closed(self):
        change = self.transaction.MODE_CHANGES["enable"]
        baseline = baseline_document(self.transaction, "enable")
        post = copy.deepcopy(baseline)
        post["parameters"]["SDLOG_MODE"]["value"] = 2
        post["parameters"]["P001"]["value"] = 999
        with self.assertRaisesRegex(
            self.transaction.TransactionError, "unexpected parameters"
        ):
            self.transaction.validate_post_snapshot(baseline, post, change)

        with self.assertRaisesRegex(
            self.transaction.TransactionError, "missing from diff"
        ):
            self.transaction.validate_post_snapshot(
                baseline, copy.deepcopy(baseline), change
            )

    def test_baseline_hash_mismatch_fails_before_connection(self):
        baseline = baseline_document(self.transaction, "enable")
        with tempfile.TemporaryDirectory(prefix="px4_sdlog_transaction.") as temp:
            path = pathlib.Path(temp) / "baseline.json"
            path.write_text(json.dumps(baseline), encoding="utf-8")
            with self.assertRaisesRegex(
                self.transaction.TransactionError, "SHA-256 mismatch"
            ):
                self.transaction.load_baseline(
                    path,
                    "0" * 64,
                    self.transaction.MODE_CHANGES["enable"],
                )

    def test_explicit_execute_flag_is_required(self):
        required = [
            "--direction",
            "enable",
            "--baseline",
            "baseline.json",
            "--baseline-sha256",
            "0" * 64,
            "--post-output",
            "post.json",
            "--transaction-output",
            "transaction.json",
        ]
        with self.assertRaises(SystemExit):
            self.transaction.parse_args(required)


if __name__ == "__main__":
    unittest.main()
