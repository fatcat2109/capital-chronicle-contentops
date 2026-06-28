"""V6 Article Claim Ledger Scaffold.

Generates unverified claim placeholders linked to research requirements.
"""
from __future__ import annotations

import hashlib
from typing import Any


def generate_claim_ledger_scaffold(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Builds a claim ledger scaffold where claims remain unverified and blocked from public drafts."""
    claims = []

    # Mappings of claims to requirement types
    claim_templates = [
        {
            "text": "Treasury yield curve spreads have experienced heightened volatility over the last quarter.",
            "type": "statistical_trend",
            "req_type": "treasury_yield_series"
        },
        {
            "text": "The methodology for computing yield curve adjustments relies on the Nelson-Siegel model parameters.",
            "type": "methodology",
            "req_type": "yield_curve_calculation"
        },
        {
            "text": "Historical yield volatility patterns under similar macro tightening cycles show mean reversion trends.",
            "type": "statistical_trend",
            "req_type": "historical_volatility"
        }
    ]

    for idx, ct in enumerate(claim_templates):
        # Find matching req ID
        req_ref = next((r["research_requirement_id"] for r in requirements if r["required_source_type"] == ct["req_type"]), "stub_req_id")

        hasher = hashlib.sha256(f"claim_{idx}_{ct['type']}".encode("utf-8"))
        claim_id = f"claim_{hasher.hexdigest()[:12]}"

        claims.append({
            "claim_id": claim_id,
            "claim_text_draft": ct["text"],
            "claim_type": ct["type"],
            "source_requirement_refs": [req_ref],
            "verification_status": "unverified",
            "allowed_in_public_draft": False,
            "needs_human_review": True,
            "no_numeric_truth_invented": True,
            "no_forward_signal": True
        })

    return claims
