"""CC-459: real publication preparation uses the shared snapshot, never the parked renderer."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from live_contentops import plan_call_cards_v1 as cards, plan_status_posts_v1 as posts
from live_contentops import tradingview_snapshot_v1 as tv
from test_plan_call_cards_cc399 import NOW, five, main_root, queue, rows, controlled_tradingview  # noqa: F401
from test_plan_status_publication_cc306 import fake_host
from test_tradingview_snapshot_cc314 import tradingview_worker


def sample(key="one", symbol="US500"):
    return {"key": key, "symbol": symbol, "at_utc": datetime.now(timezone.utc).isoformat(),
            "levels": {"valid_until_utc": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()}}


def fresh_snapshot(calls):
    # Keep the real wrapper even when the card tests install their media fixture.
    from importlib import import_module
    capture = import_module(__name__).ORIGINAL_CAPTURE
    def take(*args):
        value = capture(*args, worker=tradingview_worker(calls))
        value["captured_at_utc"] = datetime.now(timezone.utc).isoformat()
        return value
    return take


ORIGINAL_CAPTURE = tv.capture


def test_one_market_capture_serves_different_posts_for_fifteen_minutes(tmp_path, monkeypatch):
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")
    calls = []
    first = tv.plan_snapshot(sample(), tmp_path / "one", snapshot=fresh_snapshot(calls))
    again = tv.plan_snapshot(sample("two"), tmp_path / "two", snapshot=fresh_snapshot(calls),
                             snapshot_allowed=lambda: False)
    assert len(calls) == 1 and first["sha256"] == again["sha256"]
    state = json.loads((tmp_path / "two/tradingview_capture_v1.json").read_bytes())
    assert state["cache_hit"] and state["attempts"] == 0
    third = tv.plan_snapshot(sample("three"), tmp_path / "three", snapshot=fresh_snapshot(calls),
                            now=datetime.now(timezone.utc) + timedelta(seconds=901))
    assert third and len(calls) == 2


def test_budget_deferral_resumes_same_request_without_drawing_or_losing_attempts(tmp_path, monkeypatch):
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")
    row, calls = sample(), []
    with pytest.raises(tv.SnapshotPending):
        tv.plan_snapshot(row, tmp_path / "one", snapshot=fresh_snapshot(calls), snapshot_allowed=lambda: False)
    first = json.loads((tmp_path / "one/tradingview_capture_v1.json").read_bytes())
    assert first["attempts"] == 0 and calls == []
    asset = tv.plan_snapshot(row, tmp_path / "one", snapshot=fresh_snapshot(calls))
    second = json.loads((tmp_path / "one/tradingview_capture_v1.json").read_bytes())
    assert asset and second["attempts"] == 1
    assert first["started_at_utc"] == second["started_at_utc"]


def test_two_failures_retain_first_cause_and_resume_as_text_without_more_captures(tmp_path, monkeypatch):
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")
    calls = []
    def failure(*args):
        calls.append(1)
        raise tv.SnapshotError("first" if len(calls) == 1 else "second")
    row = sample()
    assert tv.plan_snapshot(row, tmp_path / "one", snapshot=failure) is None
    assert tv.plan_snapshot(row, tmp_path / "one", snapshot=failure) is None
    assert len(calls) == 2
    state = json.loads((tmp_path / "one/tradingview_capture_v1.json").read_bytes())
    assert state["status"] == "TEXT_ONLY" and state["cause"] == "first"


def test_five_minute_deadline_counts_a_text_fallback_without_an_unbounded_wait(tmp_path, monkeypatch):
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")
    folder = tmp_path / "one"
    folder.mkdir()
    (folder / "tradingview_capture_v1.json").write_text(json.dumps({
        "key": "one", "market": "US500", "attempts": 0,
        "started_at_utc": (datetime.now(timezone.utc) - timedelta(seconds=301)).isoformat()}))
    assert tv.plan_snapshot(sample(), folder, snapshot=lambda *a: pytest.fail("deadline already elapsed")) is None
    assert json.loads((folder / "tradingview_capture_v1.json").read_bytes())["cause"] == "TRADINGVIEW_CAPTURE_WAIT_EXPIRED"


def test_card_preparation_uses_tradingview_and_credits_every_destination(five, main_root, tmp_path, monkeypatch):
    from live_contentops import plan_call_card_media_v1 as parked
    monkeypatch.setattr(parked, "render", lambda *a: pytest.fail("parked drawn levels renderer"))
    monkeypatch.setattr(cards, "_reference", lambda *a: {"public_object_id": "parent", "public_object_url": "https://example.test/parent"})
    store, folder, _, _ = five
    queue(store, folder, main_root)
    card = next(r for r in rows(store) if r["kind"] == "setup")
    prepared = posts.prepare_post(store, card["key"], root=tmp_path / "posts", host=fake_host)
    context = json.loads((Path(prepared["output_dir"]) / "run_context_v1.json").read_bytes())
    assert context["media"]["assets"][0]["tradingview_snapshot"]["tv_symbol"] == tv.SYMBOLS[card["symbol"]]
    assert context["chart_credit"] and context["status_post_chart_policy"] == "CC459_TRADINGVIEW"
    assert all(tv.CREDIT in d["payload"] for d in prepared["destinations"])
    posts.validate_status_post_plan(store, card["key"], prepared)


def test_setup_with_exhausted_capture_closes_every_copy_with_the_first_cause(five, main_root, tmp_path, monkeypatch):
    monkeypatch.setattr(cards, "_reference", lambda *a: {"public_object_id": "parent", "public_object_url": "https://example.test/parent"})
    store, folder, _, _ = five
    queue(store, folder, main_root)
    queued = rows(store)
    card = next(row for row in queued if row["kind"] == "setup")
    for row in queued:
        if row["key"] != card["key"]:
            store.set_outbox_status(row["key"], posts.SUPERSEDED)
    failures = iter(["TRADINGVIEW_SNAPSHOT_TIMEOUT", "TRADINGVIEW_SNAPSHOT_FILE_MISSING"])

    def failure(*args):
        raise tv.SnapshotError(next(failures))

    result = cards.publish_ready(store, now=NOW, root=tmp_path / "posts", snapshot=failure,
        coordinator_for=lambda *args: pytest.fail("no chart to publish"))
    outcome, = result["posts"]
    assert outcome["key"] == card["key"] and outcome["status"] == cards.SETTLED_POST
    assert outcome["destination_causes"] == dict.fromkeys(cards.destinations_for(card), "TRADINGVIEW_SNAPSHOT_TIMEOUT")
    assert store.get_outbox_message(card["key"])["status"] == cards.SETTLED_POST
    assert store.get_dispatches_for_work_item(card["key"]) == []


def test_threads_keeps_all_levels_windows_and_long_links_within_actual_character_limit(five, main_root):
    store, folder, _, _ = five
    queue(store,folder,main_root)
    card = next(r for r in rows(store) if r["kind"] == "setup")
    card["text"] = card["text"].replace("\n\n"+cards.NOTICES,
        "\nFull analysis: https://capitalchronicle.substack.com/p/"+"source-bound-"*12+"analysis\n\n"+cards.NOTICES)
    package = cards.destination_payloads(card,card_id="fixture",chart_credit=True,complete_levels=True)["threads"]
    assert all(len(part) <= 500 for part in [package["text"],*package["reply_texts"]])
    assert "Model target level:" in package["full_text"] and "Time exit:" in package["full_text"]
    assert "Entry window to" in package["full_text"] and tv.CREDIT in package["text"]
