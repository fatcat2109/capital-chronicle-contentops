"""Jim, 23 Nov 2026 about 05:30 GMT+7: "Keep targets off." Decision 40: no profit target in public copy."""
from datetime import datetime, timezone
import sys

from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_state_alerts_v1 as alerts
from live_contentops import plan_status_posts_v1 as posts
from test_plan_call_cards_cc399 import controlled_tradingview, write, rows  # noqa: F401
from test_plan_status_posts_cc306 import main_root, event  # noqa: F401
from test_plan_state_alerts_cc543 import replay  # noqa: F401


def test_new_rows_print_no_target_and_old_rows_keep_their_bytes(replay, main_root, monkeypatch):
    store, folder, raw, now = replay
    assert raw.get("target_level") is not None or (raw.get("public_instrument") or {}).get("target") is not None \
        or cards.card_plan(raw).get("target"), "the fixture plan carries a target"
    monkeypatch.setattr(cards, "NO_TARGET_EFFECTIVE", datetime(2026, 1, 1, tzinfo=timezone.utc))
    queued = posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)
    assert queued["status"] == "OK", queued
    row, = rows(store)
    assert row["target_policy"] == cards.NO_TARGET_POLICY
    assert "target" not in row["text"].lower()
    alerts.validate(row, store=store)
    legacy = {k: v for k, v in row.items() if k != "target_policy"}
    assert "Target level: " in alerts.compose(legacy)["text"]


def test_rows_queued_before_the_decision_keep_the_target_line(replay, main_root):
    store, folder, raw, now = replay  # the retained 12 Nov plan, queued on its own clock
    queued = posts.queue_posts(store, folder, now=now, main_root=main_root, python=sys.executable)
    assert queued["status"] == "OK", queued
    row, = rows(store)
    assert "target_policy" not in row
    alerts.validate(row, store=store)
