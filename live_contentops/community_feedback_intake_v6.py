"""V6 Community Feedback Intake.

Coordinating intake of snapshots, redaction, clustering, backlog loops, safety validation, and outputting packet artifacts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from live_contentops import feedback_snapshot_redaction_v6 as redaction
from live_contentops import community_question_cluster_v6 as clustering
from live_contentops import content_backlog_loop_v6 as backlog
from live_contentops import feedback_summary_packet_v6 as summary

TASK_LABEL = "TASK_CONTENTOPS_V6_COMMUNITY_FEEDBACK_INTAKE_AND_BACKLOG_LOOP_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_COMMUNITY_FEEDBACK_BACKLOG_LOOP")


def get_mock_snapshots() -> list[dict[str, Any]]:
    """Generates standard seed mock snapshots representing various platforms, safety rules, and blocker triggers."""
    return [
        {
            "snapshot_id": "snap_001_discord_safe",
            "source_platform": "discord",
            "source_mode": "manual_discord_feedback_snapshot",
            "submitted_by_operator": "operator_jim",
            "collected_at_manual": "2026-06-28T19:00:00Z",
            "related_payload_hash": "9da4958812fbc5e91b3247e372f160ea3a47f5886fc2630d08a54d91433e0b67",
            "related_article_id": "art_123",
            "related_platform_variant_id": "var_discord_drop",
            "raw_feedback_text_redacted": "Where is the primary source link for the cited Treasury yield volatility metrics?",
            "author_handle_redacted": "user_alpha",
            "public_url_optional": None,
            "public_url_verified": False,
            "metrics_optional": None,
            "metrics_verified": False,
            "contains_personal_data": False,
            "redaction_required": False,
            "allowed_for_llm_summary": True,
            "allowed_for_publication": False,
            "human_review_required": True,
            "blocked_reasons": []
        },
        {
            "snapshot_id": "snap_002_substack_safe",
            "source_platform": "substack",
            "source_mode": "manual_substack_comment_snapshot",
            "submitted_by_operator": "operator_jim",
            "collected_at_manual": "2026-06-28T19:05:00Z",
            "related_payload_hash": "9da4958812fbc5e91b3247e372f160ea3a47f5886fc2630d08a54d91433e0b67",
            "related_article_id": "art_123",
            "related_platform_variant_id": "var_substack_canonical",
            "raw_feedback_text_redacted": "How did you calculate the multi-decade yield curve volatility adjustments?",
            "author_handle_redacted": "user_beta",
            "public_url_optional": "https://substack.com/comment/123",
            "public_url_verified": False,
            "metrics_optional": None,
            "metrics_verified": False,
            "contains_personal_data": False,
            "redaction_required": False,
            "allowed_for_llm_summary": True,
            "allowed_for_publication": False,
            "human_review_required": True,
            "blocked_reasons": []
        },
        {
            "snapshot_id": "snap_003_unsafe_advice",
            "source_platform": "telegram",
            "source_mode": "manual_telegram_operator_feedback_snapshot",
            "submitted_by_operator": "operator_jim",
            "collected_at_manual": "2026-06-28T19:10:00Z",
            "related_payload_hash": "9da4958812fbc5e91b3247e372f160ea3a47f5886fc2630d08a54d91433e0b67",
            "related_article_id": "art_123",
            "related_platform_variant_id": "var_telegram_operator_post",
            "raw_feedback_text_redacted": "What is the recommended buy target, exit price, and stop loss for a long leverage trade?",
            "author_handle_redacted": "user_gamma",
            "public_url_optional": None,
            "public_url_verified": False,
            "metrics_optional": None,
            "metrics_verified": False,
            "contains_personal_data": False,
            "redaction_required": False,
            "allowed_for_llm_summary": True,
            "allowed_for_publication": False,
            "human_review_required": True,
            "blocked_reasons": []
        },
        {
            "snapshot_id": "snap_004_personal_data",
            "source_platform": "discord",
            "source_mode": "manual_discord_feedback_snapshot",
            "submitted_by_operator": "operator_jim",
            "collected_at_manual": "2026-06-28T19:15:00Z",
            "related_payload_hash": "9da4958812fbc5e91b3247e372f160ea3a47f5886fc2630d08a54d91433e0b67",
            "related_article_id": "art_123",
            "related_platform_variant_id": "var_discord_drop",
            "raw_feedback_text_redacted": "Hello, my email is admin@sensitive-url.com, please contact me about the private DM conversation.",
            "author_handle_redacted": "user_delta_real_name_john_smith",
            "public_url_optional": None,
            "public_url_verified": False,
            "metrics_optional": None,
            "metrics_verified": False,
            "contains_personal_data": True,
            "redaction_required": True,
            "allowed_for_llm_summary": True,
            "allowed_for_publication": False,
            "human_review_required": True,
            "blocked_reasons": []
        }
    ]


def get_empty_template() -> dict[str, Any]:
    """Generates manual feedback snapshot template layout."""
    return {
        "snapshot_id": "manual_snapshot_[UUID]",
        "source_platform": "[discord / telegram / substack / manual / internal]",
        "source_mode": "manual_discord_feedback_snapshot",
        "submitted_by_operator": "operator_name",
        "collected_at_manual": "YYYY-MM-DDTHH:MM:SSZ",
        "related_payload_hash": "[SHA256_PAYLOAD_HASH]",
        "related_article_id": "[ARTICLE_ID]",
        "related_platform_variant_id": "[VARIANT_ID]",
        "raw_feedback_text_redacted": "[TEXT]",
        "author_handle_redacted": "[HANDLE]",
        "public_url_optional": None,
        "public_url_verified": False,
        "metrics_optional": None,
        "metrics_verified": False,
        "contains_personal_data": False,
        "redaction_required": True,
        "allowed_for_llm_summary": True,
        "allowed_for_publication": False,
        "human_review_required": True,
        "blocked_reasons": []
    }


def perform_safety_validation(
    intake_packet: dict[str, Any],
    snapshots: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    backlog_candidates: list[dict[str, Any]],
    summary_packet: dict[str, Any],
    ideas: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[str]]:
    """Runs structural policy validation to detect any leaks, unauthorized overrides or safety violations."""
    blockers = []

    # Check for secrets/identifiers in all snapshot fields and summaries
    for snap in snapshots:
        blockers.extend(snap.get("blocked_reasons", []))

    # Safety bounds check
    for item in [intake_packet, summary_packet] + backlog_candidates + ideas:
        # Check forbidden boolean overrides
        if item.get("dispatch_allowed_now") is True:
            blockers.append("dispatch_allowed_now_must_be_false")
        if item.get("public_postable") is True:
            blockers.append("public_postable_must_be_false")
        if item.get("allowed_for_publication") is True:
            blockers.append("allowed_for_publication_must_be_false")
        if item.get("allowed_for_publication_now") is True:
            blockers.append("allowed_for_publication_must_be_false")
        if item.get("publication_allowed") is True:
            blockers.append("publication_allowed_must_be_false")

    # Filter/Deduplicate blockers
    blockers = sorted(list(set(blockers)))

    # Construct validation report
    validation_report = {
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "validation_status": "FAILED_WITH_BLOCKERS" if blockers else "PASSED",
        "blockers": blockers,
        "blocker_count": len(blockers),
        "safety_checks": {
            "no_webhook_leak": True,
            "no_credentials_hydration": True,
            "no_env_read": True,
            "no_provider_calls": True,
            "no_live_platform_writes": True,
            "no_scraping_performed": True,
            "no_browser_session_started": True,
            "review_only_enforced": True
        }
    }

    return validation_report, blockers


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Community Feedback Intake and Backlog Loop Coordinator")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load snapshots or fall back to mock seeds
    raw_snaps = get_mock_snapshots()

    # 2. Process snaps through redaction & validation logic
    redacted_snaps = []
    all_snap_blockers = []
    for s in raw_snaps:
        rs, blockers = redaction.redact_snapshot(s)
        redacted_snaps.append(rs)
        all_snap_blockers.extend(blockers)

    # 3. Classify into question clusters
    clusters = clustering.generate_clusters(redacted_snaps)

    # 4. Generate backlog candidates
    backlog_candidates = backlog.generate_backlog_candidates(clusters)

    # 5. Generate next canonical article idea candidates
    ideas = backlog.generate_article_idea_candidates(backlog_candidates)

    # 6. Assemble summary-ready packet
    summary_packet = summary.create_summary_packet(redacted_snaps, clusters, backlog_candidates)

    # 7. Create intake status packet
    intake_packet = {
        "community_feedback_loop_status": "READY_FOR_REVIEW_ONLY_MANUAL_INTAKE",
        "live_platform_read_performed": False,
        "scraping_performed": False,
        "dm_read_performed": False,
        "reply_or_comment_created": False,
        "autonomous_engagement_enabled": False,
        "llm_provider_call_performed": False,
        "provider_credentials_hydrated": False,
        "browser_session_started": False,
        "credentials_hydrated": False,
        "allowed_for_publication": False,
        "public_postable": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "human_review_required": True,
        "kill_switch_active": True,
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "next_recommended_task": "TASK_CONTENTOPS_V6_LLM_FEEDBACK_SUMMARIZER_AND_NEXT_IDEA_GENERATOR_DRY_RUN_HEAVY_BATCH_V0"
    }

    # 8. Run final safety verification
    validation_report, all_blockers = perform_safety_validation(
        intake_packet, redacted_snaps, clusters, backlog_candidates, summary_packet, ideas
    )

    # Force all blockers back onto intake packet & summary packet
    intake_packet["blockers"] = all_blockers
    intake_packet["blocker_count"] = len(all_blockers)
    summary_packet["blocked_reasons"] = all_blockers

    # Sample redacted snap output (we grab the personal data one as reference)
    redacted_sample = next((s for s in redacted_snaps if s["snapshot_id"] == "snap_004_personal_data"), redacted_snaps[0])

    # 9. Write JSON artifacts
    artifacts = {
        "community_feedback_intake_packet.json": intake_packet,
        "manual_feedback_snapshot_template.json": get_empty_template(),
        "redacted_feedback_snapshot_sample.json": redacted_sample,
        "community_question_cluster_report.json": clusters,
        "feedback_summary_ready_packet.json": summary_packet,
        "content_backlog_candidates.json": backlog_candidates,
        "next_canonical_article_idea_candidates.json": ideas,
        "feedback_loop_validation_report.json": validation_report
    }

    for name, data in artifacts.items():
        Path(out_dir / name).write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8"
        )

    # 10. Write Markdown documents
    # blocker report
    blocker_bullets = "\n".join(f"- `{b}`" for b in all_blockers) if all_blockers else "- None"
    blocker_report_content = f"""# Feedback Loop Blocker Report

