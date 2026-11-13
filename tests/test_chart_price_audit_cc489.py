"""The acceptance reader needs an observed day, honest gaps and distinct charts."""
from datetime import datetime, timedelta, timezone
import json

from live_contentops import publication_image_contract_v1 as contract
from live_contentops.published_images_v1 import SCHEMA
from live_contentops.tradingview_snapshot_v1 import SYMBOLS
from scripts.audit_chart_prices_cc489 import audit

NOW = datetime(2026, 11, 12, 16, tzinfo=timezone.utc)
DAY = "2026-11-12"


def sample(index, *, at=NOW, compared=True, market="EURUSD"):
    snap = {"tv_symbol": SYMBOLS[market], "sha256": f"{index:064x}",
            "page_title": "PRICE 100", "captured_at_utc": at.isoformat()}
    if compared:
        at_quote, _ = contract.comparison_clock(market, at)
        quote = {"market": market, "instrument": market, "price": 100,
            "quoted_at_utc": at_quote.isoformat(), "known_at_utc": at_quote.isoformat(),
            "source_path": "test.json", "source_sha256": "a" * 64}
        return contract.compare_scale(market, snap, quote)
    return contract.not_compared(market, snap, contract.QUOTE_ABSENT[0])


def record(index, *, compared=True, state="PUBLISHED", at=NOW, destination="telegram"):
    check = sample(index, compared=compared, at=at)
    return {"schema_version": SCHEMA, "state": state, "record_id": f"{index}-{destination}",
        "piece_id": f"plan-{index}", "day": DAY, "destination": destination,
        "counts_as_article": False, "images": [{"sha256": f"{index:064x}",
            "image_type": "TRADINGVIEW_MARKET_CHART", "price_scale_check": check}]}


def report(tmp_path, rows=(), events=(), *, now=NOW + timedelta(days=1), since=NOW):
    register, outcomes = tmp_path / "images.jsonl", tmp_path / "outcomes.jsonl"
    register.write_text(''.join(json.dumps(r) + '\n' for r in rows), encoding="utf-8")
    outcomes.write_text(''.join(json.dumps(r) + '\n' for r in events), encoding="utf-8")
    return audit(register, outcomes, DAY, since=since, now=now)


def test_empty_and_partial_day_never_prove_95_percent(tmp_path):
    assert report(tmp_path)["status"] == "NO_PLAN_CHART_OBSERVED"
    partial = report(tmp_path, [record(1)], now=NOW)
    assert partial["compared_percent"] == 100 and partial["status"] == "OBSERVATION_PENDING"


def test_95_percent_is_measured_once_per_plan_chart_and_gaps_keep_their_cause(tmp_path):
    rows = [record(i, compared=i != 20) for i in range(1, 21)]
    rows += [record(1, destination="discord"), record(99, state="RESERVED")]
    result = report(tmp_path, rows)
    assert result["status"] == "PASS" and result["plan_charts"] == 20
    assert result["compared_plan_charts"] == 19 and result["compared_percent"] == 95
    assert result["not_compared"][0]["cause"] == contract.QUOTE_ABSENT[0]
    rows[0] = record(1, compared=False)
    assert report(tmp_path, rows)["status"] == "FAIL"


def test_a_missing_quote_refusal_fails_even_with_full_comparison_coverage(tmp_path):
    event = {"key": "one", "market": "EURUSD", "recorded_at_utc": NOW.isoformat(),
             "status": "TEXT_ONLY", "first_cause": contract.QUOTE_ABSENT[0]}
    result = report(tmp_path, [record(1)], [event, event])
    assert result["compared_percent"] == 100 and result["status"] == "FAIL"
    assert len(result["missing_quote_refusals"]) == 1


def test_shared_capture_under_different_work_items_cannot_inflate_coverage(tmp_path):
    rows = [record(1), record(1, destination="discord"), record(2, compared=False)]
    rows[1]["piece_id"] = "different-work-item-for-the-same-capture"
    result = report(tmp_path, rows)
    assert result["plan_charts"] == 2 and result["compared_plan_charts"] == 1
    assert result["compared_percent"] == 50 and result["status"] == "FAIL"
    chart = next(c for c in result["charts"] if c["compared"])
    assert len(chart["piece_ids"]) == 2 and chart["publication_records"] == 2
    assert set(chart["destinations"]) == {"telegram", "discord"}


def test_same_image_bytes_at_distinct_capture_clocks_remain_distinct_observations(tmp_path):
    rows = [record(1), record(1, at=NOW + timedelta(minutes=1), destination="discord")]
    result = report(tmp_path, rows)
    assert result["plan_charts"] == 2 and result["compared_plan_charts"] == 2


def test_three_day_limits_never_claim_observations_from_one_day_or_reservations(tmp_path):
    result = report(tmp_path, [record(1)], since=NOW - timedelta(days=3))
    market = result["calibration"]["markets"]["EURUSD"]
    assert result["calibration"]["whole_three_day_window_elapsed"]
    assert not market["three_day_observations_present"]
    assert market["limit_pct"] == .15 and market["limit_basis"] == "APPROVED_STARTING_LIMIT"
    assert result["calibration"]["status"] == "THREE_DAY_SAMPLE_INCOMPLETE"
    assert set(result["calibration"]["pending_markets"]) == set(SYMBOLS)


def test_three_observed_days_include_refused_measurements_without_counting_copies(tmp_path):
    events = [{"price_scale_check": sample(100 + i, at=NOW + timedelta(days=i))} for i in range(3)]
    events += events
    result = report(tmp_path, events=events, now=NOW + timedelta(days=3))
    market = result["calibration"]["markets"]["EURUSD"]
    assert market["compared_images"] == 3 and market["three_day_observations_present"]
    assert market["maximum_observed_difference_pct"] == 0


def test_wrong_instrument_or_untimed_comparison_cannot_count_as_measured(tmp_path):
    row = record(1)
    row["images"][0]["price_scale_check"]["quote"]["instrument"] = "6E"
    result = report(tmp_path, [row])
    assert result["compared_percent"] == 0 and result["status"] == "FAIL"
