from datetime import datetime, timezone
import importlib.util
from pathlib import Path

from live_contentops.x_reply_pack_v1 import save_json

SCRIPT = Path(__file__).resolve().parents[1] / "docs/publisher/CC-511/session_funnel.py"
spec = importlib.util.spec_from_file_location("cc511_funnel", SCRIPT)
reporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reporter)
START, END = reporter.session_bounds("2026-11-12")
ASOF = datetime(2026, 11, 12, 22, tzinfo=timezone.utc)


def run(root, *, number, funnel=None, drops=(), delivery=None):
    folder = root / f"20261112T143{number}00-test"
    data = {"status": "NO_FRESH_UNSENT_DRAFTS", "started_at_utc": f"2026-11-12T14:3{number}:00Z",
            "ended_at_utc": f"2026-11-12T14:3{number}:30Z", "dropped_candidates": list(drops),
            "stage_seconds": {"filter": 6, "ranking": 12, "drafting": 0, "checks": 0, "whole_tick": 30}}
    if funnel is not None:
        data["funnel"] = funnel
    if delivery:
        data["delivery"] = delivery
    save_json(folder / "result.json", data)
    return folder


def test_future_session_is_not_reported_as_a_complete_empty_session(tmp_path):
    result = reporter.summarize(tmp_path, start=START, end=END, asof="2026-11-12T13:00:00Z")
    assert result["session_state"] == "SESSION_NOT_STARTED"
    assert result["window_elapsed"] is False and result["observed_cutoff_utc"] is None
    assert result["stage_minutes"]["filter"]["median_active_minutes"] is None
    assert result["post_to_send_minutes"] == []


def test_distinct_stages_and_first_causes_survive_multiple_ticks(tmp_path):
    funnel = {"seen_post_ids": ["1", "2", "3"], "on_topic": [
        {"post_id": "1", "post_time_utc": "2026-11-12T14:29:00Z"},
        {"post_id": "2", "post_time_utc": "2026-11-12T14:29:00Z"}],
        "with_fact_post_ids": ["2"], "ranking_input_post_ids": ["2"],
        "ranked_above_floor_post_ids": [], "authored_post_ids": []}
    drops = [{"post_id": "1", "cause": "NO_USABLE_FACT"},
             {"post_id": "2", "cause": "NO_ADDED_FACT_ABOVE_QUALITY_FLOOR"},
             {"post_id": "3", "cause": "NO_SIX_MARKET_OR_MACRO_TOPIC"}]
    run(tmp_path, number=0, funnel=funnel, drops=drops)
    run(tmp_path, number=1, funnel=funnel, drops=[{"post_id": "1", "cause": "TARGET_OVER_15_MINUTES_AT_SEND"}])
    result = reporter.summarize(tmp_path, start=START, end=END, asof=ASOF)
    assert result["runs_read"] == 2
    assert result["counts_distinct_posts"] == {"seen": 3, "fresh": 3, "on_topic": 2,
        "with_fact": 1, "ranking_input": 1, "above_floor": 0, "authored": 0, "validated": 0, "sent": 0}
    assert result["first_undrafted_causes"] == {"NO_USABLE_FACT": 1, "NO_ADDED_FACT_ABOVE_QUALITY_FLOOR": 1}
    assert result["stage_minutes"]["filter"]["median_active_minutes"] == 0.1
    assert len(result["artifacts"]) == 2


def test_confirmed_send_is_distinct_from_returned_or_validated_drafts(tmp_path):
    folder = run(tmp_path, number=0, funnel={"on_topic": [{"post_id": "1"}, {"post_id": "2"}],
        "ranked_above_floor_post_ids": ["1", "2"], "authored_post_ids": ["1", "2"],
        "validated_draft_post_ids": ["1"]}, delivery={"delivered": [{
            "post_id": "1", "delivered_at_utc": "2026-11-12T14:30:20Z", "post_to_delivery_minutes": 3.5,
            "post_to_draft_minutes": 3, "stage_seconds": {"telegram_send": 2}}]})
    result = reporter.summarize(tmp_path, start=START, end=END, asof=ASOF)
    assert result["counts_distinct_posts"]["authored"] == 2
    assert result["counts_distinct_posts"]["validated"] == 1
    assert result["counts_distinct_posts"]["sent"] == 1
    assert result["post_to_send_minutes"][0]["post_to_delivery_minutes"] == 3.5
    assert result["stage_minutes"]["telegram_send"]["minutes"] == [2/60]


def test_legacy_absent_stage_and_first_cause_are_named_unknown(tmp_path):
    folder = run(tmp_path, number=0)
    save_json(folder / "reply-pack-request-test.json", {"candidates": [{"post_id": "1",
        "post_time_utc": "2026-11-12T14:29:00Z", "usable_source_ids": ["source"]}]})
    result = reporter.summarize(tmp_path, start=START, end=END, asof=ASOF)
    assert result["counts_distinct_posts"]["with_fact"] == 1
    assert result["counts_distinct_posts"]["above_floor"] == 0
    assert result["first_undrafted_causes"] == {"FIRST_CAUSE_NOT_RETAINED_IN_LEGACY_RUN": 1}


def test_saved_rank_before_a_writer_timeout_counts_its_actual_score(tmp_path):
    folder = run(tmp_path, number=0, drops=[{"post_id": "1", "cause": "CODEX_DRAFT_TIMEOUT_90S"}])
    save_json(folder / "reply-pack-request-test.json", {"candidates": [{"post_id": "1",
        "attempt_key": "attempt-1", "usable_source_ids": ["source"]}]})
    save_json(folder / "editorial/rank/response.json", {"ranking": [{"post_id": "1", "quality_score": 87}]})
    save_json(folder / "editorial/rank/call.json", {"status": "RETURNED"})
    result = reporter.summarize(tmp_path, start=START, end=END, asof=ASOF)
    assert result["counts_distinct_posts"]["above_floor"] == 1
    assert result["counts_distinct_posts"]["authored"] == 0
    assert result["first_undrafted_causes"] == {"CODEX_DRAFT_TIMEOUT_90S": 1}


def test_partial_and_missing_window_records_are_never_complete(tmp_path):
    result = reporter.summarize(tmp_path, start=START, end=END, asof="2026-11-12T15:00:00Z")
    assert result["session_state"] == "PARTIAL_SESSION_OBSERVED"
    result = reporter.summarize(tmp_path, start=START, end=END, asof=ASOF)
    assert result["session_state"] == "NO_COMPLETED_SESSION_RUNS"
