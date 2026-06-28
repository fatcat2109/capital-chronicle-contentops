"""V6 Verified Source Pack Import Handler.

Assembles operator import template, runs offline parses, and handles default validation checks.
"""
from __future__ import annotations

from typing import Any

from live_contentops import source_pack_draft_validator_v6 as draft_validator


def make_operator_source_pack_import_template() -> dict[str, Any]:
    """Builds operator import template."""
    return {
        "source_pack_import_status": "OPERATOR_SOURCE_PACK_REQUIRED",
        "import_mode": "manual_local_file_deferred",
        "source_pack_complete": False,
        "all_required_sources_verified": False,
        "all_claims_bound_to_sources": False,
        "allowed_for_article_use": False,
        "draft_generation_allowed": False,
        "human_review_required": True,
        "source_verification_required": True,
        "provider_call_performed": False,
        "browser_session_started": False,
        "env_read_performed": False,
        "live_source_fetch_performed": False,
        "credentials_hydrated": False,
        "public_postable": False,
        "dispatch_allowed_now": False,
        "kill_switch_active": True,
        "source_entries": []
    }


def validate_imported_source_pack(source_pack: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Runs structural checks over imported pack, appending detailed missing fields if blank."""
    report, blockers = draft_validator.validate_source_pack_draft(source_pack)

    # Inject default broad missing-pack blockers
    entries = source_pack.get("source_entries", [])
    if not entries or source_pack.get("verified_source_pack_status") == "MISSING_REQUIRED_SOURCE_VERIFICATION":
        if "operator_source_pack_missing" not in blockers:
            blockers.append("operator_source_pack_missing")
        if "verified_source_pack_missing" not in blockers:
            blockers.append("verified_source_pack_missing")
        if "draft_generation_blocked" not in blockers:
            blockers.append("draft_generation_blocked")
        
        # Enforce all five missing-field blockers for blank import
        for f in ["source_url_missing", "evidence_hash_missing", "retrieved_at_missing", "operator_signature_missing", "source_excerpt_ref_missing"]:
            if f not in blockers:
                blockers.append(f)

    blockers = sorted(list(set(blockers)))

    report["safety_checks"]["verified_fields_complete"] = not any(
        b in blockers for b in [
            "source_url_missing", "evidence_hash_missing", "retrieved_at_missing",
            "operator_signature_missing", "source_excerpt_ref_missing"
        ]
    )

    # Synchronize report status
    report["validation_status"] = "FAILED_WITH_BLOCKERS" if blockers else "PASSED"
    report["blockers"] = blockers
    report["blocker_count"] = len(blockers)

    return report, blockers
