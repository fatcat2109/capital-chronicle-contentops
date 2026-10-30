import json

from live_contentops.channel_engagement_v1 import CHANNELS, weekly_channel_engagement, render_engagement_digest
from live_contentops import destination_performance_observer_v1 as observer


def fixture(channel="x", *, object_id="123", suffix="a"):
    dispatch = {"dispatch_id": "dispatch_" + suffix, "message_id": suffix, "platform": channel,
        "public_object_id": object_id, "public_object_url": "https://capitalchronicle.substack.com/p/test" if channel == "substack" else "https://example.test/public/" + object_id,
        "status": "DISPATCH_CONFIRMED"}
    reconciliation = {"reconciliation_id": "reconciliation_" + suffix, "status": "RECONCILED_CONFIRMED"}
    readback = {"dispatch_id": dispatch["dispatch_id"], "readback_data": '{"verified":true}'}
    def sample(metrics, states, clock="2026-10-30T10:00:00Z"):
        return {"dispatch_id": dispatch["dispatch_id"], "platform": channel, "public_object_id": object_id,
            "collected_at_utc": clock, "collection_status": "COLLECTED", "learning_eligible": 1,
            "metrics_native_json": json.dumps(metrics), "metric_availability_json": json.dumps(states)}
    return dispatch, reconciliation, readback, sample


def test_all_ten_channels_named_when_no_metric_exists():
    result = weekly_channel_engagement(dispatches=[], reconciliations=[], readbacks=[], observations=[], week_ending="2026-10-30")
    assert tuple(row["channel"] for row in result["channels"]) == CHANNELS
    assert all(row["native_counter_sums"] is None and row["missing_causes"] for row in result["channels"])
    assert "linkedin_company" in render_engagement_digest(result)


def test_weekly_digest_uses_latest_cumulative_snapshot_once_and_preserves_real_zero():
    dispatch, reconciliation, readback, sample = fixture()
    observations = [sample({"views": 10, "likes": 0}, {"views": "AVAILABLE", "likes": "AVAILABLE"}, "2026-10-29T10:00:00Z"),
        sample({"views": 15, "likes": 0}, {"views": "AVAILABLE", "likes": "AVAILABLE"})]
    result = weekly_channel_engagement(dispatches=[dispatch], reconciliations=[reconciliation], readbacks=[readback],
        observations=observations, week_ending="2026-10-30")
    x = next(row for row in result["channels"] if row["channel"] == "x")
    assert x["native_counter_sums"] == {"views": 15, "likes": 0}
    assert x["objects_with_metrics"] == 1
    assert "not incremental weekly activity" in result["metric_basis"]


def test_linkedin_member_company_and_rates_remain_separate():
    records = [fixture("linkedin", suffix="member"), fixture("linkedin_company", suffix="company")]
    samples = [records[0][3]({"likes": 2, "open_rate": 0.4}, {"likes": "AVAILABLE", "open_rate": "AVAILABLE"}),
        records[1][3]({"likes": 7}, {"likes": "AVAILABLE"})]
    result = weekly_channel_engagement(dispatches=[r[0] for r in records], reconciliations=[r[1] for r in records],
        readbacks=[r[2] for r in records], observations=samples, week_ending="2026-10-30")
    member = next(r for r in result["channels"] if r["channel"] == "linkedin")
    company = next(r for r in result["channels"] if r["channel"] == "linkedin_company")
    assert member["native_counter_sums"] == {"likes": 2}
    assert company["native_counter_sums"] == {"likes": 7}
    assert member["non_additive_native_values"]["open_rate"][0]["value"] == 0.4


def test_unavailable_latest_value_never_inherits_an_older_counter_or_fills_zero():
    dispatch, reconciliation, readback, sample = fixture()
    old = sample({"views": 10}, {"views": "AVAILABLE"}, "2026-10-29T10:00:00Z")
    latest = sample({}, {"views": "AUTH_REQUIRED"})
    latest["collection_status"] = "AUTH_REQUIRED"
    result = weekly_channel_engagement(dispatches=[dispatch], reconciliations=[reconciliation], readbacks=[readback],
        observations=[old, latest], week_ending="2026-10-30")
    x = next(r for r in result["channels"] if r["channel"] == "x")
    assert x["native_counter_sums"] is None and "AUTH_REQUIRED" in x["missing_causes"]


def test_unknown_public_write_and_invalid_counter_are_excluded():
    dispatch, reconciliation, readback, sample = fixture()
    bad = sample({"views": True}, {"views": "AVAILABLE"})
    result = weekly_channel_engagement(dispatches=[dispatch], reconciliations=[reconciliation], readbacks=[readback],
        observations=[bad], week_ending="2026-10-30")
    assert next(r for r in result["channels"] if r["channel"] == "x")["native_counter_sums"] is None
    dispatch["status"] = "UNKNOWN_WRITE"
    result = weekly_channel_engagement(dispatches=[dispatch], reconciliations=[reconciliation], readbacks=[readback],
        observations=[sample({"likes": 9}, {"likes": "AVAILABLE"})], week_ending="2026-10-30")
    x = next(r for r in result["channels"] if r["channel"] == "x")
    assert x["native_counter_sums"] is None and "UNCONFIRMED_OR_MISMATCHED_PUBLIC_OBJECT" in x["missing_causes"]


def test_missing_provider_fields_are_not_manufactured_as_zero(monkeypatch):
    monkeypatch.setattr(observer, "_meta_token", lambda *_: "CONTROLLED_NOT_A_REAL_TOKEN")
    monkeypatch.setattr(observer, "_get_json", lambda *_: {"id": "exact", "like_count": 0})
    instagram = observer.collect_current_authorized_destination_metrics(destination="instagram_business", public_object_id="exact")
    assert instagram["metrics"] == {"likes": 0}
    assert instagram["availability"]["comments"] == "NOT_EXPOSED"
    facebook = observer.collect_current_authorized_destination_metrics(destination="facebook_page", public_object_id="exact")
    assert facebook["metrics"] == {} and facebook["availability"]["shares"] == "NOT_EXPOSED"


def test_threads_reply_page_is_a_sample_not_an_invented_total(monkeypatch):
    monkeypatch.setattr(observer, "_meta_token", lambda *_: "CONTROLLED_NOT_A_REAL_TOKEN")
    monkeypatch.setattr(observer, "_get_json", lambda *_: {"data": [{"id": "one", "text": "Controlled reply"}],
        "paging": {"next": "not-followed"}})
    value = observer.collect_current_authorized_destination_metrics(destination="threads", public_object_id="exact")
    assert value["metrics"] == {"reply_sample_count": 1}
    assert value["availability"]["replies"] == "NOT_EXPOSED"
    assert value["provider_requests"] == 1


def test_rejected_provider_read_is_one_actual_request_not_a_missing_binding():
    from urllib.error import HTTPError
    value = observer._http_failure("facebook_page", HTTPError("https://example.test/", 403, "Forbidden", {}, None))
    assert value["status"] == "PERMISSION_REQUIRED"
    assert value["provider_requests"] == 1 and value["metrics"] == {}
