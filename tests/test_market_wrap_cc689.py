from datetime import date, timedelta
from hashlib import sha256
import json
from pathlib import Path
from subprocess import TimeoutExpired, check_output

import pytest

from live_contentops import market_wrap_sources_v1 as sources
from live_contentops import market_wrap_editorial_v1 as editorial
from live_contentops import market_wrap_job_v1 as job
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.publication_coordinator_v1 import (
    CanonicalDestinationTransportRuntimeV1, DurablePublicationCoordinator,
)


def at(value):
    return sources.utc(value)


@pytest.fixture
def cash():
    return {"years": {
        "2026": {"closed": ["2026-11-26"], "early_close_13_et": ["2026-11-27"]},
        "2027": {"closed": [], "early_close_13_et": []},
    }}


def test_due_windows_follow_the_cash_open_and_close_calendar(cash):
    assert sources.slot_at(at("2026-11-20T13:00Z"), cash) is None
    assert sources.slot_at(at("2026-11-26T13:00Z"), cash) is None
    assert sources.slot_at(at("2026-11-28T13:00Z"), cash) is None
    monday = sources.slot_at(at("2026-11-23T13:00Z"), cash)
    assert monday["start_utc"] == "2026-11-23T13:00:00+00:00"
    assert monday["deadline_utc"] == "2026-11-23T13:45:00+00:00"
    friday = sources.slot_at(at("2026-11-27T13:00Z"), cash)
    assert friday["id"] == "cc689-daily-2026-11-27"
    first_sunday = sources.slot_at(at("2026-11-22T12:00Z"), cash)
    assert first_sunday["start_utc"] == "2026-11-22T12:00:00+00:00"
    assert first_sunday["deadline_utc"] == "2026-11-22T18:00:00+00:00"
    sunday = sources.slot_at(at("2026-11-29T15:00Z"), cash)
    assert sunday["start_utc"] == "2026-11-29T15:00:00+00:00"
    assert sunday["deadline_utc"] == "2026-11-29T18:00:00+00:00"
    summer = sources.slot_at(at("2027-07-19T12:00Z"), cash)
    assert summer["deadline_utc"] == "2027-07-19T12:45:00+00:00"


def event(key="US_GDP_20261125", **overrides):
    return {"event_id": key, "title": "Gross Domestic Product", "source_url": "https://www.bea.gov/news",
            "source_timezone": "America/New_York", "scheduled_date": "2026-11-25",
            "scheduled_at_utc": "2026-11-25T13:30:00Z", "retrieved_at_utc": "2026-11-23T00:00Z",
            "public_use_allowed": True, "schedule_status": "PUBLISHER_SCHEDULE_SUBJECT_TO_REVISION",
            **overrides}


def test_calendar_binds_the_exact_et_row_and_keeps_date_only_precision():
    point = at("2026-11-24T14:00Z")
    doc = {"public_use_allowed": True, "built_at_utc": "2026-11-23T00:00Z",
           "events": [event(), event("DATE_ONLY", title="Publication date", scheduled_at_utc=None),
                      event("PRIVATE_EVENT", public_use_allowed=False),
                      event("FUTURE_REVISION", retrieved_at_utc="2026-11-25T00:00Z"),
                      event("INVALID_CLOCK", scheduled_date="2026-11-24")]}
    rows = sources.calendar_events(json.dumps(doc).encode(), point, point + timedelta(days=1), as_of=point)
    assert [(row["id"], row["time"]) for row in rows] == [
        ("DATE_ONLY", "Wed 25 Nov (date only)"), ("US_GDP_20261125", "Wed 25 Nov, 8:30 AM ET")]
    assert rows[-1]["row_sha256"] == sha256_of(event())


def test_latest_main_checks_receipt_and_only_uses_visible_analysis(tmp_path):
    old = tmp_path / "requests" / "complete"
    latest = tmp_path / "requests" / "latest"
    empty = {"native_synthesis": {"summary": [{"text": "Rates fell before the open."}],
             "candidates": [{"candidate_id": "cand_macro_gold", "rationale": "Gold followed yields lower.",
                             "execution_price": 8300}]},
             "primary_analysis": {"claims": [{"candidate_ids": ["cand_macro_gold"], "claim": "Options skew fell."}]}}
    for folder, stamp, digest in ((old, "2026-11-23T12:40Z", sha256_of(empty)),
                                  (latest, "2026-11-23T12:55Z", "wrong")):
        folder.mkdir(parents=True)
        (folder / "analysis-native.json").write_text(json.dumps(empty))
        (folder / "capture.json").write_text(json.dumps({"known_at_utc": stamp}))
        (folder / "analysis-end.json").write_text(json.dumps({"completed_at_utc": stamp, "output_sha256": digest}))
    result = sources.latest_main(at("2026-11-23T13:00Z"), tmp_path)
    assert result["run_id"] == "complete"
    assert result["layers"]["XAUUSD"]["Options"] == "Options skew fell."
    assert "8300" not in json.dumps(result)
    assert result["sha256"] == sha256((old / "analysis-native.json").read_bytes()).hexdigest()


