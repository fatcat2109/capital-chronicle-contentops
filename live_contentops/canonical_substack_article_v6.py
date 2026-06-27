"""V6 Canonical Substack Article Packet Layer.

Consumes the operator intent packet and outputs a structured canonical Substack
article draft scaffold/outline without making any live or external calls.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_CANONICAL_SUBSTACK_ARTICLE_PACKET_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_INTENT_PACKET = Path("docs/automation/V6_OPERATOR_INTENT/operator_intent_packet.json")
DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_CANONICAL_SUBSTACK_ARTICLE")
DEFAULT_PACKET_OUTPUT = DEFAULT_OUTPUT_DIR / "canonical_article_packet.json"
DEFAULT_OUTLINE_OUTPUT = DEFAULT_OUTPUT_DIR / "canonical_article_outline.md"


def path_text(path: str | Path | None) -> str | None:
    if path is None:
        return None
    return str(path).replace("\\", "/")


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def generate_scaffold_markdown(packet: dict[str, Any]) -> str:
    title = packet.get("title", "Untitled Draft Outline")
    subtitle = packet.get("subtitle", "")
    source_mode = packet.get("source_mode", "unknown")
    status = packet.get("article_status", "unknown")
    
    # Block warning
    block_warning = ""
    blocked_reasons = packet.get("blocked_reasons", [])
    if blocked_reasons:
        reasons_list = "\n".join(f"- {r}" for r in blocked_reasons)
        block_warning = f"""
> [!WARNING]
> **PUBLISH BLOCK ACTIVE**: This draft scaffold is blocked due to validation errors:
{reasons_list}
"""

    return f"""# {title}
{f"## {subtitle}" if subtitle else ""}

> [!IMPORTANT]
> **DRAFT SCAFFOLD ONLY**: This document is a safe pre-production outline. It is not publish-ready and must not be posted publicly.
{block_warning}

## Editor & Source Limitation Note
- **Source Mode**: {source_mode}
- **Status**: {status}
- **Verification Requirement**: This article is generated under `operator_idea_only` mode. Real-world verification and source evidence are required before any public post can be created.

## 1. Thesis Placeholder
[Enter canonical Substack article core thesis here.]

## 2. Why It Matters
- Relevance to the Capital Chronicle readership.
- Impact on the AI-native editorial workflows and publishing industry.

## 3. Architecture & Product Context
- Underpinning technologies in V6 ContentOps pipeline.
- Local-only execution validation and safety gates.

## 4. Evidence Needed Before Publish
- Verification of any numeric metrics, performance latency improvements, or client-side telemetry.
- Confirmed files or links inside `source_refs`.

## 5. Risk & Compliance Notes
- **Strict Compliance**: No financial advice, buy/sell/hold calls, entry/exit levels, or conviction trade positioning.
- **Risk Disclaimers**: Outline is purely informational and institutional.

