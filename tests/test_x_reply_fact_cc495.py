from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3

import pytest

from live_contentops import x_reply_fact_policy_v1 as policy
from live_contentops import x_reply_fact_sources_v1 as facts
from live_contentops import x_reply_pack_v1 as packs
from live_contentops import x_reply_bot_v1 as botlane
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

NOW = datetime(2026, 11, 11, 16, tzinfo=timezone.utc)


def post(text="NASDAQ 100 RISES 2.1% TO SESSION HIGH", *, age=2):
    return {"post_text": text, "post_time_utc": (NOW-timedelta(minutes=age)).isoformat()}


def source(text, *, kind=None, markets=None, **binding):
    result = {"excerpt": text, "label": text, "known_at_utc": NOW.isoformat()}
    if kind:
        result["fact_binding"] = {"kind": kind, "markets": markets or ["NDX"], **binding}
    return result


def test_positioning_age_uses_actual_as_of_not_fresh_report_clock():
    value = source("CFTC data for 3 Nov show 129,414 S&P 500 e-mini contracts net short.")
    with pytest.raises(ValueError, match="FACT_POSITIONING_OVER_THREE_CALENDAR_DAYS"):
        policy.check_fact(post("S&P 500 CFTC POSITIONING"), value, now=NOW)
    # The rejected incident also fails independently on the other index.
    with pytest.raises(ValueError, match="FACT_MARKET_MISMATCH"):
        policy.check_fact(post(), value, now=NOW)


def test_a_report_date_in_the_fact_sentence_does_not_refresh_positioning():
    value = source("On 11 Nov 2026, CFTC data for 3 Nov show 129,414 S&P 500 futures contracts net short.")
    with pytest.raises(ValueError, match="FACT_POSITIONING_OVER_THREE_CALENDAR_DAYS"):
        policy.check_fact(post("S&P 500 CFTC positioning"), value, now=NOW)


def test_nasdaq_e_minis_are_not_classified_as_sp_futures():
    assert "SPX" not in policy.markets("CFTC Nasdaq 100 e-minis positioning")


@pytest.mark.parametrize("days,valid", [(3, True), (4, False)])
def test_positioning_three_calendar_day_boundary(days, valid):
    value = source("CFTC yen contracts: 102,321.", kind="positioning", markets=["USDJPY"],
                   as_of_date=(NOW.date()-timedelta(days=days)).isoformat())
    if valid:
        assert policy.check_fact(post("CFTC YEN POSITIONING"), value, now=NOW)["age_text"] == "3 calendar days old"
    else:
        with pytest.raises(ValueError, match="FACT_POSITIONING_OVER_THREE"):
            policy.check_fact(post("CFTC YEN POSITIONING"), value, now=NOW)


@pytest.mark.parametrize("text,cause", [
    ("YEN RISES TODAY", "FACT_POSITIONING_TARGET_NOT_POSITIONING"),
    ("CFTC YEN POSITIONING AS THE YEN RISES", "FACT_POSITIONING_CANNOT_EXPLAIN_SESSION_MOVE"),
])
def test_recent_positioning_never_explains_a_session_move(text, cause):
    value = source("CFTC data for 9 Nov show 102,321 yen contracts net long.")
    with pytest.raises(ValueError, match=cause):
        policy.check_fact(post(text), value, now=NOW)


@pytest.mark.parametrize("offset,cause", [(-61, "FACT_SESSION_NOT_CURRENT"), (-60, None), (1, None), (3, "FACT_SESSION_NOT_CURRENT")])
def test_session_observation_window_and_no_future_fact(offset, cause):
    target = post()
    observed = policy.utc(target["post_time_utc"]) + timedelta(minutes=offset)
    value = source("Nasdaq 100: 20,000 points.", kind="session", observed_at_utc=observed.isoformat())
    if cause:
        with pytest.raises(ValueError, match=cause):
            policy.check_fact(target, value, now=NOW)
    else:
        assert "today," in policy.check_fact(target, value, now=NOW)["age_text"]


def test_a_fresh_capture_cannot_turn_yesterdays_price_into_todays_fact():
    value = source("Nasdaq 100: 20,000 points.", kind="session", observed_at_utc=(NOW-timedelta(days=1)).isoformat())
    with pytest.raises(ValueError, match="FACT_SESSION_NOT_CURRENT"):
        policy.check_fact(post(), value, now=NOW)
    unclocked = source("Nasdaq 100: 20,000 points (11 Nov).")
    with pytest.raises(ValueError, match="FACT_SESSION_OBSERVATION_CLOCK_REQUIRED"):
        policy.check_fact(post(), unclocked, now=NOW)


