#!/usr/bin/env python3
"""Offline authority-envelope contract oracle.

This module never starts ROS, publishes a topic, or grants production authority.
The SyntheticAuthorityConsumer is deliberately a test fixture; its counter cannot
be used as SITL, bench, hardware, or production evidence.
"""

import argparse
import copy
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


ACCEPTED = "AUTH_ACCEPTED"
SCHEMA_INVALID = "AUTH_SCHEMA_INVALID"
FAULT_LATCHED = "AUTH_FAULT_LATCHED"
DUPLICATE_WRITER = "AUTH_DUPLICATE_WRITER"
DUPLICATE_OWNER = "AUTH_DUPLICATE_OWNER"
GRAPH_EPOCH_CHANGED = "AUTH_GRAPH_EPOCH_CHANGED"
SOURCE_EPOCH_CHANGED = "AUTH_SOURCE_EPOCH_CHANGED"
OWNER_NOT_CURRENT = "AUTH_OWNER_NOT_CURRENT"
OWNER_INSTANCE_NOT_CURRENT = "AUTH_OWNER_INSTANCE_NOT_CURRENT"
NO_ACTIVE_LEASE = "AUTH_NO_ACTIVE_LEASE"
LEASE_NOT_CURRENT = "AUTH_LEASE_NOT_CURRENT"
LEASE_NOT_ACTIVE = "AUTH_LEASE_NOT_ACTIVE"
LEASE_EXPIRED = "AUTH_LEASE_EXPIRED"
SEQUENCE_DUPLICATE = "AUTH_SEQUENCE_DUPLICATE"
SEQUENCE_OUT_OF_ORDER = "AUTH_SEQUENCE_OUT_OF_ORDER"
CREATED_IN_FUTURE = "AUTH_CREATED_IN_FUTURE"
DEADLINE_EXPIRED = "AUTH_DEADLINE_EXPIRED"
DEADLINE_OUTSIDE_LEASE = "AUTH_DEADLINE_OUTSIDE_LEASE"
CORRELATION_REPLAY = "AUTH_CORRELATION_REPLAY"
DOWNSTREAM_NOT_READY = "AUTH_DOWNSTREAM_NOT_READY"
MANUAL_RECOVERY_REQUIRED = "AUTH_MANUAL_RECOVERY_REQUIRED"

LATCHING_CODES = {
    DUPLICATE_WRITER,
    DUPLICATE_OWNER,
    GRAPH_EPOCH_CHANGED,
    SOURCE_EPOCH_CHANGED,
}

STABLE_EVENT_CODES = {
    ACCEPTED,
    SCHEMA_INVALID,
    FAULT_LATCHED,
    DUPLICATE_WRITER,
    DUPLICATE_OWNER,
    GRAPH_EPOCH_CHANGED,
    SOURCE_EPOCH_CHANGED,
    OWNER_NOT_CURRENT,
    OWNER_INSTANCE_NOT_CURRENT,
    NO_ACTIVE_LEASE,
    LEASE_NOT_CURRENT,
    LEASE_NOT_ACTIVE,
    LEASE_EXPIRED,
    SEQUENCE_DUPLICATE,
    SEQUENCE_OUT_OF_ORDER,
    CREATED_IN_FUTURE,
    DEADLINE_EXPIRED,
    DEADLINE_OUTSIDE_LEASE,
    CORRELATION_REPLAY,
    DOWNSTREAM_NOT_READY,
    MANUAL_RECOVERY_REQUIRED,
}


@dataclass
class AuthorityContext:
    """Previously verified identity and monotonic replay state."""

    current_owner_id: str
    current_owner_instance_id: str
    current_lease_id: Optional[str]
    source_epoch: str
    graph_epoch: str
    now_monotonic_ns: int
    writer_count: int = 1
    owner_count: int = 1
    last_sequence: Optional[int] = None
    seen_correlations: Set[str] = field(default_factory=set)
    latch_state: str = "CLEAR"
    consumer_state: str = "READY"

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "AuthorityContext":
        copied = dict(value)
        copied["seen_correlations"] = set(copied.get("seen_correlations", []))
        return cls(**copied)

    def as_dict(self) -> Dict[str, Any]:
        value = dict(self.__dict__)
        value["seen_correlations"] = sorted(self.seen_correlations)
        return value


@dataclass(frozen=True)
class AuthorityDecision:
    accepted: bool
    event_code: str
    latch_state: str
    consumer_state: str
    envelope_id: Optional[str]
    correlation_id: Optional[str]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "accepted": self.accepted,
            "event_code": self.event_code,
            "latch_state": self.latch_state,
            "consumer_state": self.consumer_state,
            "envelope_id": self.envelope_id,
            "correlation_id": self.correlation_id,
        }


