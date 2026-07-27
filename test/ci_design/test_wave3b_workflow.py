"""Wave 3B executable-workflow static and fail-closed tests."""

import json
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "Scripts" / "ci"))

from run_offline_gate import sandbox_command, unresolved_locks  # noqa: E402
from validate_workflow import job_ids, validate  # noqa: E402


CONTRACT = HERE / "workflow_contract.json"
WORKFLOW = ROOT / ".github" / "workflows" / "wave3b-offline-gates.yml"


def load(path: Path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


class Wave3BWorkflowTest(unittest.TestCase):
    def test_workflow_matches_contract(self) -> None:
        self.assertEqual(
            validate(WORKFLOW.read_text(encoding="utf-8"), load(CONTRACT)), [])

    def test_stable_job_ids_are_exact(self) -> None:
        self.assertEqual(
            job_ids(WORKFLOW.read_text(encoding="utf-8")),
            set(load(CONTRACT)["expected_job_ids"]))

    def test_dependency_lock_remains_explicitly_unresolved(self) -> None:
        self.assertEqual(len(unresolved_locks(load(CONTRACT))), 8)

    def test_sandbox_has_no_network_or_device_binding(self) -> None:
        command = sandbox_command(Path("/workspace"), "true")
        rendered = " ".join(command)
        self.assertIn("--unshare-all", command)
        self.assertNotIn("--share-net", command)
        self.assertNotIn("/dev", rendered)
        self.assertNotIn("--dev", rendered)

    def test_no_package_name_executable_probe(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        runner = (ROOT / "Scripts" / "ci" / "run_offline_gate.py").read_text(
            encoding="utf-8")
        self.assertIn("command -v bwrap", workflow)
        self.assertNotIn("command -v bubblewrap", workflow + runner)


if __name__ == "__main__":
    unittest.main()
