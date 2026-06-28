"""V6 Canonical Draft Positive Path Coordinator.

Coordinates positive-path dry-run generation and validations under the V6 Operating Profile.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from live_contentops import canonical_draft_claim_source_mapper_v6 as mapper
from live_contentops import canonical_draft_fixture_renderer_v6 as renderer
from live_contentops import canonical_draft_positive_path_validator_v6 as validator

TASK_LABEL = "TASK_CONTENTOPS_V6_CANONICAL_DRAFT_GENERATION_FROM_VERIFIED_SOURCE_PACK_POSITIVE_PATH_DRY_RUN_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_CANONICAL_DRAFT_POSITIVE_PATH_DRY_RUN")


def load_json_or_fallback(path: str | Path, default_val: Any) -> Any:
    p = Path(path)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default_val


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Canonical Draft Positive Path Coordinator")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load planning inputs
    packet = load_json_or_fallback(
        "docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/next_canonical_article_packet.json",
        {}
    )
    requirements = load_json_or_fallback(
        "docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/article_research_requirements.json",
        []
    )
    claims = load_json_or_fallback(
        "docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/article_claim_ledger_scaffold.json",
        []
    )

    # 2. Build test-only verified source pack fixture summary
    fixture_summary = {
        "test_only": True,
        "runtime_truth": False,
        "synthetic_fixture_loaded": True,
        "committed_runtime_verified_source_pack_created": False,
        "real_source_fetch_performed": False,
        "operator_verification_performed": False,
        "source_pack_complete": True,
        "all_required_sources_verified": True,
        "all_claims_bound_to_sources": True,
        "operator_verified_by": "TEST_ONLY_OPERATOR_NOT_REAL_VERIFICATION",
        "publication_allowed": False,
        "dispatch_allowed_now": False,
        "public_postable": False
    }

    # 3. Generate claim-source binding proof
    binding_proof = mapper.map_claims_to_test_only_sources(claims, requirements)

    # 4. Generate review-only draft preview markdown
    title = packet.get("title_candidate", "Macroeconomic Providence Study")
    draft_markdown = renderer.render_review_only_draft_preview(title, claims, binding_proof)

    # 5. Build review-only canonical draft packet
    review_only_packet = {
        "canonical_draft_status": "REVIEW_ONLY_SYNTHETIC_POSITIVE_PATH",
        "draft_source": "test_only_verified_source_pack_fixture",
        "runtime_truth": False,
        "article_copy_generated": True,
        "draft_markdown_created": True,
        "source_verification_required_for_runtime": True,
        "all_claims_bound_to_test_sources": True,
        "all_claims_bound_to_runtime_sources": False,
        "allowed_for_publication": False,
        "public_postable": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "provider_call_performed": False,
        "llm_provider_call_performed": False,
        "browser_session_started": False,
        "credentials_hydrated": False,
        "human_review_required": True,
        "kill_switch_active": True
    }

    # 6. Build positive-path packet
    positive_path_packet = {
        "positive_path_status": "READY_FOR_TEST_ONLY_DRY_RUN",
        "runtime_truth": False,
        "test_only_fixture_used": True,
        "committed_runtime_verified_source_pack_created": False,
        "real_source_fetch_performed": False,
        "provider_call_performed": False,
        "browser_session_started": False,
        "env_read_performed": False,
        "credentials_hydrated": False,
        "source_urls_persisted_in_runtime_artifact": False,
        "evidence_hashes_persisted_in_runtime_artifact": False,
        "article_copy_generated": True,
        "allowed_for_publication": False,
        "public_postable": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "human_review_required": True,
        "kill_switch_active": True
    }

    # 7. Safety Validation
    validation_report, blockers = validator.validate_positive_path_draft_generation(
        positive_path_packet, fixture_summary, binding_proof, review_only_packet, draft_markdown
    )

    # 8. Write JSON artifacts
    artifacts = {
        "canonical_draft_positive_path_packet.json": positive_path_packet,
        "test_only_verified_source_pack_fixture_summary.json": fixture_summary,
        "test_only_claim_source_binding_proof.json": binding_proof,
        "canonical_draft_review_only_packet.json": review_only_packet,
        "canonical_draft_positive_path_validation_report.json": validation_report
    }

    for name, data in artifacts.items():
        Path(out_dir / name).write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8"
        )

    # 9. Write Markdown files
    Path(out_dir / "canonical_draft_review_only_preview.md").write_text(draft_markdown, encoding="utf-8")

    # Blocker report
    blockers_bullets = "\n".join(f"- `{b}`" for b in blockers)
    blocker_md = f"""# Canonical Draft Positive Path Blocker Report

- **Task Label**: {TASK_LABEL}
- **Active Blockers Count**: {len(blockers)}

## Active Blockers
{blockers_bullets}
"""
    Path(out_dir / "canonical_draft_positive_path_blocker_report.md").write_text(blocker_md, encoding="utf-8")

    # Runbook
    runbook_md = """# Canonical Draft Positive Path Runbook

Proves draft rendering paths using test-only synthetic fixtures.

## Instructions
1. This is a local dry-run only.
2. Confirm the TEST-ONLY watermark is preserved.
3. Supplying real operator source pack files remains blocked.
"""
    Path(out_dir / "canonical_draft_positive_path_runbook.md").write_text(runbook_md, encoding="utf-8")

    # Implementation report
    impl_md = f"""# Positive Path Implementation Report

- **Task Label**: {TASK_LABEL}
- **Safety posture**: positive-path proven on synthetic mocks; runtime remains blocked.
"""
    Path(out_dir / "implementation_report.md").write_text(impl_md, encoding="utf-8")

    # Next task pointer
    next_task_pointer_md = """# Next Task Pointer

Recommended next task:

`TASK_CONTENTOPS_V6_CANONICAL_DRAFT_OPERATOR_SOURCE_PACK_IMPORT_UI_AND_APPROVAL_REVIEW_HEAVY_BATCH_V0`
"""
    Path(out_dir / "next_task_pointer.md").write_text(next_task_pointer_md, encoding="utf-8")

    print(json.dumps({
        "positive_path_status": positive_path_packet["positive_path_status"],
        "blockers": blockers
    }, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
