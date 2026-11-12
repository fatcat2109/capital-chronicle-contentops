from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import math

import pytest

from live_contentops import x_reply_base_rates_v1 as rates
from live_contentops import x_reply_bot_v1 as bot
from live_contentops import x_reply_fact_policy_v1 as policy
from live_contentops import x_reply_fact_sources_v1 as held
from live_contentops import x_reply_pack_v1 as packs
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

NOW = datetime(2026, 11, 12, 16, tzinfo=timezone.utc)
HEADLINES = ["Gold rises 0.5%", "EUR/USD falls 0.3%", "USD/JPY gains 0.4%",
             "WTI crude oil falls 0.3%", "S&P 500 rises 2.1%", "Bitcoin rises 1.2%"]


def post(text=HEADLINES[0]):
    return {"post_text": text, "post_time_utc": (NOW - timedelta(minutes=2)).isoformat(),
            "post_id": "123", "post_url": "https://x.com/FirstSquawk/status/123",
            "kind": "target", "author_handle": "FirstSquawk", "reply_count": 2}


class Producer:
    def __init__(self):
        self.calls = []
        self.mutate = lambda a: a

    def active_rows(self, market, completed):
        return [("LONG_WHILE_UP_20", 1), ("WITH_YARDSTICK_5", 1)]

    def stats_after(self, **query):
        self.calls.append(query)
        market = query["market"]
        instrument = {"XAUUSD": "GC=F", "US500": "ES=F", "USOIL": "CL=F"}.get(market, market)
        # Deliberately not inferable from either the census mean or share.
        n, hits = (48, 31) if query["horizon"] == 1 else (93, 47)
        return self.mutate({"schema": "MarketStatisticsAnswerV1", "state": "AVAILABLE", "market": market,
            "timeframe": "D1", "horizon_bars": query["horizon"],
            "condition": {k: v for k, v in query["condition"].items() if k != "through_utc"},
            "case_count": n, "terminal_up": {"n": n, "hits": hits, "share": 0.12345},
            "sample_from_utc": "2016-11-14T05:00:00Z", "sample_through_utc": "2026-11-11T05:00:00Z",
            "series_id": "YAHOO_FINANCE:" + instrument, "rate_interval_95_pct": [40, 70],
            "selection": "CHRONOLOGICAL_MATCHES_WITH_NONOVERLAPPING_OUTCOME_WINDOWS",
            "zero_returns_in_denominator": True,
            "sources": [{"known_at_utc": "2026-11-12T04:00:00Z", "source_id": "source-" + market,
                         "source_instrument": instrument, "price_basis": "UNADJUSTED_SOURCE_OHLC"}]})


@pytest.fixture
def census(tmp_path):
    path = tmp_path / "odds.json"
    table = {"generated_at_utc": "2026-11-12T10:10:04Z", "content_hash": "producer-census-hash",
        "columns": ["behaviour", "n", "mean_r", "t", "first_half_r", "second_half_r", "read"],
        "behaviours": {"LONG_WHILE_UP_20": "Long while the yardstick is UP.",
                       "WITH_YARDSTICK_5": "With the yardstick, either side.", "INACTIVE": "not active"},
        "markets": {m: {"from": "2016-11-14", "through": "2026-11-10"} for m in rates.LABELS},
        "by_market": {m: [["LONG_WHILE_UP_20", 76, 0.391, 2.2, 0.29, 0.49, "PAID_BOTH_HALVES"],
                          ["WITH_YARDSTICK_5", 349, 0.053, 1, 0, 0.11, "PAID"],
                          ["INACTIVE", 10000, 99, 99, 99, 99, "PAID"]] for m in rates.LABELS},
        "desk_record": {"MUST_NOT_USE": "private scored trades"},
        "all_six_markets": [["MUST_NOT_USE", 9000, 9.9]],
        "construction": {"pooled_win_share": 0.9}}
    path.write_text(json.dumps(table), encoding="utf-8")
    return path


