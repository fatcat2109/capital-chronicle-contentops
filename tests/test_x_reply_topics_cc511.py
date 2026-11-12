from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from live_contentops import x_reply_bot_v1 as bot
from live_contentops import x_reply_fact_policy_v1 as policy
from live_contentops import x_reply_fact_sources_v1 as facts
from live_contentops import x_reply_pack_v1 as packs
from live_contentops.x_reply_topics_v1 import driver_links


CASES = json.loads((Path(__file__).resolve().parents[1] /
    "docs/publisher/CC-511/topic-cases.json").read_bytes())["cases"]
NOW = datetime(2026, 11, 12, 15, tzinfo=timezone.utc)


def post(text, **extra):
    return {"post_id": "123", "post_text": text, "author_handle": "FirstSquawk",
            "post_time_utc": (NOW - timedelta(minutes=2)).isoformat(), "reply_count": 0, **extra}


def source(market):
    return {"source_id": "fact-" + market, "kind": "HELD_MARKET_FACT", "label": market,
            "known_at_utc": NOW.isoformat(), "excerpt": {"NDX": "Nasdaq 100: 20,000 points.",
            "SPX": "S&P 500: 7,000 points.", "XAUUSD": "Gold: 4,000 USD.",
            "EURUSD": "EUR/USD: 1.1 USD per EUR."}.get(market, market + ": 4."),
            "fact_binding": {"kind": "session", "markets": [market], "observed_at_utc": NOW.isoformat()}}


@pytest.mark.parametrize("case", CASES, ids=lambda row: row["post_id"])
def test_eight_exact_posts_from_the_12_november_record(case):
    row = {"tweet_id": case["post_id"], "text": case["text"], "handle": case["author_handle"],
           "url": f'https://x.com/{case["author_handle"]}/status/{case["post_id"]}',
           "posted_utc": case["posted_utc"]}
    now = policy.utc(case["posted_utc"]) + timedelta(minutes=1)
    selected, causes = packs.select_posts({"rows": [row]}, handles={row["handle"].casefold()}, now=now, mobile=True)
    assert bool(selected) is case["expected_on_topic"]
    if selected:
        assert selected[0]["market_links"] and policy.target_markets(selected[0])
    else:
        assert causes == {"NO_SIX_MARKET_OR_MACRO_TOPIC": 1}


@pytest.mark.parametrize("text,expected", [
    ("Nvidia shares fall premarket", {"NDX", "SPX"}),
    ("US bank shares fall after earnings", {"SPX"}),
    ("US technology sector drops premarket", {"NDX", "SPX"}),
    ("Iran vows to strike US bases if war restarts", {"WTI", "BRENT", "XAUUSD"}),
    ("Russian refinery attacks disrupt exports", {"WTI", "BRENT", "XAUUSD"}),
    ("Fed speaker sees inflation risk", {"DXY", "EURUSD", "USDJPY", "XAUUSD"}),
    ("ECB speaker discusses policy", {"EURUSD", "DXY", "XAUUSD"}),
    ("BoJ speaker discusses policy", {"USDJPY", "DXY", "XAUUSD"}),
    ("US Treasury auction tails", {"DXY", "EURUSD", "USDJPY", "XAUUSD"}),
    ("OPEC cuts output", {"WTI", "BRENT"}),
    ("API crude inventories show a draw", {"WTI", "BRENT"}),
    ("IBIT fund inflows accelerate", {"BTCUSD"}),
    ("Digital asset regulation changes", {"BTCUSD"}),
])
def test_named_driver_families_have_an_explained_market_tie(text, expected):
    links = driver_links(text)
    assert {market for link in links for market in link["markets"]} == expected
    assert all(link["relationship"] for link in links)


@pytest.mark.parametrize("text", [
    "Russian and Ukrainian officials agree a prisoner exchange",
    "Iran appoints an ambassador to Europe",
    "Nvidia sponsors a local chess tournament",
    "A new municipal warehouse inventory system",
    "OPEC delegates attend a charity dinner",
    "SEC announces an office refurbishment",
])
def test_a_name_without_a_market_driver_stays_out(text):
    assert not driver_links(text)


