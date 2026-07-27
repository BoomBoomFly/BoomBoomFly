#!/usr/bin/env python3
"""Pure-software C2 owner/lease/graph authority runtime.

This module has no ROS, PX4, transport, Agent, device, or hardware dependency.
Its publish counter is synthetic test instrumentation and is not flight or bench
evidence.
"""

import copy
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Optional, Sequence, Tuple

from tools.authority.adapter import EnvelopeContractError, adapt_authority_envelope
from tools.authority.validate_envelope import (
    ACCEPTED,
    CREATED_IN_FUTURE,
    DEADLINE_EXPIRED,
    DEADLINE_OUTSIDE_LEASE,
    DUPLICATE_OWNER,
    DUPLICATE_WRITER,
    FAULT_LATCHED,
    GRAPH_EPOCH_CHANGED,
    LATCHING_CODES,
    LEASE_EXPIRED,
    LEASE_NOT_ACTIVE,
    LEASE_NOT_CURRENT,
    MANUAL_RECOVERY_REQUIRED,
    NO_ACTIVE_LEASE,
    OWNER_INSTANCE_NOT_CURRENT,
    OWNER_NOT_CURRENT,
    SCHEMA_INVALID,
    SEQUENCE_DUPLICATE,
    SEQUENCE_OUT_OF_ORDER,
    SOURCE_EPOCH_CHANGED,
    STABLE_EVENT_CODES,
    AuthorityContext,
    SyntheticAuthorityConsumer,
)


RUNTIME_INITIALIZED = "AUTH_RUNTIME_INITIALIZED"
GRAPH_HEALTHY = "AUTH_GRAPH_HEALTHY"
LEASE_GRANTED = "AUTH_LEASE_GRANTED"
LEASE_REUSE_REJECTED = "AUTH_LEASE_REUSE_REJECTED"
RECOVERY_ACKNOWLEDGED = "AUTH_RECOVERY_ACKNOWLEDGED"
RESTART_SAFE = "AUTH_RESTART_SAFE"

STABLE_LIFECYCLE_EVENT_CODES_V1: FrozenSet[str] = frozenset(
    {
        RUNTIME_INITIALIZED,
        GRAPH_HEALTHY,
        LEASE_GRANTED,
        RECOVERY_ACKNOWLEDGED,
        RESTART_SAFE,
    }
)
STABLE_REJECTION_EVENT_CODES_V1: FrozenSet[str] = frozenset(
    (STABLE_EVENT_CODES - {ACCEPTED}) | {LEASE_REUSE_REJECTED}
)
STABLE_RUNTIME_EVENT_CODES_V1: FrozenSet[str] = frozenset(
    STABLE_EVENT_CODES
    | STABLE_LIFECYCLE_EVENT_CODES_V1
    | STABLE_REJECTION_EVENT_CODES_V1
)

SAFE_INITIAL = "SAFE_INITIAL"
READY = "READY"
ACTIVE = "ACTIVE"
FAULT_LATCHED_STATE = "FAULT_LATCHED"


@dataclass(frozen=True, order=True)
class OwnerIdentity:
    principal_id: str
    instance_id: str


@dataclass(frozen=True)
class GraphSnapshot:
    """One complete graph observation used by the continuous guard."""

    source_epoch: str
    graph_epoch: str
    writer_ids: Tuple[str, ...]
    owners: Tuple[OwnerIdentity, ...]

    @classmethod
    def create(
        cls,
        source_epoch: str,
        graph_epoch: str,
        writer_ids: Sequence[str],
        owners: Sequence[OwnerIdentity],
    ) -> "GraphSnapshot":
        return cls(source_epoch, graph_epoch, tuple(writer_ids), tuple(owners))


@dataclass(frozen=True)
class LeaseGrant:
    lease_id: str
    issued_monotonic_ns: int
    expires_monotonic_ns: int


@dataclass(frozen=True)
class AuthorityRuntimeEvent:
    event_code: str
    accepted: bool
    latch_state: str
    runtime_state: str
    envelope_id: Optional[str] = None
    correlation_id: Optional[str] = None
    synthetic_publish_delta: int = 0
    synthetic_publish_count: int = 0


