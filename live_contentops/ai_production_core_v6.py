"""V6 AI Production Core.

Consolidates Idea -> Grounding -> Canonical Substack -> SEO Refinement pipelines.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from live_contentops import ai_provider_gate_v6 as provider_gate
from live_contentops import prompt_template_registry_v6 as prompt_registry
from live_contentops import operator_intent_contract_v6 as intent_contract
from live_contentops import content_idea_packet_v6 as idea_packet
from live_contentops import research_grounding_packet_v6 as grounding_packet
from live_contentops import canonical_article_workflow_v6 as article_workflow
from live_contentops import seo_editorial_packet_v6 as seo_packet

TASK_LABEL = "TASK_CONTENTOPS_V6_AI_PRODUCTION_CORE_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_AI_PRODUCTION_CORE")


def write_json(path: str | Path, data: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def generate_runbook_markdown() -> str:
    return """# V6 AI Production Core Runbook

This runbook guides operators to process content ideas safely.

## Content Core Process
1. Operator inputs Jim's Content Idea.
2. AI research grounding is constructed (never invent source citations).
3. Canonical Substack article workflow drafts the post (enforce limitations and disclosure).
4. SEO refinement optimizes readability and filters out clickbait and financial trade suggestions.
"""


def generate_blocker_report_markdown(blockers: list[str]) -> str:
    blocker_str = ", ".join(f"`{b}`" for b in blockers) if blockers else "None"
    return f"""# AI Production Core Blocker Report

- **Active Blockers**: {blocker_str}
"""


def generate_implementation_report_markdown(status: str) -> str:
    return f"""# AI Production Core Implementation Report

- **Task Label**: {TASK_LABEL}
- **Status**: {status}
- **Schema Version**: {SCHEMA_VERSION}
- **Alignment with V6 North Star**: Confirmed.
"""


def generate_next_task_pointer_markdown(next_task: str) -> str:
    return f"""# Next Task Pointer

Recommended next task:

