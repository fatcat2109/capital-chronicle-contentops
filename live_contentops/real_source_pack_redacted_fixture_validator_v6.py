"""V6 Real Source Pack Redacted Fixture Validator.

Validates the redacted operator-filled fixture offline.
"""
from __future__ import annotations

from typing import Any

from live_contentops import real_source_pack_manual_import_validator_v6 as base_validator


def validate_real_source_pack_redacted_fixture(
    fixture: dict[str, Any],
    hash_review: dict[str, Any],
    policy: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    """Runs redacted fixture validations returning status and blockers."""
    base_report, base_blockers = base_validator.validate_real_source_pack_manual_import(
        fixture, hash_review, policy
    )

    failed = base_report["validation_status"] == "FAILED_WITH_BLOCKERS"

    blockers = []
    # If failed, carry over leak blockers
    if failed:
        for b in base_blockers:
            # check if it is a leak blocker (doesn't contain missing/required/blocked/false)
            if not any(x in b for x in ["missing", "required", "blocked", "false"]):
                blockers.append(b)

    # Always append the 7 required checkers
    blockers.extend([
        "operator_source_approval_missing",
        "runtime_truth_false",
        "canonical_draft_generation_blocked",
        "publication_blocked_until_real_source_verification",
        "dispatch_blocked",
        "human_review_required",
        "source_verification_required"
    ])

    blockers = sorted(list(set(blockers)))
    status = "FAILED_WITH_BLOCKERS" if failed else "PASSED_WITH_REVIEW_ONLY_BLOCKERS"

    report = {
        "schema_version": "6.0.0",
        "validation_status": status,
        "runtime_truth": False,
        "redacted_fixture_review_validated": True,
        "blockers": blockers,
        "blocker_count": len(blockers)
    }

    return report, blockers
