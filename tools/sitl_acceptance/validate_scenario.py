#!/usr/bin/env python3
"""Validate one BoomBoomFly offline SITL scenario without external packages."""

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set


SCHEMA_VERSION = "1.0.0"
ALLOWED_STATUS = {
    "PLANNED",
    "STATICALLY_VERIFIED",
    "UNIT_TESTED",
    "BLOCKED",
    "UNVERIFIED",
}
ALLOWED_BLOCKERS = {
    "BLOCKED_BY_T00",
    "BLOCKED_BY_T01",
    "BLOCKED_BY_T02",
    "BLOCKED_BY_T03",
    "BLOCKED_BY_T04",
    "BLOCKED_BY_T05",
    "BLOCKED_BY_T06",
    "BLOCKED_BY_T08",
    "SAFETY_DECISION_REQUIRED",
}
DURATION_RE = re.compile(r"^(0|[1-9][0-9]*)(\.[0-9]+)?(ns|us|ms|s|min)$")
SCENARIO_ID_RE = re.compile(r"^SITL-(NORMAL|FAULT)-[0-9]{3}$")
AMBIGUOUS_FIELDS = {
    "wait_some_time",
    "eventually",
    "should_be_ok",
    "approximately",
}
CORE_FIELDS = {
    "schema_version",
    "scenario_id",
    "title",
    "status",
    "requirement_ids",
    "audit_ids",
    "milestone",
    "profile",
    "preconditions",
    "forbidden_conditions",
    "participants",
    "source_identity",
    "initial_state",
    "stimuli",
    "expected_events",
    "forbidden_events",
    "timeouts",
    "cleanup",
    "evidence",
    "dependencies",
    "limitations",
    "assertions",
    "fault_injection",
    "extensions",
}


def _error(errors: List[Dict[str, str]], code: str, path: str, message: str) -> None:
    errors.append({"code": code, "message": message, "path": path})


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_string_array(
    value: Any,
    path: str,
    errors: List[Dict[str, str]],
    *,
    minimum: int = 0
) -> None:
    if not isinstance(value, list):
        _error(errors, "TYPE", path, "must be an array")
        return
    if len(value) < minimum:
        _error(errors, "MIN_ITEMS", path, "must contain at least %d item(s)" % minimum)
    seen: Set[str] = set()
    for index, item in enumerate(value):
        item_path = "%s[%d]" % (path, index)
        if not _nonempty_string(item):
            _error(errors, "TYPE", item_path, "must be a non-empty string")
        elif item in seen:
            _error(errors, "DUPLICATE", item_path, "must be unique")
        else:
            seen.add(item)


def _validate_duration(value: Any, path: str, errors: List[Dict[str, str]]) -> None:
    if not isinstance(value, str) or not DURATION_RE.fullmatch(value):
        _error(
            errors,
            "TIME_UNIT_REQUIRED",
            path,
            "must be a non-negative duration with ns, us, ms, s, or min unit",
        )


def _validate_count(value: Any, path: str, errors: List[Dict[str, str]]) -> None:
    if not isinstance(value, dict):
        _error(errors, "TYPE", path, "must be an object with min and max")
        return
    if set(value) != {"min", "max"}:
        _error(errors, "FIELDS", path, "must contain exactly min and max")
    minimum = value.get("min")
    maximum = value.get("max")
    for key, item in (("min", minimum), ("max", maximum)):
        if not isinstance(item, int) or isinstance(item, bool) or item < 0:
            _error(errors, "COUNT", "%s.%s" % (path, key), "must be a non-negative integer")
    if (
        isinstance(minimum, int)
        and not isinstance(minimum, bool)
        and isinstance(maximum, int)
        and not isinstance(maximum, bool)
        and minimum > maximum
    ):
        _error(errors, "COUNT_RANGE", path, "min must not exceed max")


