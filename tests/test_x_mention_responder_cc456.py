from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import runpy
from urllib.parse import parse_qs, urlsplit

import pytest

from live_contentops import sourced_replies_v1 as replies
from live_contentops import x_mention_responder_v1 as api
from live_contentops import x_reply_pack_v1 as packs
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.event_article_guard_v1 import PUBLIC_NOTICE

NOW = datetime.now(timezone.utc)


class Server:
    def __init__(self):
        self.account = {"id": "999", "username": "Capitalnicle"}
        self.mention = {"id": "123", "author_id": "111", "text": "@Capitalnicle what would disprove that inflation view?",
                        "created_at": (NOW - timedelta(minutes=10)).isoformat(),
                        "entities": {"mentions": [{"id": "999", "username": "Capitalnicle"}]}}
        self.mentions = [self.mention]
        self.users = [{"id": "111", "username": "Reader"}]
        self.posts = {"123": self.mention}
        self.calls = []
        self.writes = []
        self.meta = {"newest_id": "123"}
        self.lost_return = False
        self.readback_visible = True

    def __call__(self, method, url, headers, body):
        parsed = urlsplit(url)
        assert parsed.netloc == "api.x.com"
        assert headers["Authorization"].startswith("OAuth ")
        payload = json.loads(body) if body else None
        self.calls.append((method, parsed.path, parse_qs(parsed.query), payload))
        if parsed.path == "/2/users/me":
            return {"data": deepcopy(self.account)}
        if parsed.path.endswith("/mentions"):
            return {"data": deepcopy(self.mentions), "includes": {"users": deepcopy(self.users)}, "meta": self.meta}
        if method == "POST":
            post = {"id": "456", "author_id": "999", "text": payload["text"], "created_at": NOW.isoformat(),
                    "referenced_tweets": [{"type": "replied_to", "id": payload["reply"]["in_reply_to_tweet_id"]}]}
            self.writes.append(post)
            self.posts["456"] = post
            if self.lost_return:
                raise TimeoutError("Never serialize fixture-secret inside this exception")
            return {"data": {"id": "456", "text": payload["text"]}}
        if parsed.path.endswith("/tweets"):
            return {"data": deepcopy(self.writes) if self.readback_visible else []}
        post_id = parsed.path.rsplit("/", 1)[-1]
        if post_id == "456" and not self.readback_visible:
            return {"data": {"id": "456", "author_id": "111", "text": "something else"}}
        return {"data": deepcopy(self.posts[post_id])}


@pytest.fixture
def setup(tmp_path, monkeypatch):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3", auto_migrate=True)
    control = store.get_operating_control()
    store.update_operating_control(expected_state_version=control["state_version"], operating_mode="AUTONOMOUS_DEFAULT",
                                   control_source="CONTROLLED_TEST")
    key = "existing-public-desk-scan"
    store.create_work_item(story_id=key, title="Existing public records", target_surface="PRIVATE", work_item_id=key)
    source = {"source_id": "BLS", "rights_class": "BLS_OFFICIAL_PUBLIC_DERIVED", "attribution": "BLS"}
    field = {"citation": "export#ECI/wages", "field_path": "/wages", "display": "0.7",
             "value": 0.7, "rights_class": "BLS_OFFICIAL_PUBLIC_DERIVED", "unit": "%", "source_ids": ["BLS"]}
    data = {"desk_record_sources": [{"title": "BLS ECI civilian wages, three-month change",
             "known_at_utc": (NOW - timedelta(days=12)).isoformat(),
             "binding": {"fixture": False, "record_type": "event_card", "fields": [field], "sources": [source]}}]}
    store.register_outbox_message(message_id=key, work_item_id=key, destination="internal:cc-report-feed", payload=json.dumps(data))
    feed = tmp_path / "held-feed.json"
    packs.save_json(feed, {"generated_at_utc": NOW.isoformat(), "rows": []})
    monkeypatch.setattr(packs, "PACK_ROOT", tmp_path / "pack")
    server = Server()
    client = api.XApiClient(store, secret_reader=lambda name: "fixture-secret-" + name, wire=server, now=lambda: NOW)
    return store, feed, tmp_path, server, client


