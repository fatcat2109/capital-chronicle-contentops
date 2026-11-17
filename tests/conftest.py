import os

import pytest


@pytest.fixture(autouse=True)
def _disable_intake_lane_for_tests(monkeypatch, tmp_path):
    monkeypatch.setenv("CONTENTOPS_DAILY_APP_DISABLE_INTAKE_LANE", "1")
    # CC-297: tests and the processes they start never read Credential Manager or the live user
    # environment, so a test that removes a key can never post with Jim's real one.
    monkeypatch.setenv("CAPITAL_CHRONICLE_SECRET_STORE", "environment-only")
    # Unit tests must never consume or mutate the operator's canonical Runtime control state.
    from live_contentops import llm_cost_governor_v1, llm_operator_control_v1

    isolated = tmp_path / "llm_controls"
    monkeypatch.setattr(llm_operator_control_v1, "RUNTIME_CONTROL_ROOT", isolated)
    monkeypatch.setattr(llm_cost_governor_v1, "RUNTIME_CONTROL_ROOT", isolated)
    # CC-509's new cache/network boundary is isolated for every unit test.
    # Tests inject their own response; none fetches a public quote or reads
    # the operating Main/Data stores just because it prepares a reply.
    from live_contentops import public_market_quote_v1, chart_price_reference_v1, publication_image_contract_v1
    monkeypatch.setattr(public_market_quote_v1, "ROOT", tmp_path / "public-quotes")
    monkeypatch.setattr(chart_price_reference_v1, "PLAN_STATUS_PATH", tmp_path / "plan-status.json")
    monkeypatch.setattr(chart_price_reference_v1, "BAR_STORE", tmp_path / "bars.sqlite3")
    monkeypatch.setattr(publication_image_contract_v1, "QUOTE_ROOT", tmp_path / "main-captures")
    def no_live_quote(url):
        raise public_market_quote_v1.QuoteError("PUBLIC_QUOTE_TEST_RESPONSE_NOT_SUPPLIED")
    monkeypatch.setattr(public_market_quote_v1, "http_read", no_live_quote)
    from live_contentops import x_reply_base_rates_v1
    def no_live_statistics(*args, **kwargs):
        raise ValueError("BASE_RATE_TEST_PRODUCER_NOT_SUPPLIED")
    monkeypatch.setattr(x_reply_base_rates_v1, "Producer", no_live_statistics)
    yield
