"""Project catalog integrity tests."""

import copy
import json
import unittest

from fixture_utils import REPO_ROOT
from validate_catalog import EXPECTED_IDS, validate_catalog


CATALOG_PATH = (
    REPO_ROOT / "docs" / "verification" / "scenarios" / "catalog.json"
)


class CatalogIntegrityTests(unittest.TestCase):
    """Require a complete, unique, machine-valid project catalog."""

    def test_project_catalog_is_complete_and_valid(self) -> None:
        self.assertTrue(CATALOG_PATH.is_file(), "catalog.json must exist")
        document = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        summary = validate_catalog(document, CATALOG_PATH)
        self.assertEqual([], summary["errors"], summary["errors"])
        self.assertEqual("PASS", summary["status"])
        self.assertEqual(12, summary["counts"]["normal"])
        self.assertEqual(24, summary["counts"]["fault"])
        self.assertEqual(36, summary["counts"]["total"])
        self.assertEqual(
            EXPECTED_IDS,
            {entry["scenario_id"] for entry in document["scenarios"]},
        )

    def test_duplicate_catalog_id_is_rejected(self) -> None:
        document = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        duplicate = copy.deepcopy(document)
        duplicate["scenarios"].append(copy.deepcopy(duplicate["scenarios"][0]))
        summary = validate_catalog(duplicate, CATALOG_PATH)
        self.assertEqual("FAIL", summary["status"])
        self.assertIn("DUPLICATE_ID", {item["code"] for item in summary["errors"]})


if __name__ == "__main__":
    unittest.main()
