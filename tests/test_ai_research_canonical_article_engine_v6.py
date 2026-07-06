import json
import pytest

from live_contentops.ai_research_canonical_article_engine_v6 import (
    EngineInput,
    check_financial_advice,
    run_article_engine,
    validate_article_quality,
)


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
        "intro": base * 20,
        "sections": [
            {"title": f"Section {idx}", "body": base * 18}
            for idx in range(1, 6)
        ],
        "conclusion": base * 12,
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

    assert packet["blockers"] == []
    assert packet["provider_recovery_used"] is True
    assert any(w.startswith("article_deterministic_recovery_used:") for w in packet["warnings"])
    assert packet["provider_attempts"][-1]["provider"] == "deterministic_recovery"
    assert validate_article_quality(packet["canonical_article_draft"]) == []
