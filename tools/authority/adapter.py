#!/usr/bin/env python3
"""Strict, authorization-neutral adapter for authority envelope version 1.

Adapting an envelope never grants authority and never permits publication.  The
runtime must still verify the current graph, owner, lease, epochs, replay state,
deadline, and downstream readiness.
"""

import copy
from dataclasses import dataclass
from typing import Any, Dict

from tools.authority.validate_envelope import SCHEMA_INVALID, _has_required_shape


AUTHORITY_INTERFACE_VERSION = "boom-boom-fly.authority-envelope/1.0.0"


class EnvelopeContractError(ValueError):
    """Fail-closed adapter error with a stable rejection code."""

    event_code = SCHEMA_INVALID


@dataclass(frozen=True)
class AdaptedAuthorityEnvelope:
    """Observable authority fields consumed by the B/C integration boundary."""

    interface_version: str
    envelope_id: str
    owner_principal_id: str
    owner_instance_id: str
    lease_id: str
    lease_lifecycle: str
    lease_issued_monotonic_ns: int
    lease_expires_monotonic_ns: int
    sequence: int
    created_monotonic_ns: int
    deadline_monotonic_ns: int
    source_epoch: str
    graph_epoch: str
    correlation_id: str
    command_kind: str
    command_payload: Dict[str, Any]


def adapt_authority_envelope(envelope: Dict[str, Any]) -> AdaptedAuthorityEnvelope:
    """Map the exact v1 shape into immutable integration fields.

    The C1 direct-call shape guard intentionally rejects missing and unknown
    fields.  Full JSON Schema validation remains required at an external input
    boundary; this guard makes in-process calls fail closed as well.
    """

    if not _has_required_shape(envelope):
        raise EnvelopeContractError("authority envelope does not match the frozen v1 shape")
    owner = envelope["owner"]
    lease = envelope["lease"]
    command = envelope["command"]
    return AdaptedAuthorityEnvelope(
        interface_version=AUTHORITY_INTERFACE_VERSION,
        envelope_id=envelope["envelope_id"],
        owner_principal_id=owner["principal_id"],
        owner_instance_id=owner["instance_id"],
        lease_id=lease["lease_id"],
        lease_lifecycle=lease["lifecycle"],
        lease_issued_monotonic_ns=lease["issued_monotonic_ns"],
        lease_expires_monotonic_ns=lease["expires_monotonic_ns"],
        sequence=envelope["sequence"],
        created_monotonic_ns=envelope["created_monotonic_ns"],
        deadline_monotonic_ns=envelope["deadline_monotonic_ns"],
        source_epoch=envelope["source_epoch"],
        graph_epoch=envelope["graph_epoch"],
        correlation_id=command["correlation_id"],
        command_kind=command["kind"],
        command_payload=copy.deepcopy(command["payload"]),
    )
