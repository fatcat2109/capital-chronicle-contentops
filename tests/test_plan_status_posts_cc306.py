"""CC-306: one post per change of plan state for the six markets. Controlled fixtures only.

The fixture follows Main's CC-307 export (plan_status_export_v1, 9d1838a4): two sealed documents
joined by status_content_hash. Gold's plan mirrors section 4.4's example (zone 4,070-4,085).
"""
from __future__ import annotations

import json

import pytest

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.event_article_guard_v1 import CONFLICTS_NOTICE, PUBLIC_NOTICE
from live_contentops.plan_status_posts_v1 import (
    DESTINATION, PlanPostError, _sha, compose, queue_posts, read_transitions,
)

GENERATED = "2026-11-05T12:30:00Z"


def plan(plan_id, asset, direction, low, high, *, cancel=None, invalid=None, deadline="2026-11-06T12:45:00Z"):
    below = direction == "BULLISH"
    conditions = [] if invalid is None else [
        {"field": "close", "operator": "LT" if below else "GT", "threshold": invalid}]
    return {"plan_id": plan_id, "asset_id": asset, "direction": direction, "status": "WAITING",
            "status_label": "Waiting", "zone": {"minimum": low, "maximum": high}, "cancel_level": cancel,
            "invalidation_conditions": conditions, "expires_at_utc": deadline, "entry_deadline_utc": deadline,
            "data_state": "AVAILABLE"}


def event(plan_id, status, at, reason=None):
    return {"transition_id": "transition_" + _sha([plan_id, status])[:32], "plan_id": plan_id, "status": status,
            "status_label": status.title(), "at_utc": at, "evidence_hash": "e" * 64, "reason_code": reason or status}


def write_export(folder, plans, events):
    status = {"schema": "CapitalChroniclePlanStatusV1", "schema_version": "1.0.0", "generated_at_utc": GENERATED,
              "plans": plans}
    status["content_hash"] = _sha(status)
    transitions = {"schema": "CapitalChroniclePlanTransitionsV1", "schema_version": "1.0.0",
                   "generated_at_utc": GENERATED, "status_content_hash": status["content_hash"], "transitions": events}
    transitions["content_hash"] = _sha(transitions)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "plan-status.public.json").write_text(json.dumps(status), encoding="utf-8")
    (folder / "plan-transitions.public.json").write_text(json.dumps(transitions), encoding="utf-8")
    return folder


@pytest.fixture
def export(tmp_path):
    plans = [plan("plan_gold", "XAUUSD", "BULLISH", 4070, 4085, cancel=4150, invalid=4055),
             plan("plan_oil", "USOIL", "BEARISH", 61.2, 61.8, cancel=59.5, invalid=62.4),
             plan("plan_aud", "AUDUSD", "BULLISH", 0.65, 0.651, invalid=0.648),
             plan("plan_jpy", "USDJPY", "BULLISH", 152.1, 152.4)]  # no invalidation level
    events = [event("plan_gold", "WAITING", "2026-11-05T01:45:00Z"),
              event("plan_gold", "TRIGGERED", "2026-11-05T05:20:00Z"),
              event("plan_oil", "WAITING", "2026-11-05T02:00:00Z"),
              event("plan_oil", "CANCELLED", "2026-11-05T09:10:00Z", "RUNAWAY_CANCEL"),
              event("plan_aud", "WAITING", "2026-11-05T02:00:00Z"),
              event("plan_jpy", "WAITING", "2026-11-05T03:00:00Z")]
    return write_export(tmp_path / "plan-status-v1", plans, events)


def by_symbol_state(export):
    return {(r["symbol"], r["to"]): r for r in read_transitions(export)}


def test_setup_post_states_the_conditional_call_with_zone_invalidation_validity_and_notices(export):
    post = compose(by_symbol_state(export)[("XAUUSD", "WAITING")])
    assert post["status"] == "COMPOSED" and post["kind"] == "setup"
    text = post["text"]
    assert text.startswith("Gold: new plan. If price trades into 4,070–4,085, the desk is bullish on gold over "
                           "the period to Fri 6 Nov, 12:45 UTC. Invalidated if price moves below 4,055.")
    assert "If price reaches 4,150 before that, the plan is cancelled." in text
    assert PUBLIC_NOTICE in text and CONFLICTS_NOTICE in text
    assert post["conditional_calls"][0]["direction"] == "bullish"


