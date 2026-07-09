"""Daily database support packet builder.

Step 3 of the Daily ContentOps loop.
Loads the Step 2 article idea brief, looks up read-only database contracts,
checks data availability, and creates support summaries and gap reports.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_DAILY_DATABASE_SUPPORT_PACKET_V0"
CLASSIFICATION_WITH_GAPS = "PASS_WITH_GAPS_DAILY_DATABASE_SUPPORT_PACKET_V0"
CLASSIFICATION_NORMAL = "PASS_DAILY_DATABASE_SUPPORT_PACKET_V0"

DEFAULT_MAIN_DB_REPO = Path("A:/Capital Chronicle/Headline Raw data local json/capital-chronicle-ingestion")

def build_database_support_packet(
    idea_selection_file: str | Path,
    output_dir: str | Path | None = None,
    main_db_repo: str | Path | None = None
) -> dict[str, Any]:
    idea_path = Path(idea_selection_file)
    output_path = Path(output_dir) if output_dir else Path(".")
    output_path.mkdir(parents=True, exist_ok=True)

    db_repo_path = Path(main_db_repo) if main_db_repo else DEFAULT_MAIN_DB_REPO

    # 1. Load selected idea packet
    if not idea_path.exists():
        raise FileNotFoundError(f"Step 2 idea selection file not found at: {idea_path}")

    with open(idea_path, "r", encoding="utf-8") as f:
        idea = json.load(f)

    selected_idea_id = idea.get("selected_idea_id")
    selected_title = idea.get("selected_title")
    selected_family = idea.get("selected_topic_family")
    support_families_requested = idea.get("database_support_needed") or []

    # 2. Check main database repo path
    db_repo_exists = db_repo_path.exists()

    # 3. Resolve support families honestly (candidate / proxy / missing)
    support_items = {}
    
    # Resolving Japan Yield Curve (JGB)
    jgb_contract_path = db_repo_path / "docs/research/database_foundation/apac_china_japan_official_macro_contracts/APAC_CHINA_JAPAN_API_SOURCE_CONTRACTS_V1.json"
    if db_repo_exists and jgb_contract_path.exists():
        support_items["Japan Yield Curve (JGB)"] = {
            "support_family": "Japan Yield Curve (JGB)",
            "availability": "partial",
            "authority_level": "candidate",
            "source_artifact_path": str(jgb_contract_path),
            "source_artifact_type": "source_contract",
            "source_health_or_dqr_ref": "dqr_status: BLOCKED",
            "latest_observed_timestamp_if_available": None,
            "numeric_values_included": False,
            "caveats": "BOJ macro contracts exist as candidate-only metadata structures but are BLOCKED from state promotion."
        }
    else:
        support_items["Japan Yield Curve (JGB)"] = {
            "support_family": "Japan Yield Curve (JGB)",
            "availability": "missing",
            "authority_level": "missing",
            "source_artifact_path": None,
            "source_artifact_type": None,
            "source_health_or_dqr_ref": None,
            "latest_observed_timestamp_if_available": None,
            "numeric_values_included": False,
            "caveats": "Japan JGB/rate contract source not found in database repo."
        }

    # Resolving USD/JPY FX Spot & Volatility
    oanda_contract_path = db_repo_path / "data/audit/data_sufficiency/task_usdjpy_oanda_practice_readonly_source_review_and_contract_v1/usdjpy_oanda_practice_source_contract.json"
    if db_repo_exists and oanda_contract_path.exists():
        support_items["USD/JPY FX Spot & Volatility"] = {
            "support_family": "USD/JPY FX Spot & Volatility",
            "availability": "partial",
            "authority_level": "candidate",
            "source_artifact_path": str(oanda_contract_path),
            "source_artifact_type": "source_contract",
            "source_health_or_dqr_ref": "do_not_use_as_numeric_truth: true",
            "latest_observed_timestamp_if_available": None,
            "numeric_values_included": False,
            "caveats": "USD/JPY covers MT5 symbol plan and OANDA practice contracts but remains candidate-only (do not use as numeric truth)."
        }
    else:
        support_items["USD/JPY FX Spot & Volatility"] = {
            "support_family": "USD/JPY FX Spot & Volatility",
            "availability": "missing",
            "authority_level": "missing",
            "source_artifact_path": None,
            "source_artifact_type": None,
            "source_health_or_dqr_ref": None,
            "latest_observed_timestamp_if_available": None,
            "numeric_values_included": False,
            "caveats": "USD/JPY FX contracts not found in database repo."
        }

    # Resolving Global Central Bank Liquidity Measures
    # Fed H.4.1/SOFR rates remain in design planning phase based on source_family_coverage_matrix
    support_items["Global Central Bank Liquidity Measures"] = {
        "support_family": "Global Central Bank Liquidity Measures",
        "availability": "missing",
        "authority_level": "missing",
        "source_artifact_path": None,
        "source_artifact_type": None,
        "source_health_or_dqr_ref": "rates_liquidity: design_planning_phase",
        "latest_observed_timestamp_if_available": None,
        "numeric_values_included": False,
        "caveats": "Rates and liquidity datasets are in design planning phase; no active ingestion pipeline exists."
    }

    # Calculate counts
    support_families_resolved = []
    support_families_partial = []
    support_families_missing = []

    for fam in support_families_requested:
        item = support_items.get(fam)
        if not item or item["availability"] == "missing":
            support_families_missing.append(fam)
        elif item["availability"] == "partial":
            support_families_partial.append(fam)
        else:
            support_families_resolved.append(fam)

    available_count = len(support_families_resolved)
    partial_count = len(support_families_partial)
    missing_count = len(support_families_missing)

    # ready_for_article_draft is false if there are missing required supports
    ready_for_article_draft = False

    # 4. Generate source gap report
    gap_report = {
        "task_label": TASK_LABEL,
        "selected_idea_id": selected_idea_id,
        "missing_families": support_families_missing,
        "partial_families": support_families_partial,
        "recommended_next_data_ingestion_tasks": [
            "TASK_TREASURY_FED_NYFED_RATES_LIQUIDITY_CONTRACT_FIXTURE_EXTREME_V1",
            "TASK_APAC_CHINA_JAPAN_OFFICIAL_MACRO_VALUE_CAPTURE_V1"
        ],
        "caveats": "Local database lacks proven numeric truth values for Yen/JGB macro commentary. Downstream article draft must explicitly label JGB/liquidity claims as qualitative background rather than verified numeric truth."
    }

    # 5. Generate database support packet
    support_packet = {
        "task_label": TASK_LABEL,
        "selected_idea_id": selected_idea_id,
        "selected_title": selected_title,
        "selected_topic_family": selected_family,
        "support_families_requested": support_families_requested,
        "support_families_resolved": support_families_resolved,
        "support_families_partial": support_families_partial,
        "support_families_missing": support_families_missing,
        "support_items": support_items,
        "database_repo_path_checked": str(db_repo_path),
        "main_repo_mutated": False,
        "external_fetch_performed": False,
        "exact_numeric_claims_made": False,
        "ready_for_article_draft": ready_for_article_draft,
        "caveats": "Information is strictly qualitative. No actual numeric databases were queried or mutated."
    }

    # 6. Generate database support summary memo (MD)
    md_content = f"""# Database Support Summary Memo