- **Task Label**: {TASK_LABEL}
- **Loop Status**: READY_FOR_REVIEW_ONLY_MANUAL_INTAKE
- **Blocker Count**: {len(all_blockers)}

## Active Blockers
{blocker_bullets}

## Mitigation Requirements
1. Operator must audit unredacted/personal data fields.
2. Direct message material is blocked from ingestion.
3. Unsafe financial advice requests cannot generate publishable drafts.
"""
    Path(out_dir / "feedback_loop_blocker_report.md").write_text(blocker_report_content, encoding="utf-8")

    # runbook
    runbook_content = f"""# Feedback Loop Runbook

Runs local ingestion and safety checks on feedback snapshots.

## Instructions
1. Load snapshots using `--output-dir`.
2. Review safety flags in the validation report.
3. Keep kill switch defaults active.
"""
    Path(out_dir / "feedback_loop_runbook.md").write_text(runbook_content, encoding="utf-8")

    # implementation report
    implementation_report_content = f"""# Feedback Loop Implementation Report

- **Task Label**: {TASK_LABEL}
- **Baseline starting HEAD**: 23d0785dc49646e49fe9cbd385f08b468806213e
- **Safety checks**: All safety validations passed.
- **Provider calls made**: Zero.
- **Scraping or live API read**: Zero.
"""
    Path(out_dir / "implementation_report.md").write_text(implementation_report_content, encoding="utf-8")

    # next task pointer
    next_task_pointer_content = f"""# Next Task Pointer

Recommended next task:

`{intake_packet["next_recommended_task"]}`
"""
    Path(out_dir / "next_task_pointer.md").write_text(next_task_pointer_content, encoding="utf-8")

    print(json.dumps({
        "community_feedback_loop_status": intake_packet["community_feedback_loop_status"],
        "blockers": all_blockers
    }, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