def test_daily_fact_counts_trading_days_and_requires_its_day_in_the_sentence():
    monday = datetime(2026, 11, 9, 16, tzinfo=timezone.utc)
    target = {**post("S&P 500 SESSION"), "post_time_utc": (monday-timedelta(minutes=2)).isoformat()}
    value = source("S&P 500 close: 7,000 points on 6 Nov.", kind="daily", markets=["SPX"], as_of_date="2026-11-06")
    value["known_at_utc"] = "2026-11-06T22:00:00Z"
    assert policy.check_fact(target, value, now=monday, draft={"draft_text": value["excerpt"]})["age_text"] == "1 trading day old"
    with pytest.raises(ValueError, match="FACT_DAILY_SENTENCE_DAY_NOT_STATED"):
        policy.check_fact(target, value, now=monday, draft={"draft_text": "S&P 500 closed at 7,000 points."})
    with pytest.raises(ValueError, match="FACT_DAILY_OVER_ONE_TRADING_DAY"):
        policy.check_fact(post("S&P 500"), value, now=NOW)


def test_bond_holiday_does_not_add_a_trading_day():
    value = source("US 10-year yield 4 percent on 10 Nov.", kind="daily", markets=["US10Y"], as_of_date="2026-11-10")
    assert policy.check_fact(post("US 10-year yield"), value, now=NOW)["age_text"] == "0 trading days old"


def test_base_rate_is_a_completed_count_with_its_explicit_historical_period():
    value = source("Nasdaq 100 rose in 7 of 10 CPI days since Jan 2024.", kind="base_rate",
                   count=7, sample_count=10, period_text="CPI days since Jan 2024", through_date="2026-11-10")
    assert "historical count" in policy.check_fact(post(), value, now=NOW, draft={"draft_text": value["excerpt"]})["age_text"]
    with pytest.raises(ValueError, match="FACT_BASE_RATE_COUNT_AND_PERIOD_NOT_STATED"):
        policy.check_fact(post(), value, now=NOW, draft={"draft_text": "Nasdaq 100 rose 7 times."})
    value["fact_binding"]["through_date"] = "2026-11-11"
    with pytest.raises(ValueError, match="FACT_BASE_RATE_COUNT_PERIOD_OR_COMPLETION_INVALID"):
        policy.check_fact(post(), value, now=NOW)


def test_same_market_is_required_even_for_a_fresh_fact():
    value = source("S&P 500 futures: 7,000 USD.", kind="session", markets=["SPX"], observed_at_utc=NOW.isoformat())
    with pytest.raises(ValueError, match="FACT_MARKET_MISMATCH"):
        policy.check_fact(post(), value, now=NOW, draft={"draft_text": "S&P 500 futures at 7,000 USD support the Nasdaq 100."})


def test_a_driver_sentence_names_both_markets_and_the_relationship():
    value = source("US 10-year yield: 4 percent.", kind="session", markets=["US10Y"], observed_at_utc=NOW.isoformat())
    with pytest.raises(ValueError, match="FACT_DRIVER_LINK_NOT_STATED"):
        policy.check_fact(post(), value, now=NOW, draft={"draft_text": value["excerpt"]})
    assert policy.check_fact(post(), value, now=NOW,
        draft={"draft_text": "US 10-year yield at 4 percent raises the discount rate for Nasdaq 100 stocks."})


def test_no_fact_means_no_draft():
    with pytest.raises(ValueError, match="NO_USABLE_FACT"):
        policy.check_fact(post(), None, now=NOW)


def test_send_deadline_is_checked_at_the_actual_send_boundary():
    policy.check_send_time(post(age=15), now=NOW)
    with pytest.raises(ValueError, match="TARGET_OVER_15_MINUTES_AT_SEND"):
        policy.check_send_time(post(age=15), now=NOW+timedelta(microseconds=1))


