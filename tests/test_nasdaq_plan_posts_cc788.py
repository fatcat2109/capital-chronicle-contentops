"""CC-788: a Nasdaq 100 plan goes from setup through fill to its result on every destination by the same rules
as an S&P 500 plan with the same levels. Controlled export, copied store, no browser or provider request."""
from __future__ import annotations

from datetime import datetime, timezone
import difflib
import json
import sqlite3
import sys

import pytest

from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_status_posts_v1 as posts
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.event_article_guard_v1 import CONFLICTS_NOTICE, PUBLIC_NOTICE
from live_contentops.public_decision_checks_v1 import plan_target_present
from test_plan_call_cards_cc399 import controlled_tradingview  # noqa: F401  (autouse: no browser)
from test_plan_status_posts_cc306 import event, main_root, plan  # noqa: F401  (main_root is a fixture)

NOW = datetime(2026, 11, 30, 15, 0, tzinfo=timezone.utc)
NAMES = {"USTEC": "Nasdaq 100", "US500": "S&P 500"}


def call(asset):
    pid = "plan_" + asset.lower() + "_cc788"
    value = plan(pid, asset, "BULLISH", 25120.5, 25180.25, invalid=24990.75, deadline="2026-11-30T20:00:00Z")
    value.update(registered_at_utc="2026-11-30T14:45:00Z", target=25600.5, tick_size=.01,
                 public_call_id="call_" + pid,
                 reader_reasons=["Falling yields support growth shares.", "The entry waits for a pullback."],
                 scenario_analysis={"horizon_end_utc": "2026-12-01T21:00:00Z",
                                    "base_case": {"probability_pct": 55},
                                    "main_alternative": {"probability_pct": 45}})
    return value


def write(folder, plans, events):
    folder.mkdir(parents=True, exist_ok=True)
    status = {"schema": "CapitalChroniclePlanStatusV1", "schema_version": "1.0.0",
              "generated_at_utc": NOW.isoformat(), "plans": plans, "content_hash": "a" * 64,
              "scored_call_count": 12,
              "record_summary": {"judged_count": 12, "right_count": 7, "trend_rule_right_count": 5}}
    (folder / "plan-status.public.json").write_text(json.dumps(status), encoding="utf-8")
    (folder / "plan-transitions.public.json").write_text(json.dumps({
        "schema": "CapitalChroniclePlanTransitionsV1", "schema_version": "1.0.0",
        "generated_at_utc": status["generated_at_utc"], "status_content_hash": "a" * 64,
        "transitions": events}), encoding="utf-8")
    return folder


@pytest.fixture
def pair(tmp_path, main_root, monkeypatch):
    from live_contentops import secret_store_v1
    monkeypatch.setattr(secret_store_v1, "read_secret",
                        lambda name: "fixture-bot" if name == "DISCORD_BOT_TOKEN" else None)

    class FixtureClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return NOW.astimezone(tz) if tz else NOW.replace(tzinfo=None)
    monkeypatch.setattr(cards, "datetime", FixtureClock)
    seed = ContentOpsDurableStore(tmp_path / "seed.sqlite")
    copied = tmp_path / "copy.sqlite"
    with sqlite3.connect(seed.db_path) as source, sqlite3.connect(copied) as target:
        source.backup(target)
    store = ContentOpsDurableStore(copied)
    plans = [call("USTEC"), call("US500")]
    events = [event(p["plan_id"], "WAITING", p["registered_at_utc"]) for p in plans]
    folder = write(tmp_path / "export", plans, events)

    def current_public_plan(pid, **options):
        view = json.loads((folder / "plan-status.public.json").read_bytes())
        return next(p for p in view["plans"] if p["plan_id"] == pid)
    monkeypatch.setattr(posts, "current_public_plan", current_public_plan)
    return store, folder, plans, events


def queue(store, folder, main_root):
    return posts.queue_posts(store, folder, now=NOW, main_root=main_root, python=sys.executable)


def rows(store):
    return [json.loads(r["payload"]) for r in store.list_outbox_messages(destination=posts.DESTINATION)]


def as_sp(text, row):
    """The Nasdaq copy with the S&P 500 plan's own name and identifiers, for a like-for-like comparison."""
    return (text.replace("Nasdaq 100", "S&P 500").replace("NASDAQ:NDX", "SP:SPX")
            .replace("ustec", "us500").replace("USTEC", "US500"))


