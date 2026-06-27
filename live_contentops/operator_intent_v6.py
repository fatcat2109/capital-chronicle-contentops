"""V6 Operator Intent + Content Idea Packet Layer.

Converts Jim/operator text into a structured intent packet. Enforces local-only
constraints, validates safety rules, and generates intent packets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_INTENT_AND_CONTENT_IDEA_PACKET_V0"
SCHEMA_VERSION = "6.0.0"

# Regexes for safety rules
TRADING_SIGNAL_RE = re.compile(r"\b(buy|sell|hold|long|short|entry|exit|take profit|stop loss)\b", re.IGNORECASE)
POSITION_SIZING_RE = re.compile(r"\b(position size|size your position|allocate(?:\s+\w+){0,3}\s+\d+%|risk\s+\d+%|portfolio weight)", re.IGNORECASE)
GUARANTEED_PREDICTION_RE = re.compile(r"\b(guaranteed|will definitely|certain to|risk[- ]free|cannot lose|sure thing)\b", re.IGNORECASE)
FINANCIAL_ADVICE_RE = re.compile(r"\b(financial advice|investment advice|not financial advice|alpha call|conviction trade)\b", re.IGNORECASE)
SECRETISH_RE = re.compile(r"https://(?:discord(?:app)?\.com)/api/webhooks/|webhooks/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+|\b(?:token|cookie|sessionid|authorization|bearer)\b", re.IGNORECASE)
NUMERIC_CLAIMS_RE = re.compile(r"\b(?<![vV])\d+(?:\.\d+)?%?\b")
PATH_RE = re.compile(r"\b(?:[a-zA-Z0-9_\-\/]+\.(?:md|txt|json))\b")


def path_text(path: str | Path | None) -> str | None:
    if path is None:
        return None
    return str(path).replace("\\", "/")


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def classify_intent_class(prompt: str) -> str:
    lower = prompt.lower()
    if "approve" in lower or "approval" in lower:
        return "approve_payload"
    if "reject" in lower or "deny" in lower or "decline" in lower:
        return "reject_payload"
    if "manual fallback" in lower or "fallback playbook" in lower:
        return "request_manual_fallback"
    if "webhook dispatch" in lower or "dispatch webhook" in lower:
        return "request_webhook_dispatch"
    if "audit summary" in lower or "audit report" in lower or "security audit" in lower:
        return "request_audit_summary"
    if "discord drop" in lower or "discord post" in lower or "discord message" in lower:
        return "create_discord_drop"
    if "product update" in lower or "release update" in lower or "feature update" in lower:
        return "create_product_update"
    if "platform variants" in lower or "variant generator" in lower or "cross-platform" in lower:
        return "create_platform_variants"
    if "research question" in lower or "backlog" in lower or "research topic" in lower:
        return "create_research_question_backlog"
    if "inspect draft" in lower or "check draft" in lower or "review draft" in lower:
        return "inspect_draft"
    if "summarize" in lower or "summary" in lower or "brief" in lower:
        return "summarize_source"
    if "canonical" in lower or "article" in lower or "substack" in lower:
        return "create_canonical_article"
    
    # Defaults
    if "idea" in lower:
        return "create_canonical_article"
    return "create_canonical_article"


def extract_refs_and_mode(prompt: str) -> tuple[list[str], str]:
    refs = PATH_RE.findall(prompt)
    lower = prompt.lower()
    
    if "future internal alpha" in lower or "alpha artifact" in lower or "alpha claim" in lower:
        return refs, "future_internal_alpha_artifact"
    if refs:
        return refs, "source_artifact_path"
    if "community signal" in lower or "signal manual" in lower or "user feedback" in lower or "discord signal" in lower:
        return refs, "community_signal_manual"
    if len(prompt) > 300 or "\n" in prompt or "source text:" in lower or "content:" in lower:
        return refs, "operator_source_text"
    
    return refs, "operator_idea_only"


def classify_content_lane(prompt: str, source_mode: str, blocked: bool) -> str:
    if blocked:
        return "blocked_or_unknown"
    lower = prompt.lower()
    if source_mode == "future_internal_alpha_artifact" or "alpha" in lower or "artifact" in lower:
        return "future_artifact_backed"
    if "news" in lower or "substack" in lower or "market" in lower:
        return "grounded_news_context"
    return "pre_alpha_general_process"


def extract_topic(prompt: str) -> str:
    lines = [line.strip() for line in prompt.splitlines() if line.strip()]
    if not lines:
        return "unknown_topic"
    first = lines[0].lstrip("#* ").strip()
    return first[:80]


def extract_target_platforms(prompt: str) -> list[str]:
    platforms = []
    lower = prompt.lower()
    if "discord" in lower:
        platforms.append("discord")
    if "telegram" in lower:
        platforms.append("telegram")
    if "substack" in lower:
        platforms.append("substack")
    if not platforms:
        platforms.append("substack")  # default canonical channel
    return platforms


def extract_requested_outputs(prompt: str, intent_class: str) -> list[str]:
    outputs = []
    if "article" in intent_class or "article" in prompt.lower():
        outputs.append("article_draft")
    if "discord" in intent_class or "discord" in prompt.lower():
        outputs.append("discord_drop_draft")
    if "platform_variants" in intent_class or "variants" in prompt.lower():
        outputs.append("social_variants")
    if "backlog" in intent_class:
        outputs.append("research_backlog")
    if not outputs:
        outputs.append("intent_metadata")
    return outputs


def parse_intent(prompt: str) -> dict[str, Any]:
    prompt = prompt.strip()
    excerpt = prompt[:240]
    
    # Basic classification
    intent_class = classify_intent_class(prompt)
    source_refs, source_mode = extract_refs_and_mode(prompt)
    topic = extract_topic(prompt)
    target_platforms = extract_target_platforms(prompt)
    requested_outputs = extract_requested_outputs(prompt, intent_class)
    
    # State tracking
    no_advice_status = True
    no_signal_status = True
    approval_requested = "approve" in prompt.lower() or "approval" in prompt.lower()
    dispatch_requested = any(w in prompt.lower() for w in ["send", "post", "dispatch", "publish"])
    
    blocked_reasons: list[str] = []
    
    # Safety Check: Trading Signal
    if TRADING_SIGNAL_RE.search(prompt):
        no_signal_status = False
        blocked_reasons.append("trading_signal_language_blocked")
        
    # Safety Check: Position Sizing
    if POSITION_SIZING_RE.search(prompt):
        blocked_reasons.append("position_sizing_language_blocked")
        
    # Safety Check: Guaranteed Prediction
    if GUARANTEED_PREDICTION_RE.search(prompt):
        blocked_reasons.append("guaranteed_prediction_language_blocked")
        
    # Safety Check: Financial Advice
    if FINANCIAL_ADVICE_RE.search(prompt):
        no_advice_status = False
        blocked_reasons.append("financial_advice_language_blocked")
        
    # Safety Check: Secrets / Webhook Urls
    if SECRETISH_RE.search(prompt):
        blocked_reasons.append("secrets_or_webhook_url_blocked")
        
    # Numeric Claims & Evidence
    numeric_claim_found = False
    for val in NUMERIC_CLAIMS_RE.findall(prompt):
        # filter out simple v6 or vX versions
        if not re.search(r'\b[vV]\d+\b', val):
            numeric_claim_found = True
            break
            
    source_evidence_required = False
    source_needed = False
    if numeric_claim_found:
        if not source_refs:
            source_evidence_required = True
            source_needed = True
            blocked_reasons.append("numeric_claim_requires_source_evidence")
            
    # Future Artifact check
    future_artifact_claim_detected = source_mode == "future_internal_alpha_artifact"
    if future_artifact_claim_detected and not source_refs:
        blocked_reasons.append("missing_future_alpha_artifact_path")
        
    # Approval Logic
    approval_valid_for_dispatch = False
    if approval_requested:
        # Check for exact payload hash (hex string of 12-64 chars)
        payload_hash_match = re.search(r"\b([0-9a-fA-F]{12,64})\b", prompt)
        # Check for destination binding
        destination_match = re.search(
            r"\b(discord_webhook_destination|discord_announcements|discord_substack_drops|discord_product_updates|telegram_channel|telegram_operator_chat_id|discord|telegram|substack)\b",
            prompt, re.I
        )
        if not payload_hash_match:
            blocked_reasons.append("missing_payload_hash_for_approval")
        if not destination_match:
            blocked_reasons.append("missing_destination_binding_for_approval")
            
        if payload_hash_match and destination_match:
            # Must check if there are any other block reasons
            if not any(r in blocked_reasons for r in [
                "trading_signal_language_blocked", "position_sizing_language_blocked",
                "guaranteed_prediction_language_blocked", "financial_advice_language_blocked",
                "secrets_or_webhook_url_blocked"
            ]):
                approval_valid_for_dispatch = True
            else:
                blocked_reasons.append("approval_blocked_by_safety_violations")
                
    # Dispatch check
    if dispatch_requested:
        blocked_reasons.append("dispatch_not_allowed_in_this_task")
        
    content_lane = classify_content_lane(prompt, source_mode, len(blocked_reasons) > 0)
    
    # Deterministic intent ID
    hasher = hashlib.sha256(prompt.encode("utf-8"))
    intent_id = f"discord_operator_intent_{hasher.hexdigest()[:12]}"
    
    return {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "intent_id": intent_id,
        "raw_prompt_excerpt": excerpt,
        "source_mode": source_mode,
        "intent_class": intent_class,
        "content_lane": content_lane,
        "topic": topic,
        "target_platforms_requested": target_platforms,
        "requested_outputs": requested_outputs,
        "source_refs": source_refs,
        "source_needed": source_needed,
        "source_evidence_required": source_evidence_required,
        "future_artifact_claim_detected": future_artifact_claim_detected,
        "no_advice_status": no_advice_status,
        "no_signal_status": no_signal_status,
        "approval_requested": approval_requested,
        "approval_valid_for_dispatch": approval_valid_for_dispatch,
        "dispatch_requested": dispatch_requested,
        "dispatch_allowed_now": False,
        "blocked_reasons": sorted(list(set(blocked_reasons))),
        "human_review_required": True,
        "not_public_postable": True,
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "raw_secret_output": False,
        "webhook_url_printed": False,
    }


def get_sample_prompts() -> list[str]:
    return [
        "Draft a canonical article about Capital Chronicle V6 AI-native editorial workflows.",
        "We achieved 50% database latency reduction with the new indexing strategy. Summarize this findings file: docs/indexing_perf.md",
        "We achieved 50% database latency reduction. Write a Discord announcements post.",
        "Please approve payload abc123def456 for discord_webhook_destination",
        "approve this draft payload",
        "publish/send this payload to Discord channels announcements immediately",
        "We have a future internal alpha artifact containing our roadmap. Please inspect it.",
        "We have a future internal alpha artifact docs/alpha_roadmap.md containing our roadmap. Summarize it.",
        "Should we buy this conviction trade? Position sizing is 10%.",
        "Guaranteed wins with this strategy! Risk-free returns are certain."
    ]


def implementation_report(packet: dict[str, Any]) -> str:
    blocked_flag = "BLOCKED_FAIL_SAFE" if packet.get("blocked_reasons") else "PASS"
    return f"""# V6 Operator Intent + Content Idea Packet Layer