@pytest.mark.parametrize("text,market,good", [
    ("Nvidia shares slide premarket", "NDX", "Nvidia's slide pressures Nasdaq 100 stocks, at 20,000 points."),
    ("Iran vows to strike US bases if war restarts", "XAUUSD", "Iran's war risk supports gold, at 4,000 USD."),
    ("Germany's DAX hits a record high", "EURUSD", "The DAX rally supports EUR/USD risk appetite, at 1.1 USD per EUR."),
])
def test_linked_facts_reach_selection_but_the_draft_must_explain_the_link(text, market, good):
    target, fact = post(text), source(market)
    assert policy.check_fact(target, fact, now=NOW)
    with pytest.raises(ValueError, match="FACT_DRIVER_LINK_NOT_STATED"):
        policy.check_fact(target, fact, now=NOW, draft={"draft_text": fact["excerpt"]})
    assert policy.check_fact(target, fact, now=NOW, draft={"draft_text": good})


def test_an_explicit_index_never_takes_another_index_via_a_company_link():
    target = post("Nasdaq 100 falls as Nvidia shares slide")
    assert policy.target_markets(target) == {"NDX"}
    with pytest.raises(ValueError, match="FACT_MARKET_MISMATCH"):
        policy.check_fact(target, source("SPX"), now=NOW,
                          draft={"draft_text": "Nvidia's slide pressures S&P 500 stocks, at 7,000 points."})


def test_forged_relationship_metadata_never_admits_an_unrelated_fact():
    target = post("A diplomatic appointment", market_links=driver_links("Iran war"))
    with pytest.raises(ValueError, match="FACT_MARKET_UNIDENTIFIED"):
        policy.check_fact(target, source("XAUUSD"), now=NOW)


def test_new_topic_still_requires_a_fresh_source_observation():
    fact = source("NDX")
    fact["fact_binding"]["observed_at_utc"] = (NOW-timedelta(days=1)).isoformat()
    with pytest.raises(ValueError, match="FACT_SESSION_NOT_CURRENT"):
        policy.check_fact(post("Nvidia shares slide"), fact, now=NOW)


def test_linked_markets_feed_the_existing_quote_and_rank_consumers(tmp_path, monkeypatch):
    from live_contentops import chart_price_reference_v1 as prices
    from live_contentops import public_market_quote_v1 as public
    from live_contentops import x_reply_base_rates_v1 as rates

    target = post("U.S. CHIPSTOCKS FALL PREMARKET FOLLOWING NVIDIA'S SLIDE")
    markets_read = []

    def quote(market, *args, **kwargs):
        markets_read.append(market)
        return {"price": 20000, "quoted_at_utc": NOW.isoformat(), "known_at_utc": NOW.isoformat()}

    monkeypatch.setattr(prices, "plan_status_quote", quote)
    monkeypatch.setattr(public, "freeze", lambda value: {**value, "observation_path": "fixture",
                                                        "observation_sha256": "fixture"})
    additional, attempts, _ = facts.supplement([target], [], now=NOW)
    assert "NDX" in markets_read and "US500" in markets_read
    assert {m for value in additional for m in value["fact_binding"]["markets"]} == {"NDX", "SPX"}
    monkeypatch.setattr(packs, "held_sources", lambda *a, **kw: [])
    monkeypatch.setattr(facts, "load", lambda **kw: ([], []))
    monkeypatch.setattr(facts, "supplement", lambda *a, **kw: (additional, attempts, NOW))
    monkeypatch.setattr(rates, "collect", lambda *a, **kw: ([], []))
    monkeypatch.setattr(packs, "report_manual_replies", lambda *a, **kw: {})
    feed = tmp_path / "feed.json"
    packs.save_json(feed, {"generated_at_utc": NOW.isoformat(), "rows": [{
        "tweet_id": target["post_id"], "text": target["post_text"], "handle": "FirstSquawk",
        "url": "https://x.com/FirstSquawk/status/123", "posted_utc": target["post_time_utc"]}]})
    ready = packs.prepare(None, feed_path=feed, output_root=tmp_path, now=NOW, reply_policy=packs.MOBILE_POLICY)
    captured = []

    def ranker(prompt, **kwargs):
        captured.extend(json.loads(prompt.split("\n", 1)[1])["candidates"])
        return {"ranking": []}, {"caller": "fixture"}

    bot.rank_and_draft(ready["request_path"], output_dir=tmp_path / "rank", ranker=ranker, now=NOW)
    assert captured[0]["available_facts"]
    assert captured[0]["market_links"][0]["markets"] == ["NDX", "SPX"]