def _require_fields(
    value: Any,
    path: str,
    required: Iterable[str],
    allowed: Iterable[str],
    errors: List[Dict[str, str]],
) -> bool:
    if not isinstance(value, dict):
        _error(errors, "TYPE", path, "must be an object")
        return False
    required_set = set(required)
    allowed_set = set(allowed)
    for key in sorted(required_set - set(value)):
        _error(errors, "REQUIRED", "%s.%s" % (path, key), "required field is missing")
    for key in sorted(set(value) - allowed_set):
        _error(errors, "UNKNOWN_FIELD", "%s.%s" % (path, key), "field is not allowed")
    return True


def _walk_forbidden_keys(value: Any, path: str, errors: List[Dict[str, str]]) -> None:
    if isinstance(value, dict):
        for key in sorted(value):
            next_path = "%s.%s" % (path, key)
            if key in AMBIGUOUS_FIELDS:
                _error(errors, "AMBIGUOUS_FIELD", next_path, "ambiguous timing/result field is forbidden")
            _walk_forbidden_keys(value[key], next_path, errors)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk_forbidden_keys(item, "%s[%d]" % (path, index), errors)


def _walk_safety_strings(value: Any, path: str, errors: List[Dict[str, str]]) -> None:
    prohibited_statuses = {
        "SITL_" + "VERIFIED",
        "BENCH_" + "VERIFIED",
        "FLIGHT_" + "VERIFIED",
        "PRODUCTION_" + "READY",
    }
    prohibited_devices = (
        "/dev/" + "ttyTHS0",
        "/dev/" + "ttyACM",
        "/dev/" + "ttyUSB",
    )
    if isinstance(value, str):
        lowered = value.lower()
        if value in prohibited_statuses:
            _error(errors, "FORBIDDEN_STATUS", path, "runtime/higher-level verification status is forbidden")
        if any(device in value for device in prohibited_devices):
            _error(errors, "HARDWARE_PATH", path, "hardware device paths are forbidden in SITL scenarios")
        if "firmware " + "flash" in lowered:
            _error(errors, "FIRMWARE_OPERATION", path, "firmware programming is forbidden")
        if "real hardware" in lowered and "arm" in lowered:
            _error(errors, "HARDWARE_ARM", path, "arming real hardware is forbidden")
    elif isinstance(value, dict):
        for key in sorted(value):
            _walk_safety_strings(value[key], "%s.%s" % (path, key), errors)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk_safety_strings(item, "%s[%d]" % (path, index), errors)


def _validate_profile(value: Any, errors: List[Dict[str, str]]) -> None:
    required = {"profile_id", "environment", "transport", "ros_domain_isolated", "namespace"}
    if not _require_fields(value, "$.profile", required, required, errors):
        return
    if not _nonempty_string(value.get("profile_id")):
        _error(errors, "TYPE", "$.profile.profile_id", "must be a non-empty string")
    expected = {
        "environment": "SITL",
        "transport": "UDP",
        "ros_domain_isolated": True,
        "namespace": "/",
    }
    for key in sorted(expected):
        if value.get(key) != expected[key]:
            _error(errors, "PROFILE", "$.profile.%s" % key, "must equal %r" % expected[key])


def _validate_participants(value: Any, errors: List[Dict[str, str]]) -> Set[str]:
    identifiers: Set[str] = set()
    if not isinstance(value, list) or not value:
        _error(errors, "TYPE", "$.participants", "must be a non-empty array")
        return identifiers
    fields = {"participant_id", "role", "required", "expected_count"}
    for index, participant in enumerate(value):
        path = "$.participants[%d]" % index
        if not _require_fields(participant, path, fields, fields, errors):
            continue
        participant_id = participant.get("participant_id")
        if not _nonempty_string(participant_id):
            _error(errors, "TYPE", path + ".participant_id", "must be a non-empty string")
        elif participant_id in identifiers:
            _error(errors, "DUPLICATE_ID", path + ".participant_id", "participant ID must be unique")
        else:
            identifiers.add(participant_id)
        if not _nonempty_string(participant.get("role")):
            _error(errors, "TYPE", path + ".role", "must be a non-empty string")
        if not isinstance(participant.get("required"), bool):
            _error(errors, "TYPE", path + ".required", "must be boolean")
        _validate_count(participant.get("expected_count"), path + ".expected_count", errors)
    return identifiers


