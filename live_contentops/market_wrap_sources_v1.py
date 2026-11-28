"""Point-in-time inputs for the daily and Sunday market wraps (CC-689)."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
import json
import re
from pathlib import Path
from subprocess import TimeoutExpired
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from . import public_market_quote_v1 as quotes
from . import scenario_voice_v1 as voice
from .capital_chronicle_latest_report_consumer_v1 import sha256_of
from .daily_trend_board_v1 import SOURCE as TREND_BOARD, us_trading_age
from .event_article_guard_v1 import FEDWATCH_PATTERN, check_publication_copy
from .main_report_projection_source_v1 import NATIVE_MAIN_ANALYSIS_ROOT
from .plan_reader_copy_v1 import et, scenario_case_copy
from .plan_scenario_lines_v1 import _clean
from .plan_status_posts_v1 import MAIN_ROOT, read_export
from .publication_image_contract_v1 import CASH_INDEX_MARKETS, us_cash_session_bounds
from .reader_article_contract_v1 import sentences, words
from .weekly_scored_calls_v1 import project as weekly_calls

ET = ZoneInfo("America/New_York")
UTC = timezone.utc
START = date(2026, 11, 23)
INTAKE = Path(r"A:\Capital Chronicle\Runtime\OfficialRates\cc-078-20261101\state\intake")
CALENDAR = INTAKE / "official-calendar/calendar.json"
CASH_CALENDAR = MAIN_ROOT / "config/ibkr_paper/us_session_calendar_v1.json"
BARS_DB = quotes.BARS_DB
RELEASES = INTAKE.parents[3] / "OfficialReleases/official_release_feed_v1.json"
FEDERAL_SOURCES = {"www.bls.gov", "www.bea.gov", "www.census.gov",
                   "www.eia.gov", "www.federalreserve.gov"}
MARKETS = {
    "EURUSD": ("Euro", "EURUSD", ("eurusd", "euro")),
    "USDJPY": ("Yen", "USDJPY", ("usdjpy", "yen")),
    "XAUUSD": ("Gold", "XAUUSD", ("xauusd", "gold")),
    "USOIL": ("Oil", "USOIL", ("usoil", "wti", "oil")),
    "US500": ("S&P 500", "US500", ("us500", "spx", "sp500")),
    "BTCUSD": ("Bitcoin", "BTCUSD", ("btcusd", "bitcoin", "btc")),
    # CC-788 / CC-024: all seven core markets resolve directly from held local bars.
    "USTEC": ("Nasdaq 100", "USTEC", ("ustec", "ndx", "nasdaq", "nas100")),
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
    if weekly:
        # Ops Product moved the first Sunday wrap forward while the PC stays on.
        start_hour = 12 if day == START - timedelta(days=1) else 15
        start = datetime.combine(day, time(start_hour), UTC)
    else:
        start = datetime.combine(day, time(8), ET)
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
    if re.search(r"https?://|\b(?:Kalshi|Polymarket|prediction markets?|X list)\b|" + FEDWATCH_PATTERN, value, re.I):
        return None
    try:
        line, _ = _clean(value)
        if line and not any(len(words(s)) > 35 for s in sentences(line)):
            from .plan_analysis_pages_v1 import public_filter
            from .public_instruments_v1 import POLICY, validate_payload
            public_filter(line)
            validate_payload({"public_instrument_policy": POLICY}, {"text": line})
            check_publication_copy({"body": line}, require_notice=False)
            voice.validate_copy(line)
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
            ("Positioning and sentiment", r"\b(?:positioning|sentiment|crowding|flows)\b"),
            ("Priced in", r"\b(?:priced in|already reflects?|discounted)\b"),
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
        # Builder L, 24 Nov 2026 (relaunch rehearsal): the wrap's scenarios are an open plan's. The newest plan
        # of any status led the 1 Dec wrap with a USD/JPY plan that had expired on 23 Nov.
        if (market not in MARKETS or not label or not row.get("registered_at_utc")
                or utc(row["registered_at_utc"]) > as_of):
            continue
        cases = scenario_case_copy(row)
        if cases:
            scenarios.append({"market": market, "id": plan_id, "registered_at_utc": row["registered_at_utc"],
                              "cases": cases, "scenario_voice": voice.CONTRACT})
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


def history_bars_from_sqlite(market, *, as_of, db_path=None, cash_calendar=None, zero_write=False):
    """Read completed non-Yahoo D1 bars and roll up deduplicated M15 NATIVE_BROKER sessions.

    Trap 1: bars.sqlite3 table `bars` has ~9x duplicate rows per open_epoch; deduplicate by
    (open_epoch -> newest known_epoch) excluding `invalid_bars`.
    Trap 2: NATIVE_DAILY_ROUTE paused 2026-11-22, so completed sessions strictly after the
    latest D1 bar (or missing from D1) are rolled up from M15 `bars` respecting US cash
    holidays and 13:00 ET early closes for US500/USTEC.
    WAL-aware read-only: uses quotes._open_readonly_sqlite (immutable=1 when wal_bytes == 0;
    live WAL read or zero_write temp-copy snapshot when wal_bytes > 0).
    """
    as_of_utc = utc(as_of)
    as_of_ts = as_of_utc.timestamp()
    as_of_et_day = as_of_utc.astimezone(ET).date()
    as_of_utc_day = as_of_utc.date()
    db_symbol = quotes.SYMBOLS[MARKETS[market][1]][1]
    path = Path(BARS_DB if db_path is None else db_path)
    bars: dict[date, tuple[float, float, float]] = {}
    used_series: set[str] = set()
    used_hashes: set[str] = set()
    latest_known: float | None = None
    rolled_days: list[str] = []

    with quotes._open_readonly_sqlite(path, zero_write=zero_write) as con:
        tables = quotes._sqlite_tables(con)
        # 1) Non-Yahoo D1 bars from history_bars (priority: DESK_ODDS > NATIVE_DAILY_ROUTE > EXNESS:%).
        if "history_bars" in tables and "history_sources" in tables:
            has_hist_invalid = "history_invalid" in tables
            invalid_clause = (
                "AND NOT EXISTS (SELECT 1 FROM history_invalid i "
                "WHERE i.source_id = b.source_id AND i.open_epoch = b.open_epoch)"
                if has_hist_invalid else ""
            )
            sources = con.execute(
                """SELECT source_id, source_sha256, series_id, known_epoch
                   FROM history_sources
                   WHERE market = ? AND timeframe = 'D1'
                     AND series_id NOT LIKE 'YAHOO_FINANCE:%'
                     AND known_epoch <= ?""",
                (db_symbol, as_of_ts),
            ).fetchall()
            sources = sorted(
                sources,
                key=lambda s: (quotes._d1_series_rank(str(s["series_id"])), -float(s["known_epoch"])),
            )
            for src in sources:
                rows = con.execute(
                    f"""SELECT b.session_date, b.end_epoch, b.high, b.low, b.close
                        FROM history_bars b
                        WHERE b.source_id = ? AND b.end_epoch <= ?
                          {invalid_clause}
                        ORDER BY b.session_date ASC, b.open_epoch ASC""",
                    (src["source_id"], as_of_ts),
                ).fetchall()
                src_used = False
                for r in rows:
                    try:
                        sday = date.fromisoformat(str(r["session_date"]))
                        cutoff_day = as_of_utc_day if market == "BTCUSD" else as_of_et_day
                        if sday >= cutoff_day:
                            continue
                        high, low, close = map(quotes._number, (r["high"], r["low"], r["close"]))
                    except (ValueError, TypeError):
                        continue
                    if low <= close <= high and sday not in bars:
                        bars[sday] = (high, low, close)
                        src_used = True
                if src_used:
                    used_series.add(str(src["series_id"]))
                    used_hashes.add(str(src["source_sha256"]))
                    known_ep = float(src["known_epoch"])
                    if latest_known is None or known_ep > latest_known:
                        latest_known = known_ep

        # 2) Mandatory M15 -> D1 rollup from deduplicated NATIVE_BROKER bars excluding invalid_bars.
        if "bars" in tables:
            has_invalid = "invalid_bars" in tables
            invalid_clause = (
                "AND NOT EXISTS (SELECT 1 FROM invalid_bars i "
                "WHERE i.source_sha256 = b.source_sha256 AND i.symbol = b.symbol AND i.open_epoch = b.open_epoch)"
                if has_invalid else ""
            )
            m15_rows = con.execute(
                f"""SELECT b.open_epoch, b.high, b.low, b.close, b.known_epoch, b.source_sha256
                    FROM bars b
                    WHERE b.symbol = ? AND b.series_id = 'NATIVE_BROKER'
                      AND b.known_epoch <= ? AND (b.open_epoch + 900) <= ?
                      {invalid_clause}
                    ORDER BY b.open_epoch ASC, b.known_epoch DESC""",
                (db_symbol, as_of_ts, as_of_ts),
            ).fetchall()
            # Deduplicate by open_epoch, keeping the newest valid capture (highest known_epoch).
            deduped: dict[int, tuple[float, float, float, float, str]] = {}
            for r in m15_rows:
                op = int(r["open_epoch"])
                if op in deduped:
                    continue
                try:
                    high, low, close = map(quotes._number, (r["high"], r["low"], r["close"]))
                except ValueError:
                    continue
                if low <= close <= high:
                    deduped[op] = (high, low, close, float(r["known_epoch"]), str(r["source_sha256"]))

            grouped: dict[date, list[tuple[int, float, float, float, float, str]]] = {}
            cal_arg = cash_calendar if isinstance(cash_calendar, dict) else None
            cal_path = None if cal_arg is not None else (cash_calendar or CASH_CALENDAR)
            for op in sorted(deduped):
                high, low, close, known_ep, src_sha = deduped[op]
                open_utc = datetime.fromtimestamp(op, UTC)
                if market == "BTCUSD":
                    sday = open_utc.date()
                    session_done = sday < as_of_utc_day
                elif market in CASH_INDEX_MARKETS:
                    open_et = open_utc.astimezone(ET)
                    sday = open_et.date()
                    bounds = us_cash_session_bounds(sday, calendar_path=cal_path, calendar=cal_arg)
                    if bounds is None:
                        continue
                    open_t, close_t = bounds
                    if not (open_t <= open_et.time() < close_t):
                        continue
                    session_close_utc = datetime.combine(sday, close_t, ET).astimezone(UTC)
                    session_done = as_of_utc >= session_close_utc
                else:
                    open_et = open_utc.astimezone(ET)
                    sday = open_et.date()
                    if sday.weekday() >= 5:
                        continue
                    session_done = sday < as_of_et_day or as_of_utc >= datetime.combine(sday, time(17, 0), ET).astimezone(UTC)
                if not session_done or sday in bars:
                    continue
                grouped.setdefault(sday, []).append((op, high, low, close, known_ep, src_sha))

            for sday in sorted(grouped):
                session_bars = grouped[sday]
                bars[sday] = (
                    max(b[1] for b in session_bars),
                    min(b[2] for b in session_bars),
                    session_bars[-1][3],
                )
                rolled_days.append(sday.isoformat())
                used_series.add("NATIVE_BROKER:M15_ROLLUP")
                for b in session_bars:
                    used_hashes.add(b[5])
                    if latest_known is None or b[4] > latest_known:
                        latest_known = b[4]

    meta_payload = {
        "market": market,
        "db_symbol": db_symbol,
        "series_ids": sorted(used_series),
        "source_hashes": sorted(used_hashes),
        "m15_rolled_up_days": rolled_days,
    }
    known_iso = (
        datetime.fromtimestamp(latest_known, UTC).isoformat()
        if latest_known is not None else as_of_utc.isoformat()
    )
    return bars, {
        "sha256": sha256_of(meta_payload),
        "source": "LOCAL_BARS",
        "series_ids": sorted(used_series),
        "m15_rolled_up_days": rolled_days,
        "known_at_utc": known_iso,
    }


def market_history(market, days, *, as_of, db_path=None, cash_calendar=None, zero_write=False):
    """Load completed daily closing sessions from local held SQLite bars (zero Yahoo HTTP)."""
    bars, metadata = history_bars_from_sqlite(
        market, as_of=as_of, db_path=db_path, cash_calendar=cash_calendar, zero_write=zero_write,
    )
    if not set(days) <= bars.keys():
        raise ValueError("WRAP_HELD_CLOSING_SESSIONS_UNAVAILABLE")
    return bars, metadata


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
            rows.append(f"- A {name} plan was stopped on {et(resolved)}.")
    return "\n".join(rows) or "No plan was stopped in the last completed cash session."


def morning_map_sources(snapshots, board_path, *, now, last_close, quote, clock, gaps):
    """Bind the map to the chart instruments and each market's completed trend bar."""
    board = json.loads(Path(board_path).read_bytes())
    content = {key: value for key, value in board.items() if key != "content_hash"}
    if (board.get("schema") != "CapitalChronicleDeskBoardPublicV1"
            or sha256_of(content) != board.get("content_hash")):
        raise ValueError("BOARD_PUBLIC_PROJECTION_INVALID")
    board_at = utc(board["as_of_utc"])
    if board_at > now:
        raise ValueError("BOARD_FROM_FUTURE")
    if us_trading_age(board_at.astimezone(ET).date(), now.astimezone(ET).date()) > 1:
        raise ValueError("BOARD_OLDER_THAN_ONE_TRADING_DAY")
    states = {"UP": "Trending up", "DOWN": "Trending down", "MIXED": "Mixed trend"}
    rows = {}
    for market in MARKETS:
        try:
            yardstick = (board["markets"].get(market) or {}).get("yardstick") or {}
            state = states.get(yardstick.get("yardstick"))
            if yardstick.get("state") != "AVAILABLE" or not state or not yardstick.get("last_completed_bar_utc"):
                raise ValueError("BOARD_MARKET_TREND_UNAVAILABLE")
            completed = utc(yardstick["last_completed_bar_utc"]) + timedelta(days=1)
            if completed > board_at:
                raise ValueError("BOARD_BAR_NOT_COMPLETED")
            if us_trading_age(completed.astimezone(ET).date(), last_close.astimezone(ET).date()) > 1:
                raise ValueError("BOARD_MARKET_DATA_OLDER_THAN_ONE_TRADING_DAY")

            snapshot = snapshots.get(market) or {}
            expected_symbol = quotes.SYMBOLS[market][1]
            if snapshot.get("symbol") != expected_symbol:
                # The wrap can discuss futures moves. The map's gold and S&P
                # rows use the spot/cash instruments shown on their charts.
                quote_options = {"max_age_seconds": 3600}
                if market in {"US500", "USTEC"}:
                    # Cash is closed at the pre-US wrap. The provider can
                    # stamp the last session's index quote after its close.
                    quote_options.update(reference_at=last_close + timedelta(hours=1), max_age_seconds=3660)
                try:
                    observed = quote(market, fetch=False, **quote_options)
                except (OSError, ValueError):
                    observed = quote(market, **quote_options)
                snapshot = wrap_quote(observed)
            if snapshot.get("symbol") != expected_symbol or not snapshot.get("sha256"):
                raise ValueError("MORNING_MAP_QUOTE_SYMBOL_MISMATCH")
            if not utc(snapshot["observed_at_utc"]) <= utc(snapshot["known_at_utc"]) <= utc(clock()):
                raise ValueError("MORNING_MAP_QUOTE_FUTURE_CLOCK")
            change = move(market, snapshot, {**snapshot, "value": snapshot["prior_close"]},
                          basis="from the provider's prior close")["change_pct"]
            rows[market] = {"quote": snapshot, "last": snapshot["value"], "change_1d_pct": change,
                            "state_word": state, "trend_completed_at_utc": completed.isoformat()}
        except (OSError, ValueError, KeyError, TypeError) as exc:
            gaps[f"morning_map:{market}"] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
    return {"rows": rows, "trend_sha256": board["content_hash"], "trend_as_of_utc": board_at.isoformat()}


