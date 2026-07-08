import json
from datetime import date, timedelta

import pytest

from live_contentops.ai_research_canonical_article_engine_v6 import (
    EngineInput,
    check_financial_advice,
    run_article_engine,
    validate_article_quality,
)
from live_contentops.editorial_quality_audit_v6 import audit_editorial_quality_packet


def _inputs() -> EngineInput:
    return EngineInput(
        operator_idea="Fed liquidity and shipping stress",
        target_audience="general_financial_education",
        editorial_angle="educational macro transmission channels",
        source_context=["Policy source note", "Shipping index source note"],
        risk_disclaimer_policy="V6_EDUCATIONAL_DISCLAIMER",
        output_style="educational_process_heavy",
    )


def _good_article_json() -> str:
    base = (
        "According to source data, this educational macro review explains policy liquidity, "
        "shipping index pressure, and reported 3.5% changes across 12 months without giving investment advice. "
    )
    return json.dumps({
        "title": "Liquidity and shipping stress in the policy data cycle",
        "subtitle": "A source-led educational review of macro transmission channels",
        "slug_candidate": "liquidity-shipping-stress-policy-data-cycle",
        "dek": "A source-led look at how liquidity plumbing and freight stress shape macro transmission.",
        "meta_description": "Capital Chronicle reviews liquidity and shipping stress through source-led macro context, visual evidence, and process-first education.",
        "intro": base * 20,
        "sections": [
            {"title": f"Section {idx}", "body": base * 18}
            for idx in range(1, 6)
        ],
        "conclusion": base * 12,
        "source_trail": [
            {"label": "Source 1", "publisher_or_origin": "Primary Source", "url": "https://example.com/source-1", "claim_supported": "Reported shipping index pressure rose across the reviewed window."},
            {"label": "Source 2", "publisher_or_origin": "Primary Source", "url": "https://example.com/source-2", "claim_supported": "Policy liquidity timing changed funding conditions during the reviewed period."},
            {"label": "Source 3", "publisher_or_origin": "Primary Source", "url": "https://example.com/source-3", "claim_supported": "Macro data revisions require caution when comparing current readings with past cycles."},
        ],
        "chart_callouts": ["[CHART: current liquidity and shipping stress series with source dates]"],
        "media_callouts": ["[IMAGE: source-backed chart showing current macro transmission evidence]"],
        "visual_slots": [
            {
                "asset_id": "primary",
                "placement_after_section": "intro",
                "visual_kind": "chart",
                "editorial_purpose": "Anchor the macro setup in current source data.",
                "data_requirement": "Current liquidity and shipping stress series with latest observation date.",
                "caption_guidance": "Name the series, source, and latest observation date.",
                "source_requirement": "Primary source or source-backed public data provider.",
                "audit_questions": "Is the endpoint current and directionally aligned?",
            },
            {
                "asset_id": "recent_price",
                "placement_after_section": "Section 3",
                "visual_kind": "chart",
                "editorial_purpose": "Support the market-structure interpretation with a second visual lens.",
                "data_requirement": "Recent-window chart tied to the article's market-structure claim.",
                "caption_guidance": "Explain the recent window and claim supported.",
                "source_requirement": "Same-source or clearly attributed secondary provider.",
                "audit_questions": "Does this visual add evidence beyond the first chart?",
            },
        ],
    })


def test_financial_advice_scanner_allows_generic_targets_context():
    check_financial_advice("Policy targets and inflation targets are macro context, not a trade instruction.")


@pytest.mark.parametrize("text", ["buy now", "sell this", "hold position", "price target raised"])
def test_financial_advice_scanner_blocks_explicit_advice_language(text):
    with pytest.raises(ValueError):
        check_financial_advice(text)


def test_provider_timeout_then_model_fallback_accepts_quality_article(monkeypatch):
    monkeypatch.setenv("NINE_ROUTER_API_KEY", "sk-test")
    monkeypatch.setattr(
        "live_contentops.grounded_search_engine_v6.execute_grounded_search",
        lambda *_args, **_kwargs: [{"publisher_or_origin": "Source", "title": "Shipping index up 3.5%", "url_or_local_reference": "https://example.com/source"}],
    )
    calls = {"count": 0}

    def fake_provider(*_args, **kwargs):
        calls["count"] += 1
        if kwargs.get("model_override") is None:
            raise TimeoutError("provider timed out")
        return _good_article_json()

    monkeypatch.setattr("live_contentops.ai_research_canonical_article_engine_v6.call_live_provider", fake_provider)
    packet = run_article_engine(_inputs(), provider_mode="live_provider_call", provider_request_budget=2, live_provider="9router", timeout_seconds=7)

    assert packet["blockers"] == []
    assert packet["provider_request_count"] == 2
    assert packet["provider_attempts"][0]["failure"].startswith("provider_call_failed:TimeoutError")
    assert packet["provider_attempts"][1]["status"] == "accepted"
    assert packet["provider_attempts"][1]["timeout_seconds"] == 7
    assert validate_article_quality(packet["canonical_article_draft"]) == []


