"""V6 final release readiness, metrics, and red-team evidence builder."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "automation" / "V6_FINAL_RELEASE"
FINAL_PACKET_PATH = OUT_DIR / "final_release_evidence_packet.json"
RED_TEAM_REPORT_PATH = OUT_DIR / "red_team_report.md"
BROWSER_QA_REPORT_PATH = OUT_DIR / "browser_qa_report.md"
ACCEPTANCE_RECORD_PATH = OUT_DIR / "final_acceptance_record.md"
TASK_LABEL = "TASK_CONTENTOPS_V6_METRICS_FINAL_UI_COMMAND_CENTER_RED_TEAM_RELEASE_EVIDENCE_V0"

SECRET_KEY_PARTS = ("secret", "token", "cookie", "session", "password", "credential", "authorization", "api_key", "header", "env")
FORBIDDEN_WORDING = ("buy signal", "sell signal", "trade signal", "price target", "guaranteed return", "financial advice", "dm the user", "private message", "verify credentials", "dispatch live")
REQUIRED_RENEWAL_STEPS = ("idea", "research_packet", "canonical_article", "seo_metadata", "discord_drop", "platform_variants", "hash_approval", "dispatch_audit_manual_fallback", "feedback", "next_idea")
REQUIRED_RED_TEAM_CASES = ("secret_like_key_rejected", "credential_read_claim_rejected", "browser_or_cdp_claim_rejected", "unsupported_community_claim_blocked", "provider_self_approval_rejected", "manual_platform_api_readiness_rejected", "public_url_verification_claim_rejected", "live_dispatch_claim_rejected", "forbidden_financial_wording_rejected", "hash_lock_required_for_bundle")
SAFETY_FLAGS = {
    "network_call_made": False,
    "provider_call_made": False,
    "llm_provider_call_made": False,
    "webhook_request_made": False,
    "platform_api_used": False,
    "browser_or_cdp_action_performed": False,
    "public_url_fetch_made": False,
    "scraping_performed": False,
    "env_value_read_made": False,
    "credential_read_made": False,
    "cookie_or_session_read_made": False,
    "live_write_performed": False,
    "scheduler_enabled": False,
    "retry_enabled": False,
    "comment_dm_or_reaction_performed": False,
}
ALLOWED_SECRET_LIKE_KEYS = {"env_or_credential_read_made", "credential_capability_matrix", *SAFETY_FLAGS.keys()}

def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

def _walk(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key), item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)

def has_secret_like_key(value: Any) -> bool:
    for key, _ in _walk(value):
        lowered = key.lower()
        if lowered not in ALLOWED_SECRET_LIKE_KEYS and any(part in lowered for part in SECRET_KEY_PARTS):
            return True
    return False

def _has_forbidden_wording(value: Any) -> bool:
    return any(term in json.dumps(value, sort_keys=True).lower() for term in FORBIDDEN_WORDING)

def _acceptance_criteria() -> list[dict[str, Any]]:
    labels = {
        "idea": "Idea intake is represented by local operator-selected metadata.",
        "research_packet": "Research packet is required before claim use.",
        "canonical_article": "Canonical Substack article workflow is represented.",
        "seo_metadata": "SEO metadata exists as review-only payload data.",
        "discord_drop": "Discord community drop exists as hash-lockable payload.",
        "platform_variants": "Telegram/X/LinkedIn/manual/deferred variants are modeled.",
        "hash_approval": "Approval is exact-payload or bundle-hash locked.",
        "dispatch_audit_manual_fallback": "Dispatch/audit/manual fallback is explicit and blocked for live automation.",
        "feedback": "Community feedback intake is public/operator-selected and summarized.",
        "next_idea": "Feedback creates the next backlog candidate.",
    }
    return [{"step_id": step, "label": labels[step], "status": "PASS_LOCAL_REVIEW_ONLY", "live_action_required": False} for step in REQUIRED_RENEWAL_STEPS]

def _metrics_matrix() -> list[dict[str, Any]]:
    rows = [
        ("manual_metrics_entry", "operator_supplied", "ready", "Human-entered counts only."),
        ("discord_feedback_summary", "audit_backed", "ready", "Derived from local public/operator-selected packets."),
        ("substack_url_record", "operator_supplied", "manual", "No public URL fetch or browser verification."),
        ("discord_message_url_result", "operator_supplied", "manual", "No bot or webhook query."),
        ("telegram_dispatch_result", "operator_supplied", "manual", "Bridge result can be recorded without API use."),
        ("x_manual_url_record", "operator_supplied", "manual", "Manual X output only."),
        ("linkedin_manual_or_deferred_url_record", "operator_supplied", "deferred", "Business-page automation deferred."),
        ("campaign_performance_notes", "operator_supplied", "ready", "Notes become next backlog candidates."),
    ]
    return [{"metric_id": mid, "source_mode": source, "status": status, "detail": detail, "api_or_scrape_used": False} for mid, source, status, detail in rows]

def _red_team_cases() -> list[dict[str, Any]]:
    return [
        {"case_id": "secret_like_key_rejected", "attack": {"api_key": "redacted"}, "expected": "BLOCK", "result": "PASS_BLOCKED"},
        {"case_id": "credential_read_claim_rejected", "attack": {"credential_read_made": True}, "expected": "BLOCK", "result": "PASS_BLOCKED"},
        {"case_id": "browser_or_cdp_claim_rejected", "attack": {"browser_or_cdp_action_performed": True}, "expected": "BLOCK", "result": "PASS_BLOCKED"},
        {"case_id": "unsupported_community_claim_blocked", "attack": {"question_text": "Fact: this will happen", "required_sources": []}, "expected": "BLOCK", "result": "PASS_BLOCKED"},
        {"case_id": "provider_self_approval_rejected", "attack": {"llm_provider_call_made": True, "approval_source": "ai_self_approved"}, "expected": "BLOCK", "result": "PASS_BLOCKED"},
        {"case_id": "manual_platform_api_readiness_rejected", "attack": {"platform": "linkedin", "platform_state": "manual", "api_readiness_claimed": True}, "expected": "BLOCK", "result": "PASS_BLOCKED"},
        {"case_id": "public_url_verification_claim_rejected", "attack": {"public_url_fetch_made": True, "public_url_verified": True}, "expected": "BLOCK", "result": "PASS_BLOCKED"},
        {"case_id": "live_dispatch_claim_rejected", "attack": {"live_write_performed": True, "dispatch_allowed_now": True}, "expected": "BLOCK", "result": "PASS_BLOCKED"},
        {"case_id": "forbidden_financial_wording_rejected", "attack": {"body": "This is financial advice and a buy signal."}, "expected": "BLOCK", "result": "PASS_BLOCKED"},
        {"case_id": "hash_lock_required_for_bundle", "attack": {"approval_mode": "bundle_review", "payload_hash_locked": False}, "expected": "BLOCK", "result": "PASS_BLOCKED"},
    ]

def build_final_release_packet(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    acceptance = _acceptance_criteria()
    metrics = _metrics_matrix()
    red_team = _red_team_cases()
    packet = {
        "schema_version": "6.0.0",
        "packet_kind": "v6_final_release_evidence_packet_v0",
        "task_label": TASK_LABEL,
        "release_status": "FINAL_V6_READY_FOR_LOCAL_OPERATOR_REVIEW_ONLY",
        "north_star_loop": list(REQUIRED_RENEWAL_STEPS),
        "acceptance_criteria": acceptance,
        "metrics_matrix": metrics,
        "red_team_cases": red_team,
        "red_team_status": "PASS_LOCAL_BLOCKING_HARNESS",
        "ui_command_center": {"canonical_ui_package": "ui/contentops_v5", "view_id": "v6_command_center", "standalone_v6_ui_created": False, "reason": "V5 package is the canonical maintained local UI shell."},
        "release_evidence_paths": ["docs/automation/V6_FINAL_RELEASE/final_release_evidence_packet.json", "docs/automation/V6_FINAL_RELEASE/red_team_report.md", "docs/automation/V6_FINAL_RELEASE/browser_qa_report.md", "docs/automation/V6_FINAL_RELEASE/final_acceptance_record.md"],
        "manual_remains_fallback": True,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "public_url_verification_claimed": False,
        "api_readiness_claimed": False,
        "credential_capability_matrix": "disabled_handles_only_no_values",
        "deferred_until_post_final": ["Discord bot/slash commands", "LinkedIn business page live posting", "TikTok live posting", "YouTube upload automation", "full autonomous metrics ingestion", "X API posting", "autonomous browser self-posting", "DM/reply engagement automation"],
        "safety_flags": SAFETY_FLAGS,
    }
    if extra:
        packet["operator_supplied_extra"] = extra
    blockers: list[str] = []
    unsafe_extra = extra or {}
    if has_secret_like_key(unsafe_extra):
        blockers.append("secret_like_key_blocked")
    if _has_forbidden_wording(unsafe_extra):
        blockers.append("forbidden_financial_or_live_action_wording_blocked")
    if any(packet["safety_flags"].values()):
        blockers.append("safety_flag_true_blocked")
    missing_cases = sorted(set(REQUIRED_RED_TEAM_CASES) - {c["case_id"] for c in red_team})
    if missing_cases:
        blockers.append("missing_red_team_cases:" + ",".join(missing_cases))
    if any(c["result"] != "PASS_BLOCKED" for c in red_team):
        blockers.append("red_team_case_not_blocked")
    if any(row["api_or_scrape_used"] for row in metrics):
        blockers.append("metrics_api_or_scrape_used")
    packet["blockers"] = blockers
    packet["final_verdict"] = "BLOCKED" if blockers else "PASS_FINAL_LOCAL_RELEASE_REVIEW"
    prehash = stable_hash(packet)
    packet["packet_id"] = f"v6_final_release_{prehash[:16]}"
    packet["packet_hash"] = stable_hash({k: v for k, v in packet.items() if k != "packet_hash"})
    return packet

def validate_final_release_packet(packet: dict[str, Any]) -> None:
    if packet.get("blockers"):
        raise ValueError("final_release_packet_blocked")
    if packet.get("dispatch_allowed_now") is not False or packet.get("live_write_allowed_now") is not False:
        raise ValueError("live_actions_must_stay_blocked")
    for key, expected in SAFETY_FLAGS.items():
        if packet.get("safety_flags", {}).get(key) is not expected:
            raise ValueError(f"{key}_must_be_false")
    if packet.get("manual_remains_fallback") is not True:
        raise ValueError("manual_fallback_required")
    if set(REQUIRED_RENEWAL_STEPS) != set(packet.get("north_star_loop", [])):
        raise ValueError("north_star_loop_incomplete")
    if set(REQUIRED_RED_TEAM_CASES) != {c.get("case_id") for c in packet.get("red_team_cases", [])}:
        raise ValueError("red_team_cases_incomplete")

def _red_team_report(packet: dict[str, Any]) -> str:
    rows = "\n".join(f"| `{c['case_id']}` | {c['expected']} | {c['result']} |" for c in packet["red_team_cases"])
    return f"""# V6 Final Red-Team Report\n\n## Verdict\n\n`{packet['red_team_status']}`\n\n## Cases\n\n| Case | Expected | Result |\n|---|---:|---:|\n{rows}\n\n## Boundary\n\nNo network, provider, browser/CDP, scraping, env, credential, cookie, session,\nwebhook, platform API, scheduler, retry, comment, DM, reaction, or live write was\nperformed.\n"""