@pytest.fixture
def consumer(tmp_path, monkeypatch):
    from live_contentops import x_reply_base_rates_v1
    monkeypatch.setattr(x_reply_base_rates_v1, "collect", lambda *a, **kw: ([], []))
    root = tmp_path / "intake"
    path = root / "completed-bars/bars.sqlite3"
    path.parent.mkdir(parents=True)
    observed = NOW-timedelta(minutes=5)
    with sqlite3.connect(path) as db:
        db.executescript("""
            CREATE TABLE history_sources(source_id TEXT PRIMARY KEY,source_sha256 TEXT,path TEXT,market TEXT,
                timeframe TEXT,series_id TEXT,known_epoch REAL,metadata_json TEXT);
            CREATE TABLE history_bars(source_id TEXT,open_epoch INTEGER,end_epoch INTEGER,session_date TEXT,
                open REAL,high REAL,low REAL,close REAL);
            CREATE TABLE history_points(source_id TEXT,open_epoch INTEGER,end_epoch INTEGER,session_date TEXT,value REAL);
            CREATE TABLE history_invalid(source_id TEXT,open_epoch INTEGER);
            CREATE TABLE bars(symbol TEXT,open_epoch INTEGER,source_sha256 TEXT,series_id TEXT,known_epoch REAL);
        """)
        db.execute("INSERT INTO history_sources VALUES(?,?,?,?,?,?,?,?)", (
            "fixture-source", "source-hash", "fixture-public-source.json", "US500", "M1", "YAHOO_FINANCE:ES=F",
            (NOW-timedelta(minutes=4)).timestamp(), json.dumps({"provider": "YAHOO_FINANCE_CHART"})))
        db.execute("INSERT INTO history_bars VALUES(?,?,?,?,?,?,?,?)", (
            "fixture-source", int(observed.timestamp())-60, int(observed.timestamp()), "2026-11-11", 7000, 7000, 7000, 7000.0))
    # The real loader and resolver read only this isolated bar store.
    original_load = facts.load
    monkeypatch.setattr(facts, "load", lambda **kw: original_load(root=root, **kw))
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3", auto_migrate=True)
    binding = tmp_path / "control/x_reply_bot_binding.json"
    packs.save_json(binding, {"bound_chat_id": 123456789, "start_nonce": None})
    feed = tmp_path / "feed.json"
    packs.save_json(feed, {"generated_at_utc": NOW.isoformat(), "rows": [{"handle": "FirstSquawk",
        "text": "S&P 500 CASH INDEX RISES", "url": "https://x.com/FirstSquawk/status/123", "tweet_id": "123",
        "posted_utc": (NOW-timedelta(minutes=2)).isoformat(), "metrics": {"replies": 2}}]})
    return store, binding, feed, tmp_path


def authored(request):
    target = request["candidates"][0]
    return {"request_sha256": request["request_sha256"], "stage_seconds": {"ranking": 1.25, "drafting": 2.5},
        "items": [{"post_id": target["post_id"], "source_id": target["usable_source_ids"][0],
            "draft_text": "S&P 500 futures traded at 7000.0 USD at 10:55 AM ET on 11 Nov (Yahoo Finance). That is a futures price.",
            "fact_text": "7000.0 USD", "source_name": "Yahoo Finance", "date_text": "11 Nov",
            "addition": "Futures price", "point": "Exact same-market observation", "reply_shape": "priced_in"}]}


def drafter(path, *, output_dir):
    result = output_dir / "response.json"
    packs.save_json(result, authored(packs.read_json(path)))
    return result


class Bot:
    private_chat = botlane.TelegramBot.private_chat

    def __init__(self):
        self.sent = []

    def call(self, method, payload=None):
        if method == "getMe":
            return {"username": botlane.BOT_NAME}
        if method == "getWebhookInfo":
            return {}
        if method == "getUpdates":
            return []
        if method == "getChat":
            return {"id": payload["chat_id"], "type": "private"}
        if method == "sendMessage":
            self.sent.append(deepcopy(payload))
            return {"message_id": 7, "date": int(NOW.timestamp())}
        pytest.fail(method)


def test_minute_consumer_reads_held_bar_checks_age_and_records_all_four_stages(consumer):
    store, binding, feed, root = consumer
    bot = Bot()
    result = botlane.refresh_due(store, binding_path=binding, feed_path=feed, output_root=root / "out",
                                 bot=bot, drafter=drafter, now=NOW)
    assert result["status"] == "DELIVERED", result
    assert "Fact age: today, 10:55 AM ET" in bot.sent[0]["text"]
    proof = result["delivery"]["delivered"][0]
    assert proof["post_to_send_attempt_minutes"] == 2
    assert proof["post_to_delivery_minutes"] == 2
    assert {"filter", "ranking", "drafting", "checks"} <= proof["stage_seconds"].keys()
    assert proof["stage_seconds"]["ranking"] == 1.25 and proof["stage_seconds"]["drafting"] == 2.5
    assert not store.list_platform_dispatches()