def prepare(setup):
    store, feed, root, server, client = setup
    result = api.poll(store, feed_path=feed, output_root=root / "api", client=client, now=NOW)
    assert result["status"] == "MENTIONS_PREPARED", result
    request = packs.read_json(result["editorial"]["request_path"])
    source = request["sources"][0]
    text = ("BLS civilian wages rose 0.7% over three months. " + source["public_timestamp"]
            + ". A price view needs a wage test. " + PUBLIC_NOTICE + " " + api.OPT_OUT_COPY)
    assert len(text) <= 280
    response = {"request_sha256": request["request_sha256"], "editorial_call": {
        "configured_model": "different-model-label", "configured_effort": "low", "runtime_model": None,
        "runtime_effort": None, "telemetry": "CONFIGURED_NOT_OBSERVED"},
        "items": [{"post_id": "123", "source_id": source["source_id"], "fact_text": "0.7",
                   "draft_text": text, "point": "Test prices against wages", "addition": "A price view needs a wage test",
                   "reply_shape": "priced_in_comparison"}]}
    response_path = root / "native-response.json"
    packs.save_json(response_path, response)
    built = packs.build(store, feed_path=feed, mentions_path=result["mentions_feed_path"],
                        request_path=result["editorial"]["request_path"], response_path=response_path,
                        output_root=root / "pack", now=NOW)
    assert built["item_count"] == 1, built
    rows = api.stage_from_pack(store, request_path=result["editorial"]["request_path"], response_path=response_path,
                               mentions_path=result["mentions_feed_path"], pack_path=built["pack_path"],
                               x_approval_ref="controlled-X-written-approval", now=NOW)
    assert len(rows) == 1
    return result, request, response_path, built, rows[0]


def test_no_keys_reaches_first_api_call_and_keeps_jims_pack(setup):
    store, feed, root, server, _ = setup
    existing = root / "pack" / ("reply-pack-" + NOW.astimezone(packs.LOCAL).strftime("%Y%m%d") + ".json")
    packs.save_json(existing, {"items": [{"draft_text": "Retained Jim draft"}]})
    before = existing.read_bytes()
    client = api.XApiClient(store, secret_reader=lambda name: None, wire=server, now=lambda: NOW)
    result = api.poll(store, feed_path=feed, output_root=root / "api", client=client, now=NOW)
    assert result["status"] == "X_API_KEYS_NOT_SET"
    assert result["first_api_call"] == {"method": "GET", "path": "/2/users/me"}
    assert result["network_calls"] == 0 and server.calls == []
    assert result["cost"]["cost_upper_bound_usd"] == 0
    assert result["manual_fallback"]["route"] == "CC455_JIM_CLICK"
    assert Path(result["run_record"]).is_file() and existing.read_bytes() == before
    assert not store.list_platform_dispatches()


def test_official_mentions_native_pack_and_live_coordinator_use_exact_reply_edge(setup):
    store, _, root, server, client = setup
    _, request, _, built, row = prepare(setup)
    assert "Reply STOP to opt out." in request["instructions"]
    assert Path(built["html_path"]).is_file()
    coordinator = api.bind_coordinator(store, client=client)
    result = replies.publish(store, row["key"], coordinator=coordinator, root=root / "replies", now=NOW)
    assert len(server.writes) == 1, result
    assert server.writes[0]["referenced_tweets"] == [{"type": "replied_to", "id": "123"}]
    assert result["reply"]["readback_url"] == "https://x.com/Capitalnicle/status/456", result
    intent = json.loads(store.list_outbox_messages(destination="x")[0]["payload"])
    assert intent["destination_plan"]["transport_type"] == "X_OFFICIAL_API"
    assert intent["native_payload"]["text"] == row["text"]
    replies.publish(store, row["key"], coordinator=coordinator, root=root / "replies", now=NOW)
    assert len(server.writes) == 1
    costs = api.budget(store, now=NOW)
    assert 0 < costs["estimated_cost_usd"] <= costs["cost_upper_bound_usd"] <= 0.50
    assert costs["invoice_cost_usd"] is None
    assert "fixture-secret" not in json.dumps(api._values(store, api.COSTS) + api._values(store, api.SETTLEMENTS))


