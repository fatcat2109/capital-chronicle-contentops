"""CC-469: the TradingView idea pack on the posting desk, from stored plan posts of 20-22 Nov 2026."""
from copy import deepcopy
from datetime import timedelta
import json
from pathlib import Path

import pytest

from live_contentops import manual_desk_v1 as desk
from live_contentops import tradingview_idea_v1 as tv
from live_contentops.tradingview_snapshot_v1 import SYMBOLS
from test_manual_desk_cc748 import (  # noqa: F401  (the world fixture)
    FIRST_POST, FakeBot, confirm_page, platform_payload, read_packs, refresh, update_message, world,
)

FIXTURE = Path(__file__).parent / "fixtures" / "tradingview_idea_cc469_plans.json"


def stored_plans():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["plans"]


@pytest.fixture
def usdjpy():
    return next(p for p in stored_plans() if p["symbol"] == "USDJPY")


@pytest.fixture
def ready(usdjpy):
    idea = tv.idea_entry(usdjpy)
    assert idea["status"] == "READY", idea
    return idea


@pytest.mark.parametrize("plan", stored_plans(), ids=lambda p: p["symbol"] + "-" + p["kind"])
def test_stored_plans_of_20_to_22_nov_make_packs_that_pass_the_check(plan):
    idea = tv.idea_entry(plan)
    assert idea["status"] == "READY", idea
    assert idea["check"] == "PASS" and tv.check_idea(idea) == "PASS"
    title, description = idea["title"], idea["description"]
    # A normal-case title stating the view, its zone, its invalidation and its date.
    assert title != title.upper() and len(title) <= tv.TITLE_LIMIT
    assert "bearish" in title and "wrong above" in title and "Nov 2026" in title
    # Base and bull cases with their odds and causes, built from the plan's own fields.
    base = plan["levels"]["scenario_analysis"]["base_case"]["probability_pct"]
    alternative = plan["levels"]["scenario_analysis"]["main_alternative"]["probability_pct"]
    assert f"Base case (bear, {base:g}%): " in description
    assert f"Bull case ({alternative:g}%): " in description
    assert description.count("Why: ") >= 2
    assert "Entry zone " in description and "Invalidation: " in description
    assert "Dates: Plan of " in description and " ET" in description
    # The stored post carried a target line; the idea never does.
    assert "Target level" in plan["text"]
    assert "target" not in description.casefold() and "target" not in title.casefold()
    for absent in ("http", "www.", "Capital Chronicle", "substack", "Telegram", "today", "UTC", "Z."):
        assert absent not in description and absent not in title
    chart = idea["chart"]
    assert chart["symbol"] == SYMBOLS[plan["symbol"]]
    assert [d["label"] for d in chart["draw"]] == ["Entry zone", "Invalidation"]
    assert "Publish idea" in idea["how_to_post"] and "nothing else" in idea["how_to_post"]


def test_usdjpy_pack_reads_its_own_numbers_and_horizon(ready, usdjpy):
    assert ready["title"] == "USD/JPY: bearish at 158.8–158.88, wrong above 159.6 (20 Nov 2026)"
    assert "The plan: bearish on USD/JPY if price breaks through 158.88 (breakout). Entry zone 158.8–158.88." \
        in ready["description"]
    assert "157.95" not in ready["description"]  # the stored target level
    # Written 20 Nov 08:14Z, the view runs to 23 Nov 06:00Z: a 4-hour chart.
    assert ready["chart"]["interval"] == "240" and ready["chart"]["timeframe"] == "4-hour"
    assert "the view runs to Mon 23 Nov 2026, 1:00 AM ET (short-term horizon)" in ready["description"]


def test_long_horizon_plan_gets_a_daily_chart_and_grouped_numbers():
    btc = next(p for p in stored_plans() if p["symbol"] == "BTCUSD")
    idea = tv.idea_entry(btc)
    assert idea["chart"]["interval"] == "D" and idea["chart"]["symbol"] == "COINBASE:BTCUSD"
    assert "60,000–61,400" in idea["title"] and "68,450" in idea["title"]
    assert "60600.84" not in idea["description"] and "60,601" in idea["description"]
    assert "broker" not in idea["description"] and "MISSING" not in idea["description"]


@pytest.mark.parametrize("change,cause", [
    (lambda i: i.update(description=i["description"] + "\n\nMore at https://example.com/ideas"), "LINK"),
    (lambda i: i.update(description=i["description"] + "\n\nFull analysis on capitalchronicle.substack.com"), "LINK"),
    (lambda i: i.update(description=i["description"] + "\n\nWrite to desk@example.org"), "LINK"),
    (lambda i: i.update(title=i["title"] + " by Capital Chronicle"), "BRAND"),
    (lambda i: i.update(description=i["description"] + "\n\nJoin our Telegram channel."), "CONTACT_REFERENCE"),
    (lambda i: i.update(description=i["description"] + "\n\nTarget level: 157.95."), "TARGET"),
    (lambda i: i.update(description=i["description"] + "\n\nTake profit near 157.95."), "TARGET"),
    (lambda i: i["chart"]["draw"].append({"tool": "horizontal line", "level": "157.95", "label": "Target"}), "TARGET"),
    (lambda i: i.update(description=i["description"] + "\n\nWritten with Claude."), "AI_LABEL"),
    (lambda i: i.update(description=i["description"] + "\n\nAn AI desk view."), "AI_LABEL"),
    (lambda i: i.update(description=i["description"] + "\n\nWatch today's data."), "RELATIVE_DAY"),
    (lambda i: i.update(title=i["title"].upper()), "TITLE_CAPITALS"),
    (lambda i: i.update(description=i["description"] + "\n\nPhân tích vàng."), "NOT_ENGLISH"),
    (lambda i: i.update(description="Base case only."), "DESCRIPTION_REQUIRED"),
])
def test_check_refuses_links_brand_targets_ai_words_relative_days_and_shouting(ready, change, cause):
    idea = deepcopy(ready)
    change(idea)
    with pytest.raises(tv.IdeaError, match="TRADINGVIEW_IDEA_" + cause):
        tv.check_idea(idea)