## 6. Next Operator Review Checklist
- [ ] Confirm thesis statement with Jim.
- [ ] Bind exact payload hash to destination channel.
- [ ] Conduct final security scan review.
"""


def materialize_article_packet(
    intent_packet_path: str | Path = DEFAULT_INTENT_PACKET
) -> dict[str, Any]:
    try:
        intent_data = load_json(intent_packet_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        # Fallback if intent is unreadable
        return {
            "task_label": TASK_LABEL,
            "schema_version": SCHEMA_VERSION,
            "article_id": "substack_article_unreadable",
            "source_intent_id": None,
            "source_intent_class": None,
            "source_mode": "unknown",
            "article_status": "BLOCKED_BY_OPERATOR_INTENT",
            "title": "Blocked Draft Outline",
            "subtitle": "Capital Chronicle Editorial Scaffold",
            "canonical_channel": "substack",
            "article_stage": "outline_scaffold",
            "sections": [],
            "claims_register": [],
            "source_refs": [],
            "source_needed": True,
            "source_evidence_required": True,
            "public_postable": False,
            "human_review_required": True,
            "approval_required": True,
            "approval_performed": False,
            "dispatch_requested_from_intent": False,
            "dispatch_allowed_now": False,
            "not_approved": True,
            "not_dispatchable": True,
            "not_public_postable": True,
            "no_live_request_in_this_task": True,
            "no_env_read_in_this_task": True,
            "no_provider_call_in_this_task": True,
            "raw_secret_output": False,
            "webhook_url_printed": False,
            "blocked_reasons": [f"operator_intent_unreadable:{exc.__class__.__name__}"],
            "next_recommended_task": "TASK_CONTENTOPS_V6_OPERATOR_INTENT_AND_CONTENT_IDEA_PACKET_V0"
        }

    intent_id = intent_data.get("intent_id")
    intent_class = intent_data.get("intent_class")
    source_mode = intent_data.get("source_mode")
    topic = intent_data.get("topic", "Untitled Topic")
    source_refs = intent_data.get("source_refs", [])
    source_needed = intent_data.get("source_needed", False)
    source_evidence_required = intent_data.get("source_evidence_required", False)
    blocked_reasons = list(intent_data.get("blocked_reasons", []))
    dispatch_requested = intent_data.get("dispatch_requested", False)
    
    # Propagate blocked status
    if blocked_reasons:
        status = "BLOCKED_BY_OPERATOR_INTENT"
    else:
        status = "OUTLINE_SCAFFOLD_READY"

    # Enforce rules: numeric/artifact claims require source evidence
    future_artifact_claim = intent_data.get("future_artifact_claim_detected", False)
    if (source_evidence_required or future_artifact_claim) and not source_refs:
        source_needed = True
        source_evidence_required = True
        if "missing_source_evidence" not in blocked_reasons:
            blocked_reasons.append("missing_source_evidence")
        status = "BLOCKED_BY_OPERATOR_INTENT"
        
    if source_mode == "operator_idea_only":
        source_needed = True  # idea only requires sourcing before finalization

    # Claims Register entries
    claims_register = []
    if source_evidence_required:
        claims_register.append({
            "claim_type": "numeric_or_artifact_claim",
            "evidence_status": "PENDING_SOURCE_REF",
            "description": "Factual claim detected in operator intent requiring verification references."
        })

    hasher = hashlib.sha256(f"{intent_id}_{status}".encode("utf-8"))
    article_id = f"substack_article_{hasher.hexdigest()[:12]}"

    next_task = (
        "TASK_CONTENTOPS_V6_CANONICAL_SUBSTACK_ARTICLE_PACKET_V0"
        if status == "BLOCKED_BY_OPERATOR_INTENT"
        else "TASK_CONTENTOPS_V6_AI_RESEARCH_GROUNDING_LANE_V0"
    )

    return {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "article_id": article_id,
        "source_intent_id": intent_id,
        "source_intent_class": intent_class,
        "source_mode": source_mode,
        "article_status": status,
        "title": f"Draft Outline: {topic}",
        "subtitle": "Capital Chronicle Editorial Scaffold",
        "canonical_channel": "substack",
        "article_stage": "outline_scaffold",
        "sections": [
            "Thesis Placeholder",
            "Why It Matters",
            "Architecture & Product Context",
            "Evidence Needed Before Publish",
            "Risk & Compliance Notes",
            "Next Operator Review Checklist"
        ],
        "claims_register": claims_register,
        "source_refs": source_refs,
        "source_needed": source_needed,
        "source_evidence_required": source_evidence_required,
        "public_postable": False,
        "human_review_required": True,
        "approval_required": True,
        "approval_performed": False,
        "dispatch_requested_from_intent": dispatch_requested,
        "dispatch_allowed_now": False,
        "not_approved": True,
        "not_dispatchable": True,
        "not_public_postable": True,
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "no_provider_call_in_this_task": True,
        "raw_secret_output": False,
        "webhook_url_printed": False,
        "blocked_reasons": sorted(blocked_reasons),
        "next_recommended_task": next_task
    }


def implementation_report(packet: dict[str, Any]) -> str:
    blocked_flag = "BLOCKED_FAIL_SAFE" if packet.get("blocked_reasons") else "PASS"
    return f"""# Discord Real Content Canonical Substack Article Workflow

Status: `{blocked_flag}`

- No live request in this task: `true`
- No env read in this task: `true`
- No provider call in this task: `true`
- Scaffold generated as outline only: `true`
- Fake public-postable content created: `false`

The canonical Substack article is generated as an unapproved outline scaffold.
"""


def next_task_pointer(packet: dict[str, Any]) -> str:
    next_task = packet.get("next_recommended_task")
    if packet.get("blocked_reasons"):
        goal = "Resolve operator intent block reasons or supply missing evidence/parameters."
    else:
        goal = "Trigger research grounding lane for canonical Substack article draft."
    return f"""# Next Task Pointer

Recommended next task:

`{next_task}`

Goal: {goal}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Canonical Substack Article Generator")
    parser.add_argument("--intent-packet", default=str(DEFAULT_INTENT_PACKET))
    parser.add_argument("--output-packet", default=str(DEFAULT_PACKET_OUTPUT))
    parser.add_argument("--output-outline", default=str(DEFAULT_OUTLINE_OUTPUT))
    args = parser.parse_args(argv)
    
    packet = materialize_article_packet(args.intent_packet)
    write_json(args.output_packet, packet)
    
    outline_text = generate_scaffold_markdown(packet)
    Path(args.output_outline).write_text(outline_text, encoding="utf-8")
    
    # Write report and pointer
    out_path = Path(args.output_packet)
    (out_path.parent / "implementation_report.md").write_text(implementation_report(packet), encoding="utf-8")
    (out_path.parent / "next_task_pointer.md").write_text(next_task_pointer(packet), encoding="utf-8")
    
    print(json.dumps({
        "article_id": packet["article_id"],
        "article_status": packet["article_status"],
        "blocked_reasons": packet["blocked_reasons"]
    }, indent=2))
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
