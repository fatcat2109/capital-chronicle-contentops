"""V6 Canonical Draft Fixture Renderer.

Renders a review-only synthetic article-shaped draft preview from test-only fixtures,
ensuring watermarking and absolute exclusion of publication-ready or sensitive language.
"""
from __future__ import annotations

import re
from typing import Any

FINANCIAL_ADVICE_KEYWORDS = ["buy", "sell", "hold", "target price", "stop loss", "position size", "trade setup", "alpha call", "guaranteed return"]


def render_review_only_draft_preview(
    title: str,
    claims: list[dict[str, Any]],
    source_bindings: list[dict[str, Any]]
) -> str:
    """Renders a review-only synthetic draft preview watermarked as TEST-ONLY."""
    # Build claims mapping
    binding_by_claim = {b["claim_id"]: b for b in source_bindings}

    claim_details = []
    for c in claims:
        claim_id = c.get("claim_id")
        binding = binding_by_claim.get(claim_id)
        if binding:
            refs = ", ".join(binding.get("source_requirement_refs", []))
            status = binding.get("source_support_status", "unverified")
        else:
            refs = "None"
            status = "unverified"
        
        claim_details.append(
            f"- **[Claim {claim_id}]**: {c.get('claim_text_draft')}\n"
            f"  *Binding Status*: {status} (Refs: {refs})"
        )
    
    claims_section = "\n".join(claim_details)

    md = f"""# TEST-ONLY / NOT RUNTIME TRUTH

## Study: Macroeconomic Data Providence Review (Synthetic Preview)

> [!WARNING]
> **TEST-ONLY / NOT RUNTIME TRUTH**: This document is generated exclusively for positive-path unit-test validation.
> It contains no public-ready claims, no real citations, no real or fake source URLs, and no fake evidence hashes.

### Executive Summary
This analysis tracks interest rate frameworks and treasury yield maturities.

### Scaffolding Provenance Claims
{claims_section}

### Structural Caveats
- Macroeconomic parameters are highly uncertain and model-dependent.
- This analysis is for educational purposes only; consult licensed financial professionals.

### Next Operator Actions
> [!IMPORTANT]
> **Required Action**: The operator must supply a real verified source pack later to replace this synthetic preview.
"""
    # Clean any accidental forbidden words/patterns just in case
    for k in FINANCIAL_ADVICE_KEYWORDS:
        pattern = re.compile(rf"\b{k}\b", re.IGNORECASE)
        md = pattern.sub("[REDACTED_FINANCIAL_TERM]", md)

    return md
