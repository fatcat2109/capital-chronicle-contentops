from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from scripts.verify_cpi_reaction_page_v1 import compare_cells, join_capture_periods, recompute_market, sample_releases
from test_cpi_reaction_page_cc425 import pack
from live_contentops.cpi_reaction_page_v1 import writer_guidance


def test_fixed_seed_keeps_newest_three_and_five_distinct_older_releases():
    events = [{"release_utc": f"2026-{month:02d}-10T12:30:00Z"} for month in range(1, 11)]
    sample = sample_releases(events)
    assert len(set(sample)) == 8
    assert sample[-3:] == [row["release_utc"] for row in events[-3:]]
    assert sample == sample_releases(list(reversed(events)))
    assert sample[:5] == [events[i]["release_utc"] for i in (0, 1, 2, 3, 5)]


def test_missing_release_or_duplicate_never_reduces_verification_sample():
    with pytest.raises(ValueError, match="EIGHT_DISTINCT"):
        sample_releases([{"release_utc": "2026-01-10T12:30:00Z"}] * 8)


def test_recomputed_return_uses_one_series_and_keeps_missing_endpoint():
    released = datetime(2026, 10, 14, 12, 30, tzinfo=timezone.utc)
    stamp = int(released.timestamp())
    endpoint = released + timedelta(minutes=5)
    cpi = SimpleNamespace(endpoints=lambda _: {"5m": endpoint, "30m": released + timedelta(minutes=30)},
        iso=lambda t: t.isoformat(), bar_ref=lambda row: {"id": row["id"]} if row else None)
    bars = {("XAUUSD", "SOURCE_A", "BID"): {stamp: {"close": 100, "id": "a"},
                                                stamp + 300: {"close": 90, "id": "b"}},
            ("XAUUSD", "SOURCE_B", "BID"): {stamp + 1800: {"close": 200, "id": "c"}}}
    actual = recompute_market("XAUUSD", bars, released, released + timedelta(days=1), cpi)
    assert actual["windows"]["5m"]["move_pct"] == -10
    assert actual["windows"]["30m"]["move_pct"] is None
    assert actual["windows"]["30m"]["missing_reason"] == "EXACT_ENDPOINT_ABSENT"
    changed = {**actual, "windows": {**actual["windows"],
        "5m": {**actual["windows"]["5m"], "move_pct": 10}}}
    result = {"checked_cells": 0, "mismatches": []}
    compare_cells(actual, changed, "/release/Gold", result)
    assert [m["cell"] for m in result["mismatches"]] == ["/release/Gold/windows/5m/move_pct"]
    assert "exported_sha256" in result["mismatches"][0]


def test_current_writer_consumer_replaces_superseded_review_and_november_wait():
    guidance = writer_guidance(pack())
    assert "fixed seed" in guidance and "publish through October" in guidance
    assert "Ops Product's table review precedes" not in guidance


def test_capture_recovery_joins_only_one_explicit_month_for_same_measure_and_date():
    rows = [{"source": "investing", "release_date": "2026-08-12", "measure_id": "headline",
             "reference_period": "2026-07"},
            {"source": "myfxbook", "release_date": "2026-08-12", "measure_id": "headline",
             "reference_period": None},
            {"source": "myfxbook", "release_date": "2026-08-12", "measure_id": "core",
             "reference_period": None}]
    recovered = join_capture_periods(rows)
    assert recovered[1]["reference_period"] == "2026-07"
    assert recovered[2]["reference_period"] is None