def test_plan_projection_keeps_waiting_and_unknown_status_and_excludes_closed():
    now = at("2026-11-23T13:00Z")
    common = {"asset_id": "EURUSD", "registered_at_utc": "2026-11-23T12:00Z",
              "entry_deadline_utc": "2026-11-23T16:00Z", "horizon_lane": "SHORT"}
    rows = [{**common, "plan_id": key, "status": status}
            for key, status in (("a", "WAITING"), ("b", None), ("c", "CLOSED"), ("d", "FILLED"))]
    result = sources.project_plans({"status": {"generated_at_utc": now.isoformat(),
                                    "content_hash": "source", "plans": rows}}, now)
    assert {r["id"] for r in result["rows"]} == {"a", "b", "d"}
    assert "Status unavailable" in result["rows"][1]["text"]
    assert "7:00 AM ET" in result["rows"][1]["text"]


def test_normal_day_is_measured_on_its_own_instrument():
    first = date(2026, 11, 1)
    bars = {first + timedelta(days=i): (104 + i, 100 + i, 102 + i) for i in range(15)}
    assert sources.normal_day(bars, first + timedelta(days=14)) == 4
    start, end = {"symbol": "GC=F", "value": 100}, {"symbol": "GC=F", "value": 90}
    assert sources.move("XAUUSD", end, start, basis="since the last wrap", normal_day=4)["normal_days"] == -2.5
    with pytest.raises(ValueError, match="INSTRUMENT_MISMATCH"):
        sources.move("XAUUSD", {**end, "symbol": "XAU="}, start, basis="since the last wrap")


def test_daily_pack_uses_retained_moves_and_separate_source_clocks(tmp_path, cash):
    start = at("2026-11-23T13:00Z")
    observed, captured = start + timedelta(minutes=1), start + timedelta(minutes=3)
    calendar = tmp_path / "calendar.json"
    release = event(scheduled_date="2026-11-24", scheduled_at_utc="2026-11-24T13:01Z",
                    retrieved_at_utc=captured.isoformat())
    calendar.write_text(json.dumps({"public_use_allowed": True, "built_at_utc": captured.isoformat(),
                                   "events": [release]}))
    calls = []

    def quote(key, *, max_age_seconds, fetch=True):
        calls.append((key, fetch, max_age_seconds))
        if key == "USOIL" and not fetch:
            raise ValueError("PUBLIC_QUOTE_NOT_CACHED")
        return {"source_symbol": sources.quotes.SYMBOLS[key][1], "value": 102, "prior_close": 99,
                "observed_at_utc": observed.isoformat(), "known_at_utc": observed.isoformat(),
                "source": "Yahoo Finance", "source_url": "https://example.test/quote", "observation_sha256": "quote"}

    def history(market, days, *, as_of):
        assert as_of == start
        return {days[0]: (103, 97, 98)}, {"sha256": market}

    def plans():
        raise TimeoutExpired("plan export reader", 120)

    def main(cutoff):
        assert cutoff == captured
        return {"layers": {}, "outlooks": {}}

    previous = {"slot": {"id": "prior-wrap"}, "snapshots": {
        "US500": {"symbol": "ES=F", "value": 100, "date": "2026-11-20"}}}
    pack = sources.collect(sources.slot_at(start, cash), now=start, cash_calendar=cash, previous=previous,
                           quote=quote, history=history, plans=plans, main=main, calendar=calendar,
                           releases=lambda *_: [], clock=lambda: captured, trend_board=None)
    assert set(pack["markets"]) == set(sources.MARKETS)
    assert pack["markets"]["US500"]["basis"] == "since the last wrap"
    assert pack["markets"]["US500"]["change_pct"] == 2
    assert pack["markets"]["XAUUSD"]["basis"] == "since the last session's close"
    assert [row for row in calls if row[1]] == [("USOIL", True, 3600)]
    assert pack["data_cutoff_utc"] == observed.isoformat()
    assert pack["source_pack_as_of_utc"] == captured.isoformat()
    assert pack["events"][0]["time"] == "Tue 24 Nov, 8:01 AM ET"
    assert pack["gaps"] == {"plans": "PLAN_EXPORT_READER_TIMEOUT"}


