"""V6 Canonical Article Draft Gate.

Evaluates if verified source packs satisfy article requirements to unblock draft generation.
"""
from __future__ import annotations

from typing import Any


def evaluate_draft_gate(
    source_pack: dict[str, Any],
    requirements: list[dict[str, Any]],
    claims: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[str]]:
    """Evaluates the verified source pack, compiling blockers and returning the gate report."""
    blockers = []

    source_entries = source_pack.get("source_entries", [])
    pack_status = source_pack.get("verified_source_pack_status")
    pack_complete = source_pack.get("source_pack_complete", False)

    # 1. Basic package validations
    if pack_status == "MISSING_REQUIRED_SOURCE_VERIFICATION" or not pack_complete:
        blockers.append("verified_source_pack_missing")

    # 2. Check if all required sources are verified
    all_required_sources_verified = True
    verified_entry_ids = set()

    for r in requirements:
        req_id = r["research_requirement_id"]
        # Find verified entry
        entry = next((e for e in source_entries if e["source_requirement_id"] == req_id), None)
        if not entry or entry.get("verification_status") != "verified":
            all_required_sources_verified = False
            blockers.append("source_verification_required")
        else:
            verified_entry_ids.add(req_id)

    # 3. Check if all claims are bound to verified sources
    all_claims_bound_to_sources = True
    for c in claims:
        # Check if every reference is matched to a verified source entry
        refs = c.get("source_requirement_refs", [])
        if not refs:
            all_claims_bound_to_sources = False
        for ref in refs:
            if ref not in verified_entry_ids:
                all_claims_bound_to_sources = False

    if not all_claims_bound_to_sources:
        blockers.append("all_claims_not_bound_to_verified_sources")

    # 4. Standard pipeline blockers
    blockers.append("publication_blocked_until_source_verification")
    blockers.append("claim_ledger_unverified")
    blockers.append("article_copy_not_generated")

    # Deduplicate blockers
    blockers = sorted(list(set(blockers)))

    passed = len([b for b in blockers if b in ["verified_source_pack_missing", "source_verification_required", "all_claims_not_bound_to_verified_sources"]]) == 0

    report = {
        "gate_status": "PASSED" if passed else "BLOCKED_MISSING_VERIFIED_SOURCE_PACK",
        "source_pack_complete": pack_complete,
        "all_required_sources_verified": all_required_sources_verified,
        "all_claims_bound_to_sources": all_claims_bound_to_sources,
        "draft_copy_generation_allowed": passed,
        "publication_allowed": False,
        "human_research_required": True,
        "blockers": blockers
    }

    return report, blockers
