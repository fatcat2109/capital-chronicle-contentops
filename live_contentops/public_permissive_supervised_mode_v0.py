"""Supervised public-permissive mode for CC artifact candidate commentary.

This module prepares local preview artifacts only. It does not dispatch,
schedule, call platform adapters, fetch sources, inspect credentials, touch
browser state, or mutate the Capital Chronicle database/main repo.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

from .cc_artifact_packet_approval_v0 import canonical_json_hash

TASK_LABEL = "TASK_CONTENTOPS_PUBLIC_PERMISSIVE_SUPERVISED_MODE_V0"
SCHEMA_VERSION = "0.1.0"

POLICY_MODE_NAME = "OPERATOR_PUBLIC_OVERRIDE_CANDIDATE_COMMENTARY"
PUBLIC_MODE_CANDIDATE_COMMENTARY = "candidate_commentary"

PUBLIC_CANDIDATE_ALLOWED_WITH_CAVEATS = "PUBLIC_CANDIDATE_ALLOWED_WITH_CAVEATS"
PUBLIC_CANDIDATE_OVERRIDE_BLOCKED = "PUBLIC_CANDIDATE_OVERRIDE_BLOCKED"

MANDATORY_DISCLAIMER = (
    "Internal candidate analysis / non-authoritative / not financial advice / source caveats apply."
)

DEFAULT_OUTPUT_DIR = Path("docs/automation/PUBLIC_PERMISSIVE_SUPERVISED_MODE_V0")
DEFAULT_DUPLICATE_LEDGER = Path("docs/automation/V6_PUBLIC_DISPATCH_FREEZE/public_dispatch_duplicate_ledger_v6.jsonl")

CURRENT_PUBLIC_PLATFORMS = (
    "substack",
    "linkedin",
    "x",
    "instagram",
    "facebook_page",
    "telegram",
    "threads",
    "discord",
)

PROMOTABLE_BLOCKER_PREFIXES = (
    "dqr_status_not_clear",
    "candidate_only_true",
    "publish_eligibility_internal_draft_only",
    "publish_eligibility_manual_review_only",
    "source_quality_degraded_or_blocked",
    "packet_caveats_internal_or_non_authoritative",
    "limitations_include_dqr_blocked",
    "public_freeze_duplicate_status_not_checked",
    "live_provider_or_platform_path_forbidden_in_this_task",
)

APPROVAL_OR_ARTIFACT_BLOCKER_PREFIXES = (
    "missing_",
    "approval_hash_mismatch",
    "component_hash_mismatch",
    "rehearsal_intent_public_ready_true",
    "rehearsal_intent_dispatch_allowed_true",
)

TRADING_ADVICE_PATTERNS = (
    r"\byou should\s+(buy|sell|short|go long|go short|trade)\b",
    r"\bwe recommend\s+(buying|selling|shorting|going long|going short)\b",
    r"\b(strong buy|strong sell|buy now|sell now|trade now)\b",
    r"\b(position size|position sizing|stop loss|take profit|broker order)\b",
    r"\bthis is financial advice\b",
)

EXACT_AUTHORITY_FORBIDDEN_PHRASES = (
    "dqr cleared",
    "production active",
    "authoritative record",
    "authoritative database",
    "source truth verified",
    "numeric truth verified",
)


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _flatten_text(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        text: list[str] = []
        for item in value.values():
            text.extend(_flatten_text(item))
        return text
    if isinstance(value, (list, tuple, set)):
        text = []
        for item in value:
            text.extend(_flatten_text(item))
        return text
    return [str(value)]


def _blob(value: Any) -> str:
    return " ".join(_flatten_text(value)).lower()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_duplicate_ledger(path: str | Path = DEFAULT_DUPLICATE_LEDGER) -> list[dict[str, Any]]:
    ledger_path = Path(path)
    if not ledger_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw in ledger_path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def candidate_topic_hash(packet: dict[str, Any]) -> str:
    return stable_hash(
        {
            "topic": packet.get("topic"),
            "article_angle": packet.get("article_angle"),
            "headline_or_catalyst": packet.get("headline_or_catalyst"),
        }
    )


def build_caveat_disclaimer_block(packet: dict[str, Any]) -> str:
    forbidden_notes = packet.get("forbidden_use_notes") if isinstance(packet.get("forbidden_use_notes"), list) else []
    limitations = packet.get("limitations") if isinstance(packet.get("limitations"), list) else []
    lines = [
        MANDATORY_DISCLAIMER,
        "",
        "Public candidate-commentary caveats:",
        f"- DQR status remains {packet.get('dqr_status')}.",
        f"- Publish eligibility remains {packet.get('publish_eligibility')}.",
        f"- Candidate-only flag remains {str(packet.get('candidate_only')).lower()}.",
        f"- Source quality: {packet.get('source_quality_status')}.",
    ]
    for note in forbidden_notes:
        lines.append(f"- Preserved source caveat: {note}")
    for limitation in limitations:
        lines.append(f"- Preserved limitation: {limitation}")
    return "\n".join(lines).strip() + "\n"


def _format_numeric_anchors(packet: dict[str, Any]) -> list[str]:
    anchors = packet.get("numeric_anchors") if isinstance(packet.get("numeric_anchors"), list) else []
    lines: list[str] = []
    for anchor in anchors:
        if not isinstance(anchor, dict):
            continue
        lines.append(
            "- Candidate/proxy non-authoritative value: "
            f"{anchor.get('value')} {anchor.get('unit')} for {anchor.get('period')} "
            f"from {anchor.get('source_ref')} ({anchor.get('authority_status')}); "
            f"caveat: {anchor.get('caveat')}"
        )
    return lines


def build_candidate_public_preview(packet: dict[str, Any], disclaimer_block: str | None = None) -> str:
    disclaimer = disclaimer_block or build_caveat_disclaimer_block(packet)
    source_trail = packet.get("source_trail") if isinstance(packet.get("source_trail"), list) else []
    claim_ledger = packet.get("claim_ledger") if isinstance(packet.get("claim_ledger"), list) else []
    lines = [
        "# Candidate Commentary Preview",
        "",
        disclaimer.strip(),
        "",
        f"Topic: {packet.get('topic')}",
        f"Angle: {packet.get('article_angle')}",
        f"Catalyst: {packet.get('headline_or_catalyst')}",
        "",
        "This is editorial candidate commentary for operator-supervised public preview. "
        "It keeps candidate/proxy labels visible and does not promote blocked-DQR material.",
        "",
        "## Candidate Status",
        "",
        f"- DQR status: {packet.get('dqr_status')}",
        f"- Candidate only: {str(packet.get('candidate_only')).lower()}",
        f"- Publish eligibility: {packet.get('publish_eligibility')}",
        f"- Source quality: {packet.get('source_quality_status')}",
        "",
        "## Candidate/Proxy Numeric Context",
        "",
    ]
    numeric_lines = _format_numeric_anchors(packet)
    lines.extend(numeric_lines or ["- No numeric anchors were provided in the packet."])
    lines.extend(["", "## Source Trail", ""])
    lines.extend(f"- {item}" for item in source_trail)
    lines.extend(["", "## Supported Candidate Claims", ""])
    for claim in claim_ledger:
        if not isinstance(claim, dict):
            continue
        lines.append(f"- {claim.get('claim_text')} Support status: {claim.get('support_status')}.")
    lines.extend(
        [
            "",
            "## Operator Review Note",
            "",
            "Public use requires the explicit operator public override recorded in the evidence packet. "
            "A future live task must still run duplicate, platform, dispatch, and readback gates before posting.",
            "",
        ]
    )
    return "\n".join(lines)


def build_candidate_platform_payloads(
    packet: dict[str, Any],
    *,
    approval_hash: str,
    disclaimer_block: str | None = None,
) -> dict[str, Any]:
    disclaimer = (disclaimer_block or build_caveat_disclaimer_block(packet)).splitlines()[0]
    topic = packet.get("topic")
    angle = packet.get("article_angle")
    catalyst = packet.get("headline_or_catalyst")
    base_text = (
        f"{disclaimer}\n\n"
        f"Candidate commentary: {topic}. {angle} Catalyst: {catalyst}\n\n"
        f"DQR status remains {packet.get('dqr_status')}; values stay candidate/proxy and non-authoritative."
    )
    platform_payloads: dict[str, dict[str, Any]] = {}
    for platform in CURRENT_PUBLIC_PLATFORMS:
        payload = {
            "platform": platform,
            "payload_class": PUBLIC_MODE_CANDIDATE_COMMENTARY,
            "policy_mode": POLICY_MODE_NAME,
            "text": base_text,
            "approval_hash": approval_hash,
            "public_dispatch_ready": False,
            "requires_separate_live_task": True,
            "requires_post_dispatch_readback": True,
            "canonical_url": None,
        }
        payload["payload_hash"] = canonical_json_hash(payload)
        platform_payloads[platform] = payload
    bundle = {
        "schema_version": SCHEMA_VERSION,
        "packet_kind": "candidate_platform_payloads_v0",
        "policy_mode": POLICY_MODE_NAME,
        "public_mode": PUBLIC_MODE_CANDIDATE_COMMENTARY,
        "platforms": list(CURRENT_PUBLIC_PLATFORMS),
        "payloads": platform_payloads,
    }
    bundle["payload_hash"] = canonical_json_hash(bundle)
    return bundle


def evaluate_duplicate_guard(
    packet: dict[str, Any],
    payload_bundle: dict[str, Any],
    *,
    duplicate_ledger_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    rows = duplicate_ledger_rows if duplicate_ledger_rows is not None else load_duplicate_ledger()
    topic_hash = candidate_topic_hash(packet)
    payload_hash = payload_bundle["payload_hash"]
    topic_blob = _blob(
        {
            "topic": packet.get("topic"),
            "article_angle": packet.get("article_angle"),
            "headline_or_catalyst": packet.get("headline_or_catalyst"),
        }
    )
    blockers: list[str] = []
    matches: list[dict[str, Any]] = []
    for row in rows:
        row_blob = _blob(row)
        row_hash_values = {
            str(row.get("topic_hash") or ""),
            str(row.get("candidate_topic_hash") or ""),
            str(row.get("payload_hash") or ""),
            str(row.get("candidate_payload_hash") or ""),
            str(row.get("public_payload_hash") or ""),
        }
        family = str(row.get("duplicate_family") or row.get("topic_hint") or "").lower()
        matched = False
        reason = ""
        if topic_hash in row_hash_values:
            matched = True
            reason = "duplicate_topic_hash"
        elif payload_hash in row_hash_values:
            matched = True
            reason = "duplicate_payload_hash"
        elif family and family == str(packet.get("topic") or "").lower():
            matched = True
            reason = "duplicate_family_exact"
        elif topic_blob and row_blob and topic_blob == row_blob:
            matched = True
            reason = "duplicate_topic_blob"
        if matched:
            blockers.append(reason)
            matches.append({"reason": reason, "row": row})
    return {
        "status": "PASS_DETERMINISTIC_NO_DUPLICATE" if not blockers else "BLOCKED_DUPLICATE_DETECTED",
        "blockers": list(dict.fromkeys(blockers)),
        "ledger_rows_checked": len(rows),
        "topic_hash": topic_hash,
        "payload_hash": payload_hash,
        "matches": matches,
    }


def _has_trading_advice(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in TRADING_ADVICE_PATTERNS)


def _has_exact_authority_promotion(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in EXACT_AUTHORITY_FORBIDDEN_PHRASES)


def validate_public_candidate_materials(
    *,
    packet: dict[str, Any],
    preview_markdown: str,
    payload_bundle: dict[str, Any],
    disclaimer_block: str,
) -> dict[str, Any]:
    combined_text = "\n".join([preview_markdown, disclaimer_block, _blob(payload_bundle)])
    hard_blockers: list[str] = []
    if MANDATORY_DISCLAIMER not in combined_text:
        hard_blockers.append("mandatory_disclaimer_missing")
    if "candidate/proxy" not in combined_text.lower() or "non-authoritative" not in combined_text.lower():
        hard_blockers.append("candidate_proxy_non_authoritative_labels_missing")
    if str(packet.get("dqr_status") or "").lower() == "blocked" and "dqr status: blocked" not in combined_text.lower():
        hard_blockers.append("dqr_blocked_not_visible")
    if "internal candidate analysis" not in combined_text.lower():
        hard_blockers.append("internal_caveat_not_transformed_to_public_disclaimer")
    if _has_exact_authority_promotion(combined_text):
        hard_blockers.append("exact_authority_promotion_detected")
    if _has_trading_advice(combined_text):
        hard_blockers.append("trading_or_financial_advice_detected")
    return {
        "status": "PASS" if not hard_blockers else "BLOCKED",
        "hard_blockers": hard_blockers,
        "mandatory_disclaimer_present": MANDATORY_DISCLAIMER in combined_text,
        "candidate_proxy_labels_visible": "candidate/proxy" in combined_text.lower(),
        "dqr_blocked_visible": "dqr status: blocked" in combined_text.lower(),
        "trading_advice_detected": _has_trading_advice(combined_text),
        "exact_authority_promotion_detected": _has_exact_authority_promotion(combined_text),
    }


def _split_base_blockers(base_eligibility: dict[str, Any]) -> tuple[list[str], list[str]]:
    converted: list[str] = []
    hard: list[str] = []
    for blocker in base_eligibility.get("blockers") or []:
        if any(blocker.startswith(prefix) for prefix in PROMOTABLE_BLOCKER_PREFIXES):
            converted.append(blocker)
        elif any(blocker.startswith(prefix) for prefix in APPROVAL_OR_ARTIFACT_BLOCKER_PREFIXES):
            hard.append(blocker)
        else:
            hard.append(blocker)
    return converted, hard


def build_public_override_decision(
    *,
    packet: dict[str, Any],
    base_eligibility: dict[str, Any],
    operator_public_override: bool,
    public_mode: str,
    duplicate_ledger_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    disclaimer = build_caveat_disclaimer_block(packet)
    preview = build_candidate_public_preview(packet, disclaimer)
    payload_bundle = build_candidate_platform_payloads(
        packet,
        approval_hash=str(base_eligibility.get("approval_hash") or ""),
        disclaimer_block=disclaimer,
    )
    duplicate_guard = evaluate_duplicate_guard(packet, payload_bundle, duplicate_ledger_rows=duplicate_ledger_rows)
    material_validation = validate_public_candidate_materials(
        packet=packet,
        preview_markdown=preview,
        payload_bundle=payload_bundle,
        disclaimer_block=disclaimer,
    )
    converted_blockers, hard_blockers = _split_base_blockers(base_eligibility)

    if not operator_public_override:
        hard_blockers.append("operator_public_override_missing")
    if public_mode != PUBLIC_MODE_CANDIDATE_COMMENTARY:
        hard_blockers.append(f"unsupported_public_mode:{public_mode}")
    if base_eligibility.get("approval_hash_continuity_status") != "PASS":
        hard_blockers.append("approval_hash_continuity_not_pass")
    if duplicate_guard["status"] != "PASS_DETERMINISTIC_NO_DUPLICATE":
        hard_blockers.extend(duplicate_guard["blockers"])
    hard_blockers.extend(material_validation["hard_blockers"])

    hard_blockers = list(dict.fromkeys(hard_blockers))
    allowed = not hard_blockers
    warnings = [
        f"converted_block_to_warning:{blocker}"
        for blocker in converted_blockers
    ]
    warnings.extend(
        [
            "candidate_commentary_only_not_exact_analysis",
            "live_dispatch_requires_separate_exact_task",
            "post_dispatch_readback_required_if_future_live_task_runs",
        ]
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "packet_kind": "public_permissive_supervised_decision_v0",
        "task_label": TASK_LABEL,
        "policy_mode": POLICY_MODE_NAME,
        "public_mode": public_mode,
        "classification": PUBLIC_CANDIDATE_ALLOWED_WITH_CAVEATS if allowed else PUBLIC_CANDIDATE_OVERRIDE_BLOCKED,
        "operator_public_override_received": operator_public_override,
        "operator_public_override_scope": "candidate_commentary_preview_only_not_live_dispatch",
        "packet_id": packet.get("packet_id"),
        "approval_hash": base_eligibility.get("approval_hash"),
        "payload_hash": payload_bundle["payload_hash"],
        "public_ready": allowed,
        "dispatch_allowed_now": False,
        "public_dispatch_performed": False,
        "platform_api_call_performed": False,
        "browser_cdp_performed": False,
        "network_or_source_fetch_performed": False,
        "env_credential_session_read_performed": False,
        "main_repo_write_performed": False,
        "scheduler_retry_outbox_execution_performed": False,
        "readback_evidence_required_after_future_live_dispatch": True,
        "hard_blockers": hard_blockers,
        "converted_blockers_to_warnings": converted_blockers,
        "warnings": list(dict.fromkeys(warnings)),
        "duplicate_guard": duplicate_guard,
        "material_validation": material_validation,
        "mandatory_disclaimer": MANDATORY_DISCLAIMER,
        "disclaimer_block": disclaimer,
        "candidate_public_preview_markdown": preview,
        "candidate_platform_payloads": payload_bundle,
        "preserved_caveats": {
            "dqr_status": packet.get("dqr_status"),
            "candidate_only": packet.get("candidate_only"),
            "publish_eligibility": packet.get("publish_eligibility"),
            "source_quality_status": packet.get("source_quality_status"),
            "forbidden_use_notes": packet.get("forbidden_use_notes") or [],
            "limitations": packet.get("limitations") or [],
            "numeric_anchor_authority_statuses": [
                anchor.get("authority_status")
                for anchor in packet.get("numeric_anchors") or []
                if isinstance(anchor, dict)
            ],
        },
    }


def write_public_permissive_artifacts(
    decision: dict[str, Any],
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    decision_path = output / "public_override_decision_v0.json"
    preview_path = output / "candidate_public_preview_v0.md"
    payloads_path = output / "candidate_platform_payloads_v0.json"
    disclaimer_path = output / "caveat_disclaimer_block_v0.md"
    evidence_path = output / "public_permissive_evidence_v0.json"

    payloads = decision["candidate_platform_payloads"]
    _write_json(decision_path, {k: v for k, v in decision.items() if k not in {"candidate_public_preview_markdown", "candidate_platform_payloads", "disclaimer_block"}})
    preview_path.write_text(decision["candidate_public_preview_markdown"], encoding="utf-8")
    _write_json(payloads_path, payloads)
    disclaimer_path.write_text(decision["disclaimer_block"], encoding="utf-8")
    evidence = {
        "schema_version": SCHEMA_VERSION,
        "packet_kind": "public_permissive_supervised_mode_evidence_v0",
        "task_label": TASK_LABEL,
        "created_at": utc_now(),
        "classification": decision["classification"],
        "policy_mode": decision["policy_mode"],
        "public_mode": decision["public_mode"],
        "packet_id": decision["packet_id"],
        "approval_hash": decision["approval_hash"],
        "payload_hash": decision["payload_hash"],
        "public_ready": decision["public_ready"],
        "dispatch_allowed_now": decision["dispatch_allowed_now"],
        "operator_public_override_received": decision["operator_public_override_received"],
        "operator_public_override_scope": decision["operator_public_override_scope"],
        "old_blocks_converted_to_warnings": decision["converted_blockers_to_warnings"],
        "hard_blockers": decision["hard_blockers"],
        "hard_blocks_remaining": [
            "secret_or_session_value_read",
            "main_repo_database_mutation",
            "numeric_truth_promotion_to_authoritative",
            "financial_advice_or_trading_signal",
            "missing_operator_public_override",
            "duplicate_or_spam_guard_failure",
            "hidden_caveats_or_disclaimers",
            "scheduler_retry_storm",
            "platform_api_call_without_separate_live_task",
        ],
        "duplicate_guard": decision["duplicate_guard"],
        "material_validation": decision["material_validation"],
        "output_files": {
            "public_override_decision": str(decision_path),
            "candidate_public_preview": str(preview_path),
            "candidate_platform_payloads": str(payloads_path),
            "caveat_disclaimer_block": str(disclaimer_path),
            "public_permissive_evidence": str(evidence_path),
        },
        "safety": {
            "public_dispatch_performed": False,
            "platform_api_call_performed": False,
            "browser_cdp_performed": False,
            "network_or_source_fetch_performed": False,
            "env_credential_session_read_performed": False,
            "main_repo_write_performed": False,
            "scheduler_retry_outbox_execution_performed": False,
        },
        "next_task": "controlled live dispatch under operator public override",
    }
    evidence["evidence_hash"] = stable_hash(evidence)
    _write_json(evidence_path, evidence)
    return {
        "public_override_decision": decision_path,
        "candidate_public_preview": preview_path,
        "candidate_platform_payloads": payloads_path,
        "caveat_disclaimer_block": disclaimer_path,
        "public_permissive_evidence": evidence_path,
    }
