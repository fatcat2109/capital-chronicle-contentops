from copy import deepcopy
from datetime import timedelta
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from live_contentops import x_reply_pack_v1 as packs
from live_contentops import x_reply_tabs_v1 as tabs
from test_x_reply_pack_cc455 import NOW, post, response_for, setup as pack_setup


@pytest.fixture
def setup(tmp_path):
    return pack_setup.__wrapped__(tmp_path)


class Neo(tabs.NeoReplyTabs):
    def __init__(self):
        self.opened, self.closed, self.filled, self.current = [], [], [], {}
        self.client = SimpleNamespace(act=self.fill)
        self.error = None

    def connect(self):
        if self.error:
            raise ValueError(self.error)

    def capture_inputs(self, store, root):
        paths = [Path(root) / name for name in ("replies.json", "mentions.json")]
        for path in paths:
            packs.save_json(path, {"rows": [], "generated_at_utc": NOW.isoformat()})
        return paths

    def pages(self):
        return [{"pageId": page, "groupId": value["group"], "url": value["url"]}
                for page, value in self.current.items()]

    def inspect(self, page):
        return deepcopy(self.current[page])

    def open_draft(self, item, group):
        page = max(self.current, default=0) + 1
        group = group or "reply-group"
        self.current[page] = {"group": group, "url": item["intent_url"], "editors": [item["draft_text"]],
            "rows": [{"tweet_id": item["post_id"], "handle": item["author_handle"]}],
            "textboxes": [{"ref": "e1", "name": "Post text"}]}
        self.opened.append(page)
        return page, group

    def close(self, page):
        self.closed.append(page)
        del self.current[page]

    def fill(self, page, kind, **values):
        assert kind == "fill"
        self.filled.append(page)
        self.current[page]["editors"] = [values["value"]]


def drafter_for():
    def draft(request_path, *, output_dir):
        request = packs.read_json(request_path)
        source = request["sources"][0]
        items = [{"post_id": p["post_id"], "source_id": source["source_id"], "fact_text": "0.7",
                  "draft_text": "BLS wages rose 0.7%. " + source["public_timestamp"] + ". " + packs.PUBLIC_NOTICE,
                  "point": "wage cross-check", "addition": "BLS wages rose 0.7%", "reply_shape": "cross_check"}
                 for p in request["candidates"][:5]]
        path = Path(output_dir) / "response.json"
        packs.save_json(path, {"request_sha256": request["request_sha256"], "items": items, "omissions": [],
                               "editorial_call": {"model": tabs.MODEL, "configuration_status": "CONFIGURED_NOT_OBSERVED"}})
        return path
    return draft


def run(setup, *, neo=None, now=NOW, force=True, drafter=None):
    store, feed, root = setup
    return tabs.refresh_due(store, feed_path=feed, output_root=root, control_path=root / "control.json",
                            driver=neo or Neo(), drafter=drafter or drafter_for(), now=now, force=force)


def test_live_pack_consumer_reaches_waiting_neo_text_without_public_dispatch(setup):
    store, _, root = setup
    neo = Neo()
    result = run(setup, neo=neo)
    assert result["status"] == "READY_FOR_JIM"
    assert result["public_submit_actions"] == 0 and not result["public_write_performed"]
    saved = packs.read_json(result["pack"]["pack_path"])
    assert saved["items"][0]["draft_text"] == neo.current[1]["editors"][0]
    assert tabs.latest_state(store)["tabs"][0]["page_id"] == 1
    assert store.get_outbox_message(result["store_message_id"])["destination"] == tabs.RUN_DESTINATION
    assert not store.list_outbox_messages(destination="x") and not store.list_platform_dispatches()
    cadence = tabs.enable_cadence(store, control_path=root / "control.json")
    assert cadence["interval_seconds"] == 7200 and cadence["schedule_changed"] is False
    assert run(setup, neo=neo, force=False, now=NOW + timedelta(minutes=119))["status"] == "NOT_DUE"
    assert len(neo.opened) == 1


def test_120_minute_boundary_and_six_hour_consumer(setup):
    selected, causes = packs.select_posts({"rows": [post(age=120), post("124", age=121)]},
                                           handles={"firstsquawk"}, now=NOW)
    assert len(selected) == 1 and causes["POST_OUTSIDE_120_MINUTE_BUILD_WINDOW"] == 1
    result = run(setup)
    item = packs.read_json(result["pack"]["pack_path"])["items"][0]
    assert packs.clock(item["stale_at_utc"]) == packs.clock(item["post_time_utc"]) + timedelta(hours=6)
    assert not packs.read_pack(result["pack"]["pack_path"], now=NOW + timedelta(hours=4))["items"][0]["stale"]
    assert packs.read_pack(result["pack"]["pack_path"], now=NOW + timedelta(hours=6))["items"][0]["stale"]