def _validate_source_identity(value: Any, errors: List[Dict[str, str]]) -> Set[str]:
    sources: Set[str] = set()
    fields = {"profile_ref", "bindings"}
    if not _require_fields(value, "$.source_identity", fields, fields, errors):
        return sources
    if not _nonempty_string(value.get("profile_ref")):
        _error(errors, "TYPE", "$.source_identity.profile_ref", "must be a non-empty string")
    bindings = value.get("bindings")
    if not isinstance(bindings, list) or not bindings:
        _error(errors, "TYPE", "$.source_identity.bindings", "must be a non-empty array")
        return sources
    binding_fields = {"source", "identity_kind", "expected", "mock"}
    for index, binding in enumerate(bindings):
        path = "$.source_identity.bindings[%d]" % index
        if not _require_fields(binding, path, binding_fields, binding_fields, errors):
            continue
        source = binding.get("source")
        for key in ("source", "identity_kind", "expected"):
            if not _nonempty_string(binding.get(key)):
                _error(errors, "TYPE", path + "." + key, "must be a non-empty string")
        if _nonempty_string(source):
            if source in sources:
                _error(errors, "DUPLICATE_ID", path + ".source", "source binding must be unique")
            sources.add(source)
        if not isinstance(binding.get("mock"), bool):
            _error(errors, "TYPE", path + ".mock", "must be boolean")
        identity_text = "%s %s" % (binding.get("identity_kind", ""), binding.get("expected", ""))
        if binding.get("mock") is True and "PX4" in identity_text.upper():
            _error(errors, "MOCK_IDENTITY", path, "mock source cannot claim authoritative PX4 identity")
    return sources


def _validate_stimuli(value: Any, errors: List[Dict[str, str]]) -> Set[str]:
    identifiers: Set[str] = set()
    fields = {"stimulus_id", "at", "action", "source", "target", "payload_class", "correlation_id"}
    if not isinstance(value, list):
        _error(errors, "TYPE", "$.stimuli", "must be an array")
        return identifiers
    for index, stimulus in enumerate(value):
        path = "$.stimuli[%d]" % index
        if not _require_fields(stimulus, path, fields, fields, errors):
            continue
        for key in fields - {"at"}:
            if not _nonempty_string(stimulus.get(key)):
                _error(errors, "TYPE", path + "." + key, "must be a non-empty string")
        _validate_duration(stimulus.get("at"), path + ".at", errors)
        stimulus_id = stimulus.get("stimulus_id")
        if _nonempty_string(stimulus_id):
            if stimulus_id in identifiers:
                _error(errors, "DUPLICATE_ID", path + ".stimulus_id", "stimulus ID must be unique")
            identifiers.add(stimulus_id)
    return identifiers


def _validate_events(
    value: Any,
    path: str,
    errors: List[Dict[str, str]],
    *,
    forbidden: bool
) -> List[Dict[str, Any]]:
    checked: List[Dict[str, Any]] = []
    fields = {
        "event_id",
        "event_type",
        "source",
        "target",
        "earliest",
        "deadline",
        "count",
        "order_after",
        "order_before",
        "correlation_id",
    }
    if not isinstance(value, list):
        _error(errors, "TYPE", path, "must be an array")
        return checked
    identifiers: Set[str] = set()
    for index, event in enumerate(value):
        item_path = "%s[%d]" % (path, index)
        if not _require_fields(event, item_path, fields, fields, errors):
            continue
        checked.append(event)
        for key in fields - {"earliest", "deadline", "count", "order_after", "order_before"}:
            if not _nonempty_string(event.get(key)):
                _error(errors, "TYPE", item_path + "." + key, "must be a non-empty string")
        _validate_duration(event.get("earliest"), item_path + ".earliest", errors)
        _validate_duration(event.get("deadline"), item_path + ".deadline", errors)
        _validate_count(event.get("count"), item_path + ".count", errors)
        for key in ("order_after", "order_before"):
            _validate_string_array(event.get(key), item_path + "." + key, errors)
        event_id = event.get("event_id")
        if _nonempty_string(event_id):
            if event_id in identifiers:
                _error(errors, "DUPLICATE_ID", item_path + ".event_id", "event ID must be unique")
            identifiers.add(event_id)
        count = event.get("count")
        if forbidden and isinstance(count, dict) and (count.get("min") != 0 or count.get("max") != 0):
            _error(errors, "FORBIDDEN_COUNT", item_path + ".count", "forbidden event count must be exactly zero")
    return checked


