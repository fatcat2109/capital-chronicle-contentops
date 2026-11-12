"""CC-489: read held prices for the chart check, without opening a terminal.

The minute export is preferred when it actually contains a timed price. Otherwise
use an exact-instrument completed M1 close from CC-481's existing store, then
Main's saved tick. Private bar values stay inside the image check's metadata.
"""
from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

from . import publication_image_contract_v1 as contract

PLAN_STATUS_PATH = Path(r"A:\Capital Chronicle\ResearchRuns\plan-status-v1\plan-status.public.json")
BAR_STORE = Path(r"A:\Capital Chronicle\Runtime\OfficialRates\cc-078-20261101\state\intake"
                 r"\completed-bars\bars.sqlite3")
POLICY = "CC489_HELD_CHART_REFERENCE_V1"


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def _iso(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat()


def _unavailable(failures, cause):
    if failures:
        # Sources are scanned newest first. Report the closest held price,
        # rather than letting the last (oldest) failed import mask its age.
        raise min(failures, key=lambda e: abs(getattr(e, "details", {}).get("age_seconds", float("inf"))))
    raise contract.ImageContractError(cause)


def _reference(market, captured_at, price, price_at, known_at, *, max_age_seconds=contract.QUOTE_SKEW_SECONDS,
               comparison_at=None, **source):
    capture = contract.utc(captured_at)
    at, closed = contract.comparison_clock(market, capture)
    if comparison_at is not None:
        at, closed = contract.utc(comparison_at), False
    quoted, known = contract.utc(price_at), contract.utc(known_at)
    age = (at - quoted).total_seconds()
    if known > capture or quoted > known:
        raise contract.ImageContractError("CHART_REFERENCE_NOT_KNOWN_AT_CAPTURE")
    if not 0 <= age <= max_age_seconds:
        raise contract.ImageContractError("CHART_REFERENCE_STALE", price_at_utc=quoted.isoformat(),
                                          age_seconds=age)
    return {"market": market, "instrument": market, "price": contract.number(price),
            "quoted_at_utc": quoted.isoformat(), "known_at_utc": known.isoformat(),
            "comparison_basis": "LAST_CLOSE" if closed else "AT_CAPTURE",
            "comparison_at_utc": at.isoformat(), "age_seconds": age,
            "capture_age_seconds": (capture - quoted).total_seconds(),
            "reference_policy": POLICY, **source}


def plan_status_quote(market, captured_at, path, *, max_age_seconds=contract.QUOTE_SKEW_SECONDS, comparison_at=None):
    """Never confuse an export/check clock, a plan level or an entry with a price."""
    path = Path(path)
    raw = path.read_bytes()
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get("schema") != "CapitalChroniclePlanStatusV1":
        raise contract.ImageContractError("PLAN_STATUS_PRICE_SCHEMA_INVALID")
    digest = sha256(_canonical({k: v for k, v in data.items() if k != "content_hash"})).hexdigest()
    if data.get("content_hash") != digest:
        raise contract.ImageContractError("PLAN_STATUS_PRICE_HASH_INVALID")
    known = contract.utc(data["generated_at_utc"])
    if known > contract.utc(captured_at):
        raise contract.ImageContractError("CHART_REFERENCE_NOT_KNOWN_AT_CAPTURE")
    candidates, failures = [], []
    if not isinstance(data.get("plans"), list):
        raise contract.ImageContractError("PLAN_STATUS_PRICE_SCHEMA_INVALID")
    for row in data["plans"]:
        if not isinstance(row, dict) or row.get("asset_id") != market:
            continue
        quote = row.get("last_quote") or row.get("quote")
        if not isinstance(quote, dict):
            # Scalar last_price needs its own observation clock. checked_at is
            # deliberately not a substitute for last_price_at_utc.
            if row.get("last_price") is None:
                continue
            quote = {"instrument": market, "price": row["last_price"],
                     "quoted_at_utc": row.get("last_price_at_utc")}
        try:
            if quote.get("instrument") != market:
                raise contract.ImageContractError("CHART_REFERENCE_INSTRUMENT_MISMATCH")
            quote_known = contract.utc(quote.get("known_at_utc") or known)
            if quote_known > known or contract.utc(quote["quoted_at_utc"]) > quote_known:
                raise contract.ImageContractError("CHART_REFERENCE_NOT_KNOWN_AT_CAPTURE")
            candidates.append(_reference(market, captured_at, quote["price"],
                quote["quoted_at_utc"], known, source_kind="PLAN_STATUS_EXPORT",
                source_path=str(path.resolve()), source_sha256=sha256(raw).hexdigest(),
                source_content_hash=digest, price_basis="plan_feed", max_age_seconds=max_age_seconds,
                comparison_at=comparison_at))
        except (ValueError, KeyError, TypeError, OverflowError) as exc:
            failures.append(exc)
    if not candidates:
        _unavailable(failures, "PLAN_STATUS_LAST_PRICE_NOT_EXPORTED")
    return min(candidates, key=lambda q: q["age_seconds"])


def bar_store_quote(market, captured_at, path, *, max_age_seconds=contract.QUOTE_SKEW_SECONDS, comparison_at=None):
    """CC-481 M1 closes; no proxy futures/ETF, forming bar, invalid bar or future import.

    Source capture time remains known-at. A historical bar imported after an old
    snapshot cannot certify that snapshot. The original source hash and an exact
    row hash are retained instead of hashing a mutable 69 MB SQLite file.
    """
    path = Path(path)
    capture = contract.utc(captured_at)
    at, _ = contract.comparison_clock(market, capture)
    if comparison_at is not None:
        at = contract.utc(comparison_at)
    candidates, failures = [], []
    # mode=ro refuses a missing file without creating one; query_only also
    # protects an existing store. The timeout bounds contention with its writer.
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=.25)) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        sources = db.execute("""SELECT * FROM history_sources
            WHERE market=? AND timeframe='M1' AND series_id='NATIVE_BROKER'
                AND known_epoch<=? ORDER BY known_epoch DESC LIMIT 64""",
            (market, capture.timestamp())).fetchall()
        for source in sources:
            try:
                metadata = json.loads(source["metadata_json"])
                if (not isinstance(metadata, dict) or metadata.get("source_instrument") != market
                        or metadata.get("contract_id") != "EXNESS_DEMO:" + market):
                    failures.append(contract.ImageContractError("CHART_REFERENCE_INSTRUMENT_MISMATCH"))
                    continue
                row = db.execute("""SELECT * FROM history_bars b WHERE source_id=? AND end_epoch<=?
                    AND NOT EXISTS (SELECT 1 FROM history_invalid i
                        WHERE i.source_id=b.source_id AND i.open_epoch=b.open_epoch)
                    ORDER BY open_epoch DESC LIMIT 1""", (source["source_id"], at.timestamp())).fetchone()
                if not row:
                    continue
                if (row["end_epoch"] - row["open_epoch"] != 60
                        or not 0 < row["low"] <= row["close"] <= row["high"]):
                    raise contract.ImageContractError("CHART_REFERENCE_BAR_INVALID")
                candidates.append(_reference(market, capture, row["close"], _iso(row["end_epoch"]),
                    _iso(source["known_epoch"]), source_kind="BAR_STORE_M1_CLOSE",
                    source_path=source["path"], source_sha256=source["source_sha256"],
                    storage_path=str(path.resolve()), source_record_sha256=sha256(_canonical(dict(row))).hexdigest(),
                    source_id=source["source_id"], bar_start_utc=_iso(row["open_epoch"]),
                    bar_end_utc=_iso(row["end_epoch"]), price_basis="plan_bar_close", max_age_seconds=max_age_seconds,
                    comparison_at=comparison_at))
            except (ValueError, KeyError, TypeError, OverflowError) as exc:
                failures.append(exc)
    if not candidates:
        _unavailable(failures, "BAR_STORE_EXACT_M1_PRICE_UNAVAILABLE")
    return min(candidates, key=lambda q: q["age_seconds"])


