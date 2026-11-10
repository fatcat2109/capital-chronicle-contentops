"""CC-306: one post per change of plan state for the six markets. Controlled fixtures only.

The export follows Main's CC-307 contract (plan_status_export_v1): plan-status.public.json and
plan-transitions.public.json, joined by status_content_hash and read through Main's own
read_public_status / read_public_transitions in a separate process. Here a stub Main root stands
in for that reader; the live one is exercised by the dry run against the live folder.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import re
import sys
import textwrap

import pytest

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.event_article_guard_v1 import CONFLICTS_NOTICE, PUBLIC_NOTICE
from live_contentops.plan_status_posts_v1 import DESTINATION, compose, queue_posts, read_transitions


@pytest.fixture(autouse=True)
def ended_posts_on(monkeypatch):
    """Decision 106 turns ended-without-entry posts off; these tests cover their machinery."""
    from live_contentops import plan_status_posts_v1
    monkeypatch.setattr(plan_status_posts_v1, "POST_ENDED_WITHOUT_ENTRY", True)

NOW = datetime(2026, 11, 5, 12, 30, tzinfo=timezone.utc)
STUB_READER = textwrap.dedent('''
    import json
    from pathlib import Path

    class PlanStatusError(ValueError):
        pass

    def read_public_status(path, *, as_of):
        value = json.loads(Path(path).read_bytes())
        if value.get("tampered"):
            raise PlanStatusError("PUBLIC_PLAN_STATUS_SCHEMA_INVALID")
        return value

    def read_public_transitions(path, *, status):
        value = json.loads(Path(path).read_bytes())
        if value["status_content_hash"] != status["content_hash"]:
            raise PlanStatusError("PUBLIC_PLAN_SNAPSHOT_MISMATCH")
        return value
''')


@pytest.fixture
def main_root(tmp_path):
    root = tmp_path / "main"
    (root / "tools" / "product").mkdir(parents=True)
    (root / "tools" / "product" / "plan_status_export_v1.py").write_text(STUB_READER, encoding="utf-8")
    return root


def plan(plan_id, asset, direction, low, high, *, cancel=None, invalid=None, deadline="2026-11-06T12:45:00Z"):
    below = direction == "BULLISH"
    conditions = [] if invalid is None else [
        {"field": "close", "operator": "LT" if below else "GT", "threshold": invalid}]
    return {"plan_id": plan_id, "asset_id": asset, "direction": direction, "status": "WAITING",
            "zone": {"minimum": low, "maximum": high}, "cancel_level": cancel,
            "invalidation_conditions": conditions, "expires_at_utc": deadline, "entry_deadline_utc": deadline}


def event(plan_id, status, at, reason=None):
    return {"plan_id": plan_id, "status": status, "at_utc": at, "reason_code": reason or status}


def write_export(folder, plans, events, *, tampered=False):
    folder.mkdir(parents=True, exist_ok=True)
    status = {"schema": "CapitalChroniclePlanStatusV1", "schema_version": "1.0.0",
              "generated_at_utc": "2026-11-05T12:29:50Z", "plans": plans, "content_hash": "s" * 64,
              **({"tampered": True} if tampered else {})}
    transitions = {"schema": "CapitalChroniclePlanTransitionsV1", "schema_version": "1.0.0",
                   "generated_at_utc": status["generated_at_utc"], "status_content_hash": "s" * 64,
                   "transitions": events}
    (folder / "plan-status.public.json").write_text(json.dumps(status), encoding="utf-8")
    (folder / "plan-transitions.public.json").write_text(json.dumps(transitions), encoding="utf-8")
    return folder


@pytest.fixture
def export(tmp_path):
    plans = [plan("plan_gold", "XAUUSD", "BULLISH", 4070, 4085, cancel=4150, invalid=4055),
             plan("plan_oil", "USOIL", "BEARISH", 61.2, 61.8, cancel=59.5, invalid=62.4),
             plan("plan_aud", "AUDUSD", "BULLISH", 0.65, 0.651, invalid=0.648),
             plan("plan_jpy", "USDJPY", "BULLISH", 152.1, 152.4),  # no invalidation level
             plan("plan_old", "EURUSD", "BULLISH", 1.1214, 1.1227, invalid=1.12)]
    events = [event("plan_gold", "WAITING", "2026-11-05T11:45:00Z"),
              event("plan_gold", "TRIGGERED", "2026-11-05T12:20:00Z"),
              event("plan_oil", "WAITING", "2026-11-05T12:00:00Z"),
              event("plan_oil", "CANCELLED", "2026-11-05T12:10:00Z", "RUNAWAY_CANCEL"),
              event("plan_aud", "WAITING", "2026-11-05T12:00:00Z"),
              event("plan_jpy", "WAITING", "2026-11-05T12:05:00Z"),
              event("plan_old", "WAITING", "2026-10-27T23:11:17Z")]  # history: never posted
    return write_export(tmp_path / "plan-status-v1", plans, events)


def rows_by(export, main_root):
    return {(r["symbol"], r["to"]): r for r in read_transitions(export, main_root=main_root, python=sys.executable)}


def queue(store, export, main_root, **kw):
    return queue_posts(store, export, now=NOW, main_root=main_root, python=sys.executable, **kw)


def test_setup_post_states_the_conditional_call_with_zone_invalidation_validity_and_notices(export, main_root):
    post = compose(rows_by(export, main_root)[("XAUUSD", "WAITING")])
    assert post["status"] == "COMPOSED" and post["kind"] == "setup"
    assert post["text"].startswith(
        "Gold: new plan. If price trades into 4,070–4,085, the desk is bullish on gold over the period to "
        "Fri 6 Nov, 07:45 ET. Invalidated if price moves below 4,055.")
    # CC-307's rows carry no target, so the cancel number never prints (decision 40).
    assert "If price runs away before any pullback, the plan is cancelled and we re-assess." in post["text"]
    assert "4,150" not in post["text"]
    assert PUBLIC_NOTICE in post["text"] and CONFLICTS_NOTICE in post["text"]


def test_triggered_and_cancelled_posts_report_the_change_in_plain_words(export, main_root):
    rows = rows_by(export, main_root)
    assert compose(rows[("XAUUSD", "TRIGGERED")])["text"].startswith(
        "Gold: the 4,070–4,085 entry zone filled at Thu 5 Nov, 07:20 ET, and Capital Chronicle's position is"
        " open. It is invalidated if price moves below 4,055.")
    cancelled = compose(rows[("USOIL", "CANCELLED")])["text"]
    assert cancelled.startswith("US crude oil: the plan with the 61.2–61.8 entry zone is cancelled at "
                                "Thu 5 Nov, 07:10 ET: price moved away before reaching the zone.")


@pytest.mark.parametrize("state,reason,expected", [
    ("EXPIRED", "CONTRACT_EXPIRY", "expired at Thu 5 Nov, 07:10 ET without price reaching the zone"),
    ("INVALIDATED", "WATCH_INVALIDATED", "is invalidated at Thu 5 Nov, 07:10 ET: price moved below 4,055"),
    ("VIEW_CHANGED", "THESIS_CHANGED", "our view changed at Thu 5 Nov, 07:10 ET"),
])
def test_every_other_state_has_one_plain_post(tmp_path, main_root, state, reason, expected):
    folder = write_export(tmp_path / "x", [plan("plan_gold", "XAUUSD", "BULLISH", 4070, 4085, invalid=4055)],
                          [event("plan_gold", state, "2026-11-05T12:10:00Z", reason)])
    row = read_transitions(folder, main_root=main_root, python=sys.executable)[0]
    assert expected in compose(row)["text"]


def test_no_post_carries_ids_internal_words_targets_or_sizes(export, main_root):
    for row in rows_by(export, main_root).values():
        post = compose(row)
        if post["status"] == "COMPOSED":
            for word in ("plan_", "frozen", "committee", "export", "target", " lot", " r ", "buy now"):
                assert word not in post["text"].lower()


def test_only_the_six_markets_post_and_a_call_without_invalidation_is_not_posted(export, main_root):
    rows = rows_by(export, main_root)
    assert compose(rows[("AUDUSD", "WAITING")]) == {"status": "NOT_A_FIRST_PHASE_MARKET"}
    assert compose(rows[("USDJPY", "WAITING")]) == {"status": "NOT_POSTED", "cause": "PLAN_INVALIDATION_LEVEL_MISSING"}


def test_each_recent_transition_queues_exactly_once_and_history_never_posts(tmp_path, export, main_root):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    first = queue(store, export, main_root)
    assert [(q["symbol"], q["state"]) for q in first["queued"]] == [
        ("XAUUSD", "WAITING"), ("USOIL", "WAITING"), ("XAUUSD", "TRIGGERED")]
    assert first["older_than_window"] == 1  # 27 Oct EURUSD
    assert {s["cause"] for s in first["not_posted"]} == {"PLAN_INVALIDATION_LEVEL_MISSING", "PLAN_NEVER_ANNOUNCED"}
    again = queue(store, export, main_root)
    assert again["queued"] == [] and len(again["already_queued"]) == 3
    rows = store.list_outbox_messages(destination=DESTINATION)
    assert len(rows) == 3 and {r["status"] for r in rows} == {"READY_FOR_PUBLISHER"}


def test_a_dry_run_reports_the_rows_and_writes_nothing(tmp_path, export, main_root):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    dry = queue(store, export, main_root, dry_run=True)
    assert dry["dry_run"] is True and len(dry["would_queue"]) == 3 and "queued" not in dry
    assert store.list_outbox_messages(destination=DESTINATION) == []
    queue(store, export, main_root)
    assert queue(store, export, main_root, dry_run=True)["would_queue"] == []


def test_a_refused_export_is_named_and_queues_nothing(tmp_path, main_root):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    folder = write_export(tmp_path / "bad", [plan("plan_gold", "XAUUSD", "BULLISH", 4070, 4085, invalid=4055)],
                          [event("plan_gold", "WAITING", "2026-11-05T12:10:00Z")], tampered=True)
    result = queue(store, folder, main_root)
    assert result == {"status": "EXPORT_UNREADABLE", "cause": "PLAN_EXPORT_UNREADABLE:PUBLIC_PLAN_STATUS_SCHEMA_INVALID"}
    assert store.list_outbox_messages(destination=DESTINATION) == []


def test_no_export_yet_queues_nothing(tmp_path, main_root):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    result = queue(store, tmp_path / "absent", main_root)
    assert result["status"] == "OK" and result["queued"] == [] and result["transitions_read"] == 0


@pytest.mark.parametrize("target,printed", [
    (82500, False),                                   # cancel at the target: never printed
    ({"minimum": 82000, "maximum": 83000}, False),    # cancel inside the target's range
    (84000, True),                                    # a known target clear of the cancel level
    (None, False),                                    # no target known
])
def test_a_runaway_cancel_at_the_target_never_reveals_the_number(tmp_path, main_root, target, printed):
    row = plan("plan_btc", "BTCUSD", "BULLISH", 79850, 80150, cancel=82500, invalid=79200)
    if target is not None:
        row["target"] = target
    folder = write_export(tmp_path / "btc", [row], [event("plan_btc", "WAITING", "2026-11-05T12:10:00Z")])
    text = compose(read_transitions(folder, main_root=main_root, python=sys.executable)[0])["text"]
    assert ("82,500" in text) is printed
    if not printed:
        assert "If price runs away before any pullback, the plan is cancelled and we re-assess." in text

def test_a_later_state_of_an_announced_plan_posts_late_but_unannounced_history_does_not(tmp_path, main_root):
    """6 Nov: oil's invalidation reached the export after the window, and the public setup kept showing it."""
    from live_contentops.plan_status_posts_v1 import WORK_ITEM_ID, freshness_limit_minutes
    plans = [plan("plan_gold", "XAUUSD", "BULLISH", 4070, 4085, cancel=4150, invalid=4055),
             plan("plan_oil", "USOIL", "BEARISH", 61.2, 61.8, cancel=59.5, invalid=62.4)]
    events = [event("plan_gold", "WAITING", "2026-11-05T09:00:00Z"),
              event("plan_gold", "INVALIDATED", "2026-11-05T10:00:00Z", "WATCH_INVALIDATED"),
              event("plan_oil", "WAITING", "2026-11-05T09:00:00Z"),
              event("plan_oil", "CANCELLED", "2026-11-05T10:00:00Z", "RUNAWAY_CANCEL")]
    late_export = write_export(tmp_path / "late", plans, events)
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    store.create_work_item(story_id=WORK_ITEM_ID, title="Plan status posts (decision 79)",
                           target_surface="MULTI_PLATFORM", work_item_id=WORK_ITEM_ID)
    store.register_outbox_message(message_id="announced-gold-setup", work_item_id=WORK_ITEM_ID,
                                  destination=DESTINATION, status="PUBLISHED",
                                  payload=json.dumps({"plan_id": "plan_gold", "state": "WAITING"}))
    result = queue(store, late_export, main_root)
    assert [(q["symbol"], q["state"]) for q in result["queued"]] == [("XAUUSD", "INVALIDATED")]
    assert result["older_than_window"] == 3
    late_row = next(r for r in store.list_outbox_messages(destination=DESTINATION)
                    if r["message_id"] != "announced-gold-setup")
    payload = json.loads(late_row["payload"])
    assert payload["late"] is True and freshness_limit_minutes(payload) == 24 * 60
    assert freshness_limit_minutes({"state": "WAITING"}) == 60

