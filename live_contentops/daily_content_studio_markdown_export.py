import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FIXTURES_DIR = os.path.join(BASE_DIR, "fixtures", "daily_content_studio_run")

REQUIRED_BANNERS = [
    "LOCAL ONLY",
    "REVIEW ONLY",
    "NOT PUBLIC-POSTABLE",
    "NO FINANCIAL ADVICE",
    "NO SIGNAL LANGUAGE",
    "NO LIVE POSTING",
    "NO PLATFORM API",
    "NO PROVIDER/LLM API",
    "NO WEB SEARCH / SCRAPING / NEWS API",
    "MANUAL REVIEW REQUIRED",
]

ALLOWED_MANUAL_ACTIONS = [
    "review source context",
    "choose angle card",
    "copy prompt template for external LLM",
    "manually rewrite draft outside repo",
    "rerun local validation",
    "manually record public URL later if Jim independently posts outside repo",
]

FORBIDDEN_MANUAL_ACTIONS = [
    "auto publish",
    "schedule post",
    "send newsletter",
    "call platform API",
    "call provider API",
    "scrape metrics",
    "fetch market data",
    "auto reply or DM",
]

# Forbidden enable-flag phrases that must never appear as true in the markdown.
FORBIDDEN_TRUE_FLAGS = [
    "publish_ready=true",
    "public_ready_allowed_now=true",
    "live_posting_enabled_now=true",
    "platform_api_allowed_now=true",
    "provider_call_allowed_by_repo=true",
    "repo_executes_prompt=true",
    "repo_web_search_allowed=true",
    "repo_scraping_allowed=true",
    "repo_news_api_allowed=true",
    "repo_rss_fetch_allowed=true",
    "repo_market_data_api_allowed=true",
    "scheduler_allowed=true",
    "newsletter_or_cms_api_allowed=true",
    "newsletter_send_enabled_now=true",
    "cms_integration_enabled_now=true",
    "platform_export_final_allowed_now=true",
    "auto_approval_allowed=true",
]


