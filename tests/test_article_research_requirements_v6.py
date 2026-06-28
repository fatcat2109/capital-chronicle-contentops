"""Test article research requirements module."""
from __future__ import annotations

from live_contentops import article_research_requirements_v6 as research


def test_generate_research_requirements():
    reqs = research.generate_research_requirements("article_packet_123")
    assert len(reqs) == 5

    required_types = [
        "treasury_yield_series",
        "yield_curve_calculation",
        "historical_volatility",
        "chart_table_data",
        "limitations_disclaimer"
    ]

    for r in reqs:
        assert r["required_source_type"] in required_types
        assert r["source_verification_status"] == "missing"
        assert r["source_url_placeholder"] is None
        assert r["official_source_required"] is True
        assert r["claim_supported"] is False
        assert r["required_before_publication"] is True
        assert r["human_research_required"] is True
