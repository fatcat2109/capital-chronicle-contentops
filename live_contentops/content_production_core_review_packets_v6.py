"""V6 content production core review packets, local-only no-provider no-send."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "6.0.0"
TASK_LABEL = "TASK_CONTENTOPS_V6_CONTENT_PRODUCTION_CORE_REVIEW_PACKETS_HEAVY_BATCH_NO_PROVIDER_NO_SEND_V0"
INTENT_CLASSES = {"create_canonical_article", "create_discord_drop", "create_platform_variants", "create_product_update", "create_research_question_backlog", "create_campaign_review_bundle"}
CONTENT_LANES = {"macro_education", "source_trust", "data_sufficiency", "forecast_readiness_explainer", "build_in_public", "product_update", "community_question_response"}
PLATFORMS = {"substack", "discord", "telegram", "x_manual", "linkedin_personal_deferred", "linkedin_org_deferred", "threads", "facebook_page", "instagram_business", "tiktok_deferred"}
SOURCE_MODES = {"operator_supplied_context_only", "future_research_required", "no_external_sources_used"}
DROP_TYPES = {"substack_drop", "product_update", "announcement", "research_question_prompt", "build_in_public_update"}
CHANNEL_CLASSES = {"announcements", "substack_drops", "product_updates", "research_questions", "build_in_public"}
REQUEST_FALSE_FLAGS = ("live_write_requested", "provider_call_requested", "browser_requested", "publication_requested", "dispatch_requested", "financial_advice_requested", "signal_service_requested")
BUNDLE_FALSE_FLAGS = ("eligible_for_live_send_now", "provider_call_made", "env_read", "credential_value_read", "network_call_made", "browser_session_used", "public_url_created", "metrics_created", "publication_ready", "dispatch_allowed", "runtime_truth")
SECRET_OR_URL_RE = re.compile(r"https?://|discord(?:app)?\.com/api/webhooks|[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}", re.I)
FORBIDDEN_TEXT = ("buy", "sell", "hold", "entries", "exits", "targets", "position sizing", "guaranteed prediction", "signal service", "financial advice", "fake metrics", "fake citation", "fake public url", "public url", "webhook", "endpoint", "secret", "publication ready", "dispatch approval", "live send", "provider call", "model says", "ai guarantees")

@dataclass(frozen=True)
class ContentProductionReviewBundle:
    schema_version: str
    task_label: str
    content_production_review_bundle_id: str
    operator_intent_packet: dict[str, Any]
    research_grounding_packet: dict[str, Any]
    canonical_article_review_packet: dict[str, Any]
    seo_editorial_packet: dict[str, Any]
    discord_drop_candidate_packet: dict[str, Any]
    platform_variant_set_candidate_packet: dict[str, Any]
    eligible_for_future_draft_inspection_task: bool
    eligible_for_payload_hash_approval_task: bool
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
        for k, v in obj.items(): out.extend(_walk(v, f"{path}.{k}" if path else str(k)))
        return out
    if isinstance(obj, list):
        out = []
        for i, v in enumerate(obj): out.extend(_walk(v, f"{path}[{i}]"))
        return out
    return [(path, obj)]


def _assert_safe(obj: dict[str, Any], label: str) -> None:
    for path, value in _walk(obj):
        if isinstance(value, str):
            low = value.lower()
            if SECRET_OR_URL_RE.search(value):
                raise ValueError(f"{label}_forbidden_value:{path}")
            if any(term in low for term in FORBIDDEN_TEXT):
                raise ValueError(f"{label}_forbidden_text:{path}")


def _add(blockers: list[str], ok: bool, msg: str) -> None:
    if not ok: blockers.append(msg)


def _intent_blockers(intent: dict[str, Any]) -> list[str]:
    b: list[str] = []
    required = {"schema_version", "operator_intent_id", "operator_id", "created_at_manual", "intent_class", "raw_operator_topic", "content_lane", "intended_platforms", *REQUEST_FALSE_FLAGS, "notes"}
    _add(b, not (set(intent) - required), "operator_intent_extra_fields")
    for key in required: _add(b, key in intent, f"missing_operator_intent_{key}")
    _add(b, intent.get("schema_version") == SCHEMA_VERSION, "operator_intent_schema_version_invalid")
    _add(b, intent.get("intent_class") in INTENT_CLASSES, "operator_intent_class_invalid")
    _add(b, intent.get("content_lane") in CONTENT_LANES, "operator_intent_content_lane_invalid")
    _add(b, isinstance(intent.get("raw_operator_topic"), str) and bool(intent.get("raw_operator_topic", "").strip()), "operator_intent_topic_missing")
    _add(b, isinstance(intent.get("notes"), str), "operator_intent_notes_not_string")
    platforms = intent.get("intended_platforms")
    _add(b, isinstance(platforms, list) and all(p in PLATFORMS for p in platforms), "operator_intent_platforms_invalid")
    for flag in REQUEST_FALSE_FLAGS: _add(b, intent.get(flag) is False, f"operator_intent_{flag}_not_false")
    return b


def _make_research(intent: dict[str, Any]) -> dict[str, Any]:
    topic = str(intent.get("raw_operator_topic", ""))
    safe_angles = ["educational framing", "source limitations", "human review before publication"]
    required_caveats = ["Review packet only", "No external research performed", "Human review required"]
    missing = ["fresh external source review", "official citation verification"]
    return {
        "research_packet_id": "research_" + _sha({"topic": topic})[:16],
        "operator_intent_id": intent.get("operator_intent_id", ""),
        "topic": topic,
        "source_mode": "operator_supplied_context_only",
        "source_refs": [],
        "official_source_refs": [],
        "non_official_source_refs": [],
        "freshness_status": "source_review_required",
        "source_quality_status": "unverified_review_only",
        "missing_evidence": missing,
        "safe_angles": safe_angles,
        "unsafe_angles": ["market calls", "certainty claims", "advice framing"],
        "required_caveats": required_caveats,
        "no_signal_status": "pass",
        "no_advice_status": "pass",
        "allowed_for_drafting": True,
        "allowed_for_publication": False,
        "blocked_reasons": [],
        "human_review_required": True,
    }


def _research_blockers(packet: dict[str, Any]) -> list[str]:
    b: list[str] = []
    _add(b, packet.get("source_mode") in SOURCE_MODES, "research_source_mode_invalid")
    _add(b, isinstance(packet.get("missing_evidence"), list), "research_missing_evidence_not_list")
    _add(b, bool(packet.get("safe_angles")), "research_safe_angles_missing")
    _add(b, bool(packet.get("required_caveats")), "research_required_caveats_missing")
    _add(b, packet.get("no_signal_status") == "pass", "research_no_signal_status_not_pass")
    _add(b, packet.get("no_advice_status") == "pass", "research_no_advice_status_not_pass")
    _add(b, packet.get("allowed_for_publication") is False, "research_allowed_for_publication_not_false")
    _add(b, packet.get("human_review_required") is True, "research_human_review_required_not_true")
    if packet.get("allowed_for_drafting") is True:
        _add(b, bool(packet.get("safe_angles")) and bool(packet.get("required_caveats")), "research_drafting_without_safety")
    return b


def _make_article(intent: dict[str, Any], research: dict[str, Any]) -> dict[str, Any]:
    title = f"Review draft: {intent.get('raw_operator_topic', '')}"
    article_id = "article_" + _sha({"intent": intent.get("operator_intent_id", ""), "title": title})[:16]
    seo_id = "seo_" + _sha({"article": article_id})[:16]
    return {
        "article_id": article_id,
        "research_packet_id": research["research_packet_id"],
        "title": title,
        "subtitle": "Review-only educational draft for human inspection.",
        "slug_candidate": "review-draft-" + _sha(title)[:8],
        "lede": "This review-only draft frames the topic for human editorial inspection.",
        "body_markdown": "## Review draft\n\nThis packet is local-only and requires human review before any publication path.",
        "section_map": ["lede", "context", "limitations", "review questions"],
        "citations": [],
        "citation_status": "source_review_required",
        "limitations": ["No external source verification performed", "Requires separate publication review"],
        "disclosure": "Educational review draft only. Not personal guidance or alert service.",
        "media_request": None,
        "seo_packet_id": seo_id,
        "draft_status": "review_only",
        "human_review_required": True,
        "publication_ready": False,
        "no_advice_status": "pass",
        "no_signal_status": "pass",
        "blocked_reasons": [],
    }


def _article_blockers(packet: dict[str, Any]) -> list[str]:
    b: list[str] = []
    _add(b, packet.get("draft_status") == "review_only", "article_draft_status_invalid")
    _add(b, packet.get("human_review_required") is True, "article_human_review_required_not_true")
    _add(b, packet.get("publication_ready") is False, "article_publication_ready_not_false")
    _add(b, bool(packet.get("limitations")), "article_limitations_missing")
    _add(b, bool(packet.get("disclosure")), "article_disclosure_missing")
    if not packet.get("citations"):
        _add(b, packet.get("citation_status") == "source_review_required" and packet.get("publication_ready") is False, "article_empty_citations_without_review_status")
    _add(b, packet.get("no_advice_status") == "pass", "article_no_advice_status_not_pass")
    _add(b, packet.get("no_signal_status") == "pass", "article_no_signal_status_not_pass")
    return b


def _make_seo(article: dict[str, Any]) -> dict[str, Any]:
    return {
        "seo_packet_id": article["seo_packet_id"],
        "article_id": article["article_id"],
        "primary_keyword": "review draft",
        "secondary_keywords": ["source review", "human inspection", "content operations"],
        "search_intent": "educational_review",
        "title_candidates": [article["title"]],
        "subtitle_candidates": [article["subtitle"]],
        "slug_candidates": [article["slug_candidate"]],
        "meta_description": "Review-only draft requiring human inspection and source verification.",
        "readability_score": "review_required",
        "editorial_score": "review_required",
        "audience_fit_score": "review_required",
        "rejected_clickbait": ["certainty claim", "market call", "guaranteed outcome"],
        "limitations_preserved": True,
        "caveats_preserved": True,
        "review_only": True,
    }


def _seo_blockers(packet: dict[str, Any]) -> list[str]:
    b: list[str] = []
    _add(b, packet.get("review_only") is True, "seo_review_only_not_true")
    _add(b, packet.get("limitations_preserved") is True, "seo_limitations_preserved_not_true")
    _add(b, packet.get("caveats_preserved") is True, "seo_caveats_preserved_not_true")
    _add(b, isinstance(packet.get("rejected_clickbait"), list), "seo_rejected_clickbait_missing")
    return b


def _make_discord(article: dict[str, Any]) -> dict[str, Any]:
    seed = {"article_id": article["article_id"], "title": article["title"]}
    return {
        "discord_drop_id": "discord_drop_" + _sha(seed)[:16],
        "article_id": article["article_id"],
        "drop_type": "substack_drop",
        "target_channel_class": "substack_drops",
        "title": article["title"],
        "one_line_thesis": "Review-only discussion seed for human inspection.",
        "why_it_matters": "Helps evaluate whether the topic deserves deeper sourced review.",
        "summary": "Local candidate only; not approved for posting.",
        "discussion_question": "What source checks should happen before this becomes a publishable draft?",
        "source_link_placeholder": None,
        "disclosure": article["disclosure"],
        "payload_hash_candidate": _sha(seed),
        "approval_required": True,
        "publication_ready": False,
        "dispatch_allowed": False,
        "human_review_required": True,
        "no_advice_status": "pass",
        "no_signal_status": "pass",
        "blocked_reasons": [],
    }


def _discord_blockers(packet: dict[str, Any]) -> list[str]:
    b: list[str] = []
    _add(b, packet.get("drop_type") in DROP_TYPES, "discord_drop_type_invalid")
    _add(b, packet.get("target_channel_class") in CHANNEL_CLASSES, "discord_target_channel_class_invalid")
    _add(b, bool(packet.get("discussion_question")), "discord_discussion_question_missing")
    _add(b, bool(packet.get("disclosure")), "discord_disclosure_missing")
    _add(b, packet.get("approval_required") is True, "discord_approval_required_not_true")
    _add(b, packet.get("publication_ready") is False, "discord_publication_ready_not_false")
    _add(b, packet.get("dispatch_allowed") is False, "discord_dispatch_allowed_not_false")
    _add(b, packet.get("human_review_required") is True, "discord_human_review_required_not_true")
    return b


def _make_variants(intent: dict[str, Any], article: dict[str, Any]) -> dict[str, Any]:
    platforms = list(intent.get("intended_platforms") or [])
    deferred = [p for p in platforms if p in {"linkedin_org_deferred", "tiktok_deferred"}]
    readiness = {p: False for p in platforms}
    fallback = {p: (p == "x_manual") for p in platforms}
    variants = {p: {"review_only_text": f"Review-only {p} candidate for {article['title']}", "dispatch_ready": False} for p in platforms}
    return {
        "variant_set_id": "variant_set_" + _sha({"article": article["article_id"], "platforms": platforms})[:16],
        "article_id": article["article_id"],
        "variants": variants,
        "execution_readiness_by_platform": readiness,
        "manual_fallback_by_platform": fallback,
        "deferred_platforms": deferred,
        "inspection_required": True,
        "approval_required": True,
        "publication_ready": False,
        "dispatch_allowed": False,
        "no_advice_status": "pass",
        "no_signal_status": "pass",
        "blocked_reasons": [],
    }


def _variant_blockers(packet: dict[str, Any]) -> list[str]:
    b: list[str] = []
    readiness = packet.get("execution_readiness_by_platform", {})
    _add(b, isinstance(readiness, dict) and all(v is False for v in readiness.values()), "variant_execution_readiness_not_all_false")
    variants = packet.get("variants", {})
    if isinstance(variants, dict):
        _add(b, all(v.get("dispatch_ready") is False for v in variants.values() if isinstance(v, dict)), "variant_dispatch_ready_not_false")
    _add(b, packet.get("manual_fallback_by_platform", {}).get("x_manual") is True if "x_manual" in packet.get("manual_fallback_by_platform", {}) else True, "variant_x_manual_not_manual")
    deferred = set(packet.get("deferred_platforms", []))
    for p in ("linkedin_org_deferred", "tiktok_deferred"):
        if p in readiness: _add(b, p in deferred, f"variant_{p}_not_deferred")
    _add(b, packet.get("inspection_required") is True, "variant_inspection_required_not_true")
    _add(b, packet.get("approval_required") is True, "variant_approval_required_not_true")
    _add(b, packet.get("publication_ready") is False, "variant_publication_ready_not_false")
    _add(b, packet.get("dispatch_allowed") is False, "variant_dispatch_allowed_not_false")
    return b


def make_content_production_review_bundle(operator_intent: dict[str, Any]) -> ContentProductionReviewBundle:
    _assert_safe(operator_intent, "operator_intent")
    research = _make_research(operator_intent)
    article = _make_article(operator_intent, research)
    seo = _make_seo(article)
    discord = _make_discord(article)
    variants = _make_variants(operator_intent, article)
    for label, packet in (("research", research), ("article", article), ("seo", seo), ("discord", discord), ("variants", variants)):
        _assert_safe(packet, label)
    blockers = _intent_blockers(operator_intent) + _research_blockers(research) + _article_blockers(article) + _seo_blockers(seo) + _discord_blockers(discord) + _variant_blockers(variants)
    eligible = not blockers
    bundle_id = "content_production_review_bundle_" + _sha({"intent": operator_intent.get("operator_intent_id", ""), "topic": operator_intent.get("raw_operator_topic", "")})[:16]
    bundle = ContentProductionReviewBundle(
        schema_version=SCHEMA_VERSION, task_label=TASK_LABEL, content_production_review_bundle_id=bundle_id,
        operator_intent_packet=operator_intent, research_grounding_packet=research,
        canonical_article_review_packet=article, seo_editorial_packet=seo,
        discord_drop_candidate_packet=discord, platform_variant_set_candidate_packet=variants,
        eligible_for_future_draft_inspection_task=eligible, eligible_for_payload_hash_approval_task=eligible,
        eligible_for_live_send_now=False, provider_call_made=False, env_read=False, credential_value_read=False,
        network_call_made=False, browser_session_used=False, public_url_created=False, metrics_created=False,
        publication_ready=False, dispatch_allowed=False, runtime_truth=False, human_review_required=True,
        blockers=blockers, warnings=["review_only", "no_provider_call", "no_live_send", "human_review_required"],
    )
    data = asdict(bundle)
    return ContentProductionReviewBundle(**{**data, "packet_sha256": _packet_sha(data)})


def blocked_bundle(reason: str) -> ContentProductionReviewBundle:
    empty: dict[str, Any] = {}
    bundle = ContentProductionReviewBundle(SCHEMA_VERSION, TASK_LABEL, "content_production_review_bundle_blocked", empty, empty, empty, empty, empty, empty, False, False, False, False, False, False, False, False, False, False, False, False, False, True, [reason], ["blocked_fail_closed"])
    data = asdict(bundle)
    return ContentProductionReviewBundle(**{**data, "packet_sha256": _packet_sha(data)})


def load_json_object(path: str | Path) -> dict[str, Any]:
    try: data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc: raise ValueError("malformed_json") from exc
    if not isinstance(data, dict): raise ValueError("json_not_object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 content production review bundle CLI")
    parser.add_argument("--operator-intent", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try: packet = make_content_production_review_bundle(load_json_object(args.operator_intent))
    except ValueError as exc: packet = blocked_bundle(str(exc))
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")
    return 0 if packet.eligible_for_future_draft_inspection_task else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
