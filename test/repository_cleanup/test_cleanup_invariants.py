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
)
CURRENT_AUTHORITY_DOCUMENTS = (
    "README.md",
    "Scripts/README.md",
    "docs/handoff.md",
    "docs/governance/DOCUMENT_AUTHORITY.md",
)
HISTORICAL_ROOTS = (
    "docs/audits",
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

    def test_historical_roots_are_preserved_but_not_scanned_as_current(self) -> None:
        current_paths = {
            (REPO_ROOT / relative_path).resolve()
            for relative_path in CURRENT_AUTHORITY_DOCUMENTS
        }
        for relative_path in HISTORICAL_ROOTS:
            with self.subTest(path=relative_path):
                root = (REPO_ROOT / relative_path).resolve()
                self.assertTrue(root.is_dir(), "historical root is missing")
                self.assertTrue(
                    any(path.is_file() for path in root.rglob("*")),
                    "historical root contains no preserved files",
                )
                self.assertTrue(
                    all(root not in path.parents for path in current_paths),
                    "historical material entered the current-authority scan",
                )


if __name__ == "__main__":
    unittest.main()