def test_sunday_pack_keeps_dated_closes_and_calendar_windows(tmp_path, cash):
    sunday = at("2026-11-29T15:00Z")
    stamp = sunday.isoformat()
    calendar = tmp_path / "calendar.json"
    rows = [event("SUNDAY_DATE_ONLY", scheduled_date="2026-11-29", scheduled_at_utc=None),
            event("FRIDAY_AFTER_CLOSE", scheduled_date="2026-11-27", scheduled_at_utc="2026-11-27T18:05Z"),
            event("MONDAY_RELEASE", scheduled_date="2026-11-30", scheduled_at_utc="2026-11-30T14:00Z")]
    calendar.write_text(json.dumps({"public_use_allowed": True, "built_at_utc": stamp, "events": rows}))

    def history(_market, days, *, as_of):
        assert as_of == sunday
        assert days == [date(2026, 11, 20), date(2026, 11, 27)]
        return {days[0]: (103, 97, 100), days[1]: (108, 102, 104)}, {"sha256": "closes"}

    def no_sunday_quote(*args, **kwargs):
        pytest.fail("Sunday comparisons must use the completed sessions")

    pack = sources.collect(sources.slot_at(sunday, cash), now=sunday, cash_calendar=cash,
                           quote=no_sunday_quote, history=history, calendar=calendar, clock=lambda: sunday,
                           plans=lambda: {"status": {"generated_at_utc": stamp, "plans": [], "content_hash": "plans",
                                                    "scored_call_count": 0}, "transitions": {"transitions": []}},
                           main=lambda _: {"layers": {}, "outlooks": {}}, releases=lambda *_: [])
    assert pack["data_cutoff_utc"] is None
    assert pack["market_close_date"] == "2026-11-27"
    assert pack["last_cash_close_utc"] == "2026-11-27T18:00:00+00:00"
    assert pack["snapshots"]["BTCUSD"]["date"] == "2026-11-27"
    assert [row["id"] for row in pack["weekend_events"]] == ["FRIDAY_AFTER_CLOSE"]
    assert [row["id"] for row in pack["events"]] == ["SUNDAY_DATE_ONLY", "MONDAY_RELEASE"]
    assert pack["gaps"] == {}
    article, markets = editorial.article_for(pack, editorial.draft(pack, tmp_path, call=select_first))
    assert "sessions dated November 27, 2026" in article["substack_body_markdown"]
    assert article["market_asset"] == "US500"
    assert "Scored calls: 0. Hits: 0. Stops: 0." in article["substack_body_markdown"]
    assert all(market["change_pct"] == 4 for market in markets.values())


@pytest.fixture
def pack(cash):
    now = at("2026-11-23T13:00Z")
    first = {"symbol": "GC=F", "value": 100, "date": "2026-11-20"}
    quote = {"symbol": "GC=F", "value": 99, "observed_at_utc": now.isoformat()}
    return {
        "slot": sources.slot_at(now, cash),
        "markets": {"XAUUSD": sources.move("XAUUSD", quote, first, basis="since the last wrap", normal_day=4)},
        "analysis": {"at_utc": "2026-11-23T12:00Z", "layers": {
            "XAUUSD": {"Macro and catalysts": "Higher yields weighed on gold.", "Options": "Skew rose."}},
            "outlooks": {}},
        "data_cutoff_utc": now.isoformat(), "snapshots": {"XAUUSD": quote},
        "events": [{"id": "US_GDP_20261123", "name": "Gross Domestic Product", "time": "Mon 23 Nov, 8:30 AM ET",
                    "qualifier": "", "source_url": "https://www.bea.gov/news"}],
        "weekend_events": [], "plans": {"rows": [{"id": "plan_1", "text": "Gold, Waiting for entry."}]},
        "gaps": {"quote:US500": "unavailable"}, "weekly_calls": None,
    }


def select_first(prompt, **kwargs):
    options = json.loads(prompt.split("\n", 1)[1])
    result = {section: [{"id": key, "text": lines[0]} for key, lines in rows.items()]
              for section, rows in options.items()}
    return json.dumps(result).encode(), {"answered_by": kwargs["callers"][0]}


@pytest.mark.parametrize("weekly", [False, True], ids=["pre-us", "sunday"])
def test_decision_98_wrap_renderer_keeps_reader_shape(pack, cash, weekly):
    if weekly:
        close = {"symbol": "GC=F", "value": 99, "date": "2026-11-20"}
        prior = {"symbol": "GC=F", "value": 100, "date": "2026-11-13"}
        move = sources.move("XAUUSD", close, prior, basis="since the prior Friday close", normal_day=4)
        pack.update(
            slot=sources.slot_at(at("2026-11-22T12:00Z"), cash),
            market_close_date=close["date"],
            markets={"XAUUSD": move},
            snapshots={"XAUUSD": close},
            data_cutoff_utc=None,
        )
        pack["analysis"]["at_utc"] = "2026-11-20T21:00Z"
        pack["analysis"]["outlooks"]["XAUUSD"] = "Watch whether gold holds its Friday move."
    pack["plans"]["scenario"] = {
        "market": "XAUUSD",
        "registered_at_utc": "2026-11-20T20:30Z",
        "cases": [
            {"name": "Base", "probability": 60, "text": "Gold stabilizes.", "checks": {}},
            {"name": "Alternative", "probability": None, "text": "Gold falls further.", "checks": {}},
        ],
    }
    sections = {
        section: [{"id": key, "text": lines[0]} for key, lines in rows.items()]
        for section, rows in editorial.source_choices(pack).items()
    }
    article, _ = editorial.article_for(pack, {"sections": sections})
    body = article["substack_body_markdown"]
    table = [line for line in body.splitlines() if line.startswith("| ")][2:]
    markets = [line.split("|")[1].strip().partition(" (")[0] for line in table]
    assert len(markets) == 7  # CC-788: the Nasdaq 100 is the seventh core market
    assert set(markets) == {
        "EUR/USD spot", "USD/JPY spot", "COMEX gold futures",
        "WTI crude oil futures", "S&P 500 E-mini futures", "Bitcoin spot", "Nasdaq 100 E-mini futures",
    }
    headings = [line for line in body.splitlines() if line.startswith("## ")]
    assert "## What changed since the last wrap" in headings
    assert "## Scenarios" in headings
    assert "## Open plans" in headings
    if weekly:
        assert "The comparison ends with the sessions dated November 20, 2026." in body
        assert "since the prior Friday close" in body
        assert "Watch whether gold holds its Friday move." in body
        assert "## What to watch at the open" in headings
        assert "## Coming week's events" in headings
    else:
        assert "since the last wrap" in body
        assert "## Next 24 hours" in headings