def test_triggered_and_cancelled_posts_report_the_change_in_plain_words(export):
    rows = by_symbol_state(export)
    triggered = compose(rows[("XAUUSD", "TRIGGERED")])["text"]
    assert triggered.startswith("Gold: the plan with the 4,070–4,085 entry zone is now active. "
                                "Price reached the zone at Thu 5 Nov, 05:20 UTC.")
    assert "invalidated if price moves below 4,055" in triggered
    cancelled = compose(rows[("USOIL", "CANCELLED")])["text"]
    assert cancelled.startswith("US crude oil: the plan with the 61.2–61.8 entry zone is cancelled at "
                                "Thu 5 Nov, 09:10 UTC: price moved away before reaching the zone.")
    assert "ended without an entry" in cancelled


@pytest.mark.parametrize("state,reason,expected", [
    ("EXPIRED", "CONTRACT_EXPIRY", "expired at Thu 5 Nov, 09:10 UTC without price reaching the zone"),
    ("INVALIDATED", "WATCH_INVALIDATED", "is invalidated at Thu 5 Nov, 09:10 UTC: price moved below 4,055"),
    ("VIEW_CHANGED", "THESIS_CHANGED", "our view changed at Thu 5 Nov, 09:10 UTC"),
])
def test_every_other_state_has_one_plain_post(tmp_path, state, reason, expected):
    folder = write_export(tmp_path / "x", [plan("plan_gold", "XAUUSD", "BULLISH", 4070, 4085, invalid=4055)],
                          [event("plan_gold", state, "2026-11-05T09:10:00Z", reason)])
    assert expected in compose(read_transitions(folder)[0])["text"]


def test_no_post_carries_ids_internal_words_targets_or_sizes(export):
    for row in read_transitions(export):
        post = compose(row)
        if post["status"] != "COMPOSED":
            continue
        for word in ("plan_", "transition_", "frozen", "committee", "export", "target", " lot", " R ", "buy now"):
            assert word not in post["text"].lower()


def test_only_the_six_markets_post_and_a_call_without_invalidation_is_not_posted(export):
    rows = by_symbol_state(export)
    assert compose(rows[("AUDUSD", "WAITING")]) == {"status": "NOT_A_FIRST_PHASE_MARKET"}
    assert compose(rows[("USDJPY", "WAITING")]) == {"status": "NOT_POSTED", "cause": "PLAN_INVALIDATION_LEVEL_MISSING"}


def test_each_transition_queues_exactly_once_for_the_publisher(tmp_path, export):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    first = queue_posts(store, export)
    assert len(first["queued"]) == 4  # gold setup and trigger, oil setup and cancel
    assert first["not_posted"] == [{"key": by_symbol_state(export)[("USDJPY", "WAITING")]["key"],
                                    "cause": "PLAN_INVALIDATION_LEVEL_MISSING"}]
    again = queue_posts(store, export)
    assert again["queued"] == [] and sorted(again["already_queued"]) == sorted(first["queued"])
    rows = store.list_outbox_messages(destination=DESTINATION)
    assert len(rows) == 4 and {r["status"] for r in rows} == {"READY_FOR_PUBLISHER"}
    payload = json.loads(next(r["payload"] for r in rows if json.loads(r["payload"])["kind"] == "triggered"))
    assert payload["symbol"] == "XAUUSD" and payload["state"] == "TRIGGERED"


def test_a_tampered_or_mismatched_export_is_named_and_queues_nothing(tmp_path, export):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    path = export / "plan-transitions.public.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    value["transitions"][0]["at_utc"] = "2026-11-05T01:46:00Z"
    path.write_text(json.dumps(value), encoding="utf-8")
    assert queue_posts(store, export) == {"status": "EXPORT_UNREADABLE", "cause": "PLAN_EXPORT_SEAL_INVALID"}
    assert store.list_outbox_messages(destination=DESTINATION) == []


def test_the_stated_jsonl_contract_is_read_too(tmp_path):
    folder = tmp_path / "jsonl"
    folder.mkdir()
    (folder / "status.json").write_text(json.dumps({"plans": [
        {"plan_id": "p1", "symbol": "BTCUSD", "side": "SHORT", "zone_low": 71000, "zone_high": 71500,
         "cancel_level": 68000, "stop": 72500, "expires_at_utc": "2026-11-07T00:00:00Z"}]}), encoding="utf-8")
    (folder / "transitions.jsonl").write_text(json.dumps(
        {"at_utc": "2026-11-05T10:00:00Z", "plan_id": "p1", "symbol": "BTCUSD", "from": None, "to": "WAITING",
         "cause": None}) + "\n", encoding="utf-8")
    text = compose(read_transitions(folder)[0])["text"]
    assert "the desk is bearish on Bitcoin" in text and "price moves above 72,500" in text


def test_no_export_yet_queues_nothing(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    assert queue_posts(store, tmp_path / "absent") == {"status": "OK", "queued": [], "already_queued": [],
                                                       "not_posted": []}
