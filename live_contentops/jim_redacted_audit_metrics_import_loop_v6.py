"""Jim Redacted Audit + Metrics Import Loop V6.

Transforms local manual export workbench packets into a redacted post-manual-publish
review loop. Inputs are operator-supplied sample values only. No public reference locator fields,
network, scraping, browser/CDP, env, credential, platform API, scheduler, or live
write path.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from live_contentops.jim_manual_export_approval_workbench_v6 import build_jim_manual_export_approval_workbench

TASK_LABEL = "TASK_0080_HEAVY_BATCH_REDACTED_AUDIT_METRICS_IMPORT_LOOP_V0"
CONTRACT_VERSION = "jim_redacted_audit_metrics_import_loop_v6.0"
AUDIT_STATUS = "OPERATOR_SUPPLIED_REDACTED_AUDIT_READY_FOR_JIM_REVIEW"
METRICS_STATUS = "OPERATOR_SUPPLIED_METRICS_REVIEW_ONLY"
BACKLOG_STATUS = "FEEDBACK_CANDIDATE_NOT_PROMOTED"

FALSE_FLAGS = (
    "final_public_copy_created",
    "llm_provider_called",
    "provider_api_called",
    "network_called",
    "browser_or_cdp_used",
    "credential_or_env_read",
    "platform_api_called",
    "platform_dispatch_performed",
    "scheduler_enabled",
    "scraping_performed",
    "metrics_api_called",
    "public_reference_verified",
    "public_postable",
    "publish_ready",
    "dispatch_ready",
    "baseline_promoted",
)

TRUE_FLAGS = (
    "local_only",
    "operator_supplied_values_only",
    "redacted_public_reference_only",
    "jim_review_required",
    "feedback_candidate_created",
)

METRIC_FIELDS = (
    "impressions",
    "views",
    "opens",
    "likes",
    "comments",
    "shares",
    "saves",
    "clicks",
    "reposts",
    "subscribers_delta",
)

SAMPLE_OPERATOR_INPUTS = {
    "Substack": {"views": 144, "opens": 91, "likes": 7, "comments": 1, "shares": 2, "subscribers_delta": 0},
    "X": {"impressions": 2200, "likes": 18, "comments": 3, "reposts": 4, "clicks": 11},
    "LinkedIn": {"impressions": 880, "likes": 21, "comments": 5, "shares": 3, "clicks": 9},
    "Telegram": {"views": 312, "comments": 0, "shares": 1},
}

FORBIDDEN_KEY_PARTS = ("url", "href", "link")
FORBIDDEN_TEXT = ("http://", "https://", "scrape", "fetch live", "api sync", "dispatch-ready", "publish-ready")


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _stable_hash(data: Any) -> str:
    return hashlib.sha256(_json(data).encode("utf-8")).hexdigest()


def _safety_flags() -> dict[str, bool]:
    return {flag: False for flag in FALSE_FLAGS} | {flag: True for flag in TRUE_FLAGS}


def _assert_no_forbidden_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = key.lower()
            if any(part in lowered for part in FORBIDDEN_KEY_PARTS):
                raise ValueError(f"forbidden field name: {key}")
            _assert_no_forbidden_keys(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_forbidden_keys(child)


def _assert_no_forbidden_text(value: Any) -> None:
    text = _json(value).lower()
    if any(term in text for term in FORBIDDEN_TEXT):
        raise ValueError("forbidden live/network text in redacted audit packet")


def _metrics_for(platform: str, index: int) -> dict[str, int]:
    supplied = SAMPLE_OPERATOR_INPUTS[platform]
    return {field: int(supplied.get(field, 0)) for field in METRIC_FIELDS if field in supplied}


def _audit_card(export: dict[str, Any], index: int) -> dict[str, Any]:
    platform = export["platform"]
    card = {
        "audit_card_id": f"REDACTED-AUDIT-{index:03d}-{platform.upper()}",
        "source_export_packet_id": export["export_packet_id"],
        "source_export_hash": export["export_hash"],
        "platform": platform,
        "title": export["title"],
        "audit_status": AUDIT_STATUS,
        "operator_id": "Jim",
        "public_reference_redacted": f"{platform.lower()}-operator-supplied-redacted-reference-{index:03d}",
        "operator_supplied_reference_only": True,
        "public_reference_verified": False,
        "network_checked": False,
        "scraping_performed": False,
        "captured_at_local": f"2026-07-03T06:{index:02d}:00Z",
        "redaction_notes": [
            "Public reference stored as redacted operator-supplied text only",
            "No live lookup or scraping performed",
            "No private account data captured",
        ],
        "safety_flags": _safety_flags(),
    }
    card["audit_card_hash"] = _stable_hash(card)
    return card


def _metrics_packet(card: dict[str, Any], index: int) -> dict[str, Any]:
    metrics = _metrics_for(card["platform"], index)
    packet = {
        "metrics_packet_id": f"METRICS-IMPORT-{index:03d}-{card['platform'].upper()}",
        "source_audit_card_id": card["audit_card_id"],
        "source_audit_card_hash": card["audit_card_hash"],
        "platform": card["platform"],
        "metrics_status": METRICS_STATUS,
        "operator_id": "Jim",
        "metrics_source": "operator_supplied_manual_entry",
        "metrics_network_verified": False,
        "metrics_api_called": False,
        "metrics": metrics,
        "normalized_engagement_total": sum(metrics.values()),
        "quality_notes": [
            "Manual values need Jim review before strategy decisions",
            "Zero values can mean not supplied, not verified absence",
            "Packet is evidence for backlog triage only",
        ],
        "safety_flags": _safety_flags(),
    }
    packet["metrics_packet_hash"] = _stable_hash(packet)
    return packet


def _backlog_candidate(card: dict[str, Any], metrics: dict[str, Any], index: int) -> dict[str, Any]:
    total = metrics["normalized_engagement_total"]
    recommendation = "review_for_repeat_angle" if total >= 100 else "hold_for_more_manual_evidence"
    candidate = {
        "candidate_id": f"BACKLOG-FEEDBACK-{index:03d}-{card['platform'].upper()}",
        "source_audit_card_id": card["audit_card_id"],
        "source_metrics_packet_id": metrics["metrics_packet_id"],
        "platform": card["platform"],
        "title": card["title"],
        "candidate_status": BACKLOG_STATUS,
        "recommendation": recommendation,
        "reason": "operator-supplied manual metrics only; not enough authority for automatic promotion",
        "requires_jim_review": True,
        "baseline_promoted": False,
        "safety_flags": _safety_flags(),
    }
    candidate["candidate_hash"] = _stable_hash(candidate)
    return candidate


def build_jim_redacted_audit_metrics_import_loop(
    manual_workbench: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build deterministic redacted audit + metrics loop for Jim review."""
    source = deepcopy(manual_workbench if manual_workbench is not None else build_jim_manual_export_approval_workbench())
    ready_exports = [
        export for export in source["manual_export_packets"]
        if export["manual_export_status"] == "READY_FOR_MANUAL_COPY_AFTER_JIM_APPROVAL"
    ]
    audit_cards = [_audit_card(export, index + 1) for index, export in enumerate(ready_exports)]
    metric_packets = [_metrics_packet(card, index + 1) for index, card in enumerate(audit_cards)]
    backlog_candidates = [
        _backlog_candidate(card, metrics, index + 1)
        for index, (card, metrics) in enumerate(zip(audit_cards, metric_packets))
    ]
    loop = {
        "task_label": TASK_LABEL,
        "contract_version": CONTRACT_VERSION,
        "loop_id": f"redacted_audit_metrics_loop_for_{source['workbench_id']}",
        "source_workbench_id": source["workbench_id"],
        "operator_id": "Jim",
        "loop_status": "JIM_REVIEW_REQUIRED_OPERATOR_SUPPLIED_METRICS_ONLY",
        "audit_card_count": len(audit_cards),
        "metrics_packet_count": len(metric_packets),
        "backlog_candidate_count": len(backlog_candidates),
        "manual_publish_record_packets": audit_cards,
        "metrics_import_packets": metric_packets,
        "evidence_vault_cards": audit_cards,
        "feedback_backlog_candidates": backlog_candidates,
        "operator_next_action": "Jim reviews redacted audit cards and manual metrics before any strategy promotion.",
        "forbidden_actions": [
            "No public reference locator fields",
            "No network verification",
            "No metrics API",
            "No scraping",
            "No platform writes",
            "No baseline promotion",
        ],
        "safety_flags": _safety_flags(),
    }
    _assert_no_forbidden_keys(loop)
    _assert_no_forbidden_text(loop)
    loop["loop_hash"] = _stable_hash(loop)
    loop["loop_hash_algorithm"] = "sha256"
    return loop


if __name__ == "__main__":
    print(_json(build_jim_redacted_audit_metrics_import_loop()))