def test_pre_draft_filter_drops_other_index_and_does_not_call_a_model(consumer):
    store, binding, feed, root = consumer
    data = packs.read_json(feed)
    data["rows"][0]["text"] = "NASDAQ 100 RISES 2.1% TO SESSION HIGH"
    packs.save_json(feed, data)
    def no_call(*a, **kw):
        pytest.fail("No usable same-market fact: no ranking or drafting call")
    bot = Bot()
    result = botlane.refresh_due(store, binding_path=binding, feed_path=feed, output_root=root / "out",
                                 bot=bot, drafter=no_call, now=NOW)
    assert result["status"] == "NO_NEW_ELIGIBLE_TARGETS"
    dropped = result["dropped_candidates"][0]
    assert dropped["post_id"] == "123" and dropped["cause"] == "NO_USABLE_FACT"
    assert dropped["fact_refusals"]["FACT_MARKET_MISMATCH"] == 1
    assert not bot.sent


def test_old_pack_cannot_bypass_the_new_send_deadline_or_rewrite_issued_bytes(consumer):
    store, binding, feed, root = consumer
    ready = packs.prepare(store, feed_path=feed, output_root=root / "request", now=NOW, reply_policy=packs.MOBILE_POLICY)
    before = Path(ready["request_path"]).read_bytes()
    response = drafter(ready["request_path"], output_dir=root)
    built = packs.build(store, request_path=ready["request_path"], response_path=response, feed_path=feed, output_root=root, now=NOW)
    bot = Bot()
    result = botlane.deliver_pack(store, built["store_message_id"], binding_path=binding, bot=bot, now=NOW+timedelta(minutes=14))
    assert result["causes"]["TARGET_OVER_15_MINUTES_AT_SEND"] == 1
    assert not bot.sent and Path(ready["request_path"]).read_bytes() == before
    assert result["dropped_candidates"][0]["post_id"] == "123"


def test_source_row_change_is_rechecked_before_private_send(consumer):
    store, binding, feed, root = consumer
    ready = packs.prepare(store, feed_path=feed, output_root=root / "request", now=NOW, reply_policy=packs.MOBILE_POLICY)
    response = drafter(ready["request_path"], output_dir=root)
    built = packs.build(store, request_path=ready["request_path"], response_path=response, feed_path=feed, output_root=root, now=NOW)
    with sqlite3.connect(root / "intake/completed-bars/bars.sqlite3") as db:
        db.execute("UPDATE history_bars SET close=7001")
    bot = Bot()
    result = botlane.deliver_pack(store, built["store_message_id"], binding_path=binding, bot=bot, now=NOW)
    assert result["causes"]["REPLY_SOURCE_BINDING_CHANGED"] == 1 and not bot.sent


def test_an_old_unpublished_ranking_does_not_hide_new_usable_facts(consumer):
    store, binding, feed, root = consumer
    botlane.record(store, botlane.ATTEMPTS, {"post_id": "123", "at_utc": (NOW-timedelta(minutes=1)).isoformat()},
                   key="xrb-attempt-123", status="ATTEMPTED")
    bot = Bot()
    result = botlane.refresh_due(store, binding_path=binding, feed_path=feed, output_root=root / "out",
                                 bot=bot, drafter=drafter, now=NOW)
    assert result["status"] == "DELIVERED" and len(bot.sent) == 1


def test_unchanged_low_quality_target_is_not_ranked_again_but_new_facts_are_used(consumer):
    store, binding, feed, root = consumer
    calls = []
    def low_quality(path, *, output_dir):
        request = packs.read_json(path)
        calls.append(request["candidates"][0]["fact_context_sha256"])
        result = output_dir / "response.json"
        packs.save_json(result, {"request_sha256": request["request_sha256"], "items": [],
            "omissions": [{"post_id": "123", "cause": "NO_ADDED_FACT_ABOVE_QUALITY_FLOOR"}]})
        return result
    options = dict(binding_path=binding, feed_path=feed, output_root=root / "out", bot=Bot(), drafter=low_quality, now=NOW)
    botlane.refresh_due(store, **options)
    assert botlane.refresh_due(store, **options)["status"] == "NO_NEW_ELIGIBLE_TARGETS"
    with sqlite3.connect(root / "intake/completed-bars/bars.sqlite3") as db:
        db.execute("INSERT INTO history_sources SELECT 'new-source',source_sha256,path,market,timeframe,series_id,?,metadata_json "
                   "FROM history_sources WHERE source_id='fixture-source'", ((NOW-timedelta(minutes=2)).timestamp(),))
        db.execute("INSERT INTO history_bars SELECT 'new-source',open_epoch+60,end_epoch+60,session_date,open,high,low,close "
                   "FROM history_bars WHERE source_id='fixture-source'")
    botlane.refresh_due(store, **options)
    assert len(calls) == 2 and calls[0] != calls[1]