def item(number, *, age=10):
    return {"post_id": str(number), "post_url": f"https://x.com/FirstSquawk/status/{number}",
            "author_handle": "FirstSquawk", "draft_text": "Draft " + str(number),
            "intent_url": f"https://x.com/intent/post?in_reply_to={number}&text=Draft+{number}",
            "post_time_utc": (NOW - timedelta(minutes=age)).isoformat(),
            "stale_at_utc": (NOW - timedelta(minutes=age) + timedelta(hours=6)).isoformat()}


def seed_tab(state, neo, row):
    page, group = neo.open_draft(row, state["group_id"])
    state["group_id"] = group
    state["tabs"].append({**row, "page_id": page, "waiting_url": row["intent_url"]})
    return page


def test_next_refresh_closes_only_sent_or_expired_unedited_tabs_and_keeps_edits(setup):
    store, _, _ = setup
    neo, state = Neo(), tabs.latest_state(store)
    first = seed_tab(state, neo, item(1))
    old = seed_tab(state, neo, item(2, age=361))
    edited = seed_tab(state, neo, item(3, age=361))
    neo.current[edited]["editors"] = ["Jim is editing this"]
    other = seed_tab(state, neo, item(4))
    neo.current[other]["group"] = "someone-elses-group"
    tabs._record(store, packs.READBACK_DESTINATION, {"parent_post_id": "1"})
    actions = tabs.sync_tabs(store, state, {"items": [item(n) for n in range(1, 10)]}, neo, now=NOW)
    assert set(neo.closed) == {first, old}
    assert neo.current[edited]["editors"] == ["Jim is editing this"]
    assert other in neo.current
    assert sum(p["groupId"] == state["group_id"] for p in neo.pages()) == 5
    assert any(a["action"] == "SENT_CLOSED" for a in actions)
    assert any(a["action"] == "EXPIRED_CLOSED" for a in actions)
    assert len(state["tabs"]) == 6  # Five waiting in our group and Jim's preserved moved tab.


def test_empty_waiting_box_is_refilled_but_changed_text_is_never_overwritten(setup):
    store, _, _ = setup
    neo, state = Neo(), tabs.latest_state(store)
    page = seed_tab(state, neo, item(1))
    neo.current[page]["editors"] = [""]
    tabs.sync_tabs(store, state, {"items": []}, neo, now=NOW)
    assert neo.filled == [page] and neo.current[page]["editors"] == ["Draft 1"]
    neo.current[page]["editors"] = ["Jim's words"]
    tabs.sync_tabs(store, state, {"items": []}, neo, now=NOW + timedelta(hours=7))
    assert neo.filled == [page] and not neo.closed
    assert state["tabs"][0]["status"] == "JIM_EDIT_PRESERVED"


def test_last_expired_tab_releases_group_before_opening_replacement(setup):
    store, _, _ = setup
    neo, state = Neo(), tabs.latest_state(store)
    first = seed_tab(state, neo, item(1, age=361))
    tabs.sync_tabs(store, state, {"items": [item(2)]}, neo, now=NOW)
    assert first in neo.closed and state["tabs"][0]["post_id"] == "2"


def test_sent_composer_that_closed_after_jims_click_is_removed(setup):
    store, _, _ = setup
    neo, state = Neo(), tabs.latest_state(store)
    page = seed_tab(state, neo, item(1))
    neo.current[page]["url"] = item(1)["post_url"]
    neo.current[page]["editors"] = []
    tabs._record(store, packs.READBACK_DESTINATION, {"parent_post_id": "1"})
    tabs.sync_tabs(store, state, {"items": []}, neo, now=NOW)
    assert neo.closed == [page] and not state["tabs"]


def test_failed_drafter_leaves_group_unchanged_and_waits_two_hours(setup):
    store, _, root = setup
    neo = Neo()
    assert run(setup, neo=neo)["status"] == "READY_FOR_JIM"
    tabs.enable_cadence(store, control_path=root / "control.json")
    before = deepcopy(neo.current)
    def fail(*a, **kw):
        raise ValueError("AGY_TIMEOUT_120S")
    result = run(setup, neo=neo, drafter=fail, now=NOW + timedelta(hours=2))
    assert result["status"] == "REFRESH_FAILED" and result["stage"] == "AGY_DRAFT"
    assert result["cause"] == "ValueError: AGY_TIMEOUT_120S"
    assert neo.current == before and not neo.closed
    assert run(setup, neo=neo, force=False, now=NOW + timedelta(hours=3))["status"] == "NOT_DUE"


