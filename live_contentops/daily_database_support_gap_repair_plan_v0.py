"""Daily database support gap repair plan builder.

Step 3b of the Daily ContentOps loop.
Loads the Step 3 database support packet, identifies data gaps,
and defines recommended next data-ingestion/promotion tasks.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_DAILY_DATABASE_SUPPORT_GAP_REPAIR_PLAN_V0"
CLASSIFICATION_WITH_GAPS = "PASS_WITH_GAPS_DAILY_DATABASE_SUPPORT_GAP_REPAIR_PLAN_V0"
CLASSIFICATION_NORMAL = "PASS_DAILY_DATABASE_SUPPORT_GAP_REPAIR_PLAN_V0"

def build_database_support_gap_repair_plan(
    support_packet_file: str | Path,
    output_dir: str | Path | None = None
) -> dict[str, Any]:
    packet_path = Path(support_packet_file)
    output_path = Path(output_dir) if output_dir else Path(".")
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. Load support packet
    if not packet_path.exists():
        raise FileNotFoundError(f"Step 3 database support packet not found at: {packet_path}")

    with open(packet_path, "r", encoding="utf-8") as f:
        packet = json.load(f)

    selected_idea_id = packet.get("selected_idea_id")
    selected_title = packet.get("selected_title")
    selected_family = packet.get("selected_topic_family")
    support_families_requested = packet.get("support_families_requested") or []
    support_families_partial = packet.get("support_families_partial") or []
    support_families_missing = packet.get("support_families_missing") or []

    # 2. Define gap repair tasks for each missing/partial family
    gap_repairs = {}

    if "Global Central Bank Liquidity Measures" in support_families_requested:
        is_missing = "Global Central Bank Liquidity Measures" in support_families_missing
        gap_repairs["Global Central Bank Liquidity Measures"] = {
            "support_family": "Global Central Bank Liquidity Measures",
            "gap_status": "missing" if is_missing else "partial",
            "recommended_task": "TASK_TREASURY_FED_NYFED_RATES_LIQUIDITY_CONTRACT_FIXTURE_EXTREME_V1",
            "action_required": "Implement local rates and liquidity database ingestion sidecars to fetch NY Fed, SOFR, and H.4.1 balance sheet metrics.",
            "authority_target": "Capital Chronicle local database",
            "estimated_complexity": "Medium"
        }

    if "Japan Yield Curve (JGB)" in support_families_requested:
        is_missing = "Japan Yield Curve (JGB)" in support_families_missing
        gap_repairs["Japan Yield Curve (JGB)"] = {
            "support_family": "Japan Yield Curve (JGB)",
            "gap_status": "missing" if is_missing else "partial",
            "recommended_task": "TASK_APAC_CHINA_JAPAN_OFFICIAL_MACRO_VALUE_CAPTURE_V1",
            "action_required": "Promote BOJ official macro contracts and execute localized value capture scripts to verify real JGB yield curve values.",
            "authority_target": "Capital Chronicle local database",
            "estimated_complexity": "Medium"
        }

    if "USD/JPY FX Spot & Volatility" in support_families_requested:
        is_missing = "USD/JPY FX Spot & Volatility" in support_families_missing
        gap_repairs["USD/JPY FX Spot & Volatility"] = {
            "support_family": "USD/JPY FX Spot & Volatility",
            "gap_status": "missing" if is_missing else "partial",
            "recommended_task": "TASK_USDJPY_MT5_OANDA_CONTRACT_PROMOTION_V1",
            "action_required": "Perform source review and promote MT5/OANDA practice FX contracts from candidate-only metadata to cleared numeric truth status.",
            "authority_target": "Capital Chronicle local database",
            "estimated_complexity": "Low"
        }

    # 3. Generate the Gap Repair Plan JSON
    gap_repair_plan = {
        "task_label": TASK_LABEL,
        "selected_idea_id": selected_idea_id,
        "selected_title": selected_title,
        "selected_topic_family": selected_family,
        "support_families_requested": support_families_requested,
        "support_families_missing": support_families_missing,
        "support_families_partial": support_families_partial,
        "gap_repairs": gap_repairs,
        "ready_for_article_draft": False,  # Safety invariant: remains false until gaps are repaired
        "ready_for_data_ingestion_runs": True,
        "caveats": "Local database lacks verified numeric truth values for Yen/JGB macro commentary. This document outlines the ingestion roadmap and does not approve drafting code."
    }

    # 4. Generate the Summary Memo Markdown
    summary_memo = f"""# Database Support Gap Repair Plan Memo

**Idea Title:** {selected_title}
**Selected Idea ID:** {selected_idea_id}

## Gap Diagnostics
- **Missing Required Data:** {", ".join(support_families_missing) if support_families_missing else "None"}
- **Partial/Candidate Data Only:** {", ".join(support_families_partial) if support_families_partial else "None"}

## Required Database Ingestion & Promotion Roadmap
"""
    for family, repair in gap_repairs.items():
        summary_memo += f"""
### {family} ({repair['gap_status'].upper()})
- **Recommended Ingestion Task:** `{repair['recommended_task']}`
- **Action Required:** {repair['action_required']}
- **Target Authority:** {repair['authority_target']}
- **Complexity:** {repair['estimated_complexity']}
"""

    summary_memo += """
## Downstream Article Draft Guidance
Until these database gaps are closed by the ingestion tasks above:
1. Downstream article drafts **MUST NOT** make exact numeric claims about Yen/JGB rates.
2. Market movements must be described as qualitative background or operator-supplied metrics with clear source caveats.
3. Live dispatch/publishing remains locked.
"""

    # 5. Generate run evidence
    missing_count = len(support_families_missing)
    partial_count = len(support_families_partial)
    classification = CLASSIFICATION_WITH_GAPS if (missing_count > 0 or partial_count > 0) else CLASSIFICATION_NORMAL

    run_evidence = {
        "classification": classification,
        "task_label": TASK_LABEL,
        "baseline_head": "911a970ea5b8f619d931b7ae35fcf27425ee478f",
        "selected_idea_id": selected_idea_id,
        "main_repo_mutated": False,
        "external_fetch_performed": False,
        "no_article_draft_confirmation": True,
        "no_media_confirmation": True,
        "no_platform_write_confirmation": True,
        "no_dispatch_confirmation": True,
        "no_raw_secret_read_confirmation": True,
        "output_paths": {
            "database_support_gap_repair_plan": str(output_path / "database_support_gap_repair_plan_v0.json"),
            "database_support_gap_repair_summary": str(output_path / "database_support_gap_repair_summary_v0.md"),
            "run_evidence": str(output_path / "run_evidence_v0.json")
        }
    }

    # Write files
    with open(output_path / "database_support_gap_repair_plan_v0.json", "w", encoding="utf-8") as f:
        json.dump(gap_repair_plan, f, indent=2, ensure_ascii=False)

    with open(output_path / "database_support_gap_repair_summary_v0.md", "w", encoding="utf-8") as f:
        f.write(summary_memo)

    with open(output_path / "run_evidence_v0.json", "w", encoding="utf-8") as f:
        json.dump(run_evidence, f, indent=2, ensure_ascii=False)

    # Generate a README.md if not exists
    readme_content = """# Step 3b: Daily Database Support Gap Repair Plan

This directory contains the outputs of the Gap Repair Planning phase.
Its purpose is to define the exact next tasks required to populate the main database repository with necessary JGB/FX/Liquidity series.
"""
    with open(output_path / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    return {
        "plan": gap_repair_plan,
        "summary": summary_memo,
        "evidence": run_evidence
    }
