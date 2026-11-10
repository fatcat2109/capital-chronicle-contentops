"""Platform prohibitions stop requests; held data still reaches the feed consumer."""
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from live_contentops import neo_destination_handoff_v1 as handoff
from live_contentops import x_list_feed_v1 as feed
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_neo_executor_v1 import NativeNeoExecutor
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator, DEFINITE_NO_WRITE


def fail(*args, **kwargs):
    pytest.fail("prohibited route reached a browser or constructed a request")


@pytest.mark.parametrize("destination", list(handoff.NON_API_AUTOMATION_PROHIBITED))
@pytest.mark.parametrize("action", ["publish", "amend_existing"])
def test_barred_route_refused_before_request(monkeypatch, destination, action):
    adapter = handoff.NeoDestinationHandoff(native_executor=fail)
    monkeypatch.setattr(adapter, "request", fail)
    kwargs = dict(destination=destination, intent={}, authorization_context={})
    if action == "amend_existing":
        kwargs.update(public_object_id="old", public_object_url="https://example.org/old")
    result = getattr(adapter, action)(**kwargs)
    assert result["definite_no_write"] and not result["public_write_performed"]
    assert result["reason_code"] == handoff.NON_API_AUTOMATION_PROHIBITED[destination]


def test_new_entry_in_existing_bar_list_is_consumed(monkeypatch):
    monkeypatch.setitem(handoff.NON_API_AUTOMATION_PROHIBITED, "substack_notes", "TEST_PLATFORM_RULE")
    adapter = handoff.NeoDestinationHandoff(native_executor=fail)
    monkeypatch.setattr(adapter, "request", fail)
    assert adapter.publish(destination="substack_notes", intent={}, authorization_context={})[
        "reason_code"] == "TEST_PLATFORM_RULE"


@pytest.mark.parametrize("destination", list(handoff.NON_API_AUTOMATION_PROHIBITED))
@pytest.mark.parametrize("action", ["PUBLISH", "EDIT_EXISTING"])
def test_direct_request_cannot_bypass_bar(destination, action):
    with pytest.raises(ValueError, match=handoff.NON_API_AUTOMATION_PROHIBITED[destination]):
        handoff.NeoDestinationHandoff().request(destination=destination, action=action, intent={})


@pytest.mark.parametrize("action", ["PUBLISH", "EDIT_EXISTING"])
def test_pending_request_cannot_be_begun_after_route_is_barred(tmp_path, action):
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    store.create_work_item(story_id="s", work_item_id="work", title="test", target_surface="test")
    executor = NativeNeoExecutor(store, operation_id="op", output_dir=tmp_path,
                                 native_invocation_id="controlled", allow_publish=True)
    request = {"destination": "linkedin", "action": action, "work_item_id": "work"}
    request["request_sha256"] = sha256_of(request)
    key = request["request_sha256"]
    executor._put(key, "request", {"request": request}, "work")
    with pytest.raises(ValueError, match="LINKEDIN_NON_API_AUTOMATION_PROHIBITED"):
        executor.begin(key)
    assert executor._get(key, "started") is None
    assert executor(request)["definite_no_write"]
    # A real older attempted action remains ambiguous, never relabelled no-write.
    executor._put(key, "started", {"native_invocation_id": "earlier"}, "work")
    assert executor(request)["status"] == "UNKNOWN_WRITE"


@pytest.mark.parametrize("destination", ["youtube", "linkedin_company"])
def test_restored_article_route_reaches_live_coordinator_transport(tmp_path, destination):
    from test_publication_coordinator_v1 import _coordinator, _quality_plan, _set_mode
    store, transport, coordinator = _coordinator(tmp_path)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    plan = _quality_plan()
    row = next(r for r in coordinator.register_plan("work-1", plan)["registered"]
        if r["destination"] == destination)
    result = coordinator._dispatch_message(store.get_outbox_message(row["message_id"]),
        canonical_url="https://capitalchronicle.substack.com/p/test")
    assert result["status"] == "DISPATCH_CONFIRMED"
    assert transport.publish_calls == transport.readback_calls == [destination]


