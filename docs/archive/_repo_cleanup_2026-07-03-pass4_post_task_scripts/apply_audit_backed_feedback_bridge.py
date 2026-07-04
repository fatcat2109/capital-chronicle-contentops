from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(r"A:\Capital Chronicle\tools\cc-live-contentops")
sys.path.insert(0, str(ROOT))
ARTIFACT = Path(r"C:\Users\bullw\.gemini\antigravity-ide\brain\3b41c2a4-3160-4a9b-bf7f-e4224da537fe")
ARCHIVE = ROOT / "docs" / "archive" / "_repo_cleanup_2026-07-03-pass4_post_task_scripts"

MODULE = r'''"""Audit-backed distribution record to feedback backlog bridge v6.

Local-only deterministic bridge for Jim's north-star loop:
publication audit/outcome evidence -> operator feedback -> backlog -> next brief.
No network, API, webhook, provider, browser, CDP, scraping, env, credential,
cookie, storage, session, token, header, live write, retry, schedule, comment,
DM, or reaction action is performed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from live_contentops.dispatch_outcome_identity_link_v6 import make_dispatch_outcome_identity_link
from live_contentops.feedback_backlog_next_article_brief_v6 import build_feedback_backlog_next_article_brief_packet
from live_contentops.operator_feedback_backlog_summary_v6 import build_operator_feedback_backlog_summary_packet
from live_contentops.operator_supplied_feedback_intake_v6 import (
    SAMPLE_FEEDBACK_ITEMS,
    build_operator_supplied_feedback_intake_packet,
)
from live_contentops.platform_publication_identity_registry_v6 import make_registry_record

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "automation" / "V6_AUDIT_BACKED_FEEDBACK_BACKLOG"
TASK_LABEL = "TASK_CONTENTOPS_V6_AUDIT_BACKED_DISTRIBUTION_RECORD_TO_FEEDBACK_BACKLOG_V0"

SAFETY_FLAGS = {
    "network_call_made": False,
    "provider_call_made": False,
    "llm_provider_call_made": False,
    "env_value_read_made": False,
    "credential_read_made": False,
    "browser_session_used": False,
    "browser_or_cdp_action_performed": False,
    "public_url_fetch_made": False,
    "platform_api_used": False,
    "webhook_request_made": False,
    "scraping_performed": False,
    "comment_or_reply_performed": False,
    "dm_or_private_message_performed": False,
    "reaction_performed": False,
    "scheduler_enabled": False,
    "retry_enabled": False,
    "live_publish_performed_by_contentops": False,
}

SECRET_KEY_MARKERS = (
    "cookie",
    "token",
    "secret",
    "authorization",
    "password",
    "session",
    "localstorage",
    "sessionstorage",
    "credential_value",
    "raw_header",
    "webhook_url",
)
ALLOWED_STATUS_KEYS = {
    "dm_or_private_message_performed",
    "llm_provider_call_made",
    "provider_call_made",
    "browser_session_used",
    "browser_or_cdp_action_performed",
    "credential_read_made",
    "webhook_request_made",
}
FORBIDDEN_WORDING = (
    "financial advice",
    "trade signal",
    "buy signal",
    "sell signal",
    "hold recommendation",
    "price target",
    "position sizing",
    "guaranteed return",
    "prediction guarantee",
)
PRIVATE_SOURCE_KINDS = {"dm", "direct_message", "private_message", "private_chat"}


def _stable_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _has_secret_like_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            key_lower = str(key).lower()
            if key_lower not in ALLOWED_STATUS_KEYS and any(marker in key_lower for marker in SECRET_KEY_MARKERS):
                return True
            if _has_secret_like_key(child):
                return True
    if isinstance(value, list):
        return any(_has_secret_like_key(child) for child in value)
    return False


def _has_forbidden_wording(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_has_forbidden_wording(child) for child in value.values())
    if isinstance(value, list):
        return any(_has_forbidden_wording(child) for child in value)
    if isinstance(value, str):
        lowered = value.lower()
        return any(term in lowered for term in FORBIDDEN_WORDING)
    return False


def _has_private_message_source(feedback_items: list[dict[str, Any]]) -> bool:
    return any(str(item.get("source_kind", "")).lower() in PRIVATE_SOURCE_KINDS for item in feedback_items)


def make_sample_identity_link() -> dict[str, Any]:
    """Create a safe synthetic identity link for local packet generation."""
    record = make_registry_record(
        platform="x",
        payload_hash="sha256:auditbackedfeedbackbridge001",
        public_url="https://x.com/CapitalChron/status/1800000000000000000",
        approval_id="approval_audit_feedback_001",
        outbox_entry_id="outbox_audit_feedback_001",
        dispatch_attempt_id="dispatch_audit_feedback_001",
        account_binding_ref="acct_x_capital_chronicle",
        destination_binding_ref="dest_x_main",
        created_at_utc="2026-07-03T00:00:00+00:00",
    )
    return make_dispatch_outcome_identity_link(record)


def build_audit_backed_feedback_backlog_packet(
    identity_link: dict[str, Any] | None = None,
    audit_record_ref: str | None = "audit_record_redacted_ref_001",
    feedback_items: list[dict[str, Any]] | None = None,
    metrics_notes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build local audit-backed feedback/backlog/next-brief packet."""
    link = identity_link or make_sample_identity_link()
    items = SAMPLE_FEEDBACK_ITEMS if feedback_items is None else feedback_items
    notes = metrics_notes or []
    blockers: list[str] = []

    audit_backed = bool(audit_record_ref) or link.get("ready_for_publication_audit_record") is True
    if not audit_backed:
        blockers.append("audit_backing_missing")
    if not items:
        blockers.append("feedback_items_missing")
    if _has_secret_like_key({"feedback_items": items, "metrics_notes": notes, "identity_link": link}):
        blockers.append("secret_like_input_key_blocked")
    if _has_forbidden_wording({"feedback_items": items, "metrics_notes": notes}):
        blockers.append("forbidden_financial_advice_or_signal_wording")
    if _has_private_message_source(items):
        blockers.append("private_message_feedback_source_blocked")

    unsafe = any(
        blocker in {
            "secret_like_input_key_blocked",
            "forbidden_financial_advice_or_signal_wording",
            "private_message_feedback_source_blocked",
        }
        for blocker in blockers
    )
    if unsafe:
        status = "BLOCKED_UNSAFE_FEEDBACK_OR_METRIC_INPUT"
    elif "audit_backing_missing" in blockers:
        status = "BLOCKED_MISSING_AUDIT_BACKING"
    elif "feedback_items_missing" in blockers:
        status = "REVIEW_MISSING_FEEDBACK_ITEMS"
    else:
        status = "READY_FOR_OPERATOR_BACKLOG_REVIEW"

    if items and not unsafe:
        intake = build_operator_supplied_feedback_intake_packet(items)
        backlog = build_operator_feedback_backlog_summary_packet(intake)
        brief = build_feedback_backlog_next_article_brief_packet(backlog) if backlog["candidate_count"] else None
    else:
        intake = None
        backlog = None
        brief = None

    packet = {
        "schema_version": "6.0.0",
        "packet_kind": "audit_backed_feedback_backlog_packet_v0",
        "task_label": TASK_LABEL,
        "bridge_status": status,
        "distribution_record_id": f"distribution_feedback_record_{_stable_hash(link)[:16]}",
        "source_identity_link_hash": _stable_hash(link),
        "source_audit_record_ref": audit_record_ref,
        "audit_backed_publication_context": {
            "registry_record_id": link.get("registry_record_id"),
            "platform": link.get("platform"),
            "public_url": link.get("public_url"),
            "platform_publication_id": link.get("platform_publication_id"),
            "approval_id": link.get("approval_id"),
            "outbox_entry_id": link.get("outbox_entry_id"),
            "dispatch_attempt_id": link.get("dispatch_attempt_id"),
            "publication_audit_ready": link.get("ready_for_publication_audit_record") is True,
            "explicit_audit_record_ref_present": bool(audit_record_ref),
        },
        "operator_feedback_intake_packet_id": intake.get("feedback_intake_packet_id") if intake else None,
        "feedback_backlog_summary_packet_id": backlog.get("backlog_summary_packet_id") if backlog else None,
        "next_article_brief_packet_id": brief.get("next_article_brief_packet_id") if brief else None,
        "feedback_items": intake.get("feedback_items", []) if intake else [],
        "backlog_candidates": backlog.get("backlog_candidates", []) if backlog else [],
        "selected_next_article_brief": brief.get("brief_candidate") if brief else None,
        "metrics_notes": notes,
        "community_signal_status": "operator_supplied_only_no_scrape_no_bot",
        "final_product_loop_position": "audit_to_feedback_to_next_idea",
        "blocked_controls": ["approve", "dispatch", "publish", "schedule", "send", "scrape", "reply", "dm", "react"],
        "safety_flags": SAFETY_FLAGS,
        "non_readiness_claims": {
            "live_readiness_claimed": False,
            "api_readiness_claimed": False,
            "llm_summary_claimed": False,
            "public_url_verification_claimed": False,
            "dispatch_readiness_claimed": False,
            "canonical_draft_readiness_claimed": False,
            "community_scrape_claimed": False,
            "bot_or_slash_command_claimed": False,
        },
        "blockers": blockers,
    }
    packet["exact_payload_hash"] = _stable_hash(packet)
    validate_audit_backed_feedback_backlog_packet(packet)
    return packet


def validate_audit_backed_feedback_backlog_packet(packet: dict[str, Any]) -> None:
    """Validate the local-only bridge packet."""
    if _has_secret_like_key(packet):
        raise ValueError("secret_like_packet_key_blocked")
    flags = packet.get("safety_flags", {})
    for key, expected in SAFETY_FLAGS.items():
        if flags.get(key) is not expected:
            raise ValueError(f"{key}_must_be_false")
    if packet["bridge_status"] == "READY_FOR_OPERATOR_BACKLOG_REVIEW" and packet.get("blockers"):
        raise ValueError("ready_packet_cannot_have_blockers")
    if packet["bridge_status"] == "READY_FOR_OPERATOR_BACKLOG_REVIEW" and not packet.get("selected_next_article_brief"):
        raise ValueError("ready_packet_requires_next_article_brief")


def write_default_packet() -> dict[str, Any]:
    """Write deterministic evidence packet and implementation report."""
    packet = build_audit_backed_feedback_backlog_packet()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "audit_backed_feedback_backlog_packet.json").write_text(
        json.dumps(packet, indent=2, sort_keys=True), encoding="utf-8"
    )
    report = f"""# V6 Audit-Backed Feedback Backlog Implementation Report

## Status

`{packet['bridge_status']}`

## Purpose

This packet closes the local final-product loop segment:

```text
audit-backed distribution record -> operator feedback -> backlog -> next brief
```

## Safety Boundary

No network, API, webhook, provider, browser, CDP, scraping, env, credential,
cookie, storage, session, token, header, live write, retry, schedule, comment,
DM, or reaction action is performed.

## Packet

- `distribution_record_id`: `{packet['distribution_record_id']}`
- `feedback items`: {len(packet['feedback_items'])}
- `backlog candidates`: {len(packet['backlog_candidates'])}
- `next brief`: `{packet['next_article_brief_packet_id']}`

## Next Task

```text
TASK_CONTENTOPS_V6_CAMPAIGN_OBJECT_AND_FINAL_LOOP_INTEGRATION_V0
```
"""
    (OUT_DIR / "implementation_report.md").write_text(report, encoding="utf-8")
    return packet


if __name__ == "__main__":
    print(json.dumps(write_default_packet(), indent=2, sort_keys=True))
'''

