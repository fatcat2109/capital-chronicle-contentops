"""V6 Source-Claim Binding Validator.

Checks if claims in the ledger scaffold are correctly backed by verified source entries.
"""
from __future__ import annotations

from typing import Any


def generate_source_claim_binding_report(
    claims: list[dict[str, Any]],
    source_pack: dict[str, Any]
) -> dict[str, Any]:
    """Binds claims to source entries and determines their safety draft status."""
    source_entries = source_pack.get("source_entries", [])
    verified_entry_ids = {
        e["source_requirement_id"] for e in source_entries
        if e.get("verification_status") == "verified"
    }

    bindings = []
    all_bound = True

    for c in claims:
        claim_id = c["claim_id"]
        refs = c.get("source_requirement_refs", [])

        matching_entries = [
            ref for ref in refs
            if any(e["source_requirement_id"] == ref for e in source_entries)
        ]

        # Is it fully supported by verified sources?
        is_supported = len(refs) > 0 and all(r in verified_entry_ids for r in refs)

        claim_blockers = []
        if not is_supported:
            claim_blockers.append("source_verification_required")
            all_bound = False

        bindings.append({
            "claim_id": claim_id,
            "claim_text_draft": c["claim_text_draft"],
            "source_requirement_refs": refs,
            "source_pack_entries_found": matching_entries,
            "source_support_status": "verified" if is_supported else "missing",
            "allowed_in_article_draft": is_supported,
            "blockers": claim_blockers
        })

    return {
        "schema_version": "6.0.0",
        "all_claims_bound_to_sources": all_bound,
        "bindings": bindings,
        "human_review_required": True
    }
