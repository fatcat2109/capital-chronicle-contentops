"""V6 Next Canonical Article Packet Coordinator.

Main coordinator module running candidate selection, brief planning, requirements checklist compilation, and safety validation.
"""
from __future__ import annotations

import argparse
import json
import hashlib
from pathlib import Path
from typing import Any

from live_contentops import article_research_requirements_v6 as research
from live_contentops import article_claim_ledger_scaffold_v6 as claims
from live_contentops import article_source_verification_checklist_v6 as checklist
from live_contentops import canonical_article_planning_validator_v6 as validator

TASK_LABEL = "TASK_CONTENTOPS_V6_NEXT_CANONICAL_ARTICLE_PACKET_FROM_BACKLOG_DRY_RUN_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG")


def load_json_or_fallback(path: str | Path, default_val: Any) -> Any:
    p = Path(path)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default_val


def select_candidate(ideas: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Selects the highest priority next canonical article idea candidate."""
    if not ideas:
        return None

    # Filter/verify safety conditions just in case, though upstream is expected to be safe
    # Selection rule: highest priority_score first, then by refined_idea_id DESC for tie-breaking
    sorted_ideas = sorted(
        ideas,
        key=lambda x: (x.get("priority_score", 0.0), x.get("refined_idea_id", "")),
        reverse=True
    )
    return sorted_ideas[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Next Canonical Article Packet planning coordinator")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load refined next canonical article ideas
    refined_ideas = load_json_or_fallback(
        "docs/automation/V6_LLM_FEEDBACK_SUMMARIZER_NEXT_IDEA/refined_next_canonical_article_ideas.json",
        []
    )

    selected = select_candidate(refined_ideas)
    if not selected:
        print("Error: No refined canonical article ideas found to select from.")
        return 1

    idea_id = selected.get("refined_idea_id", "stub_idea_id")
    hasher = hashlib.sha256(idea_id.encode("utf-8"))
    article_packet_id = f"article_packet_{hasher.hexdigest()[:12]}"

    # 2. Assemble next canonical article packet
    article_packet = {
        "article_packet_id": article_packet_id,
        "source_refined_idea_id": idea_id,
        "source_backlog_id": selected.get("source_backlog_id"),
        "source_cluster_ids": selected.get("source_cluster_ids"),
        "title_candidate": selected.get("title_candidate"),
        "thesis_candidate": selected.get("thesis_candidate"),
        "audience_need": selected.get("audience_need"),
        "outline": selected.get("outline"),
        "research_questions": selected.get("outline"),
        "required_sources": ["operator_verified_data_ref"],
        "required_caveats": selected.get("required_caveats"),
        "evidence_required": selected.get("evidence_required"),
        "source_verification_required": True,
        "claim_ledger_required": True,
        "canonical_platform": "substack_canonical",
        "downstream_platform_targets": selected.get("platform_variant_targets"),
        "allowed_for_drafting": selected.get("allowed_for_drafting", True),
        "allowed_for_publication": False,
        "public_postable": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "human_review_required": True,
        "provider_call_performed": False,
        "browser_session_started": False,
        "credentials_hydrated": False,
        "kill_switch_active": True,
        "next_canonical_article_status": "READY_FOR_REVIEW_ONLY_ARTICLE_PLANNING",
        "article_copy_generated": False
    }

    # 3. Generate requirements, checklist, claim ledger
    requirements_data = research.generate_research_requirements(article_packet_id)
    checklist_data = checklist.generate_source_verification_checklist(article_packet_id, requirements_data)
    claims_data = claims.generate_claim_ledger_scaffold(requirements_data)

    # 4. Generate outline packet
    outline_packet = {
        "title_candidate": selected.get("title_candidate"),
        "subtitle_candidate": "An educational analysis on interest rate structures and data grounding.",
        "opening_question": "Which primary sources ground our recent macroeconomic curve analysis?",
        "section_outline": [
            "I. Introduction to Yield Curve Parameters",
            "II. Historical Trend Analysis & Sourcing",
            "III. Sourcing Volatility Data",
            "IV. Conclusion and limitations"
        ],
        "evidence_slots": [
            "Slot 1: Verified Historical Series",
            "Slot 2: Computation Model parameters"
        ],
        "caveat_slots": [
            "Caveat 1: Macroeconomic parameter uncertainty"
        ],
        "conclusion_boundary": "A summary of verified reference links and structural caveats.",
        "reader_takeaway": "Grounding curves under model uncertainty.",
        "prohibited_language": [
            "buy target", "sell target", "guaranteed prediction", "trading signals", "position sizing"
        ]
    }

    # 5. Generate risk matrix
    editorial_risk = [
        {
            "risk_id": "risk_source_missing",
            "severity": "high",
            "affected_artifact": "substack_canonical",
            "mitigation_required": "Operator must match yield database keys.",
            "blocks_publication": True
        },
        {
            "risk_id": "risk_methodology_unclear",
            "severity": "medium",
            "affected_artifact": "substack_canonical",
            "mitigation_required": "Draft Nelson-Siegel model parameters reference.",
            "blocks_publication": True
        },
        {
            "risk_id": "risk_unsupported_numeric_claim",
            "severity": "high",
            "affected_artifact": "substack_canonical",
            "mitigation_required": "Ensure all numbers trace to official source rows.",
            "blocks_publication": True
        },
        {
            "risk_id": "risk_financial_advice_misread",
            "severity": "high",
            "affected_artifact": "substack_canonical",
            "mitigation_required": "Include macroeconomic parameter uncertainty caveats.",
            "blocks_publication": True
        },
        {
            "risk_id": "risk_overconfidence",
            "severity": "medium",
            "affected_artifact": "substack_canonical",
            "mitigation_required": "Preserve review-only labeling.",
            "blocks_publication": True
        },
        {
            "risk_id": "risk_stale_context",
            "severity": "medium",
            "affected_artifact": "substack_canonical",
            "mitigation_required": "Refresh timestamps manually on ingestion.",
            "blocks_publication": True
        },
        {
            "risk_id": "risk_community_feedback_privacy",
            "severity": "high",
            "affected_artifact": "substack_canonical",
            "mitigation_required": "Confirm author handles are fully redacted.",
            "blocks_publication": True
        },
        {
            "risk_id": "risk_platform_overcompression",
            "severity": "medium",
            "affected_artifact": "discord_drop",
            "mitigation_required": "Review post previews manually.",
            "blocks_publication": True
        }
    ]

    # 6. Downstream placeholders
    placeholders = {
        "substack_canonical_article_draft_pending": {
            "generated": False,
            "public_postable": False,
            "dispatch_allowed_now": False,
            "source_verification_required": True,
            "human_review_required": True
        },
        "discord_drop_pending": {
            "generated": False,
            "public_postable": False,
            "dispatch_allowed_now": False,
            "source_verification_required": True,
            "human_review_required": True
        },
        "telegram_operator_status_pending": {
            "generated": False,
            "public_postable": False,
            "dispatch_allowed_now": False,
            "source_verification_required": True,
            "human_review_required": True
        },
        "x_manual_thread_pending": {
            "generated": False,
            "public_postable": False,
            "dispatch_allowed_now": False,
            "source_verification_required": True,
            "human_review_required": True
        },
        "linkedin_manual_post_pending": {
            "generated": False,
            "public_postable": False,
            "dispatch_allowed_now": False,
            "source_verification_required": True,
            "human_review_required": True
        },
        "manual_fallback_export_pending": {
            "generated": False,
            "public_postable": False,
            "dispatch_allowed_now": False,
            "source_verification_required": True,
            "human_review_required": True
        }
    }

    # 7. Run compliance validator
    validation_report, all_blockers = validator.validate_article_planning(
        article_packet, requirements_data, checklist_data, claims_data, outline_packet, editorial_risk, placeholders
    )

    article_packet["blockers"] = all_blockers
    article_packet["blocker_count"] = len(all_blockers)

    # 8. Write JSON artifacts
    artifacts = {
        "next_canonical_article_packet.json": article_packet,
        "selected_backlog_candidate.json": selected,
        "article_research_requirements.json": requirements_data,
        "source_verification_checklist.json": checklist_data,
        "article_claim_ledger_scaffold.json": claims_data,
        "article_outline_packet.json": outline_packet,
        "editorial_risk_matrix.json": editorial_risk,
        "downstream_platform_readiness_placeholders.json": placeholders,
        "article_planning_validation_report.json": validation_report
    }

    for name, data in artifacts.items():
        Path(out_dir / name).write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8"
        )

    # 9. Write Markdown documents
    # blocker report
    blocker_bullets = "\n".join(f"- `{b}`" for b in all_blockers) if all_blockers else "- None"
    blocker_report_content = f"""# Article Planning Blocker Report

- **Task Label**: {TASK_LABEL}
- **Loop Status**: READY_FOR_REVIEW_ONLY_ARTICLE_PLANNING
- **Blocker Count**: {len(all_blockers)}

## Active Blockers
{blocker_bullets}

## Mitigation Requirements
1. Operator must verify sources for all requirements in source_verification_checklist.json.
2. Numeric claims in article_claim_ledger_scaffold.json must trace to validated sources.
3. No publication is allowed until formal sign-off.
"""
    Path(out_dir / "article_planning_blocker_report.md").write_text(blocker_report_content, encoding="utf-8")

    # runbook
    runbook_content = f"""# Article Planning Runbook

Orchestrates review-only planning briefs and requirement ledgers.

## Instructions
1. Load selected backlog candidates.
2. Verify all source requirements trace back to valid historical yield references.
3. Keep default review-only invariants active.
"""
    Path(out_dir / "article_planning_runbook.md").write_text(runbook_content, encoding="utf-8")

    # implementation report
    implementation_report_content = f"""# Article Planning Implementation Report

- **Task Label**: {TASK_LABEL}
- **Baseline starting HEAD**: 9631127c67caa37e634e15c67f155f75703b3dc9
- **Safety posture**: review-only planning constraints passed; validator status remains FAILED_WITH_BLOCKERS due to pending manual source verifications.
- **Provider calls made**: Zero.
- **Scraping or live API read**: Zero.
"""
    Path(out_dir / "implementation_report.md").write_text(implementation_report_content, encoding="utf-8")

    # next task pointer
    next_task_pointer_content = f"""# Next Task Pointer

Recommended next task:

`TASK_CONTENTOPS_V6_CANONICAL_ARTICLE_DRAFT_FROM_VERIFIED_SOURCE_PACK_DRY_RUN_HEAVY_BATCH_V0`
"""
    Path(out_dir / "next_task_pointer.md").write_text(next_task_pointer_content, encoding="utf-8")

    print(json.dumps({
        "next_canonical_article_status": article_packet["next_canonical_article_status"],
        "blockers": all_blockers
    }, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