def _decision(
    context: AuthorityContext,
    envelope: Dict[str, Any],
    code: str,
) -> AuthorityDecision:
    if code in LATCHING_CODES:
        context.latch_state = "FAULT_LATCHED"
        context.consumer_state = "FAULT_LATCHED"
    command = envelope.get("command")
    correlation = command.get("correlation_id") if isinstance(command, dict) else None
    return AuthorityDecision(
        accepted=code == ACCEPTED,
        event_code=code,
        latch_state=context.latch_state,
        consumer_state=context.consumer_state,
        envelope_id=envelope.get("envelope_id"),
        correlation_id=correlation,
    )


def _has_required_shape(envelope: Any) -> bool:
    """Minimal fail-closed guard for direct semantic-oracle callers.

    Full shape validation is the Draft 2020-12 schema's responsibility. This
    guard prevents malformed direct calls from raising or being accepted.
    """

    if not isinstance(envelope, dict):
        return False
    required = {
        "schema_version",
        "envelope_id",
        "owner",
        "lease",
        "sequence",
        "created_monotonic_ns",
        "deadline_monotonic_ns",
        "source_epoch",
        "graph_epoch",
        "command",
    }
    if set(envelope) != required or envelope.get("schema_version") != "1.0.0":
        return False
    owner = envelope.get("owner")
    lease = envelope.get("lease")
    command = envelope.get("command")
    if not isinstance(owner, dict) or set(owner) != {"principal_id", "instance_id"}:
        return False
    if not isinstance(lease, dict) or set(lease) != {
        "lease_id",
        "lifecycle",
        "issued_monotonic_ns",
        "expires_monotonic_ns",
    }:
        return False
    if not isinstance(command, dict) or set(command) != {"correlation_id", "kind", "payload"}:
        return False
    integers = (
        envelope.get("sequence"),
        envelope.get("created_monotonic_ns"),
        envelope.get("deadline_monotonic_ns"),
        lease.get("issued_monotonic_ns"),
        lease.get("expires_monotonic_ns"),
    )
    if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in integers):
        return False
    strings = (
        envelope.get("envelope_id"),
        envelope.get("source_epoch"),
        envelope.get("graph_epoch"),
        owner.get("principal_id"),
        owner.get("instance_id"),
        lease.get("lease_id"),
        lease.get("lifecycle"),
        command.get("correlation_id"),
        command.get("kind"),
    )
    return all(isinstance(value, str) and bool(value) for value in strings) and isinstance(
        command.get("payload"), dict
    )


def validate_semantics(
    envelope: Dict[str, Any],
    context: AuthorityContext,
) -> AuthorityDecision:
    """Evaluate one envelope in deterministic fail-closed order."""

    if not _has_required_shape(envelope):
        return _decision(context, envelope if isinstance(envelope, dict) else {}, SCHEMA_INVALID)
    if context.latch_state != "CLEAR":
        return _decision(context, envelope, FAULT_LATCHED)
    if context.writer_count != 1:
        return _decision(context, envelope, DUPLICATE_WRITER)
    if context.owner_count != 1:
        return _decision(context, envelope, DUPLICATE_OWNER)
    if envelope["graph_epoch"] != context.graph_epoch:
        return _decision(context, envelope, GRAPH_EPOCH_CHANGED)
    if envelope["source_epoch"] != context.source_epoch:
        return _decision(context, envelope, SOURCE_EPOCH_CHANGED)
    if envelope["owner"]["principal_id"] != context.current_owner_id:
        return _decision(context, envelope, OWNER_NOT_CURRENT)
    if envelope["owner"]["instance_id"] != context.current_owner_instance_id:
        return _decision(context, envelope, OWNER_INSTANCE_NOT_CURRENT)
    if context.current_lease_id is None:
        return _decision(context, envelope, NO_ACTIVE_LEASE)
    if envelope["lease"]["lease_id"] != context.current_lease_id:
        return _decision(context, envelope, LEASE_NOT_CURRENT)
    if envelope["lease"]["lifecycle"] != "ACTIVE":
        return _decision(context, envelope, LEASE_NOT_ACTIVE)
    if context.now_monotonic_ns >= envelope["lease"]["expires_monotonic_ns"]:
        return _decision(context, envelope, LEASE_EXPIRED)
    if context.last_sequence is not None:
        if envelope["sequence"] == context.last_sequence:
            return _decision(context, envelope, SEQUENCE_DUPLICATE)
        if envelope["sequence"] < context.last_sequence:
            return _decision(context, envelope, SEQUENCE_OUT_OF_ORDER)
    if envelope["created_monotonic_ns"] > context.now_monotonic_ns:
        return _decision(context, envelope, CREATED_IN_FUTURE)
    if context.now_monotonic_ns >= envelope["deadline_monotonic_ns"]:
        return _decision(context, envelope, DEADLINE_EXPIRED)
    if envelope["deadline_monotonic_ns"] > envelope["lease"]["expires_monotonic_ns"]:
        return _decision(context, envelope, DEADLINE_OUTSIDE_LEASE)
    correlation = envelope["command"]["correlation_id"]
    if correlation in context.seen_correlations:
        return _decision(context, envelope, CORRELATION_REPLAY)

    context.last_sequence = envelope["sequence"]
    context.seen_correlations.add(correlation)
    return _decision(context, envelope, ACCEPTED)