def public_chart_quote(market, captured_at):
    """Read only: acquire BEFORE the download, never backdate a later HTTP read."""
    from . import public_market_quote_v1 as public
    at, _ = contract.comparison_clock(market, captured_at)
    observation = public.get(market, now=captured_at, fetch=False,
        max_age_seconds=contract.QUOTE_SKEW_SECONDS, reference_at=at)
    return _reference(market, captured_at, observation["value"], observation["observed_at_utc"],
        observation["known_at_utc"], source_kind="PUBLIC_ON_DEMAND_QUOTE",
        source=observation["source"], source_path=observation["observation_path"],
        source_sha256=observation["observation_sha256"], source_url=observation["source_url"],
        source_symbol=observation["source_symbol"], instrument_name=observation["instrument_name"],
        instrument_type=observation["instrument_type"],
        price_basis="chart_futures" if market == "USOIL" else "public_" + observation["instrument_type"].lower())


def prepare_chart_quote(market, *, now=None):
    """The existing capture calls this once, ahead of its image observation."""
    from . import public_market_quote_v1 as public
    now = now or datetime.now(timezone.utc)
    for read in (lambda: plan_status_quote(market, now, PLAN_STATUS_PATH),
                 lambda: bar_store_quote(market, now, BAR_STORE)):
        try:
            read()
            return
        except (OSError, ValueError, KeyError, TypeError, OverflowError, sqlite3.Error):
            pass
    at, _ = contract.comparison_clock(market, now)
    try:
        public.get(market, now=now, max_age_seconds=contract.QUOTE_SKEW_SECONDS, reference_at=at)
    except (OSError, ValueError):
        # The read after capture retains the exact failure. No missing quote veto.
        pass


