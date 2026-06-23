import pytest

from live_contentops.live_readonly_probe_registry import (
    WRITE_ENDPOINT_DENYLIST,
    ProbePlan,
    build_blocked_probe_report,
    build_probe_plans,
    run_http_get_probe,
)


def test_probe_plans_have_no_write_endpoint_names_and_no_retry():
    plans = build_probe_plans()
    for plan in plans:
        lowered = plan.path.lower()
        assert all(name.lower() not in lowered for name in WRITE_ENDPOINT_DENYLIST)
        assert plan.auto_retry is False
        assert plan.raw_response_persisted is False
        assert plan.request_budget in {0, 1}
        if plan.method == "GET":
            assert plan.redirect_policy == "redirect_disabled_fail_closed"


def test_blocked_report_has_no_raw_response_and_budget_enforced():
    report = build_blocked_probe_report()
    assert report["raw_response_persisted"] is False
    assert report["auto_retry"] is False
    for result in report["results"]:
        assert result["raw_response_persisted"] is False
        assert result["auto_retry"] is False
        assert result["request_count"] == 0
        assert result["result_classification"] == "blocked_not_attempted"


def test_telegram_url_validation_blocks_wrong_host_scheme_path_and_query():
    plan = next(p for p in build_probe_plans() if p.endpoint_family == "telegram_bot_identity")
    bad_host = run_http_get_probe(plan, "https://evil.example/bot123456:ABCdefghijklmnopqrstuvwxyz123456/getMe", {})
    assert "final_host_mismatch" in bad_host.blocked_reasons
    bad_scheme = run_http_get_probe(plan, "http://api.telegram.org/bot123456:ABCdefghijklmnopqrstuvwxyz123456/getMe", {})
    assert "final_scheme_mismatch" in bad_scheme.blocked_reasons
    bad_path = run_http_get_probe(plan, "https://api.telegram.org/bot123456:ABCdefghijklmnopqrstuvwxyz123456/sendMessage", {})
    assert "final_path_mismatch" in bad_path.blocked_reasons
    bad_query = run_http_get_probe(plan, "https://api.telegram.org/bot123456:ABCdefghijklmnopqrstuvwxyz123456/getMe?token=bad", {})
    assert "query_key_not_allowlisted" in bad_query.blocked_reasons


def test_getchat_allows_only_chat_id_query_key():
    plan = next(p for p in build_probe_plans() if p.endpoint_family == "telegram_channel_read")
    blocked = run_http_get_probe(plan, "https://api.telegram.org/bot123456:ABCdefghijklmnopqrstuvwxyz123456/getChat?chat_id=-1001234567890&extra=1", {})
    assert "query_key_not_allowlisted" in blocked.blocked_reasons


def test_probe_plan_not_in_allowlist_fails_closed():
    plan = ProbePlan("telegram_remote_operator", "telegram_bot_identity", "GET", "https", "api.telegram.org", "/bot<redacted>/getMe", 10, "redirect_disabled_fail_closed", 2, False, False, "official_docs_checked")
    with pytest.raises(ValueError, match="probe_plan_not_in_batch_b_allowlist"):
        run_http_get_probe(plan, "https://api.telegram.org/bot123456:ABCdefghijklmnopqrstuvwxyz123456/getMe", {})