@pytest.mark.parametrize("headline", HEADLINES)
def test_six_markets_reach_policy_with_producer_counts_and_both_horizons(census, headline):
    producer = Producer()
    sources, gaps = rates.collect([post(headline)], now=NOW, producer=producer, odds_path=census)
    assert not gaps and len(sources) == 2
    assert [s["fact_binding"]["horizon_sessions"] for s in sources] == [5, 1]
    assert [(s["fact_binding"]["count"], s["fact_binding"]["sample_count"]) for s in sources] == [(47, 93), (31, 48)]
    assert all(policy.check_fact(post(headline), s, now=NOW)["kind"] == "base_rate" for s in sources)
    assert {q["horizon"] for q in producer.calls} == {1, 5}
    assert all(q["condition"]["through_utc"] == "2026-11-12T05:00:00+00:00" for q in producer.calls)
    assert all(s["fact_binding"]["through_date"] == "2026-11-10" for s in sources)
    assert all("2016-11-14 to 2026-11-10" in s["excerpt"] for s in sources)


def test_census_uses_only_same_market_active_rows_sorted_by_sample_without_inventing_hits(census):
    sources, _ = rates.collect([post()], now=NOW, producer=Producer(), odds_path=census)
    context = sources[0]["artifact_binding"]["census"]
    assert context["market"] == "XAUUSD"
    assert [r["n"] for r in context["active_market_rows"]] == [349, 76]
    assert "not a market win numerator" in context["count_note"]
    assert "MUST_NOT_USE" not in json.dumps(sources)
    assert sources[0]["fact_binding"]["count"] == 47


def test_wrong_market_and_stronger_condition_are_refused(census):
    sources, _ = rates.collect([post()], now=NOW, producer=Producer(), odds_path=census)
    with pytest.raises(ValueError, match="FACT_MARKET_MISMATCH"):
        policy.check_fact(post("Bitcoin rises 0.5%"), sources[0], now=NOW)
    for headline in ("Gold rises 0.3%", "Gold falls 0.5%", "Gold rises", "Gold is unchanged"):
        with pytest.raises(ValueError, match="FACT_BASE_RATE_TARGET_CONDITION_NOT_MET"):
            policy.check_fact(post(headline), sources[0], now=NOW)
    assert policy.check_fact(post("Gold rises 0.7%"), sources[0], now=NOW)


def test_market_clauses_and_currency_direction_do_not_borrow_each_others_percent():
    result = rates.conditions("Gold rises 0.5%; Bitcoin falls 2.1%; S&P 500 gains 0.2%")
    assert [(c["market"], c["direction"], c["minimum_pct"]) for c in result] == [
        ("XAUUSD", "up", 0.5), ("BTCUSD", "down", 2.1), ("SPX", "up", 0.2)]
    yen = rates.conditions("Yen rises 0.3%")
    assert yen[0]["direction"] == "down" and yen[0]["minimum_pct"] is None


@pytest.mark.parametrize("headline,market", [("NASDAQ 100 RISES 2.1% TO SESSION HIGH", "NDX"),
    ("Brent falls 0.3%", "BRENT")])
def test_distinct_indices_and_oils_are_requested_by_their_own_market(census, headline, market):
    producer = Producer()
    rates.collect([post(headline)], now=NOW, producer=producer, odds_path=census)
    assert {q["market"] for q in producer.calls} == {market}


def test_record_uses_an_explicit_bounded_daily_analogue_not_an_invented_lifetime_count(census):
    producer = Producer()
    sources, _ = rates.collect([post("Gold at a record")], now=NOW, producer=producer, odds_path=census)
    assert len(sources) == 2
    assert all("prior 252-session highs" in s["excerpt"] for s in sources)
    assert all(q["condition"]["type"] == "breakout" for q in producer.calls)
    with pytest.raises(ValueError, match="TARGET_CONDITION_NOT_MET"):
        policy.check_fact(post("Gold rises 0.5%"), sources[0], now=NOW)


