from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from live_contentops import heavy_news_quotes_v1 as quotes, sourced_replies_v1 as replies
from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops import publication_image_contract_v1 as images
from live_contentops import x_reply_pack_v1 as packs
from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _durable_intent_inputs
from live_contentops.event_article_guard_v1 import PUBLIC_NOTICE
from test_publication_coordinator_v1 import FixtureTransport, _coordinator, _set_mode
from test_tradingview_snapshot_cc314 import tradingview_worker


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    now = datetime.now(timezone.utc)
    transport = FixtureTransport()
    store, _, coordinator = _coordinator(tmp_path, runtime=transport)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    store.register_outbox_message(message_id="desk", work_item_id="work-1", destination="internal:cc-report-feed",
        payload=json.dumps({"desk_record_sources": [{"title": "Desk rates context", "known_at_utc": (now-timedelta(minutes=2)).isoformat(),
            "binding": {"fields": [{"value": .8, "display": "Price dispersion is 0.8%.", "rights_class": "CC_OWN_ANALYSIS",
                                     "citation": "dispersion", "field_path": "/volatility"}], "sources": []}}]}))
    source = packs.held_sources(store)[0]
    media = tmp_path / "heavy-quote-123/media"
    shot = tv.capture("US500", "240", media, worker=tradingview_worker([]))
    shot["captured_at_utc"] = now.isoformat()
    shot["price_scale_check"] = images.not_compared("US500", shot, images.QUOTE_ABSENT[0])
    image = tv.snapshot_asset("US500", "Market context", shot, media)
    row = {"target_id": "123", "target_url": "https://x.com/FirstSquawk/status/123", "target_author": "FirstSquawk",
        "target_text": "A heavy policy surprise.", "source_posted_at_utc": (now-timedelta(seconds=20)).isoformat(),
        "source": source, "fact_text": source["excerpt"], "text": "Rates drive stocks. Price dispersion is 0.8%. Chart: TradingView. " + PUBLIC_NOTICE,
        "market": "US500", "media_folder": str(media), "image": image}
    return store, coordinator, transport, row, now


def test_real_consumer_freezes_quote_edge_figure_and_chart_then_reuses_confirmation(prepared, tmp_path):
    store, coordinator, transport, raw, now = prepared
    row = quotes.stage(store, raw, now=now)
    result = replies.publish(store, row["key"], coordinator=coordinator, root=tmp_path, now=now)
    assert transport.publish_calls == ["x"], result
    assert result["reply"]["readback_url"]
    intent = json.loads(store.list_outbox_messages(destination="x")[0]["payload"])
    actual = _durable_intent_inputs(intent)
    assert actual["payloads"]["x"]["quote_to_id"] == "123"
    assert "reply_to_id" not in actual["payloads"]["x"]
    assert actual["media_assets"] == [row["image"]]
    assert intent["quote_parent"] == quotes.quote_parent(row)
    assert "published_content_export" not in intent and not intent["canonical_url"]
    assert images.validate_write(coordinator, intent, "x")["first_image_type"] == "TRADINGVIEW_MARKET_CHART"
    replies.publish(store, row["key"], coordinator=coordinator, root=tmp_path, now=now+timedelta(days=1))
    assert transport.publish_calls == ["x"]


def test_fresh_write_deadline_never_prevents_older_uncertain_write_readback(prepared, tmp_path):
    store, coordinator, transport, raw, now = prepared
    transport.raise_after_write, transport.ambiguous = True, True
    row = quotes.stage(store, raw, now=now)
    replies.publish(store, row["key"], coordinator=coordinator, root=tmp_path, now=now)
    replies.publish(store, row["key"], coordinator=coordinator, root=tmp_path, now=now+timedelta(minutes=10))
    assert transport.publish_calls == ["x"]
    assert not replies.report_one(store, row)["readback_url"]


def test_attempt_cap_includes_uncertain_and_preserves_source_idempotency(prepared):
    store, _, _, raw, now = prepared
    row = quotes.stage(store, raw, now=now)
    quotes.reserve(store, row, now)
    quotes.reserve(store, row, now)
    for i in range(4):
        store.create_work_item(story_id=str(i), title="quote", target_surface="INTERNAL", work_item_id=str(i))
        quotes.reserve(store, {**row, "key":str(i), "target_id":str(i)}, now)
    with pytest.raises(ValueError, match="FIVE_QUOTES_PER_DAY"):
        quotes.reserve(store, {**row, "key":"six", "target_id":"six"}, now)
    assert len(store.list_outbox_messages(destination=replies.RESERVATIONS)) == 5