def _validate_timeouts(value: Any, errors: List[Dict[str, str]]) -> None:
    fields = {"timeout_id", "duration", "starts_at", "on_expiry"}
    identifiers: Set[str] = set()
    if not isinstance(value, list) or not value:
        _error(errors, "TYPE", "$.timeouts", "must be a non-empty array")
        return
    for index, timeout in enumerate(value):
        path = "$.timeouts[%d]" % index
        if not _require_fields(timeout, path, fields, fields, errors):
            continue
        for key in fields - {"duration"}:
            if not _nonempty_string(timeout.get(key)):
                _error(errors, "TYPE", path + "." + key, "must be a non-empty string")
        _validate_duration(timeout.get("duration"), path + ".duration", errors)
        timeout_id = timeout.get("timeout_id")
        if _nonempty_string(timeout_id):
            if timeout_id in identifiers:
                _error(errors, "DUPLICATE_ID", path + ".timeout_id", "timeout ID must be unique")
            identifiers.add(timeout_id)


def _validate_cleanup(value: Any, participants: Set[str], errors: List[Dict[str, str]]) -> None:
    fields = {"actions", "deadline", "expected_absent_participants"}
    if not _require_fields(value, "$.cleanup", fields, fields, errors):
        return
    _validate_string_array(value.get("actions"), "$.cleanup.actions", errors, minimum=1)
    _validate_duration(value.get("deadline"), "$.cleanup.deadline", errors)
    _validate_string_array(
        value.get("expected_absent_participants"),
        "$.cleanup.expected_absent_participants",
        errors,
    )
    if isinstance(value.get("expected_absent_participants"), list):
        for index, participant in enumerate(value["expected_absent_participants"]):
            if participant not in participants:
                _error(
                    errors,
                    "UNKNOWN_PARTICIPANT",
                    "$.cleanup.expected_absent_participants[%d]" % index,
                    "participant is not declared",
                )


def _validate_evidence(value: Any, errors: List[Dict[str, str]]) -> None:
    fields = {"required_artifacts", "synthetic_fixture_allowed", "acceptance_level"}
    if not _require_fields(value, "$.evidence", fields, fields, errors):
        return
    _validate_string_array(value.get("required_artifacts"), "$.evidence.required_artifacts", errors, minimum=1)
    if not isinstance(value.get("synthetic_fixture_allowed"), bool):
        _error(errors, "TYPE", "$.evidence.synthetic_fixture_allowed", "must be boolean")
    if value.get("acceptance_level") not in {"OFFLINE_SPEC", "FORMAL_SITL"}:
        _error(errors, "ENUM", "$.evidence.acceptance_level", "unsupported acceptance level")