def test_adapter_preserves_a_claimed_write_and_its_saved_return(tmp_path, monkeypatch):
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    store.create_work_item(story_id="s", work_item_id="work", title="test", target_surface="test")
    executor = NativeNeoExecutor(store, operation_id="op", output_dir=tmp_path,
                                 native_invocation_id="controlled", allow_publish=True)
    request = {"destination": "linkedin", "action": "PUBLISH", "work_item_id": "work",
               "dispatch_attempt_identity": "exact-dispatch"}
    request["request_sha256"] = sha256_of(request)
    key = request["request_sha256"]
    executor._put(key, "request", {"request": request}, "work")
    executor._put(key, "started", {"native_invocation_id": "earlier"}, "work")
    adapter = handoff.NeoDestinationHandoff(native_executor=executor)
    monkeypatch.setattr(adapter, "request", fail)
    kwargs = dict(destination="linkedin", intent={"work_item_id": "work"},
                  authorization_context={"dispatch_attempt_identity": "exact-dispatch"})
    assert adapter.publish(**kwargs)["status"] == "UNKNOWN_WRITE"
    saved = {"status": "SUCCESS", "public_object_id": "old-observed-id"}
    executor._put(key, "response", {"result": saved}, "work")
    assert adapter.publish(**kwargs) == saved


def test_retained_sidecar_reaches_feed_without_browser_bootstrap(tmp_path, monkeypatch):
    now = datetime(2026, 11, 10, 1, tzinfo=timezone.utc)
    sidecar = tmp_path / "sidecars"
    sidecar.mkdir()
    tweet = str((int(now.timestamp() * 1000) - feed.X_EPOCH_MS) << 22)
    (sidecar / "step1_headline_sidecar_2026_11_10.jsonl").write_text(json.dumps({
        "tweet_id": tweet, "tweet_url": f"https://x.com/financialjuice/status/{tweet}",
        "headline_text": "Retained source lead", "author_handle": "financialjuice",
        "captured_at_utc": "2026-11-10T01:00:00Z"}) + "\n", encoding="utf-8")
    runner = feed.FeedRunner(feed_path=tmp_path / "feed.json", log_path=tmp_path / "log.jsonl",
                             sidecar_dir=sidecar, now_fn=lambda: now, capture_factory=fail)
    monkeypatch.setattr(runner, "_browser_ready", lambda: {"ready": False, "detail": "CONTROLLED_TEST"})
    result = runner.iterate()
    assert result["capture"]["state"] == "BROWSER_NOT_READY"
    exported = json.loads((tmp_path / "feed.json").read_text(encoding="utf-8"))
    assert exported["rows"][0]["text"] == "Retained source lead"
    assert result["feed_written"] and result["rows"] == 1


def test_review_has_sources_for_every_route_and_matches_the_live_bar_list():
    record = json.loads((Path(__file__).parents[1] / "docs/publisher/CC-393/platform-rules.json").read_text(encoding="utf-8"))
    expected = {
        "substack_posts", "substack_notes", "linkedin_company_neo", "youtube_community_neo",
        "telegram_bot_api", "discord_api", "threads_api", "facebook_page_api", "instagram_api",
        "linkedin_member_api", "x_official_api", "x_list_cdp", "fxstreet_contributor",
        "investing_contributor", "seekingalpha_contributor", "tradingview_ideas",
        "candidate_substack_notes", "substack_recommendations", "event_frozen_call_hash",
        "metaculus_ai_tournament", "partner_pilot", "vietnam_gold_telegram", "vietnam_gold_zalo"}
    assert {r["id"] for r in record["routes"]} == expected
    sources = {s["id"]: s for s in record["sources"]}
    for source in sources.values():
        assert source["classification"] in {"PRIMARY", "SECONDARY"}
        assert source["url"].startswith("https://") and source["read_at_utc"].endswith("Z")
        assert len(source["quotes"]) <= 2
    for route in record["routes"]:
        profile = record["policy_profiles"][route["policy_profile"]]
        assert set(profile) == {"automation", "ai_content", "financial_content", "identity", "account_steps"}
        for rule_id in profile.values():
            rule = record["rules"][rule_id]
            assert rule["source_ids"] and set(rule["source_ids"]) <= sources.keys()
            if rule["status"] == "NOT_FOUND":
                assert rule["search_queries"]
    # The dated decision-109 review stays exact; decisions 112/121 reopen routes.
    assert {k: v for k, v in record["enforcement"]["neo_barred_destinations"].items()
            if k not in {"x", "linkedin_company", "youtube"}} == handoff.NON_API_AUTOMATION_PROHIBITED
    assert record["consumer"]["owner"] == "Ops Product"


