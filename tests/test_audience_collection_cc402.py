import json
from datetime import datetime, timezone

from live_contentops.audience_collection_v1 import run_collection
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.model_invocation_usage_v1 import import_native_invocations, piece_usage
from live_contentops import destination_performance_observer_v1 as observer
from live_contentops.channel_engagement_v1 import weekly_channel_engagement, weekly_audience_lines

NOW = datetime(2026, 11, 11, 6, tzinfo=timezone.utc)


def seed(tmp_path, routes=("threads", "telegram")):
    store = ContentOpsDurableStore(tmp_path / "audience.sqlite3")
    for index, route in enumerate(routes):
        work = "work-" + route
        store.create_work_item(story_id=work, title="A real call", target_surface=route, work_item_id=work)
        store.register_outbox_message(message_id="card-" + route, work_item_id=work, destination="internal:plan-status-post",
            payload=json.dumps({"plan_id": "plan-one", "short_id": "abcd1234"}))
        store.register_outbox_message(message_id="message-" + route, work_item_id=work, destination=route,
            payload=json.dumps({"plan_status_post": "card-" + route}))
        with store.get_connection() as conn:
            conn.execute("INSERT INTO platform_dispatches VALUES (?,?,?,?,?,?,?,?)", ("dispatch_" + route, "message-" + route, route,
                "DISPATCH_CONFIRMED", "2026-11-10T06:00:00Z", str(100 + index), "https://example.test/" + route, None))
            conn.execute("INSERT INTO readbacks VALUES (?,?,?,?)", ("read-" + route, "dispatch_" + route, '{"verified":true}', "2026-11-10T06:01:00Z"))
        store.register_reconciliation(reconciliation_id="reconciliation_" + route, work_item_id=work, status="RECONCILED_CONFIRMED")
    return store


def test_existing_consumer_collects_every_post_once_with_call_and_true_collection_clock(tmp_path):
    store = seed(tmp_path)
    calls = []
    def collect(**kwargs):
        calls.append(kwargs)
        return {"status": "COLLECTED", "metrics": {"views": 0}, "availability": {"views": "AVAILABLE"}}
    account = lambda _route: {"metrics": {}, "status": "NOT_EXPOSED"}
    result = run_collection(store, now=NOW, limit=5, published_day="2026-11-10", collector=collect, account_collector=account)
    assert result["collected"] == 2
    rows = store.list_performance_observations()
    assert all(json.loads(r["metrics_native_json"])["_call_ids"][0]["call_id"] == "abcd1234" for r in rows)
    assert all(r["collection_status"] == "COLLECTED" and r["collected_at_utc"] > "2026-11-10" for r in rows)
    assert all(json.loads(r["metrics_native_json"])["views"] == 0 for r in rows)
    assert run_collection(store, now=NOW, collector=collect, account_collector=account)["collected"] == 0
    assert len(calls) == 2


def test_unknown_write_never_earns_an_observation(tmp_path):
    store = seed(tmp_path)
    with store.get_connection() as conn:
        conn.execute("UPDATE platform_dispatches SET status='UNKNOWN_WRITE'")
    assert run_collection(store, now=NOW, collector=lambda **_: 1)["scheduled"] == 0


def test_insights_are_collected_without_turning_a_reply_sample_into_total(monkeypatch):
    monkeypatch.setattr(observer, "_meta_token", lambda *_: "controlled")
    calls = []
    def get(url, params):
        calls.append(url)
        if url.endswith("/insights"):
            return {"data": [{"name": "views", "values": [{"value": 23}]}, {"name": "replies", "values": [{"value": 2}]}]}
        return {"data": [{"id": "r", "text": "Question"}]}
    monkeypatch.setattr(observer, "_get_json", get)
    result = observer._threads("123")
    assert result["metrics"] == {"reply_sample_count": 1, "views": 23, "replies": 2}
    assert result["provider_requests"] == len(calls) == 2


def test_invocation_import_uses_retained_cost_and_does_not_price_unknown_usage(tmp_path):
    store = seed(tmp_path)
    for suffix, usage in [("known", {"input_tokens": 250, "output_tokens": 100, "cost_usd": 0.012}), ("unknown", {})]:
        store.register_outbox_message(message_id="return-" + suffix, work_item_id="work-threads", destination="internal:native-desktop-editorial",
            payload=json.dumps({"request_sha256": suffix, "output": {}, "invocation_observation": {"invocation_id": "/root", "model": "observed-model", "usage": usage}}))
    assert import_native_invocations(store)["imported"] == 2
    assert import_native_invocations(store)["imported"] == 0
    piece = piece_usage(store, "work-threads")
    assert piece["invocation_count"] == 2 and piece["cost_usd"] is None
    assert piece["invocations"][0]["cost_usd"] == 0.012
    assert piece["invocations"][1]["prompt_tokens"] is None
    assert store.verify_applied_migrations()
    assert store.verify_schema_integrity()


def test_comment_uses_its_own_counters_without_a_futile_media_insights_call(monkeypatch):
    monkeypatch.setattr(observer, "_meta_token", lambda *_: "controlled")
    calls = []
    monkeypatch.setattr(observer, "_get_json", lambda url, params: calls.append((url, params)) or {"id": "123", "like_count": 0, "comment_count": 2})
    result = observer.collect_current_authorized_destination_metrics(destination="facebook_page", public_object_id="123", object_kind="comment")
    assert result["metrics"] == {"likes": 0, "replies": 2}
    assert result["availability"]["views"] == "NOT_EXPOSED" and len(calls) == 1


def test_weekly_digest_and_call_totals_use_store_observations_without_duplicating_carousel(tmp_path):
    store = seed(tmp_path, ("threads", "telegram"))
    run_collection(store, now=NOW, collector=lambda **_: {"status": "COLLECTED", "metrics": {"views": 2, "replies": 0},
        "availability": {"views": "AVAILABLE", "replies": "AVAILABLE"}}, account_collector=lambda _: {"metrics": {"followers_count": 3}, "status": "COLLECTED"})
    with store.get_read_only_connection() as conn:
        rows = lambda table: [dict(r) for r in conn.execute("SELECT * FROM " + table)]
        result = weekly_channel_engagement(dispatches=rows("platform_dispatches"), reconciliations=rows("reconciliations"),
            readbacks=rows("readbacks"), observations=rows("performance_observations"), week_ending="2026-11-11")
    threads = next(r for r in result["channels"] if r["channel"] == "threads")
    assert threads["posts_in_week"] == 1
    assert threads["net_new_followers_or_members"] is None
    assert threads["account_snapshot"]["metrics"]["followers_count"] == 3
    assert next(r for r in result["calls"] if r["channel"] == "threads")["native_counter_sums"]["views"] == 2
    line = next(line for line in weekly_audience_lines(result) if line.startswith("threads:"))
    assert "posts 1; views 2; replies 0" in line