def _validate_assertions(
    value: Any,
    participants: Set[str],
    sources: Set[str],
    errors: List[Dict[str, str]],
) -> None:
    fields = {"endpoint_contracts", "state_transitions", "participant_cardinality"}
    if not _require_fields(value, "$.assertions", fields, fields, errors):
        return
    endpoints = value.get("endpoint_contracts")
    endpoint_fields = {
        "topic",
        "message_type",
        "direction",
        "qos",
        "publisher_count",
        "required_source",
    }
    if not isinstance(endpoints, list):
        _error(errors, "TYPE", "$.assertions.endpoint_contracts", "must be an array")
    else:
        topics: Set[str] = set()
        qos_fields = {"reliability", "durability", "history", "depth"}
        for index, endpoint in enumerate(endpoints):
            path = "$.assertions.endpoint_contracts[%d]" % index
            if not _require_fields(endpoint, path, endpoint_fields, endpoint_fields, errors):
                continue
            topic = endpoint.get("topic")
            if not isinstance(topic, str) or not topic.startswith("/"):
                _error(errors, "TOPIC", path + ".topic", "must be an absolute topic name")
            elif topic in topics:
                _error(errors, "DUPLICATE_ID", path + ".topic", "endpoint topic must be unique")
            else:
                topics.add(topic)
            if not _nonempty_string(endpoint.get("message_type")):
                _error(errors, "TYPE", path + ".message_type", "must be a non-empty string")
            if endpoint.get("direction") not in {"publisher", "subscriber"}:
                _error(errors, "ENUM", path + ".direction", "must be publisher or subscriber")
            _validate_count(endpoint.get("publisher_count"), path + ".publisher_count", errors)
            required_source = endpoint.get("required_source")
            if required_source not in sources:
                _error(errors, "UNKNOWN_SOURCE", path + ".required_source", "source identity binding is missing")
            qos = endpoint.get("qos")
            if _require_fields(qos, path + ".qos", qos_fields, qos_fields, errors):
                if qos.get("reliability") not in {"best_effort", "reliable"}:
                    _error(errors, "ENUM", path + ".qos.reliability", "unsupported reliability")
                if qos.get("durability") not in {"volatile", "transient_local"}:
                    _error(errors, "ENUM", path + ".qos.durability", "unsupported durability")
                if qos.get("history") not in {"keep_last", "keep_all"}:
                    _error(errors, "ENUM", path + ".qos.history", "unsupported history")
                depth = qos.get("depth")
                if not isinstance(depth, int) or isinstance(depth, bool) or depth < 0:
                    _error(errors, "COUNT", path + ".qos.depth", "must be a non-negative integer")
    transitions = value.get("state_transitions")
    transition_fields = {"from", "to", "trigger", "deadline"}
    if not isinstance(transitions, list):
        _error(errors, "TYPE", "$.assertions.state_transitions", "must be an array")
    else:
        for index, transition in enumerate(transitions):
            path = "$.assertions.state_transitions[%d]" % index
            if not _require_fields(transition, path, transition_fields, transition_fields, errors):
                continue
            for key in transition_fields - {"deadline"}:
                if not _nonempty_string(transition.get(key)):
                    _error(errors, "TYPE", path + "." + key, "must be a non-empty string")
            _validate_duration(transition.get("deadline"), path + ".deadline", errors)
    cardinality = value.get("participant_cardinality")
    cardinality_fields = {"participant_id", "count"}
    if not isinstance(cardinality, list):
        _error(errors, "TYPE", "$.assertions.participant_cardinality", "must be an array")
    else:
        seen: Set[str] = set()
        for index, assertion in enumerate(cardinality):
            path = "$.assertions.participant_cardinality[%d]" % index
            if not _require_fields(assertion, path, cardinality_fields, cardinality_fields, errors):
                continue
            participant_id = assertion.get("participant_id")
            if participant_id not in participants:
                _error(errors, "UNKNOWN_PARTICIPANT", path + ".participant_id", "participant is not declared")
            elif participant_id in seen:
                _error(errors, "DUPLICATE_ID", path + ".participant_id", "cardinality assertion must be unique")
            else:
                seen.add(participant_id)
            _validate_count(assertion.get("count"), path + ".count", errors)