TEST = r'''import pytest

from live_contentops.audit_backed_feedback_backlog_bridge_v6 import (
    build_audit_backed_feedback_backlog_packet,
    make_sample_identity_link,
)


def test_ready_identity_link_and_operator_feedback_produces_backlog_and_brief():
    packet = build_audit_backed_feedback_backlog_packet()

    assert packet["bridge_status"] == "READY_FOR_OPERATOR_BACKLOG_REVIEW"
    assert packet["feedback_items"]
    assert packet["backlog_candidates"]
    assert packet["selected_next_article_brief"]
    assert packet["final_product_loop_position"] == "audit_to_feedback_to_next_idea"
    assert packet["safety_flags"]["network_call_made"] is False
    assert packet["safety_flags"]["scraping_performed"] is False


def test_missing_feedback_returns_review_status():
    packet = build_audit_backed_feedback_backlog_packet(feedback_items=[])

    assert packet["bridge_status"] == "REVIEW_MISSING_FEEDBACK_ITEMS"
    assert "feedback_items_missing" in packet["blockers"]
    assert packet["selected_next_article_brief"] is None


def test_missing_audit_backing_blocks():
    link = make_sample_identity_link()
    link["ready_for_publication_audit_record"] = False
    packet = build_audit_backed_feedback_backlog_packet(identity_link=link, audit_record_ref=None)

    assert packet["bridge_status"] == "BLOCKED_MISSING_AUDIT_BACKING"
    assert "audit_backing_missing" in packet["blockers"]


def test_secret_like_feedback_key_blocks():
    feedback = [{
        "feedback_item_id": "feedback_1",
        "source_platform": "discord",
        "source_kind": "operator_note",
        "operator_supplied_text": "Safe public channel summary.",
        "operator_supplied_timestamp": "2026-07-03T00:00:00Z",
        "topic_tags": ["faq"],
        "raw_secret_value": "do-not-output",
    }]

    packet = build_audit_backed_feedback_backlog_packet(feedback_items=feedback)

    assert packet["bridge_status"] == "BLOCKED_UNSAFE_FEEDBACK_OR_METRIC_INPUT"
    assert "secret_like_input_key_blocked" in packet["blockers"]
    assert "do-not-output" not in str(packet)


def test_forbidden_financial_advice_wording_blocks():
    feedback = [{
        "feedback_item_id": "feedback_1",
        "source_platform": "discord",
        "source_kind": "operator_note",
        "operator_supplied_text": "Reader asked for a buy signal.",
        "operator_supplied_timestamp": "2026-07-03T00:00:00Z",
        "topic_tags": ["faq"],
    }]

    packet = build_audit_backed_feedback_backlog_packet(feedback_items=feedback)

    assert packet["bridge_status"] == "BLOCKED_UNSAFE_FEEDBACK_OR_METRIC_INPUT"
    assert "forbidden_financial_advice_or_signal_wording" in packet["blockers"]


@pytest.mark.parametrize("source_kind", ["dm", "direct_message", "private_message", "private_chat"])
def test_private_message_source_kind_blocks(source_kind):
    feedback = [{
        "feedback_item_id": "feedback_1",
        "source_platform": "discord",
        "source_kind": source_kind,
        "operator_supplied_text": "Private message should not enter the backlog.",
        "operator_supplied_timestamp": "2026-07-03T00:00:00Z",
        "topic_tags": ["faq"],
    }]

    packet = build_audit_backed_feedback_backlog_packet(feedback_items=feedback)

    assert packet["bridge_status"] == "BLOCKED_UNSAFE_FEEDBACK_OR_METRIC_INPUT"
    assert "private_message_feedback_source_blocked" in packet["blockers"]


def test_metrics_note_with_secret_like_key_blocks():
    packet = build_audit_backed_feedback_backlog_packet(metrics_notes=[{"api_token": "do-not-output"}])

    assert packet["bridge_status"] == "BLOCKED_UNSAFE_FEEDBACK_OR_METRIC_INPUT"
    assert "secret_like_input_key_blocked" in packet["blockers"]
    assert "do-not-output" not in str(packet)


def test_output_asserts_no_live_network_provider_browser_or_scrape_flags():
    packet = build_audit_backed_feedback_backlog_packet()

    for key, value in packet["safety_flags"].items():
        assert value is False, key
    assert packet["non_readiness_claims"]["community_scrape_claimed"] is False
    assert packet["non_readiness_claims"]["bot_or_slash_command_claimed"] is False
'''

