"""Bidirectional Main decision to ContentOps editorial quality feedback.

Main keeps analytical/Core eligibility authority. ContentOps reports only editorial handling,
traceability, disagreement, and quality evidence. The pack is deterministic, read-only, and
shadow-only; it never creates scores, forecasts, runtime/public claims, or a second owner.
"""

from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence

from live_contentops.destination_transport_registry_v1 import (
    V1_REQUIRED_DERIVATIVE_DESTINATIONS,
)
from live_contentops.editorial_traceability_quality_pack_v1 import (
    SCHEMA_VERSION as TRACEABILITY_SCHEMA,
    verify_editorial_traceability_quality_pack,
)

SCHEMA_VERSION = "contentops.decision_editorial_feedback_quality_pack.v1"
VERSION = "1.0.0"
CANONICALIZATION = "JSON_SORT_KEYS_COMPACT_ASCII_UTF8_NO_FLOAT_NAN"
MAIN_SCHEMA = "CapitalChronicleDecisionEvidencePrioritizationPackV1"
MAIN_REPOSITORY = "fatcat2109/Headline-Raw-data-json"
MAIN_REF = "main"
MAIN_HEAD = "1bbb21dc1e2c9dbf6b09ada84fc45d98101b6e62"
MAIN_ARTIFACT_PATH = (
    "tests/fixtures/decision_evidence_prioritization_pack_current_v1.json"
)
MAIN_ARTIFACT_BYTES = 45748
MAIN_ARTIFACT_FILE_SHA256 = (
    "4e5a1131326f55533e9e9fe654f76156e8d03873f6f2a6b323056c6df386ed6c"
)
MAIN_PACK_SHA256 = "9f42139c1f188eda32051d0dfc1aa5786ee2b1743ba7fb7f9794e82804d420ed"
GOAL9_RECEIPT_SHA256 = (
    "313631f2c3c16ce8fa0de5de7d08aefe961caecbfa4d1e95842c7e43a3cddc29"
)
GOAL10_BUNDLE_SHA256 = (
    "9e113fd45caf623458f7bb2adfe9b43fe204cb10d96abe62b718f6a13affaed9"
)
GOAL11_LEDGER_SHA256 = (
    "834d5fb73a4a299392419cde850b0adb0e5746fb6fdfc14743f13077d75c8697"
)
GOAL12_EVALUATION_SHA256 = (
    "ae67ad70a7a692a7c92003a3fb3d4869fd3898ee3dc5b0ed07166c39c960a043"
)
CONTENTOPS_HEAD = "be87f8ab1efc4b98fc1b78a4bbeb9ab4c8c27a4d"
GOAL13_CONTENTOPS_HEAD = "49ad25dc2b3e741d4e60f2de057a99b91d8e4021"
GOAL12_CONTENTOPS_HEAD = "a0c62b3470ad801bc38efae2ef6671d3ad3ef2d0"
PARENT_MAIN_HEAD = "8f66238d320062e9258c893d59d2293253655f94"
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
        "AMBIGUOUS",
        "STALE",
        "UNKNOWN_WRITE",
        "AUTHORITY_FLAG",
        "PACKET_HASH_MISMATCH",
        "SOURCE_HEAD_MISMATCH",
    }
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SECRET_RE = re.compile(
    r"(?i)(?:bearer\s+[A-Za-z0-9._~+/=-]{8,}|(?:sk|pk|rk)-[A-Za-z0-9_-]{12,})"
)
SENSITIVE_RE = re.compile(
    r"(?i)(?:^|_)(?:access[_-]?token|refresh[_-]?token|cookie|password|secret|authorization|api[_-]?key|private[_-]?key|session[_-]?token|webhook[_-]?url)(?:$|_)"
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def sha256_without(value: Mapping[str, Any], field: str) -> str:
    return sha256(
        canonical_bytes({k: v for k, v in value.items() if k != field})
    ).hexdigest()


def pack_sha256(value: Mapping[str, Any]) -> str:
    return sha256_without(value, "pack_sha256")


def _authority_flags() -> dict[str, Any]:
    return {key: (0 if key == "external_effects" else False) for key in AUTHORITY_KEYS}


def _walk_secret(value: Any, path: str = "root") -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if SENSITIVE_RE.search(key_text):
                found.append(f"secret_material:{path}.{key_text}")
            found.extend(_walk_secret(item, f"{path}.{key_text}"))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for idx, item in enumerate(value):
            found.extend(_walk_secret(item, f"{path}[{idx}]"))
    elif isinstance(value, str) and SECRET_RE.search(value):
        found.append(f"secret_material:{path}")
    return found


def _unknown_write(value: Any) -> bool:
    if isinstance(value, Mapping):
        if (
            value.get("unknown_write") is True
            or str(value.get("status") or "") == "UNKNOWN_WRITE"
        ):
            return True
        return any(_unknown_write(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_unknown_write(item) for item in value)
    return str(value).upper() == "UNKNOWN_WRITE"


def _hashes(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return sorted({str(item) for item in value})


def _validate_parent(
    main_pack: Mapping[str, Any],
    contentops_pack: Mapping[str, Any],
    artifact_bytes: bytes | None,
) -> tuple[list[str], dict[str, Any]]:
    blockers: list[str] = []
    raw_hash = (
        sha256(artifact_bytes).hexdigest() if artifact_bytes is not None else None
    )
    artifact = {
        "repository": MAIN_REPOSITORY,
        "ref": MAIN_REF,
        "commit": MAIN_HEAD,
        "path": MAIN_ARTIFACT_PATH,
        "bytes": len(artifact_bytes) if artifact_bytes is not None else None,
        "sha256": raw_hash,
        "expected_sha256": MAIN_ARTIFACT_FILE_SHA256,
        "status": "SYNTHETIC"
        if artifact_bytes is None
        else (
            "SEALED_MATCH"
            if len(artifact_bytes) == MAIN_ARTIFACT_BYTES
            and raw_hash == MAIN_ARTIFACT_FILE_SHA256
            else "HASH_MISMATCH"
        ),
    }
    if main_pack.get("schema") != MAIN_SCHEMA:
        blockers.append("main_schema_invalid")
    if main_pack.get("pack_sha256") != sha256_without(main_pack, "pack_sha256"):
        blockers.append("main_pack_hash_invalid")
    if artifact_bytes is not None and main_pack.get("pack_sha256") != MAIN_PACK_SHA256:
        blockers.append("main_pack_hash_mismatch")
    if contentops_pack.get("schema_version") != TRACEABILITY_SCHEMA:
        blockers.append("contentops_schema_invalid")
    if not verify_editorial_traceability_quality_pack(contentops_pack):
        blockers.append("contentops_pack_verification_failed")
    if (
        contentops_pack.get("main_source", {}).get("ledger_sha256")
        != GOAL11_LEDGER_SHA256
    ):
        blockers.append("contentops_ledger_binding_mismatch")
    parent = (
        main_pack.get("parent_bindings")
        if isinstance(main_pack.get("parent_bindings"), Mapping)
        else {}
    )
    checks = {
        "goal9_receipt": (parent.get("goal9_reconciliation", {}) or {}).get(
            "receipt_sha256"
        ),
        "goal10_bundle": (parent.get("goal10_bundle", {}) or {}).get("bundle_sha256"),
        "goal11_ledger": (parent.get("goal11_quality_ledger", {}) or {}).get(
            "quality_ledger_sha256"
        ),
        "goal12_evaluation": (parent.get("goal12_outcome_evaluation", {}) or {}).get(
            "evaluation_sha256"
        ),
    }
    expected = {
        "goal9_receipt": GOAL9_RECEIPT_SHA256,
        "goal10_bundle": GOAL10_BUNDLE_SHA256,
        "goal11_ledger": GOAL11_LEDGER_SHA256,
        "goal12_evaluation": GOAL12_EVALUATION_SHA256,
    }
    strict_parent = artifact_bytes is not None
    for name, value in checks.items():
        if strict_parent and value != expected[name]:
            blockers.append(f"{name}_binding_mismatch")
    if _unknown_write(main_pack) or _unknown_write(contentops_pack):
        blockers.append("unknown_write")
    blockers.extend(_walk_secret(main_pack))
    blockers.extend(_walk_secret(contentops_pack))
    return list(dict.fromkeys(blockers)), artifact


def _candidate_map(pack: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        str(row.get("candidate_id", "")).removeprefix("decision:"): row
        for row in pack.get("decision_candidates", [])
        if isinstance(row, Mapping)
    }


def _editorial_map(pack: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        str(row.get("claim_id")): row
        for row in pack.get("candidate_adjudications", [])
        if isinstance(row, Mapping)
    }


def _decision(main: Mapping[str, Any]) -> str:
    core = (
        main.get("core_eligibility", {}).get("admitted_to_core_shaped_projection")
        is True
    )
    editorial = main.get("editorial_relevance", {}).get("status")
    if core:
        return "CORE_ADMITTED"
    if editorial == "CONTEXT_ONLY":
        return "EDITORIAL_CONTEXT"
    if main.get("contradiction", {}).get("state") == "UNRESOLVED_CONTRADICTION":
        return "QUARANTINED"
    return "ABSTAINED"


def _feedback(
    main: Mapping[str, Any] | None, editorial: Mapping[str, Any] | None
) -> dict[str, Any]:
    main = main or {}
    editorial = editorial or {}
    main_id = str(main.get("candidate_id", ""))
    claim_id = main_id.removeprefix("decision:")
    main_decision = _decision(main) if main else "MISSING_MAIN_CANDIDATE"
    content_decision = str(
        editorial.get("decision") or "MISSING_CONTENTOPS_ADJUDICATION"
    )
    m_hashes = _hashes(main.get("source_hashes"))
    c_hashes = _hashes(editorial.get("source_hashes"))
    reasons: list[str] = []
    if not main:
        reasons.append("MAIN_CANDIDATE_MISSING")
    if not editorial:
        reasons.append("CONTENTOPS_ADJUDICATION_MISSING")
    if m_hashes != c_hashes:
        reasons.append("SOURCE_HASH_DISAGREEMENT")
    if (
        main
        and editorial
        and main.get("exact_proxy_context") != editorial.get("exact_proxy_context")
    ):
        reasons.append("EXACT_PROXY_CONTEXT_DISAGREEMENT")
    if (
        main
        and editorial
        and main.get("rights")
        != editorial.get("pit_freshness_rights", {}).get("rights")
    ):
        reasons.append("RIGHTS_DISAGREEMENT")
    main_reasons = (
        [str(x) for x in main.get("abstention_reasons") or []] if main else []
    )
    editorial_reason = str(editorial.get("decision_reason") or "")
    if (
        main_reasons
        and editorial_reason
        and not any(editorial_reason.lower() in x.lower() for x in main_reasons)
    ):
        reasons.append("DECISION_REASON_DISAGREEMENT")
    agreement = not reasons
    return {
        "claim_id": claim_id,
        "main_candidate_id": main_id,
        "main_decision": main_decision,
        "contentops_decision": content_decision,
        "agreement": agreement,
        "agreement_state": "AGREE" if agreement else "DISAGREE",
        "disagreement_reasons": sorted(set(reasons)),
        "main_source_hashes": m_hashes,
        "contentops_source_hashes": c_hashes,
        "source_hashes": sorted(set(m_hashes) | set(c_hashes)),
        "main_evidence_hashes": _hashes(main.get("evidence_hashes")),
        "contentops_evidence_hashes": _hashes(editorial.get("evidence_hashes")),
        "duplicate_lineage": editorial.get("duplicate_lineage")
        or main.get("dedupe_lineage")
        or {},
        "contradiction_lineage": editorial.get("contradiction_lineage")
        or main.get("contradiction")
        or {},
        "exact_proxy_context": {
            "main": main.get("exact_proxy_context") or {},
            "contentops": editorial.get("exact_proxy_context") or {},
        },
        "pit_freshness_rights_horizon_unit_clock": {
            "main": {
                "pit": main.get("pit_state"),
                "freshness": main.get("freshness"),
                "rights": main.get("rights"),
                "compatibility": main.get("horizon_unit_currency_clock_compatibility"),
            },
            "contentops": {
                "pit": editorial.get("pit_freshness_rights", {}).get("pit_state"),
                "freshness": editorial.get("pit_freshness_rights", {}).get("freshness"),
                "rights": editorial.get("pit_freshness_rights", {}).get("rights"),
                "compatibility": editorial.get("horizon_unit_clock_compatibility"),
            },
        },
        "unsupported_dimensions": sorted(
            set(main.get("unsupported_dimensions") or [])
            | set(editorial.get("unsupported_dimensions") or [])
        ),
        "authority": False,
    }


def _component(
    value: int | None, state: str, missing: str | None = None
) -> dict[str, Any]:
    return {
        "value": value,
        "state": state,
        "missingness_reason": missing,
        "comparability": state in {"AVAILABLE", "OBSERVED"},
    }


def build_decision_editorial_feedback_quality_pack(
    main_pack: Mapping[str, Any],
    contentops_pack: Mapping[str, Any],
    *,
    traceability_pack: Mapping[str, Any] | None = None,
    artifact_bytes: bytes | None = None,
) -> dict[str, Any]:
    traceability_pack = traceability_pack or contentops_pack
    blockers, artifact = _validate_parent(main_pack, traceability_pack, artifact_bytes)
    if (
        contentops_pack.get("schema_version")
        != "contentops.editorial_adjudication_prioritization_pack.v1"
    ):
        blockers.append("contentops_adjudication_schema_invalid")
    if contentops_pack.get("pack_sha256") != sha256_without(
        contentops_pack, "pack_sha256"
    ):
        blockers.append("contentops_adjudication_hash_invalid")
    mains = _candidate_map(main_pack)
    editorials = _editorial_map(contentops_pack)
    ids = sorted(set(mains) | set(editorials))
    feedback = [_feedback(mains.get(cid), editorials.get(cid)) for cid in ids]
    trace_editorial = (
        traceability_pack.get("claim_to_editorial")
        if isinstance(traceability_pack.get("claim_to_editorial"), Mapping)
        else {}
    )
    trace_derivative = (
        traceability_pack.get("claim_to_derivative")
        if isinstance(traceability_pack.get("claim_to_derivative"), Mapping)
        else {}
    )
    sections = [
        dict(row)
        for row in trace_editorial.get("draft_sections") or []
        if isinstance(row, Mapping)
    ]
    article = dict(trace_derivative)
    packages = [
        dict(row)
        for row in trace_derivative.get("packages") or []
        if isinstance(row, Mapping)
    ]
    all_claim_ids = set(ids)
    section_claim_ids = {
        str(cid) for row in sections for cid in row.get("claim_ids") or []
    }
    derivative_claim_ids = {
        str(cid) for row in packages for cid in row.get("claim_ids") or []
    }
    orphan_sections = sorted(section_claim_ids - all_claim_ids)
    orphan_derivatives = sorted(derivative_claim_ids - all_claim_ids)
    duplicate_payloads = sorted(
        payload
        for payload, count in __import__("collections")
        .Counter(str(row.get("payload_sha256")) for row in packages)
        .items()
        if count > 1
    )
    if orphan_sections:
        blockers.append("orphan_draft_section")
    if orphan_derivatives:
        blockers.append("orphan_derivative")
    if duplicate_payloads:
        blockers.append("duplicate_derivative_payload")
    if len(packages) not in {0, len(V1_REQUIRED_DERIVATIVE_DESTINATIONS)}:
        blockers.append("derivative_count_mismatch")
    if len(packages) == len(V1_REQUIRED_DERIVATIVE_DESTINATIONS) and {
        row.get("destination") for row in packages
    } != set(V1_REQUIRED_DERIVATIVE_DESTINATIONS):
        blockers.append("destination_set_mismatch")
    if any(
        row.get("contradiction_lineage", {}).get("state") == "UNRESOLVED_CONTRADICTION"
        and row.get("contentops_decision") != "QUARANTINED"
        for row in feedback
    ):
        blockers.append("contradiction_feedback_mismatch")
    main_ids = set(mains)
    editor_ids = set(editorials)
    if main_ids != editor_ids:
        blockers.append("candidate_set_disagreement")
    quality_rows = []
    for name, values in {
        "source_coverage": [bool(row.get("source_hashes")) for row in feedback],
        "lineage_completeness": [
            bool(row.get("duplicate_lineage")) for row in feedback
        ],
        "contradiction_handling": [
            row.get("contentops_decision") == "QUARANTINED"
            for row in feedback
            if row.get("contradiction_lineage", {}).get("state")
            == "UNRESOLVED_CONTRADICTION"
        ],
        "abstention_fidelity": [row.get("agreement") for row in feedback],
        "exact_proxy_separation": [
            row.get("contentops_decision") != "PRIORITIZED"
            for row in feedback
            if (row.get("exact_proxy_context", {}).get("contentops") or {}).get("state")
            in {"PROXY", "CONTEXT_ONLY"}
        ],
        "outcome_state_fidelity": [
            bool(main.get("outcome_states")) for main in editorials.values()
        ],
        "derivative_consistency": [bool(row.get("source_hashes")) for row in packages],
        "destination_shadow_consistency": [
            row.get("public_write_performed") is False for row in packages
        ],
    }.items():
        available = [bool(x) for x in values]
        quality_rows.append(
            {
                "component": name,
                "count": sum(available) if values else None,
                "state": "AVAILABLE" if values else "NOT_COMPARABLE",
                "missingness_reason": None if values else "NO_ROWS",
            }
        )
    outcomes = []
    for row in main_pack.get("outcome_links") or []:
        outcomes.append(
            {
                key: row.get(key)
                for key in (
                    "candidate_id",
                    "claim_id",
                    "slot_name",
                    "proof_layer",
                    "outcome_state",
                    "comparability_class",
                    "evidence_hash",
                )
            }
        )
    selected = set(trace_derivative.get("canonical_article_claim_ids") or [])
    classifications = (
        "SHADOW_CONFIRMED"
        if not blockers
        and contentops_pack.get("classification") == "SHADOW_CONFIRMED"
        and artifact["status"] in {"SEALED_MATCH", "SYNTHETIC"}
        else "NOT_VERIFIED"
    )
    if any("unknown_write" in x for x in blockers):
        classifications = "UNKNOWN_WRITE"
    if any("authority" in x for x in blockers):
        classifications = "AUTHORITY_FLAG"
    if any("hash" in x for x in blockers):
        classifications = "PACKET_HASH_MISMATCH"
    if any("head" in x for x in blockers):
        classifications = "SOURCE_HEAD_MISMATCH"
    zero = (
        contentops_pack.get("zero_effect")
        if isinstance(contentops_pack.get("zero_effect"), Mapping)
        else {}
    )
    zero_effect = {key: zero.get(key) for key in ZERO_EFFECT_KEYS}
    if any(value not in (False, 0, None) for value in zero_effect.values()):
        blockers.append("zero_effect_not_zero")
    if any(value is None for value in zero_effect.values()):
        blockers.append("zero_effect_incomplete")
    pack = {
        "schema_version": SCHEMA_VERSION,
        "version": VERSION,
        "canonicalization": CANONICALIZATION,
        "status": classifications,
        "immutable_pack": True,
        "shadow_only": True,
        "source_state": "MERGED_MAIN_ARCHIVE"
        if artifact["status"] == "SEALED_MATCH"
        else "SYNTHETIC",
        "main_source": {
            "repository": MAIN_REPOSITORY,
            "ref": MAIN_REF,
            "head": MAIN_HEAD,
            "artifact_path": MAIN_ARTIFACT_PATH,
            "artifact_bytes": MAIN_ARTIFACT_BYTES,
            "artifact_file_sha256": MAIN_ARTIFACT_FILE_SHA256,
            "pack_sha256": MAIN_PACK_SHA256,
            "schema": MAIN_SCHEMA,
        },
        "contentops_source": {
            "repository": "fatcat2109/capital-chronicle-contentops",
            "ref": "master",
            "head": CONTENTOPS_HEAD,
            "goal13_head": GOAL13_CONTENTOPS_HEAD,
        },
        "artifact": artifact,
        "parent_bindings": {
            "goal9_receipt_sha256": GOAL9_RECEIPT_SHA256,
            "goal10_bundle_sha256": GOAL10_BUNDLE_SHA256,
            "goal11_ledger_sha256": GOAL11_LEDGER_SHA256,
            "goal12_evaluation_sha256": GOAL12_EVALUATION_SHA256,
            "goal13_main_pack_sha256": MAIN_PACK_SHA256,
            "goal13_contentops_pack_sha256": contentops_pack.get("pack_sha256"),
        },
        "candidate_feedback": feedback,
        "editorial_quality_matrix": quality_rows,
        "section_traceability": {
            "sections": sections,
            "orphan_claim_ids": orphan_sections,
        },
        "canonical_article_traceability": {
            "article": article,
            "claim_ids": sorted(selected),
            "source_hashes": article.get("source_hashes") or [],
            "evidence_hashes": article.get("evidence_hashes") or [],
        },
        "eight_derivative_traceability": {
            "packages": packages,
            "orphan_claim_ids": orphan_derivatives,
            "destination_count": len(packages),
        },
        "destination_shadow_traceability": {
            "readback_shadow_sha256": trace_derivative.get(
                "destination_readback_shadow_sha256"
            ),
            "interruption_resume": trace_derivative.get(
                "interruption_resume", "NOT_ATTEMPTED"
            ),
            "public_write_performed": False,
            "destinations": [row.get("destination") for row in packages],
        },
        "feedback_disagreements": [row for row in feedback if not row.get("agreement")],
        "abstention_quarantine_ledger": {
            "abstained_claim_ids": [
                row["claim_id"]
                for row in feedback
                if row.get("contentops_decision") == "ABSTAINED"
            ],
            "quarantined_claim_ids": [
                row["claim_id"]
                for row in feedback
                if row.get("contentops_decision") == "QUARANTINED"
            ],
            "reasons": {
                row["claim_id"]: row.get("disagreement_reasons")
                for row in feedback
                if row.get("contentops_decision") in {"ABSTAINED", "QUARANTINED"}
            },
        },
        "outcome_boundary_map": {
            "states_allowed": [
                "OUTCOME_PENDING",
                "NOT_COMPARABLE",
                "NOT_VERIFIED",
                "OBSERVED",
            ],
            "proof_layers": [
                "RETROSPECTIVE_REPLAY",
                "PROSPECTIVE_NATURAL_OBSERVATION",
                "PAPER_SIMULATION",
                "RUNTIME_PROVEN",
                "REALIZED_EXECUTION",
                "PROXY_CONTEXT",
            ],
            "slots": outcomes,
            "performance_claims_created": False,
            "forecast_claims_created": False,
            "runtime_claims_created": False,
            "public_claims_created": False,
        },
        "quality_counts": {
            "candidate_count": len(feedback),
            "agreement_count": sum(bool(row.get("agreement")) for row in feedback),
            "disagreement_count": sum(
                not bool(row.get("agreement")) for row in feedback
            ),
            "orphan_section_count": len(orphan_sections),
            "orphan_derivative_count": len(orphan_derivatives),
            "duplicate_payload_count": len(duplicate_payloads),
            "abstained_count": sum(
                row.get("contentops_decision") == "ABSTAINED" for row in feedback
            ),
            "quarantined_count": sum(
                row.get("contentops_decision") == "QUARANTINED" for row in feedback
            ),
            "derivative_count": len(packages),
            "outcome_pending_count": sum(
                row.get("outcome_state") == "OUTCOME_PENDING" for row in outcomes
            ),
            "not_comparable_count": sum(
                row.get("outcome_state") == "NOT_COMPARABLE" for row in outcomes
            ),
            "not_verified_count": sum(
                row.get("outcome_state") == "NOT_VERIFIED" for row in outcomes
            ),
            "observed_count": sum(
                row.get("outcome_state") == "OBSERVED" for row in outcomes
            ),
        },
        "zero_effect": zero_effect,
        "proof_axes": {
            "artifact_hash": artifact["status"] == "SEALED_MATCH",
            "main_pack_hash": not any("hash" in x for x in blockers),
            "candidate_sets_reconciled": main_ids == editor_ids,
            "traceability_complete": not orphan_sections and not orphan_derivatives,
            "runtime_proven": False,
            "publicly_proven": False,
        },
        "authority_flags": {
            key: (0 if key == "external_effects" else False) for key in AUTHORITY_KEYS
        },
        "classification": classifications,
        "blockers": list(dict.fromkeys(blockers)),
        "next": "RETAIN_FEEDBACK_PACK_AND_HAND_TO_MAIN_FOR_NEXT_DECISION_EVALUATION",
        "pack_sha256": None,
    }
    pack["pack_sha256"] = pack_sha256(pack)
    return pack


def verify_decision_editorial_feedback_quality_pack(pack: Mapping[str, Any]) -> bool:
    try:
        if (
            pack.get("schema_version") != SCHEMA_VERSION
            or pack.get("version") != VERSION
        ):
            return False
        if (
            pack.get("pack_sha256") != pack_sha256(pack)
            or pack.get("immutable_pack") is not True
            or pack.get("shadow_only") is not True
        ):
            return False
        if _walk_secret(pack) or _unknown_write(pack):
            return False
        if (
            pack.get("canonical_article_traceability", {}).get("public_write_performed")
            is True
        ):
            return False
        for row in pack.get("candidate_feedback") or []:
            if not row.get("source_hashes") or row.get("authority") is not False:
                return False
        for row in pack.get("outcome_boundary_map", {}).get("slots") or []:
            if row.get("outcome_state") not in {
                "OUTCOME_PENDING",
                "NOT_COMPARABLE",
                "NOT_VERIFIED",
                "OBSERVED",
            }:
                return False
        return True
    except (KeyError, TypeError, ValueError):
        return False


__all__ = [
    "MAIN_ARTIFACT_BYTES",
    "MAIN_ARTIFACT_FILE_SHA256",
    "MAIN_ARTIFACT_PATH",
    "MAIN_HEAD",
    "MAIN_PACK_SHA256",
    "SCHEMA_VERSION",
    "build_decision_editorial_feedback_quality_pack",
    "canonical_bytes",
    "pack_sha256",
    "verify_decision_editorial_feedback_quality_pack",
]
