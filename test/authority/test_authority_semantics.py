#!/usr/bin/env python3
"""Table-driven fail-closed authority and synthetic consumer tests."""

import copy
import importlib.util
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = REPO_ROOT / "tools/authority/validate_envelope.py"
FIXTURE_ROOT = REPO_ROOT / "test/authority/fixtures"

SPEC = importlib.util.spec_from_file_location("authority_validate_envelope", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
AUTHORITY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUTHORITY)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def set_dotted(document, path, value) -> None:
    target = document
    parts = path.split(".")
    for part in parts[:-1]:
        target = target[part]
    target[parts[-1]] = value


class AuthoritySemanticTest(unittest.TestCase):
    def setUp(self) -> None:
        self.envelope = load_json(FIXTURE_ROOT / "valid/envelope.json")
        self.context_data = load_json(FIXTURE_ROOT / "valid/context.json")

    def context(self):
        return AUTHORITY.AuthorityContext.from_dict(copy.deepcopy(self.context_data))

    def test_valid_envelope_is_accepted_by_c1(self) -> None:
        decision = AUTHORITY.validate_semantics(copy.deepcopy(self.envelope), self.context())
        self.assertTrue(decision.accepted)
        self.assertEqual(decision.event_code, "AUTH_ACCEPTED")
        self.assertEqual(decision.latch_state, "CLEAR")

    def test_all_negative_cases_reject_and_publish_zero(self) -> None:
        cases = load_json(FIXTURE_ROOT / "invalid/semantic_cases.json")
        self.assertGreaterEqual(len(cases), 16)
        for case in cases:
            with self.subTest(case=case["id"]):
                envelope = copy.deepcopy(self.envelope)
                for path, value in case["envelope"].items():
                    set_dotted(envelope, path, value)
                context_data = copy.deepcopy(self.context_data)
                context_data.update(case["context"])
                consumer = AUTHORITY.SyntheticAuthorityConsumer(
                    AUTHORITY.AuthorityContext.from_dict(context_data)
                )
                decision = consumer.consume(envelope, downstream_ready=True)
                self.assertFalse(decision.accepted)
                self.assertEqual(decision.event_code, case["expected_code"])
                self.assertEqual(decision.latch_state, case["expected_latch"])
                self.assertEqual(consumer.synthetic_px4_publish_count, 0)

    def test_rejection_does_not_advance_replay_state(self) -> None:
        context = self.context()
        envelope = copy.deepcopy(self.envelope)
        envelope["owner"]["principal_id"] = "mission.intruder"
        before_sequence = context.last_sequence
        before_correlations = set(context.seen_correlations)
        decision = AUTHORITY.validate_semantics(envelope, context)
        self.assertFalse(decision.accepted)
        self.assertEqual(context.last_sequence, before_sequence)
        self.assertEqual(context.seen_correlations, before_correlations)

    def test_c1_accept_is_insufficient_without_b1_downstream_gates(self) -> None:
        consumer = AUTHORITY.SyntheticAuthorityConsumer(self.context())
        before_sequence = consumer.context.last_sequence
        before_correlations = set(consumer.context.seen_correlations)
        decision = consumer.consume(copy.deepcopy(self.envelope), downstream_ready=False)
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.event_code, "AUTH_DOWNSTREAM_NOT_READY")
        self.assertEqual(consumer.synthetic_px4_publish_count, 0)
        self.assertEqual(consumer.context.last_sequence, before_sequence)
        self.assertEqual(consumer.context.seen_correlations, before_correlations)

    def test_accept_and_all_downstream_gates_may_increment_synthetic_count(self) -> None:
        consumer = AUTHORITY.SyntheticAuthorityConsumer(self.context())
        decision = consumer.consume(copy.deepcopy(self.envelope), downstream_ready=True)
        self.assertTrue(decision.accepted)
        self.assertEqual(consumer.synthetic_px4_publish_count, 1)
        self.assertEqual(decision.consumer_state, "ACTIVE")

    def test_latch_persists_after_cardinality_recovers(self) -> None:
        context = self.context()
        context.writer_count = 2
        first = AUTHORITY.validate_semantics(copy.deepcopy(self.envelope), context)
        self.assertEqual(first.event_code, "AUTH_DUPLICATE_WRITER")
        context.writer_count = 1
        second = AUTHORITY.validate_semantics(copy.deepcopy(self.envelope), context)
        self.assertEqual(second.event_code, "AUTH_FAULT_LATCHED")
        self.assertEqual(second.consumer_state, "FAULT_LATCHED")

    def test_automatic_recovery_is_rejected(self) -> None:
        context = self.context()
        context.latch_state = "FAULT_LATCHED"
        context.consumer_state = "FAULT_LATCHED"
        decision = AUTHORITY.manual_recover(context, human_authorized=False)
        self.assertEqual(decision.event_code, "AUTH_MANUAL_RECOVERY_REQUIRED")
        self.assertEqual(context.consumer_state, "FAULT_LATCHED")
        self.assertIsNotNone(context.current_lease_id)

    def test_human_recovery_returns_ready_and_revokes_old_lease(self) -> None:
        context = self.context()
        context.latch_state = "FAULT_LATCHED"
        context.consumer_state = "FAULT_LATCHED"
        decision = AUTHORITY.manual_recover(context, human_authorized=True)
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.event_code, "AUTH_NO_ACTIVE_LEASE")
        self.assertEqual(context.latch_state, "CLEAR")
        self.assertEqual(context.consumer_state, "READY")
        self.assertIsNone(context.current_lease_id)
        self.assertNotEqual(context.consumer_state, "ACTIVE")

    def test_malformed_direct_call_fails_closed(self) -> None:
        malformed = copy.deepcopy(self.envelope)
        del malformed["source_epoch"]
        decision = AUTHORITY.validate_semantics(malformed, self.context())
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.event_code, "AUTH_SCHEMA_INVALID")

    def test_stable_event_code_set_is_frozen(self) -> None:
        expected = {
            "AUTH_ACCEPTED",
            "AUTH_SCHEMA_INVALID",
            "AUTH_FAULT_LATCHED",
            "AUTH_DUPLICATE_WRITER",
            "AUTH_DUPLICATE_OWNER",
            "AUTH_GRAPH_EPOCH_CHANGED",
            "AUTH_SOURCE_EPOCH_CHANGED",
            "AUTH_OWNER_NOT_CURRENT",
            "AUTH_OWNER_INSTANCE_NOT_CURRENT",
            "AUTH_NO_ACTIVE_LEASE",
            "AUTH_LEASE_NOT_CURRENT",
            "AUTH_LEASE_NOT_ACTIVE",
            "AUTH_LEASE_EXPIRED",
            "AUTH_SEQUENCE_DUPLICATE",
            "AUTH_SEQUENCE_OUT_OF_ORDER",
            "AUTH_CREATED_IN_FUTURE",
            "AUTH_DEADLINE_EXPIRED",
            "AUTH_DEADLINE_OUTSIDE_LEASE",
            "AUTH_CORRELATION_REPLAY",
            "AUTH_DOWNSTREAM_NOT_READY",
            "AUTH_MANUAL_RECOVERY_REQUIRED",
        }
        self.assertEqual(AUTHORITY.STABLE_EVENT_CODES, expected)


if __name__ == "__main__":
    unittest.main()