def _announce(store, plan_id):
    from live_contentops.plan_status_posts_v1 import WORK_ITEM_ID
    store.create_work_item(story_id=WORK_ITEM_ID, title="Plan status posts (decision 79)",
                           target_surface="MULTI_PLATFORM", work_item_id=WORK_ITEM_ID)
    store.register_outbox_message(message_id="announced-" + plan_id, work_item_id=WORK_ITEM_ID, destination=DESTINATION,
                                  status="PUBLISHED", payload=json.dumps({"plan_id": plan_id, "state": "WAITING"}))


@pytest.mark.parametrize("announced", [False, True])
def test_a_withdrawal_posts_only_for_a_plan_readers_saw_and_before_the_new_plan(tmp_path, main_root, announced):
    """Jim, 6 Nov: EUR/USD's new sell plan went out, then 'view changed' about an older plan whose setup post had
    been refused; readers saw a plan and its withdrawal of something they never read."""
    plans = [plan("plan_old", "EURUSD", "BEARISH", 1.1255, 1.1272, invalid=1.1305),
             plan("plan_new", "EURUSD", "BEARISH", 1.1187, 1.1191, invalid=1.1204)]
    events = [event("plan_new", "WAITING", "2026-11-05T12:19:32Z"),
              event("plan_old", "VIEW_CHANGED", "2026-11-05T12:20:18Z", "THESIS_CHANGED")]
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    if announced:
        _announce(store, "plan_old")
    result = queue(store, write_export(tmp_path / "swap", plans, events), main_root)
    order = [(q["state"], q["at_utc"]) for q in result["queued"]]
    if announced:
        assert order == [("VIEW_CHANGED", "2026-11-05T12:20:18Z"), ("WAITING", "2026-11-05T12:19:32Z")]
    else:
        assert order == [("WAITING", "2026-11-05T12:19:32Z")]
        assert [s["cause"] for s in result["not_posted"]] == ["PLAN_NEVER_ANNOUNCED"]