def test_wrong_account_stops_before_mentions_or_drafts(setup):
    store, feed, root, server, client = setup
    server.account["username"] = "SomeoneElse"
    result = api.poll(store, feed_path=feed, output_root=root, client=client, now=NOW)
    assert result["status"] == "X_API_WRONG_ACCOUNT_EXPECTED_CAPITALNICLE"
    assert len(server.calls) == 1 and not server.writes


@pytest.mark.parametrize("kind", ["bare_text", "other_account", "retweet", "other_quote", "own_post"])
def test_unsolicited_or_unverified_targets_never_enter_api_drafting(setup, kind):
    store, feed, root, server, client = setup
    if kind == "bare_text":
        server.mention["entities"] = {}
    elif kind == "other_account":
        server.mention["entities"]["mentions"][0]["id"] = "998"
    elif kind == "retweet":
        server.mention["referenced_tweets"] = [{"type": "retweeted", "id": "222"}]
    elif kind == "own_post":
        server.mention["author_id"] = "999"
    else:
        server.mention["entities"] = {}
        server.mention["referenced_tweets"] = [{"type": "quoted", "id": "222"}]
        server.posts["222"] = {"id": "222", "author_id": "998"}
    result = api.poll(store, feed_path=feed, output_root=root, client=client, now=NOW)
    assert result["mention_count"] == 0
    assert not packs.read_json(result["editorial"]["request_path"])["candidates"]
    assert not server.writes


def test_quote_requires_the_quoted_posts_actual_account(setup):
    store, feed, root, server, client = setup
    server.mention["text"] = "What would disprove this call?"
    server.mention["entities"] = {}
    server.mention["referenced_tweets"] = [{"type": "quoted", "id": "222"}]
    server.posts["222"] = {"id": "222", "author_id": "999"}
    result = api.poll(store, feed_path=feed, output_root=root, client=client, now=NOW)
    assert result["mention_count"] == 1
    row = packs.read_json(result["mentions_feed_path"])["rows"][0]
    assert row["api_interaction"]["quoted_post_id"] == "222"


@pytest.mark.parametrize("lost", [False, True])
def test_unknown_write_is_readback_first_and_never_resubmitted(setup, lost):
    store, _, root, server, client = setup
    *_, row = prepare(setup)
    server.lost_return = lost
    server.readback_visible = False
    coordinator = api.bind_coordinator(store, client=client)
    for _ in range(2):
        result = replies.publish(store, row["key"], coordinator=coordinator, root=root / "replies", now=NOW)
    assert len(server.writes) == 1, result
    assert result["reply"]["readback_url"] is None
    assert "fixture-secret" not in json.dumps(result)


def test_lost_return_can_be_reconciled_from_exact_own_reply(setup):
    store, _, root, server, client = setup
    *_, row = prepare(setup)
    server.lost_return = True
    result = replies.publish(store, row["key"], coordinator=api.bind_coordinator(store, client=client), root=root / "replies", now=NOW)
    assert len(server.writes) == 1
    assert result["reply"]["readback_url"] == "https://x.com/Capitalnicle/status/456", result


def test_readback_must_prove_author_parent_and_exact_copy(setup):
    store, _, _, server, client = setup
    *_, row = prepare(setup)
    intent = {"sourced_reply": row["key"], "work_item_id": row["key"], "native_payload": replies.payload(row),
              "plan_hash": replies.digest(row), "x_api_mention": row["x_api_mention"]}
    expected = {"id": "456", "author_id": "999", "text": row["text"], "created_at": NOW.isoformat(),
                "referenced_tweets": [{"type": "replied_to", "id": "123"}]}
    transport = api.XApiMentionTransport(store, client)
    for change in [{"author_id": "998"}, {"referenced_tweets": [{"type": "replied_to", "id": "124"}]}, {"text": "different"}]:
        server.posts["456"] = {**expected, **change}
        result = transport.readback(destination="x", intent=intent, public_object_id="456", public_object_url=None)
        assert result["verified"] is False


def test_target_change_or_manual_answer_prevents_a_new_write(setup):
    store, _, root, server, client = setup
    *_, row = prepare(setup)
    server.mention["text"] += " changed"
    result = replies.publish(store, row["key"], coordinator=api.bind_coordinator(store, client=client), root=root / "replies", now=NOW)
    assert not server.writes and result["reply"]["readback_url"] is None
    server.mention["text"] = row["api_target"]["text"]
    api._save(store, packs.READBACK_DESTINATION, "manual-reply-readback", {"parent_post_id": "123"})
    with pytest.raises(api.ApiError, match="ALREADY_ANSWERED_BY_JIM"):
        api.require_publishable(store, row, NOW)


