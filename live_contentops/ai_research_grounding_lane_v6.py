"""V6 AI Research Grounding Lane Packet Layer.

Consumes the canonical article packet and generates evidence requirements,
research questions, and grounding status in a local-only fashion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_AI_RESEARCH_GROUNDING_LANE_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_ARTICLE_PACKET = Path("docs/automation/V6_CANONICAL_SUBSTACK_ARTICLE/canonical_article_packet.json")
DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_AI_RESEARCH_GROUNDING")
DEFAULT_PACKET_OUTPUT = DEFAULT_OUTPUT_DIR / "research_grounding_packet.json"
DEFAULT_BACKLOG_OUTPUT = DEFAULT_OUTPUT_DIR / "research_question_backlog.md"
DEFAULT_EVIDENCE_OUTPUT = DEFAULT_OUTPUT_DIR / "evidence_requirements.md"


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


def generate_research_questions(sections: list[str]) -> list[dict[str, str]]:
    questions = []
    section_mapping = {
        "Thesis Placeholder": "What is the validated core thesis statement from the operator?",
        "Why It Matters": "What are the specific readership metrics and workflow efficiencies achieved?",
        "Architecture & Product Context": "What are the local-only safety boundaries and preflight checks in the V6 ContentOps codebase?",
        "Evidence Needed Before Publish": "Where are the file/log verification source references located?",
        "Risk & Compliance Notes": "Does the text fully comply with the absolute ban on financial advice, signal framing, and position sizing?",
        "Next Operator Review Checklist": "Has the operator verified the final payload hash against the destination binding?"
    }
    for sec in sections:
        q = section_mapping.get(sec, f"What specific evidence is needed to verify the section '{sec}'?")
        questions.append({
            "section": sec,
            "question": q
        })
    # If no sections, supply default questions
    if not questions:
        questions.append({
            "section": "General",
            "question": "What is the verified editorial objective of this canonical post?"
        })
    return questions


def generate_backlog_markdown(packet: dict[str, Any], title: str) -> str:
    status = packet.get("grounding_status", "unknown")
    source_mode = packet.get("source_mode", "unknown")
    questions = packet.get("research_questions", [])
    
    questions_str = ""
    for q in questions:
        questions_str += f"### {q.get('section')}\n- {q.get('question')}\n\n"
        
    return f"""# Research Question Backlog: {title}

> [!IMPORTANT]
> **DRAFT RESEARCH BACKLOG**: This document lists required research queries and evidence slots. It is not publish-ready and does not contain postable content.

## Grounding Status
- **Status**: {status}
- **Source Mode**: {source_mode}
- **Source Limitation Note**: Generated under `{source_mode}` mode. Factual verification is required before drafting.

## Research Questions by Section
{questions_str}
## Next Operator Review Checklist
- [ ] Answer all research questions listed above.
- [ ] Compile evidence requirements mapping to all claims.
- [ ] Provide explicit paths for any internal alpha artifacts.
"""


def generate_evidence_markdown(packet: dict[str, Any]) -> str:
    required_source_refs = packet.get("required_source_refs", [])
    missing_source_refs = packet.get("missing_source_refs", [])
    
    req_refs_str = "\n".join(f"- `{r}`" for r in required_source_refs) or "- None"
    miss_refs_str = "\n".join(f"- `{r}`" for r in missing_source_refs) or "- None"
    
    return f"""# Evidence Requirements Register

> [!IMPORTANT]
> **NO-PUBLICATION WARNING**: This document outlines verification evidence rules. It is not publish-ready.

## Factual Verification Rules
1. **Factual Claims**: Require verified external source references.
2. **Internal Alpha Claims**: Must map to valid local files or build artifact paths.
3. **UI/Product Claims**: Require screenshots or file layout references.
4. **Implementation Claims**: Must map to local test suites or logs.
5. **Safety Exclusions**: Absolute ban on financial advice, buy/sell/hold signal framing, price targets, guaranteed predictions, and position sizing.

