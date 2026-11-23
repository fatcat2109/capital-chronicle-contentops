"""A result names its plan's dates, and a corrected outcome says so (t.me/CapitalChronicle/230, 23 Nov 2026)."""
from datetime import datetime, timezone

import pytest

from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_state_alerts_v1 as alerts
from test_plan_copy_cc682 import gold_export, replay_gold, GOLD_ENDING  # noqa: F401
from test_plan_status_posts_cc306 import main_root  # noqa: F401


@pytest.fixture
def frame_policy_on(monkeypatch):
    monkeypatch.setattr(cards, "RESULT_FRAME_EFFECTIVE", datetime(2026, 1, 1, tzinfo=timezone.utc))


def test_rows_queued_before_the_policy_keep_their_exact_text(replay_gold):
    _, _, result = replay_gold
    assert "result_frame" not in result and result["text"].startswith(GOLD_ENDING)
    assert alerts.compose(result)["text"] == result["text"]


def test_a_framed_result_leads_with_its_dates_and_a_corrected_one_says_correction(replay_gold):
    _, _, result = replay_gold
    frame = cards.result_frame(result)
    assert frame["plan_dates"] == cards.plan_dates(result["registered_at_utc"], result["at_utc"])
    assert alerts.compose({**result, "result_frame": frame})["text"].startswith(
        f"Gold, plan of {frame['plan_dates']}: hit its target. Result: +1.6R.")
    corrected = {**result, "corrects_outcome_id": "outcome-earlier"}
    corrected["result_frame"] = cards.result_frame(corrected)
    assert corrected["result_frame"]["correction"] is True
    assert alerts.compose(corrected)["text"].startswith(
        f"Correction to the {frame['plan_dates']} Gold result: hit its target.")


def test_rows_queued_after_the_policy_carry_the_frame_and_validate(frame_policy_on, replay_gold):
    setup, fill, result = replay_gold  # the fixture validates every queued row against its recomposed copy
    assert "result_frame" not in setup and "result_frame" not in fill
    assert result["result_frame"] == {"policy": cards.RESULT_FRAME_POLICY, "correction": False,
                                      "plan_dates": cards.plan_dates(result["registered_at_utc"], result["at_utc"])}
    assert result["text"].startswith(f"Gold, plan of {result['result_frame']['plan_dates']}: hit its target.")


@pytest.mark.parametrize(("start", "end", "words"), [
    ("2026-11-17T06:28:43Z", "2026-11-18T18:30:00Z", "17–18 Nov"),
    ("2026-11-20T08:14:00Z", "2026-11-20T20:45:00Z", "20 Nov"),
    ("2026-11-30T15:00:00Z", "2026-12-01T18:00:00Z", "30 Nov–1 Dec"),
    ("2026-11-21T03:00:00Z", "2026-11-21T04:00:00Z", "20 Nov"),  # 22:00-23:00 ET on 20 Nov
])
def test_plan_dates_use_the_public_calendar(start, end, words):
    assert cards.plan_dates(start, end) == words