def test_ranker_gets_actual_relevant_facts_without_internal_binding_ids(consumer):
    store, _, feed, root = consumer
    ready = packs.prepare(store, feed_path=feed, output_root=root / "request", now=NOW, reply_policy=packs.MOBILE_POLICY)
    request = packs.read_json(ready["request_path"])
    request["candidates"][0].update(attempt_key="private-attempt-marker", fact_context_sha256="private-context-marker")
    request["candidates"][0]["usable_source_ids"].extend(["internal-binding-marker" * 100] * 20)
    request["request_sha256"] = packs.digest({k: v for k, v in request.items() if k != "request_sha256"})
    packs.save_json(ready["request_path"], request)
    sizes = []
    def rank(prompt, **kwargs):
        sizes.append(len(prompt))
        assert "7000.0 USD" in prompt and "today, 10:55 AM ET" in prompt
        assert "reply_count" in prompt and "internal-binding-marker" not in prompt
        assert "private-attempt-marker" not in prompt and "private-context-marker" not in prompt
        assert request["sources"][0]["source_id"] not in prompt
        return {"ranking": [{"post_id": "123", "quality_score": 92}]}, {}
    def write(prompt, **kwargs):
        assert request["sources"][0]["source_id"] in prompt
        return authored(request), {}
    response = botlane.rank_and_draft(ready["request_path"], output_dir=root / "editorial", ranker=rank, writer=write, now=NOW)
    assert sizes[0] < 3000 and packs.read_json(response)["items"]


def test_bounded_rank_timeout_is_recorded_without_changing_model_roles(tmp_path):
    import subprocess
    def slow(args, **kwargs):
        assert kwargs["timeout"] == 90 and "90s" in args
        raise subprocess.TimeoutExpired(args, 90, output=b"partial rank result")
    with pytest.raises(ValueError, match="AGY_RANK_TIMEOUT_90S"):
        botlane._text_call("No tools. Rank only.", root=tmp_path, runner=slow)
    call = packs.read_json(tmp_path / "call.json")
    assert call["status"] == "TIMEOUT" and call["configuration_status"] == "CONFIGURED_NOT_OBSERVED"
    assert call["configured_model"] != botlane.WRITER_MODEL


def test_media_time_cannot_push_a_draft_past_fifteen_minutes(consumer, monkeypatch):
    from hashlib import sha256
    from PIL import Image
    store, binding, feed, root = consumer
    ready = packs.prepare(store, feed_path=feed, output_root=root / "request", now=NOW, reply_policy=packs.MOBILE_POLICY)
    response = drafter(ready["request_path"], output_dir=root)
    built = packs.build(store, request_path=ready["request_path"], response_path=response, feed_path=feed, output_root=root, now=NOW)
    value = json.loads(store.get_outbox_message(built["store_message_id"])["payload"])
    image = root / "test-chart.png"
    Image.new("RGB", (40, 40), "white").save(image)
    value["items"][0]["image"] = {"path": str(image), "sha256": sha256(image.read_bytes()).hexdigest(),
                                  "kind": "chart", "rights_class": "CC_OWN_ANALYSIS"}
    key = "isolated-media-delay-pack"
    store.create_work_item(work_item_id=key, story_id=key, title=key, target_surface="PRIVATE")
    store.register_outbox_message(message_id=key, work_item_id=key, destination=packs.PACK_DESTINATION, payload=json.dumps(value))
    current = [NOW]
    monkeypatch.setattr(packs, "utcnow", lambda: current[0])
    class SlowPhoto(Bot):
        def send_photo(self, chat_id, path):
            current[0] += timedelta(minutes=14)
            return {"message_id": 9}
    bot = SlowPhoto()
    result = botlane.deliver_pack(store, key, binding_path=binding, bot=bot)
    assert result["causes"]["TARGET_OVER_15_MINUTES_AT_SEND"] == 1 and not bot.sent
    assert store.get_outbox_message("xrb-123")["status"] == "REFUSED_BEFORE_TEXT_SEND"