def wrap_quote(observation):
    return {"symbol": observation["source_symbol"], "value": observation["value"],
            "prior_close": observation["prior_close"], "observed_at_utc": observation["observed_at_utc"],
            "known_at_utc": observation["known_at_utc"], "source": observation["source"],
            "url": observation["source_url"], "sha256": observation["observation_sha256"]}


def collect(slot, *, now, cash_calendar, previous=None, quote=quotes.get,
            history=market_history, plans=read_export, main=latest_main, calendar=CALENDAR,
            clock=quotes.utcnow, releases=public_release_facts, trend_board=TREND_BOARD):
    """Collect each source once. A defect affects only dependent rows."""
    now = utc(now)
    weekly = slot["edition"] == "weekly"
    day = date.fromisoformat(slot["day_et"])
    last = last_session(day - timedelta(days=2 if weekly else 1), cash_calendar)
    prior = last_session(day - timedelta(days=9), cash_calendar) if weekly else None
    last_close = cash_close(last, cash_calendar)
    gaps, rows, snapshots = {}, {}, {}
    for market, (_, key, _) in MARKETS.items():
        try:
            ticker = quotes.SYMBOLS[key][1]
            bars, source = {}, {}
            try:
                hist_kwargs = {"as_of": now}
                if history is market_history:
                    hist_kwargs["cash_calendar"] = cash_calendar
                bars, source = history(market, [prior, last] if weekly else [last], **hist_kwargs)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                if weekly:
                    raise
                gaps[f"history:{market}"] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
            if weekly:
                end = {"symbol": ticker, "date": last.isoformat(), "value": bars[last][2], "source": source}
                start = {"symbol": ticker, "date": prior.isoformat(), "value": bars[prior][2], "source": source}
                basis = "from the previous week's close"
            else:
                # Reuse the cache before a single bounded fetch. A stale quote
                # remains a gap instead of borrowing another instrument's move.
                try:
                    observation = quote(key, fetch=False, max_age_seconds=120)
                except (OSError, ValueError):
                    observation = quote(key, max_age_seconds=3600)
                end = wrap_quote(observation)
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

    map_sources = None
    if not weekly and trend_board is not None:
        try:
            map_sources = morning_map_sources(snapshots, trend_board, now=max(now, utc(clock())),
                                              last_close=last_close, quote=quote, clock=clock, gaps=gaps)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            gaps["morning_map"] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__

    score = None
    stops = None
    plan_record = {"rows": [], "scenario": None}
    try:
        export = plans()
        # The producer may update during I/O. Its generation clock remains
        # distinct from the quote and Main clocks.
        plan_cutoff = max(now, utc(clock()))
        plan_record = project_plans(export, plan_cutoff)
    except TimeoutExpired:
        gaps["plans"] = "PLAN_EXPORT_READER_TIMEOUT"
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
    source_cutoff = max(now, utc(clock()))
    upcoming, weekend, calendar_hash = [], [], None
    try:
        raw_calendar = Path(calendar).read_bytes()
        source_cutoff = max(source_cutoff, utc(clock()))
        calendar_hash = sha256(raw_calendar).hexdigest()
        upcoming = calendar_events(raw_calendar, source_cutoff,
            source_cutoff + timedelta(days=7 if weekly else 1), as_of=source_cutoff)
        if weekly:
            already_in_upcoming = {row["id"] for row in upcoming}
            weekend = [row for row in calendar_events(raw_calendar, last_close, source_cutoff, as_of=source_cutoff)
                       if row["id"] not in already_in_upcoming]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        gaps["calendar"] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
    report = main(source_cutoff)
    if report.get("cause"):
        gaps["main"] = report["cause"]
    try:
        release_facts = releases(last_close if weekly else datetime.combine(last, time(), ET), source_cutoff)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        release_facts = []
        gaps["releases"] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
    latest_quote = max((utc(obs["observed_at_utc"]) for obs in snapshots.values()
                        if obs.get("observed_at_utc")), default=None)
    # Daily quotes have observed UTC clocks. Weekend comparisons use the
    # instrument's dated session bar, whose date is not a shared closing instant.
    return {"slot": slot, "markets": rows, "snapshots": snapshots, "previous_wrap": (
            previous["slot"]["id"] if previous else None), "analysis": report, "plans": plan_record,
            "events": upcoming, "weekend_events": weekend, "calendar_sha256": calendar_hash,
            "weekly_calls": score, "prior_stops_text": stops, "gaps": gaps,
            **({"morning_map_sources": map_sources} if map_sources else {}),
            "released_facts": release_facts,
            "source_pack_as_of_utc": source_cutoff.isoformat(),
            "market_close_date": last.isoformat() if weekly else None,
            "last_cash_close_utc": last_close.astimezone(UTC).isoformat(),
            "data_cutoff_utc": latest_quote.isoformat() if latest_quote else None}


def cash_close(day, calendar):
    early = calendar["years"][str(day.year)]["early_close_13_et"]
    return datetime.combine(day, time(13 if day.isoformat() in early else 16), ET)