def test_edition_writer_binds_moves_and_events_to_exact_rows(tmp_path, pack):
    def wrong(prompt, **kwargs):
        answer, record = select_first(prompt, **kwargs)
        if kwargs["callers"] == ("codex",):
            return answer, record
        value = json.loads(answer)
        value["changes"][0]["text"] = value["changes"][0]["text"].replace("-1.00%", "+1.00%")
        value["events"][0]["text"] = value["events"][0]["text"].replace("8:30", "9:30")
        return json.dumps(value).encode(), record

    manuscript = editorial.draft(pack, tmp_path, call=wrong)
    article, markets = editorial.article_for(pack, manuscript)
    assert not markets
    assert "9:30" not in article["substack_body_markdown"]
    assert "+1.00%" not in article["substack_body_markdown"]
    assert "Gold, Waiting for entry." in article["substack_body_markdown"]
    assert json.loads((tmp_path / "wrap-changes/light-call.json").read_bytes())["result"] == "FAIL"


@pytest.mark.parametrize("edition", ["daily", "weekly"])
def test_cc755_market_wrap_renders_main_cases_in_the_article_and_social_copy(tmp_path, pack, edition):
    now = at(pack["data_cutoff_utc"])
    pack["slot"]["edition"] = edition
    raw = {"plan_id": "source-plan", "asset_id": "XAUUSD", "direction": "BEARISH",
           "registered_at_utc": "2026-11-23T12:00Z", "status": "WAITING", "scenario_analysis": {
               "base_case": {"market_move": "Gold falls as real yields rise.", "probability_pct": 57},
               "main_alternative": {"market_move": "Gold rebounds if real yields fall.",
                                    "invalidation": "The rebound fails if real yields rise again."},
           }}
    pack["plans"] = sources.project_plans({"status": {
        "generated_at_utc": now.isoformat(), "content_hash": "main-export", "plans": [raw]}}, now)

    def select(prompt, **kwargs):
        assert "Base case and its stated chance" in prompt
        return select_first(prompt, **kwargs)

    article, _ = editorial.article_for(pack, editorial.draft(pack, tmp_path, call=select))
    body = article["substack_body_markdown"]
    assert body.startswith("## Scenarios\n")
    assert body.index("Base case (57%)") < body.index("What changed since the last wrap")
    assert "Bull case: Gold rebounds if real yields fall." in body
    assert "What would undo the bull case: The rebound fails if real yields rise again." in body
    assert "43%" not in body
    link = "https://capitalchronicle.substack.com/p/wrap"
    for route in ("x", "telegram"):
        copy = editorial.derivative_payload(article, [], link, route)
        assert "Base case (57%)" in copy["text"] and "Bull case" in copy["full_text"]
        assert link in copy["full_text"]


def test_codex_capacity_returns_desk_sections_to_antigravity(tmp_path, pack):
    callers = []

    def call(prompt, **kwargs):
        callers.extend(kwargs["callers"])
        if kwargs["callers"] == ("codex",):
            assert kwargs["codex_effort"] == "max"
            assert kwargs["timeout_seconds"] == 240
            assert kwargs["job"] == "market_wrap_desk"
            return b"", {"cause": "CODEX_QUOTA"}
        return select_first(prompt, **kwargs)

    manuscript = editorial.draft(pack, tmp_path, call=call)
    article, markets = editorial.article_for(pack, manuscript)
    assert callers == ["antigravity", "codex", "antigravity"]
    assert "Gross Domestic Product" in article["substack_body_markdown"]
    assert "Higher yields weighed on gold." in article["substack_body_markdown"]
    hit = article["substack_body_markdown"].count("Higher yields weighed on gold.")
    assert hit == 1
    asset = editorial.chart_for(pack, markets, tmp_path)
    assert (asset["width"], asset["height"]) == (1080, 1350)
    assert "Gold -0.25" in asset["alt_text"]
    link = "https://capitalchronicle.substack.com/p/pre-us-wrap"
    for route in ("x", "substack_notes", "instagram_business", "linkedin_company", "discord"):
        payload = editorial.derivative_payload(article, asset, link, route)
        assert link in payload["full_text"]
        assert payload["media_asset_ids"] == [asset["asset_id"]]


