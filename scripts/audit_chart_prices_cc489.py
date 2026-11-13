"""Read CC-489's coverage and three-day differences from existing image records.

No dispatch, capture, broker access, store write, job or waiting loop.
"""
from __future__ import annotations

import argparse
from datetime import datetime, time, timedelta, timezone
import json
import math
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from live_contentops import publication_image_contract_v1 as contract
from live_contentops.chart_price_reference_v1 import saved_chart_quote
from live_contentops.published_images_v1 import PublishedImages
from live_contentops.tradingview_snapshot_v1 import OUTCOMES, SYMBOLS


def _outcomes(path):
    path = Path(path)
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_bytes().splitlines() if line.strip()]


def _measured(check):
    """Recheck clocks/instrument/arithmetic, including recorded measured refusals."""
    if check.get("comparison_basis") not in {"AT_CAPTURE", "LAST_CLOSE"}:
        return None
    market = check.get("market")
    if market not in SYMBOLS:
        return None
    try:
        snap = {"tv_symbol": check["tv_symbol"], "sha256": check["chart_sha256"],
                "page_title": "REFERENCE " + str(check["chart_price"]),
                "captured_at_utc": check["captured_at_utc"]}
        result = contract.compare_scale(market, snap, check["quote"])
    except contract.ImageContractError as error:
        if str(error) != "TRADINGVIEW_PRICE_SCALE_MISMATCH":
            return None
        result = error.details
    except (ValueError, KeyError, TypeError, OverflowError):
        return None
    if not math.isclose(result["difference_pct"], check.get("difference_pct", -1), abs_tol=1e-9):
        return None
    return result