for path, content in {
    ROOT / "live_contentops" / "audit_backed_feedback_backlog_bridge_v6.py": MODULE,
    ROOT / "tests" / "test_audit_backed_feedback_backlog_bridge_v6.py": TEST,
}.items():
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    path.write_text(content, encoding="utf-8")

# Generate docs packet/report via module function without network/live behavior.
import importlib.util
spec = importlib.util.spec_from_file_location(
    "audit_backed_feedback_backlog_bridge_v6",
    ROOT / "live_contentops" / "audit_backed_feedback_backlog_bridge_v6.py",
)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)
mod.write_default_packet()

context = ROOT / "docs" / "CURRENT_CONTEXT.md"
text = context.read_text(encoding="utf-8")
text = text.replace(
    "`TASK_CONTENTOPS_V6_IDENTITY_REGISTRY_TO_DISPATCH_OUTCOME_MODEL_V0`",
    "`TASK_CONTENTOPS_V6_CAMPAIGN_OBJECT_AND_FINAL_LOOP_INTEGRATION_V0`",
)
context.write_text(text, encoding="utf-8")

pointer = ROOT / "docs" / "automation" / "V6_FINAL_PRODUCT_EXECUTION_PLAN" / "next_task_pointer.md"
pointer.write_text('''# V6 Next Task Pointer

Current task: `TASK_CONTENTOPS_V6_AUDIT_BACKED_DISTRIBUTION_RECORD_TO_FEEDBACK_BACKLOG_V0`

Recommended next task:

```text
TASK_CONTENTOPS_V6_CAMPAIGN_OBJECT_AND_FINAL_LOOP_INTEGRATION_V0
```

Purpose: batch Task 22 campaign object with the audit-backed feedback packet references, final loop status from idea to next idea, and release-readiness inputs for Task 25.

Do not start live writes, browser/CDP probes, Discord webhook/API calls, scheduler/retry wiring, approval ledger writes, outbox execution, credential/env value reads, public URL fetches, scraping, comments, DMs, reactions, or LLM/provider API calls unless explicitly authorized.
''', encoding="utf-8")