class LocalTransport(CanonicalDestinationTransportRuntimeV1):
    """Use the real canonical-link compiler; no external transport is called."""

    def __init__(self):
        super().__init__()
        self.writes = []
        self.reads = []

    def prepare_delivery_media(self, **_):
        return {"status": "CLOUDINARY_DELIVERY_MEDIA_READY"}

    def publish(self, *, destination, intent, authorization_context):
        self.writes.append((destination, intent))
        url = ("https://capitalchronicle.substack.com/p/pre-us-wrap-20261123" if destination == "substack"
               else None if destination == "discord" else f"https://example.test/{destination}/1")
        object_id = "12345" if destination == "discord" else f"{destination}-object-1"
        return {"status": "SUCCESS", "id": object_id, "public_url": url}

    def readback(self, *, destination, public_object_id, public_object_url, intent):
        self.reads.append(destination)
        return {"status": "SUCCESS", "verified": True, "public_object_id": public_object_id,
                "public_object_url": public_object_url,
                "published_at_utc": "2026-11-23T13:09:00Z"}


def test_wrap_can_read_back_its_observed_canonical_without_another_write(tmp_path, pack):
    from live_contentops.publication_coordinator_v1 import RECONCILED_CONFIRMED, RECONCILED_ABSENT_SAFE_TO_RETRY

    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    transport = LocalTransport()
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=transport)
    packet = job.stage(store, pack, editorial.draft(pack, tmp_path, call=select_first), tmp_path,
                       media=lambda pack, article, markets, folder: (
                           article, [editorial.chart_for(pack, markets, folder)]))
    identity, plan = packet["identity"], packet["plan"]
    coordinator.register_plan(identity, plan)
    ids = coordinator._ids(identity, plan["plan_hash"], "substack")
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
                                     platform="substack", status=RECONCILED_ABSENT_SAFE_TO_RETRY)
    canonical = "https://capitalchronicle.substack.com/p/wrap"
    with pytest.raises(ValueError, match="EXACT_WRAP_PUBLIC_OBJECT_REQUIRED"):
        coordinator.readback_existing_dispatch(ids["dispatch_id"], observed_wrap_root=("123", "https://example.test/draft"))
    result = coordinator.readback_existing_dispatch(ids["dispatch_id"], observed_wrap_root=("123", canonical))
    assert result["reconciliation_status"] == RECONCILED_CONFIRMED
    assert coordinator._confirmed_canonical_url_for_work_item(identity, plan_hash=plan["plan_hash"]) == canonical
    assert transport.reads == ["substack"]
    assert transport.writes == []


def test_weekly_wrap_binds_the_closed_cash_chart_to_both_linkedin_requests(tmp_path, pack, cash, monkeypatch):
    from live_contentops import tradingview_snapshot_v1 as tv
    from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
    from live_contentops.publication_image_contract_v1 import comparison_clock

    sunday = at("2026-11-22T12:00Z")
    friday_close = at("2026-11-20T21:00Z")
    weekly = {**pack, "slot": sources.slot_at(sunday, cash), "market_close_date": "2026-11-20",
              "last_cash_close_utc": friday_close.isoformat(), "data_cutoff_utc": None,
              "markets": {}, "snapshots": {}, "analysis": {**pack["analysis"], "at_utc": friday_close.isoformat()}}

    def prepare_chart(article, assets, *, output_dir):
        market = article["market_asset"]
        assert not assets
        assert tv.SYMBOLS[market] == "SP:SPX"
        assert comparison_clock(market, sunday) == (friday_close, True)
        chart = editorial.chart_for(weekly, {}, output_dir)
        return article, [{**chart, "modality": "tradingview_chart_snapshot"}]

    monkeypatch.setattr(tv, "prepare_contract_article", prepare_chart)
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    article_dir = tmp_path / "weekly"
    packet = job.stage(store, weekly, editorial.draft(weekly, article_dir, call=select_first), article_dir)
    plan = packet["plan"]
    runtime = CanonicalDestinationTransportRuntimeV1()
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=runtime, clock=lambda: sunday)
    coordinator.register_plan(packet["identity"], plan)
    canonical = "https://capitalchronicle.substack.com/p/weekend-wrap-20261122"
    handoff = NeoDestinationHandoff(store=store)
    for destination in ("linkedin", "linkedin_company"):
        ids = coordinator._ids(packet["identity"], plan["plan_hash"], destination)
        queued = json.loads(store.get_outbox_message(ids["message_id"])["payload"])
        intent = runtime.finalize_intent(destination=destination, intent=queued, canonical_url=canonical)
        assert intent["cc684_linkedin"]
        request = handoff.request(destination=destination, action="PUBLISH", intent=intent, authorization_context={
            "schema_version": "contentops.canonical_machine_authorization.v1", "operating_mode": "AUTONOMOUS_DEFAULT",
            "destination": destination, "work_item_id": packet["identity"], "dispatch_attempt_identity": ids["dispatch_id"],
            "payload_hash": intent["destination_plan"]["payload_hash"],
        })
        assert request["canonical_url"] in request["native_payload"]["text"]
        chart, = request["content_binding"]["media_manifest"]
        assert chart["sha256"] == packet["media_assets"][0]["sha256"]
        assert Path(chart["path"]).is_relative_to(article_dir / "media")


