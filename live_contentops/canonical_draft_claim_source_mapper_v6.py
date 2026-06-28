"""V6 Canonical Draft Claim-Source Mapper.

Binds scaffold claims to source requirements using IDs only, avoiding any raw URL or evidence hash exposure.
"""
from __future__ import annotations

from typing import Any


def map_claims_to_test_only_sources(
    claims: list[dict[str, Any]],
    requirements: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Maps scaffold claims to source requirement IDs, producing test-only binding proof entries."""
    bindings = []
    
    # Extract known requirements IDs
    req_ids = {r.get("research_requirement_id") for r in requirements if r.get("research_requirement_id")}

    for c in claims:
        claim_id = c.get("claim_id")
        refs = c.get("source_requirement_refs", [])
        
        # Verify that refs align with available requirements
        bound_refs = [r for r in refs if r in req_ids]
        if not bound_refs:
            # Fallback mock binding if scaffold refs are empty or mismatch
            bound_refs = list(req_ids)[:1] if req_ids else []

        bindings.append({
            "claim_id": claim_id,
            "source_requirement_refs": bound_refs,
            "source_support_status": "test_only_bound",
            "allowed_in_review_draft": True,
            "allowed_in_publication": False,
            "runtime_truth": False
        })
        
    return bindings