def same(nasdaq, spx, label):
    if "x" in (label if isinstance(label, tuple) else (label,)):
        # X threads split at 280 characters, so a longer market name can move a line to the next post:
        # the same lines, in the same order, in any split between posts.
        def lines(payload, rename=lambda line: line):
            posts_text = [p["text"] for p in payload.get("posts") or []] or [payload["text"]]
            return [rename(line) for text in posts_text for line in text.splitlines() if line]
        assert lines(nasdaq, lambda line: as_sp(line, None)) == lines(spx), label
        return
    mine = as_sp(json.dumps(nasdaq, sort_keys=True, ensure_ascii=False, indent=1), None).splitlines()
    other = json.dumps(spx, sort_keys=True, ensure_ascii=False, indent=1).splitlines()
    differ = [line for line in difflib.ndiff(mine, other) if line[:1] in "+-"]
    assert not differ, (label, differ[:6])


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def public_checks(text):
    if not isinstance(text, str):
        for field in strings(text):
            public_checks(field)
        return
    assert "USTEC" not in text and "CFD" not in text
    assert not plan_target_present(text)  # decisions 40 and 157: no target level, ever
    assert text.count(PUBLIC_NOTICE) <= 1 and text.count(CONFLICTS_NOTICE) <= 1
    assert "25120.5" not in text and "24990.75" not in text  # grouped numbers only


def by_symbol(items, kind):
    return {r["symbol"]: r for r in items if r["kind"] == kind}


def test_setup_fill_and_result_match_the_sp_500_copy_on_every_destination(pair, main_root):
    store, folder, plans, events = pair
    assert queue(store, folder, main_root)["status"] == "OK"
    setups = by_symbol(rows(store), "setup")
    assert set(setups) == {"USTEC", "US500"}
    nasdaq, spx = setups["USTEC"], setups["US500"]
    assert "\nNasdaq 100: waiting for price to trade into 25,120.5–25,180.25." in nasdaq["text"]
    assert nasdaq["text"].startswith("Scenarios: Base case (55%).")  # the scenario voice (decision 158)
    assert "25,120.5" in nasdaq["text"] or "25,120.50" in nasdaq["text"]
    assert as_sp(nasdaq["text"], nasdaq) == spx["text"]
    public_checks(nasdaq["text"])
    assert set(cards.destinations_for(nasdaq)) == set(cards.destinations_for(spx))
    for destination, payload in cards.destination_payloads(nasdaq, card_id="card").items():
        other = cards.destination_payloads(spx, card_id="card")[destination]
        same(payload, other, destination)
        public_checks(payload)

    for item in setups.values():
        store.set_outbox_status(item["key"], "PUBLISHED")
    for raw in plans:
        pid = raw["plan_id"]
        raw["status"] = "FILLED"
        raw["outcome"] = {"state": "SCORED", "result": "HIT", "outcome_id": "outcome-" + pid,
                          "score": {"plan_id": pid, "asset_id": raw["asset_id"], "outcome_id": "outcome-" + pid,
                                    "result": "HIT", "resolved_at_utc": "2026-11-30T14:58:00Z",
                                    "direction_correct": True}}
        events.append(event(pid, "FILLED", "2026-11-30T14:50:00Z"))
    write(folder, plans, events)
    queue(store, folder, main_root)
    later = rows(store)
    for kind in ("update", "result"):
        items = by_symbol(later, kind)
        assert set(items) == {"USTEC", "US500"}, kind
        nasdaq, spx = items["USTEC"], items["US500"]
        assert as_sp(nasdaq["text"], nasdaq) == spx["text"], kind
        public_checks(nasdaq["text"])
        for destination, payload in cards.destination_payloads(nasdaq, card_id="card").items():
            other = cards.destination_payloads(spx, card_id="card")[destination]
            same(payload, other, (kind, destination))
            public_checks(payload)
    result = by_symbol(later, "result")["USTEC"]["text"]
    assert "30 Nov" in result  # a dated result (CC-768)


def test_the_result_rows_and_feed_result_post_name_the_nasdaq_100(pair):
    _, folder, plans, events = pair
    ndx = plans[0]
    ndx["status"] = "FILLED"
    ndx["outcome"] = {"state": "SCORED", "result": "STOPPED", "outcome_id": "o1",
                      "score": {"plan_id": ndx["plan_id"], "asset_id": "USTEC", "outcome_id": "o1",
                                "result": "STOPPED", "resolved_at_utc": "2026-11-30T14:58:00Z"}}
    export = {"status": json.loads(json.dumps({"plans": [ndx], "scored_call_count": 12, "content_hash": "a" * 64})),
              "transitions": {"transitions": events}}
    row, = posts.result_rows_from_export(export)
    assert row["symbol"] == "USTEC"
    text = posts.compose_result(row)["text"]
    assert text.startswith("Nasdaq 100: plan result — stopped at ")
    assert "Entry zone: 25,120.5–25,180.25." in text or "Entry zone: 25,120.50–25,180.25." in text
    public_checks(text)