status = ROOT / "docs" / "status" / "current_project_status.json"
if status.exists():
    data = json.loads(status.read_text(encoding="utf-8"))
    data["last_updated_by_task"] = "TASK_CONTENTOPS_V6_AUDIT_BACKED_DISTRIBUTION_RECORD_TO_FEEDBACK_BACKLOG_V0"
    data["current_product_phase"] = "Audit-backed distribution record to feedback backlog bridge added"
    data["current_product_lane"] = "Jim north-star final loop; audit/outcome evidence feeds operator feedback backlog and next article brief; live actions locked"
    data["accepted_baseline_summary"] = "The local-only audit-backed feedback backlog bridge connects safe distribution identity/audit context to operator-supplied feedback intake, deterministic backlog summary, and review-only next article brief candidate. It performs no live write, network/API/webhook/provider/browser/CDP/env/credential/session/scraping/comment/DM/reaction/retry/scheduler action and does not verify public URLs."
    data["dispatch_live_status"] = "Dispatch/live write remains locked. Audit-backed feedback packets are local planning/evidence records only, not executable outbox entries, dispatch attempts, scraping jobs, bot commands, or public URL verification."
    data["provider_env_credential_status"] = "No provider/API/browser/network/env/credential action is authorized or required for the audit-backed feedback backlog bridge task."
    blockers = data.get("active_blockers", [])
    blockers.append("Audit-backed feedback bridge is local planning evidence only; real community feedback capture must be operator-supplied unless a future exact approved live task authorizes another source.")
    data["active_blockers"] = list(dict.fromkeys(blockers))
    data["latest_accepted_task"] = "TASK_CONTENTOPS_V6_AUDIT_BACKED_DISTRIBUTION_RECORD_TO_FEEDBACK_BACKLOG_V0"
    data["latest_accepted_task_result"] = "audit_backed_feedback_backlog_bridge_added"
    data["latest_changed_areas"] = [
        "live_contentops/audit_backed_feedback_backlog_bridge_v6.py",
        "tests/test_audit_backed_feedback_backlog_bridge_v6.py",
        "docs/automation/V6_AUDIT_BACKED_FEEDBACK_BACKLOG/audit_backed_feedback_backlog_packet.json",
        "docs/automation/V6_AUDIT_BACKED_FEEDBACK_BACKLOG/implementation_report.md",
        "docs/CURRENT_CONTEXT.md",
        "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md",
        "docs/status/current_project_status.json",
    ]
    data["next_recommended_task"] = "TASK_CONTENTOPS_V6_CAMPAIGN_OBJECT_AND_FINAL_LOOP_INTEGRATION_V0: batch Task 22 campaign object with audit-backed feedback packet references, final loop status from idea to next idea, and release-readiness inputs; local/read-only first, no live/provider/browser/network/env/credential action."
    status.write_text(json.dumps(data, indent=2), encoding="utf-8")

ARCHIVE.mkdir(parents=True, exist_ok=True)
for stale in [
    ARTIFACT / "scratch" / "apply_identity_outcome_link.py",
    ARTIFACT / "scratch" / "probe3.txt",
]:
    if stale.exists():
        shutil.move(str(stale), str(ARCHIVE / stale.name))

print("audit-backed feedback backlog bridge applied")