def saved_chart_quote(market, captured_at, *, export_path=None, bar_store=None, root=None):
    """Choose a held reference; an unavailable source never refuses the image."""
    attempts = []
    for kind, read in (
        ("PLAN_STATUS_EXPORT", lambda: plan_status_quote(market, captured_at, export_path or PLAN_STATUS_PATH)),
        ("BAR_STORE_M1_CLOSE", lambda: bar_store_quote(market, captured_at, bar_store or BAR_STORE)),
        ("PUBLIC_ON_DEMAND_QUOTE", lambda: public_chart_quote(market, captured_at)),
        ("MAIN_SAVED_TICK", lambda: contract.saved_main_quote(market, captured_at, root=root)),
    ):
        try:
            quote = read()
            if kind == "MAIN_SAVED_TICK":
                at, _ = contract.comparison_clock(market, captured_at)
                quote.update(source_kind=kind, reference_policy=POLICY,
                    age_seconds=(at - contract.utc(quote["quoted_at_utc"])).total_seconds(),
                    capture_age_seconds=(contract.utc(captured_at) - contract.utc(quote["quoted_at_utc"])).total_seconds())
            if attempts:
                quote["source_attempts"] = attempts
            return quote
        except (OSError, ValueError, KeyError, TypeError, OverflowError, sqlite3.Error) as exc:
            from .public_market_quote_v1 import QuoteError
            attempts.append({"source_kind": kind,
                "cause": str(exc) if isinstance(exc, (contract.ImageContractError, QuoteError)) else
                         "CHART_REFERENCE_SOURCE_UNREADABLE:" + type(exc).__name__,
                **(exc.details if isinstance(exc, (contract.ImageContractError, QuoteError)) else {})})
    _, closed = contract.comparison_clock(market, captured_at)
    raise contract.ImageContractError(contract.QUOTE_ABSENT[int(closed)], market=market,
                                      source_attempts=attempts)