def test_short_provider_article_uses_deterministic_recovery(monkeypatch):
    monkeypatch.setenv("NINE_ROUTER_API_KEY", "sk-test")
    monkeypatch.setattr("live_contentops.grounded_search_engine_v6.execute_grounded_search", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(
        "live_contentops.ai_research_canonical_article_engine_v6.call_live_provider",
        lambda *_args, **_kwargs: json.dumps({"title": "Short", "sections": []}),
    )

    packet = run_article_engine(_inputs(), provider_mode="live_provider_call", provider_request_budget=1, live_provider="9router")

    assert "article_provider_recovery_not_publishable" in packet["blockers"]
    assert packet["provider_recovery_used"] is True
    assert any(w.startswith("article_deterministic_recovery_blocked:") for w in packet["warnings"])
    assert packet["provider_attempts"][-1]["provider"] == "deterministic_recovery"
    assert validate_article_quality(packet["canonical_article_draft"]) != []


def test_oil_provider_near_miss_uses_source_backed_longform_repair(monkeypatch):
    monkeypatch.setenv("NINE_ROUTER_API_KEY", "sk-test")
    monkeypatch.setattr("live_contentops.grounded_search_engine_v6.execute_grounded_search", lambda *_args, **_kwargs: [])

    start = date(2025, 10, 1)
    points = []
    for idx in range(120):
        day = start + timedelta(days=idx)
        value = 68.0 + idx * 0.18
        if idx % 11 == 0:
            value += 2.2
        points.append((day, value))

    monkeypatch.setattr("live_contentops.media_content_audit_v6._read_fred_csv", lambda *_args, **_kwargs: points)
    monkeypatch.setattr(
        "live_contentops.ai_research_canonical_article_engine_v6.call_live_provider",
        lambda *_args, **_kwargs: json.dumps({
            "title": "Short oil volatility note",
            "sections": [{"title": "Thin section", "body": "Oil volatility is rising."}],
        }),
    )

    inputs = EngineInput(
        operator_idea="US recession risks rise as oil volatility spikes",
        target_audience="general_financial_education",
        editorial_angle="Focus on data transparency, geopolitics, and yield curves.",
        source_context=[],
        risk_disclaimer_policy="V6_EDUCATIONAL_DISCLAIMER",
        output_style="educational_process_heavy",
    )

    packet = run_article_engine(inputs, provider_mode="live_provider_call", provider_request_budget=1, live_provider="9router")
    draft = packet["canonical_article_draft"]

    assert packet["blockers"] == []
    assert packet["provider_recovery_used"] is True
    assert packet["provider_attempts"][-1]["provider"] == "deterministic_article_repair"
    assert packet["provider_attempts"][-1]["status"] == "accepted"
    assert validate_article_quality(draft) == []
    assert draft["body_word_count"] >= 2000
    assert len(draft["sections"]) >= 5
    assert len(draft["source_trail"]) >= 5
    assert len(draft["visual_slots"]) >= 3
    assert "operator_review_required" not in json.dumps(draft["source_trail"])
    assert "DCOILWTICO" in json.dumps(draft["source_trail"])
    assert packet["seo_packet"]["target_keyword"] == "oil volatility recession risk"
    assert audit_editorial_quality_packet(packet, topic=inputs.operator_idea)["classification"] == "EDITORIAL_APPROVED"


def test_oil_dry_run_fixture_uses_source_backed_longform_without_fred_network(monkeypatch):
    def fail_fred_read(*_args, **_kwargs):
        raise AssertionError("dry-run fixture must not fetch FRED")

    monkeypatch.setattr("live_contentops.media_content_audit_v6._read_fred_csv", fail_fred_read)
    inputs = EngineInput(
        operator_idea="US recession risks rise as oil volatility spikes",
        target_audience="general_financial_education",
        editorial_angle="Focus on data transparency, geopolitics, and yield curves.",
        source_context=[],
        risk_disclaimer_policy="V6_EDUCATIONAL_DISCLAIMER",
        output_style="educational_process_heavy",
    )

    packet = run_article_engine(inputs, provider_mode="dry_run_fixture")
    draft = packet["canonical_article_draft"]

    assert packet["provider_call_made"] is False
    assert packet["provider_recovery_used"] is True
    assert packet["provider_attempts"][-1]["model"] == "dry_run_source_backed_wti_fixture_longform_template"
    assert "dry_run_source_backed_wti_fixture_used" in packet["warnings"]
    assert validate_article_quality(draft) == []
    assert draft["body_word_count"] >= 2000
    assert audit_editorial_quality_packet(packet, topic=inputs.operator_idea)["classification"] == "EDITORIAL_APPROVED"