def test_prior_x_written_approval_is_a_platform_requirement_not_a_model_label(setup):
    store, _, _, _, _ = setup
    *_, row = prepare(setup)
    with pytest.raises(api.ApiError, match="PRIOR_WRITTEN_APPROVAL"):
        api.require_publishable(store, {**row, "x_approval_ref": None}, NOW)
    api.require_publishable(store, row, NOW)  # Different model/effort labels above are recorded and accepted.


def test_daily_cap_counts_unknown_requests_and_stops_before_network(setup):
    store, _, _, server, client = setup
    api._reserve_cost(store, "GET", "/2/tweets/1", 495_000, NOW)
    with pytest.raises(api.ApiError, match="DAILY_050_USD_CAP"):
        client.account()
    assert not server.calls
    assert api.budget(store, now=NOW)["cost_upper_bound_usd"] == 0.495
    assert api.budget(store, now=NOW + timedelta(days=1))["remaining_micro_usd"] == 500_000


def test_empty_mentions_are_charged_per_returned_resource_not_per_poll(setup):
    store, feed, root, server, client = setup
    server.mentions, server.users, server.meta = [], [], {}
    result = api.poll(store, feed_path=feed, output_root=root, client=client, now=NOW)
    assert result["cost"]["cost_upper_bound_usd"] == 0.01  # One user identity; zero mentions.
    assert len(api._values(store, api.SETTLEMENTS)) == 2


def test_opt_out_is_honored_across_future_polls(setup):
    store, feed, root, server, client = setup
    server.mention["text"] = "@Capitalnicle STOP"
    first = api.poll(store, feed_path=feed, output_root=root, client=client, now=NOW)
    assert first["selection_causes"] == {"X_API_AUTHOR_OPTED_OUT": 1}
    server.mention["text"] = "@Capitalnicle what about gold?"
    second = api.poll(store, feed_path=feed, output_root=root, client=client, now=NOW + timedelta(seconds=1))
    assert second["mention_count"] == 0


def test_cursor_keeps_unread_pages_and_only_advances_after_last_page(setup):
    store, feed, root, server, client = setup
    server.meta = {"newest_id": "123", "next_token": "page-two"}
    api.poll(store, feed_path=feed, output_root=root, client=client, now=NOW)
    server.meta = {"newest_id": "120"}
    server.mentions, server.users = [], []
    api.poll(store, feed_path=feed, output_root=root, client=client, now=NOW + timedelta(seconds=1))
    calls = [v for v in server.calls if v[1].endswith("/mentions")]
    assert calls[1][2]["pagination_token"] == ["page-two"]
    assert calls[0][2]["start_time"] == calls[1][2]["start_time"]
    cursor = api._values(store, api.CURSORS)[-1]
    assert cursor["since_id"] == "123" and cursor["pagination_token"] is None


def test_runner_api_poll_uses_installed_cli_without_any_browser(setup, monkeypatch, capsys):
    store, feed, root, server, _ = setup
    client = api.XApiClient(store, secret_reader=lambda name: None, wire=server, now=lambda: NOW)
    monkeypatch.setattr(api, "XApiClient", lambda store: client)
    monkeypatch.setattr("sys.argv", ["run_sourced_replies.py", "api-poll", "--store", str(store.db_path),
                                   "--feed", str(feed), "--output-root", str(root / "api")])
    runpy.run_path(str(Path(__file__).parents[1] / "scripts/run_sourced_replies.py"), run_name="__main__")
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "X_API_KEYS_NOT_SET" and result["network_calls"] == 0


def test_credential_entry_rejects_piped_input_before_prompt_or_write(monkeypatch):
    module = runpy.run_path(str(Path(__file__).parents[1] / "scripts/set_x_api_keys.py"))
    monkeypatch.setattr("sys.argv", ["set_x_api_keys.py"])
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    with pytest.raises(SystemExit) as result:
        module["main"]()
    assert result.value.code == 2