def _validate_fault(value: Any, dependencies: Set[str], errors: List[Dict[str, str]]) -> None:
    fields = {
        "injection_point",
        "at",
        "duration",
        "expected_fault_code",
        "detection_deadline",
        "expected_state",
        "forbidden_states",
        "automatic_recovery",
        "reset_conditions",
        "cleanup",
        "unimplemented_dependencies",
    }
    if not _require_fields(value, "$.fault_injection", fields, fields, errors):
        return
    for key in ("injection_point", "expected_fault_code", "expected_state"):
        if not _nonempty_string(value.get(key)):
            _error(errors, "TYPE", "$.fault_injection." + key, "must be a non-empty string")
    for key in ("at", "duration", "detection_deadline"):
        _validate_duration(value.get(key), "$.fault_injection." + key, errors)
    for key in ("forbidden_states", "reset_conditions", "cleanup"):
        _validate_string_array(value.get(key), "$.fault_injection." + key, errors, minimum=1)
    if not isinstance(value.get("automatic_recovery"), bool):
        _error(errors, "TYPE", "$.fault_injection.automatic_recovery", "must be boolean")
    unimplemented = value.get("unimplemented_dependencies")
    if not isinstance(unimplemented, list):
        _error(errors, "TYPE", "$.fault_injection.unimplemented_dependencies", "must be an array")
    else:
        for index, blocker in enumerate(unimplemented):
            path = "$.fault_injection.unimplemented_dependencies[%d]" % index
            if blocker not in ALLOWED_BLOCKERS:
                _error(errors, "DEPENDENCY", path, "unsupported blocker")
            elif blocker not in dependencies:
                _error(errors, "DEPENDENCY", path, "fault blocker must also appear in top-level dependencies")


def validate_scenario(document: Any, source_path: str = "<memory>") -> List[Dict[str, str]]:
    """Return stable validation errors; an empty list means offline validation passed."""
    errors: List[Dict[str, str]] = []
    if not isinstance(document, dict):
        return [{"code": "TYPE", "message": "scenario must be a JSON object", "path": "$"}]
    for field in sorted(CORE_FIELDS - {"fault_injection", "extensions"} - set(document)):
        _error(errors, "REQUIRED", "$." + field, "required field is missing")
    for field in sorted(set(document) - CORE_FIELDS):
        _error(errors, "UNKNOWN_FIELD", "$." + field, "field is not allowed")
    if document.get("schema_version") != SCHEMA_VERSION:
        _error(errors, "SCHEMA_VERSION", "$.schema_version", "must equal %s" % SCHEMA_VERSION)
    scenario_id = document.get("scenario_id")
    if not isinstance(scenario_id, str) or not SCENARIO_ID_RE.fullmatch(scenario_id):
        _error(errors, "SCENARIO_ID", "$.scenario_id", "must match SITL-(NORMAL|FAULT)-NNN")
    for field in ("title", "milestone", "initial_state"):
        if not _nonempty_string(document.get(field)):
            _error(errors, "TYPE", "$." + field, "must be a non-empty string")
    status = document.get("status")
    if status not in ALLOWED_STATUS:
        _error(errors, "STATUS", "$.status", "unsupported scenario status")
    for field in ("requirement_ids", "audit_ids", "preconditions", "forbidden_conditions", "limitations"):
        _validate_string_array(document.get(field), "$." + field, errors, minimum=1)
    dependencies = document.get("dependencies")
    dependency_set: Set[str] = set()
    if not isinstance(dependencies, list):
        _error(errors, "TYPE", "$.dependencies", "must be an array")
    else:
        for index, blocker in enumerate(dependencies):
            path = "$.dependencies[%d]" % index
            if blocker not in ALLOWED_BLOCKERS:
                _error(errors, "DEPENDENCY", path, "unsupported blocker")
            elif blocker in dependency_set:
                _error(errors, "DUPLICATE", path, "blocker must be unique")
            else:
                dependency_set.add(blocker)
    if status == "BLOCKED" and not dependency_set:
        _error(errors, "BLOCKER_REQUIRED", "$.dependencies", "BLOCKED scenario requires a blocker")
    _validate_profile(document.get("profile"), errors)
    participants = _validate_participants(document.get("participants"), errors)
    sources = _validate_source_identity(document.get("source_identity"), errors)
    _validate_stimuli(document.get("stimuli"), errors)
    expected = _validate_events(document.get("expected_events"), "$.expected_events", errors, forbidden=False)
    forbidden = _validate_events(document.get("forbidden_events"), "$.forbidden_events", errors, forbidden=True)
    expected_ids = {item.get("event_id") for item in expected if _nonempty_string(item.get("event_id"))}
    all_event_ids = expected_ids | {
        item.get("event_id") for item in forbidden if _nonempty_string(item.get("event_id"))
    }
    for collection_name, collection in (("expected_events", expected), ("forbidden_events", forbidden)):
        for index, event in enumerate(collection):
            for order_field in ("order_after", "order_before"):
                if isinstance(event.get(order_field), list):
                    for ref_index, reference in enumerate(event[order_field]):
                        if reference not in all_event_ids:
                            _error(
                                errors,
                                "UNKNOWN_EVENT_REFERENCE",
                                "$.%s[%d].%s[%d]" % (collection_name, index, order_field, ref_index),
                                "referenced event ID is not declared",
                            )
                        if reference == event.get("event_id"):
                            _error(
                                errors,
                                "SELF_REFERENCE",
                                "$.%s[%d].%s[%d]" % (collection_name, index, order_field, ref_index),
                                "event cannot order relative to itself",
                            )
    _validate_timeouts(document.get("timeouts"), errors)
    _validate_cleanup(document.get("cleanup"), participants, errors)
    _validate_evidence(document.get("evidence"), errors)
    _validate_assertions(document.get("assertions"), participants, sources, errors)
    if isinstance(scenario_id, str) and scenario_id.startswith("SITL-FAULT-"):
        if "fault_injection" not in document:
            _error(errors, "REQUIRED", "$.fault_injection", "fault scenarios require injection details")
        else:
            _validate_fault(document.get("fault_injection"), dependency_set, errors)
    elif "fault_injection" in document:
        _error(errors, "FAULT_ONLY_FIELD", "$.fault_injection", "only fault scenarios may define fault injection")
    if "extensions" in document and not isinstance(document.get("extensions"), dict):
        _error(errors, "TYPE", "$.extensions", "must be an object")
    _walk_forbidden_keys(document, "$", errors)
    _walk_safety_strings(document, "$", errors)
    return sorted(errors, key=lambda item: (item["path"], item["code"], item["message"]))