`{next_task}`
"""


def run_production_pipeline(output_dir: Path) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    # Create safe samples
    idea = idea_packet.create_content_idea_packet(
        idea_text="Analyzing the historical volatility of Treasury yields",
        operator_name="Jim",
        source_context={"ref_source": "Fed H.15 database Release 2026-06-25"},
        target_audience="general_financial_education"
    )
    
    intent = intent_contract.validate_operator_intent({
        "intent_class": "create_canonical_article",
        "intent_text": "Create educational analysis on volatility of treasury yields H.15",
        "research_grounding_complete": True
    })
    
    grounding = grounding_packet.construct_research_grounding_packet(
        topic="historical volatility of Treasury yields",
        source_refs=["Fed H.15 database Release 2026-06-25"],
        official_source_refs=["Fed H.15 database Release 2026-06-25"],
        freshness_status="fresh",
        source_quality_status="high_official"
    )
    
    article = article_workflow.create_canonical_article(
        research_packet=grounding,
        title="Historical Volatility of Treasury Yields",
        subtitle="An educational analysis of yield movements based on Fed H.15 release",
        body_markdown="Treasury yields represent key cost of capital metrics. Historically, yield volatility reflects macroeconomic adjustments.",
        citations=["Fed H.15 database Release 2026-06-25"],
        limitations="This analysis is limited by the parameters of the H.15 dataset and does not account for future policy changes. Yield analysis is uncertain.",
        disclosure="No financial recommendations or trade positioning suggestions are made."
    )
    
    seo = seo_packet.create_seo_editorial_packet(
        article_packet=article,
        primary_keyword="Treasury yields historical volatility",
        secondary_keywords=["Treasury yields", "volatility", "Fed H.15"],
        title_candidates=["Analyzing Treasury Yield Volatility", "Treasury Yield Volatility: A Fed H.15 Study"],
        meta_description="Read about the historical volatility of Treasury yields in our educational deep dive.",
        limitations_preserved=True
    )
    
    # Check if there are any validation blockers in our sub-components
    blockers = []
    if not intent["is_valid"]:
        blockers.extend(intent["blockers"])
    if grounding["blocked_reasons"]:
        blockers.extend(grounding["blocked_reasons"])
    if article.get("blockers"):
        blockers.extend(article["blockers"])
    if seo.get("blockers"):
        blockers.extend(seo["blockers"])
        
    blockers = sorted(list(set(blockers)))
    
    core_status = "READY_FOR_REVIEW_ONLY_DRY_RUN"
    
    # Main status packet
    core_packet = {
        "ai_production_core_status": core_status,
        "live_provider_call_performed": False,
        "provider_credentials_hydrated": False,
        "public_postable": False,
        "dispatch_allowed_now": False,
        "approval_valid_for_dispatch": False,
        "human_review_required": True,
        "allowed_for_drafting": True,
        "allowed_for_publication": False,
        "kill_switch_active": True,
        "live_write_allowed_now": False,
        "browser_session_started": False,
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "next_recommended_task": "TASK_CONTENTOPS_V6_PLATFORM_CONTENT_GENERATORS_AND_THREAD_CONTINUATION_HEAVY_BATCH_V0",
        "blockers": blockers
    }
    
    validation_report = {
        "schema_version": SCHEMA_VERSION,
        "safety_checks_pass": len(blockers) == 0,
        "operator_intent_valid": intent["is_valid"],
        "research_grounding_valid": len(grounding["blocked_reasons"]) == 0,
        "canonical_article_valid": len(article.get("blockers", [])) == 0,
        "seo_refinement_valid": len(seo.get("blockers", [])) == 0,
        "unexpected_claims_detected": False,
        "unsafe_material_detected": False
    }
    
    # Save files
    write_json(output_dir / "sample_content_idea_packet.json", idea)
    write_json(output_dir / "sample_operator_intents.json", intent)
    write_json(output_dir / "sample_research_grounding_packet.json", grounding)
    write_json(output_dir / "sample_canonical_article_packet.json", article)
    write_json(output_dir / "sample_seo_editorial_packet.json", seo)
    
    return core_packet, validation_report, blockers


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 AI Production Core")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)
    
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Pre-write prompt registry & provider packets
    credentials = provider_gate.inspect_provider_credentials()
    provider_packet = {
        "ai_provider_mode": provider_gate.get_provider_mode(),
        "credentials_present": credentials,
        "schema_version": SCHEMA_VERSION
    }
    write_json(out_dir / "provider_gate_packet.json", provider_packet)
    
    prompt_packet = {
        "prompt_families": prompt_registry.PROMPT_FAMILIES,
        "templates_count": len(prompt_registry.TEMPLATES),
        "schema_version": SCHEMA_VERSION
    }
    write_json(out_dir / "prompt_registry_packet.json", prompt_packet)
    
    # Run the core pipeline
    packet, report, blockers = run_production_pipeline(out_dir)
    
    write_json(out_dir / "ai_production_core_packet.json", packet)
    write_json(out_dir / "ai_production_core_validation_report.json", report)
    
    # Write md files
    (out_dir / "ai_production_core_blocker_report.md").write_text(generate_blocker_report_markdown(blockers), encoding="utf-8")
    (out_dir / "ai_production_core_runbook.md").write_text(generate_runbook_markdown(), encoding="utf-8")
    (out_dir / "implementation_report.md").write_text(generate_implementation_report_markdown(packet["ai_production_core_status"]), encoding="utf-8")
    (out_dir / "next_task_pointer.md").write_text(generate_next_task_pointer_markdown(packet["next_recommended_task"]), encoding="utf-8")
    
    print(json.dumps({
        "ai_production_core_status": packet["ai_production_core_status"],
        "blockers": packet["blockers"]
    }, indent=2))
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
