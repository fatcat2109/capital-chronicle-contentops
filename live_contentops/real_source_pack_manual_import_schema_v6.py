"""V6 Real Source Pack Manual Import Schema Definition.

Defines structural fields for future operator-filled source entries and outputs schema files.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from live_contentops import real_source_pack_hash_review_v6 as hash_builder
from live_contentops import real_source_pack_manual_import_validator_v6 as validator
from live_contentops import real_source_pack_redaction_v6 as redaction_builder

TASK_LABEL = "TASK_CONTENTOPS_V6_REAL_SOURCE_PACK_MANUAL_IMPORT_FIXTURE_SCHEMA_AND_HASH_REVIEW_DRY_RUN_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_REAL_SOURCE_PACK_MANUAL_IMPORT_SCHEMA")


def get_source_entry_schema_fields() -> dict[str, str]:
    """Returns the name and type map of the redacted source entry schema fields."""
    return {
        "source_requirement_id": "string",
        "required_source_type": "string",
        "source_name_redacted": "string",
        "source_url_redacted": "string",
        "source_publisher_redacted": "string",
        "retrieval_method": "string",
        "retrieved_at_redacted": "string",
        "evidence_hash_present": "boolean",
        "evidence_hash_redacted": "string",
        "source_excerpt_ref_redacted": "string",
        "source_excerpt_text_redacted": "string",
        "source_supports_claim_ids": "array_of_strings",
        "operator_verified_by_redacted": "string",
        "verification_status": "string",
        "allowed_for_article_use": "boolean",
        "human_review_required": "boolean",
        "source_verification_required": "boolean",
        "redaction_status": "string",
        "raw_values_persisted": "boolean",
        "runtime_truth": "boolean"
    }


def make_blank_import_fixture() -> dict[str, Any]:
    """Creates a blank manual import fixture template with no real/fake evidence."""
    return {
        "import_fixture_status": "OPERATOR_MANUAL_SOURCE_PACK_REQUIRED",
        "runtime_truth": False,
        "real_source_pack_imported": False,
        "source_pack_complete": False,
        "all_required_sources_verified": False,
        "all_claims_bound_to_sources": False,
        "source_entries": [],
        "raw_values_persisted": False,
        "evidence_hash_present": False,
        "allowed_for_article_use": False,
        "canonical_draft_generation_allowed": False,
        "allowed_for_publication": False,
        "public_postable": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "provider_call_performed": False,
        "browser_session_started": False,
        "env_read_performed": False,
        "credentials_hydrated": False,
        "human_review_required": True,
        "kill_switch_active": True
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Real Source Pack Manual Import Coordinator")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate core artifacts
    schema_fields = get_source_entry_schema_fields()
    blank_fixture = make_blank_import_fixture()
    hash_review = hash_builder.make_hash_review_packet()
    policy = redaction_builder.make_redaction_policy()

    # 2. Validation report
    validation_report, blockers = validator.validate_real_source_pack_manual_import(
        blank_fixture, hash_review, policy
    )

    # 3. Write files
    artifacts = {
        "real_source_pack_manual_import_schema.json": schema_fields,
        "real_source_pack_manual_import_blank_fixture.json": blank_fixture,
        "real_source_pack_hash_review_packet.json": hash_review,
        "real_source_pack_redaction_policy.json": policy,
        "real_source_pack_manual_import_validation_report.json": validation_report
    }

    for name, data in artifacts.items():
        Path(out_dir / name).write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8"
        )

    # Markdown blocker report
    blocker_bullets = "\n".join(f"- `{b}`" for b in blockers)
    blocker_md = f"""# Real Source Pack Manual Import Blocker Report

- **Task Label**: {TASK_LABEL}
- **Active Blockers Count**: {len(blockers)}

## Active Blockers
{blocker_bullets}
"""
    Path(out_dir / "real_source_pack_manual_import_blocker_report.md").write_text(blocker_md, encoding="utf-8")

    # Runbook
    runbook_md = """# Real Source Pack Manual Import Runbook

Stages structural schema fields and hash reviews.

## Instructions
1. This is a local schema setup only.
2. Confirm the redaction policy rules.
3. No real source pack should be loaded or generated now.
"""
    Path(out_dir / "real_source_pack_manual_import_runbook.md").write_text(runbook_md, encoding="utf-8")

    # Implementation report
    impl_md = f"""# Manual Import Schema Implementation Report

- **Task Label**: {TASK_LABEL}
- **Safety posture**: offline schema structures verified; all runtime draft execution pathways remain locked.
"""
    Path(out_dir / "implementation_report.md").write_text(impl_md, encoding="utf-8")

    # Next task pointer
    next_task_pointer_md = """# Next Task Pointer

Recommended next task:

`TASK_CONTENTOPS_V6_REAL_SOURCE_PACK_OPERATOR_FILLED_REDACTED_FIXTURE_DRY_RUN_REVIEW_HEAVY_BATCH_V0`
"""
    Path(out_dir / "next_task_pointer.md").write_text(next_task_pointer_md, encoding="utf-8")

    print(json.dumps({
        "import_fixture_status": blank_fixture["import_fixture_status"],
        "blockers": blockers
    }, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