def test_a_fill_confirms_the_model_position_at_its_own_clock(tmp_path, main_root):
    """CC-331 / decision 106: accept the whole batch and prefer the true fill to its earlier trigger."""
    plans = [plan("plan_eur", "EURUSD", "BEARISH", 1.1187, 1.1191, invalid=1.1204)]
    events = [event("plan_eur", "WAITING", "2026-11-05T12:00:00Z"),
              event("plan_eur", "TRIGGERED", "2026-11-05T12:10:00Z"),
              event("plan_eur", "FILLED", "2026-11-05T12:10:05Z")]
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    result = queue(store, write_export(tmp_path / "fill", plans, events), main_root)
    assert result["status"] == "OK"
    assert [(q["symbol"], q["state"]) for q in result["queued"]] == [("EURUSD", "WAITING"), ("EURUSD", "TRIGGERED")]
    assert result["queued"][1]["at_utc"] == "2026-11-05T12:10:05Z"
    assert [s["cause"] for s in result["not_posted"]] == ["FILL_EVENT_SUPERSEDES_TRIGGER"]


def test_a_resting_order_fill_posts_once_as_price_reaching_the_zone(tmp_path, main_root):
    """CC-360 (9 Nov): a resting order goes WAITING -> FILLED with no TRIGGERED. Readers learn that price reached
    the zone, at the fill's clock, with no order or size words; a placement alone posts nothing."""
    plans = [plan("plan_eur", "EURUSD", "BULLISH", 1.1166, 1.117, invalid=1.1144)]
    events = [event("plan_eur", "WAITING", "2026-11-05T12:00:00Z"),
              event("plan_eur", "FILLED", "2026-11-05T12:10:05Z")]
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    folder = write_export(tmp_path / "fill", plans, events)
    result = queue(store, folder, main_root)
    assert [(q["symbol"], q["state"], q["at_utc"]) for q in result["queued"]] == [
        ("EURUSD", "WAITING", "2026-11-05T12:00:00Z"), ("EURUSD", "TRIGGERED", "2026-11-05T12:10:05Z")]
    text = result["queued"][1]["text"]
    assert text.startswith("EUR/USD: the 1.1166–1.117 entry zone filled at Thu 5 Nov, 07:10 ET, and Capital"
                           " Chronicle's position is open.")
    # CC-423 permits only the exact demo-position notice; execution details stay private.
    assert not re.search(r"\b(?:order|lots?|size|demo|account)\b", text.replace(CONFLICTS_NOTICE, ""), re.I)
    assert queue(store, folder, main_root)["queued"] == []