def audit(register, outcomes, day, *, since, now=None):
    now = now or datetime.now(timezone.utc)
    zone = ZoneInfo("Asia/Bangkok")
    # The existing newsroom production day resets at 02:00 GMT+7.
    start = datetime.combine(datetime.fromisoformat(day).date(), time(2), zone)
    end = start + timedelta(days=1)
    rows = {row["record_id"]: row for row in PublishedImages(register).records()}
    events = _outcomes(outcomes)
    samples, charts, absences = {}, {}, []
    for row in rows.values():
        if row["state"] != "PUBLISHED":
            continue
        for image in row["images"]:
            check = image.get("price_scale_check") or {}
            if check.get("chart_sha256"):
                samples[(check["chart_sha256"], check["captured_at_utc"])] = check
            if (row["day"] != day or row.get("counts_as_article", True)
                    or image.get("image_type") != "TRADINGVIEW_MARKET_CHART"):
                continue
            # Notes, replies and result posts can register a shared capture as
            # different work items. Count the underlying observation once,
            # rather than letting its destination/work-item copies weight it.
            chart_hash = check.get("chart_sha256") or image["sha256"]
            key = (chart_hash, check.get("captured_at_utc"))
            measured = _measured(check)
            entry = {"piece_id": row["piece_id"], "chart_sha256": chart_hash,
                "captured_at_utc": check.get("captured_at_utc"),
                "market": check.get("market") or row.get("market"), "compared": measured is not None,
                "source_kind": (check.get("quote") or {}).get("source_kind", "MAIN_SAVED_TICK")
                               if measured else None,
                "quote_age_seconds": (check.get("quote") or {}).get("age_seconds"),
                "comparison_basis": check.get("comparison_basis"),
                "cause": None if measured else check.get("quote_absent_cause") or "CHART_COMPARISON_NOT_RECORDED",
                "source_attempts": check.get("quote_source_attempts", []),
                "piece_ids": [], "destinations": [], "publication_records": 0}
            entry = charts.setdefault(key, entry)
            if row["piece_id"] not in entry["piece_ids"]:
                entry["piece_ids"].append(row["piece_id"])
            if row.get("destination") and row["destination"] not in entry["destinations"]:
                entry["destinations"].append(row["destination"])
            entry["publication_records"] += 1
    missing_refusals = {}
    for event in events:
        check = event.get("price_scale_check") or {}
        if check.get("chart_sha256"):
            samples[(check["chart_sha256"], check["captured_at_utc"])] = check
        clock = event.get("recorded_at_utc")
        if (clock and start <= contract.utc(clock) < end and
                (event.get("cause") in contract.QUOTE_ABSENT or event.get("first_cause") in contract.QUOTE_ABSENT)):
            key = (event.get("key") or event.get("chart_sha256"), event.get("market"))
            missing_refusals[key] = {"key": key[0], "market": key[1],
                                    "cause": event.get("first_cause") or event.get("cause")}
    compared = sum(row["compared"] for row in charts.values())
    for entry in charts.values():
        if not entry["compared"]:
            absences.append(entry)
    coverage = compared / len(charts) * 100 if charts else None
    elapsed = now >= end
    status = ("OBSERVATION_PENDING" if not elapsed else "NO_PLAN_CHART_OBSERVED" if not charts else
              "FAIL" if coverage < 95 or missing_refusals else "PASS")

    since = contract.utc(since)
    until = since + timedelta(days=3)
    per_market = {}
    for market in SYMBOLS:
        checks = [result for check in samples.values() if check.get("market") == market
                  and (result := _measured(check)) is not None
                  and since <= contract.utc(result["captured_at_utc"]) < min(now, until)]
        differences = sorted(check["difference_pct"] for check in checks)
        dates = sorted({contract.utc(c["captured_at_utc"]).astimezone(contract.ET).date().isoformat() for c in checks})
        per_market[market] = {"limit_pct": contract.MAX_DIFFERENCE_PCT[market],
            "limit_basis": "APPROVED_STARTING_LIMIT", "compared_images": len(checks), "observed_et_dates": dates,
            "maximum_observed_difference_pct": max(differences) if differences else None,
            "p95_difference_pct": differences[max(0, math.ceil(len(differences) * .95) - 1)] if differences else None,
            "measured_above_limit": sum(c["difference_pct"] > contract.MAX_DIFFERENCE_PCT[market] for c in checks),
            "closed_market_comparisons": sum(c["comparison_basis"] == "LAST_CLOSE" for c in checks),
            "three_day_observations_present": now >= until and len(dates) >= 3}
    pending_markets = [market for market, result in per_market.items()
                       if not result["three_day_observations_present"]]
    return {"day": day, "status": status, "whole_live_day_elapsed": elapsed,
        "plan_charts": len(charts), "compared_plan_charts": compared, "compared_percent": coverage,
        "required_compared_percent": 95, "not_compared": absences,
        "missing_quote_refusals": list(missing_refusals.values()), "charts": list(charts.values()),
        "calibration": {"from_utc": since.isoformat(), "until_utc": until.isoformat(),
            "whole_three_day_window_elapsed": now >= until, "markets": per_market,
            "status": "THREE_DAY_SAMPLE_PRESENT" if not pending_markets else "THREE_DAY_SAMPLE_INCOMPLETE",
            "pending_markets": pending_markets},
        "public_write_performed": False, "schedule_changed": False}


def source_readback(*, now=None):
    now = now or datetime.now(timezone.utc)
    result = {}
    for market in SYMBOLS:
        try:
            quote = saved_chart_quote(market, now)
            result[market] = {"status": "AVAILABLE", "quote": {k: v for k, v in quote.items() if k != "price"}}
        except contract.ImageContractError as error:
            result[market] = {"status": "NOT_COMPARED", "cause": str(error), **error.details}
    return {"observed_at_utc": now.isoformat(), "markets": result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", required=True, type=Path)
    parser.add_argument("--outcomes", default=OUTCOMES, type=Path)
    parser.add_argument("--day", required=True)
    parser.add_argument("--since", required=True, help="actual installation/observation start, UTC")
    parser.add_argument("--read-sources", action="store_true")
    args = parser.parse_args()
    report = audit(args.register, args.outcomes, args.day, since=args.since)
    if args.read_sources:
        report["source_readback"] = source_readback()
    print(json.dumps(report, indent=2))
