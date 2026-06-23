from live_contentops.live_readonly_probe_registry import WRITE_ENDPOINT_DENYLIST, build_blocked_probe_report, build_probe_plans


def test_probe_plans_have_no_write_endpoint_names_and_no_retry():
    plans = build_probe_plans()
    for plan in plans:
        lowered = plan.path.lower()
        assert all(name.lower() not in lowered for name in WRITE_ENDPOINT_DENYLIST)
        assert plan.auto_retry is False
        assert plan.raw_response_persisted is False
        assert plan.request_budget in {0, 1}


def test_blocked_report_has_no_raw_response_and_budget_enforced():
    report = build_blocked_probe_report()
    assert report["raw_response_persisted"] is False
    assert report["auto_retry"] is False
    for result in report["results"]:
        assert result["raw_response_persisted"] is False
        assert result["auto_retry"] is False
        assert result["request_count"] == 0
        assert result["result_classification"] == "blocked_not_attempted"