@pytest.mark.parametrize("unavailable", [None, "x", "substack_notes"])
def test_normal_job_publishes_via_real_coordinator_and_reuses_retained_bytes(
        tmp_path, pack, cash, monkeypatch, unavailable):
    from live_contentops import llm_operator_control_v1 as controls
    from live_contentops.neo_destination_handoff_v1 import _payload_binding

    monkeypatch.setattr(controls, "llm_operator_pause_active", lambda *args, **kwargs: False)
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    transport = LocalTransport()
    now = at("2026-11-23T13:10Z")

    def readiness(destination):
        return {"readiness_state": "SESSION_UNAVAILABLE" if destination == unavailable
                else "READY_NON_BROWSER_BINDING"}

    def factory(store, plan, **kwargs):
        coordinator = DurablePublicationCoordinator(store=store, transport_runtime=transport,
            readiness_provider=readiness,
            clock=lambda: now, published_content_path=tmp_path / "published.jsonl")
        coordinator.recovery_scope = {"work_item_id": plan["market_wrap"], "plan": plan, "exact_work_item_only": True}
        coordinator.allow_prior_confirmed_distribution = True
        return coordinator

    def publish(store, packet, *, clock):
        return job.continue_wrap(store, packet, clock=clock, factory=factory)

    def write(pack, root):
        return editorial.draft(pack, root, call=select_first)

    def media(pack, article, markets, folder):
        # Production daily editions use the existing TradingView capture. The
        # isolated transport fixture exercises the real weekly chart bytes.
        return {k: v for k, v in article.items() if k != "market_asset"}, [editorial.chart_for(pack, markets, folder)]

    rollout = {"editorial_output_root": str(tmp_path)}
    out = job.run_due(store, rollout=rollout, now=now, clock=lambda: now, cash_calendar=cash,
        gather=lambda *_a, **_kw: pack, writer=write, publish=publish, media=media)
    publication = out["publication"]
    assert publication["canonical_url"] == "https://capitalchronicle.substack.com/p/pre-us-wrap-20261123", publication
    assert transport.writes[0][0] == "substack"
    assert {destination for destination, _ in transport.writes} == set(job.WRAP_DESTINATIONS) - {unavailable}
    assert set(transport.reads) == set(job.WRAP_DESTINATIONS) - {unavailable}
    canonical = transport.writes[0][1]
    canonical_payload, canonical_binding = _payload_binding(canonical, "substack")
    assert canonical["destination_plan"]["substack_delivery_mode"] == "WEB_ONLY"
    assert "| Market | Move | Normal days | Comparison |" in canonical_payload["body_markdown"]
    assert len(canonical_binding["media_manifest"]) == 1
    for destination, intent in transport.writes[1:]:
        assert publication["canonical_url"] in intent["native_payload"]["full_text"]
        payload, binding = _payload_binding(intent, destination)
        assert publication["canonical_url"] in payload["full_text"]
        assert [a["asset_id"] for a in binding["media_manifest"]] == payload["media_asset_ids"]
        assert len(binding["media_manifest"]) == 1
    assert publication["unconfirmed_wrap_destinations"] == ({unavailable: "SESSION_UNAVAILABLE"}
                                                            if unavailable else {})
    record, = (tmp_path / "published.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(record)["title"].startswith("Pre-US Market Wrap")
    retained = (job.output_path(rollout, pack["slot"]) / "article_manifest_v1.json").read_bytes()
    def unexpected(*args, **kwargs):
        pytest.fail("Re-entry must not recollect or rewrite a staged edition")
    repeated = job.run_due(store, rollout=rollout, now=now, clock=lambda: now, cash_calendar=cash,
        gather=unexpected, writer=unexpected, publish=publish)
    assert repeated["plan_hash"] == out["plan_hash"]
    assert len(transport.writes) == len(job.WRAP_DESTINATIONS) - bool(unavailable)
    assert (job.output_path(rollout, pack["slot"]) / "article_manifest_v1.json").read_bytes() == retained

    after_cutoff = at("2026-11-23T13:45Z")
    resumed = job.run_due(store, rollout={}, now=after_cutoff, clock=lambda: after_cutoff,
        resume=out["identity"], gather=unexpected, writer=unexpected, publish=publish)
    assert resumed["plan_hash"] == out["plan_hash"]
    assert resumed["publication"]["deadline_elapsed"] is True
    assert set(resumed["publication"]["unconfirmed_wrap_destinations"]) == ({unavailable} if unavailable else set())
    assert len(transport.writes) == len(job.WRAP_DESTINATIONS) - bool(unavailable)
    assert job.read_json(job.output_path(rollout, pack["slot"]) / "wrap-result.json") == resumed


def test_daily_wrap_delivers_held_market_map_chart_first(tmp_path, pack, cash, monkeypatch):
    from live_contentops import image_quality_v1 as quality, tradingview_snapshot_v1 as tv
    from live_contentops.image_template_inputs_v1 import ORDER
    from live_contentops.neo_destination_handoff_v1 import _payload_binding
    from test_image_templates_cc465 import capture, yes_review

    now = at("2026-11-23T13:10Z")
    friday_close = at("2026-11-20T21:00Z")
    board_path = tmp_path / "desk-board.json"
    board = {"schema": "CapitalChronicleDeskBoardPublicV1", "as_of_utc": "2026-11-21T18:00:00Z",
             "markets": {market: {"yardstick": {"state": "AVAILABLE",
                         "yardstick": "MIXED" if market == "USDJPY" else "DOWN",
                         "last_completed_bar_utc": "2026-11-20T00:00:00Z" if market == "USDJPY"
                                                   else "2026-11-19T00:00:00Z"}}
                         for market in ORDER}}
    board_path.write_text(json.dumps({**board, "content_hash": sha256_of(board)}), encoding="utf-8")
    quote_reads = []

    def quote(market, **options):
        quote_reads.append((market, options.get("reference_at")))
        return {"source_symbol": sources.quotes.SYMBOLS[market][1], "value": 158.2,
                "prior_close": 153 if market == "USDJPY" else 158,
                "observed_at_utc": (friday_close if market == "US500" else now).isoformat(),
                "known_at_utc": now.isoformat(), "source": "Attributed test quote",
                "source_url": "https://example.test/quote", "observation_sha256": market.lower()}

    snapshots = {market: sources.wrap_quote(quote(market)) for market in ORDER if market not in {"XAUUSD", "US500"}}
    snapshots.update({"XAUUSD": {"symbol": "GC=F"}, "US500": {"symbol": "ES=F"}})
    quote_reads.clear()
    gaps = {}
    pack["morning_map_sources"] = sources.morning_map_sources(
        snapshots, board_path, now=now, last_close=friday_close, quote=quote, clock=lambda: now, gaps=gaps)
    assert not gaps
    assert quote_reads == [("XAUUSD", None), ("US500", friday_close + timedelta(hours=1))]
    assert pack["morning_map_sources"]["rows"]["USDJPY"]["state_word"] == "Mixed trend"

    def snapshot(market, interval, folder, *, chart_size):
        folder.mkdir(parents=True, exist_ok=True)
        return capture(folder, "W" if chart_size == (1600, 700) else "T", market)

    monkeypatch.setattr(tv, "capture", snapshot)
    monkeypatch.setattr(quality, "review_vision",
                        lambda image, **_: {**yes_review(image)["vision"], "status": "REVIEWED"})
    from live_contentops import llm_operator_control_v1 as controls
    monkeypatch.setattr(controls, "llm_operator_pause_active", lambda *args, **kwargs: False)
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    transport = LocalTransport()
    folder = tmp_path / "wrap"
    packet = job.stage(store, pack, editorial.draft(pack, folder, call=select_first), folder)

    def factory(store, plan, **kwargs):
        coordinator = DurablePublicationCoordinator(store=store, transport_runtime=transport,
            readiness_provider=lambda _d: {"readiness_state": "READY_NON_BROWSER_BINDING"},
            clock=lambda: now, published_content_path=tmp_path / "published.jsonl")
        coordinator.recovery_scope = {"work_item_id": plan["market_wrap"], "plan": plan, "exact_work_item_only": True}
        coordinator.allow_prior_confirmed_distribution = True
        return coordinator

    publication = job.continue_wrap(store, packet, clock=lambda: now, factory=factory)
    assert not publication["unconfirmed_wrap_destinations"]
    assert {destination for destination, _ in transport.writes} == set(job.WRAP_DESTINATIONS)
    by_id = {asset["asset_id"]: asset for asset in packet["media_assets"]}
    for destination, intent in transport.writes:
        _, binding = _payload_binding(intent, destination)
        assets = [by_id[item["asset_id"]] for item in binding["media_manifest"]]
        assert assets[0]["tradingview_snapshot"]["tv_symbol"] == tv.SYMBOLS["USDJPY"]
        master = "T" if destination in {"instagram_business", "threads"} else "W"
        assert {asset["image_template"]["master"] for asset in assets} == {master}
        if destination in quality.SINGLE_IMAGE_DESTINATIONS:
            assert len(assets) == 1
        else:
            assert [asset["image_template"]["image_number"] for asset in assets] == [1, 2]
            assert [row["market"] for row in assets[1]["image_template"]["input"]["map"]["rows"]] == list(ORDER)


def test_late_resume_reconciles_other_surfaces_when_one_readback_is_pending():
    from live_contentops.native_neo_executor_v1 import PENDING, NativeNeoInputRequired

    class RetainedStore:
        def get_dispatches_for_work_item(self, _):
            return [{"dispatch_id": "x", "platform": "x", "status": "UNKNOWN_WRITE"},
                    {"dispatch_id": "substack_notes", "platform": "substack_notes", "status": PENDING}]

    class ReadbackOnly:
        def readback_existing_dispatch(self, dispatch_id):
            if dispatch_id == "x":
                raise NativeNeoInputRequired({"destination": "x", "action": "READBACK"})
            return {"reconciliation_status": "RECONCILED_CONFIRMED"}

        def publication_state(self, *_):
            return {"per_destination": {}}

    def factory(*_, allow_publish):
        assert allow_publish is False
        return ReadbackOnly()

    now = at("2026-11-23T13:45Z")
    packet = {"identity": "cc689-daily-2026-11-23", "plan": {
        "publication_window": {"expires_at_utc": now.isoformat()}}}
    result = job.continue_wrap(RetainedStore(), packet, clock=lambda: now, factory=factory)
    assert result["recovery"]["x"]["pending_native_request"]["action"] == "READBACK"
    assert result["recovery"]["substack_notes"]["reconciliation_status"] == "RECONCILED_CONFIRMED"


def test_expired_job_cannot_start_new_drafts(tmp_path, cash):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    def unexpected(*args, **kwargs):
        pytest.fail("The cutoff precedes collection or any transport")
    now = at("2026-11-23T13:45Z")
    result = job.run_due(store, rollout={"editorial_output_root": str(tmp_path)}, now=now,
        clock=lambda: now, cash_calendar=cash, gather=unexpected, writer=unexpected, publish=unexpected)
    assert result["state"] == "WRAP_WINDOW_ELAPSED_WITHOUT_PACKET"


def test_writer_finishing_at_cutoff_does_not_start_a_chart_capture(tmp_path, pack, cash):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    now = at("2026-11-23T13:00Z")

    def writer(pack, folder):
        nonlocal now
        now = at(pack["slot"]["deadline_utc"])
        return editorial.draft(pack, folder, call=select_first)

    def unexpected(*args, **kwargs):
        pytest.fail("The cutoff precedes the chart capture and publication")

    result = job.run_due(store, rollout={"editorial_output_root": str(tmp_path)}, now=now,
                         clock=lambda: now, cash_calendar=cash, gather=lambda *_a, **_kw: pack,
                         writer=writer, media=unexpected, publish=unexpected)
    assert result["state"] == "WRAP_EDITORIAL_WINDOW_EXPIRED"
    assert store.get_outbox_message(pack["slot"]["id"]) is None


def test_neo_clicks_apply_the_wrap_deadline_to_each_browser_transport():
    from live_contentops import neo_endpoint_executor_v1 as neo

    script = r"""
const fs = require('node:fs');
const AsyncFunction = Object.getPrototypeOf(async function() {}).constructor;
const run = new AsyncFunction('page', 'input', fs.readFileSync(process.argv[1], 'utf8'));
const deadline = '2026-11-23T13:45:00Z';
const cases = [
  ['plan_substack_publish', 'substack', 'Publish now', [true]],
  ['plan_substack_confirm', 'substack', 'Publish on web only', []],
  ['article_publish', 'linkedin', 'Post', [['Bound copy'], true]],
  ['article_publish', 'linkedin_company', 'Post', [['Bound copy'], true]],
  ['publish', 'substack_notes', 'Post', [{count:1,matches:true}, ['Bound copy'], {marked:true}]],
  ['publish', 'x', 'Post', [{count:1,matches:true}, ['Bound copy'], {marked:true}]],
];
(async () => {
  const results = [];
  for (const [phase, destination, name, values] of cases) {
    for (const elapsed of [false, true]) {
      Date.now = () => Date.parse(deadline) - (elapsed ? 0 : 1);
      const clicks = [];
      let index = 0;
      const refs = [{role:'button', name, ref:'submit'}];
      if (destination === 'linkedin') {
        refs.push({role:'button', name:'Jim Pham'}, {role:'button', name:'Post to Anyone'});
      }
      const page = {
        snapshot: async () => ({url:'https://www.linkedin.com/feed/', refs}),
        evaluateInPage: async () => ({value:values[index++]}),
        waitForSelector: async () => ({matched:true}),
        click: async (ref) => clicks.push(ref),
      };
      const result = await run(page, {phase, destination, wrap_deadline_utc:deadline, posts:['Bound copy'],
                                     require_media:phase === 'article_publish'});
      results.push({phase, destination, elapsed, clicks, result});
    }
  }
  process.stdout.write(JSON.stringify(results));
})().catch(error => { console.error(error); process.exit(1); });
"""
    source = Path(neo.__file__).with_name("neo_endpoint_steps_v1.js")
    checks = json.loads(check_output(["node", "-e", script, str(source)], timeout=10))
    assert len(checks) == 12
    for check in checks:
        if check["elapsed"]:
            assert check["clicks"] == [], check
            assert check["result"]["definite_no_write"] is True
            assert check["result"]["reason_code"] == "WRAP_PUBLICATION_DEADLINE_ELAPSED"
        else:
            assert check["clicks"] == ["submit"], check
            assert check["result"]["status"] == "CLICKED"