@pytest.mark.parametrize("change,cause", [
    ({"text":"Price dispersion is 0.9%. Chart: TradingView. " + PUBLIC_NOTICE}, "FIGURE_BINDING"),
    ({"market":"XAUUSD"}, "SNAPSHOT_BINDING_INVALID"),
    ({"media_folder":"C:/another/media"}, "OUTSIDE_ITEM_MEDIA"),
    ({"target_url":"https://x.com/Other/status/123"}, "SOURCE_IDENTITY"),
    ({"text":"Rates drive stocks... Price dispersion is 0.8%. Chart: TradingView. " + PUBLIC_NOTICE}, "CUT_SENTENCE"),
])
def test_actual_copy_identity_and_media_defects_refuse_before_publication(prepared, change, cause):
    store, _, _, raw, now = prepared
    with pytest.raises(ValueError, match=cause):
        quotes.stage(store, {**raw, **change}, now=now)
    assert store.list_platform_dispatches() == []


def test_source_age_is_measured_from_post_not_feed_refresh(prepared):
    store, _, _, raw, now = prepared
    with pytest.raises(ValueError, match="OUTSIDE_FIVE_MINUTES"):
        quotes.stage(store, {**raw, "source_posted_at_utc":(now-timedelta(minutes=5)).isoformat()}, now=now)
    feed = {"generated_at_utc":now.isoformat(), "rows":[{"url":raw["target_url"], "tweet_id":"123", "handle":"FirstSquawk",
        "text":raw["target_text"], "posted_utc":(now-timedelta(minutes=6)).isoformat()}]}
    assert quotes.candidates(feed, now=now)[0] == []


def test_changed_bound_source_and_changed_quote_intent_are_rejected(prepared, tmp_path):
    store, coordinator, _, raw, now = prepared
    row = quotes.stage(store, raw, now=now)
    coordinator.register_plan(row["key"], replies.plan_for(store, row["key"], root=tmp_path))
    intent = json.loads(store.list_outbox_messages(destination="x")[0]["payload"])
    intent["quote_parent"]["public_object_id"] = "other"
    with pytest.raises(ValueError, match="QUOTE_INTENT_CHANGED"):
        replies.validate_intent(store, intent)
    source = deepcopy(row["source"]);source["excerpt"] = "Unbound figure 0.8%."
    with pytest.raises(ValueError, match="FIGURE_BINDING"):
        quotes.validate({**row,"source":source}, store=store)


def test_one_minute_tick_calls_roles_and_live_publisher_and_idle_tick_uses_no_models(prepared, tmp_path, monkeypatch):
    store, coordinator, transport, raw, now = prepared
    feed = tmp_path / "feed.json"
    feed.write_text(json.dumps({"generated_at_utc":now.isoformat(), "rows":[{"url":raw["target_url"], "tweet_id":"123",
        "handle":"FirstSquawk", "text":raw["target_text"], "is_retweet":False,"tags":[],
        "posted_utc":raw["source_posted_at_utc"]}]}))
    roles = []
    def call(role, prompt, root):
        roles.append(role)
        value = {"filter":{"target_id":"123","market":"US500","reason":"heavy policy change"},
            "prepare":{"source_id":raw["source"]["source_id"],"fact_text":raw["fact_text"],"force":"Rates drive stocks"},
            "write":{"text":raw["text"],"alt_text":"TradingView chart of the S&P 500."}}[role]
        return value, {"configuration_status":"CONFIGURED_NOT_OBSERVED"}
    def capture(market, interval, media):
        shot = tv.capture(market, "240", media, worker=tradingview_worker([]))
        shot["captured_at_utc"] = now.isoformat()
        shot["price_scale_check"] = images.not_compared(market, shot, images.QUOTE_ABSENT[0])
        return shot
    result = quotes.refresh_due(store, feed_path=feed, root=tmp_path / "quotes", now=now, call=call,
                               capture=capture, coordinator_for=lambda *a:coordinator)
    assert roles == ["filter","prepare","write"] and transport.publish_calls == ["x"], result
    assert quotes.refresh_due(store, feed_path=feed, root=tmp_path / "quotes", now=now,
        call=lambda *a:pytest.fail("same source repeated"))["status"] == "NO_FRESH_ORIGINAL_NEWS"


def test_daily_boundary_deadline_and_fourteen_day_observation_are_actual_clocks(prepared):
    store, _, _, raw, now = prepared
    row = quotes.stage(store, raw, now=now)
    assert quotes.audience_review(store, now=now)["status"] == "FIRST_LIVE_QUOTE_PENDING"
    late = datetime(2026,11,17,16,59,59,tzinfo=timezone.utc)
    row.update(created_at_utc=late.isoformat(), source_posted_at_utc=(late-timedelta(seconds=5)).isoformat())
    assert replies.clock(quotes.quote_parent(row)["deadline_at_utc"]) == late+timedelta(seconds=1)
