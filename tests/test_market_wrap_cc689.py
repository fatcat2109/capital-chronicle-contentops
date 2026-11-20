from datetime import date, datetime, timedelta
from hashlib import sha256
import json

import pytest

from live_contentops import market_wrap_sources_v1 as sources
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of


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
