"""V6 Article Research Requirements.

Generates research requirements for the next canonical Substack article.
"""
from __future__ import annotations

import hashlib
from typing import Any


def generate_research_requirements(article_packet_id: str) -> list[dict[str, Any]]:
    """Builds a deterministic requirements packet for necessary source materials."""
    categories = [
        {
            "type": "treasury_yield_series",
            "name": "Primary Source for Treasury Yield Series"
        },
        {
            "type": "yield_curve_calculation",
            "name": "Methodology / Source for Yield Curve Calculation"
        },
        {
            "type": "historical_volatility",
            "name": "Source for Historical Volatility / Statistical Claim"
        },
        {
            "type": "chart_table_data",
            "name": "Source for Yield Curve Charts / Reference Tables"
        },
        {
            "type": "limitations_disclaimer",
            "name": "Limitations / Disclaimer Source or Policy Note"
        }
    ]

    requirements = []
    for cat in categories:
        hasher = hashlib.sha256(f"{article_packet_id}_{cat['type']}".encode("utf-8"))
        req_id = f"req_{hasher.hexdigest()[:12]}"

        requirements.append({
            "research_requirement_id": req_id,
            "required_source_type": cat["type"],
            "source_name_placeholder": f"Placeholder: {cat['name']}",
            "source_url_placeholder": None,
            "source_verification_status": "missing",
            "official_source_required": True,
            "claim_supported": False,
            "required_before_publication": True,
            "human_research_required": True
        })

    return requirements