def test_signed_out_has_one_cause_without_drafting_or_touching_waiting_tabs(setup):
    neo = Neo()
    neo.error = "X_SIGNED_OUT"
    def never(*a, **kw):
        raise AssertionError("drafter must not run")
    result = run(setup, neo=neo, drafter=never)
    assert result["stage"] == "NEO_CONNECT" and result["cause"] == "ValueError: X_SIGNED_OUT"
    assert not neo.opened and not neo.closed


def test_transport_waits_for_x_identity_instead_of_rejecting_first_loading_frame():
    calls = []
    client = SimpleNamespace(wait=lambda page, selector: calls.append("identity_wait"),
        call=lambda name, args: calls.append(name) or {"ok": True, "value": {"authenticated": True}},
        value=lambda r: r)
    assert tabs.NeoReplyTabs(client).inspect(7)["authenticated"]
    assert calls == ["identity_wait", "run"]


def test_cadence_stays_disabled_until_real_refresh_is_saved(setup):
    store, _, root = setup
    assert run(setup, force=False)["status"] == "DISABLED"
    with pytest.raises(ValueError, match="DECISION_123"):
        tabs.enable_cadence(store, control_path=root / "control.json")


def test_agy_uses_bounded_existing_cli_and_records_config_without_trusting_self_report(setup):
    store, feed, root = setup
    ready = packs.prepare(store, feed_path=feed, output_root=root, now=NOW)
    seen = []
    def runner(args, **kwargs):
        seen.append(args)
        assert kwargs["timeout"] == tabs.DRAFT_TIMEOUT_SECONDS and kwargs["input"] is None
        assert args[-2] == "--print" and "request_sha256" in args[-1]
        response = {"request_sha256": ready["request_sha256"], "items": [],
                    "editorial_call": {"runtime_model": "invented"}}
        raw = json.dumps({"status": "SUCCESS", "response": json.dumps(response)}).encode()
        return subprocess.CompletedProcess(args, 0, raw, b"")
    path = tabs.draft_with_agy(ready["request_path"], output_dir=root / "agy", runner=runner)
    record = packs.read_json(root / "agy/call.json")
    assert len(seen) == 1 and seen[0][0] == tabs.AGY
    assert seen[0][seen[0].index("--model") + 1] == "gemini-3.8-flash-high"
    assert record["configuration_status"] == "CONFIGURED_NOT_OBSERVED"
    assert packs.read_json(path)["editorial_call"]["runtime_model"] is None


def test_actual_minute_entry_refreshes_tabs_when_main_export_is_stale(setup, monkeypatch, capsys):
    from scripts import plan_status_posts as entry
    from live_contentops import plan_status_posts_v1 as posts
    from live_contentops import event_timestamp_v1, event_pack_v1
    store, _, root = setup
    calls = []
    monkeypatch.setattr(entry, "ContentOpsDurableStore", lambda *a, **kw: store)
    monkeypatch.setattr(entry, "queue_posts", lambda *a, **kw: {"status": "EXPORT_STALE"})
    monkeypatch.setattr(tabs, "refresh_due", lambda s: calls.append(s) or {"status": "READY_FOR_JIM"})
    monkeypatch.setattr(event_timestamp_v1, "maintain_timestamps", lambda: {})
    monkeypatch.setattr(event_pack_v1, "run_due_packs", lambda *a, **kw: {})
    monkeypatch.setattr(posts, "record_run", lambda *a: root / "run.json")
    assert entry.main(["--publish", "--store", str(root / "store.sqlite3")]) == 1
    assert json.loads(capsys.readouterr().out)["reply_tabs"]["status"] == "READY_FOR_JIM"
    assert calls == [store]


def test_manual_readback_measures_post_to_reply_minutes_and_24h_slow_reply_views(setup):
    store, feed, root = setup
    ready, response, path = response_for(setup)
    packs.build(store, request_path=ready["request_path"], response_path=path, feed_path=feed, output_root=root, now=NOW)
    posted = NOW + timedelta(hours=3)
    capture = posted + timedelta(hours=24)
    row = {"handle": "Capitalnicle", "tweet_id": "456", "url": "https://x.com/Capitalnicle/status/456",
           "text": "Jim's edited reply", "posted_utc": posted.isoformat(), "in_reply_to_status_id": "123",
           "metrics": {"views": 17, "likes": 0}, "metrics_observed_at_utc": capture.isoformat()}
    packs.save_json(feed, {"rows": [row]})
    result = packs.observe_manual_replies(store, reply_feed_path=feed, now=capture)
    value = json.loads(store.get_outbox_message(result["observed"][0]["readback_message_id"])["payload"])
    assert value["post_to_reply_minutes"] == 190
    latency = packs.report_manual_replies(store, now=capture)["post_to_reply_latency"]
    assert latency["2_to_6h"] == {"reply_count": 1, "collected_24h": 1, "views": 17}
