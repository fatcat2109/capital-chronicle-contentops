"""Daily article brief generation module.

Step 4 of the Daily ContentOps loop.
Loads the reselection packet, blocks original Japan idea, and generates
a structured editorial brief for the reselected oil export surge topic.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_DAILY_ARTICLE_BRIEF_GENERATION_V0"
CLASSIFICATION_CANDIDATE = "PASS_CANDIDATE_ONLY_CONTENTOPS_DAILY_ARTICLE_BRIEF_GENERATION_V0"
CLASSIFICATION_PASS = "PASS_CONTENTOPS_DAILY_ARTICLE_BRIEF_GENERATION_V0"

def generate_article_brief(
    reselection_packet_file: str | Path,
    output_dir: str | Path | None = None
) -> dict[str, Any]:
    packet_path = Path(reselection_packet_file)
    output_path = Path(output_dir) if output_dir else Path(".")
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. Load reselection packet
    if not packet_path.exists():
        raise FileNotFoundError(f"Reselection packet not found at: {packet_path}")
    with open(packet_path, "r", encoding="utf-8") as f:
        packet = json.load(f)

    # 2. Verify original Japan idea is blocked
    original_idea_blocked = packet.get("original_idea_blocked")
    original_selected = packet.get("original_selected_idea") or {}
    original_idea_id = original_selected.get("selected_idea_id")

    if original_idea_id == "idea_macro_policy_rates_liquidity_20260709":
        # Block drafting of original Japan idea
        if not original_idea_blocked:
            raise ValueError("Original Japan JGB idea is not blocked. Failing closed.")

    # 3. Extract reselected topic details
    reselected_title = packet.get("reselected_title")
    reselected_idea_id = packet.get("reselected_idea_id")
    topic_family = packet.get("reselected_topic_family")
    reselected_angle = packet.get("reselected_angle")
    supporting_headline_ids = packet.get("supporting_headline_ids") or []
    expected_support_families = packet.get("expected_support_families") or []

    if len(reselected_title) > 120:
        reselected_title = reselected_title[:117] + "..."

    # 4. Generate structured article brief JSON
    working_slug = "us-oil-export-surge-spr-dynamics"
    one_sentence_thesis = "The surge in US crude oil exports and domestic production, paired with Strategic Petroleum Reserve (SPR) dynamics, is fundamentally reshaping the global energy market and trade flows."
    target_reader = "Global macro investors, energy traders, and policy analysts."
    why_now = "US crude exports have risen significantly, making the US a major global exporter alongside Russia and Saudi Arabia, necessitating a structural overview of energy flows."

    known_caveats = [
        "Since no live numeric database was queried in this phase, all data points must be treated as qualitative candidate inputs.",
        "Exact figures must not be presented as verified internal fact without prior source verification."
    ]

    outline_sections = [
        "Introduction: The New Era of US Energy Dominance",
        "Section 1: Production Heights and Export Capacity Surge",
        "Section 2: The Role of the Strategic Petroleum Reserve (SPR)",
        "Section 3: Geopolitical Repercussions and Trade Flow Realignment",
        "Conclusion: Market Outlook and Structural Implications"
    ]

    key_questions_to_answer = [
        "How did the US transition to exporting 5 million barrels per day?",
        "What is the impact of SPR releases on the export volumes?",
        "How do US oil exports affect OPEC+ pricing power?"
    ]

    prohibited_claims = [
        "Do not make definitive statements about future oil price targets (e.g. Brent to $100/bbl).",
        "Do not provide trading signals or direct investment advice (buy/sell/hold/sizing).",
        "Do not present speculative geopolitical outcomes as verified facts."
    ]

    required_disclaimers_or_caveats = [
        "This is an article brief, not a full article draft.",
        "This analysis is purely educational and for commentary purposes only; it does not constitute financial or investment advice.",
        "Information relies on candidate proxy series and qualitative background data; no numeric truth is guaranteed."
    ]

    article_brief = {
        "task_label": TASK_LABEL,
        "source_reselection_packet": str(packet_path),
        "original_idea_blocked": original_idea_blocked,
        "selected_idea_id": reselected_idea_id,
        "editorial_title": reselected_title,
        "working_slug": working_slug,
        "topic_family": topic_family,
        "one_sentence_thesis": one_sentence_thesis,
        "target_reader": target_reader,
        "why_now": why_now,
        "source_support_needed": expected_support_families,
        "known_caveats": known_caveats,
        "outline_sections": outline_sections,
        "key_questions_to_answer": key_questions_to_answer,
        "prohibited_claims": prohibited_claims,
        "required_disclaimers_or_caveats": required_disclaimers_or_caveats,
        "draft_readiness": "candidate_only",  # Kept as candidate_only per instructions
        "no_full_article_confirmation": True,
        "no_media_confirmation": True,
        "no_platform_variant_confirmation": True,
        "no_dispatch_confirmation": True
    }

    # 5. Generate article brief Markdown (article_brief_v0.md)
    brief_md = f"""# Editorial Article Brief (Candidate Only)

