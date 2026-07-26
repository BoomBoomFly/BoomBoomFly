#!/usr/bin/env python3
"""Offline tests for the preserved-checkout receipt verifier."""

import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "Scripts/installation/verify_workspace_receipts.py"
SPEC = importlib.util.spec_from_file_location("verify_workspace_receipts", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load receipt verifier")
RECEIPTS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RECEIPTS)


def command(arguments, cwd):
    completed = subprocess.run(
        arguments,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "{} failed: {}".format(
                " ".join(arguments), completed.stderr.decode("utf-8", "replace")
            )
        )
    return completed.stdout


class WorkspaceReceiptTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(
            prefix="boomboomfly_receipt_test_", dir="/tmp"
        )
        self.root = Path(self.temporary.name) / "root"
        self.root.mkdir()
        command(["git", "init", "-q"], self.root)
        command(["git", "config", "user.name", "Receipt Test"], self.root)
        command(["git", "config", "user.email", "receipt@example.invalid"], self.root)
        (self.root / ".gitignore").write_text("src/\n", encoding="utf-8")
        schema_dir = self.root / "docs/evidence/schemas"
        schema_dir.mkdir(parents=True)
        shutil.copy2(
            PROJECT_ROOT / "docs/evidence/schemas/workspace_receipt.schema.json",
            schema_dir / "workspace_receipt.schema.json",
        )

        self.repo = self.root / "src/example"
        self.repo.mkdir(parents=True)
        command(["git", "init", "-q"], self.repo)
        command(["git", "config", "user.name", "Receipt Test"], self.repo)
        command(["git", "config", "user.email", "receipt@example.invalid"], self.repo)
        command(
            [
                "git",
                "remote",
                "add",
                "origin",
                "https://github.com/example/example.git",
            ],
            self.repo,
        )
        (self.repo / "ordinary.txt").write_text("base\n", encoding="utf-8")
        launch_dir = self.repo / "launch"
        launch_dir.mkdir()
        (launch_dir / "profile.launch.py").write_text("value = 1\n", encoding="utf-8")
        command(["git", "add", "."], self.repo)
        command(["git", "commit", "-q", "-m", "base"], self.repo)
        self.head = command(["git", "rev-parse", "HEAD"], self.repo).decode().strip()

        lock = """repositories:
  src/example:
    type: git
    url: https://github.com/example/example.git
    version: {}
""".format(
            self.head
        )
        (self.root / "workspace.lock.repos").write_text(lock, encoding="utf-8")
        command(["git", "add", "."], self.root)
        command(["git", "commit", "-q", "-m", "root"], self.root)

        os.chmod(str(self.repo / "ordinary.txt"), 0o755)
        (launch_dir / "profile.launch.py").write_text("value = 2\n", encoding="utf-8")
        (launch_dir / "extra.launch.py").write_text("extra = True\n", encoding="utf-8")
        self.receipt_path, self.patch_path = RECEIPTS.capture_receipt(
            self.root,
            self.root,
            "src/example",
            "example",
            "2026-07-26T00:00:00+00:00",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def receipt(self):
        return json.loads(self.receipt_path.read_text(encoding="utf-8"))

    def write_variant(self, name, receipt):
        path = self.receipt_path.parent / name
        path.write_text(json.dumps(receipt), encoding="utf-8")
        return path

    def test_valid_observation_is_unapproved_not_pass(self):
        errors, warnings, receipt = RECEIPTS.validate_receipt(
            self.root, self.receipt_path
        )
        self.assertEqual([], errors)
        self.assertIsNotNone(receipt)
        self.assertEqual(1, len(warnings))
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = RECEIPTS.main(
                [
                    "--repository-root",
                    str(self.root),
                    "--receipt",
                    str(self.receipt_path),
                ]
            )
        self.assertEqual(RECEIPTS.EXIT_UNAPPROVED, exit_code)
        self.assertIn('"result": "UNAPPROVED"', stdout.getvalue())
        self.assertNotIn('"result": "PASS"', stdout.getvalue())

    def test_wrong_origin_head_hash_and_missing_field_fail(self):
        mutations = []
        wrong_origin = copy.deepcopy(self.receipt())
        wrong_origin["repository"]["origin"] = "https://github.com/example/wrong.git"
        mutations.append(("wrong-origin.json", wrong_origin))
        wrong_head = copy.deepcopy(self.receipt())
        wrong_head["repository"]["head"] = "0" * 40
        mutations.append(("wrong-head.json", wrong_head))
        wrong_hash = copy.deepcopy(self.receipt())
        wrong_hash["patch"]["sha256"] = "0" * 64
        mutations.append(("wrong-hash.json", wrong_hash))
        missing = copy.deepcopy(self.receipt())
        del missing["business_purpose"]
        mutations.append(("missing.json", missing))
        for name, receipt in mutations:
            with self.subTest(name=name):
                path = self.write_variant(name, receipt)
                errors, _, _ = RECEIPTS.validate_receipt(self.root, path)
                self.assertTrue(errors)

    def test_checkout_content_tamper_fails(self):
        (self.repo / "ordinary.txt").write_text("tampered\n", encoding="utf-8")
        errors, _, _ = RECEIPTS.validate_receipt(self.root, self.receipt_path)
        self.assertTrue(any("hash mismatch" in error for error in errors))

    def test_patch_paths_are_relative_and_replay_round_trips(self):
        encoded = self.patch_path.read_bytes()
        self.assertEqual(
            self.receipt()["patch"]["artifact_sha256"],
            RECEIPTS.sha256_bytes(encoded),
        )
        _, patch = RECEIPTS.decode_patch_artifact(self.root, self.receipt())
        self.assertTrue(RECEIPTS.patch_paths_are_safe(patch))
        self.assertNotIn(b"/home/", patch)
        errors = RECEIPTS.replay_receipt(
            self.root, self.receipt(), Path(self.temporary.name)
        )
        self.assertEqual([], errors)

    def test_classification_separates_mode_config_and_untracked(self):
        receipt = self.receipt()
        counts = receipt["classifications"]
        self.assertEqual(1, counts["mode_only"])
        self.assertEqual(2, counts["configuration_modification"])
        self.assertEqual(1, counts["untracked"])
        self.assertEqual(0, receipt["staged_diff"]["changed_file_count"])

    def test_reviewer_inventory_tampering_fails(self):
        mutations = []
        tracked_entry = copy.deepcopy(self.receipt())
        tracked_entry["tracked_diff"]["entries"][0]["categories"] = [
            "source_modification"
        ]
        mutations.append(
            ("tracked-entry.json", tracked_entry, "tracked_diff entries")
        )

        tracked_count = copy.deepcopy(self.receipt())
        tracked_count["tracked_diff"]["changed_file_count"] += 1
        mutations.append(("tracked-count.json", tracked_count, "tracked_diff count"))

        staged = copy.deepcopy(self.receipt())
        staged["staged_diff"]["entries"] = [
            copy.deepcopy(staged["tracked_diff"]["entries"][0])
        ]
        staged["staged_diff"]["changed_file_count"] = 1
        mutations.append(("staged-entry.json", staged, "staged_diff entries"))

        modes = copy.deepcopy(self.receipt())
        modes["file_mode_differences"]["entries"][0]["new_mode"] = "100644"
        mutations.append(("mode-entry.json", modes, "file_mode_differences entries"))

        mode_count = copy.deepcopy(self.receipt())
        mode_count["file_mode_differences"]["count"] += 1
        mutations.append(("mode-count.json", mode_count, "count does not match"))

        classifications = copy.deepcopy(self.receipt())
        classifications["classifications"]["mode_only"] = 999
        mutations.append(
            ("classifications.json", classifications, "classifications mismatch")
        )

        for name, receipt, expected in mutations:
            with self.subTest(name=name):
                path = self.write_variant(name, receipt)
                errors, _, _ = RECEIPTS.validate_receipt(self.root, path)
                self.assertTrue(any(expected in error for error in errors), errors)

    def test_approved_receipt_requires_verified_claims_and_identity(self):
        approved = copy.deepcopy(self.receipt())
        approved["baseline_status"] = "approved"
        approved["maintainer_confirmation"].update({
            "status": "approved",
            "reviewer": "Maintainer Name",
            "confirmed_at": "2026-07-26T01:00:00+00:00",
        })
        path = self.write_variant("approved-missing-claims.json", approved)
        errors, _, _ = RECEIPTS.validate_receipt(self.root, path)
        self.assertTrue(any("applicable_platform" in error for error in errors))
        self.assertTrue(any("business_purpose" in error for error in errors))

        approved["applicable_platform"].update({
            "status": "verified",
            "value": "Ubuntu 20.04 / ROS 2 Foxy / aarch64",
        })
        approved["business_purpose"].update({
            "status": "approved",
            "value": "Maintainer-approved compatibility delta",
        })
        path = self.write_variant("approved-complete.json", approved)
        schema = json.loads(
            (
                PROJECT_ROOT
                / "docs/evidence/schemas/workspace_receipt.schema.json"
            ).read_text(encoding="utf-8")
        )
        errors, warnings, _ = RECEIPTS.validate_receipt(
            self.root, path, schema_document=schema
        )
        self.assertEqual([], errors)
        self.assertEqual([], warnings)

        missing_identity = copy.deepcopy(approved)
        missing_identity["maintainer_confirmation"]["reviewer"] = None
        missing_identity["maintainer_confirmation"]["confirmed_at"] = None
        path = self.write_variant("approved-missing-identity.json", missing_identity)
        errors, _, _ = RECEIPTS.validate_receipt(self.root, path)
        self.assertTrue(any("reviewer and confirmed_at" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
