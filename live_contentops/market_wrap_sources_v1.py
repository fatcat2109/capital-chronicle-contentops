"""Point-in-time inputs for the daily and Sunday market wraps (CC-689)."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
import json
import re
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from zoneinfo import ZoneInfo

from . import public_market_quote_v1 as quotes
from .capital_chronicle_latest_report_consumer_v1 import sha256_of
from .event_article_guard_v1 import check_publication_copy
from .main_report_projection_source_v1 import NATIVE_MAIN_ANALYSIS_ROOT
from .plan_reader_copy_v1 import et
from .plan_scenario_lines_v1 import _clean
from .plan_status_posts_v1 import MAIN_ROOT, read_export
from .reader_article_contract_v1 import sentences, words
from .weekly_scored_calls_v1 import project as weekly_calls

ET = ZoneInfo("America/New_York")
UTC = timezone.utc
START = date(2026, 11, 23)
INTAKE = Path(r"A:\Capital Chronicle\Runtime\OfficialRates\cc-078-20261101\state\intake")
CALENDAR = INTAKE / "official-calendar/calendar.json"
CASH_CALENDAR = MAIN_ROOT / "config/ibkr_paper/us_session_calendar_v1.json"
HISTORY = INTAKE / "market-history/archives"
RELEASES = INTAKE.parents[3] / "OfficialReleases/official_release_feed_v1.json"
FEDERAL_SOURCES = {"www.bls.gov", "www.bea.gov", "www.census.gov",
                   "www.eia.gov", "www.federalreserve.gov"}
MARKETS = {
    "EURUSD": ("Euro", "EURUSD", ("eurusd", "euro")),
    "USDJPY": ("Yen", "USDJPY", ("usdjpy", "yen")),
    "XAUUSD": ("Gold", "GOLD_FUTURES", ("xauusd", "gold")),
    "USOIL": ("Oil", "USOIL", ("usoil", "wti", "oil")),
    "US500": ("S&P 500", "US500_FUTURES", ("us500", "spx", "sp500")),
    "BTCUSD": ("Bitcoin", "BTCUSD", ("btcusd", "bitcoin", "btc")),
}
OPEN_STATUSES = {
    "WAITING": "Waiting for entry", "WATCH": "Waiting for entry", "PENDING": "Waiting for entry",
    "ARMED": "Waiting for entry",
    "ACTIVE": "Waiting for entry", "OPEN": "Open", "TRIGGERED": "Triggered", "FILLED": "Filled",
    "ENTRY_WINDOW_OPEN": "Waiting for entry", "NOT_YET_ACTIVE": "Entry window has yet to open",
}


def utc(value):
    return quotes.utc(value)


def session_day(day, calendar):
    if day.weekday() >= 5:
        return False
    year = calendar.get("years", {}).get(str(day.year))
    if year is None:
        raise ValueError("US_CASH_CALENDAR_YEAR_UNAVAILABLE")
    return day.isoformat() not in year["closed"]


def slot_at(now, calendar):
    now = utc(now)
    day = now.astimezone(ET).date()
    weekly = day.weekday() == 6
    if day < START - timedelta(days=1 if weekly else 0) or day.weekday() == 5:
        return None
    if not weekly and not session_day(day, calendar):
        return None
    start = datetime.combine(day, time(15), UTC) if weekly else datetime.combine(day, time(8), ET)
    deadline = (datetime.combine(day, time(18), UTC) if weekly
                else datetime.combine(day, time(8, 45), ET))
    edition = "weekly" if weekly else "daily"
    return {"id": f"cc689-{edition}-{day}", "edition": edition, "day_et": day.isoformat(),
            "start_utc": start.astimezone(UTC).isoformat(),
            "deadline_utc": deadline.astimezone(UTC).isoformat()}


def last_session(day, calendar):
    while not session_day(day, calendar):
        day -= timedelta(days=1)
    return day


def safe_prose(value):
    """Use Main's admissible words and provider's lawful single facts."""
    if not isinstance(value, str) or not value.strip() or "|" in value or "[" in value:
        return None
    if re.search(r"https?://|\b(?:Kalshi|Polymarket|prediction markets?|X list)\b", value, re.I):
        return None
    try:
        line, _ = _clean(value)
        if line and not any(len(words(s)) > 35 for s in sentences(line)):
            from .plan_analysis_pages_v1 import public_filter
            from .public_instruments_v1 import POLICY, validate_payload
            public_filter(line)
            validate_payload({"public_instrument_policy": POLICY}, {"text": line})
            check_publication_copy({"body": line}, require_notice=False)
            return line
    except (ValueError, IndexError):
        return None
    return None


def public_sentences(value):
    # A private or internal sentence does not take adjacent public analysis
    # out of the wrap. Sentence spans are still the analyst's own words.
    return [line for span in sentences(value) if (line := safe_prose(span))] if isinstance(value, str) else []


def _market(candidate_id):
    suffix = str(candidate_id).lower().split("_")[-1]
    return next((key for key, (_, _, aliases) in MARKETS.items() if suffix in aliases), None)


def project_main(value):
    """Select named analysis fields only. Execution, account, and raw rows never enter."""
    synthesis = value["native_synthesis"]
    primary = value.get("primary_analysis") or {}
    layers = {key: {} for key in MARKETS}
    outlooks = {}
    for entries, field in (("causal_reasoning", "supporting_mechanism"),
                           ("candidate_evaluations", "mechanism_and_transmission")):
        for row in primary.get(entries) or []:
            market = _market(row.get("candidate_id"))
            lines = public_sentences(row.get(field))
            if market and lines:
                layers[market].setdefault("Macro and catalysts", lines[0])
    for row in synthesis.get("candidates") or []:
        market = _market(row.get("candidate_id"))
        if not market:
            continue
        lines = public_sentences(row.get("rationale"))
        if lines:
            outlooks[market] = lines[0]
    field_lines = [(line, [row.get("candidate_id")]) for row in synthesis.get("candidates") or []
                   for line in public_sentences(row.get("rationale"))]
    field_lines += [(line, row.get("candidate_ids") or []) for row in primary.get("claims") or []
                    for line in public_sentences(row.get("claim"))]
    for line, candidates in field_lines:
        # Classify only lines that name the layer themselves. A causal claim
        # can inform more than one market when Main binds those candidate IDs.
        for label, pattern in (
            ("Fundamentals", r"\b(?:supply|demand|inventories|earnings|production)\b"),
            ("Positioning and sentiment", r"\b(?:positioning|sentiment|crowding|flows|priced in)\b"),
            ("Options", r"\b(?:options|gamma|skew|implied volatility)\b"),
            ("Technical", r"\b(?:support|resistance|breakout|moving average|trend)\b"),
        ):
            if re.search(pattern, line, re.I):
                for candidate_id in candidates:
                    market = _market(candidate_id)
                    if market:
                        layers[market].setdefault(label, line)
    summaries = [line for row in synthesis.get("summary") or [] for line in public_sentences(row.get("text"))]
    return {"layers": layers, "outlooks": outlooks, "summary": summaries[:2]}


def latest_main(as_of, root=NATIVE_MAIN_ANALYSIS_ROOT):
    root = Path(root)
    paths = [*root.glob("requests/*/analysis-end.json"), *root.glob("shocks/*/analysis-end.json"),
             *root.glob("shocks/*/decision91/analysis-end.json")]
    reports = []
    for receipt in paths:
        try:
            proof_raw = receipt.read_bytes()
            proof = json.loads(proof_raw)
            completed = utc(proof["completed_at_utc"])
            if proof.get("schema_errors") or completed > as_of:
                continue
            reports.append((completed, receipt, proof, sha256(proof_raw).hexdigest()))
        except (OSError, KeyError, ValueError, TypeError):
            continue
    for completed, receipt, proof, proof_hash in sorted(reports, reverse=True):
        try:
            capture_raw = receipt.with_name("capture.json").read_bytes()
            cutoff = utc(json.loads(capture_raw)["known_at_utc"])
            if cutoff > completed:
                continue
            source = receipt.with_name("analysis-native.json")
            raw = source.read_bytes()
            value = json.loads(raw)
            if proof["output_sha256"] not in {
                sha256_of(value), sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                                  ensure_ascii=True).encode()).hexdigest(),
            }:
                continue
            return {**project_main(value), "at_utc": cutoff.isoformat(), "completed_at_utc": completed.isoformat(),
                    "run_id": source.parent.name, "sha256": sha256(raw).hexdigest(),
                    "completion_sha256": proof_hash, "capture_sha256": sha256(capture_raw).hexdigest()}
        except (OSError, KeyError, ValueError, TypeError):
            continue
    return {"cause": "MAIN_COMPLETED_ANALYSIS_UNAVAILABLE", "layers": {}, "outlooks": {}, "summary": []}


def project_plans(export, as_of):
    status = export["status"]
    published = utc(status["generated_at_utc"])
    if published > as_of:
        raise ValueError("PLAN_EXPORT_AFTER_WRAP_CUTOFF")
    result, scenarios = [], []
    for row in status.get("plans", []):
        plan_id, market = row.get("plan_id"), row.get("asset_id")
        if not plan_id or not market or not re.fullmatch(r"[A-Z][A-Z0-9]{1,14}", market):
            continue
        label = OPEN_STATUSES.get(row.get("status"))
        until = row.get("entry_deadline_utc") or row.get("expires_at_utc")
        if label is None and row.get("status") is None and until and utc(until) > as_of:
            label = "Status unavailable"
        if label:
            from .plan_status_posts_v1 import TITLES
            instrument = MARKETS.get(market, (TITLES.get(market, market),))[0]
            horizon = {"MID": "mid-term", "SHORT": "short-term", "LONG": "long-term"}.get(row.get("horizon_lane"))
            registered = et(row["registered_at_utc"]) if row.get("registered_at_utc") else None
            description = ", ".join(x for x in (instrument, horizon, label,
                                                 f"registered {registered}" if registered else None) if x)
            result.append({"id": plan_id, "market": market, "text": description + "."})
        scenario = row.get("scenario_analysis") or {}
        if market not in MARKETS or not isinstance(scenario, dict):
            continue
        cases = []
        for key, name in (("base_case", "Main"), ("main_alternative", "Alternative")):
            case = scenario.get(key) or {}
            lines = public_sentences(case.get("market_move"))
            if not lines:
                break
            odds = case.get("probability_pct")
            probability = format(odds, "g") if type(odds) in (int, float) and 0 < odds < 100 else None
            if key == "base_case" and probability is None:
                break
            checks = (
                ("Confirmation", next(iter(public_sentences(case.get("confirmation"))), None)),
                ("Invalidation", next(iter(public_sentences(scenario.get("invalidation_text")
                                                           or scenario.get("invalidation_reason"))), None)),
            )
            cases.append({"name": name, "probability": probability, "text": lines[0],
                          "checks": dict((label, v) for label, v in checks if v)})
        if len(cases) == 2 and row.get("registered_at_utc") and utc(row["registered_at_utc"]) <= as_of:
            scenarios.append({"market": market, "id": plan_id, "registered_at_utc": row["registered_at_utc"],
                              "cases": cases})
    current = max(scenarios, key=lambda row: utc(row["registered_at_utc"]), default=None)
    return {"rows": result, "scenario": current, "sha256": status["content_hash"],
            "generated_at_utc": published.isoformat(), "quarantined_rows": len(export.get("quarantined_rows", []))}


def calendar_events(raw, start, end, *, as_of):
    """Freeze public schedule rows, preserving date-only precision and rights."""
    doc = json.loads(raw)
    if (doc.get("public_use_allowed") is not True or not doc.get("built_at_utc")
            or utc(doc["built_at_utc"]) > as_of):
        raise ValueError("OFFICIAL_CALENDAR_PUBLIC_SNAPSHOT_UNAVAILABLE")
    rows, seen = [], set()
    for row in doc.get("events", []):
        key, title, url = row.get("event_id"), row.get("title"), row.get("source_url")
        if (not isinstance(key, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]{2,59}", key)
                or key in seen or row.get("public_use_allowed") is not True
                or not isinstance(title, str) or not title.strip() or not isinstance(url, str)
                or urlsplit(url).scheme != "https" or not urlsplit(url).hostname
                or row.get("schedule_status") not in {
                    "PUBLISHER_SCHEDULE_SUBJECT_TO_REVISION", "PUBLISHER_SCHEDULE_IF_NECESSARY",
                }):
            continue
        try:
            if utc(row["retrieved_at_utc"]) > as_of:
                continue
            scheduled = date.fromisoformat(row["scheduled_date"])
            if row.get("scheduled_at_utc"):
                timestamp = utc(row["scheduled_at_utc"])
                if timestamp.astimezone(ZoneInfo(row["source_timezone"])).date() != scheduled:
                    continue
                if not start <= timestamp < end:
                    continue
                label = et(timestamp)
            else:
                if not start.astimezone(ET).date() <= scheduled <= end.astimezone(ET).date():
                    continue
                timestamp = None
                label = f"{scheduled:%a} {scheduled.day} {scheduled:%b} (date only)"
            check_publication_copy({"title": title}, require_notice=False)
            from .plan_analysis_pages_v1 import public_filter
            public_filter(title, source_locator=url)
        except (KeyError, ValueError, TypeError, AttributeError):
            continue
        qualifier = " (if needed)" if row["schedule_status"].endswith("IF_NECESSARY") else ""
        rows.append({"id": key, "name": title, "time": label, "scheduled_at_utc": (
            timestamp.isoformat() if timestamp else None), "scheduled_date": scheduled.isoformat(),
            "source_url": url, "qualifier": qualifier, "country": row.get("country"),
            "row_sha256": sha256_of(row)})
        seen.add(key)
    return sorted(rows, key=lambda row: (row["scheduled_at_utc"] or row["scheduled_date"], row["id"]))


def public_release_facts(start, end, path=RELEASES):
    """Use attributable release figures where the federal feed has the exact print."""
    from .reader_article_contract_v1 import numbers
    from .plan_analysis_pages_v1 import public_filter

    raw = Path(path).read_bytes()
    values = json.loads(raw)["rows"]
    facts = {}
    for row in values:
        try:
            url = row["url"]
            if urlsplit(url).hostname not in FEDERAL_SOURCES or not url.startswith("https://"):
                continue
            at, known = utc(row["published_utc"]), utc(row["first_seen_utc"])
            if not start <= at <= known <= end:
                continue
            title = safe_prose(row["title"])
            publisher = row["source"]
            if not title or not isinstance(publisher, str):
                continue
            public_filter(publisher, source_locator=url)
            # Retain a single attributed source sentence, never a release's
            # full summary or data table. A number in the title alone is not a print.
            lines = public_sentences(row.get("summary"))
            line = next((s for s in lines if any(re.search(r"%|bps|million|billion|points", value, re.I)
                        for value in numbers(s))), None)
            if line:
                text = f"{et(at)} — {title} {line}"
                facts[row["item_id"]] = {"id": row["item_id"], "text": text, "publisher": publisher,
                    "source_url": url, "known_at_utc": known.isoformat(), "published_at_utc": at.isoformat(),
                    "sha256": sha256_of(row), "feed_sha256": sha256(raw).hexdigest()}
        except (KeyError, ValueError, TypeError):
            continue
    return sorted(facts.values(), key=lambda row: row["published_at_utc"])[-8:]


def history_bars(raw, ticker, known_at):
    """Use dated, complete sessions of the exact Yahoo instrument."""
    rows, = json.loads(raw)["chart"]["result"]
    meta = rows["meta"]
    if meta.get("symbol") != ticker:
        raise ValueError("WRAP_HISTORY_SYMBOL_MISMATCH")
    exchange = ZoneInfo(meta["exchangeTimezoneName"])
    bars, = rows["indicators"]["quote"]
    result = {}
    for seconds, high, low, close in zip(rows["timestamp"], bars["high"], bars["low"], bars["close"], strict=True):
        stamp = datetime.fromtimestamp(seconds, UTC).astimezone(exchange)
        day = stamp.date()
        if day >= known_at.astimezone(exchange).date() or any(v is None for v in (high, low, close)):
            continue
        try:
            high, low, close = map(quotes._number, (high, low, close))
        except ValueError:
            continue
        if low <= close <= high:
            result[day] = (high, low, close)
    return result


def market_history(market, days, *, as_of, root=HISTORY, reader=quotes.http_read, clock=quotes.utcnow):
    ticker = quotes.SYMBOLS[MARKETS[market][1]][1]
    # Data's JPY alias was redirected to the same pair in the provider response.
    aliases = {ticker, "JPY=X"} if market == "USDJPY" else {ticker}
    sources = []
    for sidecar in (Path(root) / market).glob("D1-*.source.json"):
        try:
            spec = json.loads(sidecar.read_bytes())
            known = utc(spec["known_at_utc"])
            if spec.get("ticker") in aliases and known <= as_of:
                sources.append((known, sidecar, spec))
        except (OSError, ValueError, KeyError, TypeError):
            continue
    for known, sidecar, spec in sorted(sources, reverse=True)[:4]:
        path = sidecar.with_suffix("").with_suffix(".json")
        try:
            raw = path.read_bytes()
            if len(raw) != spec["bytes"] or sha256(raw).hexdigest() != spec["sha256"]:
                continue
            bars = history_bars(raw, ticker, known)
            if set(days) <= bars.keys():
                return bars, {"sha256": spec["sha256"], "url": spec["url"], "known_at_utc": known.isoformat()}
        except (OSError, ValueError, KeyError, TypeError):
            continue
    if reader is None:
        raise ValueError("WRAP_HELD_CLOSING_SESSIONS_UNAVAILABLE")
    # One bounded public request through the established quote transport.
    base = quotes.source_url(MARKETS[market][1]).split("?")[0]
    url = base + "?" + urlencode({"range": "2mo", "interval": "1d"})
    raw = reader(url)
    known = clock()
    bars = history_bars(raw, ticker, known)
    if not set(days) <= bars.keys():
        raise ValueError("WRAP_CLOSING_SESSIONS_UNAVAILABLE")
    return bars, {"sha256": sha256(raw).hexdigest(), "url": url, "known_at_utc": known.isoformat()}


def move(market, end, start, *, basis, normal_day=None):
    if end["symbol"] != start["symbol"] or start["value"] <= 0:
        raise ValueError("WRAP_COMPARISON_INSTRUMENT_MISMATCH")
    delta = end["value"] - start["value"]
    return {"market": market, "instrument": quotes.SYMBOLS[MARKETS[market][1]][2],
            "end": end, "start": start, "basis": basis, "change_pct": round(delta / start["value"] * 100, 2),
            "normal_days": round(delta / normal_day, 2) if normal_day else None}


def normal_day(bars, before):
    bars = [bars[day] for day in sorted(bars) if day <= before][-15:]
    if len(bars) != 15:
        return None
    ranges = [max(high - low, abs(high - previous[2]), abs(low - previous[2]))
              for previous, (high, low, _) in zip(bars, bars[1:])]
    return sum(ranges) / len(ranges) or None


def prior_stops(export, day, as_of):
    from .plan_status_posts_v1 import TITLES
    source = export["status"]
    if source.get("scored_call_count") is None:
        return None
    rows = []
    for plan in source["plans"]:
        outcome = plan.get("outcome") or {}
        score = outcome.get("score") or {}
        if outcome.get("state") != "SCORED" or score.get("result") != "STOPPED":
            continue
        resolved = utc(score["resolved_at_utc"])
        if resolved.astimezone(ET).date() == day and utc(score["scored_at_utc"]) <= as_of:
            market = plan["asset_id"]
            name = MARKETS.get(market, (TITLES.get(market, market),))[0]
            rows.append(f"- Main recorded a stopped {name} plan on {et(resolved)}.")
    return "\n".join(rows) or "Main recorded no scored stops from the last completed cash session."


def collect(slot, *, now, cash_calendar, previous=None, quote=quotes.get,
            history=market_history, plans=read_export, main=latest_main, calendar=CALENDAR,
            clock=quotes.utcnow, releases=public_release_facts):
    """Collect each source once. A defect affects only dependent rows."""
    now = utc(now)
    weekly = slot["edition"] == "weekly"
    day = date.fromisoformat(slot["day_et"])
    last = last_session(day - timedelta(days=2 if weekly else 1), cash_calendar)
    prior = last_session(day - timedelta(days=9), cash_calendar) if weekly else None
    gaps, rows, snapshots = {}, {}, {}
    for market, (_, key, _) in MARKETS.items():
        try:
            ticker = quotes.SYMBOLS[key][1]
            bars, source = {}, {}
            try:
                bars, source = history(market, [prior, last] if weekly else [last], as_of=now)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                if weekly:
                    raise
                gaps[f"history:{market}"] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
            if weekly:
                end = {"symbol": ticker, "date": last.isoformat(), "value": bars[last][2], "source": source}
                start = {"symbol": ticker, "date": prior.isoformat(), "value": bars[prior][2], "source": source}
                basis = "from the previous week's close"
            else:
                observation = quote(key, max_age_seconds=3600)
                end = {"symbol": observation["source_symbol"], "value": observation["value"],
                       "observed_at_utc": observation["observed_at_utc"], "known_at_utc": observation["known_at_utc"],
                       "source": observation["source"], "url": observation["source_url"],
                       "sha256": observation["observation_sha256"]}
                held = (previous or {}).get("snapshots", {}).get(market)
                if (held and held["symbol"] == ticker
                        and (utc(held["observed_at_utc"]) < utc(end["observed_at_utc"])
                             if held.get("observed_at_utc") else held.get("date", "") < day.isoformat())):
                    start, basis = held, "since the last wrap"
                elif last in bars:
                    start = {"symbol": ticker, "date": last.isoformat(), "value": bars[last][2], "source": source}
                    basis = "since the last session's close"
                else:
                    start = {"symbol": ticker, "value": observation["prior_close"],
                             "source": observation["source"], "sha256": observation["observation_sha256"]}
                    basis = "from the provider's prior close"
            rows[market] = move(market, end, start, basis=basis, normal_day=normal_day(bars, last))
            if source:
                rows[market]["normal_day_source"] = source
            snapshots[market] = end
        except (OSError, ValueError, KeyError, TypeError) as exc:
            gaps[f"quote:{market}"] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__

    upcoming, weekend, calendar_hash = [], [], None
    try:
        raw_calendar = Path(calendar).read_bytes()
        calendar_hash = sha256(raw_calendar).hexdigest()
        upcoming = calendar_events(raw_calendar, now, now + timedelta(days=7 if weekly else 1), as_of=now)
        if weekly:
            friday_close = cash_close(last, cash_calendar)
            weekend = calendar_events(raw_calendar, friday_close, now, as_of=now)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        gaps["calendar"] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__

    score = None
    stops = None
    plan_record = {"rows": [], "scenario": None}
    try:
        export = plans()
        # The producer may update during I/O. Its generation clock remains
        # distinct from the quote and Main clocks.
        plan_cutoff = max(now, utc(clock()))
        plan_record = project_plans(export, plan_cutoff)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        gaps["plans"] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
    else:
        try:
            if weekly:
                score = weekly_calls(export, cutoff_utc=plan_cutoff.isoformat())
            else:
                stops = prior_stops(export, last, plan_cutoff)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            gaps["call_results"] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
    report = main(now)
    if report.get("cause"):
        gaps["main"] = report["cause"]
    try:
        release_facts = releases(cash_close(last, cash_calendar) if weekly
                                 else datetime.combine(last, time(), ET), now)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        release_facts = []
        gaps["releases"] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
    latest_quote = max((utc(obs["observed_at_utc"]) for obs in snapshots.values()
                        if obs.get("observed_at_utc")), default=None)
    # Sunday uses the explicitly dated last completed session, with its own
    # release deadline. A replay or reread does not make a quote newer.
    data_clock = cash_close(last, cash_calendar) if weekly else latest_quote
    return {"slot": slot, "markets": rows, "snapshots": snapshots, "previous_wrap": (
            previous["slot"]["id"] if previous else None), "analysis": report, "plans": plan_record,
            "events": upcoming, "weekend_events": weekend, "calendar_sha256": calendar_hash,
            "weekly_calls": score, "prior_stops_text": stops, "gaps": gaps,
            "released_facts": release_facts,
            "data_cutoff_utc": data_clock.astimezone(UTC).isoformat() if data_clock else None}


def cash_close(day, calendar):
    early = calendar["years"][str(day.year)]["early_close_13_et"]
    return datetime.combine(day, time(13 if day.isoformat() in early else 16), ET)