def validate_document(document: Any, source_path: Optional[str] = None) -> List[Dict[str, str]]:
    """Compatibility entry point for catalog validation."""
    return validate_scenario(document, source_path or "<memory>")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _summary(path: Path, errors: List[Dict[str, str]]) -> Dict[str, Any]:
    return {
        "errors": errors,
        "input": str(path),
        "schema_version": SCHEMA_VERSION,
        "status": "PASS" if not errors else "FAIL",
        "tool": "validate_scenario",
        "validation_scope": "OFFLINE_SPEC_ONLY",
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate one machine-readable SITL scenario offline."
    )
    parser.add_argument("--scenario", required=True, type=Path, help="input scenario JSON path")
    parser.add_argument("--output", type=Path, help="optional JSON summary output path")
    args = parser.parse_args(argv)
    try:
        document = load_json(args.scenario)
        errors = validate_scenario(document, str(args.scenario))
        summary = _summary(args.scenario, errors)
        encoded = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(encoded, encoding="utf-8")
        sys.stdout.write(encoded)
        return 0 if not errors else 2
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        summary = {
            "errors": [{"code": "INPUT_ERROR", "message": str(exc), "path": str(args.scenario)}],
            "input": str(args.scenario),
            "schema_version": SCHEMA_VERSION,
            "status": "FAIL",
            "tool": "validate_scenario",
            "validation_scope": "OFFLINE_SPEC_ONLY",
        }
        sys.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        return 3


if __name__ == "__main__":
    sys.exit(main())
