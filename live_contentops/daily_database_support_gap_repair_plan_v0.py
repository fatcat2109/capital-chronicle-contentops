"""Daily database support gap repair plan builder.

Step 3b of the Daily ContentOps loop.
Loads the Step 3 database support packet, identifies data gaps,
and defines recommended next database tasks in next_database_tasks_v0.json.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_DAILY_DATABASE_SUPPORT_GAP_REPAIR_PLAN_V0"
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
        gap_repairs["Global Central Bank Liquidity Measures"] = {
            "support_family": "Global Central Bank Liquidity Measures",
            "gap_status": "missing",
            "caveat": "Global Central Bank Liquidity Measures: missing, needs exact family definition/source selection before use.",
            "recommended_task": "TASK_TREASURY_FED_NYFED_RATES_LIQUIDITY_CONTRACT_FIXTURE_EXTREME_V1"
        }

    if "Japan Yield Curve (JGB)" in support_families_requested:
        gap_repairs["Japan Yield Curve (JGB)"] = {
            "support_family": "Japan Yield Curve (JGB)",
            "gap_status": "partial",
            "caveat": "Japan Yield Curve (JGB): partial/candidate, needs official source contract hardening or parser/export task.",
            "recommended_task": "TASK_APAC_CHINA_JAPAN_OFFICIAL_MACRO_VALUE_CAPTURE_V1"
        }

    if "USD/JPY FX Spot & Volatility" in support_families_requested:
        gap_repairs["USD/JPY FX Spot & Volatility"] = {
            "support_family": "USD/JPY FX Spot & Volatility",
            "gap_status": "partial",
            "caveat": "USD/JPY FX Spot & Volatility: partial/candidate, needs read-only broker/proxy policy/export task or accepted non-exact proxy wording.",
            "recommended_task": "TASK_USDJPY_MT5_OANDA_CONTRACT_PROMOTION_V1"
        }

    # 3. Generate the Next Database Tasks JSON
    tasks = [
        {
            "task_label": "TASK_CAPITAL_CHRONICLE_JAPAN_FX_LIQUIDITY_SOURCE_SUPPORT_VERIFICATION_V0",
            "target_repo": "fatcat2109/capital-chronicle-contentops",
            "target_branch": "master",
            "scope": "Verify official source contracts and JGB/FX proxy data mappings in a read-only/planning/exact-source-verification mode.",
            "allowed_reads": [
                "A:/Capital Chronicle/Headline Raw data local json/capital-chronicle-ingestion/docs/research/database_foundation/apac_china_japan_official_macro_contracts/APAC_CHINA_JAPAN_API_SOURCE_CONTRACTS_V1.json",
                "A:/Capital Chronicle/Headline Raw data local json/capital-chronicle-ingestion/data/audit/data_sufficiency/task_usdjpy_oanda_practice_readonly_source_review_and_contract_v1/usdjpy_oanda_practice_source_contract.json"
            ],
            "forbidden_actions": [
                "live_ingestion",
                "platform_api_call",
                "browser_cdp",
                "write_to_main_db",
                "article_drafting"
            ],
            "expected_outputs": [
                "docs/research/database_foundation/source_verification_report_v0.json"
            ],
            "validation": [
                "python -m pytest tests/test_source_verification.py"
            ],
            "acceptance_condition": "Verification report successfully maps the available candidate sources without mutating live data or initiating article drafting."
        },
        {
            "task_label": "TASK_TREASURY_FED_NYFED_RATES_LIQUIDITY_CONTRACT_FIXTURE_EXTREME_V1",
            "target_repo": "fatcat2109/capital-chronicle-contentops",
            "target_branch": "master",
            "scope": "Define exact schemas and rates/liquidity rules to prepare SOFR / Balance Sheet series.",
            "allowed_reads": [
                "docs/research/rates_liquidity/"
            ],
            "forbidden_actions": [
                "platform_api_call",
                "browser_cdp",
                "article_drafting"
            ],
            "expected_outputs": [
                "data/audit/data_sufficiency/rates_liquidity_schema_v1.json"
            ],
            "validation": [
                "python -m pytest tests/test_rates_liquidity_ingestion.py"
            ],
            "acceptance_condition": "Rates and liquidity schema contract is generated and verified."
        },
        {
            "task_label": "TASK_APAC_CHINA_JAPAN_OFFICIAL_MACRO_VALUE_CAPTURE_V1",
            "target_repo": "fatcat2109/capital-chronicle-contentops",
            "target_branch": "master",
            "scope": "Hardens BOJ official macro source contracts and creates localized yield capture scripts.",
            "allowed_reads": [
                "docs/research/apac_china_japan_macro/"
            ],
            "forbidden_actions": [
                "platform_api_call",
                "browser_cdp",
                "article_drafting"
            ],
            "expected_outputs": [
                "data/audit/data_sufficiency/jgb_yield_curve_captured.json"
            ],
            "validation": [
                "python -m pytest tests/test_jgb_macro_capture.py"
            ],
            "acceptance_condition": "JGB official macro yield data is successfully captured and verified."
        }
    ]

    next_database_tasks = {
        "tasks": tasks,
        "recommended_first_task": "TASK_CAPITAL_CHRONICLE_JAPAN_FX_LIQUIDITY_SOURCE_SUPPORT_VERIFICATION_V0"
    }

    # 4. Generate support_gap_repair_plan_v0.json
    support_gap_repair_plan = {
        "task_label": TASK_LABEL,
        "selected_idea_id": selected_idea_id,
        "selected_title": selected_title,
        "selected_topic_family": selected_family,
        "support_families_requested": support_families_requested,
        "support_families_missing": support_families_missing,
        "support_families_partial": support_families_partial,
        "gap_repairs": gap_repairs,
        "article_draft_blocked": True,
        "article_draft_allowed_as_candidate_only": False,
        "main_repo_mutated": False,
        "external_fetch_performed": False,
        "exact_numeric_claims_made": False,
        "caveats": "Local database lacks verified numeric truth values for Yen/JGB macro commentary. Downstream article draft guidance remains blocked until database gaps are resolved."
    }

    # 5. Generate support_gap_repair_plan_v0.md
    summary_memo = f"""# Database Support Gap Repair Plan

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
- *Status Detail:* {repair['caveat']}
- *Recommended Next Task:* `{repair['recommended_task']}`
"""

    summary_memo += """
