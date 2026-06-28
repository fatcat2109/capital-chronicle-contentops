"""V6 Real Source Pack Redacted Fixture Review Coordinator.

Generates the redacted evidence and hash review artifacts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from live_contentops import real_source_pack_redacted_fixture_v6 as fixture_builder
from live_contentops import real_source_pack_redacted_fixture_validator_v6 as validator
from live_contentops import real_source_pack_redaction_v6 as redaction_builder

TASK_LABEL = "TASK_CONTENTOPS_V6_REAL_SOURCE_PACK_OPERATOR_FILLED_REDACTED_FIXTURE_DRY_RUN_REVIEW_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_REAL_SOURCE_PACK_REDACTED_FIXTURE_REVIEW")


def make_redacted_hash_presence_review(entry_count: int) -> dict[str, Any]:
    """Generates the redacted hash presence review packet."""
    return {
        "hash_review_status": "REDACTED_HASH_PRESENCE_REVIEW_ONLY",
        "runtime_truth": False,
        "raw_hash_values_persisted": False,
        "raw_source_urls_persisted": False,
        "raw_source_excerpts_persisted": False,
        "redacted_hash_presence_only": True,
        "hash_count": entry_count,
        "source_entry_count": entry_count,
        "all_hashes_present": True,
        "all_entries_redacted": True,
        "valid_for_source_approval": False,
        "valid_for_draft_generation": False,
        "valid_for_publication": False,
        "valid_for_dispatch": False,
        "human_review_required": True,
        "kill_switch_active": True
    }


def make_redacted_claim_binding_review() -> dict[str, Any]:
    """Generates claim binding review mappings using IDs only."""
    return {
        "claims_bindings": [
            {
                "claim_id": "claim_d474a9fdbcd6",
                "source_requirement_refs": ["req_67a5db6704f5"],
                "source_support_status": "redacted_presence_only_not_approved",
                "source_entries_found_by_requirement_id": ["req_67a5db6704f5"],
                "allowed_in_review": False,
                "allowed_in_article_draft": False,
                "allowed_for_publication": False,
                "blockers": [
                    "operator_source_approval_missing",
                    "runtime_truth_false",
                    "raw_source_values_not_available_for_model"
                ]
            },
            {
                "claim_id": "claim_63d1cf20e9bf",
                "source_requirement_refs": ["req_bfcb46cc38cc"],
                "source_support_status": "redacted_presence_only_not_approved",
                "source_entries_found_by_requirement_id": ["req_bfcb46cc38cc"],
                "allowed_in_review": False,
                "allowed_in_article_draft": False,
                "allowed_for_publication": False,
                "blockers": [
                    "operator_source_approval_missing",
                    "runtime_truth_false",
                    "raw_source_values_not_available_for_model"
                ]
            },
            {
                "claim_id": "claim_492c29ad9746",
                "source_requirement_refs": ["req_e6edaf8e7750"],
                "source_support_status": "redacted_presence_only_not_approved",
                "source_entries_found_by_requirement_id": ["req_e6edaf8e7750"],
                "allowed_in_review": False,
                "allowed_in_article_draft": False,
                "allowed_for_publication": False,
                "blockers": [
                    "operator_source_approval_missing",
                    "runtime_truth_false",
                    "raw_source_values_not_available_for_model"
                ]
            }
        ]
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Real Source Pack Redacted Fixture Coordinator")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Build packets and examples
    redacted_fixture = fixture_builder.make_operator_filled_redacted_fixture()
    entry_count = len(redacted_fixture["source_entries"])
    hash_presence = make_redacted_hash_presence_review(entry_count)
    claim_binding = make_redacted_claim_binding_review()
    policy = redaction_builder.make_redaction_policy()

    # Redacted fixture review packet
    packet = {
        "redacted_fixture_review_status": "REDACTED_FIXTURE_WAITING_FOR_OPERATOR",
        "runtime_truth": False,
        "operator_filled_redacted_fixture": True,
        "human_review_required": True,
        "kill_switch_active": True
    }

    # 2. Validation report
    validation_report, blockers = validator.validate_real_source_pack_redacted_fixture(
        redacted_fixture, hash_presence, policy
    )

    # 3. Write JSON files
    artifacts = {
        "real_source_pack_redacted_fixture_packet.json": packet,
        "operator_filled_redacted_fixture_example.json": redacted_fixture,
        "redacted_hash_presence_review.json": hash_presence,
        "redacted_claim_binding_review.json": claim_binding,
        "redacted_fixture_validation_report.json": validation_report
    }

    for name, data in artifacts.items():
        Path(out_dir / name).write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8"
        )

    # Blocker report
    blocker_bullets = "\n".join(f"- `{b}`" for b in blockers)
    blocker_md = f"""# Redacted Fixture Blocker Report

- **Task Label**: {TASK_LABEL}
- **Active Blockers Count**: {len(blockers)}

## Active Blockers
{blocker_bullets}
"""
    Path(out_dir / "redacted_fixture_blocker_report.md").write_text(blocker_md, encoding="utf-8")

    # Runbook
    runbook_md = """# Redacted Fixture Review Runbook

Performs dry-run review over redacted operator-filled fixture example.

## Instructions
1. Verifies that no raw URLs or hashes are leaked.
2. Ensures all entries are redacted-only.
"""
    Path(out_dir / "redacted_fixture_review_runbook.md").write_text(runbook_md, encoding="utf-8")

    # Implementation report
    impl_md = f"""# Redacted Fixture Review Implementation Report

- **Task Label**: {TASK_LABEL}
- **Safety posture**: all operator entries redacted; no raw URLs, hashes, or signatures allowed.
"""
    Path(out_dir / "implementation_report.md").write_text(impl_md, encoding="utf-8")

    # Next task pointer
    next_task_pointer_md = """# Next Task Pointer

Recommended next task:

`TASK_CONTENTOPS_V6_REAL_SOURCE_PACK_OPERATOR_APPROVAL_GATE_DRY_RUN_HEAVY_BATCH_V0`
"""
    Path(out_dir / "next_task_pointer.md").write_text(next_task_pointer_md, encoding="utf-8")

    print(json.dumps({
        "fixture_status": redacted_fixture["fixture_status"],
        "blockers": blockers
    }, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
