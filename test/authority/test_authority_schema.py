#!/usr/bin/env python3
"""Draft 2020-12 structure tests for the authority envelope."""

import copy
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "docs/authority/schemas/authority-envelope.schema.json"
VALID_PATH = REPO_ROOT / "test/authority/fixtures/valid/envelope.json"
INVALID_PATH = REPO_ROOT / "test/authority/fixtures/invalid/malformed_envelope.json"


class AuthorityEnvelopeSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            import jsonschema
        except ImportError as error:
            raise unittest.SkipTest(
                "jsonschema Draft 2020-12 support unavailable; schema was not downgraded: %s" % error
            )
        validator_class = getattr(jsonschema, "Draft202012Validator", None)
        if validator_class is None:
            raise unittest.SkipTest(
                "installed jsonschema lacks Draft202012Validator; schema was not downgraded"
            )
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.valid = json.loads(VALID_PATH.read_text(encoding="utf-8"))
        validator_class.check_schema(cls.schema)
        cls.validator = validator_class(cls.schema)

    def assert_invalid(self, document) -> None:
        self.assertTrue(list(self.validator.iter_errors(document)))

    def test_schema_declares_draft_2020_12(self) -> None:
        self.assertEqual(
            self.schema["$schema"],
            "https://json-schema.org/draft/2020-12/schema",
        )

    def test_valid_fixture_passes(self) -> None:
        self.validator.validate(self.valid)

    def test_malformed_fixture_fails(self) -> None:
        self.assert_invalid(json.loads(INVALID_PATH.read_text(encoding="utf-8")))

    def test_missing_owner_identity_fails(self) -> None:
        document = copy.deepcopy(self.valid)
        del document["owner"]["instance_id"]
        self.assert_invalid(document)

    def test_missing_lease_lifecycle_fails(self) -> None:
        document = copy.deepcopy(self.valid)
        del document["lease"]["lifecycle"]
        self.assert_invalid(document)

    def test_missing_epoch_fails(self) -> None:
        document = copy.deepcopy(self.valid)
        del document["graph_epoch"]
        self.assert_invalid(document)

    def test_missing_command_correlation_fails(self) -> None:
        document = copy.deepcopy(self.valid)
        del document["command"]["correlation_id"]
        self.assert_invalid(document)

    def test_unknown_field_fails_closed(self) -> None:
        document = copy.deepcopy(self.valid)
        document["permit_publish"] = True
        self.assert_invalid(document)

    def test_moving_or_untyped_epoch_fails(self) -> None:
        document = copy.deepcopy(self.valid)
        document["source_epoch"] = "latest"
        self.assert_invalid(document)


if __name__ == "__main__":
    unittest.main()