@pytest.mark.parametrize("mutation,cause", [
    (lambda a: {**a, "market": "US500"}, "MARKET_CONDITION_OR_HORIZON_MISMATCH"),
    (lambda a: {**a, "condition": {"type": "any"}}, "MARKET_CONDITION_OR_HORIZON_MISMATCH"),
    (lambda a: {**a, "terminal_up": {"hits": 999, "n": 48}}, "PRODUCER_COUNT_INVALID"),
    (lambda a: {**a, "sample_through_utc": "2026-11-12T17:00:00Z"}, "COMPLETION_OR_KNOWLEDGE_CLOCK_INVALID"),
    (lambda a: {**a, "sources": [{"known_at_utc": "2026-11-13T04:00:00Z"}]}, "COMPLETION_OR_KNOWLEDGE_CLOCK_INVALID"),
])
def test_bad_producer_rows_are_named_and_other_facts_can_continue(census, mutation, cause):
    producer = Producer()
    producer.mutate = mutation
    sources, gaps = rates.collect([post()], now=NOW, producer=producer, odds_path=census)
    assert not sources and len(gaps) == 2 and all(cause in g["cause"] for g in gaps)


def test_census_unavailability_does_not_wall_off_usable_statistics(tmp_path):
    sources, gaps = rates.collect([post()], now=NOW, producer=Producer(), odds_path=tmp_path / "absent.json")
    assert len(sources) == 2 and gaps[0]["cause"] == "DESK_ODDS_CONTEXT_UNAVAILABLE"


def test_threshold_is_converted_to_producers_log_return_units():
    condition = rates.conditions("Gold falls 0.3%")[0]
    query, words = rates.query_for(condition, 1, "2026-11-12T05:00:00Z")
    assert query["condition"]["maximum"] == pytest.approx(math.log1p(-0.003))
    assert words == "daily losses of at least 0.3%"


def test_brent_crude_oil_never_uses_wti_and_unrelated_release_percent_is_not_the_move():
    assert [c["market"] for c in rates.conditions("Brent crude oil falls 0.3%")] == ["BRENT"]
    assert rates.conditions("Gold falls after CPI rises 3.2%")[0]["minimum_pct"] is None
    assert rates.conditions("Gold falls nearly 1%")[0]["minimum_pct"] is None
    assert rates.conditions("Gold rises -0.3%") == []


def test_silver_and_another_sentences_subject_never_become_gold_moves():
    assert rates.conditions("Gold near $4,000. Silver rose 1.2%") == []
    assert rates.conditions("Gold near $4,000 while silver rises 1.2%") == []
    assert rates.conditions("Gold demand falls 2%") == []
    assert rates.conditions("Gold near $4,000 after CPI rises 3.2%") == []
    assert rates.conditions("Gold demand at a record high") == []
    assert rates.conditions("Gold futures are now rising by 0.3%")[0]["minimum_pct"] == 0.3


@pytest.mark.parametrize("currency", ["Aussie", "Australian", "Canadian", "New Zealand", "Taiwan", "Hong Kong", "Singapore"])
def test_another_dollar_is_not_the_us_dollar_index(currency):
    assert rates.conditions(currency + " dollar weakens 0.3%") == []
    assert rates.conditions("Gold near $4,000 as the " + currency + " dollar gains 0.3%") == []


@pytest.mark.parametrize("headline", ["Gold will rise 2%", "Gold could fall 2%", "Gold is likely to rise 2%",
                                        "Gold to rise 2%", "Gold rises if yields fall"])
def test_hypothetical_moves_are_not_observed_conditions(headline):
    assert rates.conditions(headline) == []


def test_resolve_reuses_the_original_as_known_query_and_detects_changed_counts(census, monkeypatch):
    producer = Producer()
    sources, _ = rates.collect([post()], now=NOW, producer=producer, odds_path=census)
    observed = []
    def factory(now, bindings):
        observed.append(now)
        return producer
    monkeypatch.setattr(rates, "Producer", factory)
    assert packs.resolve_fact_source(None, sources[0])["source_id"] == sources[0]["source_id"]
    assert observed == [NOW.isoformat()]
    producer.mutate = lambda a: {**a, "terminal_up": {**a["terminal_up"], "hits": 3}}
    with pytest.raises(ValueError, match="REPLY_SOURCE_BINDING_CHANGED"):
        packs.resolve_fact_source(None, sources[0])