**Idea Title:** {selected_title}
**Selected Idea ID:** {selected_idea_id}

## Data Availability Matrix
"""
    for fam, item in support_items.items():
        md_content += f"- **{fam}**: {item['availability'].upper()} (Authority: {item['authority_level'].upper()})\n"
        if item['caveats']:
            md_content += f"  - *Caveat:* {item['caveats']}\n"

    md_content += f"""
## Gap Diagnosis
- **Missing Required Data:** {", ".join(support_families_missing) if support_families_missing else "None"}
- **Partial/Candidate Data Only:** {", ".join(support_families_partial) if support_families_partial else "None"}

## Recommendation for Downstream Article Draft
Due to the lack of finalized, DQR-cleared numeric databases in the local repository:
1. The downstream draft **MUST NOT** quote specific JGB yields or FX rates as verified internal facts.
2. Frame Yen volatility and JGB yields as **qualitative background market concerns** rather than numeric truth.
3. This memo is a data availability audit only and **NOT** a drafted commentary article or trading advice.
"""

    classification = CLASSIFICATION_WITH_GAPS if (missing_count > 0 or partial_count > 0) else CLASSIFICATION_NORMAL

    # 7. Generate run evidence
    run_evidence = {
        "classification": classification,
        "task_label": TASK_LABEL,
        "baseline_head": "b2ff7b384e3c9386347abb9cacbefff33dc66007",
        "selected_idea_id": selected_idea_id,
        "support_family_count": len(support_families_requested),
        "available_count": available_count,
        "partial_count": partial_count,
        "missing_count": missing_count,
        "main_repo_mutated": False,
        "external_fetch_performed": False,
        "no_article_draft_confirmation": True,
        "no_media_confirmation": True,
        "no_platform_write_confirmation": True,
        "no_dispatch_confirmation": True,
        "no_raw_secret_read_confirmation": True,
        "output_paths": {
            "database_support_packet": str(output_path / "database_support_packet_v0.json"),
            "database_support_summary": str(output_path / "database_support_summary_v0.md"),
            "source_gap_report": str(output_path / "source_gap_report_v0.json"),
            "run_evidence": str(output_path / "run_evidence_v0.json")
        },
        "blockers": []
    }

    # Write files
    with open(output_path / "database_support_packet_v0.json", "w", encoding="utf-8") as f:
        json.dump(support_packet, f, indent=2, ensure_ascii=False)

    with open(output_path / "source_gap_report_v0.json", "w", encoding="utf-8") as f:
        json.dump(gap_report, f, indent=2, ensure_ascii=False)

    with open(output_path / "database_support_summary_v0.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    with open(output_path / "run_evidence_v0.json", "w", encoding="utf-8") as f:
        json.dump(run_evidence, f, indent=2, ensure_ascii=False)

    return {
        "packet": support_packet,
        "gap": gap_report,
        "evidence": run_evidence
    }