class AuthorityRuntime:
    """Stateful fail-closed authority arbiter with an observable v1 contract."""

    def __init__(self, expected_owner_principal_id: str, expected_writer_id: str) -> None:
        if not expected_owner_principal_id or not expected_writer_id:
            raise ValueError("expected owner principal and writer identities are required")
        self.expected_owner_principal_id = expected_owner_principal_id
        self.expected_writer_id = expected_writer_id
        self.runtime_state = SAFE_INITIAL
        self.latch_state = "CLEAR"
        self.synthetic_px4_publish_count = 0
        self._baseline: Optional[GraphSnapshot] = None
        self._context: Optional[AuthorityContext] = None
        self._lease: Optional[LeaseGrant] = None
        self._retired_lease_ids = set()  # type: set

    def _event(
        self,
        code: str,
        accepted: bool = False,
        envelope_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        publish_delta: int = 0,
    ) -> AuthorityRuntimeEvent:
        return AuthorityRuntimeEvent(
            event_code=code,
            accepted=accepted,
            latch_state=self.latch_state,
            runtime_state=self.runtime_state,
            envelope_id=envelope_id,
            correlation_id=correlation_id,
            synthetic_publish_delta=publish_delta,
            synthetic_publish_count=self.synthetic_px4_publish_count,
        )

    @staticmethod
    def _snapshot_shape_rejection(
        snapshot: GraphSnapshot,
        expected_owner_principal_id: str,
        expected_writer_id: str,
    ) -> Optional[str]:
        if len(snapshot.writer_ids) != 1:
            return DUPLICATE_WRITER
        if len(snapshot.owners) != 1:
            return DUPLICATE_OWNER
        if snapshot.writer_ids[0] != expected_writer_id:
            return GRAPH_EPOCH_CHANGED
        if snapshot.owners[0].principal_id != expected_owner_principal_id:
            return GRAPH_EPOCH_CHANGED
        if not snapshot.source_epoch or not snapshot.graph_epoch:
            return GRAPH_EPOCH_CHANGED
        return None

    def _retire_current_lease(self) -> None:
        if self._lease is not None:
            self._retired_lease_ids.add(self._lease.lease_id)
        self._lease = None
        if self._context is not None:
            self._context.current_lease_id = None

    def _latch(self, code: str) -> AuthorityRuntimeEvent:
        self._retire_current_lease()
        self.latch_state = FAULT_LATCHED_STATE
        self.runtime_state = FAULT_LATCHED_STATE
        if self._context is not None:
            self._context.latch_state = FAULT_LATCHED_STATE
            self._context.consumer_state = FAULT_LATCHED_STATE
        return self._event(code)

    def initialize(self, snapshot: GraphSnapshot, now_monotonic_ns: int) -> AuthorityRuntimeEvent:
        """Establish the first observed graph baseline without granting a lease."""

        if self.runtime_state != SAFE_INITIAL or self._baseline is not None:
            return self._latch(GRAPH_EPOCH_CHANGED)
        rejection = self._snapshot_shape_rejection(
            snapshot, self.expected_owner_principal_id, self.expected_writer_id
        )
        if rejection is not None:
            return self._latch(rejection)
        if now_monotonic_ns < 0:
            return self._latch(GRAPH_EPOCH_CHANGED)
        owner = snapshot.owners[0]
        self._baseline = snapshot
        self._context = AuthorityContext(
            current_owner_id=owner.principal_id,
            current_owner_instance_id=owner.instance_id,
            current_lease_id=None,
            source_epoch=snapshot.source_epoch,
            graph_epoch=snapshot.graph_epoch,
            now_monotonic_ns=now_monotonic_ns,
            writer_count=1,
            owner_count=1,
            last_sequence=None,
            seen_correlations=set(),
            latch_state="CLEAR",
            consumer_state=READY,
        )
        self.runtime_state = READY
        return self._event(RUNTIME_INITIALIZED)

    def observe_graph(
        self, snapshot: GraphSnapshot, now_monotonic_ns: int
    ) -> AuthorityRuntimeEvent:
        """Continuously enforce graph cardinality, identity, and epochs."""

        if self.latch_state != "CLEAR":
            return self._event(FAULT_LATCHED)
        if self._baseline is None or self._context is None:
            return self._event(NO_ACTIVE_LEASE)
        rejection = self._snapshot_shape_rejection(
            snapshot, self.expected_owner_principal_id, self.expected_writer_id
        )
        if rejection is not None:
            return self._latch(rejection)
        if snapshot.source_epoch != self._baseline.source_epoch:
            return self._latch(SOURCE_EPOCH_CHANGED)
        if (
            snapshot.graph_epoch != self._baseline.graph_epoch
            or snapshot.writer_ids != self._baseline.writer_ids
            or snapshot.owners != self._baseline.owners
        ):
            return self._latch(GRAPH_EPOCH_CHANGED)
        self._context.now_monotonic_ns = now_monotonic_ns
        self._context.writer_count = len(snapshot.writer_ids)
        self._context.owner_count = len(snapshot.owners)
        if self._lease is not None and now_monotonic_ns >= self._lease.expires_monotonic_ns:
            self._retire_current_lease()
            self.runtime_state = READY
            self._context.consumer_state = READY
            return self._event(LEASE_EXPIRED)
        return self._event(GRAPH_HEALTHY)

    def grant_lease(
        self,
        lease_id: str,
        issued_monotonic_ns: int,
        expires_monotonic_ns: int,
        now_monotonic_ns: int,
    ) -> AuthorityRuntimeEvent:
        """Install a fresh lease only after a healthy graph baseline exists."""

        if self.latch_state != "CLEAR":
            return self._event(FAULT_LATCHED)
        if self._context is None or self._baseline is None:
            return self._event(NO_ACTIVE_LEASE)
        if self._lease is not None or lease_id in self._retired_lease_ids:
            return self._event(LEASE_REUSE_REJECTED)
        if (
            not lease_id
            or issued_monotonic_ns < 0
            or expires_monotonic_ns <= issued_monotonic_ns
            or issued_monotonic_ns > now_monotonic_ns
            or now_monotonic_ns >= expires_monotonic_ns
        ):
            return self._event(LEASE_EXPIRED)
        self._lease = LeaseGrant(lease_id, issued_monotonic_ns, expires_monotonic_ns)
        self._context.current_lease_id = lease_id
        self._context.now_monotonic_ns = now_monotonic_ns
        self._context.last_sequence = None
        self._context.seen_correlations.clear()
        self._context.consumer_state = READY
        self.runtime_state = READY
        return self._event(LEASE_GRANTED)

    def consume(
        self,
        envelope: Dict[str, Any],
        snapshot: GraphSnapshot,
        now_monotonic_ns: int,
        downstream_ready: bool,
    ) -> AuthorityRuntimeEvent:
        """Evaluate one command; a rejection always has zero publish delta."""

        graph_event = self.observe_graph(snapshot, now_monotonic_ns)
        if graph_event.event_code != GRAPH_HEALTHY:
            return graph_event
        if self._context is None or self._lease is None:
            return self._event(NO_ACTIVE_LEASE)
        try:
            adapted = adapt_authority_envelope(envelope)
        except EnvelopeContractError:
            return self._event(SCHEMA_INVALID)
        if (
            adapted.lease_id != self._lease.lease_id
            or adapted.lease_issued_monotonic_ns != self._lease.issued_monotonic_ns
            or adapted.lease_expires_monotonic_ns != self._lease.expires_monotonic_ns
        ):
            return self._event(
                LEASE_NOT_CURRENT,
                envelope_id=adapted.envelope_id,
                correlation_id=adapted.correlation_id,
            )
        consumer = SyntheticAuthorityConsumer(self._context)
        consumer.synthetic_px4_publish_count = self.synthetic_px4_publish_count
        decision = consumer.consume(copy.deepcopy(envelope), downstream_ready=downstream_ready)
        before = self.synthetic_px4_publish_count
        self.synthetic_px4_publish_count = consumer.synthetic_px4_publish_count
        if decision.event_code in LATCHING_CODES:
            self._retire_current_lease()
            self.latch_state = FAULT_LATCHED_STATE
            self.runtime_state = FAULT_LATCHED_STATE
        elif decision.accepted:
            self.runtime_state = ACTIVE
        return self._event(
            decision.event_code,
            accepted=decision.accepted,
            envelope_id=decision.envelope_id,
            correlation_id=decision.correlation_id,
            publish_delta=self.synthetic_px4_publish_count - before,
        )

    def acknowledge_recovery(
        self, snapshot: GraphSnapshot, now_monotonic_ns: int, human_authorized: bool
    ) -> AuthorityRuntimeEvent:
        """Adopt a reviewed graph only after explicit human acknowledgement."""

        if not human_authorized:
            return self._event(MANUAL_RECOVERY_REQUIRED)
        if self.latch_state != FAULT_LATCHED_STATE:
            return self._event(MANUAL_RECOVERY_REQUIRED)
        rejection = self._snapshot_shape_rejection(
            snapshot, self.expected_owner_principal_id, self.expected_writer_id
        )
        if rejection is not None:
            return self._latch(rejection)
        owner = snapshot.owners[0]
        self._baseline = snapshot
        self._context = AuthorityContext(
            current_owner_id=owner.principal_id,
            current_owner_instance_id=owner.instance_id,
            current_lease_id=None,
            source_epoch=snapshot.source_epoch,
            graph_epoch=snapshot.graph_epoch,
            now_monotonic_ns=now_monotonic_ns,
            writer_count=1,
            owner_count=1,
            last_sequence=None,
            seen_correlations=set(),
            latch_state="CLEAR",
            consumer_state=READY,
        )
        self._lease = None
        self.latch_state = "CLEAR"
        self.runtime_state = READY
        return self._event(RECOVERY_ACKNOWLEDGED)

    def restart(self) -> AuthorityRuntimeEvent:
        """Return to a no-baseline, no-lease, non-active safe initial state."""

        self._retire_current_lease()
        self._baseline = None
        self._context = None
        self.latch_state = "CLEAR"
        self.runtime_state = SAFE_INITIAL
        return self._event(RESTART_SAFE)
