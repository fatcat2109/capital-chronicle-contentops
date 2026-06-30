"""V6 Draft Inspector for content production review bundles, no-provider no-send."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "6.0.0"
TASK_LABEL = "TASK_CONTENTOPS_V6_DRAFT_INSPECTOR_FOR_CONTENT_PRODUCTION_REVIEW_BUNDLE_HEAVY_BATCH_NO_PROVIDER_NO_SEND_V0"
UPSTREAM_TASK_LABEL = "TASK_CONTENTOPS_V6_CONTENT_PRODUCTION_CORE_REVIEW_PACKETS_HEAVY_BATCH_NO_PROVIDER_NO_SEND_V0"
INSPECTOR_MODE = "deterministic_local_review_only"
HARD_FALSE_FLAGS = ("eligible_for_live_send_now", "provider_call_made", "env_read", "credential_value_read", "network_call_made", "browser_session_used", "public_url_created", "metrics_created", "publication_ready", "dispatch_allowed", "runtime_truth")
REQUIRED_SECTIONS = ("operator_intent_packet", "research_grounding_packet", "canonical_article_review_packet", "seo_editorial_packet", "discord_drop_candidate_packet", "platform_variant_set_candidate_packet")
BLOCKED_TARGETS = ("live_send", "dispatch", "publication", "public_url_creation", "metrics_creation", "provider_call", "browser_session", "env_read", "credential_value_read")
APPROVAL_TARGETS = ("payload_hash_preview_only", "approval_ledger_preparation_only")
PROHIBITED_APPROVAL_TARGETS = {"live_send", "dispatch", "publication", "public_url", "metrics"}
SECRET_OR_URL_RE = re.compile(r"https?://|discord(?:app)?\.com/api/webhooks|[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}", re.I)
FORBIDDEN_TEXT = ("cookie", "session", "localstorage", "fake citation", "fake metric", "fake metrics", "financial advice", "signal service", "buy", "sell", "hold", "entries", "exits", "targets", "position sizing", "guaranteed prediction", "model says", "ai guarantees", "publication approved", "dispatch allowed", "live send", "executable request", "webhook", "endpoint", "secret", "public url")

@dataclass(frozen=True)
class DraftInspectionBundle:
    schema_version: str
    task_label: str
    draft_inspection_bundle_id: str
    content_production_review_bundle_id: str
    draft_inspection_report: dict[str, Any]
    eligible_for_payload_hash_preview_task: bool
    eligible_for_approval_ledger_preparation_task: bool
    eligible_for_live_send_now: bool
    provider_call_made: bool
    env_read: bool
    credential_value_read: bool
    network_call_made: bool
    browser_session_used: bool
    public_url_created: bool
    metrics_created: bool
    publication_ready: bool
    dispatch_allowed: bool
    runtime_truth: bool
    human_review_required: bool
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    packet_sha256: str = ""


def _sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _packet_sha(payload: dict[str, Any]) -> str:
    clone = dict(payload); clone.pop("packet_sha256", None)
    return _sha(clone)


def _walk(obj: Any, path: str = "") -> list[tuple[str, Any]]:
    if isinstance(obj, dict):
        out: list[tuple[str, Any]] = []
        for key, value in obj.items(): out.extend(_walk(value, f"{path}.{key}" if path else str(key)))
        return out
    if isinstance(obj, list):
        out = []
        for idx, value in enumerate(obj): out.extend(_walk(value, f"{path}[{idx}]"))
        return out
    return [(path, obj)]


def _assert_safe(obj: dict[str, Any], label: str) -> None:
    for path, value in _walk(obj):
        if isinstance(value, str):
            low = value.lower()
            if SECRET_OR_URL_RE.search(value): raise ValueError(f"{label}_forbidden_value:{path}")
            if any(term in low for term in FORBIDDEN_TEXT): raise ValueError(f"{label}_forbidden_text:{path}")


def _add(blockers: list[str], ok: bool, message: str) -> None:
    if not ok: blockers.append(message)


def _upstream_blockers(bundle: dict[str, Any]) -> list[str]:
    b: list[str] = []
    _add(b, bundle.get("schema_version") == SCHEMA_VERSION, "upstream_schema_version_invalid")
    _add(b, bundle.get("task_label") == UPSTREAM_TASK_LABEL, "upstream_task_label_invalid")
    for section in REQUIRED_SECTIONS: _add(b, isinstance(bundle.get(section), dict) and bool(bundle.get(section)), f"missing_{section}")
    _add(b, bundle.get("eligible_for_future_draft_inspection_task") is True, "upstream_draft_inspection_eligibility_not_true")
    for flag in HARD_FALSE_FLAGS: _add(b, bundle.get(flag) is False, f"upstream_{flag}_not_false")
    _add(b, bundle.get("human_review_required") is True, "upstream_human_review_required_not_true")
    _add(b, bundle.get("blockers", []) == [], "upstream_blockers_not_empty")
    return b


def _status_blockers(report: dict[str, Any]) -> list[str]:
    b: list[str] = []
    _add(b, report.get("inspector_mode") == INSPECTOR_MODE, "report_inspector_mode_invalid")
    for flag in HARD_FALSE_FLAGS: _add(b, report.get(flag) is False, f"report_{flag}_not_false")
    _add(b, report.get("human_review_required") is True, "report_human_review_required_not_true")
    _add(b, report.get("claim_risk_status") in {"pass", "review_required", "blocked"}, "report_claim_risk_status_invalid")
    _add(b, report.get("no_advice_status") == "pass", "report_no_advice_status_not_pass")
    _add(b, report.get("no_signal_status") == "pass", "report_no_signal_status_not_pass")
    _add(b, report.get("market_prediction_language_status") == "pass", "report_market_prediction_status_not_pass")
    _add(b, report.get("model_authority_leakage_status") == "pass", "report_model_authority_status_not_pass")
    _add(b, report.get("trade_execution_language_status") == "pass", "report_trade_execution_status_not_pass")
    _add(b, report.get("platform_constraint_status") in {"pass", "review_required"}, "report_platform_constraint_status_invalid")
    _add(b, report.get("media_rights_status") in {"not_applicable", "review_required"}, "report_media_rights_status_invalid")
    targets = set(report.get("approval_eligible_targets", []))
    _add(b, not (targets & PROHIBITED_APPROVAL_TARGETS), "report_approval_targets_include_prohibited")
    blocked = set(report.get("blocked_targets", []))
    for target in BLOCKED_TARGETS: _add(b, target in blocked, f"report_blocked_target_missing_{target}")
    return b


def _inspect_packets(bundle: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    operator = bundle.get("operator_intent_packet", {})
    research = bundle.get("research_grounding_packet", {})
    article = bundle.get("canonical_article_review_packet", {})
    seo = bundle.get("seo_editorial_packet", {})
    discord = bundle.get("discord_drop_candidate_packet", {})
    variants = bundle.get("platform_variant_set_candidate_packet", {})
    blockers: list[str] = []
    citations = article.get("citations", []) if isinstance(article, dict) else []
    missing = research.get("missing_evidence", []) if isinstance(research, dict) else []
    citation_status = "source_review_required" if not citations else "review_required"
    missing_status = "review_required" if missing else "not_applicable"
    _add(blockers, bool(article.get("limitations")), "article_limitations_missing")
    _add(blockers, bool(article.get("disclosure")), "article_disclosure_missing")
    _add(blockers, seo.get("limitations_preserved") is True, "seo_limitations_preserved_not_true")
    _add(blockers, seo.get("caveats_preserved") is True, "seo_caveats_preserved_not_true")
    _add(blockers, bool(discord.get("discussion_question")), "discord_discussion_question_missing")
    _add(blockers, bool(discord.get("disclosure")), "discord_disclosure_missing")
    _add(blockers, discord.get("publication_ready") is False, "discord_publication_ready_not_false")
    _add(blockers, discord.get("dispatch_allowed") is False, "discord_dispatch_allowed_not_false")
    readiness = variants.get("execution_readiness_by_platform", {})
    variant_map = variants.get("variants", {})
    _add(blockers, isinstance(readiness, dict) and all(v is False for v in readiness.values()), "variant_execution_readiness_not_all_false")
    if isinstance(variant_map, dict): _add(blockers, all(v.get("dispatch_ready") is False for v in variant_map.values() if isinstance(v, dict)), "variant_dispatch_ready_not_false")
    manual = variants.get("manual_fallback_by_platform", {})
    if isinstance(manual, dict) and "x_manual" in manual: _add(blockers, manual.get("x_manual") is True, "variant_x_manual_not_manual")
    deferred = set(variants.get("deferred_platforms", []))
    if isinstance(readiness, dict):
        for p in ("linkedin_org_deferred", "tiktok_deferred"):
            if p in readiness: _add(blockers, p in deferred, f"variant_{p}_not_deferred")
    discord_status = "pass" if discord.get("discussion_question") and discord.get("disclosure") and discord.get("dispatch_allowed") is False and discord.get("publication_ready") is False else "blocked"
    seo_status = "pass" if seo.get("limitations_preserved") is True and seo.get("caveats_preserved") is True else "blocked"
    variant_status = "pass" if isinstance(readiness, dict) and all(v is False for v in readiness.values()) and isinstance(variant_map, dict) and all(v.get("dispatch_ready") is False for v in variant_map.values() if isinstance(v, dict)) else "blocked"
    disclosure_status = "pass" if article.get("disclosure") and discord.get("disclosure") else "blocked"
    report_seed = {"bundle": bundle.get("content_production_review_bundle_id", ""), "article": article.get("article_id", "")}
    report = {
        "schema_version": SCHEMA_VERSION, "task_label": TASK_LABEL,
        "draft_inspection_report_id": "draft_inspection_report_" + _sha(report_seed)[:16],
        "content_production_review_bundle_id": bundle.get("content_production_review_bundle_id", ""),
        "operator_intent_id": operator.get("operator_intent_id", ""),
        "article_id": article.get("article_id", ""),
        "discord_drop_id": discord.get("discord_drop_id", ""),
        "variant_set_id": variants.get("variant_set_id", ""),
        "inspected_at_manual": "manual_timestamp_required_for_operator_record",
        "inspector_mode": INSPECTOR_MODE,
        "provider_call_made": False, "env_read": False, "credential_value_read": False,
        "network_call_made": False, "browser_session_used": False, "public_url_created": False,
        "metrics_created": False, "publication_ready": False, "dispatch_allowed": False,
        "runtime_truth": False, "human_review_required": True,
        "claim_risk_status": "review_required" if not blockers else "blocked",
        "citation_status": citation_status,
        "source_freshness_status": "source_review_required",
        "missing_evidence_status": missing_status,
        "no_advice_status": "pass", "no_signal_status": "pass",
        "market_prediction_language_status": "pass",
        "model_authority_leakage_status": "pass",
        "trade_execution_language_status": "pass",
        "platform_constraint_status": "review_required",
        "discord_safety_status": discord_status,
        "seo_caveat_preservation_status": seo_status,
        "variant_execution_status": variant_status,
        "media_rights_status": "not_applicable",
        "disclosure_status": disclosure_status,
        "approval_eligible_targets": list(APPROVAL_TARGETS) if not blockers else [],
        "blocked_targets": list(BLOCKED_TARGETS),
        "required_edits": [] if not blockers else blockers[:],
        "warnings": ["review_only", "human_review_required", "no_provider_call", "no_live_send"],
        "blockers": blockers,
        "eligible_for_payload_hash_preview_task": not blockers,
        "eligible_for_approval_ledger_task": not blockers,
        "eligible_for_live_send_now": False,
        "packet_sha256": "",
    }
    report["packet_sha256"] = _packet_sha(report)
    return report, blockers + _status_blockers(report)


def make_draft_inspection_bundle(content_production_review_bundle: dict[str, Any]) -> DraftInspectionBundle:
    _assert_safe(content_production_review_bundle, "content_production_review_bundle")
    upstream = _upstream_blockers(content_production_review_bundle)
    report, packet_blockers = _inspect_packets(content_production_review_bundle)
    blockers = upstream + packet_blockers
    if blockers:
        report = {**report, "approval_eligible_targets": [], "required_edits": blockers[:], "blockers": blockers[:], "eligible_for_payload_hash_preview_task": False, "eligible_for_approval_ledger_task": False, "eligible_for_live_send_now": False}
        report["packet_sha256"] = _packet_sha(report)
    eligible = not blockers
    bundle = DraftInspectionBundle(
        schema_version=SCHEMA_VERSION, task_label=TASK_LABEL,
        draft_inspection_bundle_id="draft_inspection_bundle_" + _sha({"report": report.get("draft_inspection_report_id", ""), "bundle": content_production_review_bundle.get("content_production_review_bundle_id", "")})[:16],
        content_production_review_bundle_id=str(content_production_review_bundle.get("content_production_review_bundle_id", "")),
        draft_inspection_report=report,
        eligible_for_payload_hash_preview_task=eligible,
        eligible_for_approval_ledger_preparation_task=eligible,
        eligible_for_live_send_now=False,
        provider_call_made=False, env_read=False, credential_value_read=False, network_call_made=False,
        browser_session_used=False, public_url_created=False, metrics_created=False, publication_ready=False,
        dispatch_allowed=False, runtime_truth=False, human_review_required=True,
        blockers=blockers, warnings=["review_only", "human_review_required", "future_preparation_only"],
    )
    data = asdict(bundle)
    return DraftInspectionBundle(**{**data, "packet_sha256": _packet_sha(data)})


def blocked_bundle(reason: str) -> DraftInspectionBundle:
    report = {"schema_version": SCHEMA_VERSION, "task_label": TASK_LABEL, "draft_inspection_report_id": "draft_inspection_report_blocked", "content_production_review_bundle_id": "", "operator_intent_id": "", "article_id": "", "discord_drop_id": "", "variant_set_id": "", "inspected_at_manual": "manual_timestamp_required_for_operator_record", "inspector_mode": INSPECTOR_MODE, "provider_call_made": False, "env_read": False, "credential_value_read": False, "network_call_made": False, "browser_session_used": False, "public_url_created": False, "metrics_created": False, "publication_ready": False, "dispatch_allowed": False, "runtime_truth": False, "human_review_required": True, "claim_risk_status": "blocked", "citation_status": "source_review_required", "source_freshness_status": "source_review_required", "missing_evidence_status": "review_required", "no_advice_status": "pass", "no_signal_status": "pass", "market_prediction_language_status": "pass", "model_authority_leakage_status": "pass", "trade_execution_language_status": "pass", "platform_constraint_status": "review_required", "discord_safety_status": "blocked", "seo_caveat_preservation_status": "blocked", "variant_execution_status": "blocked", "media_rights_status": "not_applicable", "disclosure_status": "blocked", "approval_eligible_targets": [], "blocked_targets": list(BLOCKED_TARGETS), "required_edits": [reason], "warnings": ["review_only", "human_review_required"], "blockers": [reason], "eligible_for_payload_hash_preview_task": False, "eligible_for_approval_ledger_task": False, "eligible_for_live_send_now": False, "packet_sha256": ""}
    report["packet_sha256"] = _packet_sha(report)
    bundle = DraftInspectionBundle(SCHEMA_VERSION, TASK_LABEL, "draft_inspection_bundle_blocked", "", report, False, False, False, False, False, False, False, False, False, False, False, False, False, True, [reason], ["blocked_fail_closed"])
    data = asdict(bundle)
    return DraftInspectionBundle(**{**data, "packet_sha256": _packet_sha(data)})


def load_json_object(path: str | Path) -> dict[str, Any]:
    try: data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc: raise ValueError("malformed_json") from exc
    if not isinstance(data, dict): raise ValueError("json_not_object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 draft inspector for content production review bundle CLI")
    parser.add_argument("--content-production-review-bundle", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try: packet = make_draft_inspection_bundle(load_json_object(args.content_production_review_bundle))
    except ValueError as exc: packet = blocked_bundle(str(exc))
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")
    return 0 if packet.eligible_for_payload_hash_preview_task else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
