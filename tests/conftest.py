import os
from pathlib import Path

import pytest

from isolated_python import sitecustomize as test_isolation

test_isolation.install()


@pytest.fixture(autouse=True)
def _report_test_isolation_violations(monkeypatch, tmp_path):
    report = tmp_path / "live-io-violation.txt"
    support_root = Path(test_isolation.__file__).parent
    pythonpath = os.environ.get("PYTHONPATH")
    monkeypatch.setenv("PYTHONPATH", str(support_root) + (os.pathsep + pythonpath if pythonpath else ""))
    monkeypatch.setenv(test_isolation.REPORT_ENV, str(report))
    yield
    if report.exists():
        pytest.fail(report.read_text(encoding="utf-8").strip())


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


@pytest.fixture
def stub_minute_side_effects(monkeypatch):
    # The minute CLI calls these independent phases even for stale or rejected
    # plan exports. Each entrypoint test overrides the phases it exercises.
    from live_contentops import (
        audience_collection_v1, call_followups_v1, daily_trend_board_v1, event_pack_v1,
        event_timestamp_v1, heavy_news_quotes_v1, model_invocation_usage_v1, neo_endpoint_executor_v1,
        pinned_result_scorecard_v1, plan_analysis_pages_v1, plan_reader_editorial_v1,
        public_draft_claims_v1, substack_daily_note_v1,
        x_reply_bot_v1, x_reply_tabs_v1,
    )

    def idle(*args, **kwargs):
        return {"status": "NO_DUE_WORK"}

    for module, name in (
        (call_followups_v1, "minute_due"),
        (daily_trend_board_v1, "run_due"),
        (event_pack_v1, "run_due_packs"),
        (event_timestamp_v1, "maintain_timestamps"),
        (heavy_news_quotes_v1, "refresh_due"),
        (model_invocation_usage_v1, "import_native_invocations"),
        (neo_endpoint_executor_v1, "resume_stored_requests"),
        (pinned_result_scorecard_v1, "refresh_scorecard"),
        (plan_reader_editorial_v1, "run_due"),
        (public_draft_claims_v1, "review_plan_copy"),
        (substack_daily_note_v1, "run_due"),
        (x_reply_bot_v1, "refresh_due"),
        (x_reply_bot_v1, "observe_due"),
        (x_reply_tabs_v1, "refresh_due"),
    ):
        monkeypatch.setattr(module, name, idle)

    monkeypatch.setattr(audience_collection_v1, "run_collection", lambda *a, **kw: {"collected": 0})
    monkeypatch.setattr(plan_analysis_pages_v1, "resume_discord_links", lambda *a, **kw: [])
    monkeypatch.setattr(plan_reader_editorial_v1, "start_page_draft_worker",
                        lambda *a, **kw: {"status": "NO_DUE_PAGE_DRAFT"})
