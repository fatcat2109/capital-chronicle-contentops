"""Deterministic editorial adjudication and bounded newsroom prioritization.

The consumer turns the merged Main outcome-evaluation evidence into an editorial decision
surface.  It retains source and proof boundaries, exposes missingness, and reuses the existing
Goal 12 traceability pack for article and derivative mappings.  It never creates a score, forecast,
audience metric, Core Analyzer authority, scheduler, store, publisher, or public write.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence

from live_contentops.destination_transport_registry_v1 import V1_REQUIRED_DERIVATIVE_DESTINATIONS
from live_contentops.editorial_traceability_quality_pack_v1 import (
    MAIN_BUNDLE_SHA256,
    MAIN_LEDGER_SHA256,
    SCHEMA_VERSION as TRACEABILITY_SCHEMA,
    verify_editorial_traceability_quality_pack,
)


SCHEMA_VERSION = "contentops.editorial_adjudication_prioritization_pack.v1"
VERSION = "1.0.0"
CANONICALIZATION = "JSON_SORT_KEYS_COMPACT_ASCII_UTF8_NO_FLOAT_NAN"
MAIN_CONTRACT_SCHEMA = "CapitalChronicleOutcomeEvaluationBundleV1"
REQUESTED_MAIN_CONTRACT_SCHEMA = "CapitalChronicleDecisionEvidencePrioritizationPackV1"
MAIN_REPOSITORY = "fatcat2109/Headline-Raw-data-json"
MAIN_REF = "main"
MAIN_HEAD = "dcbeb56608672a7b17ec1bb084ee6863c9c2a10c"
MAIN_ARTIFACT_PATH = "tests/fixtures/multi_window_outcome_evaluation_current_v1.json"
MAIN_ARTIFACT_BYTES = 33663
MAIN_ARTIFACT_FILE_SHA256 = "3e0964e818a95923823f584b61529ef0288ddac58916371a8474a6eaeffd6f76"
MAIN_EVALUATION_SHA256 = "ae67ad70a7a692a7c92003a3fb3d4869fd3898ee3dc5b0ed07166c39c960a043"
MAIN_BUNDLE_SHA256 = MAIN_BUNDLE_SHA256
MAIN_LEDGER_SHA256 = MAIN_LEDGER_SHA256
GOAL9_RECEIPT_SHA256 = "313631f2c3c16ce8fa0de5de7d08aefe961caecbfa4d1e95842c7e43a3cddc29"
GOAL10_RECEIPT_SCHEMA = "contentops.multi_window_newsroom_cycle_receipt.v1"
GOAL11_RECEIPT_SCHEMA = "contentops.multi_window_newsroom_cycle_receipt.v2"
GOAL12_RECEIPT_SCHEMA = TRACEABILITY_SCHEMA
CONTENTOPS_HEAD = "49ad25dc2b3e741d4e60f2de057a99b91d8e4021"
PARENT_GOAL12_CONTENTOPS_HEAD = "a0c62b3470ad801bc38efae2ef6671d3ad3ef2d0"
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
    "score_authority",
    "outcome_authority",
    "evaluation_authority",
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
    "promotion_authorized",
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
DECISIONS = frozenset({"PRIORITIZED", "CONTEXT_ONLY", "ABSTAINED", "QUARANTINED"})
OUTCOME_STATES = frozenset({"OUTCOME_PENDING", "NOT_COMPARABLE", "NOT_VERIFIED", "OBSERVED"})
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


def _authority_flags() -> dict[str, Any]:
    return {key: (0 if key == "external_effects" else False) for key in AUTHORITY_KEYS}


def _default_zero_effect() -> dict[str, Any]:
    return {key: (0 if key.endswith("count") else False) for key in ZERO_EFFECT_KEYS}


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
            if (key_text in AUTHORITY_KEYS or key_text.endswith("authority") or key_text.endswith("_authorized")) and not isinstance(item, (Mapping, list, tuple)) and item not in (False, 0, None, "NONE", "NOT_VERIFIED"):
                found.append(f"authority_flag:{path}.{key}")
            found.extend(_authority_violations(item, path=f"{path}.{key}"))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            found.extend(_authority_violations(item, path=f"{path}[{index}]"))
    return found


def _hash_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return sorted({str(item) for item in value})


def _valid_hashes(values: Sequence[str]) -> bool:
    return bool(values) and all(SHA256_RE.fullmatch(value) for value in values)


def _trace_index(traceability_pack: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {str(row.get("claim_id")): row for row in traceability_pack.get("claim_traceability") or [] if isinstance(row, Mapping)}


def _validate_decision_pack(decision_pack: Mapping[str, Any], *, artifact_bytes: bytes | None = None) -> tuple[list[str], dict[str, Any]]:
    blockers: list[str] = []
    artifact_hash = sha256(artifact_bytes).hexdigest() if artifact_bytes is not None else None
    artifact = {
        "repository": MAIN_REPOSITORY,
        "ref": MAIN_REF,
        "commit": MAIN_HEAD,
        "path": MAIN_ARTIFACT_PATH,
        "bytes": len(artifact_bytes) if artifact_bytes is not None else None,
        "sha256": artifact_hash,
        "expected_sha256": MAIN_ARTIFACT_FILE_SHA256,
        "status": "SYNTHETIC" if artifact_bytes is None else ("SEALED_MATCH" if len(artifact_bytes) == MAIN_ARTIFACT_BYTES and artifact_hash == MAIN_ARTIFACT_FILE_SHA256 else "HASH_MISMATCH"),
    }
    if not isinstance(decision_pack, Mapping):
        return ["decision_pack_not_mapping"], artifact
    if decision_pack.get("schema") != MAIN_CONTRACT_SCHEMA or decision_pack.get("version") != "1.0.0":
        blockers.append("main_contract_schema_invalid")
    supplied = str(decision_pack.get("evaluation_sha256") or "")
    if not SHA256_RE.fullmatch(supplied) or supplied != sha256_without(decision_pack, "evaluation_sha256"):
        blockers.append("main_evaluation_hash_invalid")
    if artifact_bytes is not None and supplied != MAIN_EVALUATION_SHA256:
        blockers.append("main_evaluation_hash_mismatch")
    parent = decision_pack.get("parent_bindings") if isinstance(decision_pack.get("parent_bindings"), Mapping) else {}
    strict_parent = artifact_bytes is not None
    if strict_parent and (parent.get("goal10_bundle") or {}).get("bundle_sha256") != MAIN_BUNDLE_SHA256:
        blockers.append("goal10_bundle_binding_mismatch")
    if strict_parent and (parent.get("goal11_quality_ledger") or {}).get("quality_ledger_sha256") != MAIN_LEDGER_SHA256:
        blockers.append("goal11_ledger_binding_mismatch")
    if strict_parent and (parent.get("goal9_reconciliation") or {}).get("receipt_sha256") != GOAL9_RECEIPT_SHA256:
        blockers.append("goal9_receipt_binding_mismatch")
    source = parent.get("main_source") if isinstance(parent.get("main_source"), Mapping) else {}
    if source.get("head") != PARENT_MAIN_HEAD:
        blockers.append("main_parent_source_head_mismatch")
    if decision_pack.get("authority_flags") != _authority_flags():
        blockers.append("authority_flag")
    if _unknown_write(decision_pack):
        blockers.append("unknown_write")
    blockers.extend(_walk_secret(decision_pack))
    blockers.extend(_authority_violations(decision_pack))
    claims = decision_pack.get("claim_evaluations") if isinstance(decision_pack.get("claim_evaluations"), list) else []
    if not claims:
        blockers.append("claim_evaluations_missing")
    for row in claims:
        if not isinstance(row, Mapping):
            blockers.append("claim_evaluation_not_mapping")
            continue
        claim_id = str(row.get("claim_id") or "")
        hashes = _hash_list(row.get("source_hashes"))
        if not _valid_hashes(hashes):
            blockers.append(f"claim_source_hash_invalid:{claim_id}")
        eligibility = row.get("evaluation_eligibility") if isinstance(row.get("evaluation_eligibility"), Mapping) else {}
        if eligibility.get("authority") is not False:
            blockers.append(f"claim_authority:{claim_id}")
        if not isinstance(eligibility.get("blockers"), list):
            blockers.append(f"claim_blockers_missing:{claim_id}")
        if _unknown_write(row):
            blockers.append(f"unknown_write:{claim_id}")
    slots = decision_pack.get("outcome_slots") if isinstance(decision_pack.get("outcome_slots"), list) else []
    for slot in slots:
        if not isinstance(slot, Mapping):
            blockers.append("outcome_slot_not_mapping")
            continue
        if slot.get("outcome_state") not in OUTCOME_STATES:
            blockers.append(f"outcome_state_invalid:{slot.get('claim_id')}:{slot.get('slot_name')}")
    if artifact_bytes is not None:
        try:
            sealed = json.loads(artifact_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            blockers.append("main_artifact_json_invalid")
        else:
            if sealed != dict(decision_pack):
                blockers.append("main_artifact_payload_mismatch")
    return list(dict.fromkeys(blockers)), artifact


def _validate_traceability(traceability_pack: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if traceability_pack.get("schema_version") != TRACEABILITY_SCHEMA:
        blockers.append("traceability_schema_invalid")
    if not verify_editorial_traceability_quality_pack(traceability_pack):
        blockers.append("traceability_pack_verification_failed")
    if traceability_pack.get("main_source", {}).get("bundle_sha256") != MAIN_BUNDLE_SHA256:
        blockers.append("traceability_bundle_binding_mismatch")
    if traceability_pack.get("main_source", {}).get("ledger_sha256") != MAIN_LEDGER_SHA256:
        blockers.append("traceability_ledger_binding_mismatch")
    if _unknown_write(traceability_pack):
        blockers.append("unknown_write")
    blockers.extend(_walk_secret(traceability_pack))
    blockers.extend(_authority_violations(traceability_pack))
    return list(dict.fromkeys(blockers))


def _component(value: int | None, *, missing: str | None = None) -> dict[str, Any]:
    return {"value": value, "state": "OBSERVED" if value is not None else "NOT_COMPARABLE", "missing_reason": missing}


def _adjudicate(row: Mapping[str, Any], trace: Mapping[str, Any] | None, slots: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    claim_id = str(row.get("claim_id"))
    trace = trace or {}
    exactness = (trace.get("exact_proxy_context") or {}).get("state")
    quality = str(row.get("evaluation_eligibility", {}).get("status") or "NOT_COMPARABLE")
    blockers = [str(item) for item in row.get("evaluation_eligibility", {}).get("blockers") or []]
    trace_blockers = [str(item) for item in trace.get("core_eligibility", {}).get("blockers") or []]
    blockers.extend(trace_blockers)
    contradiction = trace.get("contradiction") if isinstance(trace.get("contradiction"), Mapping) else {}
    slot_rows = [slot for slot in slots if str(slot.get("claim_id")) == claim_id]
    comparability = {str(slot.get("comparability_class")) for slot in slot_rows}
    if _unknown_write(row) or _unknown_write(trace):
        decision, reason, band = "ABSTAINED", "UNKNOWN_WRITE", "P3_ABSTAIN"
    elif str(row.get("window_id")) == "CURRENT_REAL" or (trace.get("freshness") or {}).get("state") == "NOT_VERIFIED":
        decision, reason, band = "ABSTAINED", "CURRENT_REAL_NOT_VERIFIED", "P3_ABSTAIN"
    elif any("STALE" in item.upper() or "FUTURE" in item.upper() for item in blockers):
        decision, reason, band = "ABSTAINED", "STALE_OR_FUTURE", "P3_ABSTAIN"
    elif "rights_invalid" in {item.lower() for item in blockers} or (trace.get("rights") or {}).get("internal_analysis_allowed") is False:
        decision, reason, band = "ABSTAINED", "RIGHTS_INVALID", "P3_ABSTAIN"
    elif contradiction.get("state") == "UNRESOLVED_CONTRADICTION" or "contradiction_quarantined" in blockers:
        decision, reason, band = "QUARANTINED", "CONTRADICTION_QUARANTINED", "P4_QUARANTINE"
    elif exactness in {"PROXY", "CONTEXT_ONLY"}:
        decision, reason, band = "CONTEXT_ONLY", "PROXY_OR_CONTEXT_ONLY", "P2_CONTEXT"
    elif "HORIZON_UNIT_MISMATCH" in comparability or "CLOCK_MISMATCH" in comparability or "PROOF_LAYER_MISMATCH" in comparability:
        decision, reason, band = "ABSTAINED", sorted(comparability & {"HORIZON_UNIT_MISMATCH", "CLOCK_MISMATCH", "PROOF_LAYER_MISMATCH"})[0], "P3_ABSTAIN"
    elif quality in {"OUTCOME_PENDING", "COMPARABLE_EVALUATED"} and exactness == "EXACT":
        decision, reason, band = "PRIORITIZED", "EXACT_PIT_RIGHTS_POLICY", "P1_EDITORIAL"
    else:
        decision, reason, band = "ABSTAINED", quality or "NOT_COMPARABLE", "P3_ABSTAIN"
    source_hashes = _hash_list(row.get("source_hashes"))
    evidence_hashes = _hash_list(row.get("evidence_hashes")) or source_hashes
    unsupported = sorted(set(str(item) for item in row.get("unsupported_dimensions") or []) | set(str(item) for item in trace.get("unsupported_dimensions") or []))
    missing = []
    pit = trace.get("pit_state")
    freshness = trace.get("freshness") if isinstance(trace.get("freshness"), Mapping) else {}
    rights = trace.get("rights") if isinstance(trace.get("rights"), Mapping) else {}
    if not pit:
        missing.append("pit_state")
    if not freshness or freshness.get("state") in {None, "NOT_VERIFIED"}:
        missing.append("freshness")
    if not rights:
        missing.append("rights")
    if not trace.get("clocks"):
        missing.append("clock")
    if not trace.get("source_lineage"):
        missing.append("source_lineage")
    components = {
        "evidence_hash_count": _component(min(2, len(evidence_hashes)), missing=None if evidence_hashes else "evidence_hashes"),
        "lineage_complete": _component(1 if trace.get("source_lineage") else None, missing=None if trace.get("source_lineage") else "source_lineage"),
        "rights_compatible": _component(1 if rights.get("internal_analysis_allowed") is True else None, missing=None if rights else "rights"),
        "pit_compatible": _component(1 if pit else None, missing=None if pit else "pit_state"),
        "freshness_compatible": _component(1 if freshness.get("state") == "CURRENT" else None, missing=None if freshness.get("state") else "freshness"),
        "clock_compatible": _component(1 if trace.get("clocks") else None, missing=None if trace.get("clocks") else "clock"),
        "basis_risk": _component(1 if exactness in {"PROXY", "CONTEXT_ONLY"} or unsupported else 0),
        "unsupported_dimension_count": _component(len(unsupported)),
    }
    return {
        "claim_id": claim_id,
        "window_id": row.get("window_id"),
        "decision": decision,
        "priority_band": band,
        "decision_reason": reason,
        "source_hashes": source_hashes,
        "evidence_hashes": evidence_hashes,
        "duplicate_lineage": trace.get("dedupe") or row.get("dedupe_lineage") or {},
        "contradiction_lineage": contradiction,
        "exact_proxy_context": trace.get("exact_proxy_context") or {},
        "pit_freshness_rights": {"pit_state": pit, "freshness": freshness, "rights": rights},
        "horizon_unit_clock_compatibility": {"comparability_classes": sorted(comparability), "status": "NOT_COMPARABLE" if any(item != "PENDING" for item in comparability) else "PENDING"},
        "basis_risk_labels": sorted(set((["PROXY_CONTEXT_BASIS_RISK"] if exactness == "PROXY" else []) + (["CONTEXT_ONLY"] if exactness == "CONTEXT_ONLY" else []) + (["CONTRADICTION_BASIS_RISK"] if contradiction.get("state") == "UNRESOLVED_CONTRADICTION" else []) + (["UNSUPPORTED_DIMENSION"] if unsupported else []))),
        "unsupported_dimensions": unsupported,
        "priority_components": components,
        "missingness": {"state": "OBSERVED" if not missing else "NOT_COMPARABLE", "missing_components": sorted(set(missing))},
        "outcome_states": [
            {"slot_name": slot.get("slot_name"), "proof_layer": slot.get("proof_layer"), "outcome_state": slot.get("outcome_state"), "comparability_class": slot.get("comparability_class"), "evidence_hash": slot.get("evidence_hash")}
            for slot in slot_rows
        ],
        "authority": False,
    }


def _classification(blockers: Sequence[str], decision_pack: Mapping[str, Any], traceability_pack: Mapping[str, Any], derivative_count: int) -> str:
    text = " ".join(blockers).lower()
    candidate_text = " ".join(
        str(item)
        for row in decision_pack.get("claim_evaluations") or []
        if isinstance(row, Mapping)
        for item in (row.get("evaluation_eligibility") or {}).get("blockers") or []
    ).lower()
    if "unknown_write" in text:
        return "UNKNOWN_WRITE"
    if "authority" in text:
        return "AUTHORITY_FLAG"
    if "stale" in text or "future" in text or "stale" in candidate_text or "future" in candidate_text:
        return "STALE"
    if "hash" in text or "tampered" in text or "payload_mismatch" in text:
        return "PACKET_HASH_MISMATCH"
    if "head" in text or "source" in text and "mismatch" in text:
        return "SOURCE_HEAD_MISMATCH"
    if str((decision_pack.get("quality_counts") or {}).get("classification")) == "AMBIGUOUS":
        return "AMBIGUOUS"
    if str((decision_pack.get("quality_counts") or {}).get("classification")) != "NONE" or str(traceability_pack.get("classification")) != "SHADOW_CONFIRMED" or derivative_count not in {0, len(V1_REQUIRED_DERIVATIVE_DESTINATIONS)}:
        return "NOT_VERIFIED"
    return "SHADOW_CONFIRMED"


def build_editorial_adjudication_prioritization_pack(
    decision_pack: Mapping[str, Any],
    traceability_pack: Mapping[str, Any],
    *,
    artifact_bytes: bytes | None = None,
) -> dict[str, Any]:
    """Build the adjudication pack over one exact Main evaluation and one Goal 12 pack."""

    blockers, artifact = _validate_decision_pack(decision_pack, artifact_bytes=artifact_bytes)
    blockers.extend(_validate_traceability(traceability_pack))
    if traceability_pack.get("contentops_source", {}).get("head") not in {CONTENTOPS_HEAD, PARENT_GOAL12_CONTENTOPS_HEAD}:
        blockers.append("contentops_source_head_mismatch")
    trace_index = _trace_index(traceability_pack)
    slots = decision_pack.get("outcome_slots") if isinstance(decision_pack.get("outcome_slots"), list) else []
    candidates = [_adjudicate(row, trace_index.get(str(row.get("claim_id"))), slots) for row in decision_pack.get("claim_evaluations") or [] if isinstance(row, Mapping)]
    for row in candidates:
        for reason in row.get("decision_reason"), *[str(item) for item in row.get("outcome_states") or [] if isinstance(item, Mapping) and item.get("comparability_class") in {"HORIZON_UNIT_MISMATCH", "CLOCK_MISMATCH", "PROOF_LAYER_MISMATCH"}]:
            if reason:
                blockers.append(f"candidate:{row['claim_id']}:{reason}")
    order = {"PRIORITIZED": 0, "CONTEXT_ONLY": 1, "ABSTAINED": 2, "QUARANTINED": 3}
    prioritized = sorted(candidates, key=lambda row: (order.get(str(row["decision"]), 9), -int((row["priority_components"]["evidence_hash_count"]["value"] or 0)), str(row["claim_id"])))
    selected_ids = [row["claim_id"] for row in candidates if row["decision"] == "PRIORITIZED"]
    context_ids = [row["claim_id"] for row in candidates if row["decision"] == "CONTEXT_ONLY"]
    abstained_ids = [row["claim_id"] for row in candidates if row["decision"] == "ABSTAINED"]
    quarantined_ids = [row["claim_id"] for row in candidates if row["decision"] == "QUARANTINED"]
    trace_editorial = traceability_pack.get("claim_to_editorial") if isinstance(traceability_pack.get("claim_to_editorial"), Mapping) else {}
    trace_derivative = traceability_pack.get("claim_to_derivative") if isinstance(traceability_pack.get("claim_to_derivative"), Mapping) else {}
    packages = [dict(row) for row in trace_derivative.get("packages") or [] if isinstance(row, Mapping)]
    if traceability_pack.get("classification") == "SHADOW_CONFIRMED" and (len(packages) != len(V1_REQUIRED_DERIVATIVE_DESTINATIONS) or {row.get("destination") for row in packages} != set(V1_REQUIRED_DERIVATIVE_DESTINATIONS)):
        blockers.append("derivative_count_or_destination_mismatch")
    if any(row.get("public_write_performed") is True for row in packages):
        blockers.append("unknown_write")
    source_hashes_by_claim = {row["claim_id"]: row["source_hashes"] for row in candidates}
    draft_sections = []
    for section in trace_editorial.get("draft_sections") or []:
        section = dict(section)
        claim_ids = [str(item) for item in section.get("claim_ids") or []]
        section["source_hashes"] = sorted({item for claim_id in claim_ids for item in source_hashes_by_claim.get(claim_id, [])})
        section["evidence_hashes"] = sorted({item for row in candidates if row["claim_id"] in claim_ids for item in row["evidence_hashes"]})
        draft_sections.append(section)
    article_map = {
        "article_id": trace_derivative.get("article_id"),
        "claim_ids": selected_ids,
        "source_hashes": sorted({item for claim_id in selected_ids for item in source_hashes_by_claim.get(claim_id, [])}),
        "evidence_hashes": sorted({item for row in candidates if row["claim_id"] in selected_ids for item in row["evidence_hashes"]}),
        "status": "SHADOW_CONFIRMED" if trace_derivative.get("article_id") else "NOT_VERIFIED",
        "public_write_performed": False,
    }
    derivative_map = []
    for package in packages:
        item = dict(package)
        claim_ids = [str(value) for value in item.get("claim_ids") or selected_ids]
        item["claim_ids"] = claim_ids
        item["source_hashes"] = sorted({item2 for claim_id in claim_ids for item2 in source_hashes_by_claim.get(claim_id, item.get("source_hashes") or [])})
        item["evidence_hashes"] = sorted({item2 for row in candidates if row["claim_id"] in claim_ids for item2 in row["evidence_hashes"]})
        item["public_write_performed"] = False
        derivative_map.append(item)
    outcomes = []
    for slot in slots:
        outcomes.append({key: slot.get(key) for key in ("claim_id", "window_id", "slot_name", "proof_layer", "outcome_state", "comparability_class", "evidence_hash", "known_at_utc", "horizon", "unit")})
    counts = {
        "candidate_count": len(candidates),
        "prioritized_count": len(selected_ids),
        "context_only_count": len(context_ids),
        "abstained_count": len(abstained_ids),
        "quarantined_count": len(quarantined_ids),
        "derivative_count": len(derivative_map),
        "outcome_pending_count": sum(row.get("outcome_state") == "OUTCOME_PENDING" for row in outcomes),
        "not_comparable_count": sum(row.get("outcome_state") == "NOT_COMPARABLE" for row in outcomes),
        "not_verified_count": sum(row.get("outcome_state") == "NOT_VERIFIED" for row in outcomes),
        "observed_count": sum(row.get("outcome_state") == "OBSERVED" for row in outcomes),
        "source_hash_count": len({item for row in candidates for item in row["source_hashes"]}),
    }
    zero = traceability_pack.get("zero_effect") if isinstance(traceability_pack.get("zero_effect"), Mapping) else {}
    zero_effect = {key: zero.get(key) for key in ZERO_EFFECT_KEYS}
    if any(value not in (False, 0, None) for value in zero_effect.values()):
        blockers.append("zero_effect_not_zero")
    if any(value is None for value in zero_effect.values()):
        blockers.append("zero_effect_incomplete")
    quality = decision_pack.get("quality_counts") if isinstance(decision_pack.get("quality_counts"), Mapping) else {}
    classification = _classification(blockers, decision_pack, traceability_pack, len(derivative_map))
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
            "requested_contract_schema": REQUESTED_MAIN_CONTRACT_SCHEMA,
            "observed_contract_schema": MAIN_CONTRACT_SCHEMA,
            "artifact_path": MAIN_ARTIFACT_PATH,
            "artifact_bytes": MAIN_ARTIFACT_BYTES,
            "artifact_file_sha256": MAIN_ARTIFACT_FILE_SHA256,
            "evaluation_sha256": MAIN_EVALUATION_SHA256,
            "bundle_sha256": MAIN_BUNDLE_SHA256,
            "quality_ledger_sha256": MAIN_LEDGER_SHA256,
        },
        "contentops_source": {"repository": "fatcat2109/capital-chronicle-contentops", "ref": "master", "head": CONTENTOPS_HEAD, "goal11_head": GOAL11_CONTENTOPS_HEAD},
        "artifact": artifact,
        "parent_bindings": {
            "goal9_reconciliation_sha256": GOAL9_RECEIPT_SHA256,
            "goal10_bundle_sha256": MAIN_BUNDLE_SHA256,
            "goal11_quality_ledger_sha256": MAIN_LEDGER_SHA256,
            "goal12_traceability_pack_sha256": traceability_pack.get("pack_sha256"),
            "goal12_traceability_schema": traceability_pack.get("schema_version"),
        },
        "policy_matrix": {
            "EXACT_CURRENT_RIGHTS_PIT_COMPATIBLE": "PRIORITIZED_FOR_EDITORIAL",
            "RECENT_REPLAY_CLOCK_HORIZON_RIGHTS_COMPATIBLE": "PRIORITIZED_REPLAY_CONTEXT_ONLY_UNLESS_EXPLICITLY_COMPATIBLE",
            "PROXY_OR_CONTEXT": "CONTEXT_ONLY_WITH_BASIS_RISK",
            "CONTRADICTION": "QUARANTINED_KEEP_BOTH_SOURCE_HASHES",
            "STALE_FUTURE_RIGHTS_UNKNOWN_WRITE_AMBIGUOUS": "ABSTAIN_FAIL_CLOSED",
            "OUTCOME_MISSING": "OUTCOME_PENDING_OR_NOT_COMPARABLE",
        },
        "candidate_adjudications": prioritized,
        "editorial_priority_matrix": {
            "components_are_bounded_integer_metadata": True,
            "aggregate_score_created": False,
            "audience_score_created": False,
            "forecast_score_created": False,
            "rows": [{"claim_id": row["claim_id"], "decision": row["decision"], "priority_band": row["priority_band"], "components": row["priority_components"], "missingness": row["missingness"]} for row in prioritized],
            "ordering": [row["claim_id"] for row in prioritized],
        },
        "claim_to_draft_sections": draft_sections,
        "claim_to_canonical_article": article_map,
        "claim_to_eight_derivatives": derivative_map,
        "destination_shadow": {"destinations": derivative_map, "readback_shadow_sha256": trace_derivative.get("destination_readback_shadow_sha256"), "interruption_resume": trace_derivative.get("interruption_resume", "NOT_ATTEMPTED"), "public_write_performed": False},
        "outcome_boundary_map": {"states_allowed": sorted(OUTCOME_STATES), "proof_layers_preserved": ["RETROSPECTIVE_REPLAY", "PROSPECTIVE_NATURAL_OBSERVATION", "PAPER_SIMULATION", "RUNTIME_PROVEN", "REALIZED_EXECUTION", "PROXY_CONTEXT"], "slots": outcomes, "performance_claims_created": False, "forecast_claims_created": False, "runtime_claims_created": False, "realized_claims_created": False},
        "abstention_quarantine_ledger": {"prioritized_claim_ids": selected_ids, "context_only_claim_ids": context_ids, "abstained_claim_ids": abstained_ids, "quarantined_claim_ids": quarantined_ids, "reasons": {row["claim_id"]: row["decision_reason"] for row in candidates if row["decision"] != "PRIORITIZED"}},
        "quality_counts": {"classification": str(quality.get("classification") or "NOT_VERIFIED"), "counts": counts, "source_quality_summary": dict(quality), "exact_blocker": quality.get("exact_blocker"), "exact_next_action": quality.get("exact_next_action") or "Preserve missingness and obtain exact evidence before promotion.", "quality_state": quality.get("quality_state", "DEGRADED")},
        "proof_axes": {"artifact_hash": artifact["status"] == "SEALED_MATCH", "main_evaluation_hash": not any("evaluation_hash" in item for item in blockers), "parent_bindings": not any("binding" in item for item in blockers), "candidate_lineage": bool(candidates), "priority_matrix": bool(prioritized), "derivative_mapping": len(derivative_map) in {0, len(V1_REQUIRED_DERIVATIVE_DESTINATIONS)}, "runtime_proven": False, "publicly_proven": False},
        "zero_effect": zero_effect,
        "authority_flags": _authority_flags(),
        "classification": classification,
        "blockers": list(dict.fromkeys(str(item) for item in blockers)),
        "next": "RETAIN_ADJUDICATION_PACK_AND_HAND_TO_MAIN_FOR_NEXT_PRIORITIZATION_CONSUMER",
        "pack_sha256": None,
    }
    pack["pack_sha256"] = pack_sha256(pack)
    return pack


def verify_editorial_adjudication_prioritization_pack(pack: Mapping[str, Any]) -> bool:
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
        counts = pack.get("quality_counts", {}).get("counts") if isinstance(pack.get("quality_counts"), Mapping) else {}
        if any(not isinstance(value, int) or isinstance(value, bool) for value in counts.values()):
            return False
        if pack.get("classification") not in CLASSIFICATIONS:
            return False
        if _walk_secret(pack) or _unknown_write(pack) or _authority_violations(pack):
            return False
        matrix = pack.get("editorial_priority_matrix") if isinstance(pack.get("editorial_priority_matrix"), Mapping) else {}
        if matrix.get("aggregate_score_created") is not False or matrix.get("audience_score_created") is not False or matrix.get("forecast_score_created") is not False:
            return False
        packages = pack.get("claim_to_eight_derivatives") or []
        if pack.get("classification") == "SHADOW_CONFIRMED" and ({row.get("destination") for row in packages} != set(V1_REQUIRED_DERIVATIVE_DESTINATIONS) or len(packages) != 8):
            return False
        for row in pack.get("candidate_adjudications") or []:
            if row.get("decision") not in DECISIONS or not _valid_hashes(row.get("source_hashes") or []):
                return False
            for component in (row.get("priority_components") or {}).values():
                if component.get("value") is not None and (not isinstance(component.get("value"), int) or isinstance(component.get("value"), bool)):
                    return False
        for slot in pack.get("outcome_boundary_map", {}).get("slots") or []:
            if slot.get("outcome_state") not in OUTCOME_STATES:
                return False
        return True
    except (KeyError, TypeError, ValueError):
        return False


__all__ = [
    "MAIN_ARTIFACT_BYTES",
    "MAIN_ARTIFACT_FILE_SHA256",
    "MAIN_ARTIFACT_PATH",
    "MAIN_EVALUATION_SHA256",
    "MAIN_HEAD",
    "SCHEMA_VERSION",
    "build_editorial_adjudication_prioritization_pack",
    "canonical_bytes",
    "pack_sha256",
    "verify_editorial_adjudication_prioritization_pack",
]
