import json
import pytest
from datetime import datetime, timezone

from live_contentops.audience_collection_v1 import run_collection
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.model_invocation_usage_v1 import import_native_invocations, piece_usage
from live_contentops import destination_performance_observer_v1 as observer
from live_contentops.channel_engagement_v1 import weekly_channel_engagement, weekly_audience_lines

NOW = datetime(2026, 11, 11, 6, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def fixed_collection_clock(monkeypatch):
    from live_contentops import audience_collection_v1 as audience
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return NOW.astimezone(tz) if tz is not None else NOW.replace(tzinfo=None)
    monkeypatch.setattr(audience, "datetime", Clock)


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


def test_identity_verified_damaged_post_is_observed_without_claiming_content_success(tmp_path):
    store = seed(tmp_path, ("threads",))
    with store.get_connection() as conn:
        conn.execute("UPDATE reconciliations SET status='RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE'")
        conn.execute("UPDATE readbacks SET readback_data=?", (json.dumps({"dispatch_id": "dispatch_threads", "destination": "threads",
            "readback": {"verified": False, "identity_match": True, "observed_public_object_id": "100", "observed_public_object_url": "https://example.test/threads"}}),))
    result = run_collection(store, now=NOW, collector=lambda **_: {"status": "COLLECTED", "metrics": {"views": 2},
        "availability": {"views": "AVAILABLE"}}, account_collector=lambda _: {"metrics": {}, "status": "NOT_EXPOSED"})
    assert result["collected"] == 1
    assert store.list_performance_observations()[0]["learning_eligible"] == 0
    with store.get_read_only_connection() as conn:
        rows = lambda table: [dict(r) for r in conn.execute("SELECT * FROM " + table)]
        report = weekly_channel_engagement(dispatches=rows("platform_dispatches"), reconciliations=rows("reconciliations"),
            readbacks=rows("readbacks"), observations=rows("performance_observations"), week_ending="2026-11-11")
    assert report["content_incomplete_objects_included"] == 1
    assert next(r for r in report["channels"] if r["channel"] == "threads")["native_counter_sums"]["views"] == 2


def test_minute_consumer_still_collects_when_main_export_is_stale(tmp_path, monkeypatch, capsys):
    from scripts import plan_status_posts as consumer
    from live_contentops import audience_collection_v1 as audience
    from live_contentops import model_invocation_usage_v1 as usage
    store = seed(tmp_path)
    monkeypatch.setattr(consumer, "ContentOpsDurableStore", lambda *_args, **_kwargs: store)
    monkeypatch.setattr(consumer, "queue_posts", lambda *_args, **_kwargs: {"status": "EXPORT_STALE"})
    calls = []
    monkeypatch.setattr(audience, "run_collection", lambda *_args, **kwargs: calls.append(kwargs) or {"collected": 0})
    monkeypatch.setattr(usage, "import_native_invocations", lambda _: {"imported": 0})
    assert consumer.main(["--publish", "--store", str(tmp_path / "audience.sqlite3")]) == 1
    assert calls == [{"limit": 4}]
    assert json.loads(capsys.readouterr().out)["audience_collection"]["collected"] == 0


def test_shared_carousel_keeps_both_call_links_but_counts_one_public_object(tmp_path):
    store = seed(tmp_path, ("instagram_business",))
    store.register_outbox_message(message_id="card-two", work_item_id="work-instagram_business", destination="internal:plan-status-post",
        payload=json.dumps({"plan_id": "plan-two", "short_id": "ef012345"}))
    store.register_outbox_message(message_id="message-two", work_item_id="work-instagram_business", destination="instagram_business",
        payload=json.dumps({"plan_status_post": "card-two", "native_payload": {"reuse_run_carousel": True}}))
    with store.get_connection() as conn:
        conn.execute("INSERT INTO platform_dispatches SELECT 'dispatch_two','message-two',platform,status,dispatched_at,public_object_id,public_object_url,public_object_url_hash FROM platform_dispatches LIMIT 1")
        conn.execute("INSERT INTO readbacks VALUES ('read-two','dispatch_two','{\"verified\":true}','2026-11-10T06:01:00Z')")
    store.register_reconciliation(reconciliation_id="reconciliation_two", work_item_id="work-instagram_business", status="RECONCILED_CONFIRMED")
    calls = []
    def collect(**kwargs):
        calls.append(kwargs)
        return {"status": "COLLECTED", "metrics": {"views": 6}, "availability": {"views": "AVAILABLE"}}
    run_collection(store, now=NOW, collector=collect, account_collector=lambda _: {"metrics": {}, "status": "NOT_EXPOSED"})
    assert len(calls) == 1
    with store.get_read_only_connection() as conn:
        rows = lambda table: [dict(r) for r in conn.execute("SELECT * FROM " + table)]
        report = weekly_channel_engagement(dispatches=rows("platform_dispatches"), reconciliations=rows("reconciliations"),
            readbacks=rows("readbacks"), observations=rows("performance_observations"), week_ending="2026-11-11")
    channel = next(r for r in report["channels"] if r["channel"] == "instagram_business")
    assert channel["posts_in_week"] == 1 and channel["native_counter_sums"]["views"] == 6
    assert {r["call_id"] for r in report["calls"]} == {"abcd1234", "ef012345"}
    assert all(r["shared_object_metrics"] for r in report["calls"])


def test_reported_permission_error_keeps_its_safe_native_cause():
    from io import BytesIO
    from urllib.error import HTTPError
    error = HTTPError("https://provider.test/", 400, "Bad Request", {}, BytesIO(b'{"error":{"code":10,"message":"Application does not have permission for this action"}}'))
    result = observer._http_failure("instagram_business", error)
    assert result["status"] == "PERMISSION_REQUIRED"
    assert result["provider_error"]["code"] == 10


def test_telegram_reads_exact_public_counter_and_account_without_page_script():
    from live_contentops.audience_collection_v1 import PublicTelegramMetrics
    class Client:
        def call(self, tool, args):
            assert tool == "run" and "evaluateInPage" not in args["code"]
            return {"ok": True, "value": {"views": "[UNTRUSTED_PAGE_CONTENT]\n3\n[END_UNTRUSTED_PAGE_CONTENT]",
                "members": "[UNTRUSTED_PAGE_CONTENT]\n6 subscribers89 photos33 links\n[END_UNTRUSTED_PAGE_CONTENT]"}}
        value = staticmethod(lambda value: value)
    public = PublicTelegramMetrics(Client())
    public._open = lambda _object: "https://t.me/s/CapitalChronicle?before=151"
    public.page = 1
    result = public("150")
    assert result["metrics"] == {"views": 3}
    assert result["account_metrics"] == {"members_count": 6}


def test_run_post_is_bound_to_its_actual_cards_and_export_uses_that_join(tmp_path):
    from live_contentops.audience_collection_v1 import dispatch_call_ids
    from scripts.export_contentops_weekly_engagement import export_weekly_engagement
    store = seed(tmp_path, ("threads",))
    store.register_outbox_message(message_id="run-card", work_item_id="work-threads", destination="internal:plan-status-post",
        payload=json.dumps({"kind": "run", "plan_id": "plan-run-post-example", "card_keys": ["card-threads"]}))
    with store.get_connection() as conn:
        conn.execute("UPDATE outbox_messages SET payload=? WHERE message_id='message-threads'", (json.dumps({"plan_status_post": "run-card"}),))
    dispatch = store.get_platform_dispatch("dispatch_threads")
    links = dispatch_call_ids(store, dispatch)
    assert links[0]["plan_id"] == "plan-one" and links[0]["call_id"] == "abcd1234"
    assert links[0]["run_record_id"] == "run-card"
    run_collection(store, now=NOW, collector=lambda **_: {"status": "COLLECTED", "metrics": {"views": 2}, "availability": {"views": "AVAILABLE"}},
        account_collector=lambda _: {"metrics": {}, "status": "NOT_EXPOSED"})
    export_weekly_engagement(store.db_path, "2026-11-11", tmp_path / "weekly")
    report = json.loads((tmp_path / "weekly" / "engagement.json").read_bytes())
    assert report["calls"][0]["call_id"] == "abcd1234"


def test_lane_run_counters_bind_one_dated_piece_and_do_not_sum_resumes_or_invent_cost(tmp_path):
    store = seed(tmp_path)
    piece = "cc338-cpi-preview-20261110-v1"
    store.register_outbox_message(message_id="piece-binding", work_item_id="work-threads",
        destination="internal:native-publication-binding", payload=json.dumps({"work_item_id": piece}))
    folder = tmp_path / "runs/publisher-cc338"
    folder.mkdir(parents=True)
    (folder / "launch.json").write_text(json.dumps({"items": ["CC-338"], "started_utc": "2026-11-10T10:00:00Z",
        "model": "configured", "reasoning_effort": "max"}), encoding="utf-8")
    for suffix, total in [("", "1,000"), ("-resume1", "1,500"), ("-resume2", "1,500")]:
        (folder / ("stderr" + suffix + ".txt")).write_text("some output\ntokens used\n" + total + "\n", encoding="utf-8")
    assert import_native_invocations(store, lane_run_root=tmp_path / "runs")["lane_runs_updated"] == 1
    assert import_native_invocations(store, lane_run_root=tmp_path / "runs")["imported"] == 0
    usage = piece_usage(store, piece)
    assert usage["lane_run_usage"][0]["cli_reported_tokens_used"] == 1500
    assert usage["cost_usd"] is None and usage["lane_run_usage"][0]["prompt_tokens"] is None
    # A second possible piece on the same item/date is ambiguous; do not assign it.
    store.register_outbox_message(message_id="ambiguous-binding", work_item_id="work-threads",
        destination="internal:native-publication-binding", payload=json.dumps({"work_item_id": "cc338-other-piece-20261110-v1"}))
    (folder / "stderr-resume3.txt").write_text("tokens used\n2,000\n", encoding="utf-8")
    assert import_native_invocations(store, lane_run_root=tmp_path / "runs")["lane_runs_updated"] == 0