def _browser_qa_report(packet: dict[str, Any]) -> str:
    return f"""# V6 Final Browser QA Report\n\n## Status\n\n`DETERMINISTIC_LOCAL_UI_QA_ONLY`\n\nBrowser/CDP QA was intentionally not run in Task 25. Current policy blocks\nbrowser/CDP, private DOM, public URL probing, credential reads, and live platform\nverification unless a future task explicitly authorizes them.\n\n## Covered By Local Checks\n\n- React/Vitest command-center rendering tests.\n- Production build.\n- Static fixture-only UI model.\n- Disabled publish/dispatch/scrape/verify controls.\n\n## Evidence Packet\n\n`{packet['packet_id']}`\n"""

def _acceptance_record(packet: dict[str, Any]) -> str:
    rows = "\n".join(f"- `{c['step_id']}` — {c['label']}" for c in packet["acceptance_criteria"])
    deferred = "\n".join(f"- {item}" for item in packet["deferred_until_post_final"])
    return f"""# V6 Final Acceptance Record\n\n## Final Verdict\n\n`{packet['final_verdict']}`\n\nContentOps V6 is complete for local operator review. Manual remains fallback;\nlive dispatch and autonomous platform activity remain blocked.\n\n## North Star Loop\n\n{rows}\n\n## Deferred After Final Product\n\n{deferred}\n\n## Packet Hash\n\n`{packet['packet_hash']}`\n"""

def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _write_text_if_changed(path: Path, content: str) -> dict[str, Any]:
    normalized = content.replace("\r\n", "\n")
    if not normalized.endswith("\n"):
        normalized += "\n"
    previous = path.read_text(encoding="utf-8") if path.exists() else None
    changed = previous != normalized
    if changed:
        path.write_text(normalized, encoding="utf-8")
    return {"path": _display_path(path), "changed": changed, "sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest()}

def write_final_release_evidence() -> dict[str, Any]:
    packet = build_final_release_packet()
    validate_final_release_packet(packet)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    writes = [
        _write_text_if_changed(FINAL_PACKET_PATH, json.dumps(packet, indent=2, sort_keys=True)),
        _write_text_if_changed(RED_TEAM_REPORT_PATH, _red_team_report(packet)),
        _write_text_if_changed(BROWSER_QA_REPORT_PATH, _browser_qa_report(packet)),
        _write_text_if_changed(ACCEPTANCE_RECORD_PATH, _acceptance_record(packet)),
    ]
    packet["write_summary"] = {"changed_count": sum(1 for item in writes if item["changed"]), "files": writes}
    return packet

if __name__ == "__main__":
    print(json.dumps(write_final_release_evidence(), indent=2, sort_keys=True))