def test_private_consumer_collects_ranks_builds_rechecks_and_formats_base_rate(census, tmp_path, monkeypatch):
    producer = Producer()
    original = rates.collect
    monkeypatch.setattr(rates, "collect", lambda posts, **kw: original(posts, producer=producer, odds_path=census, **kw))
    monkeypatch.setattr(rates, "Producer", lambda *a: producer)
    monkeypatch.setattr(held, "load", lambda **kw: ([], []))
    store = ContentOpsDurableStore(tmp_path / "isolated.sqlite3", auto_migrate=True)
    feed = tmp_path / "feed.json"
    packs.save_json(feed, {"generated_at_utc": NOW.isoformat(), "rows": [{"handle": "FirstSquawk",
        "text": HEADLINES[0], "url": post()["post_url"], "tweet_id": "123",
        "posted_utc": post()["post_time_utc"], "metrics": {"replies": 2}}]})
    ready = packs.prepare(store, feed_path=feed, output_root=tmp_path, now=NOW, reply_policy=packs.MOBILE_POLICY)
    request = packs.read_json(ready["request_path"])
    assert ready["candidate_count"] == 1 and len(request["candidates"][0]["usable_source_ids"]) == 2
    seen = []
    def ranker(prompt, **kw):
        seen.append(json.loads(prompt.split("\n", 1)[1]))
        return {"ranking": [{"post_id": "123", "quality_score": 90, "reason": "new historical count"}]}, {"caller": "fixture"}
    def writer(prompt, **kw):
        source = request["sources"][0]
        assert len(source["excerpt"].split()) <= 22
        return {"items": [{"post_id": "123", "source_id": source["source_id"],
            "draft_text": source["excerpt"], "fact_text": "47 of 93", "date_text": "2026-11-10",
            "source_name": "desk count", "addition": "historical forward count", "point": "daily analogue",
            "reply_shape": "base_rate"}]}, {"caller": "fixture"}
    response = bot.rank_and_draft(ready["request_path"], output_dir=tmp_path / "editorial", ranker=ranker, writer=writer, now=NOW)
    assert [f["sample_count"] for f in seen[0]["candidates"][0]["available_facts"]] == [93, 48]
    built = packs.build(store, request_path=ready["request_path"], response_path=response, feed_path=feed, output_root=tmp_path, now=NOW)
    pack = packs.read_json(built["pack_path"])
    assert built["item_count"] == 1, pack["omissions"]
    item = pack["items"][0]
    assert packs.recheck_mobile_item(store, item, now=NOW)["count"] == 47
    message = bot.message_for(item, number=1, now=NOW)
    assert "Fact: base rate through 2026-11-10" in message
    assert "47 of 93" in message and "2016-11-14 to 2026-11-10" in message
    assert not store.list_platform_dispatches()


def test_draft_cannot_change_the_condition_or_hide_the_forward_horizon(census):
    source = rates.collect([post()], now=NOW, producer=Producer(), odds_path=census)[0][0]
    for old, new, cause in [("daily gains of at least 0.5%", "daily gains", "CONDITION_NOT_STATED"),
                             ("five-session", "later", "FORWARD_HORIZON_NOT_STATED"),
                             ("higher", "lower", "FORWARD_OUTCOME_CHANGED")]:
        with pytest.raises(ValueError, match=cause):
            policy.check_fact(post(), source, now=NOW, draft={"draft_text": source["excerpt"].replace(old, new)})


def test_a_thin_producer_sample_stays_usable_and_shows_its_exact_count(census):
    producer = Producer()
    producer.mutate = lambda a: {**a, "case_count": 1, "terminal_up": {"hits": 0, "n": 1}}
    sources, gaps = rates.collect([post()], now=NOW, producer=producer, odds_path=census)
    assert not gaps and len(sources) == 2
    assert all("0 of 1" in source["excerpt"] for source in sources)
    assert all(policy.check_fact(post(), source, now=NOW)["sample_count"] == 1 for source in sources)
