#!/usr/bin/env python3
"""C2 pure-software authority runtime and frozen adapter tests."""

import copy
import json
import unittest
from pathlib import Path

from tools.authority.adapter import (
    AUTHORITY_INTERFACE_VERSION,
    EnvelopeContractError,
    adapt_authority_envelope,
)
from tools.authority.runtime import (
    ACTIVE,
    FAULT_LATCHED_STATE,
    READY,
    SAFE_INITIAL,
    AuthorityRuntime,
    GraphSnapshot,
    OwnerIdentity,
    STABLE_LIFECYCLE_EVENT_CODES_V1,
    STABLE_REJECTION_EVENT_CODES_V1,
    STABLE_RUNTIME_EVENT_CODES_V1,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
ENVELOPE_PATH = REPO_ROOT / "test/authority/fixtures/valid/envelope.json"


class AuthorityRuntimeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.envelope = json.loads(ENVELOPE_PATH.read_text(encoding="utf-8"))
        self.owner = OwnerIdentity("mission.primary", "instance.boot-7")
        self.snapshot = GraphSnapshot.create(
            "epoch:source-7", "epoch:graph-12", ["writer.offboard"], [self.owner]
        )
        self.runtime = AuthorityRuntime("mission.primary", "writer.offboard")
        initialized = self.runtime.initialize(self.snapshot, 10_000_000_000)
        self.assertEqual(initialized.event_code, "AUTH_RUNTIME_INITIALIZED")
        granted = self.runtime.grant_lease(
            "lease-20260727-001", 9_000_000_000, 12_000_000_000, 10_000_000_000
        )
        self.assertEqual(granted.event_code, "AUTH_LEASE_GRANTED")

    def consume(self, envelope=None, snapshot=None, now=10_100_000_000, ready=True):
        return self.runtime.consume(
            copy.deepcopy(self.envelope if envelope is None else envelope),
            self.snapshot if snapshot is None else snapshot,
            now,
            ready,
        )

    def test_adapter_freezes_every_observable_identity_and_timing_field(self) -> None:
        adapted = adapt_authority_envelope(copy.deepcopy(self.envelope))
        self.assertEqual(adapted.interface_version, AUTHORITY_INTERFACE_VERSION)
        self.assertEqual(adapted.owner_principal_id, "mission.primary")
        self.assertEqual(adapted.owner_instance_id, "instance.boot-7")
        self.assertEqual(adapted.lease_id, "lease-20260727-001")
        self.assertEqual(adapted.sequence, 42)
        self.assertEqual(adapted.deadline_monotonic_ns, 10_500_000_000)
        self.assertEqual(adapted.source_epoch, "epoch:source-7")
        self.assertEqual(adapted.graph_epoch, "epoch:graph-12")
        self.assertEqual(adapted.correlation_id, "cmd-000042")

    def test_adapter_rejects_unknown_field_and_does_not_alias_payload(self) -> None:
        envelope = copy.deepcopy(self.envelope)
        adapted = adapt_authority_envelope(envelope)
        envelope["command"]["payload"]["control_mode"] = "mutated"
        self.assertEqual(adapted.command_payload["control_mode"], "position")
        envelope["permit_publish"] = True
        with self.assertRaises(EnvelopeContractError):
            adapt_authority_envelope(envelope)

    def test_accepted_command_has_exactly_one_synthetic_publish(self) -> None:
        event = self.consume()
        self.assertTrue(event.accepted)
        self.assertEqual(event.event_code, "AUTH_ACCEPTED")
        self.assertEqual(event.synthetic_publish_delta, 1)
        self.assertEqual(event.synthetic_publish_count, 1)
        self.assertEqual(event.runtime_state, ACTIVE)

    def test_non_owner_rejects_with_zero_publish_delta(self) -> None:
        envelope = copy.deepcopy(self.envelope)
        envelope["owner"]["principal_id"] = "mission.intruder"
        event = self.consume(envelope)
        self.assertEqual(event.event_code, "AUTH_OWNER_NOT_CURRENT")
        self.assertEqual(event.synthetic_publish_delta, 0)
        self.assertEqual(event.synthetic_publish_count, 0)

    def test_expired_lease_rejects_and_retires_lease(self) -> None:
        event = self.consume(now=12_000_000_000)
        self.assertEqual(event.event_code, "AUTH_LEASE_EXPIRED")
        self.assertEqual(event.synthetic_publish_delta, 0)
        second = self.consume(now=12_000_000_001)
        self.assertEqual(second.event_code, "AUTH_NO_ACTIVE_LEASE")

    def test_old_epoch_latches_and_rejected_command_never_publishes(self) -> None:
        envelope = copy.deepcopy(self.envelope)
        envelope["source_epoch"] = "epoch:source-6"
        event = self.consume(envelope)
        self.assertEqual(event.event_code, "AUTH_SOURCE_EPOCH_CHANGED")
        self.assertEqual(event.latch_state, FAULT_LATCHED_STATE)
        self.assertEqual(event.synthetic_publish_delta, 0)
        self.assertEqual(event.synthetic_publish_count, 0)

    def test_duplicate_and_out_of_order_sequences_are_rejected(self) -> None:
        accepted = self.consume()
        self.assertTrue(accepted.accepted)
        duplicate = copy.deepcopy(self.envelope)
        duplicate["command"]["correlation_id"] = "cmd-duplicate-sequence"
        event = self.consume(duplicate)
        self.assertEqual(event.event_code, "AUTH_SEQUENCE_DUPLICATE")
        self.assertEqual(event.synthetic_publish_delta, 0)
        out_of_order = copy.deepcopy(self.envelope)
        out_of_order["sequence"] = 41
        out_of_order["command"]["correlation_id"] = "cmd-out-of-order"
        event = self.consume(out_of_order)
        self.assertEqual(event.event_code, "AUTH_SEQUENCE_OUT_OF_ORDER")
        self.assertEqual(event.synthetic_publish_delta, 0)
        self.assertEqual(event.synthetic_publish_count, 1)

    def test_continuous_duplicate_writer_detection_latches_without_a_command(self) -> None:
        duplicate = GraphSnapshot.create(
            self.snapshot.source_epoch,
            self.snapshot.graph_epoch,
            ["writer.offboard", "writer.rogue"],
            [self.owner],
        )
        event = self.runtime.observe_graph(duplicate, 10_100_000_000)
        self.assertEqual(event.event_code, "AUTH_DUPLICATE_WRITER")
        self.assertEqual(event.runtime_state, FAULT_LATCHED_STATE)
        recovered_shape = self.runtime.observe_graph(self.snapshot, 10_200_000_000)
        self.assertEqual(recovered_shape.event_code, "AUTH_FAULT_LATCHED")

    def test_continuous_duplicate_owner_detection_latches_without_a_command(self) -> None:
        duplicate = GraphSnapshot.create(
            self.snapshot.source_epoch,
            self.snapshot.graph_epoch,
            ["writer.offboard"],
            [self.owner, OwnerIdentity("mission.primary", "instance.rogue")],
        )
        event = self.runtime.observe_graph(duplicate, 10_100_000_000)
        self.assertEqual(event.event_code, "AUTH_DUPLICATE_OWNER")
        self.assertEqual(event.runtime_state, FAULT_LATCHED_STATE)

    def test_graph_identity_or_cardinality_change_latches_fail_closed(self) -> None:
        changed = GraphSnapshot.create(
            self.snapshot.source_epoch,
            "epoch:graph-13",
            ["writer.offboard"],
            [self.owner],
        )
        event = self.runtime.observe_graph(changed, 10_100_000_000)
        self.assertEqual(event.event_code, "AUTH_GRAPH_EPOCH_CHANGED")
        self.assertEqual(event.latch_state, FAULT_LATCHED_STATE)
        self.assertEqual(event.synthetic_publish_count, 0)

    def test_reconnect_requires_manual_ack_and_cannot_reuse_old_lease(self) -> None:
        reconnected = GraphSnapshot.create(
            "epoch:source-8",
            "epoch:graph-13",
            ["writer.offboard"],
            [OwnerIdentity("mission.primary", "instance.boot-8")],
        )
        event = self.runtime.observe_graph(reconnected, 10_100_000_000)
        self.assertEqual(event.event_code, "AUTH_SOURCE_EPOCH_CHANGED")
        denied = self.runtime.acknowledge_recovery(
            reconnected, 10_200_000_000, human_authorized=False
        )
        self.assertEqual(denied.event_code, "AUTH_MANUAL_RECOVERY_REQUIRED")
        acknowledged = self.runtime.acknowledge_recovery(
            reconnected, 10_200_000_000, human_authorized=True
        )
        self.assertEqual(acknowledged.event_code, "AUTH_RECOVERY_ACKNOWLEDGED")
        self.assertEqual(acknowledged.runtime_state, READY)
        self.assertNotEqual(acknowledged.runtime_state, ACTIVE)
        reused = self.runtime.grant_lease(
            "lease-20260727-001", 10_200_000_000, 13_000_000_000, 10_200_000_000
        )
        self.assertEqual(reused.event_code, "AUTH_LEASE_REUSE_REJECTED")

    def test_recovery_requires_reviewed_single_writer_single_owner_graph(self) -> None:
        duplicate = GraphSnapshot.create(
            "epoch:source-8",
            "epoch:graph-13",
            ["writer.offboard", "writer.rogue"],
            [OwnerIdentity("mission.primary", "instance.boot-8")],
        )
        self.runtime.observe_graph(duplicate, 10_100_000_000)
        event = self.runtime.acknowledge_recovery(
            duplicate, 10_200_000_000, human_authorized=True
        )
        self.assertEqual(event.event_code, "AUTH_DUPLICATE_WRITER")
        self.assertEqual(event.runtime_state, FAULT_LATCHED_STATE)

    def test_restart_returns_safe_initial_and_does_not_inherit_authority(self) -> None:
        self.assertTrue(self.consume().accepted)
        event = self.runtime.restart()
        self.assertEqual(event.event_code, "AUTH_RESTART_SAFE")
        self.assertEqual(event.runtime_state, SAFE_INITIAL)
        self.assertEqual(event.latch_state, "CLEAR")
        rejected = self.consume()
        self.assertEqual(rejected.event_code, "AUTH_NO_ACTIVE_LEASE")
        self.assertEqual(rejected.synthetic_publish_delta, 0)
        self.assertEqual(rejected.synthetic_publish_count, 1)

    def test_new_lease_must_match_all_granted_lease_fields(self) -> None:
        envelope = copy.deepcopy(self.envelope)
        envelope["lease"]["expires_monotonic_ns"] = 11_900_000_000
        event = self.consume(envelope)
        self.assertEqual(event.event_code, "AUTH_LEASE_NOT_CURRENT")
        self.assertEqual(event.synthetic_publish_count, 0)

    def test_deadline_and_clock_rejections_stay_publish_free(self) -> None:
        cases = (
            ("created_monotonic_ns", 10_200_000_000, "AUTH_CREATED_IN_FUTURE"),
            ("deadline_monotonic_ns", 10_100_000_000, "AUTH_DEADLINE_EXPIRED"),
            ("deadline_monotonic_ns", 12_000_000_001, "AUTH_DEADLINE_OUTSIDE_LEASE"),
        )
        for field, value, expected in cases:
            with self.subTest(field=field, expected=expected):
                runtime = AuthorityRuntime("mission.primary", "writer.offboard")
                runtime.initialize(self.snapshot, 10_000_000_000)
                runtime.grant_lease(
                    "lease-20260727-001",
                    9_000_000_000,
                    12_000_000_000,
                    10_000_000_000,
                )
                envelope = copy.deepcopy(self.envelope)
                envelope[field] = value
                event = runtime.consume(
                    envelope, self.snapshot, 10_100_000_000, downstream_ready=True
                )
                self.assertEqual(event.event_code, expected)
                self.assertEqual(event.synthetic_publish_count, 0)

    def test_downstream_rejection_does_not_consume_replay_state(self) -> None:
        rejected = self.consume(ready=False)
        self.assertEqual(rejected.event_code, "AUTH_DOWNSTREAM_NOT_READY")
        self.assertEqual(rejected.synthetic_publish_count, 0)
        accepted = self.consume(ready=True)
        self.assertTrue(accepted.accepted)
        self.assertEqual(accepted.synthetic_publish_count, 1)

    def test_runtime_event_contract_is_exact_and_partitioned(self) -> None:
        self.assertIn("AUTH_OWNER_NOT_CURRENT", STABLE_REJECTION_EVENT_CODES_V1)
        self.assertIn("AUTH_GRAPH_EPOCH_CHANGED", STABLE_REJECTION_EVENT_CODES_V1)
        self.assertIn("AUTH_LEASE_REUSE_REJECTED", STABLE_REJECTION_EVENT_CODES_V1)
        self.assertIn("AUTH_RECOVERY_ACKNOWLEDGED", STABLE_LIFECYCLE_EVENT_CODES_V1)
        self.assertNotIn("AUTH_ACCEPTED", STABLE_REJECTION_EVENT_CODES_V1)
        self.assertEqual(
            STABLE_REJECTION_EVENT_CODES_V1 & STABLE_LIFECYCLE_EVENT_CODES_V1,
            frozenset(),
        )
        self.assertEqual(
            STABLE_RUNTIME_EVENT_CODES_V1,
            STABLE_REJECTION_EVENT_CODES_V1
            | STABLE_LIFECYCLE_EVENT_CODES_V1
            | {"AUTH_ACCEPTED"},
        )


if __name__ == "__main__":
    unittest.main()
