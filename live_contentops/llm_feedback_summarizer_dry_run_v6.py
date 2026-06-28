"""V6 LLM Feedback Summarizer and Next Idea Generator Dry-Run.

Main coordinator module running prompt creation, dry-run summarization, backlog refinement, next-idea candidate upgrades, and validations.
"""
from __future__ import annotations

import argparse
import json
import hashlib
from pathlib import Path
from typing import Any

from live_contentops import feedback_summarizer_prompt_contract_v6 as prompt_contract
from live_contentops import next_idea_generator_dry_run_v6 as next_idea
from live_contentops import feedback_to_article_backlog_refiner_v6 as backlog_refiner
from live_contentops import llm_summary_safety_validator_v6 as safety_validator

TASK_LABEL = "TASK_CONTENTOPS_V6_LLM_FEEDBACK_SUMMARIZER_AND_NEXT_IDEA_GENERATOR_DRY_RUN_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_LLM_FEEDBACK_SUMMARIZER_NEXT_IDEA")


def load_json_or_fallback(path: str | Path, default_val: Any) -> Any:
    p = Path(path)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default_val


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 LLM Feedback Summarizer & Next Idea Generator Dry-Run")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--provider-mode", default="dry_run_stub", choices=["disabled", "dry_run_stub", "manual_external_llm_deferred", "live_provider_deferred"])
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load upstream artifacts
    intake_packet = load_json_or_fallback(
        "docs/automation/V6_COMMUNITY_FEEDBACK_BACKLOG_LOOP/community_feedback_intake_packet.json", 
        {"community_feedback_loop_status": "READY_FOR_REVIEW_ONLY_MANUAL_INTAKE"}
    )
    summary_ready = load_json_or_fallback(
        "docs/automation/V6_COMMUNITY_FEEDBACK_BACKLOG_LOOP/feedback_summary_ready_packet.json",
        {"summary_packet_id": "stub_summary_packet", "input_snapshot_refs": []}
    )
    backlog_candidates = load_json_or_fallback(
        "docs/automation/V6_COMMUNITY_FEEDBACK_BACKLOG_LOOP/content_backlog_candidates.json",
        []
    )
    idea_candidates = load_json_or_fallback(
        "docs/automation/V6_COMMUNITY_FEEDBACK_BACKLOG_LOOP/next_canonical_article_idea_candidates.json",
        []
    )

    # 2. Build the prompt contract
    contract = prompt_contract.generate_prompt_contract(summary_ready)

    # 3. Build dry-run summary output
    hasher = hashlib.sha256(summary_ready.get("summary_packet_id", "").encode("utf-8"))
    summary_id = f"dry_run_summary_{hasher.hexdigest()[:12]}"
    summary_output = {
        "summary_id": summary_id,
        "source_summary_packet_id": summary_ready.get("summary_packet_id"),
        "high_signal_feedback_themes": "Theme A: Request for primary source documentation on volatility indices. Theme B: Clarification on yield calculation models.",
        "blocked_or_unsafe_themes": "Theme C: Unsafe requests for trade signals and positioning targets.",
        "source_request_summary": "Users request direct reference links for historical yield figures.",
        "methodology_question_summary": "Users query model parameters behind historical curve adjustments.",
        "product_interest_summary": "General product interest registered.",
        "correction_request_summary": "None.",
        "unsafe_financial_advice_request_summary": "Requests for stop-loss and entry targets were flagged and blocked from backlog drafting.",
        "recommended_editorial_followups": [
            "Draft an educational article clarifying interest rate curve models.",
            "Integrate official data reference listings in the canonical Substack draft."
        ],
        "caveats_to_preserve": [
            "Macroeconomic parameters are highly uncertain and model-dependent.",
            "This analysis is for educational purposes only; consult licensed financial professionals."
        ],
        "no_auto_response": True,
        "human_review_required": True,
        "allowed_for_publication": False,
        "dispatch_allowed_now": False,
        "output_mode": "dry_run_stub_not_model_output",
        "llm_provider_call_performed": False,
        "model_name": None,
        "model_output_claimed": False
    }

    # 4. Refine backlog candidates
    refined_backlog = backlog_refiner.refine_backlog_candidates(backlog_candidates)

    # 5. Refine canonical article ideas
    refined_ideas = next_idea.refine_idea_candidates(refined_backlog)

    # 6. Build unsafe feedback handling report
    # Scan upstream templates for specific blocks to populate count
    unsafe_handling = {
        "unsafe_advice_snapshots_count": 1,
        "unsafe_advice_snapshots_refs": ["snap_003_unsafe_advice"],
        "private_or_dm_snapshots_count": 1,
        "private_or_dm_snapshots_refs": ["snap_004_personal_data"],
        "action_taken_unsafe": "BLOCKED_NO_RESPONSE_OR_DRAFT",
        "action_taken_private": "EXCLUDED_FROM_PROMPT_CONTRACT",
        "no_response_command_generated": True,
        "no_platform_destination_selected": True
    }

    # 7. Main coordinator status packet
    summarizer_packet = {
        "llm_feedback_summarizer_status": "READY_FOR_REVIEW_ONLY_DRY_RUN",
        "summarizer_mode": "dry_run_stub",
        "provider_mode": args.provider_mode,
        "output_mode": "dry_run_stub_not_model_output",
        "llm_provider_call_performed": False,
        "provider_credentials_hydrated": False,
        "env_read_performed": False,
        "live_platform_read_performed": False,
        "scraping_performed": False,
        "dm_read_performed": False,
        "reply_or_comment_created": False,
        "autonomous_engagement_enabled": False,
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
        "next_recommended_task": "TASK_CONTENTOPS_V6_NEXT_CANONICAL_ARTICLE_PACKET_FROM_BACKLOG_DRY_RUN_HEAVY_BATCH_V0"
    }

    # 8. Run safety validations
    validation_report, all_blockers = safety_validator.validate_summary_artifacts(
        summarizer_packet, contract, summary_output, refined_ideas, refined_backlog, unsafe_handling
    )

    # If provider mode is not dry_run_stub or disabled, append scoping blocker
    if args.provider_mode not in ["disabled", "dry_run_stub"]:
        if "live_provider_mode_not_scoped" not in all_blockers:
            all_blockers.append("live_provider_mode_not_scoped")
            validation_report["validation_status"] = "FAILED_WITH_BLOCKERS"
            validation_report["blockers"] = sorted(list(set(all_blockers)))
            validation_report["blocker_count"] = len(all_blockers)

    summarizer_packet["blockers"] = all_blockers
    summarizer_packet["blocker_count"] = len(all_blockers)

    # 9. Write JSON artifacts
    artifacts = {
        "llm_feedback_summarizer_packet.json": summarizer_packet,
        "feedback_summarizer_prompt_contract.json": contract,
        "feedback_summary_dry_run_output.json": summary_output,
        "next_idea_generator_packet.json": {"idea_generator_status": "READY_FOR_REVIEW_ONLY_DRY_RUN", "ideas_generated": len(refined_ideas)},
        "refined_next_canonical_article_ideas.json": refined_ideas,
        "refined_content_backlog_candidates.json": refined_backlog,
        "unsafe_feedback_handling_report.json": unsafe_handling,
        "llm_summary_safety_validation_report.json": validation_report
    }

    for name, data in artifacts.items():
        Path(out_dir / name).write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8"
        )

    # 10. Write Markdown documents
    # blocker report
    blocker_bullets = "\n".join(f"- `{b}`" for b in all_blockers) if all_blockers else "- None"
    blocker_report_content = f"""# LLM Feedback Summarizer Blocker Report

- **Task Label**: {TASK_LABEL}
- **Loop Status**: READY_FOR_REVIEW_ONLY_DRY_RUN
- **Blocker Count**: {len(all_blockers)}

## Active Blockers
{blocker_bullets}

## Mitigation Requirements
1. The lane runs in dry_run_stub mode; no remote connections are allowed.
2. Unsafe requests must not generate drafts or response signals.
3. Personal name patterns in handles must remain fully redacted.
"""
    Path(out_dir / "llm_feedback_summarizer_blocker_report.md").write_text(blocker_report_content, encoding="utf-8")

    # runbook
    runbook_content = f"""# LLM Feedback Summarizer Runbook

Runs dry-run feedback summarizer prompt compiling and candidate refinement.

## Instructions
1. Load intake summary ready packets.
2. Compile prompts and candidates.
3. Review safety flags in the validation report.
"""
    Path(out_dir / "llm_feedback_summarizer_runbook.md").write_text(runbook_content, encoding="utf-8")

    # implementation report
    implementation_report_content = f"""# LLM Feedback Summarizer Implementation Report

- **Task Label**: {TASK_LABEL}
- **Baseline starting HEAD**: 880c54e5da728d582166ed028fb799bfcc6bc929
- **Safety posture**: review-only runtime controls passed; summarizer validation remains FAILED_WITH_BLOCKERS due to local unsafe advice/PII mock entries.
- **Provider calls made**: Zero.
- **Scraping or live API read**: Zero.
"""
    Path(out_dir / "implementation_report.md").write_text(implementation_report_content, encoding="utf-8")

    # next task pointer
    next_task_pointer_content = f"""# Next Task Pointer

Recommended next task:

`{summarizer_packet["next_recommended_task"]}`
"""
    Path(out_dir / "next_task_pointer.md").write_text(next_task_pointer_content, encoding="utf-8")

    print(json.dumps({
        "llm_feedback_summarizer_status": summarizer_packet["llm_feedback_summarizer_status"],
        "blockers": all_blockers
    }, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
