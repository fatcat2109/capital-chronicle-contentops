"""Replay confirmed Capital Chronicle posts without contacting their transports."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from live_contentops.plan_analysis_pages_v1 import public_filter
from live_contentops.public_time_v1 import public_timestamp, require_public_time
from live_contentops.tradingview_snapshot_v1 import validate_snapshot_asset


FIXTURES = Path(__file__).parent / "fixtures" / "cc691"


@pytest.fixture(scope="module")
def saved_posts():
    return json.loads((FIXTURES / "posts.json").read_text(encoding="utf-8"))


def _chart(post):
    asset = deepcopy(post["asset"])
    asset["path"] = FIXTURES / asset["path"]
    snapshot = asset["tradingview_snapshot"]
    snapshot["path"] = FIXTURES / snapshot["path"]
    return asset


def test_decision_82_the_attached_tradingview_chart_matches_the_post_market(saved_posts):
    gold, bitcoin = (saved_posts["charts"][market] for market in ("gold", "bitcoin"))
    validate_snapshot_asset(_chart(gold), {"market_asset": gold["market"]})
    bitcoin_chart = _chart(bitcoin)
    validate_snapshot_asset(bitcoin_chart, {"market_asset": bitcoin["market"]})

    with pytest.raises(ValueError, match="TRADINGVIEW_SNAPSHOT_BINDING_INVALID"):
        validate_snapshot_asset(bitcoin_chart, {"market_asset": gold["market"]})


def test_decision_90_the_update_uses_new_york_time(saved_posts):
    update = saved_posts["timed_plan_update"]
    require_public_time(update["text"])
    clock = public_timestamp(update["event_utc"]).split(" on ")[0]
    assert update["rendered_timestamp"].endswith(f" {clock}.")
    assert update["rendered_timestamp"] in update["text"]

    broken = update["text"].replace(clock, "12:36 GMT+7")
    with pytest.raises(ValueError, match="PUBLIC_TIMEZONE_ET_REQUIRED"):
        require_public_time(broken)


@pytest.mark.parametrize("label", ["An AI-run desk.", "Written by Claude."])
def test_decision_109_the_plan_reply_keeps_internal_authorship_out_of_copy(saved_posts, label):
    text = saved_posts["plan_analysis_reply"]["text"]
    assert public_filter(text)["status"] == "PASS"

    with pytest.raises(ValueError, match="PLAN_ANALYSIS_DESK_AI_LABEL_FORBIDDEN"):
        public_filter(f"{text}\n{label}")
