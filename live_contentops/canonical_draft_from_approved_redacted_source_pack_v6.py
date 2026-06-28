"""V6 Canonical Draft from Approved Redacted Source Pack Coordinator.

Sets up unapproved test-only simulated approved states and validates them.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from live_contentops import approved_redacted_source_pack_test_fixture_v6 as summary_builder
from live_contentops import canonical_draft_eligibility_packet_v6 as packet_builder
from live_contentops import canonical_draft_eligibility_validator_v6 as validator

TASK_LABEL = "TASK_CONTENTOPS_V6_CANONICAL_DRAFT_FROM_APPROVED_REDACTED_SOURCE_PACK_DRY_RUN_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_CANONICAL_DRAFT_FROM_APPROVED_REDACTED_SOURCE_PACK")


def make_claim_eligibility_matrix() -> list[dict[str, Any]]:
    """Generates matrix mapping claims to simulated approvals."""
    claims = [
        {"id": "claim_d474a9fdbcd6", "refs": ["req_67a5db6704f5"]},
        {"id": "claim_63d1cf20e9bf", "refs": ["req_bfcb46cc38cc"]},
        {"id": "claim_492c29ad9746", "refs": ["req_e6edaf8e7750"]}
    ]

    matrix = []
    for c in claims:
        matrix.append({
            "claim_id": c["id"],
            "source_requirement_refs": c["refs"],
            "redacted_presence_available": True,
            "source_pack_approval_simulated": True,
            "runtime_approval_present": False,
            "eligible_for_test_only_draft_outline": True,
            "eligible_for_runtime_draft": False,
            "allowed_for_publication": False,
            "blockers": [
                "runtime_operator_approval_missing",
                "raw_source_values_not_available_for_model",
                "publication_blocked",
                "dispatch_blocked"
            ]
        })
    return matrix


def make_generation_blocked_preview() -> str:
    """Generates blocked preview markdown with banner."""
    return """# TEST-ONLY APPROVAL SIMULATION / NOT RUNTIME TRUTH / NO ARTICLE COPY GENERATED

A future real Jim approval artifact is still required before runtime draft generation.

## Eligible Claim IDs
- `claim_d474a9fdbcd6` (Requirement: `req_67a5db6704f5`)
- `claim_63d1cf20e9bf` (Requirement: `req_bfcb46cc38cc`)
- `claim_492c29ad9746` (Requirement: `req_e6edaf8e7750`)
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Canonical Draft Eligibility Coordinator")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Build inputs
    eligibility_packet = packet_builder.make_canonical_draft_eligibility_packet()
    summary = summary_builder.make_approved_redacted_source_pack_summary()
    matrix = make_claim_eligibility_matrix()
    preview_md = make_generation_blocked_preview()

    # 2. Validation report
    validation_report, blockers = validator.validate_canonical_draft_eligibility(
        eligibility_packet, summary, matrix, preview_md
    )

    # 3. Write files
    artifacts = {
        "canonical_draft_eligibility_packet.json": eligibility_packet,
        "test_only_approved_redacted_source_pack_summary.json": summary,
        "canonical_draft_claim_eligibility_matrix.json": matrix,
        "canonical_draft_eligibility_validation_report.json": validation_report
    }

    for name, data in artifacts.items():
        Path(out_dir / name).write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8"
        )

    # Preview md
    Path(out_dir / "canonical_draft_generation_blocked_preview.md").write_text(
        preview_md, encoding="utf-8"
    )

    # Blocker report
    blocker_bullets = "\n".join(f"- `{b}`" for b in blockers)
    blocker_md = f"""# Canonical Draft Eligibility Blocker Report

- **Task Label**: {TASK_LABEL}
- **Active Blockers Count**: {len(blockers)}

## Active Blockers
{blocker_bullets}
"""
    Path(out_dir / "canonical_draft_eligibility_blocker_report.md").write_text(
        blocker_md, encoding="utf-8"
    )

    # Runbook
    runbook_md = """# Canonical Draft Eligibility Runbook

Establishes unapproved test-only simulated approved states.

## Instructions
1. Verifies that test-only simulated gate passes correctly.
2. Ensures no active article prose is generated.
"""
    Path(out_dir / "canonical_draft_eligibility_runbook.md").write_text(
        runbook_md, encoding="utf-8"
    )

    # Implementation report
    impl_md = f"""# Canonical Draft Eligibility Implementation Report

- **Task Label**: {TASK_LABEL}
- **Safety posture**: offline draft outline validation complete; no real approval is active.
"""
    Path(out_dir / "implementation_report.md").write_text(impl_md, encoding="utf-8")

    # Next task pointer
    next_task_pointer_md = """# Next Task Pointer

Recommended next task:

`TASK_CONTENTOPS_V6_CANONICAL_ARTICLE_STUDIO_REVIEW_QUEUE_DRY_RUN_HEAVY_BATCH_V0`
"""
    Path(out_dir / "next_task_pointer.md").write_text(next_task_pointer_md, encoding="utf-8")

    print(json.dumps({
        "eligibility_status": eligibility_packet["eligibility_status"],
        "blockers": blockers
    }, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