## Required Source References
{req_refs_str}

## Missing Source References
{miss_refs_str}

## Unsupported Factual Claims Handling
- Any claims flagged as unsupported will cause the validation to block.
- Operators must provide verified evidence paths or remove unsupported metrics from final text.
"""


def materialize_grounding_packet(
    article_packet_path: str | Path = DEFAULT_ARTICLE_PACKET
) -> dict[str, Any]:
    try:
        article_data = load_json(article_packet_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        return {
            "task_label": TASK_LABEL,
            "schema_version": SCHEMA_VERSION,
            "research_packet_id": "substack_research_unreadable",
            "source_article_id": None,
            "source_intent_id": None,
            "source_article_status": None,
            "source_mode": "unknown",
            "grounding_status": "BLOCKED_BY_SOURCE_ARTICLE",
            "canonical_channel": "substack",
            "research_stage": "grounding_backlog",
            "research_questions": [],
            "evidence_requirements": [],
            "required_source_refs": [],
            "missing_source_refs": [],
            "claims_to_verify": [],
            "unsupported_claims_detected": True,
            "source_needed": True,
            "source_evidence_required": True,
            "public_postable": False,
            "human_review_required": True,
            "approval_required": True,
            "approval_performed": False,
            "dispatch_allowed_now": False,
            "not_approved": True,
            "not_dispatchable": True,
            "not_public_postable": True,
            "no_live_request_in_this_task": True,
            "no_env_read_in_this_task": True,
            "no_provider_call_in_this_task": True,
            "no_network_call_in_this_task": True,
            "raw_secret_output": False,
            "webhook_url_printed": False,
            "blocked_reasons": [f"canonical_article_unreadable:{exc.__class__.__name__}"],
            "next_recommended_task": "TASK_CONTENTOPS_V6_CANONICAL_SUBSTACK_ARTICLE_PACKET_V0"
        }

    article_id = article_data.get("article_id")
    intent_id = article_data.get("source_intent_id")
    article_status = article_data.get("article_status")
    source_mode = article_data.get("source_mode")
    sections = article_data.get("sections", [])
    source_refs = article_data.get("source_refs", [])
    source_needed = article_data.get("source_needed", False)
    source_evidence_required = article_data.get("source_evidence_required", False)
    blocked_reasons = list(article_data.get("blocked_reasons", []))

    if article_status == "BLOCKED_BY_OPERATOR_INTENT" or blocked_reasons:
        status = "BLOCKED_BY_SOURCE_ARTICLE"
    else:
        status = "RESEARCH_BACKLOG_READY"

    required_source_refs = list(source_refs)
    missing_source_refs = []
    
    if source_mode == "operator_idea_only" and not source_refs:
        source_needed = True
        missing_source_refs.append("operator_idea_source_ref")
        
    claims_to_verify = list(article_data.get("claims_register", []))
    unsupported_claims_detected = bool(source_evidence_required and not source_refs)
    if unsupported_claims_detected:
        status = "BLOCKED_BY_SOURCE_ARTICLE"
        if "missing_source_evidence" not in blocked_reasons:
            blocked_reasons.append("missing_source_evidence")

    # Generate questions from sections
    questions = generate_research_questions(sections)

    evidence_reqs = [
        "source refs for factual claims",
        "artifact paths for internal alpha claims",
        "screenshot or file evidence for UI/product claims",
        "test/log evidence for implementation claims",
        "citation/source evidence for external factual/news claims",
        "explicit exclusion of market advice/signals"
    ]

    hasher = hashlib.sha256(f"{article_id}_{status}".encode("utf-8"))
    research_packet_id = f"substack_research_{hasher.hexdigest()[:12]}"

    next_task = (
        "TASK_CONTENTOPS_V6_AI_RESEARCH_GROUNDING_LANE_V0"
        if status == "BLOCKED_BY_SOURCE_ARTICLE"
        else "TASK_CONTENTOPS_V6_SEO_AND_EDITORIAL_REFINEMENT_LANE_V0"
    )

    return {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "research_packet_id": research_packet_id,
        "source_article_id": article_id,
        "source_intent_id": intent_id,
        "source_article_status": article_status,
        "source_mode": source_mode,
        "grounding_status": status,
        "canonical_channel": "substack",
        "research_stage": "grounding_backlog",
        "research_questions": questions,
        "evidence_requirements": evidence_reqs,
        "required_source_refs": required_source_refs,
        "missing_source_refs": missing_source_refs,
        "claims_to_verify": claims_to_verify,
        "unsupported_claims_detected": unsupported_claims_detected,
        "source_needed": source_needed,
        "source_evidence_required": source_evidence_required,
        "public_postable": False,
        "human_review_required": True,
        "approval_required": True,
        "approval_performed": False,
        "dispatch_allowed_now": False,
        "not_approved": True,
        "not_dispatchable": True,
        "not_public_postable": True,
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "no_provider_call_in_this_task": True,
        "no_network_call_in_this_task": True,
        "raw_secret_output": False,
        "webhook_url_printed": False,
        "blocked_reasons": sorted(blocked_reasons),
        "next_recommended_task": next_task
    }


def implementation_report(packet: dict[str, Any]) -> str:
    blocked_flag = "BLOCKED_FAIL_SAFE" if packet.get("blocked_reasons") else "PASS"
    return f"""# V6 AI Research Grounding Lane

