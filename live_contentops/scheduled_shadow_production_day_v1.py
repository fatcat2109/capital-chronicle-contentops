"""One injected, read-only scheduled production-day shadow cycle.

This is a deterministic composition seam, not a scheduler or a publication owner. It consumes
the existing source, BrowserOS, X-ingestion, editorial, package, destination-readback, and
coordinator recovery contracts and returns one immutable receipt without writing the store or
calling a model/provider/browser/transport.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from live_contentops.destination_transport_registry_v1 import (
    V1_REQUIRED_DERIVATIVE_DESTINATIONS,
)


SCHEMA_VERSION = "contentops.scheduled_shadow_production_day.v1"
SHADOW_CONFIRMED = "SHADOW_CONFIRMED"
DISABLED_BY_DEFAULT = "DISABLED_BY_DEFAULT"
MISSING = "MISSING"
MISMATCH = "MISMATCH"
HUMAN_REQUIRED = "HUMAN_REQUIRED"
UNKNOWN_WRITE = "UNKNOWN_WRITE"
FAIL_CLOSED = "FAIL_CLOSED"

CROSS_PLANE_INPUT_SCHEMA = "CapitalChronicleCrossPlaneShadowCycleInputV1"
CROSS_PLANE_RECEIPT_SCHEMA = "contentops.cross_plane_shadow_cycle_receipt.v1"
CROSS_PLANE_CANONICALIZATION = "JSON_SORT_KEYS_COMPACT_ASCII_UTF8_NO_FLOAT_NAN"
CROSS_PLANE_CLASSIFICATIONS = frozenset(
    {
        "NONE",
        "SOURCE_HEAD_MISMATCH",
        "PACKET_HASH_MISMATCH",
        "RECEIPT_STALE",
        "PROOF_LAYER_MISMATCH",
        "TASK_STATE_MISMATCH",
        "UNKNOWN_WRITE",
        "AUTHORITY_FLAG",
        "AMBIGUOUS",
        "NOT_VERIFIED",
    }
)
CROSS_PLANE_AUTHORITY_FLAGS = (
    "main_authority",
    "public_write",
    "runtime_proven",
    "provider_call",
    "model_call",
    "network_call",
    "external_effect",
)
CROSS_PLANE_ZERO_EFFECT_KEYS = (
    "scheduler_started",
    "durable_store_write_count",
    "database_mutation",
    "model_call_count",
    "provider_call_count",
    "browser_action_count",
    "public_write_performed",
    "publication_authority",
)
_CROSS_PLANE_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

POST_MERGE_REPLAY_RECEIPT_SCHEMA = "contentops.cross_plane_shadow_cycle_replay_receipt.v1"
POST_MERGE_ARTIFACT_COMMIT = "a3bdedf29e4fc66f917d7fcf1f458821a63d043b"
POST_MERGE_ARTIFACT_PATH = "tests/fixtures/cross_plane_shadow_cycle_post_merge_current_real_v1.json"
POST_MERGE_ARTIFACT_BYTES = 18830
POST_MERGE_ARTIFACT_SHA256_PREFIX = "4b208204"
POST_MERGE_INPUT_SHA256_PREFIX = "124311ccd5"
POST_MERGE_MAIN_SOURCE_REPOSITORY = "fatcat2109/capital-chronicle-main"
POST_MERGE_MAIN_SOURCE_REF = "main"
POST_MERGE_MAIN_SOURCE_HEAD = "8f66238d320062e9258c893d59d2293253655f94"
POST_MERGE_CONTENTOPS_REPOSITORY = "fatcat2109/capital-chronicle-contentops"
POST_MERGE_CONTENTOPS_REF = "master"
POST_MERGE_CONTENTOPS_HEAD = "aa5dbda6c73a4f53683365ce26c6323ec57298a9"
POST_MERGE_PRODUCER_COMMIT = "e5dd0a51c6b26fd22c51400784e883209aa1687d"
POST_MERGE_PRODUCER_PATH = "live_contentops/host_readiness_observation_consumer_v1.py"
POST_MERGE_ALLOWED_REPLAY_CLASSIFICATIONS = frozenset(
    {
        "NONE",
        "SOURCE_HEAD_MISMATCH",
        "PACKET_HASH_MISMATCH",
        "RECEIPT_STALE",
        "PROOF_LAYER_MISMATCH",
        "TASK_STATE_MISMATCH",
        "UNKNOWN_WRITE",
        "AUTHORITY_FLAG",
        "AMBIGUOUS",
        "NOT_VERIFIED",
    }
)
_POST_MERGE_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_POST_MERGE_AUDIT_KEYS = frozenset(
    {
        "secret_scan_status",
        "secrets_removed",
        "secret_material_detected",
        "session_material_read",
        "credential_or_session_material_read",
    }
)
_POST_MERGE_SENSITIVE_KEY_RE = re.compile(
    r"(?i)(?:^|_)(?:access[_-]?token|refresh[_-]?token|cookie|password|secret|authorization|"
    r"api[_-]?key|private[_-]?key|session[_-]?token|webhook[_-]?url)(?:$|_)"
)
_POST_MERGE_SECRET_VALUE_RE = re.compile(
    r"(?i)(?:bearer\s+[A-Za-z0-9._~+/=-]{8,}|(?:sk|pk|rk)-[A-Za-z0-9_-]{12,}|"
    r"(?:access[_-]?token|refresh[_-]?token|api[_-]?key|password|secret|cookie)\s*[:=]\s*[^\s,;]{8,})"
)


def _hash(value: Any) -> str:
    material = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return sha256(material.encode("utf-8")).hexdigest()


def cross_plane_input_sha256(value: Mapping[str, Any]) -> str:
    """Hash the Main input using the portable, strict canonical JSON boundary."""

    body = {
        key: item for key, item in value.items() if key != "input_sha256"
    }
    material = json.dumps(
        body,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return sha256(material).hexdigest()


def cross_plane_receipt_sha256(value: Mapping[str, Any]) -> str:
    """Hash one ContentOps cross-plane receipt without its self-hash field."""

    body = {
        key: item for key, item in value.items() if key != "receipt_sha256"
    }
    material = json.dumps(
        body,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return sha256(material).hexdigest()


def _cross_plane_parse_utc(value: Any, *, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field}_invalid") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field}_timezone_missing")
    return parsed.astimezone(timezone.utc)


def _cross_plane_observed_facts(receipt: Mapping[str, Any]) -> dict[str, Any]:
    observation = receipt.get("observation") if isinstance(receipt.get("observation"), Mapping) else {}
    source = observation.get("source") if isinstance(observation.get("source"), Mapping) else {}
    tasks = source.get("scheduler_tasks") if isinstance(source.get("scheduler_tasks"), Mapping) else {}
    task_rows = tasks.get("tasks") if isinstance(tasks.get("tasks"), Sequence) else []
    task_states = [
        {
            "name": str(row.get("name") or ""),
            "state_text": str(row.get("state_text") or ""),
            "state_value": row.get("state_value"),
        }
        for row in task_rows
        if isinstance(row, Mapping)
    ]
    identity = source.get("identity_shadow") if isinstance(source.get("identity_shadow"), Mapping) else {}
    destination = source.get("destination_shadow") if isinstance(source.get("destination_shadow"), Mapping) else {}
    store = source.get("store") if isinstance(source.get("store"), Mapping) else {}
    return {
        "task_states": task_states,
        "identity_status": str(identity.get("status") or ""),
        "destination_status": str(destination.get("status") or ""),
        "store": {
            "status": str(store.get("status") or ""),
            "integrity_check": store.get("integrity_check"),
            "foreign_key_violation_count": store.get("foreign_key_violation_count"),
            "unknown_write_count": store.get("unknown_write_count"),
        },
        "freshness_status": str(receipt.get("freshness", {}).get("status") or ""),
        "zero_effect": {
            key: receipt.get("zero_effect", {}).get(key)
            for key in CROSS_PLANE_ZERO_EFFECT_KEYS
        },
    }


def _cross_plane_unknown_write(value: Any) -> bool:
    if isinstance(value, Mapping):
        if bool(value.get("unknown_write")) or str(value.get("status") or "") == UNKNOWN_WRITE:
            return True
        return any(_cross_plane_unknown_write(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_cross_plane_unknown_write(item) for item in value)
    return False


def _cross_plane_base_receipt(
    input_value: Mapping[str, Any],
    *,
    input_hash: str | None,
    classification: str,
    blocker: str,
    next_action: str,
    portable_receipt: Mapping[str, Any] | None,
    production_day_receipt: Mapping[str, Any] | None,
) -> dict[str, Any]:
    portable_source = (
        portable_receipt.get("source")
        if isinstance(portable_receipt, Mapping)
        and isinstance(portable_receipt.get("source"), Mapping)
        else {}
    )
    input_source = input_value.get("source") if isinstance(input_value.get("source"), Mapping) else {}
    clock_state = input_value.get("clock_state") if isinstance(input_value.get("clock_state"), Mapping) else {}
    output = {
        "schema_version": CROSS_PLANE_RECEIPT_SCHEMA,
        "canonicalization": CROSS_PLANE_CANONICALIZATION,
        "status": "RECONCILED" if classification == "NONE" else "BLOCKED",
        "immutable_receipt": True,
        "shadow_only": True,
        "input_sha256": input_hash,
        "portable_receipt_sha256": (
            portable_receipt.get("portable_receipt_sha256")
            if isinstance(portable_receipt, Mapping)
            else None
        ),
        "production_day_receipt_sha256": (
            production_day_receipt.get("production_day_receipt_sha256")
            if isinstance(production_day_receipt, Mapping)
            else None
        ),
        "source": {
            "main_repository": input_source.get("repository"),
            "main_ref": input_source.get("ref"),
            "main_head": input_source.get("head"),
            "contentops_repository": portable_source.get("repository"),
            "contentops_ref": portable_source.get("branch"),
            "contentops_head": portable_source.get("head"),
            "portable_producer_schema": portable_source.get("producer_schema"),
            "portable_producer_commit": input_value.get("portable_producer", {}).get("commit")
            if isinstance(input_value.get("portable_producer"), Mapping)
            else None,
        },
        "clocks": {
            "input_observed_at_utc": clock_state.get("observed_at_utc"),
            "input_known_at_utc": clock_state.get("known_at_utc"),
            "input_as_of_utc": clock_state.get("as_of_utc"),
            "portable_observed_at_utc": (
                portable_receipt.get("observation", {}).get("observed_at_utc")
                if isinstance(portable_receipt, Mapping)
                else None
            ),
            "portable_known_at_utc": (
                portable_receipt.get("observation", {}).get("known_at_utc")
                if isinstance(portable_receipt, Mapping)
                else None
            ),
            "portable_as_of_utc": (
                portable_receipt.get("freshness", {}).get("as_of_utc")
                if isinstance(portable_receipt, Mapping)
                else None
            ),
            "freshness_status": (
                portable_receipt.get("freshness", {}).get("status")
                if isinstance(portable_receipt, Mapping)
                else None
            ),
        },
        "classification": classification,
        "proof_axes": {
            "input_validated": classification == "NONE",
            "portable_receipt_validated": classification == "NONE",
            "shadow_composition": production_day_receipt is not None,
            "runtime_proven": False,
            "publicly_proven": False,
        },
        "current_facts": _cross_plane_observed_facts(portable_receipt or {}),
        "zero_effect": {
            key: (portable_receipt or {}).get("zero_effect", {}).get(key, False)
            for key in CROSS_PLANE_ZERO_EFFECT_KEYS
        },
        "runtime_proven": False,
        "publicly_proven": False,
        "blocker": blocker,
        "next": next_action,
        "receipt_sha256": None,
    }
    output["receipt_sha256"] = cross_plane_receipt_sha256(output)
    return output


def reconcile_cross_plane_shadow_cycle(
    input_value: Mapping[str, Any],
    *,
    shadow_runner: Callable[..., Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Consume one Main cross-plane input and compose one read-only shadow cycle.

    This adapter is deliberately downstream of Main authority.  It validates only the supplied
    bytes and calls the existing injected scheduled-shadow seam; it never probes, starts, writes,
    publishes, or grants runtime/public authority.
    """

    if not isinstance(input_value, Mapping):
        return _cross_plane_base_receipt(
            {}, input_hash=None, classification="NOT_VERIFIED",
            blocker="cross_plane_input_not_mapping",
            next_action="STOP_AND_REISSUE_CANONICAL_MAIN_INPUT",
            portable_receipt=None, production_day_receipt=None,
        )
    supplied_hash = str(input_value.get("input_sha256") or "")
    computed_hash = cross_plane_input_sha256(input_value)
    portable_receipt = input_value.get("portable_receipt")
    if not isinstance(portable_receipt, Mapping):
        return _cross_plane_base_receipt(
            input_value, input_hash=supplied_hash or None, classification="NOT_VERIFIED",
            blocker="portable_receipt_missing",
            next_action="STOP_AND_REISSUE_CANONICAL_MAIN_INPUT",
            portable_receipt=None, production_day_receipt=None,
        )
    classification = "NONE"
    blockers: list[str] = []
    if input_value.get("schema_version") != CROSS_PLANE_INPUT_SCHEMA:
        blockers.append("cross_plane_schema_invalid")
    if input_value.get("canonicalization") != CROSS_PLANE_CANONICALIZATION:
        blockers.append("cross_plane_canonicalization_invalid")
    main_source = input_value.get("source") if isinstance(input_value.get("source"), Mapping) else {}
    if any(not main_source.get(key) for key in ("repository", "ref", "head")):
        blockers.append("cross_plane_main_source_incomplete")
    if not _CROSS_PLANE_SHA256_RE.fullmatch(supplied_hash) or supplied_hash != computed_hash:
        blockers.append("cross_plane_input_hash_invalid")
    if blockers:
        return _cross_plane_base_receipt(
            input_value,
            input_hash=None,
            classification="NOT_VERIFIED",
            blocker=";".join(blockers),
            next_action="STOP_AND_REISSUE_CANONICAL_MAIN_INPUT",
            portable_receipt=None,
            production_day_receipt=None,
        )
    try:
        from live_contentops.host_readiness_observation_consumer_v1 import (
            validate_portable_host_readiness_receipt,
        )
        portable_blockers = validate_portable_host_readiness_receipt(portable_receipt)
    except (TypeError, ValueError, AttributeError) as exc:
        portable_blockers = [f"portable_receipt_validator_error:{type(exc).__name__}"]
    if portable_blockers:
        blockers.extend(f"portable:{item}" for item in portable_blockers)
        portable_classification = str(portable_receipt.get("classification") or "")
        if portable_classification == "STALE":
            classification = "RECEIPT_STALE"
        elif portable_classification == "AMBIGUOUS":
            classification = "AMBIGUOUS"
        else:
            classification = "NOT_VERIFIED"
        return _cross_plane_base_receipt(
            input_value,
            input_hash=supplied_hash,
            classification=classification,
            blocker=";".join(dict.fromkeys(blockers)),
            next_action="STOP_RETRY_READBACK_RECONCILE_AND_REISSUE_AFTER_BLOCKER_REPAIR",
            portable_receipt=None,
            production_day_receipt=None,
        )

    observation = portable_receipt.get("observation") if isinstance(portable_receipt.get("observation"), Mapping) else {}
    observation_source = observation.get("source") if isinstance(observation.get("source"), Mapping) else {}
    portable_source = portable_receipt.get("source") if isinstance(portable_receipt.get("source"), Mapping) else {}
    receipt_freshness = portable_receipt.get("freshness") if isinstance(portable_receipt.get("freshness"), Mapping) else {}
    if any(not observation.get(key) for key in ("observation_id", "observed_at_utc", "known_at_utc")):
        classification = "NOT_VERIFIED"
        blockers.append("portable_observation_identity_or_clock_missing")
    if any(
        key not in receipt_freshness or receipt_freshness.get(key) is None
        for key in ("as_of_utc", "known_at_utc", "age_seconds", "max_age_seconds", "status")
    ):
        classification = "NOT_VERIFIED"
        blockers.append("portable_freshness_contract_incomplete")
    for field in ("repository", "branch", "head", "producer_schema"):
        if not portable_source.get(field):
            classification = "SOURCE_HEAD_MISMATCH"
            blockers.append(f"portable_source_{field}_missing")
    if portable_source.get("head") and not re.fullmatch(r"[0-9a-f]{40,64}", str(portable_source.get("head"))):
        classification = "SOURCE_HEAD_MISMATCH"
        blockers.append("portable_source_head_format_invalid")
    for key in ("main_packet_logical_hash", "v3_packet_logical_hash", "shadow_receipt_sha256"):
        if not _CROSS_PLANE_SHA256_RE.fullmatch(str((portable_receipt.get("packet_hashes") or {}).get(key) or "")):
            classification = "PACKET_HASH_MISMATCH"
            blockers.append(f"portable_packet_hash_invalid:{key}")
    portable_zero_effect = portable_receipt.get("zero_effect") if isinstance(portable_receipt.get("zero_effect"), Mapping) else {}
    missing_zero_effect = [key for key in CROSS_PLANE_ZERO_EFFECT_KEYS if key not in portable_zero_effect]
    if missing_zero_effect:
        classification = "NOT_VERIFIED"
        blockers.append("portable_zero_effect_contract_incomplete:" + ",".join(missing_zero_effect))
    if any(portable_zero_effect.get(key) not in (False, 0, None) for key in CROSS_PLANE_ZERO_EFFECT_KEYS):
        classification = "UNKNOWN_WRITE"
        blockers.append("portable_zero_effect_not_zero")
    if (observation_source.get("store") or {}).get("unknown_write_count") not in (0, None):
        classification = "UNKNOWN_WRITE"
        blockers.append("portable_store_unknown_write_count_nonzero")

    bindings = input_value.get("bindings") if isinstance(input_value.get("bindings"), Mapping) else {}
    expected_source = bindings.get("portable_source") if isinstance(bindings.get("portable_source"), Mapping) else {}
    if any(portable_source.get(key) != expected_source.get(key) for key in ("repository", "branch", "head")):
        classification = "SOURCE_HEAD_MISMATCH"
        blockers.append("portable_source_repository_ref_head_mismatch")
    expected_producer = bindings.get("portable_producer") if isinstance(bindings.get("portable_producer"), Mapping) else {}
    supplied_producer = input_value.get("portable_producer") if isinstance(input_value.get("portable_producer"), Mapping) else {}
    if (
        portable_source.get("producer_schema") != expected_producer.get("schema")
        or supplied_producer.get("schema") != portable_receipt.get("schema_version")
        or supplied_producer.get("commit") != expected_producer.get("commit")
    ):
        classification = "SOURCE_HEAD_MISMATCH"
        blockers.append("portable_producer_schema_or_commit_mismatch")

    packet_hashes = portable_receipt.get("packet_hashes") if isinstance(portable_receipt.get("packet_hashes"), Mapping) else {}
    expected_packets = bindings.get("packet_hashes") if isinstance(bindings.get("packet_hashes"), Mapping) else {}
    if any(packet_hashes.get(key) != expected_packets.get(key) for key in ("main_packet_logical_hash", "v3_packet_logical_hash", "shadow_receipt_sha256")):
        classification = "PACKET_HASH_MISMATCH"
        blockers.append("packet_or_shadow_hash_mismatch")
    main_packet = input_value.get("main_packet") if isinstance(input_value.get("main_packet"), Mapping) else {}
    if main_packet and main_packet.get("logical_hash") != packet_hashes.get("main_packet_logical_hash"):
        classification = "PACKET_HASH_MISMATCH"
        blockers.append("main_packet_logical_hash_mismatch")
    boundary_hashes = input_value.get("boundary_hashes") if isinstance(input_value.get("boundary_hashes"), Mapping) else {}
    expected_boundaries = bindings.get("boundary_hashes") if isinstance(bindings.get("boundary_hashes"), Mapping) else {}
    if boundary_hashes and dict(boundary_hashes) != dict(expected_boundaries):
        classification = "PACKET_HASH_MISMATCH"
        blockers.append("main_boundary_hashes_mismatch")

    freshness = portable_receipt.get("freshness") if isinstance(portable_receipt.get("freshness"), Mapping) else {}
    if freshness.get("status") != "FRESH":
        classification = "RECEIPT_STALE"
        blockers.append("portable_receipt_not_fresh")
    clock_state = input_value.get("clock_state") if isinstance(input_value.get("clock_state"), Mapping) else {}
    actual_clocks = {
        "observed_at_utc": (portable_receipt.get("observation") or {}).get("observed_at_utc"),
        "known_at_utc": (portable_receipt.get("observation") or {}).get("known_at_utc"),
        "as_of_utc": freshness.get("as_of_utc"),
        "freshness_status": freshness.get("status"),
    }
    if clock_state and dict(clock_state) != actual_clocks:
        classification = "RECEIPT_STALE"
        blockers.append("portable_clock_or_freshness_binding_mismatch")
    else:
        try:
            observed_dt = _cross_plane_parse_utc(actual_clocks["observed_at_utc"], field="portable_observed_at_utc")
            known_dt = _cross_plane_parse_utc(actual_clocks["known_at_utc"], field="portable_known_at_utc")
            as_of_dt = _cross_plane_parse_utc(actual_clocks["as_of_utc"], field="portable_as_of_utc")
            if known_dt < observed_dt or as_of_dt < known_dt:
                classification = "RECEIPT_STALE"
                blockers.append("portable_clock_order_invalid")
        except ValueError as exc:
            classification = "NOT_VERIFIED"
            blockers.append(str(exc))

    expected_proof = bindings.get("proof_layers") if isinstance(bindings.get("proof_layers"), Mapping) else {}
    if expected_proof and dict(portable_receipt.get("proof_layers") or {}) != dict(expected_proof):
        classification = "PROOF_LAYER_MISMATCH"
        blockers.append("portable_proof_layers_mismatch")

    expected_facts = input_value.get("current_facts") if isinstance(input_value.get("current_facts"), Mapping) else {}
    actual_facts = _cross_plane_observed_facts(portable_receipt)
    if expected_facts and dict(expected_facts) != actual_facts:
        classification = "TASK_STATE_MISMATCH"
        blockers.append("portable_current_task_identity_destination_store_facts_mismatch")

    if _cross_plane_unknown_write(input_value):
        classification = "UNKNOWN_WRITE"
        blockers.append("unknown_write_stop_retry_readback_reconcile")

    authority_flags = input_value.get("authority_flags") if isinstance(input_value.get("authority_flags"), Mapping) else {}
    flagged = [key for key in CROSS_PLANE_AUTHORITY_FLAGS if authority_flags.get(key) is True]
    missing_flags = [key for key in CROSS_PLANE_AUTHORITY_FLAGS if key not in authority_flags]
    if missing_flags:
        classification = "AUTHORITY_FLAG"
        blockers.append("main_authority_or_external_effect_flag_missing:" + ",".join(missing_flags))
    if flagged:
        classification = "AUTHORITY_FLAG"
        blockers.append("main_authority_or_external_effect_flag_true:" + ",".join(flagged))

    portable_classification = str(portable_receipt.get("classification") or "")
    if not blockers and portable_classification == "AMBIGUOUS":
        classification = "AMBIGUOUS"
        blockers.append("portable_observation_ambiguous")
    elif not blockers and portable_classification not in {"HOST_OBSERVED", "RUNTIME_PROVEN", "PUBLICLY_PROVEN"}:
        classification = "NOT_VERIFIED"
        blockers.append("portable_observation_not_verified")
    if blockers and classification == "NONE":
        classification = "NOT_VERIFIED"

    production_day_receipt: Mapping[str, Any] | None = None
    if classification == "NONE":
        components = input_value.get("shadow_components")
        if not isinstance(components, Mapping):
            classification = "NOT_VERIFIED"
            blockers.append("shadow_components_missing")
        else:
            runner = shadow_runner or run_scheduled_shadow_production_day
            try:
                production_day_receipt = runner(enabled=True, **dict(components))
            except (OSError, RuntimeError, TimeoutError, TypeError, ValueError) as exc:
                classification = "NOT_VERIFIED"
                blockers.append(f"shadow_composition_exception:{type(exc).__name__}")
            if production_day_receipt is not None and production_day_receipt.get("status") != SHADOW_CONFIRMED:
                classification = (
                    "UNKNOWN_WRITE"
                    if production_day_receipt.get("status") == UNKNOWN_WRITE
                    else "NOT_VERIFIED"
                )
                blockers.append(
                    "scheduled_shadow_not_confirmed:"
                    + str(production_day_receipt.get("status") or "MISSING")
                )
    if classification == "NONE" and not production_day_receipt:
        classification = "NOT_VERIFIED"
        blockers.append("production_day_receipt_missing")
    blocker = ";".join(dict.fromkeys(blockers)) or None
    next_action = (
        "RECONCILED_SHADOW_ONLY_NO_RUNTIME_OR_PUBLIC_PROMOTION"
        if classification == "NONE"
        else "STOP_RETRY_READBACK_RECONCILE_AND_REISSUE_AFTER_BLOCKER_REPAIR"
    )
    return _cross_plane_base_receipt(
        input_value,
        input_hash=supplied_hash if supplied_hash == computed_hash else None,
        classification=classification,
        blocker=blocker,
        next_action=next_action,
        portable_receipt=None if portable_blockers else portable_receipt,
        production_day_receipt=production_day_receipt,
    )