Status: `{blocked_flag}`

- No live request in this task: `true`
- No env read in this task: `true`
- Fake public-postable content created: `false`
- Auto-approval performed: `false`
- Auto-dispatch performed: `false`

Operator intent is validated and safely parsed in a sandbox structure.
"""


def next_task_pointer(packet: dict[str, Any]) -> str:
    if packet.get("blocked_reasons"):
        goal = "Resolve operator intent block reasons or supply missing evidence/parameters."
    else:
        goal = "Generate canonical Substack article from valid operator intent packet."
    return f"""# Next Task Pointer

Recommended next task:

`TASK_CONTENTOPS_V6_CANONICAL_SUBSTACK_ARTICLE_V0`

Goal: {goal}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Operator Intent Parser")
    parser.add_argument("--prompt", default="Draft a canonical article about Capital Chronicle V6 AI-native editorial workflows.")
    parser.add_argument("--output", default="docs/automation/V6_OPERATOR_INTENT/operator_intent_packet.json")
    parser.add_argument("--samples-output", default="docs/automation/V6_OPERATOR_INTENT/sample_operator_intents.json")
    args = parser.parse_args(argv)
    
    packet = parse_intent(args.prompt)
    write_json(args.output, packet)
    
    # Write samples
    samples = []
    for pr in get_sample_prompts():
        samples.append(parse_intent(pr))
    write_json(args.samples_output, samples)
    
    # Write docs
    out_path = Path(args.output)
    (out_path.parent / "implementation_report.md").write_text(implementation_report(packet), encoding="utf-8")
    (out_path.parent / "next_task_pointer.md").write_text(next_task_pointer(packet), encoding="utf-8")
    
    print(json.dumps({
        "intent_id": packet["intent_id"],
        "intent_class": packet["intent_class"],
        "blocked_reasons": packet["blocked_reasons"],
        "dispatch_allowed_now": packet["dispatch_allowed_now"]
    }, indent=2))
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