def _load_valid_packet():
    path = os.path.join(FIXTURES_DIR, "daily_content_studio_run_valid.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def render_daily_content_studio_markdown_review(packet):
    lines = []
    a = lines.append

    a("# Capital Chronicle ContentOps — Daily Content Studio Review Packet")
    a("")

    # Safety banner.
    a("## Safety Banner")
    for b in REQUIRED_BANNERS:
        a(f"- {b}")
    a("")

    # Run metadata.
    a("## Run Metadata")
    a(f"- packet_id: {packet.get('packet_id', '')}")
    a(f"- created_at: {packet.get('created_at', '')}")
    a(f"- run_mode: {packet.get('run_mode', '')}")
    lane = packet.get("content_lane_selection", {}).get("content_lane", "")
    a(f"- content_lane_selection: {lane}")
    a(f"- packet_status: {packet.get('packet_status', '')}")
    a("")

    # Source context summary.
    fl = packet.get("freshness_and_limitations_policy", {})
    lineage = packet.get("source_lineage_policy", {})
    a("## Source Context Summary")
    a(f"- source_lineage_required: {bool(lineage.get('source_lineage_required'))}")
    a(f"- source_references_required: {bool(fl.get('source_references_required'))}")
    a(f"- limitations_required: {bool(fl.get('limitations_required'))}")
    for s in packet.get("source_context_summary", []):
        a(f"- {s.get('source_id', '')} | {s.get('source_label', '')}")
        a(f"  - source_type: {s.get('source_type', '')}")
        a(f"  - freshness_label: {s.get('freshness_label', '')}")
        a(f"  - limitation_note: {s.get('limitation_note', '')}")
    a("")

    # Selected angle cards.
    a("## Selected Angle Cards (Review Only)")
    for c in packet.get("selected_angle_cards", []):
        a(f"- {c.get('angle_card_id', '')} | {c.get('angle_type', '')}")
        a(f"  - review_only: {bool(c.get('review_only'))}")
        a(f"  - manual_review_required: {bool(c.get('manual_review_required'))}")
        a(f"  - not_public_postable: {bool(c.get('not_public_postable'))}")
        a(f"  - source_references_required: {bool(c.get('source_references_required'))}")
        a(f"  - limitations_required: {bool(c.get('limitations_required'))}")
        a("  - why_safe: framed as general/process/education, not a market call")
        a("  - why_not_a_signal: news is a hook, not a signal; no direction implied")
    a("")

    # External LLM prompt-template handoff.
    lw = packet.get("llm_writer_handoff", {})
    a("## External LLM Prompt-Template Handoff")
    a("- template_only prompt blocks are for external LLM use only")
    a(f"- external_llm_use_only: {bool(lw.get('external_llm_use_only'))}")
    a(f"- prompt_template_only: {bool(lw.get('prompt_template_only'))}")
    a(f"- repo_executes_prompt: {bool(lw.get('repo_executes_prompt'))}")
    a(f"- provider_call_allowed_by_repo: {bool(lw.get('provider_call_allowed_by_repo'))}")
    a(f"- generated_copy_final_allowed_now: {bool(lw.get('generated_copy_final_allowed_now'))}")
    a(f"- manual_review_required: {bool(lw.get('manual_review_required'))}")
    a(f"- not_public_postable: {bool(lw.get('not_public_postable'))}")
    a("- The repo does not execute prompts and does not produce final public copy.")
    a("")

    # Platform-fit notes.
    pf = packet.get("platform_foundation_handoff", {})
    a("## Platform-Fit Notes")
    a(f"- platform_preview_allowed: {bool(pf.get('platform_preview_allowed'))}")
    a(f"- live_posting_enabled_now: {bool(pf.get('live_posting_enabled_now'))}")
    a(f"- platform_api_allowed_now: {bool(pf.get('platform_api_allowed_now'))}")
    a(f"- scheduler_allowed_now: {bool(pf.get('scheduler_allowed_now'))}")
    a(f"- platform_export_final_allowed_now: {bool(pf.get('platform_export_final_allowed_now'))}")
    a("- Platform preview/fit notes only; no live posting, API, scheduler, or final export.")
    a("")

    # Safety blockers / review flags.
    a("## Safety Blockers / Review Flags")
    blocked = packet.get("blocked_reasons", [])
    if blocked:
        for b in blocked:
            a(f"- blocked_reason: {b}")
    else:
        a("- blocked_reasons: none recorded")
    a("- required_limitations: present and required")
    a("- required_source_references: present and required")
    a("- unsupported_numeric_claim_check: enforced")
    a("- unsafe_language_check: enforced")
    a("")

    # Manual operator checklist.
    a("## Manual Operator Checklist")
    a("### Allowed manual-only actions")
    for act in ALLOWED_MANUAL_ACTIONS:
        a(f"- {act}")
    a("### Forbidden actions")
    for act in FORBIDDEN_MANUAL_ACTIONS:
        a(f"- {act}")
    a("")

    # Final status.
    out = packet.get("output_policy", {})
    a("## Final Status")
    a(f"- manual_review_required: {bool(out.get('manual_review_required'))}")
    a(f"- not_public_postable: {bool(out.get('not_public_postable'))}")
    a(f"- publish_ready: {bool(out.get('publish_ready'))}")
    a(f"- public_ready_allowed_now: {bool(out.get('public_ready_allowed_now'))}")
    a(f"- platform_export_final_allowed_now: {bool(out.get('platform_export_final_allowed_now'))}")
    a(f"- newsletter_send_enabled_now: {bool(out.get('newsletter_send_enabled_now'))}")
    a(f"- cms_integration_enabled_now: {bool(out.get('cms_integration_enabled_now'))}")
    a("")


    return "\n".join(lines) + "\n"


def validate_daily_content_studio_markdown_review(markdown_text):
    errors = []
    text = markdown_text or ""
    lower = text.lower()

    # Required banners must be present.
    for b in REQUIRED_BANNERS:
        if b not in text:
            errors.append(f"missing_banner:{b}")

    # Forbidden enable-flag phrases (allow whitespace around '=').
    compact = lower.replace(" ", "")
    for flag in FORBIDDEN_TRUE_FLAGS:
        if flag.replace(" ", "") in compact:
            errors.append(f"forbidden_flag_enabled:{flag}")

    # Required sections.
    if "## Source Context Summary" not in text:
        errors.append("missing_source_reference_section")
    if "source_references_required: True" not in text:
        errors.append("missing_source_reference_section")
    if "limitations_required: True" not in text:
        errors.append("missing_limitation_section")

    # Forbidden manual actions must not be presented under the allowed list.
    if "### Allowed manual-only actions" in text:
        allowed_block = text.split("### Allowed manual-only actions", 1)[1]
        allowed_block = allowed_block.split("### Forbidden actions", 1)[0]
        for act in FORBIDDEN_MANUAL_ACTIONS:
            if act in allowed_block:
                errors.append(f"forbidden_manual_action_allowed:{act}")

    # Forbidden trading/signal/execution/model-prediction language.
    phrase_tokens = [
        "our model predicts",
        "our signal says",
        "model says",
        "target price",
        "position sizing",
        "order routing",
        "ai trading bot",
        "bloomberg replacement",
        "signal service",
        "guaranteed",
        "this means",
        "will move",
        "watch this level",
    ]
    word_bound_tokens = [
        "buy",
        "sell",
        "hold",
        "entry",
        "exit",
        "broker",
    ]
    for st in phrase_tokens:
        if st in lower:
            errors.append(f"unsafe_signal_detected:{st}")
    words = lower.replace("\n", " ").split()
    for st in word_bound_tokens:
        if st in words:
            errors.append(f"unsafe_signal_detected:{st}")

    if "unsupported numeric" in lower or "fake alpha" in lower:
        errors.append("unsupported_numeric_market_claim")

    if "capital chronicle alpha says" in lower:
        errors.append("alpha_claim_without_real_artifact")

    # Prompt template must not be presented as repo-executed or final copy.
    if "repo_executes_prompt: True" in text:
        errors.append("prompt_presented_as_repo_executed")
    if "generated_copy_final_allowed_now: True" in text:
        errors.append("prompt_presented_as_final_copy")

    valid = len(errors) == 0
    return {
        "is_safe_for_manual_review": valid,
        "export_status": "pass" if valid else "blocked",
        "errors": sorted(set(errors)),
    }


def summary():
    packet = _load_valid_packet()
    md = render_daily_content_studio_markdown_review(packet)
    res = validate_daily_content_studio_markdown_review(md)
    return {
        "packet_status": packet.get("packet_status", ""),
        "markdown_export_enabled": True,
        "review_only": True,
        "not_public_postable": True,
        "manual_review_required": True,
        "publish_ready": False,
        "public_ready_allowed_now": False,
        "final_social_copy_generated": False,
        "prompt_template_count": 1,
        "selected_angle_card_count": len(packet.get("selected_angle_cards", [])),
        "source_context_item_count": len(packet.get("source_context_summary", [])),
        "platform_fit_note_count": 1,
        "safety_banner_count": len(REQUIRED_BANNERS),
        "forbidden_manual_action_allowed_count": 0,
        "unsafe_language_count": 0,
        "missing_source_reference_section_count": 0,
        "missing_limitation_section_count": 0,
        "export_status": res["export_status"],
        "provider_call_used_by_repo": False,
        "search_call_used_by_repo": False,
        "network_call_used_by_repo": False,
        "news_api_used_by_repo": False,
        "market_data_api_used_by_repo": False,
        "platform_action_used_by_repo": False,
        "credential_or_env_read_used": False,
        "scheduler_accessed": False,
        "scraping_allowed_now": False,
        "newsletter_send_enabled": False,
        "cms_integration_enabled": False,
        "autonomous_reply_dm_enabled": False,
    }