def _post_merge_walk_secret(value: Any, *, path: str = "root") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if (
                _POST_MERGE_SENSITIVE_KEY_RE.search(key_text)
                and key_text.casefold() not in _POST_MERGE_AUDIT_KEYS
            ):
                raise ValueError(f"secret_material:{path}.{key_text}")
            _post_merge_walk_secret(item, path=f"{path}.{key_text}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _post_merge_walk_secret(item, path=f"{path}[{index}]")
    elif isinstance(value, str) and _POST_MERGE_SECRET_VALUE_RE.search(value):
        raise ValueError(f"secret_material:{path}")


def _post_merge_hash_without(value: Mapping[str, Any], field: str) -> str:
    body = {key: item for key, item in value.items() if key != field}
    return sha256(
        json.dumps(
            body,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _post_merge_receipt_base(
    *,
    artifact_bytes: bytes | None,
    input_value: Mapping[str, Any] | None,
    input_hash: str | None,
    artifact_status: str,
    classification: str,
    blockers: Sequence[str],
    production_day_receipt: Mapping[str, Any] | None,
) -> dict[str, Any]:
    portable = input_value.get("portable_receipt") if isinstance(input_value, Mapping) else None
    portable = portable if isinstance(portable, Mapping) else {}
    portable_source = portable.get("source") if isinstance(portable.get("source"), Mapping) else {}
    source = input_value.get("source") if isinstance(input_value, Mapping) and isinstance(input_value.get("source"), Mapping) else {}
    clock_state = input_value.get("clock_state") if isinstance(input_value, Mapping) and isinstance(input_value.get("clock_state"), Mapping) else {}
    current_facts = _cross_plane_observed_facts(portable) if portable else {}
    packet_hashes = dict(portable.get("packet_hashes") or {}) if portable else {}
    boundary_hashes = dict(input_value.get("boundary_hashes") or {}) if isinstance(input_value, Mapping) else {}
    zero_effect = dict(input_value.get("zero_effect_flags") or {}) if isinstance(input_value, Mapping) else {}
    artifact_sha256 = sha256(artifact_bytes).hexdigest() if artifact_bytes is not None else None
    output: dict[str, Any] = {
        "schema_version": POST_MERGE_REPLAY_RECEIPT_SCHEMA,
        "canonicalization": CROSS_PLANE_CANONICALIZATION,
        "status": "RECONCILED" if classification == "NONE" else "BLOCKED",
        "immutable_receipt": True,
        "replay_only": True,
        "artifact": {
            "repository": "fatcat2109/Headline-Raw-data-json",
            "ref": "main",
            "commit": POST_MERGE_ARTIFACT_COMMIT,
            "path": POST_MERGE_ARTIFACT_PATH,
            "bytes": len(artifact_bytes) if artifact_bytes is not None else None,
            "sha256": artifact_sha256,
            "expected_bytes": POST_MERGE_ARTIFACT_BYTES,
            "expected_sha256_prefix": POST_MERGE_ARTIFACT_SHA256_PREFIX,
            "status": artifact_status,
        },
        "input_sha256": input_hash,
        "portable_receipt_sha256": portable.get("portable_receipt_sha256"),
        "production_day_receipt_sha256": (
            production_day_receipt.get("production_day_receipt_sha256")
            if isinstance(production_day_receipt, Mapping)
            else None
        ),
        "source": {
            "main_repository": source.get("repository"),
            "main_ref": source.get("ref"),
            "main_head": source.get("head"),
            "contentops_repository": portable_source.get("repository"),
            "contentops_ref": portable_source.get("branch"),
            "contentops_head": portable_source.get("head"),
            "portable_producer_schema": portable_source.get("producer_schema"),
            "portable_producer_commit": (
                input_value.get("portable_producer", {}).get("commit")
                if isinstance(input_value, Mapping)
                and isinstance(input_value.get("portable_producer"), Mapping)
                else None
            ),
        },
        "clocks": {
            "observed_at_utc": clock_state.get("observed_at_utc"),
            "known_at_utc": clock_state.get("known_at_utc"),
            "as_of_utc": clock_state.get("as_of_utc"),
            "freshness_status": clock_state.get("freshness_status"),
        },
        "classification": classification,
        "proof_axes": {
            "artifact_readback": artifact_status == "SEALED_MATCH",
            "input_validated": input_hash is not None,
            "portable_receipt_validated": bool(portable),
            "shadow_composition": production_day_receipt is not None,
            "runtime_proven": False,
            "publicly_proven": False,
        },
        "packet_hashes": packet_hashes,
        "boundary_hashes": boundary_hashes,
        "current_facts": current_facts,
        "zero_effect_flags": zero_effect,
        "runtime_proven": False,
        "publicly_proven": False,
        "blockers": list(dict.fromkeys(str(item) for item in blockers)),
        "next": "HAND_REPLAY_RECEIPT_HASH_TO_MAIN_FOR_NEXT_RECONCILIATION",
        "receipt_sha256": None,
    }
    output["receipt_sha256"] = cross_plane_receipt_sha256(output)
    return output


def _post_merge_payload_bytes(payload: Any) -> tuple[bytes, dict[str, Any]]:
    if isinstance(payload, Mapping):
        value = dict(payload)
        raw = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        return raw, value
    if isinstance(payload, (bytes, bytearray)):
        raw = bytes(payload)
    else:
        raw = Path(str(payload)).read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("post_merge_input_json_invalid") from exc
    if not isinstance(value, Mapping):
        raise ValueError("post_merge_input_not_mapping")
    return raw, dict(value)


def _post_merge_validate_contract(value: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if value.get("schema_version") != "CapitalChronicleCrossPlaneShadowCycleInputV1":
        blockers.append("post_merge_schema_invalid")
    if value.get("version") != "1.0.0-post-merge":
        blockers.append("post_merge_version_invalid")
    if value.get("canonicalization") != CROSS_PLANE_CANONICALIZATION:
        blockers.append("post_merge_canonicalization_invalid")
    supplied_hash = str(value.get("input_sha256") or "")
    if not _CROSS_PLANE_SHA256_RE.fullmatch(supplied_hash) or supplied_hash != cross_plane_input_sha256(value):
        blockers.append("post_merge_input_hash_invalid")
    source = value.get("source") if isinstance(value.get("source"), Mapping) else {}
    if (
        source.get("repository") != POST_MERGE_MAIN_SOURCE_REPOSITORY
        or source.get("ref") != POST_MERGE_MAIN_SOURCE_REF
        or source.get("head") != POST_MERGE_MAIN_SOURCE_HEAD
        or not _POST_MERGE_SHA1_RE.fullmatch(str(source.get("head") or ""))
    ):
        blockers.append("main_source_head_mismatch")
    provenance = value.get("post_merge_provenance") if isinstance(value.get("post_merge_provenance"), Mapping) else {}
    if (
        provenance.get("contentops_repository") != POST_MERGE_CONTENTOPS_REPOSITORY
        or provenance.get("contentops_ref") != POST_MERGE_CONTENTOPS_REF
        or provenance.get("contentops_merged_head") != POST_MERGE_CONTENTOPS_HEAD
        or provenance.get("portable_producer_commit") != POST_MERGE_PRODUCER_COMMIT
    ):
        blockers.append("contentops_source_head_or_producer_mismatch")
    portable = value.get("portable_receipt") if isinstance(value.get("portable_receipt"), Mapping) else {}
    try:
        from live_contentops.host_readiness_observation_consumer_v1 import (
            validate_portable_host_readiness_receipt,
        )
        blockers.extend(f"portable:{item}" for item in validate_portable_host_readiness_receipt(portable))
    except (TypeError, ValueError, AttributeError) as exc:
        blockers.append(f"portable_validator_error:{type(exc).__name__}")
    portable_source = portable.get("source") if isinstance(portable.get("source"), Mapping) else {}
    if (
        portable_source.get("repository") != POST_MERGE_CONTENTOPS_REPOSITORY
        or portable_source.get("branch") != POST_MERGE_CONTENTOPS_REF
        or portable_source.get("head") != POST_MERGE_CONTENTOPS_HEAD
        or portable_source.get("producer_schema") != "contentops.current_host_readiness_observation.v1"
    ):
        blockers.append("portable_source_head_or_schema_mismatch")
    producer = value.get("portable_producer") if isinstance(value.get("portable_producer"), Mapping) else {}
    if (
        producer.get("commit") != POST_MERGE_PRODUCER_COMMIT
        or producer.get("path") != POST_MERGE_PRODUCER_PATH
        or producer.get("schema") != "contentops.portable_host_readiness_receipt.v1"
    ):
        blockers.append("portable_producer_identity_mismatch")
    bindings = value.get("bindings") if isinstance(value.get("bindings"), Mapping) else {}
    expected_source = {
        "repository": POST_MERGE_CONTENTOPS_REPOSITORY,
        "branch": POST_MERGE_CONTENTOPS_REF,
        "head": POST_MERGE_CONTENTOPS_HEAD,
    }
    if dict(bindings.get("portable_source") or {}) != expected_source:
        blockers.append("portable_source_binding_mismatch")
    expected_producer = {
        "commit": POST_MERGE_PRODUCER_COMMIT,
        "schema": "contentops.current_host_readiness_observation.v1",
    }
    if dict(bindings.get("portable_producer") or {}) != expected_producer:
        blockers.append("portable_producer_binding_mismatch")
    packet_hashes = portable.get("packet_hashes") if isinstance(portable.get("packet_hashes"), Mapping) else {}
    if dict(bindings.get("packet_hashes") or {}) != dict(packet_hashes):
        blockers.append("portable_packet_hash_binding_mismatch")
    if dict(bindings.get("proof_layers") or {}) != dict(portable.get("proof_layers") or {}):
        blockers.append("portable_proof_layer_binding_mismatch")
    if dict(value.get("boundary_hashes") or {}) != dict(bindings.get("boundary_hashes") or {}):
        blockers.append("boundary_hash_binding_mismatch")
    freshness = portable.get("freshness") if isinstance(portable.get("freshness"), Mapping) else {}
    observation = portable.get("observation") if isinstance(portable.get("observation"), Mapping) else {}
    actual_clocks = {
        "observed_at_utc": observation.get("observed_at_utc"),
        "known_at_utc": observation.get("known_at_utc"),
        "as_of_utc": freshness.get("as_of_utc"),
        "freshness_status": freshness.get("status"),
    }
    if dict(value.get("clock_state") or {}) != actual_clocks:
        blockers.append("clock_binding_mismatch")
    else:
        try:
            observed = _cross_plane_parse_utc(actual_clocks["observed_at_utc"], field="observed_at_utc")
            known = _cross_plane_parse_utc(actual_clocks["known_at_utc"], field="known_at_utc")
            as_of = _cross_plane_parse_utc(actual_clocks["as_of_utc"], field="as_of_utc")
            if observed > known or known > as_of:
                blockers.append("clock_order_invalid")
        except ValueError as exc:
            blockers.append(str(exc))
    expected_facts = value.get("current_facts") if isinstance(value.get("current_facts"), Mapping) else {}
    if dict(expected_facts) != _cross_plane_observed_facts(portable):
        blockers.append("current_facts_mismatch")
    authority_flags = value.get("authority_flags") if isinstance(value.get("authority_flags"), Mapping) else {}
    if set(authority_flags) != set(CROSS_PLANE_AUTHORITY_FLAGS) or any(authority_flags.get(key) is not False for key in CROSS_PLANE_AUTHORITY_FLAGS):
        blockers.append("authority_flags_not_all_false")
    zero_effect = value.get("zero_effect_flags") if isinstance(value.get("zero_effect_flags"), Mapping) else {}
    if set(zero_effect) != set(CROSS_PLANE_ZERO_EFFECT_KEYS) or any(zero_effect.get(key) not in (False, 0, None) for key in CROSS_PLANE_ZERO_EFFECT_KEYS):
        blockers.append("zero_effect_flags_not_zero")
    if _cross_plane_unknown_write(value):
        blockers.append("unknown_write_stop_retry_readback_reconcile")
    try:
        _post_merge_walk_secret(value)
    except ValueError as exc:
        blockers.append(str(exc))
    if portable.get("portable_receipt_sha256") != (value.get("post_merge_provenance") or {}).get("portable_receipt_sha256"):
        blockers.append("portable_receipt_provenance_binding_mismatch")
    return list(dict.fromkeys(blockers))


def reconcile_post_merge_cross_plane_shadow_cycle_replay(
    payload: Any,
    *,
    shadow_runner: Callable[..., Mapping[str, Any]] | None = None,
    artifact_kind: str = "SEALED_REMOTE",
) -> dict[str, Any]:
    """Replay one sealed Main post-merge input through the existing ContentOps shadow owner."""

    artifact_bytes: bytes | None = None
    input_value: dict[str, Any] | None = None
    blockers: list[str] = []
    try:
        artifact_bytes, input_value = _post_merge_payload_bytes(payload)
    except (OSError, TypeError, ValueError) as exc:
        return _post_merge_receipt_base(
            artifact_bytes=None,
            input_value=None,
            input_hash=None,
            artifact_status="UNAVAILABLE",
            classification="NOT_VERIFIED",
            blockers=[str(exc)],
            production_day_receipt=None,
        )
    actual_artifact_hash = sha256(artifact_bytes).hexdigest()
    artifact_status = "SYNTHETIC" if artifact_kind == "SYNTHETIC" else "SEALED_MATCH"
    if artifact_kind != "SYNTHETIC":
        if len(artifact_bytes) != POST_MERGE_ARTIFACT_BYTES:
            artifact_status = "SIZE_MISMATCH"
            blockers.append("main_fixture_size_mismatch")
        if not actual_artifact_hash.startswith(POST_MERGE_ARTIFACT_SHA256_PREFIX):
            artifact_status = "HASH_MISMATCH"
            blockers.append("main_fixture_sha256_prefix_mismatch")
    canonical = json.dumps(
        input_value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    if canonical != artifact_bytes:
        blockers.append("main_fixture_bytes_not_canonical")
    contract_blockers = _post_merge_validate_contract(input_value)
    blockers.extend(contract_blockers)
    supplied_input_hash = str(input_value.get("input_sha256") or "")
    input_hash = supplied_input_hash if _CROSS_PLANE_SHA256_RE.fullmatch(supplied_input_hash) and supplied_input_hash == cross_plane_input_sha256(input_value) else None
    classification = "NOT_VERIFIED"
    if any(item in {"unknown_write_stop_retry_readback_reconcile", "zero_effect_flags_not_zero"} for item in blockers):
        classification = "UNKNOWN_WRITE"
    elif any("authority" in item for item in blockers):
        classification = "AUTHORITY_FLAG"
    elif any("source" in item or "producer" in item or "head" in item for item in blockers):
        classification = "SOURCE_HEAD_MISMATCH"
    elif any("packet" in item or "boundary" in item or "hash" in item or "portable_receipt" in item for item in blockers):
        classification = "PACKET_HASH_MISMATCH"
    elif any("clock" in item or "fresh" in item for item in blockers):
        classification = "RECEIPT_STALE"
    elif any("proof" in item for item in blockers):
        classification = "PROOF_LAYER_MISMATCH"
    elif any("fact" in item or "task" in item for item in blockers):
        classification = "TASK_STATE_MISMATCH"
    elif any("ambiguous" in item for item in blockers):
        classification = "AMBIGUOUS"
    production_day_receipt: Mapping[str, Any] | None = None
    if not blockers:
        try:
            cross_plane = reconcile_cross_plane_shadow_cycle(input_value, shadow_runner=shadow_runner)
        except (OSError, RuntimeError, TimeoutError, TypeError, ValueError) as exc:
            blockers.append(f"cross_plane_replay_exception:{type(exc).__name__}")
            cross_plane = None
        if cross_plane is not None:
            classification = str(cross_plane.get("classification") or "NOT_VERIFIED")
            production_day_receipt = cross_plane
            if cross_plane.get("status") != "RECONCILED":
                blockers.append(str(cross_plane.get("blocker") or "cross_plane_shadow_blocked"))
            if classification not in POST_MERGE_ALLOWED_REPLAY_CLASSIFICATIONS:
                classification = "NOT_VERIFIED"
                blockers.append("replay_classification_invalid")
    if blockers and classification == "NONE":
        classification = "NOT_VERIFIED"
    return _post_merge_receipt_base(
        artifact_bytes=artifact_bytes,
        input_value=input_value,
        input_hash=input_hash,
        artifact_status=artifact_status,
        classification=classification,
        blockers=blockers,
        production_day_receipt=production_day_receipt,
    )


def _status(component: Mapping[str, Any] | None) -> str:
    return str((component or {}).get("status") or "")


def _has_side_effect(component: Mapping[str, Any] | None) -> bool:
    row = component or {}
    return any(
        row.get(key) is True
        for key in (
            "public_write_performed",
            "publication_authority",
            "durable_store_written",
            "scheduler_started",
            "model_call_performed",
            "provider_call_performed",
            "browser_action_performed",
        )
    )


def _base(enabled: bool, inputs: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": DISABLED_BY_DEFAULT if not enabled else None,
        "enabled": bool(enabled),
        "shadow_only": True,
        "immutable_receipt": True,
        "input_evidence_sha256": _hash(inputs),
        "receipt_sha256": None,
        "production_day_receipt_sha256": None,
        "source_order": [
            "HTTP_OR_OFFICIAL_API_FIRST",
            "ONE_BROWSEROS_RENDERED_RECOVERY_IF_ELIGIBLE",
        ],
        "shared_request_budget": True,
        "max_browser_rendered_recovery_attempts": 1,
        "x_ingestion_cdp_port": 9222,
        "x_ingestion_only": True,
        "scheduler_started": False,
        "durable_store_write_count": 0,
        "database_mutation": False,
        "model_call_count": 0,
        "provider_call_count": 0,
        "browser_action_count": 0,
        "public_write_performed": False,
        "publication_success_proven": False,
        "runtime_readiness_proven": False,
        "account_identity_proven": False,
        "publication_authority": False,
    }


def _finish(result: dict[str, Any]) -> dict[str, Any]:
    body = {key: value for key, value in result.items() if key != "receipt_sha256"}
    result["receipt_sha256"] = _hash(body)
    return result


def _fail(result: dict[str, Any], status: str, detail: str) -> dict[str, Any]:
    result.update({"status": status, "failure_detail": detail})
    return _finish(result)


def run_scheduled_shadow_production_day(
    *,
    enabled: bool = False,
    source_recovery: Mapping[str, Any] | None = None,
    browser_preflight: Mapping[str, Any] | None = None,
    preflight_runner: Callable[..., Mapping[str, Any]] | None = None,
    x_ingestion: Mapping[str, Any] | None = None,
    grounded_evidence: Mapping[str, Any] | None = None,
    candidate_decision: Mapping[str, Any] | None = None,
    canonical_article: Mapping[str, Any] | None = None,
    derivative_packages: Sequence[Mapping[str, Any]] | None = None,
    destination_readback: Mapping[str, Any] | None = None,
    recovery_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return one end-to-end shadow receipt from injected owner outputs."""

    if enabled and browser_preflight is None and preflight_runner is not None:
        try:
            browser_preflight = dict(
                preflight_runner(auto_open=True, reconnect_once=True)
            )
        except (OSError, RuntimeError, TimeoutError, TypeError, ValueError) as exc:
            browser_preflight = {
                "status": "BROWSER_UNAVAILABLE",
                "failure_detail": str(exc) or type(exc).__name__,
            }
    inputs = {
        "source_recovery": source_recovery,
        "browser_preflight": browser_preflight,
        "x_ingestion": x_ingestion,
        "grounded_evidence": grounded_evidence,
        "candidate_decision": candidate_decision,
        "canonical_article": canonical_article,
        "derivative_packages": list(derivative_packages or []),
        "destination_readback": destination_readback,
        "recovery_state": recovery_state,
    }
    result = _base(enabled, inputs)
    if not enabled:
        return _fail(result, DISABLED_BY_DEFAULT, "scheduled_shadow_production_day_disabled_by_default")

    components = {
        "source_recovery": source_recovery,
        "browser_preflight": browser_preflight,
        "x_ingestion": x_ingestion,
        "grounded_evidence": grounded_evidence,
        "candidate_decision": candidate_decision,
        "canonical_article": canonical_article,
        "destination_readback": destination_readback,
    }
    unknown = [
        name
        for name, row in components.items()
        if isinstance(row, Mapping)
        and (
            _status(row) == UNKNOWN_WRITE
            or bool(row.get("unknown_write"))
        )
    ]
    unknown.extend(
        f"derivative:{index}"
        for index, row in enumerate(derivative_packages or [])
        if isinstance(row, Mapping)
        and (_status(row) == UNKNOWN_WRITE or bool(row.get("unknown_write")))
    )
    if unknown:
        return _fail(result, UNKNOWN_WRITE, "unknown_write_stop_retry_readback_reconcile:" + ",".join(unknown))
    side_effects = [name for name, row in components.items() if _has_side_effect(row)]
    side_effects.extend(
        f"derivative:{index}"
        for index, row in enumerate(derivative_packages or [])
        if _has_side_effect(row)
    )
    if side_effects:
        return _fail(result, FAIL_CLOSED, "shadow_side_effect_flag_present:" + ",".join(side_effects))

    missing = [name for name, row in components.items() if not isinstance(row, Mapping)]
    if not derivative_packages:
        missing.append("derivative_packages")
    if missing:
        return _fail(result, MISSING, "missing_components:" + ",".join(missing))

    if _status(source_recovery) not in {
        "HTTP_SUCCESS_NO_BROWSER",
        "BROWSER_RENDERED_RECOVERY_DRY_RUN_PASS",
    }:
        return _fail(result, FAIL_CLOSED, "source_recovery_not_admitted")
    recovery_attempts = int(
        (source_recovery or {}).get("browser_rendered_recovery_attempt_count")
        or (source_recovery or {}).get("attempt_count")
        or 0
    )
    if (
        (source_recovery or {}).get("http_first") is False
        or (source_recovery or {}).get("shared_request_budget") is False
        or recovery_attempts > 1
    ):
        return _fail(result, MISMATCH, "source_recovery_order_budget_or_attempt_contract_invalid")
    if _status(browser_preflight) != "PASS":
        return _fail(result, HUMAN_REQUIRED if _status(browser_preflight) in {"AMBIGUOUS", HUMAN_REQUIRED} else FAIL_CLOSED, "browser_preflight_not_pass")
    if _status(x_ingestion) not in {"INGESTION_ONLY_READY", "NOT_REQUESTED"} or (x_ingestion or {}).get("cdp_port") not in {None, 9222}:
        return _fail(result, MISMATCH, "x_ingestion_boundary_invalid")

    if _status(grounded_evidence) != "GROUNDED_EVIDENCE_READY":
        return _fail(result, HUMAN_REQUIRED if _status(grounded_evidence) in {"STALE", "TRUNCATED", HUMAN_REQUIRED} else FAIL_CLOSED, "grounded_evidence_not_ready")
    if not (grounded_evidence or {}).get("evidence_ids") or not (grounded_evidence or {}).get("claim_bindings_sha256"):
        return _fail(result, MISSING, "grounded_evidence_ids_or_claim_bindings_missing")
    if _status(candidate_decision) != "SELECTED" or not (candidate_decision or {}).get("candidate_id"):
        return _fail(result, MISMATCH, "candidate_decision_not_selected")
    if _status(canonical_article) != "QUALIFIED":
        return _fail(result, MISMATCH, "canonical_article_not_qualified")
    article_hash = str((canonical_article or {}).get("payload_sha256") or "")
    if len(article_hash) != 64 or not (canonical_article or {}).get("article_id"):
        return _fail(result, MISSING, "canonical_article_identity_or_payload_hash_missing")
    if str((canonical_article or {}).get("epistemic_state") or "") not in {
        "CONFIRMED", "UNCONFIRMED", "PARTIALLY_CONFIRMED", "DISPUTED_OR_DENIED", "SUPERSEDED"
    }:
        return _fail(result, MISMATCH, "canonical_article_epistemic_state_invalid")

    packages = list(derivative_packages or [])
    destinations = [str(row.get("destination") or "") for row in packages]
    if len(packages) != 8 or set(destinations) != set(V1_REQUIRED_DERIVATIVE_DESTINATIONS):
        return _fail(result, MISMATCH, "derivative_package_destination_set_invalid")
    if any(str(row.get("status") or "") != "SHADOW_READY" or len(str(row.get("payload_sha256") or "")) != 64 for row in packages):
        return _fail(result, MISSING, "derivative_package_payload_or_status_missing")
    if _status(destination_readback) != "CONFIRMED_SHADOW":
        return _fail(result, MISMATCH if _status(destination_readback) else MISSING, "destination_readback_shadow_not_confirmed")

    recovery = recovery_state or {}
    if bool(recovery.get("interrupted")):
        if recovery.get("resume_status") != "RESUMABLE" or recovery.get("semantic_rerun_forbidden") is not True:
            return _fail(result, HUMAN_REQUIRED, "interruption_resume_contract_invalid")
        result["interruption_recovery"] = "RESUMABLE_WITHOUT_SEMANTIC_RERUN"
    else:
        result["interruption_recovery"] = "NOT_INTERRUPTED"
    result.update(
        {
            "status": SHADOW_CONFIRMED,
            "failure_detail": None,
            "production_day_id": str(recovery.get("production_day_id") or "shadow-day-unknown"),
            "selected_candidate_id": candidate_decision.get("candidate_id"),
            "canonical_article_id": canonical_article.get("article_id"),
            "canonical_payload_sha256": article_hash,
            "derivative_destination_count": len(packages),
            "derivative_destinations": sorted(destinations),
            "grounded_evidence_ids": list(grounded_evidence.get("evidence_ids") or []),
            "candidate_decision_sha256": _hash(candidate_decision),
            "editorial_evidence_sha256": _hash(grounded_evidence),
            "canonical_article_sha256": _hash(canonical_article),
            "derivative_packages_sha256": _hash(packages),
            "destination_readback_sha256": _hash(destination_readback),
            "recovery_state_sha256": _hash(recovery),
        }
    )
    result["production_day_receipt_sha256"] = _hash(result)
    return _finish(result)
