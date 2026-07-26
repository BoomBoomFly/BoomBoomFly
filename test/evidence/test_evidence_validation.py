#!/usr/bin/env python3
"""Positive and fail-closed tests for T08 evidence governance."""

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List


REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_VALIDATOR = REPO_ROOT / "Scripts/evidence/validate_evidence.py"
INDEX_VALIDATOR = REPO_ROOT / "Scripts/evidence/validate_index.py"
MANIFEST_VALIDATOR = REPO_ROOT / "Scripts/evidence/validate_manifest.py"
EVIDENCE_SCHEMA = REPO_ROOT / "docs/evidence/schemas/evidence.schema.json"
INDEX_SCHEMA = REPO_ROOT / "docs/evidence/schemas/evidence_index.schema.json"
RELEASE_SCHEMA = REPO_ROOT / "docs/evidence/schemas/release.schema.json"
ROLLBACK_SCHEMA = REPO_ROOT / "docs/evidence/schemas/rollback.schema.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class EvidenceValidationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="bbf_evidence_", dir="/tmp")
        self.root = Path(self.temp.name)
        self._git(["init"])
        self._git(["checkout", "-b", "main"])
        self._git(["remote", "add", "origin", "https://github.com/BoomBoomFly/BoomBoomFly.git"])
        marker = self.root / "tracked.txt"
        marker.write_text("fixture\n", encoding="utf-8")
        self._git(["add", "tracked.txt"])
        self._git(
            [
                "-c",
                "user.name=BoomBoomFly Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-m",
                "fixture",
            ]
        )
        self.head = self._git(["rev-parse", "HEAD"]).stdout.strip()
        (self.root / "artifacts").mkdir()
        self.stdout_path = self.root / "artifacts/stdout.log"
        self.stderr_path = self.root / "artifacts/stderr.log"
        self.result_path = self.root / "artifacts/result.txt"
        self.stdout_path.write_text("ok\n", encoding="utf-8")
        self.stderr_path.write_text("", encoding="utf-8")
        self.result_path.write_text("passed\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _git(self, args: List[str]) -> subprocess.CompletedProcess:
        result = subprocess.run(
            ["git", "-C", str(self.root)] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=False,
        )
        if result.returncode != 0:
            self.fail("git command failed: {0}\n{1}".format(args, result.stderr))
        return result

    def _run(self, args: List[str]) -> subprocess.CompletedProcess:
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [sys.executable] + [str(item) for item in args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            env=environment,
            check=False,
        )

    def _write_json(self, name: str, document: Any) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        return path

    def _artifact(self, path: Path) -> Dict[str, str]:
        return {"path": str(path.relative_to(self.root)), "sha256": sha256(path)}

    def _valid_evidence(self) -> Dict[str, Any]:
        return {
            "schema_version": "1.0",
            "evidence_id": "BBF-EVID-TEST-POSITIVE",
            "title": "Synthetic positive evidence",
            "evidence_type": "test",
            "status": "current",
            "created_at": "2026-07-26T09:00:00Z",
            "supersedes": None,
            "superseded_by": None,
            "repository": {
                "origin": "git@github.com:BoomBoomFly/BoomBoomFly.git",
                "root_branch": "main",
                "root_head": self.head,
            },
            "dependency_shas": [
                {"name": "example", "sha": "1" * 40}
            ],
            "dirty_receipt_ids": [],
            "environment_id": "BBF-ENV-TEST",
            "command": {"argv": ["python3", "-m", "unittest"], "cwd": "."},
            "start_time": "2026-07-26T09:00:00Z",
            "end_time": "2026-07-26T09:00:01Z",
            "exit_code": 0,
            "stdout_artifact": self._artifact(self.stdout_path),
            "stderr_artifact": self._artifact(self.stderr_path),
            "test_result": {"outcome": "passed", "summary": "Synthetic test passed."},
            "artifacts": [self._artifact(self.result_path)],
            "hardware_access": "none",
            "px4_parameter_access": "none",
            "firmware_access": "none",
            "limitations": ["Synthetic fixture only."],
            "reviewer": {
                "state": "approved",
                "identity": "fixture-reviewer",
                "reviewed_at": "2026-07-26T09:01:00Z",
            },
        }

    def _run_evidence(self, document: Dict[str, Any]) -> subprocess.CompletedProcess:
        path = self._write_json("metadata.json", document)
        return self._run(
            [
                EVIDENCE_VALIDATOR,
                "--repo-root",
                self.root,
                "--schema",
                EVIDENCE_SCHEMA,
                path,
            ]
        )

    def _base_index_entry(self, evidence_id: str, path: Path) -> Dict[str, Any]:
        return {
            "evidence_id": evidence_id,
            "title": evidence_id,
            "evidence_type": "validation_record",
            "status": "historical",
            "path": str(path.relative_to(self.root)),
            "sha256": sha256(path),
            "metadata_path": None,
            "known_historical": True,
            "supersedes": None,
            "superseded_by": None,
            "limitations": ["Synthetic legacy fixture."],
        }

    def _run_index(self, entries: List[Dict[str, Any]], root_head: str = None) -> subprocess.CompletedProcess:
        index = {
            "schema_version": "1.0",
            "generated_at": "2026-07-26T09:00:00Z",
            "repository": {
                "origin": "https://github.com/BoomBoomFly/BoomBoomFly.git",
                "root_branch": "main",
                "root_head": root_head or self.head,
            },
            "entries": entries,
        }
        path = self._write_json("index.yaml", index)
        return self._run(
            [
                INDEX_VALIDATOR,
                "--repo-root",
                self.root,
                "--schema",
                INDEX_SCHEMA,
                "--evidence-schema",
                EVIDENCE_SCHEMA,
                "--index",
                path,
            ]
        )

    def test_valid_evidence_passes(self) -> None:
        result = self._run_evidence(self._valid_evidence())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_required_evidence_field_fails(self) -> None:
        document = self._valid_evidence()
        del document["environment_id"]
        result = self._run_evidence(document)
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)

    def test_wrong_artifact_hash_fails(self) -> None:
        document = self._valid_evidence()
        document["artifacts"][0]["sha256"] = "0" * 64
        result = self._run_evidence(document)
        self.assertEqual(result.returncode, 4, result.stdout + result.stderr)

    def test_current_evidence_with_old_head_fails(self) -> None:
        document = self._valid_evidence()
        document["repository"]["root_head"] = "0" * 40
        result = self._run_evidence(document)
        self.assertEqual(result.returncode, 5, result.stdout + result.stderr)

    def test_skipped_hash_check_is_not_success(self) -> None:
        path = self._write_json("metadata.json", self._valid_evidence())
        result = self._run(
            [
                EVIDENCE_VALIDATOR,
                "--repo-root",
                self.root,
                "--schema",
                EVIDENCE_SCHEMA,
                "--no-artifact-hash-check",
                path,
            ]
        )
        self.assertEqual(result.returncode, 5, result.stdout + result.stderr)

    def test_repository_legacy_index_passes_without_rewriting_evidence(self) -> None:
        result = self._run(
            [
                INDEX_VALIDATOR,
                "--repo-root",
                REPO_ROOT,
                "--index",
                REPO_ROOT / "docs/evidence/index.yaml",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_dangling_supersession_fails(self) -> None:
        first = self._base_index_entry("BBF-EVID-TEST-FIRST", self.result_path)
        first["supersedes"] = "BBF-EVID-TEST-MISSING"
        result = self._run_index([first])
        self.assertEqual(result.returncode, 5, result.stdout + result.stderr)

    def test_nonreciprocal_supersession_fails(self) -> None:
        second_path = self.root / "artifacts/second.txt"
        second_path.write_text("second\n", encoding="utf-8")
        first = self._base_index_entry("BBF-EVID-TEST-FIRST", self.result_path)
        second = self._base_index_entry("BBF-EVID-TEST-SECOND", second_path)
        second["supersedes"] = first["evidence_id"]
        result = self._run_index([first, second])
        self.assertEqual(result.returncode, 5, result.stdout + result.stderr)

    def test_supersession_cycle_fails(self) -> None:
        second_path = self.root / "artifacts/second.txt"
        second_path.write_text("second\n", encoding="utf-8")
        first = self._base_index_entry("BBF-EVID-TEST-FIRST", self.result_path)
        second = self._base_index_entry("BBF-EVID-TEST-SECOND", second_path)
        first["supersedes"] = second["evidence_id"]
        first["superseded_by"] = second["evidence_id"]
        second["supersedes"] = first["evidence_id"]
        second["superseded_by"] = first["evidence_id"]
        result = self._run_index([first, second])
        self.assertEqual(result.returncode, 5, result.stdout + result.stderr)

    def test_known_historical_parameter_cannot_be_current(self) -> None:
        entry = self._base_index_entry("BBF-EVID-TEST-PARAMS", self.result_path)
        entry["evidence_type"] = "parameter_snapshot"
        entry["status"] = "current"
        result = self._run_index([entry])
        self.assertEqual(result.returncode, 5, result.stdout + result.stderr)

    def test_rollback_template_is_structural_not_verified(self) -> None:
        result = self._run(
            [
                MANIFEST_VALIDATOR,
                "--kind",
                "rollback",
                "--repo-root",
                REPO_ROOT,
                "--schema",
                ROLLBACK_SCHEMA,
                REPO_ROOT / "docs/evidence/ROLLBACK_TEMPLATE.yaml",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rollback_missing_key_fails(self) -> None:
        import yaml

        template = yaml.safe_load(
            (REPO_ROOT / "docs/evidence/ROLLBACK_TEMPLATE.yaml").read_text(encoding="utf-8")
        )
        del template["stop_condition"]
        path = self._write_json("rollback.yaml", template)
        result = self._run(
            [
                MANIFEST_VALIDATOR,
                "--kind",
                "rollback",
                "--repo-root",
                self.root,
                "--schema",
                ROLLBACK_SCHEMA,
                path,
            ]
        )
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)

    def test_paper_rollback_cannot_claim_verified(self) -> None:
        import yaml

        template = yaml.safe_load(
            (REPO_ROOT / "docs/evidence/ROLLBACK_TEMPLATE.yaml").read_text(encoding="utf-8")
        )
        template["manifest_state"] = "verified"
        template["result"] = "passed"
        template["pre_state_hash"] = sha256(self.stdout_path)
        template["pre_state_artifact"] = self._artifact(self.stdout_path)
        template["target_state_hash"] = sha256(self.result_path)
        template["target_state_artifact"] = self._artifact(self.result_path)
        template["exact_artifact"] = self._artifact(self.stderr_path)
        template["exact_command"] = {"argv": ["true"], "cwd": "."}
        template["stop_condition"] = "Stop if read-only verification fails."
        template["verification"] = [
            {
                "command": {"argv": ["true"], "cwd": "."},
                "expected": "exit code zero",
            }
        ]
        template["operator"] = {
            "identity": "operator",
            "recorded_at": "2026-07-26T09:00:00Z",
        }
        template["observer"] = {
            "identity": "observer",
            "recorded_at": "2026-07-26T09:00:00Z",
        }
        path = self._write_json("rollback.yaml", template)
        result = self._run(
            [
                MANIFEST_VALIDATOR,
                "--kind",
                "rollback",
                "--repo-root",
                self.root,
                "--schema",
                ROLLBACK_SCHEMA,
                path,
            ]
        )
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)

    def test_release_missing_rollback_manifest_fails(self) -> None:
        import yaml

        template = yaml.safe_load(
            (REPO_ROOT / "docs/evidence/RELEASE_TEMPLATE.yaml").read_text(encoding="utf-8")
        )
        del template["rollback_manifest"]
        path = self._write_json("release.yaml", template)
        result = self._run(
            [
                MANIFEST_VALIDATOR,
                "--kind",
                "release",
                "--repo-root",
                self.root,
                "--schema",
                RELEASE_SCHEMA,
                path,
            ]
        )
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