Status: `{blocked_flag}`

- No live request in this task: `true`
- No env read in this task: `true`
- No provider call in this task: `true`
- No network call in this task: `true`
- Verification slots mapped as backlog: `true`
- Fake public-postable content created: `false`

The research grounding questions and evidence requirements are cataloged.
"""


def next_task_pointer(packet: dict[str, Any]) -> str:
    next_task = packet.get("next_recommended_task")
    if packet.get("blocked_reasons"):
        goal = "Resolve operator intent or source evidence blocking conditions."
    else:
        goal = "Trigger SEO and editorial refinement lane for canonical Substack post."
    return f"""# Next Task Pointer

Recommended next task:

`{next_task}`

Goal: {goal}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 AI Research Grounding Lane")
    parser.add_argument("--article-packet", default=str(DEFAULT_ARTICLE_PACKET))
    parser.add_argument("--output-packet", default=str(DEFAULT_PACKET_OUTPUT))
    parser.add_argument("--output-backlog", default=str(DEFAULT_BACKLOG_OUTPUT))
    parser.add_argument("--output-evidence", default=str(DEFAULT_EVIDENCE_OUTPUT))
    args = parser.parse_args(argv)
    
    packet = materialize_grounding_packet(args.article_packet)
    write_json(args.output_packet, packet)
    
    # Load article title for backlog
    try:
        art_data = load_json(args.article_packet)
        title = art_data.get("title", "Untitled Article")
    except Exception:
        title = "Untitled Article"
        
    backlog_text = generate_backlog_markdown(packet, title)
    Path(args.output_backlog).write_text(backlog_text, encoding="utf-8")
    
    evidence_text = generate_evidence_markdown(packet)
    Path(args.output_evidence).write_text(evidence_text, encoding="utf-8")
    
    # Write report and pointer
    out_path = Path(args.output_packet)
    (out_path.parent / "implementation_report.md").write_text(implementation_report(packet), encoding="utf-8")
    (out_path.parent / "next_task_pointer.md").write_text(next_task_pointer(packet), encoding="utf-8")
    
    print(json.dumps({
        "research_packet_id": packet["research_packet_id"],
        "grounding_status": packet["grounding_status"],
        "blocked_reasons": packet["blocked_reasons"]
    }, indent=2))
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