def test_official_rate_rows_keep_the_data_day_and_exact_source_value(consumer):
    _, _, _, root = consumer
    path = root / "intake/rates-implied/observations.sqlite3"
    path.parent.mkdir(parents=True)
    payload = {"store_available_at_utc": NOW.isoformat(), "record": {"alias": "US10Y", "value": 4.125,
        "unit": "percent", "reference_period": "2026-11-10", "official_url": "https://home.treasury.gov/data",
        "rights": {"attribution": "US Treasury", "public_or_model_use": "NOT_GRANTED"}}}
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE observations(family TEXT,series TEXT,observation_date TEXT,known_at TEXT,version TEXT,payload TEXT)")
        db.execute("INSERT INTO observations VALUES(?,?,?,?,?,?)", ("direct_rates", "US10Y", "2026-11-10",
            NOW.isoformat(), "rate-version", json.dumps(payload)))
    sources, gaps = facts.load(now=NOW)
    selected = next(s for s in sources if s.get("artifact_binding", {}).get("kind") == "rate_row")
    assert "4.125 percent" in selected["excerpt"] and "10 Nov 2026" in selected["excerpt"]
    assert selected["fact_binding"]["kind"] == "daily"
    assert selected["fact_binding"]["as_of_date"] == "2026-11-10"
    assert facts.resolve(selected) == selected
    assert any(g["cause"] == "SAME_SESSION_PRICED_IN_PATH_NOT_HELD" for g in gaps)


def test_reaction_counts_never_pool_series_windows_or_future_events(tmp_path):
    path = tmp_path / "publisher.json"
    def event(day, series, value):
        return {"release_utc": day + "T13:30:00Z", "markets": [{"symbol": "US500", "series_id": series,
            "price_basis": "BID", "windows": {"5m": {"move_pct": value, "missing_reason": None}}}]}
    def summary(series, count, dates):
        return {"symbol": "US500", "series_id": series, "price_basis": "BID", "window": "5m",
                "positive_n": count, "n": len(dates), "release_dates": dates,
                "measure": "CPI_CORE_MOM", "bucket": "HOT", "consensus_source": "held producer consensus"}
    packs.save_json(path, {"as_of_utc": NOW.isoformat(), "events": [
        event("2026-09-10", "HISTDATA:SPXUSD", 1), event("2026-10-10", "HISTDATA:SPXUSD", -1),
        event("2026-10-10", "DUKASCOPY:USA500.IDX/USD", 2), event("2026-11-12", "HISTDATA:SPXUSD", 2)],
        "summary": [summary("HISTDATA:SPXUSD", 1, ["2026-09-10", "2026-10-10"]),
                    summary("DUKASCOPY:USA500.IDX/USD", 1, ["2026-10-10"]),
                    summary("HISTDATA:SPXUSD", 3, ["2026-09-10", "2026-10-10", "2026-11-12"])]})
    sources = facts._reaction_sources(path, through_date="2026-11-10")
    hist = next(s for s in sources if s["fact_binding"]["series_id"].startswith("HISTDATA:"))
    assert len(sources) == 2 and hist["fact_binding"]["sample_count"] == 2 and hist["fact_binding"]["count"] == 1
    assert "1 of 2 retained hot core CPI days, Sep 2026 to 10 Oct 2026" in hist["excerpt"]
    assert facts.resolve(hist) == hist
    checked = policy.check_fact(post("S&P 500 ON CPI"), hist, now=NOW, draft={"draft_text": hist["excerpt"]})
    assert checked["age_text"] == "historical count; last observation 10 Oct 2026"
    with pytest.raises(ValueError, match="FACT_BASE_RATE_CONDITION_NOT_STATED"):
        policy.check_fact(post("S&P 500 ON CPI"), hist, now=NOW, draft={"draft_text": hist["excerpt"].replace("hot core CPI", "CPI")})
    with pytest.raises(ValueError, match="FACT_BASE_RATE_REACTION_WINDOW_NOT_STATED"):
        policy.check_fact(post("S&P 500 ON CPI"), hist, now=NOW, draft={"draft_text": hist["excerpt"].replace("5 minutes", "the release")})