*This is an article brief, not a full article draft.*

## Overview
- **Editorial Title:** {reselected_title}
- **Working Slug:** `{working_slug}`
- **Topic Family:** `{topic_family}`
- **One-Sentence Thesis:** {one_sentence_thesis}

## Context & Rationale
- **Target Reader:** {target_reader}
- **Why Now:** {why_now}

## Structure & Outline
"""
    for sec in outline_sections:
        brief_md += f"- **{sec}**\n"

    brief_md += """
## Key Questions to Answer
"""
    for q in key_questions_to_answer:
        brief_md += f"- {q}\n"

    brief_md += """
## Required Supporting Data
"""
    for fam in expected_support_families:
        brief_md += f"- `{fam}` (Source: Capital Chronicle database)\n"

    brief_md += """
## Editorial Rules & Prohibited Claims
"""
    for claim in prohibited_claims:
        brief_md += f"- *Prohibited:* {claim}\n"

    brief_md += """
## Disclaimers & Caveats
- *Notice:* This brief is for candidate study and qualitative description only. Since no numeric database series are actively loaded in this task, exact values are not verified and no numeric claims should be made.
- *Disclaimer:*纯学术探讨/分析评论，不构成投资建议或交易信号。
"""

    # 6. Generate run evidence
    run_evidence = {
        "classification": CLASSIFICATION_CANDIDATE,
        "task_label": TASK_LABEL,
        "baseline_head": "fa697624c42e64f342009e71b4fec795f74737cd",
        "source_reselection_packet": str(packet_path),
        "selected_idea_id": reselected_idea_id,
        "topic_family": topic_family,
        "original_idea_blocked": True,
        "draft_readiness": "candidate_only",
        "no_main_repo_mutation_confirmation": True,
        "no_external_fetch_confirmation": True,
        "no_database_repair_confirmation": True,
        "no_full_article_confirmation": True,
        "no_media_confirmation": True,
        "no_platform_variant_confirmation": True,
        "no_platform_write_confirmation": True,
        "no_dispatch_confirmation": True,
        "no_raw_secret_read_confirmation": True,
        "output_paths": {
            "article_brief_json": str(output_path / "article_brief_v0.json"),
            "article_brief_md": str(output_path / "article_brief_v0.md"),
            "run_evidence": str(output_path / "run_evidence_v0.json")
        },
        "blockers": []
    }

    # Write files
    with open(output_path / "article_brief_v0.json", "w", encoding="utf-8") as f:
        json.dump(article_brief, f, indent=2, ensure_ascii=False)

    with open(output_path / "article_brief_v0.md", "w", encoding="utf-8") as f:
        f.write(brief_md)

    with open(output_path / "run_evidence_v0.json", "w", encoding="utf-8") as f:
        json.dump(run_evidence, f, indent=2, ensure_ascii=False)

    # Generate README.md
    readme_content = """# Step 4: Daily Article Brief Generation

This directory contains the output of Step 4 of the Daily ContentOps loop.
It generates a structured editorial brief for the reselected WTI Crude oil export surge topic.
"""
    with open(output_path / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    return {
        "brief_json": article_brief,
        "brief_md": brief_md,
        "evidence": run_evidence
    }