def manual_recover(context: AuthorityContext, human_authorized: bool) -> AuthorityDecision:
    """Clear a latch only with explicit human authorization and return to READY."""

    if not human_authorized:
        context.latch_state = "FAULT_LATCHED"
        context.consumer_state = "FAULT_LATCHED"
        return AuthorityDecision(
            False,
            MANUAL_RECOVERY_REQUIRED,
            context.latch_state,
            context.consumer_state,
            None,
            None,
        )
    context.latch_state = "CLEAR"
    context.consumer_state = "READY"
    context.current_lease_id = None
    context.last_sequence = None
    context.seen_correlations.clear()
    return AuthorityDecision(False, NO_ACTIVE_LEASE, "CLEAR", "READY", None, None)


class SyntheticAuthorityConsumer:
    """Test-only boundary fixture; it never communicates with PX4 or ROS."""

    def __init__(self, context: AuthorityContext) -> None:
        self.context = context
        self.synthetic_px4_publish_count = 0

    def consume(
        self,
        envelope: Dict[str, Any],
        downstream_ready: bool,
    ) -> AuthorityDecision:
        previous_sequence = self.context.last_sequence
        previous_correlations = set(self.context.seen_correlations)
        decision = validate_semantics(copy.deepcopy(envelope), self.context)
        if not decision.accepted:
            return decision
        if not downstream_ready:
            # The combined B/C boundary rejected the transaction. Do not consume
            # its sequence/correlation merely because the C1 half was valid.
            self.context.last_sequence = previous_sequence
            self.context.seen_correlations = previous_correlations
            return _decision(self.context, envelope, DOWNSTREAM_NOT_READY)
        self.synthetic_px4_publish_count += 1
        self.context.consumer_state = "ACTIVE"
        return AuthorityDecision(
            True,
            ACCEPTED,
            self.context.latch_state,
            self.context.consumer_state,
            decision.envelope_id,
            decision.correlation_id,
        )


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _schema_errors(schema: Dict[str, Any], envelope: Dict[str, Any]) -> List[str]:
    try:
        import jsonschema
    except ImportError as error:
        raise RuntimeError("jsonschema with Draft202012Validator is required: %s" % error)
    validator_class = getattr(jsonschema, "Draft202012Validator", None)
    if validator_class is None:
        raise RuntimeError(
            "installed jsonschema does not provide Draft202012Validator; schema was not downgraded"
        )
    validator_class.check_schema(schema)
    validator = validator_class(schema)
    return [
        "%s: %s" % ("/".join(str(part) for part in error.absolute_path), error.message)
        for error in sorted(validator.iter_errors(envelope), key=lambda item: list(item.absolute_path))
    ]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--context", required=True, type=Path)
    parser.add_argument("envelope", type=Path)
    args = parser.parse_args(argv)

    try:
        envelope = _load_json(args.envelope)
        context = AuthorityContext.from_dict(_load_json(args.context))
        errors = _schema_errors(_load_json(args.schema), envelope)
    except (OSError, ValueError, TypeError, RuntimeError) as error:
        print("authority envelope validation unavailable: %s" % error, file=sys.stderr)
        return 2
    if errors:
        print(json.dumps({"accepted": False, "event_code": SCHEMA_INVALID, "errors": errors}, indent=2))
        return 3
    decision = validate_semantics(envelope, context)
    print(json.dumps({"decision": decision.as_dict(), "context": context.as_dict()}, indent=2))
    return 0 if decision.accepted else 3


if __name__ == "__main__":
    sys.exit(main())