def test_a_policy_target_in_the_analysis_is_not_a_price_target(ready):
    idea = deepcopy(ready)
    idea["description"] += "\n\nInflation target talk keeps the Fed cautious."
    assert tv.check_idea(idea) == "PASS"


def test_only_new_plans_in_the_six_markets_get_a_pack(usdjpy):
    assert tv.idea_entry({**usdjpy, "kind": "result"}) is None
    assert tv.idea_entry({**usdjpy, "kind": "correction"}) is None
    assert tv.idea_entry({**usdjpy, "symbol": "ETHUSD", "source_plan": {"asset_id": "ETHUSD"}}) is None


def test_a_plan_without_an_alternative_case_is_withheld_with_its_cause(usdjpy):
    plan = deepcopy(usdjpy)
    plan["levels"]["scenario_analysis"].pop("main_alternative")
    assert tv.idea_entry(plan) == {"status": "WITHHELD", "cause": "TRADINGVIEW_IDEA_ALTERNATIVE_CASE_REQUIRED",
                                   "plan_id": usdjpy["plan_id"]}


def test_internal_codes_and_relative_days_never_reach_the_description():
    text = ("BTCUSD is below 60600.84 at 2026-12-09T18:00Z; DVOL 58.02 on 21 Nov per block cc415:2026-11-22T18:36:29Z, "
            "about 7,590 one sigma; the priced_in gap MISSING; today's driver departs from it.")
    cleaned = tv.clean(text, year=2026, keep=4)
    assert cleaned == ("BTCUSD is below 60,601 at Wed 9 Dec 2026, 1:00 PM ET. "
                       "DVOL 58.02 on 21 Nov, about 7,590 one sigma.")


# ------------------------------------------------------------------ on the desk

def add_stored_plan(world, plan):
    store = world["store"]
    key = plan["key"]
    payload = {k: v for k, v in plan.items() if not k.startswith("store_")}
    store.row("plan-status-posts-v1", "internal:plan-status-post", payload, status="PUBLISHED", at=FIRST_POST,
              dispatch=False, message_id=key)
    store.row(key, "telegram", platform_payload("telegram", plan["text"], world["out"]), at=FIRST_POST)
    return key


def test_the_desk_pack_carries_the_idea_on_the_page_and_in_the_first_phone_send(world, usdjpy):
    add_stored_plan(world, usdjpy)
    confirm_page(world, plan_id=usdjpy["plan_id"])
    result, bot = refresh(world, FIRST_POST + timedelta(minutes=6))
    assert result["status"] == "OK" and not result["build_causes"], result
    [pack] = read_packs(world)
    idea = pack["tradingview_idea"]
    assert idea["status"] == "READY" and idea["check"] == "PASS"
    assert idea == tv.idea_entry(usdjpy) | {"status": "READY"}
    page = (world["desk"] / "index.html").read_text(encoding="utf-8")
    assert "TradingView idea" in page and "Copy the description" in page
    sent = bot.sent_texts()
    assert idea["title"] in sent and idea["description"] in sent
    assert any(t.startswith("TRADINGVIEW IDEA · In TradingView open FX_IDC:USDJPY") for t in sent)
    # The idea needs no Posted mark: the pack's state follows the four hand platforms as before.
    assert "tradingview" not in pack["unposted_platforms"]
    _, again = refresh(world, FIRST_POST + timedelta(minutes=7))
    assert again.sent_texts() == []


def test_a_reply_to_an_idea_message_is_not_a_posted_mark(world, usdjpy):
    add_stored_plan(world, usdjpy)
    confirm_page(world, plan_id=usdjpy["plan_id"])
    refresh(world, FIRST_POST + timedelta(minutes=6))
    ledger = [json.loads(line) for line in (world["desk"] / "sent.jsonl").read_text(encoding="utf-8").splitlines()]
    idea_message = next(r["message_id"] for r in ledger if r.get("platform") == "tradingview")
    update = update_message(31, "https://www.tradingview.com/chart/abc/", reply_to=idea_message)
    assert desk.accept_update(update, desk_root=world["desk"], now=FIRST_POST + timedelta(minutes=8)) is None


def test_other_pieces_carry_no_idea(world):
    from test_manual_desk_cc748 import add_plan_post
    add_plan_post(world)
    confirm_page(world)
    refresh(world, FIRST_POST + timedelta(minutes=6), bot=FakeBot())
    [pack] = read_packs(world)
    assert "tradingview_idea" not in pack
