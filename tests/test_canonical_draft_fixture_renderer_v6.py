"""Test V6 Canonical Draft Fixture Renderer."""
from __future__ import annotations

from live_contentops import canonical_draft_fixture_renderer_v6 as renderer


def test_render_review_only_draft_preview():
    title = "Interest Rate Analysis"
    claims = [
        {"claim_id": "claim_001", "claim_text_draft": "Spreads matured volatility."}
    ]
    bindings = [
        {
            "claim_id": "claim_001",
            "source_requirement_refs": ["req_001"],
            "source_support_status": "test_only_bound"
        }
    ]

    md = renderer.render_review_only_draft_preview(title, claims, bindings)

    assert "TEST-ONLY / NOT RUNTIME TRUTH" in md
    assert "claim_001" in md
    assert "test_only_bound" in md
    assert "Next Operator Actions" in md
    assert "consult licensed financial professionals" in md

    # Ensure no financial advice keyword or URL
    assert "https://" not in md
    assert "buy" not in md.lower()
    assert "sell" not in md.lower()
