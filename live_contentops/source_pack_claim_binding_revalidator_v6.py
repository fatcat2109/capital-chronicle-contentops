"""V6 Source Pack Claim Binding Revalidator.

Binds manual source pack entries to the article claim ledger scaffold.
"""
from __future__ import annotations

from typing import Any


def revalidate_source_claim_binding(
    source_pack: dict[str, Any],
    claim_scaffold: list[dict[str, Any]]
) -> tuple[dict[str, Any], bool]:
    """Matches source entries to the claim ledger scaffold and outputs the binding status."""
    rebound_claims = []
    all_bound = True

    entries = source_pack.get("source_entries", [])
    pack_complete = source_pack.get("source_pack_complete", False)
    pack_status = source_pack.get("verified_source_pack_status")

    is_missing_state = pack_status == "MISSING_REQUIRED_SOURCE_VERIFICATION" or not pack_complete

    # Map supports
    supported_claims_set = set()
    for entry in entries:
        if entry.get("verification_status") == "verified":
            for cid in entry.get("source_supports_claim_ids", []):
                supported_claims_set.add(cid)

    for item in claim_scaffold:
        cid = item["claim_id"]
        req_refs = item["source_requirement_refs"]

        # Default block logic
        support_status = "missing"
        allowed_in_draft = False
        blockers = []

        if is_missing_state:
            blockers.append("source_verification_required")
            blockers.append("claim_binding_missing")
        else:
            if cid in supported_claims_set:
                support_status = "verified"
                allowed_in_draft = True
            else:
                support_status = "missing"
                blockers.append("claim_binding_missing")
                all_bound = False

        rebound_claims.append({
            "claim_id": cid,
            "source_requirement_refs": req_refs,
            "source_entries_found": [req_refs] if support_status == "verified" else [],
            "source_support_status": support_status,
            "missing_source_refs": [] if support_status == "verified" else [req_refs],
            "allowed_in_article_draft": allowed_in_draft,
            "blockers": blockers
        })

    if is_missing_state:
        all_bound = False

    revalidation_report = {
        "schema_version": "6.0.0",
        "all_claims_bound_to_sources": all_bound,
        "rebound_claims": rebound_claims,
        "blockers": ["claim_binding_missing"] if not all_bound else []
    }

    return revalidation_report, all_bound
