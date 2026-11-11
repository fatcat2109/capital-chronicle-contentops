from datetime import datetime, timedelta, timezone
import json
from urllib.parse import parse_qs, urlparse

import pytest

from live_contentops import x_reply_pack_v1 as packs
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.event_article_guard_v1 import PUBLIC_NOTICE
from live_contentops.public_time_v1 import public_timestamp

NOW = datetime(2026, 11, 11, 0, 30, tzinfo=timezone.utc)


def post(post_id="123", handle="FirstSquawk", age=10, text="Gold moves after CPI", **extra):
    return {"handle": handle, "text": text, "tweet_id": post_id,
            "url": f"https://x.com/{handle}/status/{post_id}",
            "posted_utc": (NOW - timedelta(minutes=age)).isoformat(), "is_retweet": False, **extra}


@pytest.fixture
def setup(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3", auto_migrate=True)
    key = "existing-public-desk-scan"
    store.create_work_item(story_id=key, title="Existing public records", target_surface="PRIVATE", work_item_id=key)
    source = {"source_id": "BLS", "rights_class": "BLS_OFFICIAL_PUBLIC_DERIVED", "attribution": "BLS"}
    field = {"citation": "export#ECI/wages", "field_path": "/wages", "display": "0.7",
             "value": 0.7, "rights_class": "BLS_OFFICIAL_PUBLIC_DERIVED", "unit": "%", "source_ids": ["BLS"]}
    data = {"desk_record_sources": [{"title": "BLS ECI civilian wages, three-month change",
             "known_at_utc": (NOW - timedelta(days=12)).isoformat(),
             "binding": {"fixture": False, "record_type": "event_card", "fields": [field], "sources": [source]}}]}
    store.register_outbox_message(message_id=key, work_item_id=key, destination="internal:cc-report-feed", payload=json.dumps(data))
    feed = tmp_path / "feed.json"
    packs.save_json(feed, {"generated_at_utc": NOW.isoformat(), "rows": [post()]})
    return store, feed, tmp_path


def response_for(setup, *, items=None, **extra):
    store, feed, root = setup
    ready = packs.prepare(store, feed_path=feed, output_root=root, now=NOW)
    request = packs.read_json(ready["request_path"])
    source = request["sources"][0]
    text = ("Wages are another test: BLS civilian wages rose 0.7% over three months. "
            + source["public_timestamp"] + ". " + PUBLIC_NOTICE)
    response = {"request_sha256": ready["request_sha256"], "editorial_call": {
        "configured_model": "observed-launch-model", "configured_effort": "max",
        "runtime_model": None, "runtime_effort": None, "telemetry": "CONFIGURED_NOT_OBSERVED"},
        "items": [{"post_id": "123", "source_id": source["source_id"], "fact_text": "0.7",
                   "draft_text": text, "point": "Use wages to test a prices-only argument",
                   "addition": "BLS civilian wages rose 0.7%", "reply_shape": "priced_in_comparison"}],
        **extra}
    if items is not None:
        response["items"] = items
    path = root / "native-response.json"
    packs.save_json(path, response)
    return ready, response, path


def build(setup, ready, response, **kwargs):
    store, feed, root = setup
    return packs.build(store, feed_path=feed, output_root=root, now=NOW,
                       request_path=ready["request_path"], response_path=response, **kwargs)


def test_installed_runner_contract_feeds_html_and_desk_with_no_agent_write(setup):
    store, _, _ = setup
    ready, response, path = response_for(setup)
    result = build(setup, ready, path)
    saved = packs.read_json(result["pack_path"])
    assert result["item_count"] == 1 and result["public_write_performed"] is False
    assert result["pack_path"].endswith("reply-pack-20261111.json")  # Same private desk day as CC-457.
    item = saved["items"][0]
    query = parse_qs(urlparse(item["intent_url"]).query)
    assert query == {"in_reply_to": ["123"], "text": [response["items"][0]["draft_text"]]}
    assert item["sources"][0]["known_at_utc"] and len(item["draft_text"]) <= 280
    assert packs.read_pack(result["pack_path"], now=NOW)["item_count"] == 1
    html = __import__("pathlib").Path(result["html_path"]).read_text(encoding="utf-8")
    assert "Review reply on X" in html and "STALE" in html and "method=" not in html
    assert not store.list_outbox_messages(destination="x")
    assert not store.list_platform_dispatches()
    assert store.get_outbox_message(result["store_message_id"])["status"] == "PREPARED_FOR_JIM"
    assert build(setup, ready, path) == result


def test_freshness_identity_topic_retweets_and_duplicate_input():
    rows = [post(), post(), post("124", age=60), post("125", age=-1),
            post("126", text="Political appointment"), post("127", is_retweet=True),
            post("128", url="https://x.com/wrong/status/128")]
    selected, causes = packs.select_posts({"rows": rows}, handles={"firstsquawk"}, now=NOW)
    assert [p["post_id"] for p in selected] == ["123"]
    assert causes["POST_OUTSIDE_60_MINUTE_BUILD_WINDOW"] == 2
    assert causes["POST_IDENTITY_MISMATCH"] == 1


def test_mentions_and_quotes_use_same_pack_from_non_target_accounts():
    rows = [post("124", "Reader", text="@Capitalnicle what would disprove this?"),
            post("125", "Reader2", text="About this call", quoted_author_handle="Capitalnicle")]
    selected, _ = packs.select_posts({"rows": []}, mentions={"rows": rows}, handles=set(), now=NOW)
    assert len(selected) == 2 and all(r["kind"] == "mention" for r in selected)


@pytest.mark.parametrize("change,cause", [
    (lambda d: d.update(draft_text=d["draft_text"].replace("0.7%", "0.9%")), "EXACT_SOURCE_FACT"),
    (lambda d: d.update(draft_text=d["draft_text"] + " 99"), "UNBOUND_OR_CHANGED_NUMBER"),
    (lambda d: d.update(draft_text=d["draft_text"] + " Buy now."), "PROMOTION_OR_AI_LABEL"),
    (lambda d: d.update(draft_text=d["draft_text"] + " As an AI."), "PROMOTION_OR_AI_LABEL"),
    (lambda d: d.update(draft_text=d["draft_text"] + " DEMO account."), "PRIVATE"),
    (lambda d: d.update(draft_text=d["draft_text"] + " https://elsewhere.com"), "NOT_OWN_CONFIRMED_PAGE"),
    (lambda d: d.update(draft_text=d["draft_text"] + " elsewhere.com"), "NOT_OWN_CONFIRMED_PAGE"),
])
def test_public_copy_and_source_failures_do_not_become_usable_drafts(setup, change, cause):
    ready, response, path = response_for(setup)
    change(response["items"][0])
    packs.save_json(path, response)
    result = build(setup, ready, path)
    saved = packs.read_json(result["pack_path"])
    assert result["item_count"] == 0 and cause in saved["none_reason"]


def test_source_time_and_notice_are_bound(setup):
    ready, response, path = response_for(setup)
    source_time = public_timestamp((NOW - timedelta(days=12)).isoformat())
    response["items"][0]["draft_text"] = response["items"][0]["draft_text"].replace(source_time, "time omitted")
    packs.save_json(path, response)
    assert "SOURCE_TIME_REQUIRED" in build(setup, ready, path)["none_reason"]


def test_an_empty_pack_has_a_real_cause_and_no_filler(setup):
    ready, _, path = response_for(setup, items=[], omissions=[{"post_id": "123", "cause": "No useful priced-in comparison in held sources"}])
    result = build(setup, ready, path)
    assert result["item_count"] == 0
    assert "No useful priced-in comparison" in result["none_reason"]


def test_expired_targets_are_rechecked_at_build_and_reader_marks_stale(setup):
    ready, response, path = response_for(setup)
    result = build(setup, ready, path)
    assert packs.read_pack(result["pack_path"], now=NOW + timedelta(minutes=81))["items"][0]["stale"]
    store, feed, root = setup
    expired = packs.build(store, feed_path=feed, output_root=root, now=NOW + timedelta(minutes=51),
                          request_path=ready["request_path"], response_path=path)
    assert expired["item_count"] == 0 and expired["none_reason"]


def test_html_treats_post_text_as_text(setup):
    store, feed, _ = setup
    data = packs.read_json(feed)
    data["rows"][0]["text"] = 'Gold <script>alert("test")</script>'
    packs.save_json(feed, data)
    ready, _, path = response_for(setup)
    result = build(setup, ready, path)
    html = __import__("pathlib").Path(result["html_path"]).read_text(encoding="utf-8")
    assert '&lt;script&gt;alert' in html and '<script>alert' not in html


def test_private_field_never_enters_public_reply_sources(setup):
    store, _, _ = setup
    row = store.list_outbox_messages(destination="internal:cc-report-feed")[-1]
    data = json.loads(row["payload"])
    data["desk_record_sources"][0]["binding"]["fields"][0]["rights_class"] = "BROKER_PROXY_RAW_PRIVATE"
    with store.get_connection() as conn:
        conn.execute("UPDATE outbox_messages SET payload=? WHERE message_id=?", (json.dumps(data), row["message_id"]))
    assert packs.held_sources(store) == []


def test_request_bytes_and_original_post_bytes_cannot_be_replaced(setup):
    ready, response, path = response_for(setup)
    request = packs.read_json(ready["request_path"])
    request["candidates"][0]["post_text"] = "Changed post"
    packs.save_json(ready["request_path"], request)
    with pytest.raises(ValueError, match="REQUEST_CHANGED"):
        build(setup, ready, path)


def test_older_frozen_call_clock_and_retained_source_survive_new_feed_scan(setup):
    store, _, _ = setup
    key = "old-frozen-call"
    store.create_work_item(story_id=key, title="Frozen call", target_surface="PRIVATE", work_item_id=key)
    call = {"kind": "setup", "at_utc": (NOW - timedelta(hours=12)).isoformat(),
            "text": "Our oil view fails above 86.15.", "symbol": "USOIL"}
    store.register_outbox_message(message_id=key, work_item_id=key, destination="internal:plan-status-post", payload=json.dumps(call))
    ready, _, path = response_for(setup)
    sources = packs.held_sources(store)
    assert next(s for s in sources if s["source_id"] == key)["known_at_utc"] == call["at_utc"]
    latest = "new-public-desk-scan"
    store.create_work_item(story_id=latest, title="New scan", target_surface="PRIVATE", work_item_id=latest)
    store.register_outbox_message(message_id=latest, work_item_id=latest, destination="internal:cc-report-feed",
                                  payload=json.dumps({"desk_record_sources": []}))
    assert build(setup, ready, path)["item_count"] == 1  # Original exact source remains usable.


def manual_feed(setup, *, parent="123", handle="Capitalnicle", metrics=None, when=None):
    _, _, root = setup
    posted = NOW + timedelta(minutes=5)
    row = post("456", handle, text="Jim's edited reply with the same source fact.", age=-5,
               in_reply_to_status_id=parent)
    if metrics is not None:
        row.update(metrics=metrics, metrics_observed_at_utc=(when or posted + timedelta(hours=24)).isoformat())
    path = root / "held-own-replies.json"
    packs.save_json(path, {"generated_at_utc": (when or posted).isoformat(), "rows": [row]})
    return path, posted


def test_jims_edited_reply_joins_exact_parent_and_existing_24h_consumer(setup):
    store, _, _ = setup
    ready, _, response = response_for(setup)
    built = build(setup, ready, response)
    feed, posted = manual_feed(setup)
    result = packs.observe_manual_replies(store, reply_feed_path=feed, now=posted)
    assert len(result["observed"]) == 1 and result["public_write_performed"] is False
    record = result["observed"][0]
    dispatch = store.get_platform_dispatch(record["dispatch_id"])
    assert packs.clock(dispatch["dispatched_at"]) == posted
    assert dispatch["public_object_url"] == "https://x.com/Capitalnicle/status/456"
    message = json.loads(store.get_outbox_message(record["readback_message_id"])["payload"])
    assert message["pack_message_id"] == built["store_message_id"] and message["draft_edited"]
    assert store.list_readbacks_for_dispatch(dispatch["dispatch_id"])
    observation = store.get_performance_observation(record["daily_observation_id"])
    assert packs.clock(observation["scheduled_for_utc"]) == posted + timedelta(hours=24)
    assert json.loads(observation["metrics_native_json"]) == {}
    assert packs.report_manual_replies(store, now=posted)["cohorts"][0]["posted"] == 1
    assert packs.observe_manual_replies(store, reply_feed_path=feed, now=posted) == result
    assert not store.list_outbox_messages(destination="x")  # The dispatch is an observed manual object.


def test_collected_24h_metrics_keep_unavailable_distinct_from_zero(setup):
    store, _, _ = setup
    ready, _, response = response_for(setup)
    build(setup, ready, response)
    feed, posted = manual_feed(setup, metrics={"views": 123, "likes": 0})
    result = packs.observe_manual_replies(store, reply_feed_path=feed, now=posted + timedelta(hours=24))
    observation = store.get_performance_observation(result["observed"][0]["daily_observation_id"])
    assert json.loads(observation["metrics_native_json"]) == {"views": 123, "likes": 0}
    assert json.loads(observation["metric_availability_json"])["profile_visits"] == "NOT_EXPOSED"
    group = packs.report_manual_replies(store, now=posted + timedelta(hours=24))["cohorts"][0]
    assert group["views"] == 123 and group["likes"] == 0 and group["profile_visits"] is None
    assert group["target_author"] == "FirstSquawk" and group["reply_shape"] == "priced_in_comparison"
    assert group["collected_24h"] == 1
    next_request = packs.prepare(store, feed_path=setup[1], output_root=setup[2], now=posted + timedelta(hours=24))
    feedback = packs.read_json(next_request["request_path"])["audience_feedback"]
    assert feedback["cohorts"][0]["views"] == 123 and feedback["review_due"] is False


def test_early_or_unrelated_reader_rows_never_prove_manual_reply_or_24h_metrics(setup):
    store, _, _ = setup
    ready, _, response = response_for(setup)
    build(setup, ready, response)
    feed, posted = manual_feed(setup, parent="999")
    assert not packs.observe_manual_replies(store, reply_feed_path=feed, now=posted)["observed"]
    feed, _ = manual_feed(setup, handle="Impersonator")
    assert not packs.observe_manual_replies(store, reply_feed_path=feed, now=posted)["observed"]
    feed, _ = manual_feed(setup, metrics={"views": 999}, when=posted + timedelta(hours=1))
    result = packs.observe_manual_replies(store, reply_feed_path=feed, now=posted + timedelta(hours=25))
    observation = store.get_performance_observation(result["observed"][0]["daily_observation_id"])
    assert observation["collection_status"] == "SCHEDULED"
    assert packs.report_manual_replies(store, now=posted + timedelta(hours=25))["cohorts"][0]["views"] is None


def test_observed_post_clock_is_write_once_and_requires_offset(setup):
    from live_contentops.durable_operational_store_v1 import DispatchIdentityConflictError

    store, _, _ = setup
    ready, _, response = response_for(setup)
    build(setup, ready, response)
    feed, posted = manual_feed(setup)
    result = packs.observe_manual_replies(store, reply_feed_path=feed, now=posted)
    row = result["observed"][0]
    args = dict(dispatch_id=row["dispatch_id"], message_id=row["readback_message_id"], platform="x")
    with pytest.raises(DispatchIdentityConflictError, match="dispatched_at"):
        store.register_platform_dispatch(**args, observed_dispatched_at_utc=(posted + timedelta(seconds=1)).isoformat())
    with pytest.raises(ValueError, match="OFFSET_REQUIRED"):
        store.register_platform_dispatch(**args, observed_dispatched_at_utc="2026-11-11T00:35:00")