## Recommended Action Sequence
The recommended first task is a read-only source support verification task:
`TASK_CAPITAL_CHRONICLE_JAPAN_FX_LIQUIDITY_SOURCE_SUPPORT_VERIFICATION_V0`

This task will verify official source contracts and JGB/FX proxy data mappings before any ingestion or drafting is initiated.

## Downstream Article Draft Guidance
Until database gaps are resolved:
1. Downstream article drafts **MUST NOT** be created.
2. `article_draft_blocked` remains `true` and `article_draft_allowed_as_candidate_only` remains `false`.
3. No dispatch or publishing is authorized.
"""

    # 6. Generate run evidence
    run_evidence = {
        "classification": CLASSIFICATION_NORMAL,
        "task_label": TASK_LABEL,
        "baseline_head": "911a970ea5b8f619d931b7ae35fcf27425ee478f",
        "source_step3_packet": str(packet_path),
        "article_draft_blocked": True,
        "main_repo_mutated": False,
        "external_fetch_performed": False,
        "no_article_draft_confirmation": True,
        "no_media_confirmation": True,
        "no_platform_write_confirmation": True,
        "no_dispatch_confirmation": True,
        "no_raw_secret_read_confirmation": True,
        "output_paths": {
            "support_gap_repair_plan_json": str(output_path / "support_gap_repair_plan_v0.json"),
            "support_gap_repair_plan_md": str(output_path / "support_gap_repair_plan_v0.md"),
            "next_database_tasks": str(output_path / "next_database_tasks_v0.json"),
            "run_evidence": str(output_path / "run_evidence_v0.json")
        },
        "blockers": []
    }

    # Write files
    with open(output_path / "support_gap_repair_plan_v0.json", "w", encoding="utf-8") as f:
        json.dump(support_gap_repair_plan, f, indent=2, ensure_ascii=False)

    with open(output_path / "support_gap_repair_plan_v0.md", "w", encoding="utf-8") as f:
        f.write(summary_memo)

    with open(output_path / "next_database_tasks_v0.json", "w", encoding="utf-8") as f:
        json.dump(next_database_tasks, f, indent=2, ensure_ascii=False)

    with open(output_path / "run_evidence_v0.json", "w", encoding="utf-8") as f:
        json.dump(run_evidence, f, indent=2, ensure_ascii=False)

    # Generate README.md
    readme_content = """# Step 3b: Daily Database Support Gap Repair Plan

This directory contains the outputs of the Gap Repair Planning phase.
Its purpose is to define the exact next tasks required to verify and populate the main database repository with necessary JGB/FX/Liquidity series.
"""
    with open(output_path / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    return {
        "plan": support_gap_repair_plan,
        "summary": summary_memo,
        "tasks": next_database_tasks,
        "evidence": run_evidence
    }
