"""Static invariants for Repository Cleanup Wave 2."""

from pathlib import Path
import re
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
REMOVED_ACTIVE_PATHS = (
    "Scripts/build/m1_build.sh",
    "Scripts/installation/car_install.sh",
    "Scripts/simulation/uav_sim.sh",
    "Simulator",
    "SECURITY.md",
    ".gitmodules",
    "docs/evidence/sessions/20260728T164521+0800_onboard_h0",
    "docs/evidence/sessions/20260728T174752+0800_onboard_validation/raw",
    "docs/evidence/sessions/20260728T174752+0800_onboard_validation/artifacts/workspace.final.lock.repos",
    "docs/evidence/sessions/20260728T174752+0800_onboard_validation/artifacts/workspace.onboard_candidate.lock.repos",
)
CURRENT_AUTHORITY_DOCUMENTS = (
    "README.md",
    "Scripts/README.md",
    "docs/CONTROL_AUTHORITY_MATRIX.md",
    "docs/runbooks/SITL_ACCEPTANCE.md",
)
EVIDENCE_ROOTS = (
    "docs/evidence",
)
LEGACY_ENTRY_PATTERN = re.compile(
    r"(?:m1_build\.sh|car_install\.sh|uav_sim\.sh|(?:^|[`\s(])Simulator/)",
    re.MULTILINE,
)
PERSONAL_HOME_PATTERN = re.compile(r"/home/[A-Za-z0-9._-]+/")


class RepositoryCleanupInvariantTests(unittest.TestCase):
    """Keep removed entry points out of the current repository surface."""

    def test_removed_active_paths_stay_absent(self) -> None:
        for relative_path in REMOVED_ACTIVE_PATHS:
            with self.subTest(path=relative_path):
                self.assertFalse(
                    (REPO_ROOT / relative_path).exists(),
                    "removed active path was restored: {}".format(relative_path),
                )

    def test_current_authority_has_no_legacy_entry_or_personal_home(self) -> None:
        for relative_path in CURRENT_AUTHORITY_DOCUMENTS:
            with self.subTest(path=relative_path):
                path = REPO_ROOT / relative_path
                self.assertTrue(path.is_file(), "current authority is missing")
                text = path.read_text(encoding="utf-8")
                self.assertIsNone(
                    LEGACY_ENTRY_PATTERN.search(text),
                    "current authority references a removed legacy entry",
                )
                self.assertIsNone(
                    PERSONAL_HOME_PATTERN.search(text),
                    "current authority contains a personal absolute home path",
                )

    def test_evidence_roots_are_preserved_but_not_scanned_as_current(self) -> None:
        current_paths = {
            (REPO_ROOT / relative_path).resolve()
            for relative_path in CURRENT_AUTHORITY_DOCUMENTS
        }
        for relative_path in EVIDENCE_ROOTS:
            with self.subTest(path=relative_path):
                root = (REPO_ROOT / relative_path).resolve()
                self.assertTrue(root.is_dir(), "evidence root is missing")
                self.assertTrue(
                    any(path.is_file() for path in root.rglob("*")),
                    "evidence root contains no preserved files",
                )
                self.assertTrue(
                    all(root not in path.parents for path in current_paths),
                    "evidence material entered the current-authority scan",
                )

    def test_current_px4_hardware_identity_is_recorded(self) -> None:
        audit = (
            REPO_ROOT
            / "docs/evidence/sessions/"
            "20260728T213311+0800_px4_parameter_audit/PX4_PARAMETER_AUDIT.md"
        ).read_text(encoding="utf-8")
        for identity in (
            "PX4_FMU_V3",
            "STM32F42x rev. 5",
            "54f0455ffcd755534539a7cf33a09a20bf71d29d",
            "886acbbdb4f061e5c0ce1a76afbcfa7cb7df9849",
        ):
            with self.subTest(identity=identity):
                self.assertIn(identity, audit)

    def test_communication_checkout_is_not_stored_in_root_git(self) -> None:
        import subprocess

        result = subprocess.run(
            ["git", "ls-files", "--", "src/communication"],
            cwd=str(REPO_ROOT),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout.strip())


if __name__ == "__main__":
    unittest.main()
