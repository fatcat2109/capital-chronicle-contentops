"""Deterministic editorial traceability and quality pack over the Main replay ledger.

This module is a read-only evidence consumer.  It binds the exact Main quality ledger to the
merged Goal 10/11 newsroom receipts, preserves every claim's source and editorial disposition,
and carries the existing eight-destination shadow result forward without adding a scheduler,
publisher, analyzer, store, status owner, provider/model call, or public-write authority.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence

from live_contentops.destination_transport_registry_v1 import V1_REQUIRED_DERIVATIVE_DESTINATIONS


SCHEMA_VERSION = "contentops.editorial_traceability_quality_pack.v1"
VERSION = "1.0.0"
CANONICALIZATION = "JSON_SORT_KEYS_COMPACT_ASCII_UTF8_NO_FLOAT_NAN"
LEDGER_SCHEMA = "CapitalChronicleMultiWindowQualityReplayLedgerV1"
LEDGER_VERSION = "1.0.0"
REPLAY_STAGES = (
    "INGESTED",
    "NORMALIZED",
    "DEDUPED",
    "CONTRADICTION_QUARANTINED",
    "CORE_PROJECTED",
    "EDITORIAL_PROJECTED",
    "OUTCOME_PENDING",
)
WINDOW_IDS = ("CURRENT_REAL", "RECENT_REPLAY", "PROXY_CONTEXT")
MAIN_REPOSITORY = "fatcat2109/Headline-Raw-data-json"
MAIN_REF = "main"
MAIN_HEAD = "3cef3081d624534417f56cea836605a48a059af9"
MAIN_LEDGER_PATH = "tests/fixtures/multi_window_quality_replay_ledger_current_v1.json"
MAIN_LEDGER_BYTES = 29098
MAIN_LEDGER_FILE_SHA256 = "0e20a099483287195b7760a2cddec1bac09a482c92079cf04190091c3cb1e669"
MAIN_LEDGER_SHA256 = "834d5fb73a4a299392419cde850b0adb0e5746fb6fdfc14743f13077d75c8697"
MAIN_BUNDLE_SHA256 = "9e113fd45caf623458f7bb2adfe9b43fe204cb10d96abe62b718f6a13affaed9"
MAIN_CYCLE_ID = "multi-window-cycle-ed95e189282d21a03a9f26f9"
GOAL9_RECONCILIATION_SHA256 = "313631f2c3c16ce8fa0de5de7d08aefe961caecbfa4d1e95842c7e43a3cddc29"
GOAL10_RECEIPT_SCHEMA = "contentops.multi_window_newsroom_cycle_receipt.v1"
GOAL10_HEALTHY_RECEIPT_SHA256 = "af9d8ccacc6b4e4f4c2b2c2bb46c3bcf49ee0a7a4e57083a85b97db9168d3277"
GOAL11_RECEIPT_SCHEMA = "contentops.multi_window_newsroom_cycle_receipt.v2"
GOAL11_HEALTHY_RECEIPT_SHA256 = "b13ea09d730133a760baf4577191be2d09ed50e93145cd0d3317782be2d9363f"
CONTENTOPS_HEAD = "a0c62b3470ad801bc38efae2ef6671d3ad3ef2d0"
GOAL11_CONTENTOPS_HEAD = "8571cca13cff70fed69da113f96c243e62962170"
PARENT_MAIN_HEAD = "8f66238d320062e9258c893d59d2293253655f94"
PARENT_CONTENTOPS_INPUT_HEAD = "aa5dbda6c73a4f53683365ce26c6323ec57298a9"
PARENT_CONTENTOPS_CONSUMER_HEAD = "f3fb9fb273261d94850007db19aedf4171014c19"
ZERO_EFFECT_KEYS = (
    "scheduler_started",
    "durable_store_write_count",
    "database_mutation",
    "model_call_count",
    "provider_call_count",
    "browser_action_count",
    "public_write_performed",
    "publication_authority",
)
AUTHORITY_KEYS = (
    "decision_authority",
    "forecast_authority",
    "numeric_truth_authority",
    "paper_authority",
    "broker_authority",
    "publication_authority",
    "runtime_authority",
    "database_authority",
    "account_authority",
    "provider_call_performed",
    "model_call_performed",
    "network_call_performed",
    "runtime_mutation_performed",
    "mutable_status_owner",
    "external_effects",
)
CLASSIFICATIONS = frozenset(
    {
        "SHADOW_CONFIRMED",
        "NOT_VERIFIED",
        "STALE",
        "AMBIGUOUS",
        "UNKNOWN_WRITE",
        "AUTHORITY_FLAG",
        "PACKET_HASH_MISMATCH",
        "SOURCE_HEAD_MISMATCH",
    }
)
OUTCOME_STATES = frozenset({"OUTCOME_PENDING", "NOT_COMPARABLE", "NOT_VERIFIED"})
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SECRET_VALUE_RE = re.compile(
    r"(?i)(?:bearer\s+[A-Za-z0-9._~+/=-]{8,}|(?:sk|pk|rk)-[A-Za-z0-9_-]{12,}|"
    r"(?:access[_-]?token|refresh[_-]?token|api[_-]?key|password|secret|cookie)\s*[:=]\s*[^\s,;]{8,})"
)
SENSITIVE_KEY_RE = re.compile(
    r"(?i)(?:^|_)(?:access[_-]?token|refresh[_-]?token|cookie|password|secret|authorization|"
    r"api[_-]?key|private[_-]?key|session[_-]?token|webhook[_-]?url)(?:$|_)"
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256_without(value: Mapping[str, Any], field: str) -> str:
    return sha256(canonical_bytes({key: item for key, item in value.items() if key != field})).hexdigest()


def pack_sha256(value: Mapping[str, Any]) -> str:
    return sha256_without(value, "pack_sha256")


def _walk_secret(value: Any, *, path: str = "root") -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if SENSITIVE_KEY_RE.search(key_text):
                found.append(f"secret_material:{path}.{key_text}")
            found.extend(_walk_secret(item, path=f"{path}.{key_text}"))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            found.extend(_walk_secret(item, path=f"{path}[{index}]"))
    elif isinstance(value, str) and SECRET_VALUE_RE.search(value):
        found.append(f"secret_material:{path}")
    return found


def _unknown_write(value: Any) -> bool:
    if isinstance(value, Mapping):
        if value.get("unknown_write") is True or str(value.get("status") or "") == "UNKNOWN_WRITE":
            return True
        return any(_unknown_write(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_unknown_write(item) for item in value)
    return str(value).upper() == "UNKNOWN_WRITE"


def _authority_violations(value: Any, *, path: str = "root") -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).lower()
            is_authority = key_text in AUTHORITY_KEYS or key_text.endswith("authority") or key_text.endswith("_authority")
            if is_authority and not isinstance(item, (Mapping, list, tuple)) and item not in (False, 0, None, "NONE", "NOT_VERIFIED"):
                found.append(f"authority_flag:{path}.{key}")
            found.extend(_authority_violations(item, path=f"{path}.{key}"))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            found.extend(_authority_violations(item, path=f"{path}[{index}]"))
    return found


def _authority_flags() -> dict[str, Any]:
    return {key: (0 if key == "external_effects" else False) for key in AUTHORITY_KEYS}


def _default_zero_effect() -> dict[str, Any]:
    return {key: (0 if key.endswith("count") else False) for key in ZERO_EFFECT_KEYS}


def _hashes(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return sorted({str(item) for item in value})


def _valid_hashes(values: Sequence[str]) -> bool:
    return bool(values) and all(SHA256_RE.fullmatch(value) for value in values)


def _validate_ledger(ledger: Mapping[str, Any], *, artifact_bytes: bytes | None = None) -> tuple[list[str], dict[str, Any]]:
    blockers: list[str] = []
    artifact_hash = sha256(artifact_bytes).hexdigest() if artifact_bytes is not None else None
    artifact = {
        "repository": MAIN_REPOSITORY,
        "ref": MAIN_REF,
        "commit": MAIN_HEAD,
        "path": MAIN_LEDGER_PATH,
        "bytes": len(artifact_bytes) if artifact_bytes is not None else None,
        "sha256": artifact_hash,
        "expected_sha256": MAIN_LEDGER_FILE_SHA256,
        "status": "SYNTHETIC" if artifact_bytes is None else ("SEALED_MATCH" if len(artifact_bytes) == MAIN_LEDGER_BYTES and artifact_hash == MAIN_LEDGER_FILE_SHA256 else "HASH_MISMATCH"),
    }
    if not isinstance(ledger, Mapping):
        return ["ledger_not_mapping"], artifact
    if ledger.get("schema") != LEDGER_SCHEMA or ledger.get("version") != LEDGER_VERSION:
        blockers.append("ledger_schema_or_version_invalid")
    supplied = str(ledger.get("ledger_sha256") or "")
    if not SHA256_RE.fullmatch(supplied) or supplied != sha256_without(ledger, "ledger_sha256"):
        blockers.append("ledger_hash_invalid")
    if supplied != MAIN_LEDGER_SHA256 and artifact_bytes is not None:
        blockers.append("main_ledger_hash_mismatch")
    binding = ledger.get("bundle_binding") if isinstance(ledger.get("bundle_binding"), Mapping) else {}
    if binding.get("bundle_id") != MAIN_CYCLE_ID or binding.get("bundle_sha256") != MAIN_BUNDLE_SHA256:
        blockers.append("bundle_binding_mismatch")
    if binding.get("bundle_schema") != "CapitalChronicleMultiWindowIntelligenceCycleBundleV1":
        blockers.append("bundle_schema_mismatch")
    goal9 = binding.get("goal9_reconciliation") if isinstance(binding.get("goal9_reconciliation"), Mapping) else {}
    if goal9.get("receipt_sha256") != GOAL9_RECONCILIATION_SHA256:
        blockers.append("goal9_receipt_mismatch")
    main_source = binding.get("main_source") if isinstance(binding.get("main_source"), Mapping) else {}
    if main_source.get("head") != PARENT_MAIN_HEAD or main_source.get("repository") != "fatcat2109/capital-chronicle-main":
        blockers.append("main_source_head_mismatch")
    contentops_input = binding.get("contentops_input") if isinstance(binding.get("contentops_input"), Mapping) else {}
    consumer = binding.get("contentops_consumer") if isinstance(binding.get("contentops_consumer"), Mapping) else {}
    if contentops_input.get("head") != PARENT_CONTENTOPS_INPUT_HEAD or consumer.get("head") != PARENT_CONTENTOPS_CONSUMER_HEAD:
        blockers.append("contentops_parent_head_mismatch")
    if ledger.get("authority_flags") != _authority_flags():
        blockers.append("authority_flag")
    rows = ledger.get("claim_ledger") if isinstance(ledger.get("claim_ledger"), list) else []
    claim_ids = [str(row.get("claim_id")) for row in rows if isinstance(row, Mapping)]
    if not rows or len(claim_ids) != len(set(claim_ids)):
        blockers.append("claim_ledger_shape_invalid")
    for row in rows:
        if not isinstance(row, Mapping):
            blockers.append("claim_row_not_mapping")
            continue
        claim_id = str(row.get("claim_id") or "")
        if row.get("window_id") not in WINDOW_IDS:
            blockers.append(f"window_invalid:{claim_id}")
        source_hashes = _hashes(row.get("source_hashes"))
        evidence_hashes = _hashes(row.get("evidence_hashes"))
        if not _valid_hashes(source_hashes) or not _valid_hashes(evidence_hashes):
            blockers.append(f"claim_hash_invalid:{claim_id}")
        if not isinstance(row.get("source_lineage"), list):
            blockers.append(f"source_lineage_missing:{claim_id}")
        rights = row.get("rights") if isinstance(row.get("rights"), Mapping) else {}
        if rights.get("internal_analysis_allowed") is not True:
            blockers.append(f"rights_invalid:{claim_id}")
        freshness = row.get("freshness") if isinstance(row.get("freshness"), Mapping) else {}
        if freshness.get("state") in {"STALE", "FUTURE", "BLOCKED"}:
            blockers.append(f"freshness_{str(freshness.get('state')).lower()}:{claim_id}")
        if str(row.get("pit_state") or "").startswith("PIT_INVALID_FUTURE"):
            blockers.append(f"future:{claim_id}")
        if _unknown_write(row):
            blockers.append(f"unknown_write:{claim_id}")
        if str(row.get("outcome_status") or "") not in OUTCOME_STATES | {"OUTCOME_PENDING"}:
            blockers.append(f"outcome_state_invalid:{claim_id}")
    stages = ledger.get("replay_matrix") if isinstance(ledger.get("replay_matrix"), list) else []
    if [str(stage.get("stage_id")) for stage in stages if isinstance(stage, Mapping)] != list(REPLAY_STAGES):
        blockers.append("replay_stage_order_invalid")
    slots = ledger.get("outcome_slots") if isinstance(ledger.get("outcome_slots"), list) else []
    if [str(slot.get("claim_id")) for slot in slots if isinstance(slot, Mapping)] != claim_ids:
        blockers.append("outcome_slot_claim_binding_invalid")
    for slot in slots:
        if not isinstance(slot, Mapping):
            blockers.append("outcome_slot_not_mapping")
            continue
        if slot.get("outcome_status") not in OUTCOME_STATES or slot.get("result") is not None or slot.get("percentage") is not None:
            blockers.append(f"outcome_not_comparable:{slot.get('claim_id')}")
    summary = ledger.get("quality_summary") if isinstance(ledger.get("quality_summary"), Mapping) else {}
    counts = summary.get("counts") if isinstance(summary.get("counts"), Mapping) else {}
    scalar_counts = [value for value in counts.values() if not isinstance(value, Mapping)]
    if any(not isinstance(value, int) or isinstance(value, bool) for value in scalar_counts):
        blockers.append("quality_counts_not_integer")
    blockers.extend(_walk_secret(ledger))
    blockers.extend(_authority_violations(ledger))
    if _unknown_write(ledger):
        blockers.append("unknown_write")
    if artifact_bytes is not None:
        try:
            sealed = json.loads(artifact_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            blockers.append("main_ledger_json_invalid")
        else:
            if sealed != dict(ledger):
                blockers.append("main_ledger_payload_mismatch")
    return list(dict.fromkeys(blockers)), artifact


def _validate_receipt(receipt: Mapping[str, Any], *, schema: str, expected_sha256: str | None = None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(receipt, Mapping) or receipt.get("schema_version") != schema:
        return ["receipt_schema_invalid"]
    supplied = str(receipt.get("receipt_sha256") or "")
    if not SHA256_RE.fullmatch(supplied) or supplied != sha256_without(receipt, "receipt_sha256"):
        blockers.append("receipt_hash_invalid")
    if expected_sha256 and supplied != expected_sha256:
        blockers.append("receipt_hash_mismatch")
    if receipt.get("immutable_receipt") is not True or receipt.get("shadow_only") is not True:
        blockers.append("receipt_shadow_boundary_invalid")
    if receipt.get("runtime_proven") is True or receipt.get("publicly_proven") is True:
        blockers.append("receipt_proof_promoted")
    if _unknown_write(receipt):
        blockers.append("unknown_write")
    blockers.extend(_walk_secret(receipt))
    blockers.extend(_authority_violations(receipt))
    return list(dict.fromkeys(blockers))


def _claim_decision(row: Mapping[str, Any]) -> tuple[str, list[str], str, str]:
    quality = str(row.get("quality_classification") or "NOT_VERIFIED")
    exactness = (row.get("exact_proxy_context") or {}).get("state")
    freshness = (row.get("freshness") or {}).get("state")
    core = (row.get("core_eligibility") or {}).get("status")
    blockers = [str(item) for item in (row.get("core_eligibility") or {}).get("blockers") or []]
    if _unknown_write(row):
        return "ABSTAINED", blockers + ["UNKNOWN_WRITE"], "UNKNOWN_WRITE", "WRITE_UNCERTAINTY"
    if row.get("window_id") == "CURRENT_REAL" and freshness != "CURRENT":
        return "ABSTAINED", blockers + ["CURRENT_REAL_NOT_VERIFIED"], "NOT_VERIFIED", "HOST_UNCERTAINTY"
    if freshness in {"STALE", "FUTURE", "BLOCKED"} or str(row.get("pit_state")) == "PIT_INVALID_FUTURE_KNOWN_AT":
        return "ABSTAINED", blockers + ["STALE_OR_FUTURE"], "STALE_OR_FUTURE", "TEMPORAL_CONFLICT"
    if (row.get("rights") or {}).get("internal_analysis_allowed") is not True:
        return "ABSTAINED", blockers + ["RIGHTS_NOT_ALLOWED"], "RIGHTS_INVALID", "RIGHTS_UNCERTAINTY"
    if quality == "AMBIGUOUS" or (row.get("contradiction") or {}).get("state") == "UNRESOLVED_CONTRADICTION":
        return "QUARANTINED", blockers + ["CONTRADICTION_QUARANTINED"], "AMBIGUOUS", "CONFLICT_PRESENT"
    if exactness == "PROXY":
        return "CONTEXT_ONLY", blockers + ["PROXY_CONTEXT_ONLY"], "PROXY_CONTEXT_ONLY", "PROXY_UNCERTAINTY"
    if exactness == "CONTEXT_ONLY" or quality == "CONTEXT_ONLY":
        return "CONTEXT_ONLY", blockers + ["CONTEXT_ONLY"], "CONTEXT_ONLY", "CONTEXT_UNCERTAINTY"
    if core == "ADMITTED" and exactness == "EXACT":
        return "SELECTED", blockers, "EXACT_CORE_ELIGIBLE", "REPLAY_NOT_RUNTIME_PROVEN"
    return "ABSTAINED", blockers or ["EDITORIAL_ELIGIBILITY_NOT_ADMITTED"], quality, "EDITORIAL_UNCERTAINTY"


def _claim_traceability(rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[str], list[str], list[str], list[str]]:
    trace: list[dict[str, Any]] = []
    selected: list[str] = []
    abstained: list[str] = []
    quarantined: list[str] = []
    context_only: list[str] = []
    for row in rows:
        decision, reasons, uncertainty, conflict = _claim_decision(row)
        claim_id = str(row.get("claim_id"))
        if decision == "SELECTED":
            selected.append(claim_id)
        elif decision == "QUARANTINED":
            quarantined.append(claim_id)
        elif decision == "CONTEXT_ONLY":
            context_only.append(claim_id)
        else:
            abstained.append(claim_id)
        trace.append(
            {
                "window_id": row.get("window_id"),
                "claim_id": claim_id,
                "claim": row.get("claim"),
                "event_identity": row.get("event_identity"),
                "claim_identity": row.get("claim_identity"),
                "source_identity": row.get("source_identity"),
                "source_ref": row.get("source_ref"),
                "source_hashes": _hashes(row.get("source_hashes")),
                "evidence_hashes": _hashes(row.get("evidence_hashes")),
                "source_lineage": row.get("source_lineage") or [],
                "dedupe": {"key": row.get("dedupe_key"), "duplicate_count": row.get("duplicate_count"), "duplicate_claim_ids": row.get("duplicate_claim_ids") or []},
                "contradiction": row.get("contradiction") or {},
                "clocks": row.get("clocks") or {},
                "pit_state": row.get("pit_state"),
                "freshness": row.get("freshness") or {},
                "rights": row.get("rights") or {},
                "exact_proxy_context": row.get("exact_proxy_context") or {},
                "core_eligibility": row.get("core_eligibility") or {},
                "editorial_eligibility": row.get("editorial_eligibility") or {},
                "unsupported_dimensions": sorted(str(item) for item in row.get("unsupported_dimensions") or []),
                "decision": decision,
                "decision_reasons": sorted(set(reasons)),
                "uncertainty_label": uncertainty,
                "conflict_label": conflict,
            }
        )
    return trace, selected, abstained, quarantined, context_only


def _editorial_sections(trace: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    for row in trace:
        sections.append(
            {
                "section_id": f"claim:{row['claim_id']}",
                "section_role": "evidence_bound_editorial_trace",
                "claim_ids": [row["claim_id"]],
                "decision": row["decision"],
                "source_hashes": list(row["source_hashes"]),
                "evidence_hashes": list(row["evidence_hashes"]),
                "uncertainty_label": row["uncertainty_label"],
                "conflict_label": row["conflict_label"],
                "unsupported_dimensions": list(row["unsupported_dimensions"]),
            }
        )
    return sections


def _zero_effect(v1: Mapping[str, Any], v2: Mapping[str, Any]) -> dict[str, Any]:
    left = v1.get("zero_effect") if isinstance(v1.get("zero_effect"), Mapping) else {}
    right = v2.get("zero_effect") if isinstance(v2.get("zero_effect"), Mapping) else {}
    return {key: left.get(key) if left.get(key) is not None else right.get(key) for key in ZERO_EFFECT_KEYS}


def _derivative_mapping(receipt_v2: Mapping[str, Any], packages: Sequence[Mapping[str, Any]] | None, selected: Sequence[str], source_hashes: Sequence[str]) -> tuple[list[dict[str, Any]], list[str]]:
    blockers: list[str] = []
    shadow = receipt_v2.get("derivative_shadow") if isinstance(receipt_v2.get("derivative_shadow"), Mapping) else {}
    destinations = list(shadow.get("destinations") or [])
    if receipt_v2.get("classification") != "SHADOW_CONFIRMED" and not destinations:
        return [], blockers
    if shadow.get("count") != len(V1_REQUIRED_DERIVATIVE_DESTINATIONS) or set(destinations) != set(V1_REQUIRED_DERIVATIVE_DESTINATIONS):
        blockers.append("derivative_count_or_destination_mismatch")
    package_map = {str(item.get("destination")): item for item in packages or [] if isinstance(item, Mapping)}
    if len(package_map) != len(V1_REQUIRED_DERIVATIVE_DESTINATIONS) or set(package_map) != set(V1_REQUIRED_DERIVATIVE_DESTINATIONS):
        blockers.append("derivative_count_or_destination_mismatch")
    mapping: list[dict[str, Any]] = []
    for destination in V1_REQUIRED_DERIVATIVE_DESTINATIONS:
        package = package_map.get(destination, {})
        payload = package.get("payload_sha256")
        if not SHA256_RE.fullmatch(str(payload or "")):
            blockers.append(f"derivative_payload_hash_missing:{destination}")
        if package.get("public_write_performed") is True or package.get("unknown_write") is True:
            blockers.append(f"derivative_external_effect:{destination}")
        mapping.append(
            {
                "destination": destination,
                "claim_ids": list(selected),
                "source_hashes": sorted(set(source_hashes)),
                "payload_sha256": payload,
                "package_status": package.get("status", "SHADOW_RECEIPT_ONLY"),
                "public_write_performed": False,
                "readback_shadow_status": "SHADOW_CONFIRMED" if shadow.get("receipt_sha256") else "NOT_VERIFIED",
            }
        )
    return mapping, blockers


def _classification(blockers: Sequence[str], ledger: Mapping[str, Any], *, derivative_ready: bool) -> str:
    text = " ".join(blockers)
    lower_text = text.lower()
    if "UNKNOWN_WRITE" in text or "unknown_write" in text:
        return "UNKNOWN_WRITE"
    if "authority" in text.lower():
        return "AUTHORITY_FLAG"
    if "stale" in lower_text or "future" in lower_text:
        return "STALE"
    if "derivative_count_or_destination_mismatch" in text or "derivative_payload_hash_missing" in text:
        return "NOT_VERIFIED"
    if "hash" in text.lower() or "tamper" in text.lower() or "payload_mismatch" in text:
        return "PACKET_HASH_MISMATCH"
    if "head" in text.lower() or "source" in text.lower() and "mismatch" in text.lower():
        return "SOURCE_HEAD_MISMATCH"
    quality = str((ledger.get("quality_summary") or {}).get("classification") or "NOT_VERIFIED")
    if quality == "AMBIGUOUS":
        return "AMBIGUOUS"
    if quality != "NONE" or not derivative_ready:
        return "NOT_VERIFIED"
    return "SHADOW_CONFIRMED"


def build_editorial_traceability_quality_pack(
    ledger: Mapping[str, Any],
    newsroom_receipt_v2: Mapping[str, Any],
    *,
    newsroom_receipt_v1: Mapping[str, Any] | None = None,
    derivative_packages: Sequence[Mapping[str, Any]] | None = None,
    artifact_bytes: bytes | None = None,
) -> dict[str, Any]:
    """Build one immutable quality pack without invoking any external owner."""

    blockers, artifact = _validate_ledger(ledger, artifact_bytes=artifact_bytes)
    v2_blockers = _validate_receipt(newsroom_receipt_v2, schema=GOAL11_RECEIPT_SCHEMA)
    v1 = newsroom_receipt_v1 or {}
    v1_blockers = _validate_receipt(v1, schema=GOAL10_RECEIPT_SCHEMA) if v1 else ["goal10_receipt_missing"]
    blockers.extend(v2_blockers)
    blockers.extend(v1_blockers)
    v2_artifact = newsroom_receipt_v2.get("artifact") if isinstance(newsroom_receipt_v2.get("artifact"), Mapping) else {}
    if newsroom_receipt_v2.get("source", {}).get("main_head") != "11323a08706cfb90a9f62233598b8ba3e5e6b307":
        blockers.append("goal11_source_head_mismatch")
    if v2_artifact.get("status") == "SEALED_MATCH" and newsroom_receipt_v2.get("bundle_sha256") != MAIN_BUNDLE_SHA256:
        blockers.append("goal11_bundle_binding_mismatch")
    if v1 and v1.get("source_heads", {}).get("main") != PARENT_MAIN_HEAD:
        blockers.append("goal10_source_head_mismatch")
    rows = ledger.get("claim_ledger") if isinstance(ledger.get("claim_ledger"), list) else []
    trace, selected, abstained, quarantined, context_only = _claim_traceability(rows)
    selected_hashes = [item for row in trace if row["claim_id"] in selected for item in row["source_hashes"]]
    derivative_mapping, derivative_blockers = _derivative_mapping(newsroom_receipt_v2, derivative_packages, selected, selected_hashes)
    blockers.extend(derivative_blockers)
    zero_effect = _zero_effect(v1, newsroom_receipt_v2)
    if any(value is None for value in zero_effect.values()):
        blockers.append("zero_effect_incomplete")
    if any(value not in (False, 0, None) for value in zero_effect.values()):
        blockers.append("zero_effect_not_zero")
    outcome_slots = {str(slot.get("claim_id")): slot for slot in ledger.get("outcome_slots") or [] if isinstance(slot, Mapping)}
    outcomes = []
    for row in trace:
        slot = outcome_slots.get(row["claim_id"], {})
        outcomes.append(
            {
                "claim_id": row["claim_id"],
                "source_hashes": list(row["source_hashes"]),
                "outcome_status": slot.get("outcome_status", "OUTCOME_PENDING"),
                "evaluation_status": "NOT_COMPARABLE" if slot.get("outcome_status") == "OUTCOME_PENDING" else "NOT_VERIFIED",
                "forecast_status": slot.get("forecast_status", "NOT_VERIFIED"),
                "paper_status": slot.get("paper_status", "NOT_VERIFIED"),
                "runtime_status": slot.get("runtime_status", "NOT_VERIFIED"),
                "result": None,
                "percentage": None,
                "outcome_reference": None,
            }
        )
    quality_summary = ledger.get("quality_summary") if isinstance(ledger.get("quality_summary"), Mapping) else {}
    classification = _classification(blockers, ledger, derivative_ready=not derivative_blockers)
    pack = {
        "schema_version": SCHEMA_VERSION,
        "version": VERSION,
        "canonicalization": CANONICALIZATION,
        "status": classification,
        "immutable_pack": True,
        "shadow_only": True,
        "source_state": "MERGED_MAIN_ARCHIVE" if artifact["status"] == "SEALED_MATCH" else "SYNTHETIC",
        "main_source": {
            "repository": MAIN_REPOSITORY,
            "ref": MAIN_REF,
            "head": MAIN_HEAD,
            "artifact_path": MAIN_LEDGER_PATH,
            "artifact_bytes": MAIN_LEDGER_BYTES,
            "artifact_file_sha256": MAIN_LEDGER_FILE_SHA256,
            "ledger_sha256": MAIN_LEDGER_SHA256,
            "bundle_sha256": MAIN_BUNDLE_SHA256,
            "cycle_id": MAIN_CYCLE_ID,
        },
        "contentops_source": {
            "repository": "fatcat2109/capital-chronicle-contentops",
            "ref": "master",
            "head": CONTENTOPS_HEAD,
            "goal11_head": GOAL11_CONTENTOPS_HEAD,
        },
        "artifact": artifact,
        "ledger_binding": {
            "schema": ledger.get("schema"),
            "version": ledger.get("version"),
            "ledger_id": ledger.get("ledger_id"),
            "ledger_sha256": ledger.get("ledger_sha256"),
            "bundle_binding": ledger.get("bundle_binding"),
            "goal9_reconciliation_sha256": GOAL9_RECONCILIATION_SHA256,
        },
        "parent_receipts": {
            "goal9_reconciliation_sha256": GOAL9_RECONCILIATION_SHA256,
            "goal10_newsroom_receipt_sha256": v1.get("receipt_sha256"),
            "goal10_newsroom_receipt_schema": v1.get("schema_version"),
            "goal11_newsroom_receipt_sha256": newsroom_receipt_v2.get("receipt_sha256"),
            "goal11_newsroom_receipt_schema": newsroom_receipt_v2.get("schema_version"),
        },
        "policy_matrix": {
            "EXACT_CURRENT_RIGHTS_ALLOWED": "CORE_AND_EDITORIAL_ALLOWED",
            "RECENT_REPLAY_EXACT_PIT_RIGHTS": "EDITORIAL_AND_CORE_REPLAY_ONLY",
            "CURRENT_REAL_NOT_VERIFIED": "ABSTAIN_KEEP_FACTS_AND_HASHES",
            "PROXY_CONTEXT": "QUALITATIVE_CONTEXT_ONLY",
            "CONTRADICTION": "QUARANTINE_KEEP_BOTH_SOURCES",
            "STALE_FUTURE_RIGHTS_UNKNOWN_AMBIGUOUS": "ABSTAIN_FAIL_CLOSED",
        },
        "claim_traceability": trace,
        "claim_to_editorial": {
            "selected_claim_ids": selected,
            "abstained_claim_ids": abstained,
            "quarantined_claim_ids": quarantined,
            "context_only_claim_ids": context_only,
            "draft_sections": _editorial_sections(trace),
            "authority": False,
        },
        "claim_to_derivative": {
            "article_id": newsroom_receipt_v2.get("article_decision", {}).get("article_id"),
            "canonical_article_claim_ids": selected,
            "packages": derivative_mapping,
            "destination_readback_shadow_sha256": newsroom_receipt_v2.get("destination_readback_shadow_sha256"),
            "interruption_resume": newsroom_receipt_v2.get("interruption_resume", "NOT_ATTEMPTED"),
            "shadow_only": True,
            "public_write_performed": False,
        },
        "outcome_evaluation": {
            "states_allowed": sorted(OUTCOME_STATES),
            "claims": outcomes,
            "performance_claims_created": False,
            "forecast_claims_created": False,
            "runtime_claims_created": False,
            "public_claims_created": False,
        },
        "quality_counts": {
            "retained_claim_count": len(trace),
            "selected_count": len(selected),
            "abstained_count": len(abstained),
            "quarantined_count": len(quarantined),
            "context_only_count": len(context_only),
            "derivative_count": len(derivative_mapping),
            "outcome_pending_count": sum(item["outcome_status"] == "OUTCOME_PENDING" for item in outcomes),
            "not_comparable_count": sum(item["evaluation_status"] == "NOT_COMPARABLE" for item in outcomes),
            "not_verified_count": sum(item["runtime_status"] == "NOT_VERIFIED" for item in outcomes),
            "source_hash_count": len({item for row in trace for item in row["source_hashes"]}),
        },
        "ledger_quality_summary": dict(quality_summary),
        "proof_axes": {
            "artifact_hash": artifact["status"] == "SEALED_MATCH",
            "ledger_hash": not any("ledger_hash" in item for item in blockers),
            "parent_receipts_bound": not any("receipt" in item for item in blockers),
            "claim_lineage_complete": not any("lineage" in item for item in blockers),
            "editorial_mapping_complete": bool(trace),
            "derivative_mapping_complete": not derivative_blockers,
            "runtime_proven": False,
            "publicly_proven": False,
        },
        "zero_effect": zero_effect,
        "authority_flags": _authority_flags(),
        "host_facts": newsroom_receipt_v2.get("host_facts"),
        "classification": classification,
        "blockers": list(dict.fromkeys(str(item) for item in blockers)),
        "next": "RETAIN_TRACEABILITY_PACK_AND_HAND_TO_MAIN_FOR_NEXT_EVALUATION_CONSUMER",
        "pack_sha256": None,
    }
    pack["pack_sha256"] = pack_sha256(pack)
    return pack


def verify_editorial_traceability_quality_pack(pack: Mapping[str, Any]) -> bool:
    """Verify the deterministic pack boundary without granting any authority."""

    try:
        if pack.get("schema_version") != SCHEMA_VERSION or pack.get("version") != VERSION:
            return False
        if pack.get("pack_sha256") != pack_sha256(pack):
            return False
        if pack.get("immutable_pack") is not True or pack.get("shadow_only") is not True:
            return False
        if pack.get("authority_flags") != _authority_flags():
            return False
        zero = pack.get("zero_effect") if isinstance(pack.get("zero_effect"), Mapping) else {}
        if set(zero) != set(ZERO_EFFECT_KEYS) or any(value not in (False, 0, None) for value in zero.values()):
            return False
        counts = pack.get("quality_counts") if isinstance(pack.get("quality_counts"), Mapping) else {}
        if any(not isinstance(value, int) or isinstance(value, bool) for value in counts.values()):
            return False
        if pack.get("classification") not in CLASSIFICATIONS:
            return False
        if _walk_secret(pack) or _unknown_write(pack) or _authority_violations(pack):
            return False
        if pack.get("outcome_evaluation", {}).get("performance_claims_created") is not False:
            return False
        if pack.get("outcome_evaluation", {}).get("forecast_claims_created") is not False:
            return False
        if pack.get("outcome_evaluation", {}).get("runtime_claims_created") is not False:
            return False
        if pack.get("outcome_evaluation", {}).get("public_claims_created") is not False:
            return False
        packages = pack.get("claim_to_derivative", {}).get("packages") or []
        if pack.get("classification") == "SHADOW_CONFIRMED":
            if len(packages) != len(V1_REQUIRED_DERIVATIVE_DESTINATIONS):
                return False
            if {row.get("destination") for row in packages} != set(V1_REQUIRED_DERIVATIVE_DESTINATIONS):
                return False
        for outcome in pack.get("outcome_evaluation", {}).get("claims") or []:
            if outcome.get("outcome_status") not in OUTCOME_STATES:
                return False
            if outcome.get("result") is not None or outcome.get("percentage") is not None:
                return False
        return True
    except (KeyError, TypeError, ValueError):
        return False


__all__ = [
    "CANONICALIZATION",
    "CONTENTOPS_HEAD",
    "MAIN_HEAD",
    "MAIN_LEDGER_BYTES",
    "MAIN_LEDGER_FILE_SHA256",
    "MAIN_LEDGER_PATH",
    "MAIN_LEDGER_SHA256",
    "SCHEMA_VERSION",
    "build_editorial_traceability_quality_pack",
    "canonical_bytes",
    "pack_sha256",
    "verify_editorial_traceability_quality_pack",
]
