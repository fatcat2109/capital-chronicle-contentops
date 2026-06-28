"""V6 Verified Source Pack Revalidation Handler.

Executes local-only dry-run passes over imported packs, generating verification gate reports.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from live_contentops import source_pack_claim_binding_revalidator_v6 as binding_revalidator
from live_contentops import verified_source_pack_fixture_factory_v6 as positive_factory
from live_contentops import verified_source_pack_import_v6 as import_handler

TASK_LABEL = "TASK_CONTENTOPS_V6_VERIFIED_SOURCE_PACK_IMPORT_AND_REVALIDATION_DRY_RUN_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_VERIFIED_SOURCE_PACK_IMPORT_REVALIDATION")


def run_gate_revalidation(
    source_pack: dict[str, Any],
    all_bound: bool,
    blockers: list[str]
) -> dict[str, Any]:
    """Re-runs the canonical draft gate logic over the imported pack status."""
    gate_status = "BLOCKED_MISSING_VERIFIED_SOURCE_PACK"
    draft_copy_generation_allowed = False
    publication_allowed = False

    # Check if there are any blocking verification requirements
    verification_blockers = [
        "source_url_missing", "evidence_hash_missing", "retrieved_at_missing",
        "operator_signature_missing", "source_excerpt_ref_missing", "source_verification_required",
        "operator_source_pack_missing", "verified_source_pack_missing"
    ]
    has_verification_blockers = any(b in blockers for b in verification_blockers)

    if source_pack.get("source_pack_complete") is True and all_bound and not has_verification_blockers:
        gate_status = "PASSED_VERIFIED_SOURCE_PACK_VALID"
        draft_copy_generation_allowed = True
        publication_allowed = False  # Held by fast ship operator constraints

    return {
        "schema_version": "6.0.0",
        "gate_status": gate_status,
        "source_pack_complete": source_pack.get("source_pack_complete", False),
        "all_required_sources_verified": source_pack.get("all_required_sources_verified", False),
        "all_claims_bound_to_sources": all_bound,
        "draft_copy_generation_allowed": draft_copy_generation_allowed,
        "publication_allowed": publication_allowed,
        "human_research_required": True,
        "allowed_for_publication": False,
        "public_postable": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "blockers": blockers
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Verified Source Pack Import and Revalidation")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load claims scaffold
    claim_scaffold = []
    scaffold_path = Path("docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/article_claim_ledger_scaffold.json")
    if scaffold_path.exists():
        try:
            claim_scaffold = json.loads(scaffold_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # 2. Build template and default validation reports (Default blocked state)
    import_template = import_handler.make_operator_source_pack_import_template()
    import_report, default_blockers = import_handler.validate_imported_source_pack(import_template)

    # Re-run claim binding
    binding_report, all_bound = binding_revalidator.revalidate_source_claim_binding(
        import_template,
        claim_scaffold
    )

    # Re-run draft gate
    gate_report = run_gate_revalidation(import_template, all_bound, default_blockers)

    # Generate synthetic positive test-only fixture
    positive_pack = positive_factory.make_test_only_positive_verified_source_pack()
    pos_import_report, pos_blockers = import_handler.validate_imported_source_pack(positive_pack)
    pos_binding_report, pos_all_bound = binding_revalidator.revalidate_source_claim_binding(
        positive_pack,
        claim_scaffold
    )
    pos_gate_report = run_gate_revalidation(positive_pack, pos_all_bound, pos_blockers)

    pos_fixture_summary = {
        "test_only": True,
        "runtime_truth": False,
        "synthetic_fixture_loaded": True,
        "committed_runtime_verified_source_pack_created": False,
        "real_source_fetch_performed": False,
        "operator_verification_performed": False,
        "source_urls_persisted_in_runtime_artifact": False,
        "evidence_hashes_persisted_in_runtime_artifact": False,
        "positive_path_unit_test_only": True,
        "publication_allowed": False,
        "dispatch_allowed_now": False,
        "public_postable": False,
        "pos_blockers_count": len(pos_blockers),
        "pos_blockers": pos_blockers,
        "pos_all_claims_bound": pos_all_bound,
        "pos_gate_status": pos_gate_report["gate_status"],
        "draft_generation_possible_on_this_fixture": pos_gate_report["draft_copy_generation_allowed"]
    }

    # 3. Assemble Import packet
    import_packet = {
        "verified_source_pack_import_status": "READY_FOR_REVIEW_ONLY_IMPORT_DRY_RUN",
        "real_source_fetch_performed": False,
        "browser_session_started": False,
        "env_read_performed": False,
        "provider_call_performed": False,
        "credentials_hydrated": False,
        "allowed_for_publication": False,
        "public_postable": False,
        "dispatch_allowed_now": False,
        "human_review_required": True,
        "source_verification_required": True,
        "kill_switch_active": True
    }

    # 4. Write JSON artifacts
    artifacts = {
        "verified_source_pack_import_packet.json": import_packet,
        "operator_source_pack_import_template.json": import_template,
        "verified_source_pack_import_validation_report.json": import_report,
        "source_pack_claim_binding_revalidation_report.json": binding_report,
        "canonical_draft_gate_revalidation_report.json": gate_report,
        "test_only_positive_fixture_report.json": pos_fixture_summary
    }

    for name, data in artifacts.items():
        Path(out_dir / name).write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8"
        )

    # 5. Write Markdown files
    # blocker report
    blockers_bullets = "\n".join(f"- `{b}`" for b in default_blockers)
    blockers_md = f"""# Verified Source Pack Import Blocker Report

- **Task Label**: {TASK_LABEL}
- **Active Blockers Count**: {len(default_blockers)}

## Active Blockers
{blockers_bullets}
"""
    Path(out_dir / "verified_source_pack_import_blocker_report.md").write_text(blockers_md, encoding="utf-8")

    # runbook
    runbook_md = """# Verified Source Pack Import Runbook

Instructions for loading verified source pack artifacts.

1. Ensure manual operator verification is completed.
2. Supply manual JSON files matching operator_source_pack_import_template.json.
3. Validate and map claims without any remote browser/network connection.
"""
    Path(out_dir / "verified_source_pack_import_runbook.md").write_text(runbook_md, encoding="utf-8")

    # implementation
    impl_md = f"""# Verified Source Pack Import Implementation Report

- **Task Label**: {TASK_LABEL}
- **Safety posture**: offline import templates initialized; revalidation gate status remains BLOCKED.
"""
    Path(out_dir / "implementation_report.md").write_text(impl_md, encoding="utf-8")

    # next task pointer
    next_pointer = """# Next Task Pointer

Recommended next task:

`TASK_CONTENTOPS_V6_CANONICAL_DRAFT_GENERATION_FROM_VERIFIED_SOURCE_PACK_POSITIVE_PATH_DRY_RUN_HEAVY_BATCH_V0`
"""
    Path(out_dir / "next_task_pointer.md").write_text(next_pointer, encoding="utf-8")

    print(json.dumps({
        "verified_source_pack_import_status": import_packet["verified_source_pack_import_status"],
        "default_blockers": default_blockers
    }, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
